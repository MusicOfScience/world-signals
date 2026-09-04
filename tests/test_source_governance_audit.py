import unittest

from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.source_governance_audit import build_source_governance_audit


class SourceGovernanceAuditTests(unittest.TestCase):
    def setUp(self):
        self.registry={"version":"r","records":[
            {"occurrence_id":"O1","source_id":"S1"},
            {"occurrence_id":"O2","source_id":"S1"},
            {"occurrence_id":"O3","source_id":"S2"},
        ]}
        self.sources={"version":"s","sources":[
            {"source_id":"S1","institution":"A","machine_readable_available":True},
            {"source_id":"S2","institution":"B","canonical_provenance_use":"MANUAL_RESEARCH_ONLY"},
            {"source_id":"S3","institution":"C","canonical_provenance_use":"CLEARED_CURATED_FACTUAL_METADATA","automated_monitoring_use":"CLEARED","verification_mode":"LIVE_ENDPOINT","monitoring_readiness_status":"PILOT_VALIDATED_NO_AUTO_COMMIT"},
            {"source_id":"S4","institution":"D","machine_readable_available":True},
        ]}
        self.expectations={"version":"e","adapters":[{"adapter_id":"A1","source_id":"S1"}]}

    def test_priority_follows_operational_dependency(self):
        audit=build_source_governance_audit(self.registry,self.sources,self.expectations)
        rows={row["source_id"]:row for row in audit["backfill_research_queue"]}
        self.assertEqual(rows["S1"]["research_priority"],"P0_CONFIGURED_MONITOR_DEPENDENCY")
        self.assertEqual(rows["S2"]["research_priority"],"P1_CANONICAL_DEPENDENCY")
        self.assertEqual(rows["S4"]["research_priority"],"P2_REGISTRY_ONLY")
        self.assertEqual(rows["S1"]["canonical_occurrence_dependency_count"],2)

    def test_machine_readability_never_infers_permission(self):
        audit=build_source_governance_audit(self.registry,self.sources,self.expectations)
        s1=next(row for row in audit["backfill_research_queue"] if row["source_id"]=="S1")
        self.assertTrue(s1["machine_readable_available"])
        self.assertEqual(s1["permission_inference"],"PROHIBITED_BY_AUDIT_METHOD")
        self.assertTrue(audit["methodology"]["permission_inference_from_machine_readability_prohibited"])

    def test_fully_explicit_source_is_not_in_backfill_queue(self):
        audit=build_source_governance_audit(self.registry,self.sources,self.expectations)
        self.assertNotIn("S3",{row["source_id"] for row in audit["backfill_research_queue"]})
        self.assertEqual(audit["totals"]["fully_explicit_governance_source_count"],1)

    def test_missing_fields_are_described_not_filled(self):
        audit=build_source_governance_audit(self.registry,self.sources,self.expectations)
        s2=next(row for row in audit["backfill_research_queue"] if row["source_id"]=="S2")
        self.assertNotIn("canonical_provenance_use",s2["missing_governance_fields"])
        self.assertIn("automated_monitoring_use",s2["missing_governance_fields"])
        self.assertNotIn("recommended_automated_monitoring_use",s2)
        self.assertNotIn("recommended_canonical_provenance_use",s2)


if __name__=="__main__":
    unittest.main()
