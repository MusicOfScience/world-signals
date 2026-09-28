from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

from world_signals.world_state_admission import load_production_state, validate_production_state
from world_signals.world_state_composition import COMPOSITION_ATOMICITY, COMPOSITION_TYPE
from world_signals.world_state_production import read_production_world_state
from world_signals.world_state_history import state_hashes
from world_signals.world_state_rbnz_admission import (
    ADMISSION_TRANSACTION_ID,
    EXPECTED_MACRO_CANDIDATE_HASH,
    EXPECTED_MARKET_CANDIDATE_HASH,
    EXPECTED_ORIGINAL_PACKAGE_SHA256,
    EXPECTED_PACKAGE_FINGERPRINT,
    EXPECTED_PENDING_SNAPSHOT_FINGERPRINT,
    EXPECTED_SOURCE_MANIFEST,
    MARKET_COMPONENT_ID,
    MACRO_COMPONENT_ID,
    REVIEW_TRANSACTION_ID,
    WorldStateRbnzAdmissionError,
    build_component_review_transaction,
    build_rbnz_admission,
    materialize_rbnz_admission,
    validate_component_review_transaction_step11b,
)
from world_signals.world_state_rbnz_candidate import build_corrected_rbnz_candidate


REVIEWED_AT = "2026-09-28T04:27:16Z"
ADMITTED_AT = "2026-09-28T04:27:17Z"
ORIGINAL = ROOT / "data/world_state_audit/STEP11A_RBNZ_CANDIDATE_REVIEW_PENDING.json"
STEP14C_COMPONENT_IDS = {
    "WSBASE-CLIMATE-AU-TC-CLIMATOLOGY-1980-81-001",
    "WSDIM-CLIMATE-AU-TCSEASON-2025-26-001",
}
STEP14C_SNAPSHOT_SERIES = "WSSNAP-CLIMATE-AU-TCSEASON-2025-26"
STEP14C_ADMISSION_ID = "WS-ADMISSION-CLIMATE-AU-TCSEASON-20260929-001"


def copy_data_tree() -> Path:
    temporary = Path(tempfile.mkdtemp(prefix="world-state-step11b-"))
    shutil.copytree(ROOT / "data", temporary / "data")
    # The repository now contains the admitted Step 11B result.  Admission
    # tests still need a deterministic copy of the exact one-component
    # Step 8B pre-state, so remove only the two RBNZ production rows and its
    # retained Step 11B review artefacts from the temporary copy.
    components_path = temporary / "data/world_state/components.json"
    components = json.loads(components_path.read_text())
    components["components"] = [
        row for row in components["components"]
        if row["component_id"] not in {MACRO_COMPONENT_ID, MARKET_COMPONENT_ID} | STEP14C_COMPONENT_IDS
    ]
    components_path.write_text(json.dumps(components, indent=2, sort_keys=True) + "\n")
    snapshots_path = temporary / "data/world_state/snapshots.json"
    snapshots = json.loads(snapshots_path.read_text())
    snapshots["snapshots"] = [
        row for row in snapshots["snapshots"]
        if row.get("snapshot_series_id") not in {"WSSNAP-NZ-RBNZ-OCR-202609", STEP14C_SNAPSHOT_SERIES}
    ]
    snapshots_path.write_text(json.dumps(snapshots, indent=2, sort_keys=True) + "\n")
    admissions_path = temporary / "data/world_state/admission_transactions.json"
    admissions = json.loads(admissions_path.read_text())
    admissions["transactions"] = [
        row for row in admissions["transactions"]
        if row.get("transaction_id") not in {ADMISSION_TRANSACTION_ID, STEP14C_ADMISSION_ID}
    ]
    admissions_path.write_text(json.dumps(admissions, indent=2, sort_keys=True) + "\n")
    for relative in (
        "data/world_state_audit/STEP11B_RBNZ_COMPONENT_REVIEW_ACCEPTED.json",
        "data/world_state_audit/STEP11B_RBNZ_COMPONENT_REVIEW_ACCEPTED.md",
    ):
        (temporary / relative).unlink(missing_ok=True)
    return temporary


def all_data_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "data").rglob("*"))
        if path.is_file()
    }


