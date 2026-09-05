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

from world_signals.analysis import public_analysis_projection, validate_analysis


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

    def validate(self, schema=None, evidence=None, reviews=None):
        return validate_analysis(
            schema or self.schema,
            evidence or self.evidence,
            reviews or self.reviews,
            self.canonical,
        )

    def test_sample_validates(self):
        report = self.validate()
        self.assertTrue(report.ok, report.errors)

    def test_sample_is_bound_to_real_completed_abs_gdp_occurrence(self):
        review = self.reviews["reviews"][0]
        canonical = next(
            row
            for row in self.canonical["records"]
            if row.get("occurrence_id") == review["canonical_occurrence_id"]
        )
        self.assertEqual(review["canonical_occurrence_id"], "WSO-MAC-A-0025")
        self.assertEqual(canonical["series_id"], "WSER-MAC-AU-GDP")
        self.assertEqual(canonical["institution"], "Australian Bureau of Statistics")
        self.assertEqual(canonical["lifecycle_status"], "COMPLETED")
        self.assertEqual(canonical["start_utc"], "2026-09-02T01:30:00Z")

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

    def test_market_movement_requires_window_precision_and_evidence(self):
        reviews = deepcopy(self.reviews)
        movement = reviews["reviews"][0]["what_moved"][0]
        movement["measurement_window"] = None
        movement["measurement_precision"] = "MADE_UP"
        movement["evidence_refs"] = []
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        joined = "\n".join(report.errors)
        self.assertIn("measurement_window required", joined)
        self.assertIn("invalid measurement_precision", joined)
        self.assertIn("evidence_refs required", joined)

    def test_market_movement_does_not_supply_missing_surprise_basis(self):
        reviews = deepcopy(self.reviews)
        surprise = reviews["reviews"][0]["what_surprised"]
        surprise["status"] = "UPSIDE"
        surprise["comparisons"] = []
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("surprise requires an explicit comparison basis" in e for e in report.errors))

    def test_interaction_type_reuses_controlled_vocabulary(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"][0]["what_appears_connected"]["interaction_type"] = "POST_HOC_STORY"
        report = self.validate(reviews=reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("invalid interaction_type" in error for error in report.errors))
        self.assertIn(
            "TRANSMISSION_CHANNEL",
            self.schema["controlled_vocabularies"]["interaction_type"],
        )

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

    def test_second_order_none_is_valid_and_explicit(self):
        review = self.reviews["reviews"][0]
        self.assertEqual(review["second_order_effects"]["status"], "NOT_ESTABLISHED")
        self.assertTrue(self.validate().ok)

    def test_projection_is_read_only_and_does_not_mutate_inputs(self):
        before = digest(self.canonical)
        projection = public_analysis_projection(
            self.schema, self.evidence, self.reviews, self.canonical
        )
        after = digest(self.canonical)
        self.assertEqual(before, after)
        self.assertFalse(projection["metadata"]["canonical_mutation_allowed"])
        self.assertFalse(projection["metadata"]["google_calendar_write"])
        self.assertEqual(projection["metadata"]["review_count"], 1)
        self.assertEqual(len(projection["reviews"][0]["evidence"]), 2)

    def test_browser_module_reads_only_analysis_projection(self):
        source = (ROOT / "web/analysis.js").read_text(encoding="utf-8")
        fetches = re.findall(r"fetch\((['\"])(.*?)\1", source)
        self.assertEqual([url for _, url in fetches], ["data/analysis.json"])
        for forbidden in ("data/canonical", "data/sources", "data/monitor", "method:'POST'", 'method:"POST"', "localStorage"):
            self.assertNotIn(forbidden, source)
        self.assertIn("Canonical write: OFF", source)
        self.assertIn("Movement ≠ cause", source)

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
