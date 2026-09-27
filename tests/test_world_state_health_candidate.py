"""Step 8A tests for the real, narrowly scoped health candidate package."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.signals import signal_state_as_of  # noqa: E402
from world_signals.world_state_candidate import (  # noqa: E402
    CANDIDATE_COMPONENT_ID,
    EVIDENCE_IDS,
    OBSERVATION_IDS,
    SIGNAL_ID,
    SIGNAL_REVISION_ID,
    WorldStateCandidateError,
    build_health_candidate,
    validate_health_candidate_package,
)
from world_signals.world_state_history import (  # noqa: E402
    fingerprint,
    select_component_revisions,
    simulate_production_admission,
    state_hashes,
)


PACKAGE_PATH = ROOT / "data/world_state_audit/STEP8A_HEALTH_BVD_CANDIDATE_REVIEW_PENDING.json"
CONSTRUCTED_AT = "2026-09-27T12:20:58Z"


def load_package() -> dict:
    return json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))


def governed_hashes() -> dict[str, str]:
    paths = []
    for directory in ("canonical", "live_intelligence", "analysis", "signals", "relationships", "risks", "scenarios", "forecasts", "outcomes", "evaluation"):
        paths.extend((ROOT / "data" / directory).rglob("*"))
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


class WorldStateHealthCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_package()
        cls.candidate = cls.package["candidate"]

    def test_package_is_step8a_review_pending_and_not_production(self):
        self.assertEqual(self.package["status"], "REVIEW_PENDING")
        self.assertEqual(self.package["preflight_classification"], "READY_FOR_HUMAN_ADMISSION_REVIEW")
        self.assertEqual(self.package["production_admission"]["status"], "NOT_PERFORMED")
        self.assertEqual(self.package["production_admission"]["write_targets"], [])

    def test_real_candidate_validates_against_native_contract(self):
        self.assertEqual(validate_health_candidate_package(self.package), [])

    def test_candidate_construction_is_reproducible_at_explicit_cutoff(self):
        first = build_health_candidate(ROOT, CONSTRUCTED_AT)
        second = build_health_candidate(ROOT, CONSTRUCTED_AT)
        self.assertEqual(first, second)

    def test_all_ten_admission_gates_are_explicit(self):
        gates = self.package["production_admission_gates"]
        self.assertEqual(len(gates), 10)
        self.assertEqual({row["status"] for row in gates.values()}, {"PASS", "DEFER"})

    def test_exact_signal_revision_is_pinned(self):
        ids = {(ref["object_id"], ref.get("revision_id")) for ref in self.candidate["supporting_citations"]}
        self.assertIn((SIGNAL_ID, SIGNAL_REVISION_ID), ids)
        self.assertEqual(self.candidate["source_proposal_id"], f"WS-STEP8A-{CANDIDATE_COMPONENT_ID}")

    def test_exact_observations_and_evidence_are_pinned(self):
        citation_ids = {ref["object_id"] for ref in self.candidate["supporting_citations"]}
        self.assertTrue(set(OBSERVATION_IDS) <= citation_ids)
        self.assertTrue(set(EVIDENCE_IDS) <= citation_ids)
        self.assertEqual(self.candidate["source_manifest_sha256"], self.package["source_manifest_sha256"])

    def test_source_hashes_and_manifest_fingerprint_match(self):
        manifest = self.package["source_manifest"]
        self.assertEqual(self.package["source_manifest_sha256"], fingerprint(manifest))
        for entry in manifest:
            self.assertEqual(entry["object_sha256"], fingerprint(entry["object"]))

    def test_supporting_and_contradictory_refs_are_disjoint(self):
        support = {ref["object_id"] for ref in self.candidate["supporting_citations"]}
        contradiction = {ref["object_id"] for ref in self.candidate["contradictory_citations"]}
        self.assertTrue(support.isdisjoint(contradiction))
        self.assertEqual(contradiction, set())

    def test_shared_who_origin_does_not_become_independent_corroboration(self):
        uncertainty = next(row for row in self.candidate["uncertainties"] if row["type"] == "PROVENANCE_SOURCE")
        self.assertIn("WHO institutional family", uncertainty["description"])
        self.assertEqual(self.candidate["qualitative_confidence"], "LOW")
        self.assertNotIn("INDEPENDENT", json.dumps(self.candidate["qualitative_confidence"]))

    def test_state_label_is_narrowly_scoped(self):
        self.assertEqual(self.candidate["state_label"], "REPORTED_OUTBREAK_BURDEN_INCREASING")
        self.assertEqual(self.candidate["dimension"], "HEALTH_BIOSECURITY")
        self.assertEqual(self.candidate["scope"]["jurisdictions"], ["Democratic Republic of the Congo"])
        for forbidden in ("GLOBAL", "WORSENING", "SEVERITY", "INCIDENCE", "RISK_SCORE"):
            self.assertNotIn(forbidden, self.candidate["state_label"])

    def test_direction_is_upward_without_acceleration_or_breadth(self):
        self.assertEqual(self.candidate["direction"], "UPWARD")
        self.assertEqual(self.candidate["persistence"], "PERSISTENT")
        self.assertEqual(self.candidate["breadth"], "NOT_ASSESSED")
        self.assertNotIn("ACCELERATION", json.dumps(self.candidate))

    def test_reported_measurement_limitations_are_retained(self):
        text = json.dumps(self.candidate["limitations"]).lower()
        for term in ("reporting delay", "access", "testing", "case-definition", "unreported", "shared who"):
            self.assertIn(term, text)

    def test_effective_and_known_time_semantics_do_not_backdate_knowledge(self):
        self.assertIsNone(self.candidate["effective_at"])
        self.assertEqual(self.candidate["effective_date"], "2026-08-30")
        self.assertEqual(self.candidate["effective_time_precision"], "CIVIL_DATE")
        self.assertEqual(self.candidate["known_at_utc"], "2026-09-27T01:00:00Z")
        self.assertIsNone(self.candidate["reviewed_at_utc"])
        self.assertIsNone(self.candidate["admitted_at_utc"])

    def test_candidate_is_not_eligible_before_known_time(self):
        early = {"query_mode": "KNOWLEDGE_AS_OF", "knowledge_cutoff_utc": "2026-09-27T00:59:59Z", "effective_as_of_utc": None, "scope": self.candidate["scope"], "include_withdrawn_history": False}
        self.assertEqual(select_component_revisions([self.candidate], early), [])

    def test_freshness_uses_signal_validator_observed_time(self):
        freshness = self.package["freshness"]
        self.assertEqual(freshness["latest_supporting_observation_id"], OBSERVATION_IDS[1])
        self.assertEqual(freshness["latest_supporting_observed_at_utc"], "2026-09-06T07:41:00Z")
        self.assertEqual(freshness["stale_after_days"], 30)
        self.assertEqual(freshness["stale_review_due_at_utc"], "2026-10-06T07:41:00Z")
        self.assertEqual(freshness["status"], "ACTIVE_NEARING_REVIEW")

    def test_signal_is_active_at_candidate_cutoff_and_stale_after_threshold(self):
        signal_schema = json.loads((ROOT / "data/signals/schema.json").read_text())
        signals = json.loads((ROOT / "data/signals/signals.json").read_text())
        observations = json.loads((ROOT / "data/live_intelligence/observations.json").read_text())
        evidence = json.loads((ROOT / "data/live_intelligence/evidence_registry.json").read_text())
        current = signal_state_as_of(signal_schema, signals["signals"], observations, evidence, CONSTRUCTED_AT)[SIGNAL_ID]
        stale = signal_state_as_of(signal_schema, signals["signals"], observations, evidence, "2026-10-07T00:00:00Z")[SIGNAL_ID]
        self.assertEqual(current["effective_state"], "ACTIVE")
        self.assertEqual(stale["effective_state"], "STALE")

    def test_builder_fails_closed_after_signal_staleness(self):
        with self.assertRaises(WorldStateCandidateError):
            build_health_candidate(ROOT, "2026-10-07T00:00:00Z")

    def test_contradiction_and_correction_review_is_explicitly_empty(self):
        self.assertEqual(self.candidate["contradictory_citations"], [])
        self.assertEqual(self.candidate["correction_review_observation_ids"] if "correction_review_observation_ids" in self.candidate else [], [])
        self.assertIn("no contradiction was found", " ".join(self.candidate["limitations"]))

    def test_baseline_reuses_signal_without_duplicate_baseline_candidate(self):
        self.assertEqual(self.package["baseline_treatment"]["status"], "REUSED_EXISTING_SIGNAL_BASELINE")
        self.assertFalse(self.package["baseline_treatment"]["separate_baseline_candidate_created"])
        self.assertEqual(self.package["anomaly_treatment"]["status"], "NOT_CREATED")

    def test_no_actor_implementation_hypothesis_or_transmission_objects(self):
        self.assertEqual(self.package["actor_assertions"], [])
        self.assertEqual(self.package["implementation_claims"], [])
        self.assertEqual(self.package["hypotheses"], [])
        self.assertEqual(self.package["transmission_edges"], [])

    def test_existing_signal_hypothesised_pressure_is_not_promoted(self):
        self.assertTrue(any("response pressure" in limitation for limitation in self.package["limitations"]))
        self.assertNotIn("transmission_relevance", self.candidate)

    def test_model_provenance_is_not_factual_evidence(self):
        provenance = self.candidate["model_provenance"]
        self.assertEqual(provenance["factual_evidence_status"], "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION")
        self.assertNotIn("FACTUAL_SOURCE", json.dumps(provenance))

    def test_candidate_visibility_and_review_state_are_closed(self):
        self.assertEqual(self.candidate["visibility"], "INTERNAL_ONLY")
        self.assertEqual(self.candidate["review_state"], "UNDER_REVIEW")
        self.assertEqual(self.candidate["lifecycle_state"], "UNRESOLVED")
        self.assertFalse(self.package["public_projection_permitted"])

    def test_proposed_snapshot_references_pending_candidate_exact_hash(self):
        proposed = self.package["proposed_snapshot"]
        self.assertTrue(proposed["references_candidate_revision"])
        ref = proposed["snapshot"]["component_refs"][0]
        self.assertEqual(ref["component_id"], self.candidate["component_id"])
        self.assertEqual(ref["revision_id"], self.candidate["revision_id"])
        self.assertEqual(ref["object_sha256"], self.candidate["object_sha256"])

    def test_no_unrelated_dimensions_are_assessed(self):
        self.assertEqual(self.package["dimension_assessments"], [CANDIDATE_COMPONENT_ID])
        unqueried = {row["domain"] for row in self.package["known_empty_or_unsupported_domains"] if row["state"] == "UNQUERIED"}
        self.assertIn("WORLD_STATE_DIMENSIONS_OTHER_THAN_HEALTH_BIOSECURITY", unqueried)

    def test_temporary_admission_simulation_passes_without_production_admission(self):
        simulation = self.package["admission_simulation"]
        self.assertEqual(simulation["status"], "PASS")
        self.assertFalse(simulation["production_admission_performed"])
        self.assertFalse(simulation["result"]["governed_files_written"])
        self.assertNotEqual(simulation["result"]["pre_state_hashes_before"]["components"], simulation["result"]["post_state_hashes"]["components"])

    def test_failed_simulation_leaves_temporary_state_unchanged(self):
        simulation = self.package["admission_simulation"]
        transaction = deepcopy(simulation["transaction"])
        transaction["post_state_hashes"]["components"] = "0" * 64
        current = {"actors": [], "components": [], "snapshots": []}
        before = deepcopy(current)
        result = simulate_production_admission(transaction, current_state=current, candidate_components=[self.package["simulated_component"]], candidate_snapshot=self.package["simulated_snapshot"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(current, before)

    def test_successful_simulation_leaves_temporary_state_unchanged(self):
        current = {"actors": [], "components": [], "snapshots": []}
        before = deepcopy(current)
        simulation = self.package["admission_simulation"]
        result = simulate_production_admission(simulation["transaction"], current_state=current, candidate_components=[self.package["simulated_component"]], candidate_snapshot=self.package["simulated_snapshot"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(current, before)

    def test_governed_inputs_are_unchanged_by_candidate_read_and_simulation(self):
        before = governed_hashes()
        build_health_candidate(ROOT, CONSTRUCTED_AT)
        after = governed_hashes()
        self.assertEqual(before, after)

    def test_production_count_and_public_paths_remain_closed(self):
        self.assertEqual(self.package["production_admission"]["production_state_count_before"], 0)
        self.assertEqual(self.package["production_admission"]["production_state_count_after"], 0)
        self.assertFalse((ROOT / "data/world_state/state.json").exists())
        self.assertFalse((ROOT / "docs/world_state.json").exists())

    def test_candidate_package_contains_no_public_or_real_actor_registry_write(self):
        self.assertFalse(self.package["public_projection_permitted"])
        self.assertFalse((ROOT / "data/world_state/actor_registry.json").exists())


if __name__ == "__main__":
    unittest.main()
