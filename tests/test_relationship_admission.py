"""Step 12B first-production Relationship admission tests.

Production writes are exercised only on temporary copies of ``data``.  The
real repository is read-only until the explicit guarded materialisation step.
"""

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

from world_signals.relationship_admission import (  # noqa: E402
    ADMISSION_TRANSACTION_ID,
    ADMISSIONS_RELATIVE,
    CANDIDATE_RELATIVE,
    EXPECTED_CANDIDATE_FINGERPRINT,
    EXPECTED_SOURCE_MANIFEST,
    PRODUCTION_RELATIVE,
    REVIEW_RELATIVE,
    RelationshipAdmissionError,
    build_admission_transaction,
    build_review_transaction,
    build_accepted_relationship,
    materialize_rbnz_relationship_admission,
    validate_review_transaction,
    validate_rbnz_relationship_admission,
)
from world_signals.relationships import (  # noqa: E402
    active_relationship_graph_edges_as_of,
    relationship_history_as_of,
    validate_temporal_dependency_dag,
)


REVIEWED_AT = "2026-09-28T08:53:14Z"
ADMITTED_AT = "2026-09-28T08:53:15Z"


def copy_data_tree() -> Path:
    temporary = Path(tempfile.mkdtemp(prefix="world-state-step12b-"))
    shutil.copytree(ROOT / "data", temporary / "data")
    for relative in (
        PRODUCTION_RELATIVE,
        ADMISSIONS_RELATIVE,
        REVIEW_RELATIVE,
        Path("data/relationship_audit/STEP12B_RBNZ_RELATIONSHIP_REVIEW_ACCEPTED.md"),
    ):
        (temporary / relative).unlink(missing_ok=True)
    return temporary


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "data").rglob("*"))
        if path.is_file()
    }


