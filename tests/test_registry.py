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
        self.assertIn(self.reg["version"], {"0.20", "0.21"})
        self.assertEqual(self.reg["record_count"],669)
        if self.reg["version"] == "0.21":
            row=next(r for r in self.reg["records"] if r["occurrence_id"]=="WSO-EL-A-0004")
            self.assertEqual(row["source_id"], "WSSRC-EL-BR-002")
            self.assertEqual(row["start_local"], "2027-01-05")
            self.assertEqual(row["election_date_basis"], "CONSTITUTIONAL_RULE_DERIVED")
    def test_registry_validates(self):
        report=validate_registry(self.reg,self.src)
        self.assertTrue(report.ok, report.errors)
    def test_unique_occurrence_ids(self):
        ids=[r["occurrence_id"] for r in self.reg["records"]]
        self.assertEqual(len(ids),len(set(ids)))
    def test_google_calendar_not_canonical(self):
        self.assertNotIn("google_calendar", self.reg)

if __name__=="__main__": unittest.main()
