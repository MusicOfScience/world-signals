from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import normalize_cellar_legal_topology
from world_signals.legal_monitor import cellar_legal_topology_review_candidate


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
            "source_id":"WSSRC-TECH-001",
            "canonical_occurrence_ids":["WSO-TECH-A-0001","WSO-TECH-A-0007"],
            "baseline":{
                "cellar_legal_topology":current.copy(),
                "cellar_legal_topology_sha256":current["topology_sha256"],
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


if __name__=="__main__": unittest.main()
