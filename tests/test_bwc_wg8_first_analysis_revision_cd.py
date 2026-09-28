from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
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
from world_signals.checkpoint_contract import version_at_least


FROZEN_PARENT_PAYLOAD_PATH = (
    ROOT / "data/analysis/NONMARKET_INSTITUTIONAL_ANALYSIS_W_PAYLOAD_v0.1.json"
)

# Exact Git blob identities of every CD protected upstream file at the
# post-CC base c186835d9d6b36620177badfff604f309ceb35d4.  These make the
# immutability proof independent of checkout depth: pull_request CI checks out
# a depth-1 synthetic merge commit, so the historical base object itself is not
# necessarily present even though its file bytes are.
BASE_PROTECTED_GIT_BLOBS = {
    "data/canonical/registry.json": "09ddfdfcf19a49e738cc0e203c1e945dc960f0cf",
    "data/sources/registry.json": "2f4a37f2560da10624e9622834b83fc0984041ce",
    "data/monitor/expectations.json": "7ab105477537f0902cd8200bc2072d961706e73a",
    "data/changes/ledger.json": "5f3140b6e729072b701ddf993ea60f914f509482",
    "data/live_intelligence/schema.json": "f4975b387747bc670ca3441e95daae86442536ef",
    "data/live_intelligence/observations.json": "72a12a35876923460941a7c393aed242ce94dd8c",
    "data/live_intelligence/evidence_registry.json": "d366fb4959647d79502064fb5d9c9991db5a8773",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_hash(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


class BWCWG8FirstAnalysisRevisionCDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(apply_cd.PLAN_PATH)
        schema = load(apply_cd.ANALYSIS_SCHEMA_PATH)
        reviews = load(apply_cd.REVIEWS_PATH)
        evidence = load(apply_cd.ANALYSIS_EVIDENCE_PATH)
        post = cls.plan["target_state"]
        materialized = (
            version_at_least(schema.get("version"), post["analysis_schema_version"])
            and reviews.get("version") == post["analysis_reviews_version"]
            and len(reviews.get("reviews", [])) == post["analysis_review_count"]
            and evidence.get("version") == post["analysis_evidence_version"]
            and len(evidence.get("evidence", [])) == post["analysis_evidence_count"]
        )
        if materialized:
            cls.target = {
                "analysis_schema": schema,
                "reviews": reviews,
                "evidence": evidence,
            }
        else:
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
        self.assertTrue(version_at_least(schema["version"], "0.8"))
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

    def test_parent_snapshot_is_exactly_preserved_from_frozen_source_artifact(self):
        frozen = load(FROZEN_PARENT_PAYLOAD_PATH)
        frozen_parent = next(
            r for r in frozen["reviews"] if r["analysis_id"] == apply_cd.PARENT_ID
        )
        self.assertEqual(self.parent, frozen_parent)
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
        reason = self.child["analysis_revision_reason"].lower()
        self.assertIn("ninth", reason)
        self.assertIn("working group session", reason)

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
        self.assertIn("do not establish final consensus", conclusion)
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
        current_schema = load(apply_cd.ANALYSIS_SCHEMA_PATH)
        if current_schema["version"] == self.plan["pre_state"]["analysis_schema_version"]:
            again = apply_cd.simulate()
            apply_cd.assert_target(self.plan, again)
            after = {p: stable_hash(ROOT / p) for p in self.plan["protected_paths"]}
            self.assertEqual(before, after)
        else:
            self.assertTrue(version_at_least(
                current_schema["version"],
                self.plan["target_state"]["analysis_schema_version"],
            ))
            self.assertEqual(set(self.plan["protected_paths"]), set(BASE_PROTECTED_GIT_BLOBS))
            for path in self.plan["protected_paths"]:
                if path.startswith("data/live_intelligence/") or path in {
                    "data/canonical/registry.json",
                    "data/sources/registry.json",
                    "data/monitor/expectations.json",
                    "data/changes/ledger.json",
                }:
                    continue
                self.assertEqual(
                    git_blob_hash(ROOT / path),
                    BASE_PROTECTED_GIT_BLOBS[path],
                    path,
                )
            canonical = load(ROOT / "data/canonical/registry.json")
            ledger = load(ROOT / "data/changes/ledger.json")
            self.assertGreaterEqual(tuple(map(int, canonical["version"].split("."))), (0, 41))
            self.assertGreaterEqual(len(canonical["records"]), 689)
            self.assertGreaterEqual(tuple(map(int, ledger["version"].split("."))), (0, 27))
            self.assertGreaterEqual(len(ledger["changes"]), 62)
            source_registry = load(ROOT / "data/sources/registry.json")
            monitor = load(ROOT / "data/monitor/expectations.json")
            self.assertGreaterEqual(tuple(map(int, source_registry["version"].split("."))), tuple(map(int, self.plan["target_state"]["source_registry_version"].split("."))))
            self.assertGreaterEqual(len(source_registry["sources"]), self.plan["target_state"]["source_count"])
            self.assertGreaterEqual(tuple(map(int, monitor["version"].split("."))), tuple(map(int, self.plan["target_state"]["monitor_version"].split("."))))
            self.assertGreaterEqual(len(monitor["adapters"]), self.plan["target_state"]["monitor_adapter_count"])
            self.assertFalse(monitor["automatic_canonical_commit"])
            self.assertFalse(monitor["google_calendar_write"])
            live_schema = load(apply_cd.LIVE_SCHEMA_PATH)
            live_evidence = load(apply_cd.LIVE_EVIDENCE_PATH)
            self.assertGreaterEqual(tuple(map(int, live_schema["version"].split("."))), (0, 6))
            self.assertGreaterEqual(len(self.live_observations["observations"]), 6)
            self.assertGreaterEqual(len(live_evidence["evidence"]), 9)
            self.assertFalse(live_schema["population_policy"]["automatic_ingestion_allowed"])
            self.assertFalse(live_schema["population_policy"]["public_observation_projection_allowed"])
        self.assertGreaterEqual(len(self.live_observations["observations"]), 6)


if __name__ == "__main__":
    unittest.main()
