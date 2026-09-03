from pathlib import Path
import sys, copy, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.io import load_json
from world_signals.monitor import compare_assertion, protected_digest

class MonitorGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg=load_json(ROOT/"data/canonical/registry.json")
        cls.record=next(r for r in reg["records"] if r["occurrence_id"]=="WSO-MAC-B-0035")
    def test_no_change_returns_none(self):
        a={"start_local":self.record["start_local"],"certainty_status":self.record["certainty_status"],"lifecycle_status":self.record["lifecycle_status"]}
        self.assertIsNone(compare_assertion(self.record,a))
    def test_changed_date_is_review_only(self):
        before=protected_digest(self.record)
        a={"start_local":"2026-09-12T07:00:00","certainty_status":"CONFIRMED","lifecycle_status":"PLANNED"}
        c=compare_assertion(self.record,a)
        self.assertIsNotNone(c)
        self.assertEqual(c.diff_type,"DATE_OR_TIME_CHANGED")
        self.assertFalse(c.automatic_commit_allowed)
        self.assertEqual(before,protected_digest(self.record))
    def test_elapsed_or_absence_is_not_cancellation(self):
        # No assertion means monitor engine has nothing to compare; it cannot invent CANCELLED.
        self.assertIsNone(compare_assertion(self.record,{}))

if __name__=="__main__": unittest.main()
