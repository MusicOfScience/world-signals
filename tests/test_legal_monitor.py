from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import normalize_cellar_legal_topology
from world_signals.legal_monitor import (
    cbam_legal_milestone_review_candidate,
    cellar_legal_topology_review_candidate,
)


class LegalMonitorTests(unittest.TestCase):
    def setUp(self):
        self.base="32024R2847"
        self.base_subject="http://publications.europa.eu/resource/celex/32024R2847"
        self.relations=[
            {"predicate":"amended_by","target_uri":"http://publications.europa.eu/resource/oj/L_202500327","subject_uri":self.base_subject},
            {"predicate":"resource_legal_amended_by_resource_legal","target_uri":"http://publications.europa.eu/resource/oj/L_202500327","subject_uri":self.base_subject},
            {"predicate":"corrected_by","target_uri":"http://publications.europa.eu/resource/oj/L_202590555","subject_uri":self.base_subject},
            {"predicate":"consolidated_by","target_uri":"http://publications.europa.eu/resource/consolidation/2024R2847%2F20241120","subject_uri":self.base_subject},
            {"predicate":"resource_legal_consolidated_by_act_consolidated","target_uri":"http://publications.europa.eu/resource/consolidation/2024R2847%2F20241120_0000010","subject_uri":self.base_subject},
            {"predicate":"amends","target_uri":"http://publications.europa.eu/resource/celex/32019R1020","subject_uri":self.base_subject},
        ]
        self.topology=normalize_cellar_legal_topology(self.relations,base_celex=self.base)
        current=self.topology.as_dict()
        self.config={
            "adapter_id":"EU_CELLAR_CRA_ARTICLE_71",
            "source_id":"WSSRC-TECH-001",
            "canonical_occurrence_ids":["WSO-TECH-A-0001","WSO-TECH-A-0007"],
            "baseline":{
                "cellar_legal_topology":current.copy(),
                "cellar_legal_topology_sha256":current["topology_sha256"],
            },
        }
        self.cbam_verification_rule={
            "celex":"32025R2551",
            "rule_id":"VERIFICATION_REPORT_REGISTRY_START",
            "legal_locator":"Section 2.17.3",
            "milestone_date":"2027-01-01",
            "rule_sha256":"17be7d4335dec8dc5819d504e175d98fbb222564db99b2eb601d102f920635bf",
        }
        self.cbam_verification_config={
            "adapter_id":"EU_CBAM_VERIFICATION_RULE",
            "source_id":"WSSRC-TRD-005",
            "canonical_occurrence_ids":["WSO-TRD-A-0006"],
            "baseline":{
                "rule":self.cbam_verification_rule.copy(),
                "rule_sha256":self.cbam_verification_rule["rule_sha256"],
            },
        }
        self.cbam_sale_rule={
            "celex":"32025R2083",
            "rule_id":"CERTIFICATE_SALE_START",
            "legal_locator":"Article 20(1) replacement",
            "milestone_date":"2027-02-01",
            "rule_sha256":"56414b69dbeba2c01012bd999d50354a23b9d389aec42afa79114f2d24b18219",
        }
        self.cbam_sale_config={
            "adapter_id":"EU_CBAM_CERTIFICATE_SALE_RULE",
            "source_id":"WSSRC-TRD-005",
            "canonical_occurrence_ids":["WSO-TRD-A-0007"],
            "baseline":{
                "rule":self.cbam_sale_rule.copy(),
                "rule_sha256":self.cbam_sale_rule["rule_sha256"],
            },
        }

    def test_duplicate_predicates_and_fragments_collapse(self):
        self.assertEqual(self.topology.amendment_target_uris,(
            "http://publications.europa.eu/resource/oj/L_202500327",
        ))
        self.assertEqual(self.topology.consolidation_target_uris,(
            "http://publications.europa.eu/resource/consolidation/2024R2847%2F20241120",
        ))
        self.assertEqual(self.topology.repeal_target_uris,())

    def test_unchanged_topology_creates_no_candidate(self):
        candidate,obs=cellar_legal_topology_review_candidate(self.topology,self.config)
        self.assertIsNone(candidate)
        self.assertEqual(obs["type"],"CELLAR_LEGAL_TOPOLOGY_NO_CHANGE")

    def test_new_amendment_edge_creates_review_candidate_only(self):
        changed_relations=self.relations+[
            {"predicate":"amended_by","target_uri":"http://publications.europa.eu/resource/oj/L_202699999","subject_uri":self.base_subject}
        ]
        changed=normalize_cellar_legal_topology(changed_relations,base_celex=self.base)
        candidate,obs=cellar_legal_topology_review_candidate(changed,self.config)
        self.assertEqual(candidate["candidate_type"],"LEGAL_STATE_TOPOLOGY_CHANGED")
        self.assertEqual(candidate["review_state"],"PENDING_CELLAR_AMENDMENT_CORRIGENDUM_CONSOLIDATION_REVIEW")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(obs["type"],"CELLAR_LEGAL_TOPOLOGY_CHANGED")
        self.assertEqual(self.config["baseline"]["cellar_legal_topology"]["amendment_target_uris"],[
            "http://publications.europa.eu/resource/oj/L_202500327"
        ])

    def test_cbam_verification_rule_unchanged(self):
        candidate,obs=cbam_legal_milestone_review_candidate(
            self.cbam_verification_rule.copy(),self.cbam_verification_config
        )
        self.assertIsNone(candidate)
        self.assertEqual(obs["type"],"CBAM_LEGAL_MILESTONE_NO_CHANGE")
        self.assertEqual(obs["adapter_id"],"EU_CBAM_VERIFICATION_RULE")
        self.assertEqual(obs["milestone_date"],"2027-01-01")

    def test_cbam_verification_fake_date_change_is_review_only(self):
        changed=self.cbam_verification_rule|{
            "milestone_date":"2027-01-02",
            "rule_sha256":"fake-verification-change",
        }
        candidate,obs=cbam_legal_milestone_review_candidate(
            changed,self.cbam_verification_config
        )
        self.assertEqual(candidate["candidate_type"],"LEGAL_MILESTONE_RULE_CHANGED")
        self.assertEqual(candidate["occurrence_ids"],["WSO-TRD-A-0006"])
        self.assertEqual(candidate["review_state"],"PENDING_CBAM_LEGAL_MILESTONE_REVIEW")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(obs["type"],"CBAM_LEGAL_MILESTONE_CHANGED")
        self.assertEqual(self.cbam_verification_rule["milestone_date"],"2027-01-01")

    def test_cbam_certificate_sale_rule_unchanged(self):
        candidate,obs=cbam_legal_milestone_review_candidate(
            self.cbam_sale_rule.copy(),self.cbam_sale_config
        )
        self.assertIsNone(candidate)
        self.assertEqual(obs["type"],"CBAM_LEGAL_MILESTONE_NO_CHANGE")
        self.assertEqual(obs["adapter_id"],"EU_CBAM_CERTIFICATE_SALE_RULE")
        self.assertEqual(obs["milestone_date"],"2027-02-01")

    def test_cbam_certificate_sale_fake_date_change_is_review_only(self):
        changed=self.cbam_sale_rule|{
            "milestone_date":"2027-02-03",
            "rule_sha256":"fake-sale-change",
        }
        candidate,obs=cbam_legal_milestone_review_candidate(changed,self.cbam_sale_config)
        self.assertEqual(candidate["candidate_type"],"LEGAL_MILESTONE_RULE_CHANGED")
        self.assertEqual(candidate["occurrence_ids"],["WSO-TRD-A-0007"])
        self.assertEqual(candidate["review_state"],"PENDING_CBAM_LEGAL_MILESTONE_REVIEW")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(obs["type"],"CBAM_LEGAL_MILESTONE_CHANGED")
        self.assertEqual(self.cbam_sale_rule["milestone_date"],"2027-02-01")

    def test_cbam_empty_topology_is_valid_baseline(self):
        empty=normalize_cellar_legal_topology([],base_celex="32025R2551")
        current=empty.as_dict()
        config={
            "adapter_id":"EU_CBAM_VERIFICATION_RULE",
            "source_id":"WSSRC-TRD-005",
            "canonical_occurrence_ids":["WSO-TRD-A-0006"],
            "baseline":{
                "cellar_legal_topology":current.copy(),
                "cellar_legal_topology_sha256":current["topology_sha256"],
            },
        }
        candidate,obs=cellar_legal_topology_review_candidate(empty,config)
        self.assertIsNone(candidate)
        self.assertEqual(obs["amendment_count"],0)
        self.assertEqual(obs["correction_count"],0)


if __name__=="__main__": unittest.main()
