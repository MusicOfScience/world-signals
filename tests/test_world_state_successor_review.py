import json
from copy import deepcopy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from world_signals.world_state_history import fingerprint, validate_component_history, validate_snapshot_candidate
from world_signals.world_state_production import build_internal_briefing_read, successor_preflight
from world_signals.world_state_successor import (
    WorldStateSuccessorReviewError,
    build_snapshot_successor_candidate,
    build_successor_candidate,
    protected_hashes,
    review_successor_lineage,
    successor_diff,
)


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_ID = "WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN-202609-001"
SIGNAL_ID = "WSSIG-HEALTH-COD-BVD-BURDEN-202609-001"
SIGNAL_R1 = f"{SIGNAL_ID}-R1"
OBSERVATION_ID = "WSLI-HEALTH-COD-BVD-20260830-001"
COMPONENT_R1_HASH = "388af09e61e3d77a0f6f0ccc39dee545a17740c877872406f5b497b80d487790"


def _query_cutoff() -> str:
    return "2026-09-27T16:04:50Z"


def _read_component() -> dict:
    document = json.loads((ROOT / "data/world_state/components.json").read_text())
    return document["components"][0]


def _read_snapshot() -> dict:
    document = json.loads((ROOT / "data/world_state/snapshots.json").read_text())
    return document["snapshots"][0]


def _copy_upstream_fixture() -> Path:
    directory = Path(tempfile.mkdtemp())
    (directory / "data").mkdir()
    for relative in ("world_state", "signals", "live_intelligence"):
        shutil.copytree(ROOT / "data" / relative, directory / "data" / relative)
    return directory


