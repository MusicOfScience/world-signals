from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.io import load_json
from world_signals.operations import operations_projection


class OperationsProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg=load_json(ROOT/"data/canonical/registry.json")
        src=load_json(ROOT/"data/sources/registry.json")
        exp=load_json(ROOT/"data/monitor/expectations.json")
        policy=load_json(ROOT/"data/monitor/operations_policy.json")
        changes=load_json(ROOT/"data/changes/ledger.json")
        cls.reg=reg
        cls.src=src
        cls.exp=exp
        cls.ops=operations_projection(reg,src,exp,policy,changes)

    def test_projection_matches_current_checkpoint(self):
        meta=self.ops["metadata"]
        self.assertEqual(meta["canonical_registry_version"],self.reg["version"])
        self.assertEqual(meta["canonical_record_count"],self.reg["record_count"])
        self.assertEqual(meta["source_registry_version"],self.src["version"])
        self.assertEqual(meta["source_count"],len(self.src["sources"]))
        self.assertEqual(meta["configured_monitor_route_count"],len(self.exp["adapters"]))

    def test_static_projection_never_claims_runtime_health(self):
        meta=self.ops["metadata"]
        self.assertFalse(meta["runtime_health_embedded"])
        self.assertFalse(meta["pending_review_queue_embedded"])
        self.assertFalse(meta["automatic_canonical_commit"])
        self.assertFalse(meta["google_calendar_write"])
        for route in self.ops["configured_routes"]:
            self.assertNotIn("runtime_health_state",route)
            self.assertNotIn("current_health",route)

    def test_unrecorded_governance_is_not_treated_as_permission(self):
        summary=self.ops["source_governance_summary"]["automated_monitoring_use"]
        missing=sum(1 for source in self.src["sources"] if not source.get("automated_monitoring_use"))
        self.assertEqual(summary.get("NOT_RECORDED_IN_REGISTRY",0),missing)

    def test_fiji_source_remains_rights_held_and_not_a_live_route(self):
        fiji=[source for source in self.ops["sources"] if source.get("source_id")=="WSSRC-RISK-004"]
        self.assertEqual(len(fiji),1)
        self.assertEqual(fiji[0]["canonical_provenance_use"],"MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(fiji[0]["automated_monitoring_use"],"PROHIBITED_OR_RIGHTS_HOLD")
        self.assertFalse(any(route.get("source_id")=="WSSRC-RISK-004" for route in self.ops["configured_routes"]))


if __name__=="__main__":
    unittest.main()
