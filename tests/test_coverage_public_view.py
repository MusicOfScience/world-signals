from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.coverage import build_coverage_audit
from world_signals.coverage_public import public_coverage_projection


class PublicCoverageViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
        cls.sources = json.loads((ROOT / "data/sources/registry.json").read_text(encoding="utf-8"))
        cls.audit = build_coverage_audit(cls.registry, cls.sources)
        cls.public = public_coverage_projection(cls.audit)

    def test_projection_is_aggregate_only(self):
        self.assertEqual(self.public["dataset"], "PUBLIC_COVERAGE_PROJECTION")
        self.assertNotIn("focus_inventory", self.public)
        self.assertNotIn("by_institution", self.public)
        self.assertNotIn("source_readiness", self.public)
        self.assertNotIn("records", self.public)
        self.assertFalse(self.public["metadata"]["canonical_mutation_authority"])
        self.assertFalse(self.public["metadata"]["population_quota_authority"])

    def test_projection_preserves_current_mechanical_truth(self):
        totals = self.audit["totals"]
        metadata = self.public["metadata"]
        self.assertEqual(metadata["canonical_registry_version"], self.registry["version"])
        self.assertEqual(metadata["occurrence_count"], totals["occurrence_count"])
        self.assertEqual(metadata["unique_series_count"], totals["unique_series_count"])
        self.assertEqual(metadata["unique_institution_count"], totals["unique_institution_count"])
        self.assertEqual(metadata["unique_source_count"], totals["unique_source_count"])
        self.assertEqual(metadata["monetary_plus_macro_occurrence_share"], totals["monetary_plus_macro_occurrence_share"])

    def test_high_frequency_projection_is_bounded_and_non_occurrence_level(self):
        self.assertLessEqual(len(self.public["high_frequency_series"]), 12)
        for row in self.public["high_frequency_series"]:
            self.assertEqual(
                set(row),
                {"series_id", "occurrence_count", "region", "category", "institution"},
            )
            self.assertNotIn("occurrence_id", row)
            self.assertNotIn("source_id", row)

    def test_browser_view_is_read_only_and_build_bundles_it(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        js = (ROOT / "web/coverage.js").read_text(encoding="utf-8")
        build = (ROOT / "scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn('id="coverageTab"', html)
        self.assertIn('id="coverageView"', html)
        self.assertIn('coverage.js', html)
        self.assertIn('coverage.css', html)
        self.assertIn("data/coverage.json", build)
        self.assertIn("public_coverage_projection", build)
        self.assertIn("fetch('data/coverage.json'", js)
        upper = js.upper()
        for forbidden in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertNotIn(forbidden, upper)
        lower = js.lower()
        for forbidden in ("canonical write", "google calendar write"):
            self.assertNotIn(forbidden, lower)


if __name__ == "__main__":
    unittest.main()
