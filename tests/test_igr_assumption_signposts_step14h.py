from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.assumption_signposts import (  # noqa: E402
    ADMISSION_ID, ANALYSIS_ID, CANDIDATE_PATH, DEFINITIONS_PATH, EVIDENCE_CUTOFF,
    GAPS_PATH, REVIEW_PATH, SNAPSHOT_ID, SNAPSHOTS_PATH, TRANSACTION_PATH,
    SignpostError, _dataset_hashes, _file_hash, _validate_materialized, build_transaction,
    get_signpost, get_snapshot_by_id, human_dispositions, latest_snapshot_as_of,
    list_signposts_for_assumption, materialize, validate_stores,
)


def temp_repo() -> tempfile.TemporaryDirectory:
    temp = tempfile.TemporaryDirectory(prefix="ws-step14h-test-")
    target = Path(temp.name)
    shutil.copytree(ROOT / "data", target / "data")
    for relative in (REVIEW_PATH, TRANSACTION_PATH, "data/analysis/assumption_signposts_schema.json", DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH):
        (target / relative).unlink(missing_ok=True)
    return temp


def make_targets(root: Path):
    return build_transaction(
        root, "2026-09-28T22:04:56Z", "2026-09-28T22:04:57Z",
        decision=human_dispositions(),
    )


