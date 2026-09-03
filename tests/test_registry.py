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
        self.assertEqual(self.reg["version"],"0.18")
        self.assertEqual(self.reg["record_count"],662)
    def test_registry_validates(self):
        report=validate_registry(self.reg,self.src)
        self.assertTrue(report.ok, report.errors)
    def test_unique_occurrence_ids(self):
        ids=[r["occurrence_id"] for r in self.reg["records"]]
        self.assertEqual(len(ids),len(set(ids)))
    def test_google_calendar_not_canonical(self):
        self.assertNotIn("google_calendar", self.reg)

if __name__=="__main__": unittest.main()
