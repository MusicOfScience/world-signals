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

    def test_current_governed_counts_are_not_stale(self):
        self.assertEqual(self.derived["canonical"], {
            "registry_version": "0.41",
            "occurrence_count": 689,
            "schema_version": "0.52",
        })
        self.assertEqual(self.derived["sources"]["registry_version"], "2.02")
        self.assertEqual(self.derived["sources"]["source_count"], 257)
        self.assertEqual(self.derived["change_ledger"], {"version": "0.27", "entry_count": 62})
        self.assertEqual(self.derived["monitor"]["expectations_version"], "0.27")
        self.assertEqual(self.derived["monitor"]["configured_adapter_count"], 25)
        self.assertEqual(self.derived["monitor"]["unique_monitor_source_count"], 24)
        self.assertEqual(self.derived["monitor"]["explicit_scoped_occurrence_count"], 215)
        self.assertEqual(self.derived["live_intelligence"]["schema_version"], "0.7")
        self.assertEqual(self.derived["live_intelligence"]["observation_count"], 7)
        self.assertEqual(self.derived["live_intelligence"]["evidence_count"], 10)
        self.assertEqual(self.derived["live_intelligence"]["canonical_linked_observation_count"], 2)
        self.assertEqual(self.derived["analysis"]["schema_version"], "0.8")
        self.assertEqual(self.derived["analysis"]["review_count"], 22)
        self.assertEqual(self.derived["analysis"]["evidence_count"], 97)
        self.assertEqual(self.derived["analysis"]["production_live_input_count"], 1)
        self.assertEqual(self.derived["analysis"]["production_revision_count"], 1)

    def test_nhc_pilot_remains_validated_but_unregistered(self):
        nhc = self.derived["monitor"]["nhc_atlantic_pilot"]
        self.assertEqual(nhc["readiness_verdict"], "PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT")
        self.assertEqual(nhc["source_id"], "WSSRC-RISK-002")
        self.assertEqual(set(nhc["canonical_occurrence_ids"]), {"WSO-COM-A-0049", "WSO-COM-A-0050"})
        self.assertFalse(nhc["registered_in_expectations"])

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
