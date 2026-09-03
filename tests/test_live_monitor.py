from pathlib import Path
from types import SimpleNamespace
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.live_monitor import (
    colombia_legal_input_review_candidate,
    cra_legal_rule_review_candidate,
    rba_fsr_review_candidates,
    stable_hash,
)


class LiveMonitorTests(unittest.TestCase):
    def setUp(self):
        self.rba_record={
            "occurrence_id":"WSO-FIN-B-0001",
            "series_id":"WSER-FIN-B-RBA-FSR",
            "canonical_name":"RBA Financial Stability Review — October 2026",
            "category":"FINANCIAL_STABILITY_REGULATION",
            "jurisdiction":"Australia",
            "institution":"Reserve Bank of Australia",
            "source_id":"WSSRC-FIN-001",
            "start_local":"2026-10-01T11:30:00",
            "end_local":None,
            "certainty_status":"CONFIRMED",
            "lifecycle_status":"PLANNED",
        }
        self.rba_config={
            "source_id":"WSSRC-FIN-001",
            "canonical_occurrence_ids":["WSO-FIN-B-0001"],
            "matching":{"nearest_planned_occurrence_max_days":75},
        }
        self.cra_baseline={
            "celex":"32024R2847",
            "article":"71",
            "general_application_date":"2027-12-11",
            "article_14_application_date":"2026-09-11",
            "chapter_iv_application_date":"2026-06-11",
            "rule_sha256":"39f90548d36ac5b3ea301034e07201464edccc5412a026b3777e0f8217a0615f",
        }
        self.cra_config={
            "source_id":"WSSRC-TECH-001",
            "canonical_occurrence_ids":["WSO-TECH-A-0001","WSO-TECH-A-0007"],
            "baseline":{
                "rule":self.cra_baseline.copy(),
                "rule_sha256":self.cra_baseline["rule_sha256"],
            },
        }

    def test_rba_historical_item_does_not_touch_future_occurrence(self):
        item=SimpleNamespace(
            title="Financial Stability Review - March 2026",
            link="https://www.rba.gov.au/publications/fsr/2026/mar/",
            pub_date_iso="2026-03-19T11:30:00+11:00",
        )
        candidates,obs=rba_fsr_review_candidates([self.rba_record],[item],self.rba_config)
        self.assertEqual(candidates,[])
        self.assertEqual(obs[0]["type"],"RBA_PUBLICATION_UNMATCHED")

    def test_rba_positive_publication_generates_review_candidate_only(self):
        item=SimpleNamespace(
            title="Financial Stability Review - October 2026",
            link="https://www.rba.gov.au/publications/fsr/2026/oct/",
            pub_date_iso="2026-10-01T11:30:00+10:00",
        )
        candidates,_=rba_fsr_review_candidates([self.rba_record],[item],self.rba_config)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["diff_type"],"LIFECYCLE_CHANGED")
        self.assertFalse(candidates[0]["automatic_commit_allowed"])
        self.assertEqual(self.rba_record["lifecycle_status"],"PLANNED")

    def test_rba_moved_publication_date_is_review_candidate_not_mutation(self):
        item=SimpleNamespace(
            title="Financial Stability Review - October 2026",
            link="https://www.rba.gov.au/publications/fsr/2026/oct/",
            pub_date_iso="2026-10-02T11:30:00+10:00",
        )
        candidates,_=rba_fsr_review_candidates([self.rba_record],[item],self.rba_config)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["diff_type"],"DATE_OR_TIME_CHANGED")
        self.assertEqual(self.rba_record["start_local"],"2026-10-01T11:30:00")

    def test_colombia_unchanged_baseline(self):
        baseline={
            "tipo":"DECRETO","n_mero":"111","a_o":"1996",
            "vigencia":"Vigente","art_culos":"130",
        }
        config={
            "source_id":"WSSRC-REG4-001",
            "canonical_occurrence_ids":["WSO-REG-D-0001"],
            "baseline":{"critical_fields":baseline,"critical_fields_sha256":stable_hash(baseline)},
        }
        candidate,obs=colombia_legal_input_review_candidate([baseline.copy()],config)
        self.assertIsNone(candidate)
        self.assertEqual(obs["type"],"COLOMBIA_LEGAL_SENTINEL_NO_CHANGE")

    def test_colombia_change_requires_clause_level_review(self):
        baseline={
            "tipo":"DECRETO","n_mero":"111","a_o":"1996",
            "vigencia":"Vigente","art_culos":"130",
        }
        config={
            "source_id":"WSSRC-REG4-001",
            "canonical_occurrence_ids":["WSO-REG-D-0001"],
            "baseline":{"critical_fields":baseline,"critical_fields_sha256":stable_hash(baseline)},
        }
        changed=baseline|{"vigencia":"Derogado"}
        candidate,_=colombia_legal_input_review_candidate([changed],config)
        self.assertEqual(candidate["candidate_type"],"LEGAL_INPUT_CHANGED")
        self.assertEqual(candidate["review_state"],"PENDING_CLAUSE_LEVEL_SUIN_VERIFICATION")
        self.assertFalse(candidate["automatic_commit_allowed"])

    def test_cra_unchanged_semantic_rule(self):
        candidate,obs=cra_legal_rule_review_candidate(self.cra_baseline.copy(),self.cra_config)
        self.assertIsNone(candidate)
        self.assertEqual(obs["type"],"CRA_ARTICLE_71_RULE_NO_CHANGE")
        self.assertEqual(obs["rule_sha256"],self.cra_baseline["rule_sha256"])

    def test_cra_changed_date_generates_review_candidate_only(self):
        changed=self.cra_baseline|{
            "article_14_application_date":"2026-09-12",
            "rule_sha256":"changed-rule-hash",
        }
        candidate,obs=cra_legal_rule_review_candidate(changed,self.cra_config)
        self.assertEqual(candidate["candidate_type"],"LEGAL_RULE_CHANGED")
        self.assertEqual(candidate["review_state"],"PENDING_EURLEX_ARTICLE_71_REVIEW")
        self.assertEqual(candidate["occurrence_ids"],["WSO-TECH-A-0001","WSO-TECH-A-0007"])
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(obs["type"],"CRA_ARTICLE_71_RULE_CHANGED")
        self.assertEqual(self.cra_baseline["article_14_application_date"],"2026-09-11")


if __name__=="__main__": unittest.main()
