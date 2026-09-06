from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import parse_eia_wpsr_schedule_html
from world_signals.live_monitor import eia_wpsr_schedule_review_candidate

HTML=b'''<p>The wpsrsummary.pdf, overview.pdf, and Tables 1-14 in CSV and XLS formats, are released to the web site after 10:30 a.m. eastern time on Wednesday.</p>
<table><tr><th>Data for the week ending</th><th>Alternate release date</th><th>Release day</th><th>Release time</th><th>Holiday</th></tr>
<tr><td>September 4, 2026</td><td>September 10, 2026</td><td>Thursday</td><td>12:00 p.m.</td><td>Labor Day</td></tr></table>'''


class EIAWPSRMonitorTests(unittest.TestCase):
    def setUp(self):
        self.rule=parse_eia_wpsr_schedule_html(HTML)
        self.config={
            "adapter_id":"EIA_WPSR_SCHEDULE",
            "source_id":"WSSRC-COM-003",
            "canonical_occurrence_ids":["O1","O2"],
            "baseline":{
                "schedule_sha256":self.rule.schedule_sha256,
                "schedule":self.rule.as_dict(),
            },
            "automatic_commit_allowed":False,
        }

    def test_unchanged_schedule_yields_observation_only(self):
        candidate,observation=eia_wpsr_schedule_review_candidate(self.rule,self.config)
        self.assertIsNone(candidate)
        self.assertEqual(observation["type"],"EIA_WPSR_SCHEDULE_NO_CHANGE")
        self.assertEqual(observation["completion_inference"],"PROHIBITED")

    def test_changed_schedule_is_review_only_and_scoped(self):
        changed=deepcopy(self.rule.as_dict())
        changed["standard_release_time_local"]="11:00"
        changed["schedule_sha256"]="changed-semantic-hash"
        candidate,observation=eia_wpsr_schedule_review_candidate(changed,self.config)
        self.assertEqual(observation["type"],"EIA_WPSR_SCHEDULE_CHANGED")
        self.assertEqual(candidate["candidate_type"],"PUBLICATION_SCHEDULE_RULE_OR_EXCEPTION_CHANGED")
        self.assertEqual(candidate["occurrence_ids"],["O1","O2"])
        self.assertEqual(candidate["completion_inference"],"PROHIBITED")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertNotIn("lifecycle_status",candidate["new_value"])

    def test_missing_baseline_fails_to_review_candidate_not_silent_no_change(self):
        config=deepcopy(self.config)
        config["baseline"]={}
        candidate,observation=eia_wpsr_schedule_review_candidate(self.rule,config)
        self.assertEqual(observation["type"],"EIA_WPSR_SCHEDULE_CHANGED")
        self.assertIsNotNone(candidate)


if __name__=="__main__":
    unittest.main()
