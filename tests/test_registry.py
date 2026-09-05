from pathlib import Path
import sys, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.io import load_json
from world_signals.validation import validate_registry

class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg=load_json(ROOT/"data/canonical/registry.json")
        cls.src=load_json(ROOT/"data/sources/registry.json")
    def test_checkpoint_count(self):
        version=tuple(int(p) for p in str(self.reg["version"]).split("."))
        self.assertGreaterEqual(version,(0,20))
        expected_counts={"0.26":669,"0.27":673,"0.28":674}
        if self.reg["version"] in expected_counts:
            self.assertEqual(self.reg["record_count"],expected_counts[self.reg["version"]])
        else:
            self.assertEqual(self.reg["record_count"],len(self.reg["records"]),"unknown checkpoint must remain internally consistent")
        if version >= (0,21):
            row=next(r for r in self.reg["records"] if r["occurrence_id"]=="WSO-EL-A-0004")
            self.assertEqual(row["source_id"], "WSSRC-EL-BR-002")
            self.assertEqual(row["start_local"], "2027-01-05")
            self.assertEqual(row["election_date_basis"], "CONSTITUTIONAL_RULE_DERIVED")
        if version >= (0,22):
            row=next(r for r in self.reg["records"] if r["occurrence_id"]=="WSO-REG-G-0001")
            self.assertEqual(row["source_id"], "WSSRC-REG5-002")
            self.assertEqual(row["start_local"], "2026-10-20")
            self.assertEqual(row["certainty_status"], "PROVISIONAL")
        if version >= (0,27):
            ids={r["occurrence_id"] for r in self.reg["records"]}
            self.assertTrue({"WSO-CBN-MPC-307","WSO-CBN-MPC-308","WSO-BWC-WG-2026-S10","WSO-WOAH-GS-094"}.issubset(ids))
        if version >= (0,28):
            row=next(r for r in self.reg["records"] if r["occurrence_id"]=="WSO-FIS-NP-BUDGET-2084")
            self.assertEqual(row["source_native_date_label"],"15 Jestha 2084")
            self.assertEqual(row["gregorian_resolution_status"],"UNRESOLVED_AUTHORITATIVE_CONVERSION")
            self.assertIsNone(row["start_local"])
            self.assertIsNone(row["date_earliest"])
    def test_registry_validates(self):
        report=validate_registry(self.reg,self.src)
        self.assertTrue(report.ok, report.errors)
    def test_unique_occurrence_ids(self):
        ids=[r["occurrence_id"] for r in self.reg["records"]]
        self.assertEqual(len(ids),len(set(ids)))
    def test_google_calendar_not_canonical(self):
        self.assertNotIn("google_calendar", self.reg)

if __name__=="__main__": unittest.main()