class RelationshipAdmissionTests(unittest.TestCase):
    def test_exact_candidate_and_manifest_are_required(self):
        candidate = load(ROOT / CANDIDATE_RELATIVE)
        self.assertEqual(candidate["candidate_semantic_fingerprint"], EXPECTED_CANDIDATE_FINGERPRINT)
        self.assertEqual(candidate["source_manifest_sha256"], EXPECTED_SOURCE_MANIFEST)
        self.assertEqual(candidate["relationship"]["relationship_class"], "ASSOCIATION")
        self.assertEqual(candidate["relationship"]["directionality"], "DIRECTED")
        self.assertEqual(candidate["relationship"]["confidence"], "MEDIUM")

    def test_human_review_is_distinct_and_exact(self):
        candidate = load(ROOT / CANDIDATE_RELATIVE)
        review = build_review_transaction(candidate, REVIEWED_AT)
        self.assertEqual(review["transaction_type"], "RELATIONSHIP_REVIEW")
        self.assertEqual(review["decision"], "ACCEPTED")
        self.assertEqual(review["write_targets"], [])
        self.assertFalse(review["production_relationship_admitted"])
        self.assertEqual(validate_review_transaction(review, candidate), [])
        self.assertNotEqual(review["transaction_id"], ADMISSION_TRANSACTION_ID)

    def test_review_cannot_predate_candidate_or_accept_wrong_candidate(self):
        candidate = load(ROOT / CANDIDATE_RELATIVE)
        with self.assertRaises(RelationshipAdmissionError):
            build_review_transaction(candidate, "2026-09-28T07:21:59Z")
        review = build_review_transaction(candidate, REVIEWED_AT)
        tampered = deepcopy(candidate)
        tampered["candidate_semantic_fingerprint"] = "0" * 64
        self.assertTrue(validate_review_transaction(review, tampered))

    def test_accepted_row_corrects_independence_wording_without_mutating_candidate(self):
        candidate = load(ROOT / CANDIDATE_RELATIVE)
        original = deepcopy(candidate)
        review = build_review_transaction(candidate, REVIEWED_AT)
        row = build_accepted_relationship(candidate, review)
        self.assertEqual(row["review_state"], "ACCEPTED")
        self.assertEqual(row["lifecycle_state"], "EXPIRED")
        self.assertIn("separately reviewed", row["revision_reason"])
        self.assertIn("same Step 11B transaction", row["revision_reason"])
        self.assertIn("not independent corroboration", row["revision_reason"])
        self.assertEqual(candidate, original)

    def test_same_admission_does_not_inflate_corroboration_or_confidence(self):
        candidate = load(ROOT / CANDIDATE_RELATIVE)
        review = build_review_transaction(candidate, REVIEWED_AT)
        independence = review["independence_assessment"]
        self.assertTrue(independence["separately_reviewed_components"])
        self.assertTrue(independence["shared_analysis_or_evidence_lineage"])
        self.assertFalse(independence["counts_as_independent_corroboration"])
        self.assertFalse(independence["confidence_uplift_from_endpoint_coadmission"])
        self.assertEqual(candidate["relationship"]["confidence"], "MEDIUM")

    def test_temporal_and_causal_semantics_remain_narrow(self):
        candidate = load(ROOT / CANDIDATE_RELATIVE)["relationship"]
        scope = candidate["temporal_scope"]
        self.assertEqual(scope["scope_type"], "HISTORICAL_PERIOD")
        self.assertEqual(scope["precision"], "SOURCE_REPORTED_WINDOW")
        self.assertEqual(scope["anchor_at_utc"], "2026-09-02T02:00:00Z")
        self.assertIsNone(scope["start_at_utc"])
        self.assertIsNone(scope["end_at_utc"])
        self.assertEqual(candidate["causal_basis"], [])
        self.assertEqual(candidate["mechanism"], "NOT_ASSERTED_AT_ASSOCIATION_CLASS")

    def test_production_bundle_is_deterministic_and_admission_is_later_than_review(self):
        temporary = copy_data_tree()
        try:
            first = materialize_rbnz_relationship_admission(temporary, REVIEWED_AT, ADMITTED_AT)
            second = materialize_rbnz_relationship_admission(temporary, REVIEWED_AT, ADMITTED_AT)
            self.assertEqual(first["relationship"], second["relationship"])
            self.assertEqual(first["admission"], second["admission"])
            self.assertEqual(first["admission"]["transactions"][0]["admitted_at_utc"], ADMITTED_AT)
        finally:
            shutil.rmtree(temporary)

    def test_admission_before_review_fails_closed(self):
        temporary = copy_data_tree()
        try:
            with self.assertRaises(RelationshipAdmissionError):
                materialize_rbnz_relationship_admission(temporary, REVIEWED_AT, "2026-09-28T08:53:13Z")
        finally:
            shutil.rmtree(temporary)

    def test_materialisation_writes_exact_controlled_targets_and_preserves_v01(self):
        temporary = copy_data_tree()
        try:
            v01_schema = (temporary / "data/relationships/schema.json").read_bytes()
            v01_dataset = (temporary / "data/relationships/relationships.json").read_bytes()
            before = tree_hashes(temporary)
            bundle = materialize_rbnz_relationship_admission(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            self.assertTrue(bundle["materialized"])
            self.assertEqual((temporary / "data/relationships/schema.json").read_bytes(), v01_schema)
            self.assertEqual((temporary / "data/relationships/relationships.json").read_bytes(), v01_dataset)
            self.assertEqual(len(load(temporary / PRODUCTION_RELATIVE)["relationships"]), 1)
            self.assertEqual(len(load(temporary / ADMISSIONS_RELATIVE)["transactions"]), 1)
            self.assertEqual(load(temporary / PRODUCTION_RELATIVE)["relationships"][0]["lifecycle_state"], "EXPIRED")
            after = tree_hashes(temporary)
            self.assertEqual(after["data/relationships/schema.json"], before["data/relationships/schema.json"])
            self.assertEqual(after["data/relationships/relationships.json"], before["data/relationships/relationships.json"])
        finally:
            shutil.rmtree(temporary)

    def test_production_validation_and_relationship_history_are_distinct_from_active_graph(self):
        temporary = copy_data_tree()
        try:
            materialize_rbnz_relationship_admission(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            report = validate_rbnz_relationship_admission(temporary)
            self.assertTrue(report.ok, report.errors)
            production = load(temporary / PRODUCTION_RELATIVE)
            schema = load(temporary / "data/relationships/schema_v0.2.json")
            signals = load(temporary / "data/signals/signals.json")
            observations = load(temporary / "data/live_intelligence/observations.json")
            evidence = {"evidence": load(temporary / "data/live_intelligence/evidence_registry.json")["evidence"] + load(temporary / "data/analysis/evidence_registry.json")["evidence"]}
            canonical = load(temporary / "data/canonical/registry.json")
            components = load(temporary / "data/world_state/components.json")
            admissions = load(temporary / "data/world_state/admission_transactions.json")
            history = relationship_history_as_of(schema, production["relationships"], signals, observations, evidence, canonical, ADMITTED_AT, world_state_components=components, world_state_admissions=admissions)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["lifecycle_state"], "EXPIRED")
            edges = active_relationship_graph_edges_as_of(schema, production["relationships"], signals, observations, evidence, canonical, ADMITTED_AT, world_state_components=components, world_state_admissions=admissions)
            self.assertEqual(edges, [])
        finally:
            shutil.rmtree(temporary)

    def test_knowledge_time_excludes_relationship_before_review(self):
        temporary = copy_data_tree()
        try:
            materialize_rbnz_relationship_admission(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            production = load(temporary / PRODUCTION_RELATIVE)
            schema = load(temporary / "data/relationships/schema_v0.2.json")
            signals = load(temporary / "data/signals/signals.json")
            observations = load(temporary / "data/live_intelligence/observations.json")
            evidence = {"evidence": load(temporary / "data/live_intelligence/evidence_registry.json")["evidence"] + load(temporary / "data/analysis/evidence_registry.json")["evidence"]}
            canonical = load(temporary / "data/canonical/registry.json")
            components = load(temporary / "data/world_state/components.json")
            admissions = load(temporary / "data/world_state/admission_transactions.json")
            before_review = relationship_history_as_of(schema, production["relationships"], signals, observations, evidence, canonical, "2026-09-28T08:53:13Z", world_state_components=components, world_state_admissions=admissions)
            after_admission = relationship_history_as_of(schema, production["relationships"], signals, observations, evidence, canonical, ADMITTED_AT, world_state_components=components, world_state_admissions=admissions)
            self.assertEqual(before_review, [])
            self.assertEqual(len(after_admission), 1)
            self.assertEqual(after_admission[0]["temporal_scope"]["start_at_utc"], None)
        finally:
            shutil.rmtree(temporary)

    def test_temporal_dag_allows_future_component_but_rejects_self_cycles(self):
        c1 = {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C1", "revision_id": "C1-R1"}
        r1 = {"node_type": "RELATIONSHIP", "node_id": "R1", "revision_id": "R1-R1"}
        c2 = {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C1", "revision_id": "C1-R2"}
        valid = validate_temporal_dependency_dag([
            {"source": c1, "target": r1},
            {"source": r1, "target": c2},
        ])
        self.assertTrue(valid.ok, valid.errors)
        direct = validate_temporal_dependency_dag([{"source": c1, "target": r1}, {"source": r1, "target": c1}])
        self.assertFalse(direct.ok)
        multi = validate_temporal_dependency_dag([
            {"source": c1, "target": r1},
            {"source": r1, "target": c2},
            {"source": c2, "target": {"node_type": "RELATIONSHIP", "node_id": "R2", "revision_id": "R2-R1"}},
            {"source": {"node_type": "RELATIONSHIP", "node_id": "R2", "revision_id": "R2-R1"}, "target": c1},
        ])
        self.assertFalse(multi.ok)

    def test_production_population_and_upstream_counts_remain_bounded(self):
        production = load(ROOT / PRODUCTION_RELATIVE) if (ROOT / PRODUCTION_RELATIVE).exists() else {"relationships": []}
        if production["relationships"]:
            self.assertEqual(len(production["relationships"]), 1)
        world_state = load(ROOT / "data/world_state/components.json")
        snapshots = load(ROOT / "data/world_state/snapshots.json")
        admissions = load(ROOT / "data/world_state/admission_transactions.json")
        self.assertEqual(len(world_state["components"]), 3)
        self.assertEqual(len(snapshots["snapshots"]), 2)
        self.assertEqual(len(admissions["transactions"]), 2)
        actor_registry = ROOT / "data/world_state/actor_registry.json"
        self.assertEqual(len(load(actor_registry)["actors"]) if actor_registry.exists() else 0, 0)


if __name__ == "__main__":
    unittest.main()
