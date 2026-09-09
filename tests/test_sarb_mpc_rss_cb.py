from __future__ import annotations

import copy, json, unittest
from pathlib import Path

from world_signals.adapters.base import AdapterError
from world_signals.adapters.sarb_rss import parse_sarb_publications_rss
from world_signals.sarb_mpc_monitor import sarb_mpc_rss_review_candidates

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"data/monitor/SARB_MPC_RSS_CB_PLAN_v0.1.json").read_text())
CANONICAL=json.loads((ROOT/"data/canonical/registry.json").read_text())
EXPECT=json.loads((ROOT/"data/monitor/expectations.json").read_text())
CONFIG=next(x for x in EXPECT["adapters"] if x.get("adapter_id")=="SARB_MPC_STATEMENTS_RSS")

def xml(items):
    payload="".join(f"<item><title>{x['title']}</title><link>{x['link']}</link><description>{x.get('description','')}</description><pubDate>{x['pubDate']}</pubDate><category>{x['category']}</category><guid>{x['guid']}</guid></item>" for x in items)
    return f"<rss><channel>{payload}</channel></rss>"

def target(month='September',date='2026-09-23T13:00:00Z'):
    low=month.lower()
    return {'title':f'Statement of the Monetary Policy Committee {month} 2026','link':f'/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2026/{low}','pubDate':date,'category':"Media &gt; Media Releases | Statements &gt; Monetary Policy Statements | What's New",'guid':f'/content/sarb-project/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2026/{low}'}

class SARBRSSCBTests(unittest.TestCase):
    def test_parser_classifies_exact_mpc_identity(self):
        items=parse_sarb_publications_rss(xml([target()]))
        self.assertEqual((items[0].mpc_year,items[0].mpc_month,items[0].mpc_month_name),(2026,9,'September'))

    def test_parser_allows_non_mpc_publication(self):
        item={'title':'Working paper','link':'/en/home/publications/publication-detail-pages/working-papers/2026/example','pubDate':'2026-09-09T08:00:00Z','category':'Working Papers','guid':'/content/sarb-project/en/home/publications/publication-detail-pages/working-papers/2026/example'}
        parsed=parse_sarb_publications_rss(xml([item]))
        self.assertIsNone(parsed[0].mpc_year)

    def test_parser_fails_closed_on_mpc_title_drift(self):
        bad=target(); bad['title']='Monetary Policy Committee statement September 2026'
        with self.assertRaises(AdapterError): parse_sarb_publications_rss(xml([bad]))

    def test_parser_fails_closed_on_mpc_path_drift(self):
        bad=target(); bad['link']='/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2026/wrong'
        with self.assertRaises(AdapterError): parse_sarb_publications_rss(xml([bad]))

    def test_exact_publication_generates_review_only_candidate(self):
        items=parse_sarb_publications_rss(xml([target()]))
        candidates,obs=sarb_mpc_rss_review_candidates(CANONICAL['records'],items,CONFIG)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]['candidate_type'],'SARB_MPC_STATEMENT_PUBLICATION_EVIDENCE')
        self.assertFalse(candidates[0]['automatic_commit_allowed'])
        self.assertFalse(candidates[0]['canonical_datetime_mutation_allowed'])

    def test_different_publication_date_is_review_not_mutation(self):
        items=parse_sarb_publications_rss(xml([target(date='2026-09-24T08:00:00Z')]))
        candidates,_=sarb_mpc_rss_review_candidates(CANONICAL['records'],items,CONFIG)
        self.assertEqual(candidates[0]['candidate_type'],'SARB_MPC_PUBLICATION_DATE_MISMATCH_REVIEW')
        self.assertFalse(candidates[0]['automatic_commit_allowed'])

    def test_absence_has_no_event_state_semantics(self):
        ordinary={'title':'Working paper','link':'/en/home/publications/publication-detail-pages/working-papers/2026/example','pubDate':'2026-09-09T08:00:00Z','category':'Working Papers','guid':'/content/sarb-project/en/home/publications/publication-detail-pages/working-papers/2026/example'}
        items=parse_sarb_publications_rss(xml([ordinary]))
        candidates,obs=sarb_mpc_rss_review_candidates(CANONICAL['records'],items,CONFIG)
        self.assertEqual(candidates,[])
        self.assertEqual(obs[-1]['matched_occurrence_count'],0)
        self.assertEqual(obs[-1]['event_state_inference'],'NONE')

    def test_completed_occurrence_gets_observation_only(self):
        records=copy.deepcopy(CANONICAL['records'])
        next(r for r in records if r.get('occurrence_id')=='WSO-REG-A-0009')['lifecycle_status']='COMPLETED'
        items=parse_sarb_publications_rss(xml([target()]))
        candidates,obs=sarb_mpc_rss_review_candidates(records,items,CONFIG)
        self.assertEqual(candidates,[])
        self.assertTrue(any(x['type'].startswith('SARB_COMPLETED') for x in obs))

if __name__=='__main__': unittest.main()
