"""Executable, synthetic tests for the Migration Step 7 history contract.

All candidate state in this module is constructed in memory from the isolated
fixture.  No test writes a governed file or creates a production population.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_history import (  # noqa: E402
    COMPONENT_TYPES,
    fingerprint,
    public_view,
    select_component_revisions,
    simulate_production_admission,
    state_hashes,
    validate_actor_registry,
    validate_admission_transaction,
    validate_citations,
    validate_component_history,
    validate_component_revision,
    validate_history_query,
    validate_public_allowlist,
    validate_snapshot,
    validate_snapshot_history,
    validate_upstream_reference_ownership,
    with_object_fingerprint,
)


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "world_state_production_v1" / "fixture.json"
HASH = "a" * 64
OTHER_HASH = "b" * 64
T0 = "2026-01-01T00:00:00Z"
T1 = "2026-02-01T00:00:00Z"
T2 = "2026-03-01T00:00:00Z"
T3 = "2026-04-01T00:00:00Z"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def citation(layer: str = "SYNTHETIC", object_id: str = "fixture.evidence", epistemic_class: str = "FACTUAL_SOURCE", **extra) -> dict:
    result = {
        "layer": layer,
        "object_id": object_id,
        "revision_id": "r1",
        "object_sha256": HASH,
        "epistemic_class": epistemic_class,
    }
    result.update(extra)
    return result


def uncertainty(kind: str = "PROVENANCE_SOURCE", status: str = "BOUNDED") -> dict:
    return {"type": kind, "status": status, "description": "Synthetic bounded uncertainty", "basis_refs": ["fixture.evidence"]}


def component(template: dict, *, revision: int = 1, review_state: str = "ACCEPTED", lifecycle_state: str = "ACTIVE", **changes) -> dict:
    component_id = template["component_id"]
    row = {
        **template,
        "revision_id": f"{component_id}.r{revision}",
        "revision_number": revision,
        "previous_revision_id": f"{component_id}.r{revision - 1}" if revision > 1 else None,
        "revision_kind": "INITIAL" if revision == 1 else "UPDATE",
        "review_state": review_state,
        "lifecycle_state": lifecycle_state,
        "effective_at": T0,
        "known_at_utc": T0 if revision == 1 else T2,
        "reviewed_at_utc": (T1 if revision == 1 else T3) if review_state != "CANDIDATE" else None,
        "admitted_at_utc": (T1 if revision == 1 else T3) if review_state == "ACCEPTED" else None,
        "source_proposal_id": "synthetic-proposal-1",
        "source_manifest_sha256": HASH,
        "review_transaction_id": "synthetic-review-1" if review_state != "CANDIDATE" else None,
        "admission_transaction_id": "synthetic-admission-1" if review_state == "ACCEPTED" else None,
        "visibility": "INTERNAL_ONLY",
        "revision_reason": "Synthetic contract test revision",
        "supporting_citations": [citation()],
        "contradictory_citations": [],
        "uncertainties": [uncertainty()],
        "object_sha256": None,
    }
    row.update(changes)
    return with_object_fingerprint(row)


def registry() -> dict:
    fixture = load_fixture()
    actors = [with_object_fingerprint(row) for row in fixture["actors"]]
    return {"contract_version": "0.1", "actors": actors, "relationships": fixture["actor_relationships"]}


def template(name: str) -> dict:
    return next(row for row in load_fixture()["component_templates"] if row["component_id"] == name)


def snapshot(component_rows: list[dict], *, visibility: str = "INTERNAL_ONLY") -> dict:
    refs = [
        {"component_type": row["component_type"], "component_id": row["component_id"], "revision_id": row["revision_id"], "object_sha256": row["object_sha256"]}
        for row in component_rows
    ]
    row = {
        "snapshot_series_id": "snapshot.synthetic",
        "snapshot_revision_id": "snapshot.synthetic.r1",
        "revision_number": 1,
        "previous_snapshot_revision_id": None,
        "snapshot_kind": "COMPOSITIONAL_INDEX",
        "scope": {"jurisdictions": ["JURISDICTION_X"], "dimensions": ["TRADE_CAPITAL_ENERGY_FOOD_FLOWS"]},
        "knowledge_cutoff_utc": T2,
        "effective_as_of_utc": T2,
        "component_refs": refs,
        "upstream_refs": [citation("FORECASTS", "forecast.synthetic", "FORECAST", prospective=True)],
        "source_manifest_sha256": HASH,
        "proposal_id": "synthetic-proposal-1",
        "review_transaction_id": "synthetic-review-1",
        "admission_transaction_id": "synthetic-admission-1",
        "limitations": ["synthetic only"],
        "empty_queried_domains": load_fixture()["empty_domain_examples"],
        "lifecycle_state": "ACTIVE",
        "visibility": visibility,
        "reviewer": {"reviewer_id": "synthetic-reviewer", "role": "human"},
        "admitted_at_utc": T2,
        "object_sha256": None,
    }
    return with_object_fingerprint(row)


def admission(current_state: dict, candidate: list[dict], snap: dict, *, write_targets=None, public=False) -> dict:
    admitted = [row for row in candidate if row["review_state"] == "ACCEPTED"]
    post = {"actors": [], "components": admitted, "snapshots": [snap]}
    row = {
        "transaction_id": "synthetic-admission-1",
        "contract_version": "0.1",
        "transaction_type": "WORLD_STATE_PRODUCTION_ADMISSION",
        "decision": "ACCEPTED",
        "proposal_id": "synthetic-proposal-1",
        "proposal_semantic_fingerprint": HASH,
        "source_manifest_sha256": HASH,
        "component_fingerprints": [{"component_type": x["component_type"], "component_id": x["component_id"], "revision_id": x["revision_id"], "object_sha256": x["object_sha256"]} for x in candidate],
        "reviewer": {"reviewer_id": "synthetic-reviewer", "role": "human"},
        "decided_at_utc": T2,
        "component_dispositions": [{"component_id": x["component_id"], "revision_id": x["revision_id"], "disposition": "ADMITTED" if x["review_state"] == "ACCEPTED" else "DEFERRED", "reason": "Synthetic disposition"} for x in candidate],
        "snapshot_revision_identity": {"snapshot_series_id": snap["snapshot_series_id"], "snapshot_revision_id": snap["snapshot_revision_id"]},
        "write_targets": write_targets if write_targets is not None else ["temporary-copy-only"],
        "pre_state_hashes": state_hashes(current_state),
        "post_state_hashes": state_hashes(post),
        "visibility_decision": "INTERNAL_ONLY" if not public else "PUBLIC_ELIGIBLE",
        "admitted_at_utc": T2,
        "validator_version": "world-state-history-v1",
        "transaction_fingerprint": None,
    }
    row["transaction_fingerprint"] = fingerprint(row, exclude={"transaction_fingerprint"})
    return row


class WorldStateHistoryContractTests(unittest.TestCase):
    def test_fixture_is_test_only_and_unpopulated(self):
        fixture = load_fixture()
        self.assertEqual(fixture["status"], "TEST_ONLY_UNPOPULATED_PRODUCTION_CONTRACT")
        self.assertNotIn("admission_transaction", fixture)
        self.assertFalse((ROOT / "data/world_state/state.json").exists())

    def test_actor_registry_validates_and_person_office_institution_are_distinct(self):
        dataset = registry()
        self.assertEqual(validate_actor_registry(dataset), [])
        self.assertEqual({row["actor_type"] for row in dataset["actors"]}, {"PERSON", "OFFICE", "MINISTRY"})
        self.assertNotEqual(dataset["actors"][0]["actor_id"], dataset["actors"][1]["actor_id"])

    def test_alias_similarity_does_not_merge_identities(self):
        dataset = registry()
        dataset["actors"][1]["aliases"].append("Aurora Vale")
        dataset["actors"][1] = with_object_fingerprint(dataset["actors"][1])
        self.assertEqual(len({row["actor_id"] for row in dataset["actors"]}), 3)
        self.assertEqual(validate_actor_registry(dataset), [])

    def test_identity_registry_rejects_mutable_claims(self):
        actor = registry()["actors"][0]
        actor["capability"] = "inferred"
        self.assertTrue(validate_actor_registry({"actors": [actor], "relationships": []}))

    def test_component_families_are_controlled(self):
        self.assertEqual({row["component_type"] for row in load_fixture()["component_templates"]}, COMPONENT_TYPES)

    def test_actor_state_requires_registry_identity(self):
        row = component(template("assertion.aurora.capability"), claim_value="SUPPORTED")
        self.assertEqual(validate_component_revision(row, registry=registry()), [])
        self.assertTrue(validate_component_revision(row, registry={"actors": [], "relationships": []}))

    def test_unknown_capability_remains_valid_unknown(self):
        row = component(template("assertion.aurora.capability"), claim_value="UNKNOWN")
        self.assertEqual(validate_component_revision(row, registry=registry()), [])

    def test_supporting_and_contradictory_citations_are_distinct(self):
        row = component(template("dimension.routes.flow"), contradictory_citations=[citation(object_id="contradiction")])
        self.assertEqual(validate_component_revision(row), [])
        self.assertNotEqual(row["supporting_citations"], row["contradictory_citations"])

    def test_repeated_same_origin_citations_do_not_become_independent_evidence(self):
        row = component(template("dimension.routes.flow"), supporting_citations=[citation(object_id="same"), citation(object_id="same")])
        self.assertEqual(validate_component_revision(row), [])
        self.assertEqual({x["object_id"] for x in row["supporting_citations"]}, {"same"})

    def test_uncertainty_types_are_explicit_and_unknown_is_allowed(self):
        row = component(template("dimension.routes.flow"), uncertainties=[uncertainty("MEASUREMENT"), uncertainty("MODEL", "UNKNOWN")])
        self.assertEqual(validate_component_revision(row), [])

    def test_said_does_not_imply_decided(self):
        row = component(template("claim.routes.proposition"), state="SAID")
        self.assertEqual(row["state"], "SAID")
        self.assertNotEqual(row["state"], "DECIDED")

    def test_decided_does_not_imply_authorised(self):
        row = component(template("claim.routes.proposition"), state="DECIDED")
        self.assertNotEqual(row["state"], "AUTHORISED")

    def test_authorised_does_not_imply_implemented(self):
        row = component(template("claim.routes.proposition"), state="AUTHORISED")
        self.assertNotEqual(row["state"], "IMPLEMENTED")

    def test_implemented_does_not_imply_observed(self):
        row = component(template("claim.routes.proposition"), state="IMPLEMENTED")
        self.assertNotEqual(row["state"], "OBSERVED")

    def test_implementation_claim_can_diverge_without_rewriting_statement(self):
        said = component(template("claim.routes.proposition"), state="SAID")
        failed = component(template("claim.routes.proposition"), revision=2, revision_kind="CORRECTION", state="IMPLEMENTED", lifecycle_state="CORRECTED", previous_revision_id=said["revision_id"])
        self.assertEqual(validate_component_history([said, failed]), [])
        self.assertEqual(said["state"], "SAID")

    def test_effective_known_reviewed_and_admitted_times_are_distinct(self):
        row = component(template("dimension.routes.flow"), effective_at=T0, known_at_utc=T1, reviewed_at_utc=T2, admitted_at_utc=T3)
        self.assertEqual(validate_component_revision(row), [])
        self.assertLess(row["effective_at"], row["known_at_utc"])

    def test_history_requires_contiguous_predecessors(self):
        first = component(template("dimension.routes.flow"))
        second = component(template("dimension.routes.flow"), revision=2)
        self.assertEqual(validate_component_history([first, second]), [])
        second["previous_revision_id"] = "wrong"
        second = with_object_fingerprint(second)
        self.assertTrue(validate_component_history([first, second]))

    def test_correction_preserves_prior_revision(self):
        first = component(template("dimension.routes.flow"))
        corrected = component(template("dimension.routes.flow"), revision=2, revision_kind="CORRECTION", lifecycle_state="CORRECTED", previous_revision_id=first["revision_id"])
        self.assertEqual(validate_component_history([first, corrected]), [])
        self.assertEqual(first["lifecycle_state"], "ACTIVE")

    def test_withdrawn_history_cannot_silently_reactivate(self):
        first = component(template("dimension.routes.flow"), lifecycle_state="WITHDRAWN")
        second = component(template("dimension.routes.flow"), revision=2, previous_revision_id=first["revision_id"])
        self.assertTrue(validate_component_history([first, second]))

    def test_knowledge_as_of_excludes_later_known_revision(self):
        first = component(template("dimension.routes.flow"))
        later = component(template("dimension.routes.flow"), revision=2, known_at_utc=T3, reviewed_at_utc=T3, admitted_at_utc=T3, previous_revision_id=first["revision_id"])
        query = {"query_mode": "KNOWLEDGE_AS_OF", "knowledge_cutoff_utc": T2, "effective_as_of_utc": None, "scope": {}, "include_withdrawn_history": False}
        selected = select_component_revisions([first, later], query)
        self.assertEqual([row["revision_id"] for row in selected], [first["revision_id"]])

    def test_effective_as_of_excludes_future_effective_revision(self):
        row = component(template("dimension.routes.flow"), effective_at=T3)
        query = {"query_mode": "EFFECTIVE_AS_OF", "knowledge_cutoff_utc": T3, "effective_as_of_utc": T2, "scope": {}, "include_withdrawn_history": False}
        self.assertEqual(select_component_revisions([row], query), [])

    def test_history_query_rejects_implicit_latest(self):
        self.assertTrue(validate_history_query({"scope": {}, "include_withdrawn_history": False}))

    def test_baseline_is_structured_and_anomaly_is_not_a_forecast(self):
        baseline = component(template("baseline.routes.window"))
        anomaly = component(template("dimension.routes.flow"), baseline_ref=baseline["revision_id"], state_label="ANOMALOUS")
        self.assertEqual(validate_component_revision(baseline), [])
        self.assertEqual(validate_component_revision(anomaly), [])
        self.assertNotIn("forecast", anomaly)

    def test_no_baseline_is_explicit(self):
        no_baseline = component(template("baseline.routes.window"), basis="EXPLICIT_NO_BASELINE", baseline_value_or_label=None)
        self.assertEqual(validate_component_revision(no_baseline), [])

    def test_negative_evidence_requires_bounded_coverage(self):
        row = component(template("negative.routes.notice"))
        self.assertEqual(validate_component_revision(row), [])

    def test_source_failure_cannot_be_negative_evidence(self):
        row = component(template("negative.routes.notice"), source_health="FAILED")
        self.assertTrue(validate_component_revision(row))

    def test_unqueried_source_cannot_be_negative_evidence(self):
        row = component(template("negative.routes.notice"), search_scope=[])
        self.assertTrue(validate_component_revision(row))

    def test_no_record_found_cannot_be_negative_evidence(self):
        row = component(template("negative.routes.notice"), expected_indicator="NO_RECORD_FOUND")
        self.assertTrue(validate_component_revision(row))

    def test_competing_hypotheses_coexist(self):
        row = component(template("hypothesis.routes.cause"))
        self.assertEqual(validate_component_revision(row), [])
        self.assertEqual(row["disposition"], "UNRESOLVED")
        self.assertEqual(len(row["alternatives"]), 2)

    def test_hypothesis_citation_is_not_factual(self):
        errors: list[str] = []
        validate_citations([citation(epistemic_class="HYPOTHESIS", factual_claim=True)], errors)
        self.assertTrue(errors)

    def test_model_disagreement_retains_multiple_lenses(self):
        row = component(template("disagreement.routes.lenses"), model_provenance={"model_identity": "synthetic", "version": "1", "configuration": "default", "analytical_lens": "macro", "procedure_version": "v1", "generated_at_utc": T2, "input_manifest_sha256": HASH, "output_fingerprint": OTHER_HASH})
        self.assertEqual(validate_component_revision(row), [])

    def test_model_output_cannot_be_factual_source(self):
        row = component(template("disagreement.routes.lenses"), model_provenance={"model_identity": "synthetic", "version": "1", "configuration": "default", "analytical_lens": "macro", "procedure_version": "v1", "generated_at_utc": T2, "input_manifest_sha256": HASH, "output_fingerprint": OTHER_HASH}, model_outputs=[{"epistemic_class": "FACTUAL_SOURCE"}, {"epistemic_class": "HYPOTHESIS"}])
        self.assertTrue(validate_component_revision(row))

    def test_transmission_is_not_a_world_state_component(self):
        self.assertNotIn("TRANSMISSION", COMPONENT_TYPES)

    def test_relationship_reference_keeps_relationship_epistemic_class(self):
        ref = citation("RELATIONSHIPS", "relationship.synthetic", "INFERRED_RELATIONSHIP")
        self.assertEqual(validate_upstream_reference_ownership(ref, expected_layer="RELATIONSHIPS"), [])

    def test_forecast_reference_remains_prospective(self):
        ref = citation("FORECASTS", "forecast.synthetic", "FORECAST", prospective=True)
        self.assertEqual(validate_upstream_reference_ownership(ref, expected_layer="FORECASTS"), [])
        self.assertTrue(validate_upstream_reference_ownership({**ref, "prospective": False}, expected_layer="FORECASTS"))

    def test_snapshot_references_exact_components_without_copying_content(self):
        row = component(template("dimension.routes.flow"))
        snap = snapshot([row])
        self.assertEqual(validate_snapshot(snap, component_index={(row["component_type"], row["revision_id"]): row}), [])
        self.assertNotIn("state_label", snap["component_refs"][0])

    def test_snapshot_rejects_transmission_reference(self):
        row = snapshot([])
        row["component_refs"] = [{"component_type": "TRANSMISSION", "component_id": "x", "revision_id": "x.r1", "object_sha256": HASH}]
        row = with_object_fingerprint(row)
        self.assertTrue(validate_snapshot(row))

    def test_snapshot_history_is_append_only_and_contiguous(self):
        first_row = component(template("dimension.routes.flow"))
        first = snapshot([first_row])
        second = deepcopy(first)
        second["snapshot_revision_id"] = "snapshot.synthetic.r2"
        second["revision_number"] = 2
        second["previous_snapshot_revision_id"] = first["snapshot_revision_id"]
        second["object_sha256"] = None
        second = with_object_fingerprint(second)
        self.assertEqual(validate_snapshot_history([first, second], previous_revisions=[first], component_index={(first_row["component_type"], first_row["revision_id"]): first_row}), [])
        second["previous_snapshot_revision_id"] = "wrong"
        second = with_object_fingerprint(second)
        self.assertTrue(validate_snapshot_history([first, second], component_index={(first_row["component_type"], first_row["revision_id"]): first_row}))

    def test_empty_domains_are_explicit(self):
        snap = snapshot([])
        domains = {row["domain"]: row["state"] for row in snap["empty_queried_domains"]}
        self.assertEqual(domains["RELATIONSHIPS"], "QUERIED_EMPTY")
        self.assertEqual(domains["ACTOR_ASSERTIONS"], "UNQUERIED")
        self.assertEqual(domains["CANONICAL_HISTORY"], "UNSUPPORTED")

    def test_public_allowlist_rejects_private_fields(self):
        self.assertTrue(validate_public_allowlist(["internal_review_notes"]))

    def test_public_view_requires_allowlisted_fields_and_visibility(self):
        row = component(template("dimension.routes.flow"), visibility="PUBLIC_ELIGIBLE")
        self.assertEqual(public_view(row, ["component_id", "state_label"]), {"component_id": row["component_id"], "state_label": row["state_label"]})
        with self.assertRaises(ValueError):
            public_view({**row, "visibility": "INTERNAL_ONLY"}, ["component_id"])

    def test_new_component_cannot_start_public_projected(self):
        row = component(template("dimension.routes.flow"), visibility="PUBLIC_PROJECTED")
        self.assertTrue(validate_component_revision(row))

    def test_admission_requires_production_transaction_type(self):
        row = {"transaction_type": "WORLD_STATE_SYNTHESIS_REVIEW"}
        self.assertTrue(validate_admission_transaction(row))

    def test_partial_admission_is_simulated_in_memory(self):
        admitted = component(template("dimension.routes.flow"))
        deferred = component(template("baseline.routes.window"), review_state="DEFERRED", lifecycle_state="UNRESOLVED")
        snap = snapshot([admitted])
        current = {"actors": [], "components": [], "snapshots": []}
        tx = admission(current, [admitted, deferred], snap)
        result = simulate_production_admission(tx, current_state=current, candidate_components=[admitted, deferred], candidate_snapshot=snap)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["governed_files_written"], False)
        self.assertEqual(len(result["admitted_component_refs"]), 1)

    def test_admission_write_target_must_be_explicit(self):
        row = component(template("dimension.routes.flow"))
        snap = snapshot([row])
        tx = admission({"actors": [], "components": [], "snapshots": []}, [row], snap, write_targets=[])
        self.assertTrue(validate_admission_transaction(tx))

    def test_admission_cannot_permit_public_projection(self):
        row = component(template("dimension.routes.flow"))
        snap = snapshot([row])
        tx = admission({"actors": [], "components": [], "snapshots": []}, [row], snap, public=True)
        self.assertEqual(tx["visibility_decision"], "PUBLIC_ELIGIBLE")
        self.assertTrue(simulate_production_admission(tx, current_state={"actors": [], "components": [], "snapshots": []}, candidate_components=[row], candidate_snapshot=snap)["status"] == "PASS")

    def test_admission_hashes_are_tamper_evident(self):
        row = component(template("dimension.routes.flow"))
        snap = snapshot([row])
        tx = admission({"actors": [], "components": [], "snapshots": []}, [row], snap)
        tx["proposal_id"] = "tampered"
        self.assertTrue(validate_admission_transaction(tx))

    def test_canonical_historical_dependency_fails_closed(self):
        from world_signals.world_state_history import canonical_historical_dependency_result
        result = canonical_historical_dependency_result(requires_historical_canonical=True)
        self.assertEqual(result["code"], "CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED")
        self.assertFalse(result["admission_permitted"])

    def test_canonical_selector_allows_dependency_when_available(self):
        from world_signals.world_state_history import canonical_historical_dependency_result
        self.assertEqual(canonical_historical_dependency_result(requires_historical_canonical=True, canonical_selector_available=True)["status"], "SUPPORTED")

    def test_state_hashes_are_deterministic(self):
        state = {"actors": [], "components": [], "snapshots": []}
        self.assertEqual(state_hashes(state), state_hashes(deepcopy(state)))

    def test_simulator_does_not_mutate_current_state(self):
        row = component(template("dimension.routes.flow"))
        snap = snapshot([row])
        current = {"actors": [], "components": [], "snapshots": []}
        before = deepcopy(current)
        tx = admission(current, [row], snap)
        simulate_production_admission(tx, current_state=current, candidate_components=[row], candidate_snapshot=snap)
        self.assertEqual(current, before)

    def test_input_component_hash_change_is_detected(self):
        row = component(template("dimension.routes.flow"))
        row["state_label"] = "tampered"
        self.assertTrue(validate_component_revision(row))

    def test_no_duplicate_relationship_or_forecast_component_ownership(self):
        row = component(template("dimension.routes.flow"), supporting_citations=[citation("RELATIONSHIPS", "r", "INFERRED_RELATIONSHIP"), citation("FORECASTS", "f", "FORECAST", prospective=True)])
        self.assertEqual(validate_component_revision(row), [])
        self.assertEqual(row["component_type"], "DIMENSION_ASSESSMENT")

    def test_fixture_contains_no_real_world_content(self):
        fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")
        for term in ("Trump", "Iran", "Ukraine", "Federal Reserve"):
            self.assertNotIn(term, fixture_text)

    def test_schema_validator_script_is_present_and_read_only(self):
        script = ROOT / "scripts" / "validate_world_state_history.py"
        self.assertTrue(script.exists())


if __name__ == "__main__":
    unittest.main()
