from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_bwc_wg8_first_analysis_revision_cd as apply_cd
from world_signals.analysis import validate_analysis
from world_signals.analysis_revision import (
    REVISION_FIELDS,
    production_analysis_revision_count,
    validate_analysis_revisions,
)
from world_signals.analysis_revision_projection import (
    public_analysis_projection_with_revision_contract,
)
from world_signals.live_analysis_bridge import production_live_input_count


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BWCWG8FirstAnalysisRevisionCDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(apply_cd.PLAN_PATH)
        cls.target = apply_cd.simulate()
        apply_cd.assert_target(cls.plan, cls.target)
        cls.canonical = load(apply_cd.CANONICAL_PATH)
        cls.live_observations = load(apply_cd.LIVE_OBSERVATIONS_PATH)
        cls.parent = next(
            r for r in cls.target["reviews"]["reviews"]
            if r["analysis_id"] == apply_cd.PARENT_ID
        )
        cls.child = next(
            r for r in cls.target["reviews"]["reviews"]
            if r["analysis_id"] == apply_cd.CHILD_ID
        )

    def test_exact_target_population_and_policy_are_bounded(self):
        schema = self.target["analysis_schema"]
        reviews = self.target["reviews"]
        evidence = self.target["evidence"]
        self.assertEqual(schema["version"], "0.8")
        self.assertEqual((reviews["version"], len(reviews["reviews"])), ("0.18", 22))
        self.assertEqual((evidence["version"], len(evidence["evidence"])), ("0.18", 97))
        self.assertEqual(production_analysis_revision_count(reviews), 1)
        self.assertEqual(production_live_input_count(reviews), 1)
        policy = schema["analysis_revision_policy"]
        self.assertEqual(policy["mode"], "CONTROLLED_REVISION_LINEAGE")
        self.assertTrue(policy["production_analysis_revisions_allowed"])
        self.assertEqual(policy["maximum_production_analysis_revisions"], 1)
        self.assertEqual(policy["maximum_children_per_revision_parent"], 1)
        self.assertFalse(policy["public_revision_metadata_projection_allowed"])
        self.assertFalse(policy["automatic_latest_analysis_selection_allowed"])
        self.assertFalse(policy["public_revision_head_collapse_allowed"])

    def test_parent_snapshot_is_exactly_preserved_from_post_cc_base(self):
        base = self.plan["exact_base_main_sha"]
        raw = subprocess.check_output(
            ["git", "show", f"{base}:data/analysis/event_reviews.json"]
        )
        old = json.loads(raw)
        old_parent = next(
            r for r in old["reviews"] if r["analysis_id"] == apply_cd.PARENT_ID
        )
        self.assertEqual(self.parent, old_parent)
        self.assertTrue(all(field not in self.parent for field in REVISION_FIELDS))

    def test_child_is_new_snapshot_of_same_canonical_occurrence(self):
        self.assertEqual(self.child["revision_of_analysis_id"], apply_cd.PARENT_ID)
        self.assertEqual(self.child["analysis_revision_kind"], "NEW_EVIDENCE")
        self.assertEqual(
            self.child["canonical_occurrence_id"], self.parent["canonical_occurrence_id"]
        )
        self.assertEqual(
            self.child["canonical_occurrence_id"], "WSO-BWC-WG-2026-S08"
        )
        self.assertGreater(
            self.child["analysis_as_of_utc"], self.parent["analysis_as_of_utc"]
        )
        self.assertEqual(self.parent["second_order_effects"]["status"], "PLAUSIBLE_WATCH_ITEM")
        self.assertEqual(self.child["second_order_effects"]["status"], "OBSERVED")
        self.assertIn("ninth session", self.child["analysis_revision_reason"].lower())

    def test_new_evidence_contract_is_narrow_and_noncanonical(self):
        evidence_by_id = {
            row["evidence_id"]: row for row in self.target["evidence"]["evidence"]
        }
        self.assertEqual(set(apply_cd.NEW_EVIDENCE_IDS), {
            "WSEV-BWC-WG9-UN-INDICO-20260817",
            "WSEV-BWC-WG9-SHIB-REV7-20260827",
        })
        official = evidence_by_id["WSEV-BWC-WG9-UN-INDICO-20260817"]
        catalogue = evidence_by_id["WSEV-BWC-WG9-SHIB-REV7-20260827"]
        self.assertEqual(official["evidence_class"], "PRIMARY_OFFICIAL")
        self.assertEqual(catalogue["evidence_class"], "ACADEMIC_OR_INSTITUTIONAL")
        self.assertEqual(official["canonical_provenance_effect"], "NONE")
        self.assertEqual(catalogue["canonical_provenance_effect"], "NONE")
        self.assertIn("SECOND_ORDER_OBSERVATION", official["roles"])
        self.assertIn("SECOND_ORDER_OBSERVATION", catalogue["roles"])
        self.assertIn("indico.un.org/event/1018822", official["url"])
        self.assertIn("shib-temp.cbw-events.org.uk", catalogue["url"])
        self.assertIn("does not infer PDF-body semantics", catalogue["distribution_note"])

    def test_child_does_not_promote_draft_progress_into_final_consensus(self):
        conclusion = self.child["analytical_conclusion"].lower()
        second = self.child["second_order_effects"]["summary"].lower()
        self.assertIn("does not establish final consensus", conclusion)
        self.assertIn("not completion of the final consensus package", second)
        self.assertEqual(self.child["what_moved"], [])
        self.assertEqual(
            self.child["what_appears_connected"]["causal_status"],
            "NOT_A_CAUSAL_CLAIM",
        )

    def test_core_analysis_and_revision_validators_accept_target(self):
        core = validate_analysis(
            self.target["analysis_schema"],
            self.target["evidence"],
            self.target["reviews"],
            self.canonical,
        )
        self.assertTrue(core.ok, core.errors)
        revision = validate_analysis_revisions(
            self.target["analysis_schema"], self.target["reviews"]
        )
        self.assertTrue(revision.ok, revision.errors)

    def test_public_projection_preserves_both_snapshots_but_hides_lineage_metadata(self):
        projection = public_analysis_projection_with_revision_contract(
            self.target["analysis_schema"],
            self.target["evidence"],
            self.target["reviews"],
            self.canonical,
        )
        by_id = {row["analysis_id"]: row for row in projection["reviews"]}
        self.assertIn(apply_cd.PARENT_ID, by_id)
        self.assertIn(apply_cd.CHILD_ID, by_id)
        self.assertTrue(all(field not in by_id[apply_cd.CHILD_ID] for field in REVISION_FIELDS))
        metadata = projection["metadata"]
        self.assertFalse(metadata["public_revision_metadata_projection_allowed"])
        self.assertFalse(metadata["automatic_latest_analysis_selection_allowed"])
        self.assertFalse(metadata["derived_revision_head_projection_allowed"])

    def test_revision_population_ceiling_rejects_second_revision(self):
        reviews = deepcopy(self.target["reviews"])
        second = deepcopy(self.child)
        second["analysis_id"] = "WSAN-BWC-WG8-2026-003"
        second["analysis_as_of_utc"] = "2026-09-09T07:49:00Z"
        second["revision_of_analysis_id"] = apply_cd.CHILD_ID
        reviews["reviews"].append(second)
        report = validate_analysis_revisions(self.target["analysis_schema"], reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("exceeds reviewed maximum" in e for e in report.errors))

    def test_first_controlled_mode_rejects_branching_from_parent(self):
        schema = deepcopy(self.target["analysis_schema"])
        schema["analysis_revision_policy"]["maximum_production_analysis_revisions"] = 2
        reviews = deepcopy(self.target["reviews"])
        branch = deepcopy(self.child)
        branch["analysis_id"] = "WSAN-BWC-WG8-2026-BRANCH"
        branch["analysis_as_of_utc"] = "2026-09-09T07:49:00Z"
        branch["revision_of_analysis_id"] = apply_cd.PARENT_ID
        reviews["reviews"].append(branch)
        report = validate_analysis_revisions(schema, reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("branches to 2 children" in e for e in report.errors))

    def test_simulation_is_read_only_for_protected_upstream_layers(self):
        before = {p: stable_hash(ROOT / p) for p in self.plan["protected_paths"]}
        again = apply_cd.simulate()
        apply_cd.assert_target(self.plan, again)
        after = {p: stable_hash(ROOT / p) for p in self.plan["protected_paths"]}
        self.assertEqual(before, after)
        self.assertEqual(len(self.live_observations["observations"]), 6)


if __name__ == "__main__":
    unittest.main()