def upstream_hashes(root: Path) -> dict[str, str]:
    directories = ("canonical", "live_intelligence", "analysis", "signals", "relationships", "risks", "scenarios", "forecasts", "outcomes", "evaluation")
    paths = [path for directory in directories for path in (root / "data" / directory).rglob("*") if path.is_file()]
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def query(knowledge: str, *, mode: str = "KNOWLEDGE_AS_OF", effective: str | None = None, dimensions: list[str] | None = None) -> dict:
    return {
        "query_mode": mode,
        "knowledge_cutoff_utc": knowledge,
        "effective_as_of_utc": effective,
        "scope": {"dimensions": dimensions or [], "jurisdictions": [], "systems": [], "component_ids": []},
        "include_withdrawn_history": False,
    }


class WorldStateRbnzAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads((ROOT / "data/world_state_audit/STEP11A1_RBNZ_CANDIDATE_REVIEW_PENDING_CORRECTED.json").read_text())
        cls.original_bytes = ORIGINAL.read_bytes()

    def test_exact_corrected_package_and_source_manifest_are_required(self):
        self.assertEqual(self.package["candidate_semantic_fingerprint"], EXPECTED_PACKAGE_FINGERPRINT)
        self.assertEqual(self.package["proposed_snapshot"]["snapshot_semantic_fingerprint"], EXPECTED_PENDING_SNAPSHOT_FINGERPRINT)
        self.assertEqual(self.package["source_manifest_sha256"], EXPECTED_SOURCE_MANIFEST)
        rows = {row["component_id"]: row for row in self.package["dimension_assessment_candidates"]}
        self.assertEqual(rows[MACRO_COMPONENT_ID]["object_sha256"], EXPECTED_MACRO_CANDIDATE_HASH)
        self.assertEqual(rows[MARKET_COMPONENT_ID]["object_sha256"], EXPECTED_MARKET_CANDIDATE_HASH)
        self.assertEqual(hashlib.sha256(self.original_bytes).hexdigest(), EXPECTED_ORIGINAL_PACKAGE_SHA256)

    def test_human_review_accepts_only_macro_and_markets_and_defers_actor(self):
        review = build_component_review_transaction(self.package, REVIEWED_AT)
        self.assertEqual(validate_component_review_transaction_step11b(review, self.package), [])
        self.assertEqual(review["transaction_id"], REVIEW_TRANSACTION_ID)
        self.assertEqual(review["decision"], "ACCEPTED")
        self.assertEqual(review["component_decisions"][MACRO_COMPONENT_ID], "ACCEPTED")
        self.assertEqual(review["component_decisions"][MARKET_COMPONENT_ID], "ACCEPTED")
        self.assertEqual(review["component_decisions"]["WSACT-RBNZ-202609-001"], "DEFERRED")
        self.assertEqual(review["write_targets"], [])
        self.assertFalse(review["production_world_state_admitted"])
        self.assertFalse(review["public_projection_permitted"])

    def test_admitted_components_preserve_semantics_and_do_not_depend_on_actor(self):
        temporary = copy_data_tree()
        try:
            bundle = build_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT)
            rows = {row["component_id"]: row for row in bundle["admitted_components"]}
            macro = rows[MACRO_COMPONENT_ID]
            market = rows[MARKET_COMPONENT_ID]
            self.assertEqual(macro["state_label"], "POLICY_RATE_INCREASED_WITH_MORE_GRADUAL_FORWARD_PATH")
            self.assertEqual(macro["effective_at"], "2026-09-02T02:00:00Z")
            self.assertEqual(macro["known_at_utc"], "2026-09-05T14:40:00Z")
            self.assertEqual(macro["qualitative_confidence"], "MEDIUM")
            self.assertEqual(market["state_label"], "SHORT_RATE_AND_FX_PRICING_REPRICED_LOWER_AFTER_POLICY_PATH_SURPRISE")
            self.assertIsNone(market["effective_at"])
            self.assertEqual(market["effective_date"], "2026-09-02")
            self.assertEqual(market["effective_time_precision"], "CIVIL_DATE")
            self.assertEqual(market["known_at_utc"], "2026-09-05T14:40:00Z")
            self.assertEqual(market["qualitative_confidence"], "MEDIUM")
            self.assertEqual(market["analytical_association"]["causal_status"], "OBSERVED_ASSOCIATION")
            self.assertIsNone(market["effective_window"]["exact_start_at_utc"])
            self.assertIsNone(market["effective_window"]["exact_end_at_utc"])
            self.assertTrue(all(move["before_value"] is None for move in market["market_measurements"]))
            self.assertFalse(any("actor_id" in row for row in bundle["admitted_components"]))
            self.assertTrue(all(row["object_sha256"] not in {EXPECTED_MACRO_CANDIDATE_HASH, EXPECTED_MARKET_CANDIDATE_HASH} for row in bundle["admitted_components"]))
        finally:
            shutil.rmtree(temporary)

    def test_snapshot_pins_production_component_hashes_and_mixed_precision(self):
        temporary = copy_data_tree()
        try:
            bundle = build_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT)
            snapshot = bundle["production_snapshot"]
            refs = {ref["component_id"]: ref for ref in snapshot["component_refs"]}
            rows = {row["component_id"]: row for row in bundle["admitted_components"]}
            self.assertEqual(snapshot["snapshot_series_id"], "WSSNAP-NZ-RBNZ-OCR-202609")
            self.assertEqual(snapshot["snapshot_revision_id"], "WSSNAP-NZ-RBNZ-OCR-202609-R1")
            self.assertEqual(set(refs), {MACRO_COMPONENT_ID, MARKET_COMPONENT_ID})
            self.assertEqual(refs[MACRO_COMPONENT_ID]["object_sha256"], rows[MACRO_COMPONENT_ID]["object_sha256"])
            self.assertEqual(refs[MARKET_COMPONENT_ID]["object_sha256"], rows[MARKET_COMPONENT_ID]["object_sha256"])
            self.assertEqual(rows[MACRO_COMPONENT_ID]["effective_time_precision"], "UTC_INSTANT")
            self.assertEqual(rows[MARKET_COMPONENT_ID]["effective_time_precision"], "CIVIL_DATE")
            self.assertIsNone(snapshot["effective_as_of_utc"])
        finally:
            shutil.rmtree(temporary)

    def test_admission_transaction_and_simulation_are_distinct_from_review(self):
        temporary = copy_data_tree()
        try:
            bundle = build_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT)
            transaction = bundle["admission_transaction"]
            self.assertEqual(transaction["transaction_id"], ADMISSION_TRANSACTION_ID)
            self.assertNotEqual(transaction["transaction_id"], REVIEW_TRANSACTION_ID)
            self.assertEqual(transaction["transaction_type"], "WORLD_STATE_PRODUCTION_ADMISSION")
            self.assertEqual(transaction["decision"], "ACCEPTED")
            self.assertEqual(transaction["snapshot_fingerprint"], bundle["production_snapshot"]["object_sha256"])
            self.assertEqual(transaction["pre_state_hashes"], state_hashes(bundle["before_state"]))
            self.assertEqual(transaction["post_state_hashes"], state_hashes(bundle["after_state"]))
            self.assertEqual(bundle["simulation"]["status"], "PASS")
            self.assertEqual(validate_production_state(temporary, enforce_first_population=False), [])
        finally:
            shutil.rmtree(temporary)

    def test_materialisation_preserves_health_and_adds_exact_two_components(self):
        temporary = copy_data_tree()
        try:
            before_state = load_production_state(temporary)
            upstream_before = upstream_hashes(temporary)
            bundle = materialize_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            state = load_production_state(temporary)
            self.assertTrue(bundle["materialized"])
            self.assertEqual(len(state["actors"]), 0)
            self.assertEqual(len(state["components"]), 3)
            self.assertEqual(len(state["snapshots"]), 2)
            self.assertEqual(len(state["admissions"]), 2)
            self.assertEqual(state["components"][0], before_state["components"][0])
            self.assertEqual(state["snapshots"][0], before_state["snapshots"][0])
            self.assertEqual(state["admissions"][0], before_state["admissions"][0])
            self.assertEqual(validate_production_state(temporary, enforce_first_population=False), [])
            self.assertEqual(upstream_before, upstream_hashes(temporary))
            self.assertTrue((temporary / "data/world_state_audit/STEP11B_RBNZ_COMPONENT_REVIEW_ACCEPTED.json").exists())
            self.assertTrue((temporary / "data/world_state_audit/STEP11B_RBNZ_COMPONENT_REVIEW_ACCEPTED.md").exists())
            self.assertFalse((temporary / "data/world_state/actor_registry.json").exists())
        finally:
            shutil.rmtree(temporary)

    def test_atomic_preflight_failure_leaves_temporary_state_unchanged(self):
        temporary = copy_data_tree()
        try:
            package_path = temporary / "data/world_state_audit/STEP11A1_RBNZ_CANDIDATE_REVIEW_PENDING_CORRECTED.json"
            package = json.loads(package_path.read_text())
            package["dimension_assessment_candidates"][0]["state_label"] = "TAMPERED"
            package_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
            before = all_data_hashes(temporary)
            with self.assertRaises(WorldStateRbnzAdmissionError):
                materialize_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            self.assertEqual(before, all_data_hashes(temporary))
        finally:
            shutil.rmtree(temporary)

    def test_original_malformed_candidate_cannot_be_admitted(self):
        temporary = copy_data_tree()
        try:
            corrected_path = temporary / "data/world_state_audit/STEP11A1_RBNZ_CANDIDATE_REVIEW_PENDING_CORRECTED.json"
            corrected_path.write_bytes(ORIGINAL.read_bytes())
            before = all_data_hashes(temporary)
            with self.assertRaises(WorldStateRbnzAdmissionError):
                materialize_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            self.assertEqual(before, all_data_hashes(temporary))
        finally:
            shutil.rmtree(temporary)

    def test_historical_queries_and_multi_series_composition_are_correct(self):
        temporary = copy_data_tree()
        try:
            materialize_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            before_known = read_production_world_state(query("2026-09-05T14:39:59Z"), root=temporary)
            before_admission = read_production_world_state(query("2026-09-28T04:27:16Z"), root=temporary)
            after = read_production_world_state(query("2026-09-28T04:27:17Z"), root=temporary)
            self.assertEqual(before_known["component_count"], 0)
            self.assertNotIn(MACRO_COMPONENT_ID, {row["component_id"] for row in before_known["selected_components"]})
            self.assertEqual(before_admission["component_count"], 1)
            self.assertEqual({row["component_id"] for row in after["selected_components"]}, {"WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN-202609-001", MACRO_COMPONENT_ID, MARKET_COMPONENT_ID})
            self.assertEqual(after["composition_view"]["composition_type"], COMPOSITION_TYPE)
            self.assertEqual(after["composition_view"]["composition_atomicity"], COMPOSITION_ATOMICITY)
            self.assertEqual(after["composition_view"]["selected_series_count"], 2)
            self.assertIsNone(after["composition_view"]["admission_transaction_id"])
            macro_before = read_production_world_state(query(ADMITTED_AT, mode="EFFECTIVE_AS_OF", effective="2026-09-02T01:59:59Z", dimensions=["MACROECONOMIC_FINANCIAL_CONDITIONS"]), root=temporary)
            macro_after = read_production_world_state(query(ADMITTED_AT, mode="EFFECTIVE_AS_OF", effective="2026-09-02T02:00:00Z", dimensions=["MACROECONOMIC_FINANCIAL_CONDITIONS"]), root=temporary)
            market_before = read_production_world_state(query(ADMITTED_AT, mode="EFFECTIVE_AS_OF", effective="2026-09-01T23:59:59Z", dimensions=["MARKETS_AS_SENSORS"]), root=temporary)
            market_after = read_production_world_state(query(ADMITTED_AT, mode="EFFECTIVE_AS_OF", effective="2026-09-02T00:00:00Z", dimensions=["MARKETS_AS_SENSORS"]), root=temporary)
            self.assertEqual(macro_before["component_count"], 0)
            self.assertEqual(macro_after["component_count"], 1)
            self.assertEqual(market_before["component_count"], 0)
            self.assertEqual(market_after["component_count"], 1)
            self.assertIsNone(market_after["selected_components"][0]["effective_at"])
            self.assertEqual(market_after["selected_components"][0]["effective_time_precision"], "CIVIL_DATE")
        finally:
            shutil.rmtree(temporary)

    def test_production_state_is_unchanged_by_read_only_build_and_original_artifact_survives(self):
        before = load_production_state(ROOT)
        original = ORIGINAL.read_bytes()
        upstream_before = upstream_hashes(ROOT)
        temporary = copy_data_tree()
        try:
            bundle = build_rbnz_admission(temporary, REVIEWED_AT, ADMITTED_AT)
        finally:
            shutil.rmtree(temporary)
        self.assertEqual(before, load_production_state(ROOT))
        self.assertEqual(original, ORIGINAL.read_bytes())
        self.assertEqual(upstream_before, upstream_hashes(ROOT))
        self.assertFalse(bundle["package"]["public_projection_permitted"])


if __name__ == "__main__":
    unittest.main()
