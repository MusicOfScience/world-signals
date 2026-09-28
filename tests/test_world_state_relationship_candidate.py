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

from world_signals.relationships import (  # noqa: E402
    relationship_graph_edges_as_of,
    validate_temporal_dependency_dag,
    validate_relationship_history,
)
from world_signals.world_state_relationship_candidate import (  # noqa: E402
    ANALYSIS_HASH,
    MACRO_HASH,
    MARKETS_HASH,
    RELATIONSHIP_ID,
    build_rbnz_relationship_candidate,
    semantic_fingerprint,
    validate_rbnz_relationship_candidate,
)


class WorldStateRelationshipCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate_path = ROOT / "data/relationship_audit/STEP12A_RBNZ_RELATIONSHIP_CANDIDATE_REVIEW_PENDING.json"
        cls.candidate = json.loads(cls.candidate_path.read_text())
        cls.schema = json.loads((ROOT / "data/relationships/schema_v0.2.json").read_text())
        cls.components = json.loads((ROOT / "data/world_state/components.json").read_text())
        cls.admissions = json.loads((ROOT / "data/world_state/admission_transactions.json").read_text())
        cls.signals = json.loads((ROOT / "data/signals/signals.json").read_text())
        cls.observations = json.loads((ROOT / "data/live_intelligence/observations.json").read_text())
        cls.canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        live_evidence = json.loads((ROOT / "data/live_intelligence/evidence_registry.json").read_text())
        analysis_evidence = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text())
        cls.evidence = {"evidence": live_evidence["evidence"] + analysis_evidence["evidence"]}

    def row(self):
        return deepcopy(self.candidate["relationship"])

    def validate_row(self, row):
        return validate_relationship_history(
            self.schema,
            [row],
            self.signals,
            self.observations,
            self.evidence,
            self.canonical,
            world_state_components=self.components,
            world_state_admissions=self.admissions,
        )

    def test_retained_candidate_validates_and_is_exactly_pending(self):
        report = validate_rbnz_relationship_candidate(self.candidate, ROOT)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(self.candidate["review_state"], "UNDER_REVIEW")
        self.assertEqual(self.candidate["lifecycle_state"], "UNRESOLVED")
        self.assertEqual(self.candidate["candidate_disposition"], "READY_FOR_HUMAN_RELATIONSHIP_REVIEW")
        self.assertEqual(self.candidate["production_write_targets"], [])
        self.assertFalse(self.candidate["public_projection_permitted"])

    def test_v02_world_state_endpoints_pin_exact_admitted_revisions(self):
        row = self.row()
        self.assertEqual({node["node_type"] for node in row["source_nodes"] + row["target_nodes"]}, {"WORLD_STATE_COMPONENT"})
        self.assertEqual(row["source_nodes"][0]["object_sha256"], MACRO_HASH)
        self.assertEqual(row["target_nodes"][0]["object_sha256"], MARKETS_HASH)
        self.assertEqual(row["source_nodes"][0]["admission_transaction_id"], "WS-ADMISSION-NZ-RBNZ-OCR-20260928-001")
        self.assertTrue(self.validate_row(row).ok)

    def test_endpoint_current_use_does_not_gate_historical_candidate(self):
        self.assertEqual(
            {item["status"] for item in self.candidate["endpoint_current_use"]},
            {"NO_CURRENTNESS_CLAIM"},
        )
        self.assertTrue(self.validate_row(self.row()).ok)

    def test_analysis_is_supporting_lineage_not_endpoint(self):
        self.assertEqual(self.candidate["relationship"]["supporting_analysis_refs"][0]["object_sha256"], ANALYSIS_HASH)
        row = self.row()
        row["source_nodes"][0] = {"node_id": "WSAN-NZ-OCR-20260902-001", "node_type": "ANALYSIS"}
        self.assertIn("invalid typed node identity", " ".join(self.validate_row(row).errors))

    def test_composition_view_is_not_an_endpoint(self):
        row = self.row()
        row["source_nodes"][0] = {"node_id": "WORLD_STATE_COMPOSITION_VIEW", "node_type": "COMPOSITION_VIEW"}
        self.assertIn("invalid typed node identity", " ".join(self.validate_row(row).errors))

    def test_unadmitted_or_wrong_revision_endpoint_fails(self):
        row = self.row()
        row["source_nodes"][0]["revision_id"] = "WSDIM-MACRO-NZ-RBNZ-OCR-202609-001-R2"
        row["source_nodes"][0]["object_sha256"] = MACRO_HASH
        row["supporting_node_revisions"][0]["revision_id"] = row["source_nodes"][0]["revision_id"]
        self.assertIn("unavailable", " ".join(self.validate_row(row).errors))

    def test_wrong_component_hash_fails(self):
        row = self.row()
        row["target_nodes"][0]["object_sha256"] = "0" * 64
        row["supporting_node_revisions"][1]["object_sha256"] = "0" * 64
        self.assertIn("hash mismatch", " ".join(self.validate_row(row).errors))

    def test_relationship_class_direction_and_causal_boundary(self):
        row = self.row()
        self.assertEqual(row["relationship_class"], "ASSOCIATION")
        self.assertEqual(row["directionality"], "DIRECTED")
        self.assertNotEqual(row["relationship_class"], "HYPOTHESISED_TRANSMISSION")
        self.assertNotEqual(row["relationship_class"], "MECHANISTICALLY_SUPPORTED")
        self.assertNotEqual(row["relationship_class"], "CAUSAL_EVIDENCE")
        self.assertEqual(row["causal_basis"], [])
        self.assertEqual(row["mechanism"], "NOT_ASSERTED_AT_ASSOCIATION_CLASS")

    def test_alternatives_confounders_and_falsifiers_are_preserved(self):
        row = self.row()
        self.assertGreaterEqual(len(row["alternative_explanations"]), 3)
        self.assertGreaterEqual(len(row["confounders"]), 3)
        self.assertEqual(len(row["falsification_conditions"]), 3)
        self.assertEqual(row["confidence"], "MEDIUM")

    def test_analysis_and_evidence_hash_pins_are_exact(self):
        row = self.row()
        self.assertEqual(row["supporting_analysis_refs"][0]["object_sha256"], ANALYSIS_HASH)
        self.assertEqual({pin["evidence_id"] for pin in row["supporting_evidence_pins"]}, set(row["supporting_evidence_refs"]))
        self.assertTrue(self.validate_row(row).ok)

    def test_shared_lineage_does_not_create_extra_corroboration(self):
        row = self.row()
        self.assertEqual(row["supporting_analysis_refs"][0]["analysis_id"], "WSAN-NZ-OCR-20260902-001")
        self.assertEqual(row["confidence"], "MEDIUM")
        self.assertIn("source-reported", row["temporal_scope"]["notes"])

    def test_temporal_precision_does_not_fabricate_market_onset(self):
        scope = self.row()["temporal_scope"]
        self.assertEqual(scope["precision"], "SOURCE_REPORTED_WINDOW")
        self.assertEqual(scope["anchor_at_utc"], "2026-09-02T02:00:00Z")
        self.assertIsNone(scope["start_at_utc"])
        self.assertIsNone(scope["end_at_utc"])
        self.assertEqual(scope["start_date"], "2026-09-02")

    def test_candidate_is_excluded_from_active_graph(self):
        edges = relationship_graph_edges_as_of(
            self.schema, [self.row()], self.signals, self.observations, self.evidence,
            self.canonical, "2026-09-29T00:00:00Z",
            world_state_components=self.components,
            world_state_admissions=self.admissions,
        )
        self.assertEqual(edges, [])

    def test_candidate_can_be_seen_in_review_history_without_active_edge(self):
        from world_signals.relationships import relationship_state_as_of
        state = relationship_state_as_of(
            self.schema, [self.row()], self.signals, self.observations, self.evidence,
            self.canonical, "2026-09-29T00:00:00Z",
            world_state_components=self.components,
            world_state_admissions=self.admissions,
        )
        self.assertEqual(state[RELATIONSHIP_ID]["review_state"], "UNDER_REVIEW")

    def test_direct_and_multi_hop_cycles_are_rejected(self):
        direct = validate_temporal_dependency_dag([
            {"source": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C1", "revision_id": "C1-R1"}, "target": {"node_type": "RELATIONSHIP", "node_id": "R1", "revision_id": "R1-R1"}},
            {"source": {"node_type": "RELATIONSHIP", "node_id": "R1", "revision_id": "R1-R1"}, "target": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C1", "revision_id": "C1-R1"}},
        ])
        self.assertFalse(direct.ok)
        multi = validate_temporal_dependency_dag([
            {"source": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C1", "revision_id": "C1-R1"}, "target": {"node_type": "RELATIONSHIP", "node_id": "R1", "revision_id": "R1-R1"}},
            {"source": {"node_type": "RELATIONSHIP", "node_id": "R1", "revision_id": "R1-R1"}, "target": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C2", "revision_id": "C2-R1"}},
            {"source": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C2", "revision_id": "C2-R1"}, "target": {"node_type": "RELATIONSHIP", "node_id": "R2", "revision_id": "R2-R1"}},
            {"source": {"node_type": "RELATIONSHIP", "node_id": "R2", "revision_id": "R2-R1"}, "target": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C1", "revision_id": "C1-R1"}},
        ])
        self.assertFalse(multi.ok)

    def test_forward_temporal_dag_is_allowed(self):
        report = validate_temporal_dependency_dag([
            {"source": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C1", "revision_id": "C1-R1"}, "target": {"node_type": "RELATIONSHIP", "node_id": "R1", "revision_id": "R1-R1"}},
            {"source": {"node_type": "RELATIONSHIP", "node_id": "R1", "revision_id": "R1-R1"}, "target": {"node_type": "WORLD_STATE_COMPONENT", "node_id": "C2", "revision_id": "C2-R1"}},
        ])
        self.assertTrue(report.ok, report.errors)

    def test_same_snapshot_or_admission_does_not_create_relationship(self):
        relationships = json.loads((ROOT / "data/relationships/relationships.json").read_text())
        self.assertEqual(relationships["relationships"], [])
        self.assertEqual(self.candidate["relationship"]["supporting_analysis_refs"][0]["analysis_id"], "WSAN-NZ-OCR-20260902-001")

    def test_candidate_fingerprint_is_deterministic(self):
        first = build_rbnz_relationship_candidate(ROOT)
        second = build_rbnz_relationship_candidate(ROOT)
        self.assertEqual(first["candidate_semantic_fingerprint"], second["candidate_semantic_fingerprint"])
        self.assertEqual(first["source_manifest_sha256"], self.candidate["source_manifest_sha256"])

    def test_tampered_source_manifest_fails_without_mutating_repo(self):
        before = hashlib.sha256((ROOT / "data/world_state/components.json").read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            shutil.copytree(ROOT / "data", temp_root / "data")
            target = temp_root / "data/world_state/components.json"
            data = json.loads(target.read_text())
            data["components"][1]["state_label"] = "TAMPERED"
            target.write_text(json.dumps(data, indent=2) + "\n")
            report = validate_rbnz_relationship_candidate(self.candidate, temp_root)
            self.assertFalse(report.ok)
            self.assertTrue(any("hash mismatch" in error or "manifest" in error for error in report.errors))
        after = hashlib.sha256((ROOT / "data/world_state/components.json").read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_production_and_public_boundaries_remain_closed(self):
        relationships = json.loads((ROOT / "data/relationships/relationships.json").read_text())
        self.assertEqual(len(relationships["relationships"]), 0)
        self.assertFalse(self.candidate["public_projection_permitted"])
        self.assertFalse(self.candidate["production_relationship_admitted"])
        self.assertEqual(self.candidate["production_write_targets"], [])
        self.assertEqual(len(self.components["components"]), 5)
        self.assertEqual(len(json.loads((ROOT / "data/world_state/snapshots.json").read_text())["snapshots"]), 3)
        self.assertEqual(len(self.admissions["transactions"]), 3)


if __name__ == "__main__":
    unittest.main()