class WorldStateSuccessorReviewTests(unittest.TestCase):
    def test_real_lineage_resolves_without_successor_trigger(self):
        packet = review_successor_lineage(COMPONENT_ID, _query_cutoff())
        self.assertEqual(packet["component_revision_id"], COMPONENT_ID + "-R1")
        self.assertEqual(packet["component_object_sha256"], COMPONENT_R1_HASH)
        self.assertEqual(packet["disposition"], "NO_SUCCESSOR_NEEDED")
        self.assertFalse(packet["successor_review_warranted"])
        self.assertEqual(packet["freshness"]["status"], "CURRENT")
        self.assertEqual(packet["mutation_check"]["status"], "PASS")
        self.assertEqual(len(packet["pinned_lineage"]), 5)

    def test_time_only_review_due_does_not_create_r2(self):
        packet = review_successor_lineage(COMPONENT_ID, "2026-10-07T00:00:00Z")
        self.assertEqual(packet["disposition"], "REVIEW_DUE_NO_NEW_EVIDENCE")
        self.assertFalse(packet["successor_review_warranted"])
        self.assertEqual(packet["component_revision_id"], COMPONENT_ID + "-R1")

    def test_caller_flags_are_not_lineage_authority(self):
        view = {
            "selected_components": [_read_component()],
            "freshness": [{"stale_review_due_at_utc": "2026-10-06T07:41:00Z"}],
            "query": {"knowledge_cutoff_utc": _query_cutoff()},
        }
        legacy = successor_preflight(view, new_governed_evidence=True)
        derived = review_successor_lineage(COMPONENT_ID, _query_cutoff())
        self.assertEqual(legacy["result"], "NEW_GOVERNED_EVIDENCE_AVAILABLE")
        self.assertEqual(derived["disposition"], "NO_SUCCESSOR_NEEDED")

    def test_accepted_signal_head_advance_is_detected(self):
        root = _copy_upstream_fixture()
        path = root / "data/signals/signals.json"
        document = json.loads(path.read_text())
        signal = deepcopy(document["signals"][0])
        signal["revision_id"] = f"{SIGNAL_ID}-R2"
        signal["revision_number"] = 2
        signal["review_provenance"] = {**signal["review_provenance"], "reviewed_at_utc": "2026-09-27T16:00:00Z"}
        signal["revision_reason"] = "Synthetic material evidence update for Step 9B test."
        document["signals"].append(signal)
        path.write_text(json.dumps(document))
        packet = review_successor_lineage(COMPONENT_ID, _query_cutoff(), root=root)
        self.assertEqual(packet["disposition"], "UPSTREAM_SIGNAL_REVISION_ADVANCED")
        self.assertEqual(packet["lineage_comparison"]["signal_revision_advanced"][0]["current_accepted_revision_id"], f"{SIGNAL_ID}-R2")

    def test_candidate_signal_head_does_not_trigger(self):
        root = _copy_upstream_fixture()
        path = root / "data/signals/signals.json"
        document = json.loads(path.read_text())
        signal = deepcopy(document["signals"][0])
        signal["revision_id"] = f"{SIGNAL_ID}-R2"
        signal["revision_number"] = 2
        signal["review_state"] = "UNDER_REVIEW"
        document["signals"].append(signal)
        path.write_text(json.dumps(document))
        packet = review_successor_lineage(COMPONENT_ID, _query_cutoff(), root=root)
        self.assertEqual(packet["disposition"], "NO_SUCCESSOR_NEEDED")

    def test_source_retraction_is_detected_without_mutating_r1(self):
        root = _copy_upstream_fixture()
        path = root / "data/live_intelligence/observations.json"
        document = json.loads(path.read_text())
        row = next(item for item in document["observations"] if item["observation_id"] == OBSERVATION_ID)
        row["verification_state"] = "RETRACTED"
        path.write_text(json.dumps(document))
        packet = review_successor_lineage(COMPONENT_ID, _query_cutoff(), root=root)
        self.assertEqual(packet["disposition"], "CORRECTION_OR_RETRACTION_REQUIRES_REVIEW")
        self.assertEqual(_read_component()["object_sha256"], COMPONENT_R1_HASH)

    def test_unrelated_same_domain_observation_does_not_trigger(self):
        root = _copy_upstream_fixture()
        path = root / "data/live_intelligence/observations.json"
        document = json.loads(path.read_text())
        unrelated = {
            "observation_id": "WSLI-HEALTH-SYNTHETIC-UNRELATED-001",
            "domain_tags": ["HEALTH_BIOSECURITY"],
            "jurisdictions": ["Democratic Republic of the Congo"],
            "verification_state": "PRIMARY_CONFIRMED",
            "observed_at_utc": "2026-09-27T16:00:00Z",
        }
        document["observations"].append(unrelated)
        path.write_text(json.dumps(document))
        packet = review_successor_lineage(COMPONENT_ID, _query_cutoff(), root=root)
        self.assertEqual(packet["disposition"], "NO_SUCCESSOR_NEEDED")

    def test_explicit_linked_contradiction_is_detected(self):
        root = _copy_upstream_fixture()
        path = root / "data/live_intelligence/observations.json"
        document = json.loads(path.read_text())
        document["observations"].append({
            "observation_id": "WSLI-HEALTH-SYNTHETIC-CONTRADICTION-001",
            "contradiction_status": "LINKED",
            "revision_of_observation_id": OBSERVATION_ID,
            "verification_state": "PRIMARY_CONFIRMED",
            "observed_at_utc": "2026-09-27T16:00:00Z",
        })
        path.write_text(json.dumps(document))
        packet = review_successor_lineage(COMPONENT_ID, _query_cutoff(), root=root)
        self.assertEqual(packet["disposition"], "CONTRADICTION_REQUIRES_REVIEW")

    def test_successor_candidate_update_correction_and_supersession_are_distinct(self):
        predecessor = _read_component()
        manifest = [{"layer": "TEST", "object_id": "synthetic-evidence", "object_sha256": "0" * 64}]
        for kind in ("UPDATE", "CORRECTION", "SUPERSESSION"):
            candidate = build_successor_candidate(predecessor, revision_kind=kind, source_manifest=manifest, changes={"state_label": f"SYNTHETIC_{kind}"}, test_only=True)
            self.assertEqual(candidate["revision_number"], 2)
            self.assertEqual(candidate["previous_revision_id"], predecessor["revision_id"])
            self.assertEqual(candidate["revision_kind"], kind)
            self.assertEqual(candidate["review_state"], "UNDER_REVIEW")
            self.assertIsNone(candidate["admitted_at_utc"])
            self.assertIsNone(candidate["admission_transaction_id"])
            self.assertEqual(validate_component_history([predecessor, candidate]), [])
        self.assertEqual(_read_component()["object_sha256"], COMPONENT_R1_HASH)

    def test_successor_candidate_rejects_invalid_revision_kind(self):
        with self.assertRaises(WorldStateSuccessorReviewError):
            build_successor_candidate(_read_component(), revision_kind="INITIAL", source_manifest=[{"x": 1}], test_only=True)

    def test_successor_diff_is_field_level_and_deterministic(self):
        predecessor = _read_component()
        candidate = build_successor_candidate(predecessor, revision_kind="UPDATE", source_manifest=[{"x": 1}], changes={"direction": "DOWNWARD"}, test_only=True)
        first = successor_diff(predecessor, candidate)
        second = successor_diff(predecessor, candidate)
        self.assertEqual(first, second)
        self.assertIn("direction", first["changed_fields"])
        self.assertFalse(first["freshness_only"])

    def test_snapshot_successor_candidate_keeps_predecessor_unadmitted(self):
        predecessor = _read_component()
        candidate = build_successor_candidate(predecessor, revision_kind="UPDATE", source_manifest=[{"x": 1}], changes={"direction": "DOWNWARD"}, test_only=True)
        snapshot = build_snapshot_successor_candidate(_read_snapshot(), candidate, source_manifest_sha256=fingerprint([{"x": 1}]), test_only=True)
        self.assertEqual(snapshot["revision_number"], 2)
        self.assertEqual(snapshot["previous_snapshot_revision_id"], _read_snapshot()["snapshot_revision_id"])
        self.assertIsNone(snapshot["admission_transaction_id"])
        self.assertIsNone(snapshot["admitted_at_utc"])
        self.assertEqual(validate_snapshot_candidate(snapshot, component_index={(candidate["component_type"], candidate["revision_id"]): candidate}), [])

    def test_briefing_preserves_multiple_scoped_assessments(self):
        first = _read_component()
        second = deepcopy(first)
        second["component_id"] = "WSDIM-HEALTH-SYNTHETIC-SECOND"
        second["revision_id"] = "WSDIM-HEALTH-SYNTHETIC-SECOND-R1"
        second["scope"] = {"jurisdictions": ["Synthetic jurisdiction"], "systems": ["SYNTHETIC_OUTBREAK"], "boundaries": ["test-only"]}
        query = {"scope": {"dimensions": ["HEALTH_BIOSECURITY"]}}
        freshness = [{"component_id": first["component_id"], "status": "CURRENT"}, {"component_id": second["component_id"], "status": "CURRENT"}]
        briefing = build_internal_briefing_read([first, second], query, freshness)
        health = briefing["dimensions"][0]
        self.assertEqual(health["coverage"], "MULTIPLE_SCOPED_ASSESSMENTS")
        self.assertEqual(len(health["scoped_assessments"]), 2)
        self.assertIsNone(health["assessment"])
        self.assertFalse(briefing["narrative_generated"])

    def test_protected_hashes_unchanged_after_real_review(self):
        before = protected_hashes()
        review_successor_lineage(COMPONENT_ID, _query_cutoff())
        after = protected_hashes()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
