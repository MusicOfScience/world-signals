from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.monitor_coverage import build_monitor_coverage_audit


class MonitorCoverageAuditTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "version": "test-registry",
            "records": [
                {"occurrence_id": "O1", "series_id": "S1", "region": "Region A", "category": "CAT_A", "institution": "Inst A", "source_id": "SRC1"},
                {"occurrence_id": "O2", "series_id": "S1", "region": "Region A", "category": "CAT_A", "institution": "Inst A", "source_id": "SRC1"},
                {"occurrence_id": "O3", "series_id": "S2", "region": "Region B", "category": "CAT_B", "institution": "Inst B", "source_id": "SRC2"},
                {"occurrence_id": "O4", "series_id": "S3", "region": "Region C", "category": "CAT_C", "institution": "Inst C", "source_id": "SRC3"},
            ],
        }
        self.sources = {
            "version": "test-sources",
            "sources": [
                {"source_id": "SRC1", "institution": "Inst A", "monitoring_readiness_status": "PILOT_VALIDATED_NO_AUTO_COMMIT", "automated_monitoring_use": "CLEARED", "verification_mode": "AUTOMATED_PILOT"},
                {"source_id": "SRC2", "institution": "Inst B", "monitoring_readiness_status": "PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE"},
                {"source_id": "SRC3", "institution": "Inst C", "monitoring_readiness_status": "RIGHTS_OR_LICENSE_HOLD"},
                {"source_id": "SRC4", "institution": "Unbound", "monitoring_readiness_status": "ENDPOINT_TEST_PRIORITY"},
            ],
        }
        self.expectations = {
            "version": "test-monitor",
            "adapters": [
                {
                    "adapter_id": "A1",
                    "source_id": "SRC1",
                    "canonical_occurrence_ids": ["O1"],
                    "monitor_role": "TEST_SENTINEL",
                    "cadence": "DAILY",
                }
            ],
        }

    def test_explicit_scope_does_not_expand_to_same_series(self):
        audit = build_monitor_coverage_audit(self.registry, self.sources, self.expectations)
        self.assertEqual(audit["totals"]["scoped_occurrence_count"], 1)
        self.assertEqual(audit["totals"]["scoped_series_count"], 1)
        self.assertEqual(audit["adapter_inventory"][0]["explicit_canonical_occurrence_ids"], ["O1"])
        self.assertNotIn("O2", audit["adapter_inventory"][0]["explicit_canonical_occurrence_ids"])
        self.assertTrue(audit["methodology"]["explicit_occurrence_scope_only_no_series_inference"])

    def test_missing_regions_and_categories_are_prompts_not_quotas(self):
        audit = build_monitor_coverage_audit(self.registry, self.sources, self.expectations)
        prompts = audit["diagnostic_prompts"]
        self.assertEqual(prompts["canonical_regions_without_configured_monitor_scope"], ["Region B", "Region C"])
        self.assertEqual(prompts["canonical_categories_without_configured_monitor_scope"], ["CAT_B", "CAT_C"])
        self.assertTrue(audit["methodology"]["missing_region_or_category_is_review_prompt_not_quota"])
        self.assertNotIn("coverage_percentage", audit["totals"])

    def test_source_readiness_is_descriptive_not_route_authority(self):
        audit = build_monitor_coverage_audit(self.registry, self.sources, self.expectations)
        configured = audit["configured_source_readiness"]
        self.assertEqual(configured["monitoring_readiness_status_counts"], {"PILOT_VALIDATED_NO_AUTO_COMMIT": 1})
        self.assertFalse(audit["methodology"]["automatic_adapter_enablement"])
        self.assertFalse(audit["methodology"]["automatic_canonical_commit"])
        self.assertTrue(audit["methodology"]["source_readiness_and_rights_govern_route_viability"])

    def test_candidate_sources_require_current_canonical_dependency_for_coverage_pool(self):
        audit = build_monitor_coverage_audit(self.registry, self.sources, self.expectations)
        bound = {row["source_id"] for row in audit["candidate_sources_with_canonical_dependencies"]}
        unbound = {row["source_id"] for row in audit["candidate_sources_without_canonical_dependencies"]}
        self.assertIn("SRC2", bound)
        self.assertIn("SRC4", unbound)
        row = next(row for row in audit["candidate_sources_without_canonical_dependencies"] if row["source_id"] == "SRC4")
        self.assertEqual(row["candidate_class"], "UNBOUND_SOURCE_REGISTRY_HOLDING_NOT_MONITOR_COVERAGE")

    def test_unknown_configured_occurrence_fails_closed(self):
        expectations = copy.deepcopy(self.expectations)
        expectations["adapters"][0]["canonical_occurrence_ids"] = ["MISSING"]
        with self.assertRaisesRegex(ValueError, "unknown canonical occurrence"):
            build_monitor_coverage_audit(self.registry, self.sources, expectations)

    def test_unknown_configured_source_fails_closed(self):
        expectations = copy.deepcopy(self.expectations)
        expectations["adapters"][0]["source_id"] = "MISSING"
        with self.assertRaisesRegex(ValueError, "absent from source registry"):
            build_monitor_coverage_audit(self.registry, self.sources, expectations)

    def test_duplicate_adapter_or_scope_identity_fails_closed(self):
        expectations = copy.deepcopy(self.expectations)
        expectations["adapters"].append(copy.deepcopy(expectations["adapters"][0]))
        with self.assertRaisesRegex(ValueError, "adapter ids must be unique"):
            build_monitor_coverage_audit(self.registry, self.sources, expectations)

        expectations = copy.deepcopy(self.expectations)
        expectations["adapters"][0]["canonical_occurrence_ids"] = ["O1", "O1"]
        with self.assertRaisesRegex(ValueError, "scope contains duplicates"):
            build_monitor_coverage_audit(self.registry, self.sources, expectations)

    def test_live_projection_is_read_only_and_matches_configured_route_identity(self):
        registry = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
        sources = json.loads((ROOT / "data/sources/registry.json").read_text(encoding="utf-8"))
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text(encoding="utf-8"))
        before = (copy.deepcopy(registry), copy.deepcopy(sources), copy.deepcopy(expectations))
        audit = build_monitor_coverage_audit(registry, sources, expectations)
        self.assertEqual(audit["totals"]["configured_adapter_count"], len(expectations.get("adapters", [])))
        self.assertEqual({row["adapter_id"] for row in audit["adapter_inventory"]}, {row["adapter_id"] for row in expectations.get("adapters", [])})
        self.assertEqual((registry, sources, expectations), before)
        self.assertFalse(audit["methodology"]["automatic_adapter_enablement"])
        self.assertFalse(audit["methodology"]["automatic_canonical_commit"])


if __name__ == "__main__":
    unittest.main()
