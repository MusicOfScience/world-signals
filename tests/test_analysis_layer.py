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

from world_signals.analysis import analysis_population_readiness, public_analysis_projection, validate_analysis


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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

    def canonical_row(self, occurrence_id: str):
        return next(row for row in self.canonical["records"] if row.get("occurrence_id") == occurrence_id)

    def test_foundation_samples_validate_through_descendant_population(self):
        report = self.validate()
        self.assertTrue(report.ok, report.errors)
        analysis_ids = {row["analysis_id"] for row in self.reviews["reviews"]}
        evidence_ids = {row["evidence_id"] for row in self.evidence["evidence"]}
        self.assertTrue({"WSAN-AU-GDP-2026Q2-001", "WSAN-NZ-OCR-20260902-001"} <= analysis_ids)
        self.assertTrue({
            "WSEV-AU-GDP-ABS-20260902",
            "WSEV-AU-GDP-REUTERS-20260902",
            "WSEV-NZ-OCR-RBNZ-20260902",
            "WSEV-NZ-OCR-BT-20260902",
            "WSEV-NZ-OCR-REUTERS-20260902",
        } <= evidence_ids)
        self.assertGreaterEqual(len(self.reviews["reviews"]), 2)
        self.assertGreaterEqual(len(self.evidence["evidence"]), 5)

    def test_samples_bind_to_completed_occurrences_of_different_types(self):
        abs_review = self.review("WSAN-AU-GDP-2026Q2-001")
        nz_review = self.review("WSAN-NZ-OCR-20260902-001")
        abs_row = self.canonical_row(abs_review["canonical_occurrence_id"])
        nz_row = self.canonical_row(nz_review["canonical_occurrence_id"])
        self.assertEqual((abs_row["series_id"], abs_row["event_type"], abs_row["lifecycle_status"], abs_row["start_utc"]),
                         ("WSER-MAC-AU-GDP", "DATA_RELEASE", "COMPLETED", "2026-09-02T01:30:00Z"))
        self.assertEqual((nz_row["series_id"], nz_row["institution"], nz_row["event_type"], nz_row["lifecycle_status"], nz_row["start_utc"]),
                         ("WS.CB.RBNZ.OCR_DECISION", "Reserve Bank of New Zealand", "DECISION", "COMPLETED", "2026-09-02T02:00:00Z"))

    def test_reviewed_post_event_requires_completed_canonical_lifecycle(self):
        canonical = deepcopy(self.canonical)
        next(row for row in canonical["records"] if row.get("occurrence_id") == "WSO-8df73c7804d45880")["lifecycle_status"] = "PLANNED"
        report = self.validate(canonical=canonical)
        self.assertFalse(report.ok)
        self.assertTrue(any("requires canonical lifecycle COMPLETED" in e for e in report.errors))

    def test_population_policy_forbids_elapsed_completion_and_synthetic_history(self):
        policy = self.schema["population_readiness_policy"]
        self.assertEqual(policy["post_event_anchor_lifecycle"], "COMPLETED")
        self.assertTrue(policy["elapsed_date_never_implies_completion"])
        self.assertTrue(policy["missing_historical_anchor_never_authorizes_synthetic_occurrence"])

    def test_analytical_evidence_never_becomes_canonical_provenance(self):
        canonical_source_ids = {row.get("source_id") for row in self.canonical["records"]}
        evidence_ids = {row["evidence_id"] for row in self.evidence["evidence"]}
        self.assertTrue(evidence_ids.isdisjoint(canonical_source_ids))
        self.assertTrue(all(row["canonical_provenance_effect"] == "NONE" for row in self.evidence["evidence"]))

    def test_unknown_canonical_occurrence_fails_closed(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["canonical_occurrence_id"] = "WSO-NOT-REAL"
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("unknown canonical occurrence_id" in e for e in report.errors))

    def test_market_movement_requires_window_precision_evidence_and_representation(self):
        reviews = deepcopy(self.reviews)
        move = reviews["reviews"][0]["what_moved"][0]
        move.update(measurement_window=None, measurement_precision="MADE_UP", movement_representation="MAGIC_BASELINE", evidence_refs=[])
        joined = "\n".join(self.validate(reviews=reviews).errors)
        self.assertIn("measurement_window required", joined)
        self.assertIn("invalid measurement_precision", joined)
        self.assertIn("invalid movement_representation", joined)
        self.assertIn("evidence_refs required", joined)

    def test_pre_post_representation_requires_both_values(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_moved"][0]["before_value"] = None
        self.assertTrue(any("PRE_POST_VALUES requires before_value and after_value" in e for e in self.validate(reviews=reviews).errors))

    def test_change_and_endpoint_preserves_unknown_pre_value(self):
        nz = self.review("WSAN-NZ-OCR-20260902-001")
        for move in nz["what_moved"]:
            self.assertEqual(move["movement_representation"], "CHANGE_AND_ENDPOINT")
            self.assertIsNone(move["before_value"])
            self.assertIsNotNone(move["after_value"])
            self.assertIsNotNone(move["change"])
            self.assertFalse(move["independently_reconstructed"])
        reviews = deepcopy(self.reviews)
        nz_copy = next(row for row in reviews["reviews"] if row["analysis_id"] == "WSAN-NZ-OCR-20260902-001")
        nz_copy["what_moved"][0]["before_value"] = 3.7301
        self.assertTrue(any("must not synthesize before_value" in e for e in self.validate(reviews=reviews).errors))

    def test_surprise_requires_explicit_basis_and_allows_qualitative_guidance(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_surprised"]["comparisons"] = []
        self.assertTrue(any("surprise requires an explicit comparison basis" in e for e in self.validate(reviews=reviews).errors))
        nz = self.review("WSAN-NZ-OCR-20260902-001")
        qualitative = next(row for row in nz["what_surprised"]["comparisons"] if row["comparison_kind"] == "QUALITATIVE")
        self.assertIn("2.81 percent", qualitative["actual"])
        self.assertIn("3.5 percent", qualitative["expected"])
        reviews = deepcopy(self.reviews)
        q = next(row for row in next(r for r in reviews["reviews"] if r["analysis_id"] == "WSAN-NZ-OCR-20260902-001")["what_surprised"]["comparisons"] if row["comparison_kind"] == "QUALITATIVE")
        q["expected"] = ""
        self.assertTrue(any("qualitative comparison requires actual and expected descriptions" in e for e in self.validate(reviews=reviews).errors))

    def test_benchmark_and_interaction_vocabularies_are_controlled(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_was_expected"]["benchmarks"][0]["benchmark_type"] = "VIBES"
        reviews["reviews"][0]["what_appears_connected"]["interaction_type"] = "POST_HOC_STORY"
        joined = "\n".join(self.validate(reviews=reviews).errors)
        self.assertIn("invalid benchmark_type", joined)
        self.assertIn("invalid interaction_type", joined)
        self.assertIn("MARKET_CONSENSUS_DECISION", self.schema["controlled_vocabularies"]["benchmark_type"])
        self.assertIn("TRANSMISSION_CHANNEL", self.schema["controlled_vocabularies"]["interaction_type"])

    def test_non_null_connection_requires_alternatives_and_stronger_language_needs_more_evidence(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["alternative_explanations"] = []
        self.assertTrue(any("requires alternative explanations" in e for e in self.validate(reviews=reviews).errors))
        reviews = deepcopy(self.reviews)
        connection = reviews["reviews"][0]["what_appears_connected"]
        connection["causal_status"] = "CAUSAL_SUPPORT_PARTIAL"
        connection["evidence_refs"] = ["WSEV-AU-GDP-REUTERS-20260902"]
        self.assertTrue(any("stronger causal language" in e for e in self.validate(reviews=reviews).errors))

    def test_missing_evidence_and_provenance_escalation_fail_closed(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_happened"]["evidence_refs"] = ["WSEV-MISSING"]
        self.assertTrue(any("unknown evidence refs" in e for e in self.validate(reviews=reviews).errors))
        evidence = deepcopy(self.evidence)
        evidence["evidence"][0]["canonical_provenance_effect"] = "REPLACE_CANONICAL_SOURCE"
        self.assertTrue(any("cannot alter canonical provenance" in e for e in self.validate(evidence=evidence).errors))

    def test_foundation_second_order_none_survives_descendant_population(self):
        by_analysis = {row["analysis_id"]: row for row in self.reviews["reviews"]}
        for analysis_id in ("WSAN-AU-GDP-2026Q2-001", "WSAN-NZ-OCR-20260902-001"):
            self.assertIn(analysis_id, by_analysis)
            self.assertEqual(by_analysis[analysis_id]["second_order_effects"]["status"], "NOT_ESTABLISHED")

    def test_population_readiness_preserves_foundation_through_descendants(self):
        readiness = analysis_population_readiness(self.schema, self.reviews, self.canonical)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 2)
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 2)
        self.assertGreaterEqual(readiness["reviewed_by_event_type"].get("DATA_RELEASE", 0), 1)
        self.assertGreaterEqual(readiness["reviewed_by_event_type"].get("DECISION", 0), 1)
        self.assertEqual([row["region"] for row in readiness["priority_geographic_stress_regions"]],
                         ["Africa", "South Asia", "Southeast Asia", "Latin America"])
        self.assertTrue(readiness["elapsed_date_never_implies_completion"])
        self.assertTrue(readiness["missing_historical_anchor_never_authorizes_synthetic_occurrence"])

    def test_projection_is_read_only_generic_and_does_not_mutate_inputs(self):
        before = digest(self.canonical)
        projection = public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertEqual(before, digest(self.canonical))
        self.assertFalse(projection["metadata"]["canonical_mutation_allowed"])
        self.assertFalse(projection["metadata"]["google_calendar_write"])
        self.assertTrue(projection["metadata"]["population_readiness_is_descriptive_not_population_authority"])
        self.assertEqual(projection["metadata"]["review_count"], len(self.reviews["reviews"]))
        by_id = {row["analysis_id"]: row for row in projection["reviews"]}
        self.assertEqual(len(by_id["WSAN-AU-GDP-2026Q2-001"]["evidence"]), 2)
        self.assertEqual(len(by_id["WSAN-NZ-OCR-20260902-001"]["evidence"]), 3)
        self.assertEqual(by_id["WSAN-NZ-OCR-20260902-001"]["canonical"]["event_type"], "DECISION")

    def test_browser_reads_only_analysis_projection_and_is_generic(self):
        source = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        fetches = re.findall(r"fetch\((['\"])(.*?)\1", source)
        self.assertEqual([url for _, url in fetches], ["data/analysis.json"])
        for forbidden in ("data/canonical", "data/sources", "data/monitor", "method:'POST'", 'method:"POST"', "localStorage", "Australian GDP · June quarter 2026"):
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