class Step14HAdmissionTests(unittest.TestCase):
    def test_exact_candidate_and_upstream_pins_are_required(self):
        with temp_repo() as temp:
            root = Path(temp)
            candidate_path = root / CANDIDATE_PATH
            candidate = json.loads(candidate_path.read_text())
            candidate["selected_assumptions"][0]["why"] += " drift"
            candidate_path.write_text(json.dumps(candidate))
            with self.assertRaisesRegex(SignpostError, "candidate semantic fingerprint"):
                make_targets(root)

    def test_human_disposition_is_mandatory_and_exact(self):
        with temp_repo() as temp:
            with self.assertRaisesRegex(SignpostError, "explicit human disposition"):
                build_transaction(Path(temp), "2026-09-28T22:04:56Z", "2026-09-28T22:04:57Z", decision=None)
            altered = human_dispositions()
            altered["world_state"] = "ACCEPT"
            with self.assertRaisesRegex(SignpostError, "explicit human disposition"):
                build_transaction(Path(temp), "2026-09-28T22:04:56Z", "2026-09-28T22:04:57Z", decision=altered)

    def test_evidence_review_and_admission_cutoffs_are_distinct_and_ordered(self):
        with temp_repo() as temp:
            with self.assertRaisesRegex(SignpostError, "cutoff"):
                build_transaction(Path(temp), "2026-09-28T20:00:00Z", "2026-09-28T20:01:00Z", decision=human_dispositions())
            targets = make_targets(Path(temp))
            snap = targets[SNAPSHOTS_PATH]["snapshots"][0]
            self.assertEqual(snap["evidence_as_of_utc"], EVIDENCE_CUTOFF)
            self.assertEqual(snap["analysis_content_as_of_utc"], "2026-09-28T16:25:00Z")
            self.assertNotEqual(snap["reviewed_at_utc"], snap["evidence_as_of_utc"])
            self.assertNotEqual(snap["admitted_at_utc"], snap["evidence_as_of_utc"])
            self.assertLessEqual(snap["reviewed_at_utc"], snap["admitted_at_utc"])

    def test_exact_eight_assumptions_fifteen_ids_and_omissions_are_retained(self):
        with temp_repo() as temp:
            targets = make_targets(Path(temp))
            defs = targets[DEFINITIONS_PATH]["definitions"]
            snapshot = targets[SNAPSHOTS_PATH]["snapshots"][0]
            source_candidate = json.loads((Path(temp) / CANDIDATE_PATH).read_text())
            self.assertEqual(len(defs), 15)
            self.assertEqual(len(snapshot["assessments"]), 8)
            self.assertEqual({row["assumption_id"] for row in snapshot["assessments"]}, {
                "WSASM-AU-IGR-2026-" + suffix for suffix in (
                    "AI_DIFFUSION", "ENERGY_TRANSITION", "FERTILITY", "HEALTH_COST",
                    "MIGRATION", "PARTICIPATION", "PRODUCTIVITY", "TAX_CEILING",
                )
            })
            self.assertEqual(len(targets[REVIEW_PATH]["omitted_assumptions"]), 7)
            self.assertEqual(len({row["signpost_id"] for row in defs}), 15)
            self.assertEqual({row["signpost_id"] for row in defs}, {row["signpost_id"] for row in source_candidate["signposts"]})
            self.assertTrue(all("direction_of_evidence" not in row and "present_evidence_state" not in row for row in defs))
            self.assertEqual(len(snapshot["signpost_assessments"]), 15)

    def test_exact_assessment_states_all_observe(self):
        with temp_repo() as temp:
            snapshot = make_targets(Path(temp))[SNAPSHOTS_PATH]["snapshots"][0]
            assessments = {row["assumption_id"].rsplit("-", 1)[-1]: row for row in snapshot["assessments"]}
            self.assertEqual((assessments["PRODUCTIVITY"]["present_evidence_state"], assessments["PRODUCTIVITY"]["workflow_state"]), ("AMBIGUOUS", "OBSERVE"))
            self.assertEqual((assessments["MIGRATION"]["present_evidence_state"], assessments["MIGRATION"]["workflow_state"]), ("IN_TENSION_WITH_ASSUMPTION", "OBSERVE"))
            for suffix in {"AI_DIFFUSION", "ENERGY_TRANSITION", "FERTILITY", "HEALTH_COST", "PARTICIPATION", "TAX_CEILING"}:
                self.assertEqual((assessments[suffix]["present_evidence_state"], assessments[suffix]["workflow_state"]), ("NOT_ENOUGH_EVIDENCE", "OBSERVE"))
            self.assertEqual(snapshot["workflow_state_counts"], {"OBSERVE": 8, "REVIEW_DUE": 0, "STRUCTURAL_REASSESSMENT_REQUIRED": 0})

    def test_gaps_are_not_routes_and_production_contract_is_generic(self):
        with temp_repo() as temp:
            targets = make_targets(Path(temp))
            schema = targets["data/analysis/assumption_signposts_schema.json"]
            gaps = targets[GAPS_PATH]
            self.assertEqual(schema["contract"], "WORLD_SIGNALS_ASSUMPTION_SIGNPOST")
            self.assertNotIn("IGR", schema["contract"])
            self.assertEqual(gaps["gap_count"], 8)
            self.assertTrue(all(row["gap_code"] == "SOURCE_COVERAGE_GAP" and row["route_created"] is False for row in gaps["gaps"]))
            self.assertEqual((gaps["monitoring_authorised"], gaps["automated_retrieval_authorised"]), (False, False))

    def test_scoring_vocabulary_is_rejected(self):
        with temp_repo() as temp:
            targets = make_targets(Path(temp))
            schema = targets["data/analysis/assumption_signposts_schema.json"]
            definitions = deepcopy(targets[DEFINITIONS_PATH])
            gaps = targets[GAPS_PATH]
            snapshots = deepcopy(targets[SNAPSHOTS_PATH])
            snapshots["snapshots"][0]["assessments"][0]["score"] = 0.8
            errors = validate_stores(schema, definitions, gaps, snapshots)
            self.assertTrue(any("prohibited assessment field" in error for error in errors))

    def test_materialization_is_atomic_and_reader_is_knowledge_as_of(self):
        with temp_repo() as temp:
            root = Path(temp)
            targets = make_targets(root)
            materialize(root, targets)
            _validate_materialized(root)
            self.assertIsNone(latest_snapshot_as_of(root, "2026-09-28T22:04:56Z"))
            self.assertEqual(latest_snapshot_as_of(root, "2026-09-28T22:04:57Z")["snapshot_id"], SNAPSHOT_ID)
            self.assertEqual(get_snapshot_by_id(root, SNAPSHOT_ID)["snapshot_id"], SNAPSHOT_ID)
            self.assertEqual(len(list_signposts_for_assumption(root, "WSASM-AU-IGR-2026-PRODUCTIVITY")), 3)
            self.assertEqual(get_signpost(root, "WSIGN-AU-IGR-06-MIGRATION-FLOW")["assumption_id"], "WSASM-AU-IGR-2026-MIGRATION")
            tx = json.loads((root / TRANSACTION_PATH).read_text())
            self.assertEqual(tx["transaction_id"], ADMISSION_ID)
            self.assertEqual(tx["analysis_id"], ANALYSIS_ID)
            self.assertEqual(tx["monitoring_routes_created"], 0)
            self.assertEqual(tx["downstream_write_targets"], [])

    def test_reader_does_not_mutate_snapshot_and_requires_admission_time(self):
        with temp_repo() as temp:
            root = Path(temp)
            materialize(root, make_targets(root))
            path = root / SNAPSHOTS_PATH
            before = _file_hash(path)
            self.assertIsNone(latest_snapshot_as_of(root, "2026-09-28T22:04:56Z"))
            latest_snapshot_as_of(root, "2026-09-28T22:04:57Z")
            get_snapshot_by_id(root, SNAPSHOT_ID)
            self.assertEqual(_file_hash(path), before)

    def test_materialized_objects_are_sealed_and_targets_exact(self):
        with temp_repo() as temp:
            root = Path(temp)
            targets = make_targets(root)
            repeated = make_targets(root)
            self.assertEqual(targets, repeated)
            tx = targets[TRANSACTION_PATH]
            self.assertEqual(tx["write_targets"], [
                "data/analysis/assumption_signposts_schema.json",
                "data/analysis/assumption_signpost_definitions.json",
                "data/analysis/assumption_signpost_coverage_gaps.json",
                "data/analysis/assumption_signpost_assessment_snapshots.json",
                REVIEW_PATH, TRANSACTION_PATH,
            ])
            self.assertFalse(tx["public_projection_permitted"])
            self.assertFalse(tx["analysis_revision_created"])
            self.assertTrue(tx["pre_state_hashes"]["new_targets_absent"])
            self.assertEqual(tx["post_state_hashes"][SNAPSHOTS_PATH], hashlib.sha256(json.dumps(targets[SNAPSHOTS_PATH], indent=2, ensure_ascii=False, allow_nan=False).encode() + b"\n").hexdigest())

    def test_real_production_population_and_protected_hashes(self):
        before = _dataset_hashes(ROOT)
        _validate_materialized(ROOT, exact_post_state=False)
        reviews = json.loads((ROOT / "data/analysis/event_reviews.json").read_text())
        evidence = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text())
        transaction = json.loads((ROOT / TRANSACTION_PATH).read_text())
        review = json.loads((ROOT / REVIEW_PATH).read_text())
        self.assertEqual(len(reviews["reviews"]), 23)
        self.assertEqual(len(evidence["evidence"]), 100)
        self.assertEqual(review["dispositions"]["historical_backtest"], "DEFERRED")
        self.assertEqual(transaction["monitoring_routes_created"], 0)
        self.assertEqual(before, _dataset_hashes(ROOT))


if __name__ == "__main__":
    unittest.main()
