from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/project_state_snapshot.py"
SPEC = importlib.util.spec_from_file_location("project_state_snapshot", MODULE_PATH)
assert SPEC and SPEC.loader
state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state)


class ProjectStateSnapshotCHTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.derived = state.build_snapshot()
        cls.checked_in = json.loads((ROOT / "data/status/current_state.json").read_text(encoding="utf-8"))

    def test_checked_in_snapshot_is_exact_derivation(self):
        self.assertEqual(self.checked_in, self.derived)

    def test_governed_state_is_at_least_ch_checkpoint(self):
        vt = lambda value: tuple(int(part) for part in str(value).split("."))
        self.assertGreaterEqual(vt(self.derived["canonical"]["registry_version"]), (0, 41))
        self.assertGreaterEqual(self.derived["canonical"]["occurrence_count"], 689)
        self.assertGreaterEqual(vt(self.derived["canonical"]["schema_version"]), (0, 52))
        self.assertGreaterEqual(vt(self.derived["sources"]["registry_version"]), (2, 2))
        self.assertGreaterEqual(self.derived["sources"]["source_count"], 257)
        self.assertGreaterEqual(vt(self.derived["change_ledger"]["version"]), (0, 27))
        self.assertGreaterEqual(self.derived["change_ledger"]["entry_count"], 62)
        self.assertGreaterEqual(vt(self.derived["monitor"]["expectations_version"]), (0, 27))
        self.assertGreaterEqual(self.derived["monitor"]["configured_adapter_count"], 25)
        self.assertGreaterEqual(self.derived["monitor"]["unique_monitor_source_count"], 24)
        self.assertGreaterEqual(self.derived["monitor"]["explicit_scoped_occurrence_count"], 215)
        self.assertGreaterEqual(vt(self.derived["live_intelligence"]["schema_version"]), (0, 7))
        self.assertGreaterEqual(self.derived["live_intelligence"]["observation_count"], 7)
        self.assertGreaterEqual(self.derived["live_intelligence"]["evidence_count"], 10)
        self.assertGreaterEqual(self.derived["live_intelligence"]["canonical_linked_observation_count"], 2)
        self.assertGreaterEqual(vt(self.derived["analysis"]["schema_version"]), (0, 8))
        self.assertGreaterEqual(self.derived["analysis"]["review_count"], 22)
        self.assertGreaterEqual(self.derived["analysis"]["evidence_count"], 97)
        self.assertGreaterEqual(self.derived["analysis"]["production_live_input_count"], 1)
        self.assertGreaterEqual(self.derived["analysis"]["production_revision_count"], 1)

    def test_nhc_pilot_history_allows_only_reviewed_bounded_registration(self):
        nhc = self.derived["monitor"]["nhc_atlantic_pilot"]
        self.assertEqual(nhc["readiness_verdict"], "PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT")
        self.assertEqual(nhc["source_id"], "WSSRC-RISK-002")
        self.assertEqual(set(nhc["canonical_occurrence_ids"]), {"WSO-COM-A-0049", "WSO-COM-A-0050"})
        if not nhc["registered_in_expectations"]:
            return
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text(encoding="utf-8"))
        routes = [row for row in expectations["adapters"] if row.get("adapter_id") == "NHC_ATLANTIC_SEASON"]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(route["source_id"], "WSSRC-RISK-002")
        self.assertEqual(route["canonical_occurrence_ids"], ["WSO-COM-A-0049", "WSO-COM-A-0050"])
        self.assertEqual(route["cadence"], "DAILY")
        self.assertEqual(route["endpoint"]["request_budget_per_run"], 2)
        self.assertEqual(route["baseline"]["start_month_day"], "06-01")
        self.assertEqual(route["baseline"]["end_month_day"], "11-30")
        for gate in (
            "schedule_authority", "lifecycle_authority", "certainty_authority",
            "canonical_date_mutation_allowed", "automatic_new_occurrence_creation_allowed",
            "automatic_live_or_analysis_promotion_allowed", "automatic_commit_allowed",
        ):
            self.assertFalse(route[gate], gate)
        sources = json.loads((ROOT / "data/sources/registry.json").read_text(encoding="utf-8"))
        source = [row for row in sources["sources"] if row.get("source_id") == "WSSRC-RISK-002"]
        self.assertEqual(len(source), 1)
        self.assertEqual(source[0]["automated_monitoring_use"], "CLEARED")
        self.assertEqual(source[0]["monitoring_readiness_status"], "PILOT_VALIDATED_NO_AUTO_COMMIT")
        self.assertIn("READ_ONLY_SENTINEL_ONLY", source[0]["automated_monitoring_scope"])

    def test_all_write_and_public_projection_gates_remain_closed(self):
        gates = self.derived["write_gates"]
        self.assertFalse(gates["automatic_canonical_commit"])
        self.assertFalse(gates["google_calendar_write"])
        self.assertFalse(gates["monitor_may_mutate_canonical"])
        self.assertFalse(gates["live_automatic_ingestion_allowed"])
        self.assertFalse(gates["live_public_projection_allowed"])
        self.assertTrue(self.derived["live_intelligence"]["all_observation_auto_commit_gates_closed"])
        self.assertTrue(self.derived["live_intelligence"]["all_observation_calendar_write_gates_closed"])
        self.assertFalse(self.derived["analysis"]["public_live_input_projection_allowed"])
        self.assertFalse(self.derived["analysis"]["public_revision_metadata_projection_allowed"])
        self.assertFalse(self.derived["analysis"]["automatic_latest_analysis_selection_allowed"])

    def test_derived_surface_is_explicitly_noncanonical(self):
        policy = self.derived["derivation_policy"]
        self.assertTrue(policy["governed_registries_and_contracts_remain_authoritative"])
        self.assertTrue(policy["snapshot_is_not_canonical_state"])
        self.assertTrue(policy["snapshot_is_not_calendar_state"])
        self.assertTrue(policy["snapshot_is_not_monitor_runtime_evidence"])
        self.assertTrue(policy["snapshot_may_not_mutate_upstream_layers"])

    def test_opec_quarantine_remains_present(self):
        self.assertTrue(self.derived["quarantine"]["opec_quarantine_record_present"])

    def test_all_three_current_state_blocks_match_the_derivation(self):
        self.assertEqual(state.check_documents(self.derived), [])


if __name__ == "__main__":
    unittest.main()
