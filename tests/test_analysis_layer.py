from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import (
    analysis_population_readiness,
    public_analysis_projection,
    validate_analysis,
)


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class AnalyticalLayerFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load("data/analysis/schema.json")
        cls.evidence = load("data/analysis/evidence_registry.json")
        cls.reviews = load("data/analysis/event_reviews.json")
        cls.canonical = load("data/canonical/registry.json")

    def validate(self, schema=None, evidence=None, reviews=None, canonical=None):
        return validate_analysis(
            schema or self.schema,
            evidence or self.evidence,
            reviews or self.reviews,
            canonical or self.canonical,
        )

    def review(self, analysis_id: str):
        return next(row for row in self.reviews["reviews"] if row["analysis_id"] == analysis_id)

    def canonical(self, occurrence_id: str):
        return next(
            row for row in self.canonical["records"] if row.get("occurrence_id") == occurrence_id
        )

    def test_samples_validate(self):
        report = self.validate()
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(len(self.reviews["reviews"]), 2)
        self.assertEqual(len(self.evidence["evidence"]), 5)

    def test_samples_bind_to_real_completed_occurrences_of_different_types(self):
        abs_review = self.review("WSAN-AU-GDP-2026Q2-001")
        nz_review = self.review("WSAN-NZ-OCR-20260902-001")
        abs_canonical = self.canonical(abs_review["canonical_occurrence_id"])
        nz_canonical = self.canonical(nz_review["canonical_occurrence_id"])

        self.assertEqual(abs_review["canonical_occurrence_id"], "WSO-MAC-A-0025")
        self.assertEqual(abs_canonical["series_id"], "WSER-MAC-AU-GDP")
        self.assertEqual(abs_canonical["event_type"], "DATA_RELEASE")
        self.assertEqual(abs_canonical["lifecycle_status"], "COMPLETED")
        self.assertEqual(abs_canonical["start_utc"], "2026-09-02T01:30:00Z")

        self.assertEqual(nz_review["canonical_occurrence_id"], "WSO-8df73c7804d45880")
        self.assertEqual(nz_canonical["series_id"], "WS.CB.RBNZ.OCR_DECISION")
        self.assertEqual(nz_canonical["institution"], "Reserve Bank of New Zealand")
        self.assertEqual(nz_canonical["event_type"], "DECISION")
        self.assertEqual(nz_canonical["lifecycle_status"], "COMPLETED")
        self.assertEqual(nz_canonical["start_utc"], "2026-09-02T02:00:00Z")

    def test_reviewed_post_event_packet_requires_completed_canonical_lifecycle(self):
        canonical = deepcopy(self.canonical)
        row = next(
            item for item in canonical["records"] if item.get("occurrence_id") == "WSO-8df73c7804d45880"
        )
        row["lifecycle_status"] = "PLANNED"
        report = self.validate(canonical=canonical)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("reviewed post-event analysis requires canonical lifecycle COMPLETED" in e for e in report.errors)
        )

    def test_population_policy_forbids_elapsed_completion_and_synthetic_history(self):
        policy = self.schema["population_readiness_policy"]
        self.assertTrue(policy["elapsed_date_never_implies_completion"])
        self.assertTrue(policy["missing_historical_anchor_never_authorizes_synthetic_occurrence"])
        self.assertEqual(policy["post_event_anchor_lifecycle"], "COMPLETED")

    def test_analytical_evidence_never_becomes_canonical_provenance(self):
        canonical_source_ids = {row.get("source_id") for row in self.canonical["records"]}
        evidence_ids = {row["evidence_id"] for row in self.evidence["evidence"]}
        self.assertTrue(evidence_ids.isdisjoint(canonical_source_ids))
        self.assertTrue(
            all(row["canonical_provenance_effect"] == "NONE" for row in self.evidence["evidence"])
        )

    def test_unknown_canonical_occurrence_fails_closed(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["canonical_occurrence_id"] = "WSO-NOT-REAL"
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("unknown canonical occurrence_id" in error for error in report.errors))

    def test_market_movement_requires_window_precision_evidence_and_representation(self):
        reviews = deepcopy(self.reviews)
        movement = reviews["reviews"][0]["what_moved"][0]
        movement["measurement_window"] = None
        movement["measurement_precision"] = "MADE_UP"
        movement["movement_representation"] = "MAGIC_BASELINE"
        movement["evidence_refs"] = []
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        joined = "\n".join(report.errors)
        self.assertIn("measurement_window required", joined)
        self.assertIn("invalid measurement_precision", joined)
        self.assertIn("invalid movement_representation", joined)
        self.assertIn("evidence_refs required", joined)

    def test_pre_post_representation_requires_both_values(self):
        reviews = deepcopy(self.reviews)
        movement = reviews["reviews"][0]["what_moved"][0]
        movement["before_value"] = None
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("PRE_POST_VALUES requires before_value and after_value" in e for e in report.errors))

    def test_change_and_endpoint_preserves_unknown_pre_value(self):
        nz_review = self.review("WSAN-NZ-OCR-20260902-001")
        for movement in nz_review["what_moved"]:
            self.assertEqual(movement["movement_representation"], "CHANGE_AND_ENDPOINT")
            self.assertIsNone(movement["before_value"])
            self.assertIsNotNone(movement["after_value"])
            self.assertIsNotNone(movement["change"])
            self.assertFalse(movement["independently_reconstructed"])

        reviews = deepcopy(self.reviews)
        nz = next(row for row in reviews["reviews"] if row["analysis_id"] == "WSAN-NZ-OCR-20260902-001")
        nz["what_moved"][0]["before_value"] = 3.7301
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("must not synthesize before_value" in e for e in report.errors))

    def test_market_movement_does_not_supply_missing_surprise_basis(self):
        reviews = deepcopy(self.reviews)
        surprise = reviews["reviews"][0]["what_surprised"]
        surprise["status"] = "UPSIDE"
        surprise["comparisons"] = []
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("surprise requires an explicit comparison basis" in e for e in report.errors))

    def test_qualitative_guidance_surprise_is_valid_but_must_have_descriptions(self):
        nz_review = self.review("WSAN-NZ-OCR-20260902-001")
        qualitative = next(
            row for row in nz_review["what_surprised"]["comparisons"] if row["comparison_kind"] == "QUALITATIVE"
        )
        self.assertIn("2.81 percent", qualitative["actual"])
        self.assertIn("3.5 percent", qualitative["expected"])
        self.assertTrue(self.validate().ok)

        reviews = deepcopy(self.reviews)
        nz = next(row for row in reviews["reviews"] if row["analysis_id"] == "WSAN-NZ-OCR-20260902-001")
        q = next(row for row in nz["what_surprised"]["comparisons"] if row["comparison_kind"] == "QUALITATIVE")
        q["expected"] = ""
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("qualitative comparison requires actual and expected descriptions" in e for e in report.errors))

    def test_benchmark_type_is_controlled(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_was_expected"]["benchmarks"][0]["benchmark_type"] = "VIBES"
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("invalid benchmark_type" in e for e in report.errors))
        self.assertIn("MARKET_CONSENSUS_DECISION", self.schema["controlled_vocabularies"]["benchmark_type"])

    def test_interaction_type_reuses_controlled_vocabulary(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_appears_connected"]["interaction_type"] = "POST_HOC_STORY"
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("invalid interaction_type" in error for error in report.errors))
        self.assertIn("TRANSMISSION_CHANNEL", self.schema["controlled_vocabularies"]["interaction_type"])

    def test_non_null_connection_requires_alternatives(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["alternative_explanations"] = []
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("requires alternative explanations" in error for error in report.errors))

    def test_stronger_causal_language_requires_multiple_evidence_references(self):
        reviews = deepcopy(self.reviews)
        connection = reviews["reviews"][0]["what_appears_connected"]
        connection["causal_status"] = "CAUSAL_SUPPORT_PARTIAL"
        connection["evidence_refs"] = ["WSEV-AU-GDP-REUTERS-20260902"]
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("stronger causal language" in error for error in report.errors))

    def test_missing_evidence_reference_fails_closed(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_happened"]["evidence_refs"] = ["WSEV-MISSING"]
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("unknown evidence refs" in error for error in report.errors))

    def test_evidence_cannot_claim_canonical_provenance_effect(self):
        evidence = deepcopy(self.evidence)
        evidence["evidence"][0]["canonical_provenance_effect"] = "REPLACE_CANONICAL_SOURCE"
        report = self.validate(evidence=evidence)
        self.assertFalse(report.ok)
        self.assertTrue(any("cannot alter canonical provenance" in error for error in report.errors))

    def test_second_order_none_is_valid_and_explicit_for_both_samples(self):
        self.assertTrue(
            all(row["second_order_effects"]["status"] == "NOT_ESTABLISHED" for row in self.reviews["reviews"])
        )
        self.assertTrue(self.validate().ok)

    def test_population_readiness_is_descriptive_and_tracks_review_event_type_diversity(self):
        readiness = analysis_population_readiness(self.schema, self.reviews, self.canonical)
        self.assertEqual(readiness["reviewed_occurrence_count"], 2)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 2)
        self.assertEqual(readiness["reviewed_by_event_type"].get("DATA_RELEASE"), 1)
        self.assertEqual(readiness["reviewed_by_event_type"].get("DECISION"), 1)
        self.assertTrue(readiness["elapsed_date_never_implies_completion"])
        self.assertTrue(readiness["missing_historical_anchor_never_authorizes_synthetic_occurrence"])
        self.assertIn(
            readiness["broad_population_state"],
            {
                "BLOCKED_NO_PRIORITY_REGION_COMPLETED_ANCHOR",
                "BLOCKED_PRIORITY_REGION_REVIEW_GAP",
                "READY_FOR_CONTROLLED_EXPANSION",
            },
        )
        self.assertEqual(
            [row["region"] for row in readiness["priority_geographic_stress_regions"]],
            ["Africa", "South Asia", "Southeast Asia", "Latin America"],
        )

    def test_projection_is_read_only_generic_and_does_not_mutate_inputs(self):
        before = digest(self.canonical)
        projection = public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)
        after = digest(self.canonical)
        self.assertEqual(before, after)
        self.assertFalse(projection["metadata"]["canonical_mutation_allowed"])
        self.assertFalse(projection["metadata"]["google_calendar_write"])
        self.assertTrue(projection["metadata"]["population_readiness_is_descriptive_not_population_authority"])
        self.assertEqual(projection["metadata"]["review_count"], 2)
        self.assertEqual(len(projection["reviews"][0]["evidence"]), 2)
        self.assertEqual(len(projection["reviews"][1]["evidence"]), 3)
        self.assertEqual(projection["reviews"][1]["canonical"]["event_type"], "DECISION")
        self.assertEqual(projection["reviews"][1]["canonical"]["region"], "Oceania / Pacific")

    def test_browser_module_reads_only_analysis_projection_and_is_not_gdp_hard_coded(self):
        source = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        fetches = re.findall(r"fetch\((['\"])(.*?)\1", source)
        self.assertEqual([url for _, url in fetches], ["data/analysis.json"])
        for forbidden in (
            "data/canonical",
            "data/sources",
            "data/monitor",
            "method:'POST'",
            'method:"POST"',
            "localStorage",
            "Australian GDP · June quarter 2026",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("canonical.canonical_name", source)
        self.assertIn("CHANGE_AND_ENDPOINT", source)
        self.assertIn("endpoint ${esc(row.after_value)}", source)
        self.assertIn("Canonical write: OFF", source)
        self.assertIn("Movement ≠ cause", source)
        self.assertIn("missing historical anchor does not permit", source)

    def test_static_build_validates_and_publishes_analysis_without_html_mutation(self):
        build = (ROOT / "scripts/build_site.py").read_text(encoding="utf-8")
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        self.assertIn("validate_analysis", build)
        self.assertIn('docs/"data/analysis.json"', build)
        self.assertIn('bundled source: web/analysis.js', build)
        self.assertIn('"analysis.css"', build)
        self.assertNotIn('id="analysisView"', html)
        self.assertNotIn('id="analysisTab"', html)


if __name__ == "__main__":
    unittest.main()
