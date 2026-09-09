from __future__ import annotations
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SARBActivationCBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads((ROOT/'data/canonical/registry.json').read_text()); cls.s=json.loads((ROOT/'data/sources/registry.json').read_text()); cls.e=json.loads((ROOT/'data/monitor/expectations.json').read_text())
    def test_governed_counts(self):
        self.assertEqual((self.c['version'],len(self.c['records'])),('0.41',689)); self.assertEqual((self.s['version'],len(self.s['sources'])),('2.01',256)); self.assertEqual((self.e['version'],len(self.e['adapters'])),('0.26',24))
    def test_canonical_source_stays_held(self):
        x=next(x for x in self.s['sources'] if x.get('source_id')=='WSSRC-REG-006'); self.assertEqual(x['automated_monitoring_use'],'PROHIBITED_OR_RIGHTS_HOLD'); self.assertEqual(x['verification_mode'],'RIGHTS_HELD_MANUAL_ONLY')
    def test_monitor_source_and_route(self):
        src=next(x for x in self.s['sources'] if x.get('source_id')=='WSSRC-REG-013'); route=next(x for x in self.e['adapters'] if x.get('adapter_id')=='SARB_MPC_STATEMENTS_RSS')
        self.assertEqual(src['canonical_dependency_count'],0); self.assertEqual(src['related_source_ids'],['WSSRC-REG-006']); self.assertEqual(route['canonical_occurrence_ids'],['WSO-REG-A-0009','WSO-REG-A-0010']); self.assertEqual(route['request_budget_per_run'],1)
        for k in ('schedule_authority','clock_authority','lifecycle_authority','certainty_authority','canonical_datetime_mutation_allowed','automatic_item_link_fetch_allowed','automatic_schedule_fetch_allowed','automatic_new_occurrence_creation_allowed','automatic_live_or_analysis_promotion_allowed','automatic_commit_allowed'): self.assertIs(route[k],False,k)
        self.assertIs(self.e['automatic_canonical_commit'],False); self.assertIs(self.e['google_calendar_write'],False)
if __name__=='__main__': unittest.main()
