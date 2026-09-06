from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_analysis_revision_contract_ba as apply_ba
from world_signals.analysis import validate_analysis
from world_signals.analysis_revision import (
    REVISION_FIELDS,
    analysis_revision_heads,
    production_analysis_revision_count,
    public_review_without_revision_metadata,
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


def later_than(raw: str, seconds: int = 1) -> str:
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    return (parsed + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


class AnalysisRevisionContractBATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(apply_ba.PLAN_PATH)
        cls.canonical = load(apply_ba.CANONICAL_PATH)
        cls.reviews = load(apply_ba.REVIEWS_PATH)
        cls.evidence = load(apply_ba.ANALYSIS_EVIDENCE_PATH)
        cls.target = apply_ba.simulate()
        apply_ba.assert_target(cls.plan, cls.target)
        cls.review_by_id = {
            row["analysis_id"]: row for row in cls.reviews["reviews"]
        }
        cls.parent = cls.review_by_id["WSAN-JP-FIES-202607-001"]

    def controlled_schema(self, maximum: int = 1):
        schema = deepcopy(self.target["analysis_schema"])
        policy = schema["analysis_revision_policy"]
        policy["mode"] = "CONTROLLED_REVISION_LINEAGE"
        policy["production_analysis_revisions_allowed"] = True
        policy["maximum_production_analysis_revisions"] = maximum
        policy["maximum_children_per_revision_parent"] = 1
        return schema

    def child_of(self, parent: dict, analysis_id: str = "WSAN-TEST-REV-001"):
        child = deepcopy(parent)
        child["analysis_id"] = analysis_id
        child["analysis_as_of_utc"] = later_than(parent["analysis_as_of_utc"])
        child["revision_of_analysis_id"] = parent["analysis_id"]
        child["analysis_revision_kind"] = "METHODOLOGICAL_REASSESSMENT"
        child["analysis_revision_reason"] = "Synthetic BA contract test only."
        return child

    def test_exact_post_81_base_and_zero_revision_target_are_frozen(self):
        self.assertEqual(
            self.plan["exact_base_main_sha"],
            "802ca5b94b6e80a055ac363f48a6c8392f038048",
        )
        self.assertEqual(self.target["analysis_schema"]["version"], "0.7")
        self.assertEqual(production_analysis_revision_count(self.reviews), 0)
        self.assertEqual(len(self.reviews["reviews"]), 21)
        self.assertEqual(len(self.evidence["evidence"]), 95)
        self.assertEqual(production_live_input_count(self.reviews), 1)
        self.assertEqual(apply_ba.exact_series_count(self.reviews), 0)

    def test_status_helper_preserves_later_descendant_only_with_frozen_ba_invariants(self):
        current = apply_ba.STATUS_PATH.read_text(encoding="utf-8")
        first_header = current.splitlines()[0]
        descendant_header = "# CURRENT RECOVERY OVERRIDE — POST-BA / BB SYNTHETIC DESCENDANT"
        descendant = current.replace(first_header, descendant_header, 1)
        self.assertEqual(apply_ba.target_status(descendant), descendant)

        malformed = descendant.replace(
            "- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**",
            "- production Analysis revisions: **1 / gate OPEN**",
            1,
        )
        with self.assertRaises(SystemExit):
            apply_ba.target_status(malformed)

    def test_ba_target_core_analysis_and_revision_contract_validate(self):
        core = validate_analysis(
            self.target["analysis_schema"],
            self.evidence,
            self.reviews,
            self.canonical,
        )
        self.assertTrue(core.ok, core.errors)
        revision = validate_analysis_revisions(
            self.target["analysis_schema"], self.reviews
        )
        self.assertTrue(revision.ok, revision.errors)

    def test_existing_21_snapshots_are_not_rewritten_as_revisions(self):
        for review in self.reviews["reviews"]:
            self.assertTrue(all(field not in review for field in REVISION_FIELDS))
        self.assertEqual(
            set(analysis_revision_heads(self.reviews)),
            {row["analysis_id"] for row in self.reviews["reviews"]},
        )

    def test_foundation_gate_rejects_any_production_revision(self):
        reviews = deepcopy(self.reviews)
        reviews["reviews"].append(self.child_of(self.parent))
        report = validate_analysis_revisions(
            self.target["analysis_schema"], reviews
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("production revision gate is closed" in e for e in report.errors))

    def test_hypothetical_first_controlled_revision_is_new_snapshot_not_parent_mutation(self):
        schema = self.controlled_schema()
        reviews = deepcopy(self.reviews)
        parent_before = deepcopy(self.parent)
        child = self.child_of(parent_before)
        reviews["reviews"].append(child)
        report = validate_analysis_revisions(schema, reviews)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(self.parent, parent_before)
        self.assertEqual(child["canonical_occurrence_id"], parent_before["canonical_occurrence_id"])
        self.assertNotEqual(child["analysis_id"], parent_before["analysis_id"])
        self.assertEqual(child["revision_of_analysis_id"], parent_before["analysis_id"])

    def test_revision_metadata_without_parent_fails_closed_even_when_malformed(self):
        schema = self.controlled_schema(maximum=2)
        reviews = deepcopy(self.reviews)
        row = deepcopy(self.parent)
        row["analysis_id"] = "WSAN-TEST-MALFORMED-001"
        row["analysis_as_of_utc"] = later_than(self.parent["analysis_as_of_utc"])
        row["analysis_revision_kind"] = ["NEW_EVIDENCE"]
        row["analysis_revision_reason"] = "Malformed kind must not crash validator."
        reviews["reviews"].append(row)
        report = validate_analysis_revisions(schema, reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("requires revision_of_analysis_id" in e for e in report.errors))

    def test_unknown_parent_and_self_parent_fail_closed(self):
        schema = self.controlled_schema(maximum=2)
        reviews = deepcopy(self.reviews)
        unknown = self.child_of(self.parent, "WSAN-TEST-UNKNOWN-001")
        unknown["revision_of_analysis_id"] = "WSAN-NOT-REAL"
        self_parent = self.child_of(self.parent, "WSAN-TEST-SELF-001")
        self_parent["revision_of_analysis_id"] = self_parent["analysis_id"]
        reviews["reviews"].extend([unknown, self_parent])
        report = validate_analysis_revisions(schema, reviews)
        joined = " ".join(report.errors)
        self.assertIn("unknown revision parent", joined)
        self.assertIn("cannot reference itself", joined)

    def test_revision_cannot_jump_to_different_canonical_occurrence(self):
        schema = self.controlled_schema()
        reviews = deepcopy(self.reviews)
        child = self.child_of(self.parent)
        other = next(
            row for row in self.reviews["reviews"]
            if row["canonical_occurrence_id"] != self.parent["canonical_occurrence_id"]
        )
        child["canonical_occurrence_id"] = other["canonical_occurrence_id"]
        reviews["reviews"].append(child)
        report = validate_analysis_revisions(schema, reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("preserve parent canonical_occurrence_id" in e for e in report.errors))

    def test_revision_as_of_must_strictly_advance(self):
        schema = self.controlled_schema()
        reviews = deepcopy(self.reviews)
        child = self.child_of(self.parent)
        child["analysis_as_of_utc"] = self.parent["analysis_as_of_utc"]
        reviews["reviews"].append(child)
        report = validate_analysis_revisions(schema, reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("must strictly advance" in e for e in report.errors))

    def test_first_controlled_mode_rejects_branching(self):
        schema = self.controlled_schema(maximum=2)
        reviews = deepcopy(self.reviews)
        first = self.child_of(self.parent, "WSAN-TEST-BRANCH-A")
        second = self.child_of(self.parent, "WSAN-TEST-BRANCH-B")
        second["analysis_as_of_utc"] = later_than(self.parent["analysis_as_of_utc"], 2)
        reviews["reviews"].extend([first, second])
        report = validate_analysis_revisions(schema, reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("branches to 2 children" in e for e in report.errors))

    def test_revision_cycles_fail_closed(self):
        schema = self.controlled_schema(maximum=2)
        reviews = deepcopy(self.reviews)
        a = self.child_of(self.parent, "WSAN-TEST-CYCLE-A")
        b = self.child_of(self.parent, "WSAN-TEST-CYCLE-B")
        a["revision_of_analysis_id"] = b["analysis_id"]
        b["revision_of_analysis_id"] = a["analysis_id"]
        a["analysis_as_of_utc"] = "2026-09-07T00:00:00Z"
        b["analysis_as_of_utc"] = "2026-09-08T00:00:00Z"
        reviews["reviews"].extend([a, b])
        report = validate_analysis_revisions(schema, reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("cycle detected" in e for e in report.errors))

    def test_new_live_evidence_revision_requires_novel_explicit_observation(self):
        schema = self.controlled_schema()
        reviews = deepcopy(self.reviews)
        child = self.child_of(self.parent)
        child["analysis_revision_kind"] = "NEW_LIVE_EVIDENCE"
        child["live_inputs"] = deepcopy(self.parent.get("live_inputs") or [])
        reviews["reviews"].append(child)
        report = validate_analysis_revisions(schema, reviews)
        self.assertFalse(report.ok)
        self.assertTrue(any("requires at least one novel live observation_id" in e for e in report.errors))

        child["live_inputs"].append({
            "observation_id": "WSLI-TEST-NOVEL-001",
            "roles": ["CONTEXT_OR_ALTERNATIVE_INPUT"],
            "analysis_sections": ["alternative_explanations"],
        })
        report = validate_analysis_revisions(schema, reviews)
        self.assertTrue(report.ok, report.errors)

    def test_public_gate_strips_revision_metadata_and_does_not_select_latest_head(self):
        hypothetical = self.child_of(self.parent)
        public = public_review_without_revision_metadata(
            self.target["analysis_schema"], hypothetical
        )
        self.assertTrue(all(field not in public for field in REVISION_FIELDS))

        projection = public_analysis_projection_with_revision_contract(
            self.target["analysis_schema"],
            self.evidence,
            self.reviews,
            self.canonical,
        )
        metadata = projection["metadata"]
        self.assertTrue(metadata["analysis_revision_contract_present"])
        self.assertFalse(metadata["public_revision_metadata_projection_allowed"])
        self.assertFalse(metadata["automatic_latest_analysis_selection_allowed"])
        self.assertFalse(metadata["derived_revision_head_projection_allowed"])
        self.assertEqual(len(projection["reviews"]), 21)

    def test_read_only_simulation_protects_all_upstream_and_existing_population_paths(self):
        before = {path: stable_hash(ROOT / path) for path in self.plan["protected_paths"]}
        again = apply_ba.simulate()
        apply_ba.assert_target(self.plan, again)
        after = {path: stable_hash(ROOT / path) for path in self.plan["protected_paths"]}
        self.assertEqual(before, after)
        self.assertEqual(
            set(self.plan["governed_target_write_paths"]),
            {"data/analysis/schema.json", "PROJECT_STATUS.md", "ROADMAP.md"},
        )
        self.assertTrue(self.plan["manual_merge_only"])
        self.assertFalse(self.plan["auto_merge_allowed"])


if __name__ == "__main__":
    unittest.main()
