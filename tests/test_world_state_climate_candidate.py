from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_climate_candidate import (  # noqa: E402
    ANALYSIS_ID,
    BASELINE_ID,
    BASELINE_REVISION_ID,
    CONSTRUCTION_CUTOFF,
    DIMENSION_ID,
    DIMENSION_REVISION_ID,
    EVIDENCE_IDS,
    OCCURRENCE_ID,
    build_climate_candidate,
    validate_climate_candidate_package,
)
from world_signals.world_state_history import fingerprint  # noqa: E402


PACKAGE_PATH = ROOT / "data/world_state_audit/STEP14A_AU_TROPICAL_CYCLONE_CANDIDATE_REVIEW_PENDING.json"


def _hashes() -> dict[str, str]:
    paths = []
    for directory in ("canonical", "analysis", "relationships", "risks", "scenarios", "forecasts", "outcomes", "evaluation", "world_state"):
        paths.extend((ROOT / "data" / directory).rglob("*"))
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


class WorldStateClimateCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = build_climate_candidate(ROOT)
        cls.baseline = cls.package["baseline_candidate"]
        cls.dimension = cls.package["dimension_assessment_candidate"]
        cls.protected_before = _hashes()

    def test_real_analysis_and_canonical_lineage_is_pinned(self):
        self.assertEqual(self.package["analysis_id"], ANALYSIS_ID)
        self.assertEqual(self.package["canonical_occurrence_id"], OCCURRENCE_ID)
        self.assertEqual(
            {row["object_id"] for row in self.package["source_manifest"] if row["layer"] == "ANALYSIS_EVIDENCE"},
            set(EVIDENCE_IDS),
        )
        self.assertEqual(validate_climate_candidate_package(self.package), [])

    def test_analysis_and_four_evidence_rows_are_exactly_pinned(self):
        ids = {row["object_id"] for row in self.package["source_manifest"]}
        self.assertIn(ANALYSIS_ID, ids)
        self.assertIn(OCCURRENCE_ID, ids)
        self.assertTrue(set(EVIDENCE_IDS) <= ids)
        for entry in self.package["source_manifest"]:
            self.assertEqual(entry["object_sha256"], fingerprint(entry["object"]))

    def test_baseline_is_standalone_official_reference(self):
        self.assertEqual(self.baseline["component_type"], "BASELINE")
        self.assertEqual(self.baseline["component_id"], BASELINE_ID)
        self.assertEqual(self.baseline["revision_id"], BASELINE_REVISION_ID)
        self.assertEqual(self.baseline["basis"], "OFFICIAL_REFERENCE")
        self.assertEqual(self.baseline["scope"]["geographic_scope"], "Australian tropical cyclone region")
        self.assertEqual(self.baseline["baseline_value_or_label"], "about 10 Australian-region tropical cyclones per season")

    def test_baseline_preserves_source_native_precision(self):
        window = self.baseline["reference_window"]
        self.assertEqual(window["source_native_label"], "since 1980–81")
        self.assertIsNone(window["exact_start"])
        self.assertIsNone(window["exact_end"])
        self.assertIsNone(self.baseline["effective_at"])
        self.assertEqual(self.baseline["effective_time_precision"], "SOURCE_NATIVE_SEASON_SERIES")

    def test_baseline_is_not_a_forecast_or_anomaly(self):
        text = json.dumps(self.baseline)
        self.assertNotIn("FORECAST", text)
        self.assertNotIn("ANOMALY", text)
        self.assertIn("not a 2025–26 season-specific Forecast", " ".join(self.baseline["limitations"]))

    def test_dimension_is_narrow_climate_physical_risk(self):
        self.assertEqual(self.dimension["component_type"], "DIMENSION_ASSESSMENT")
        self.assertEqual(self.dimension["component_id"], DIMENSION_ID)
        self.assertEqual(self.dimension["revision_id"], DIMENSION_REVISION_ID)
        self.assertEqual(self.dimension["dimension"], "CLIMATE_PHYSICAL_RISK")
        self.assertEqual(self.dimension["scope"]["jurisdictions"], ["Australia"])
        self.assertEqual(self.dimension["scope"]["systems"], ["AUSTRALIAN_TROPICAL_CYCLONE_REGION"])

    def test_realised_measurements_are_preserved(self):
        actuals = {row["metric"]: row["value"] for row in self.dimension["realised_measurements"]}
        self.assertEqual(actuals["australian_region_tropical_cyclone_count"], 11)
        self.assertEqual(actuals["severe_tropical_cyclone_count"], 7)
        self.assertEqual(actuals["category_5_tropical_cyclone_count"], 2)
        self.assertEqual(actuals["mainland_landfall_count_at_tropical_cyclone_strength"], 4)
        self.assertEqual(actuals["mainland_crossing_count_at_tropical_low_strength"], 2)

    def test_direction_persistence_and_breadth_do_not_overclaim(self):
        self.assertEqual(self.dimension["direction"], "NOT_ASSESSED")
        self.assertEqual(self.dimension["persistence"], "COMPLETED_HISTORICAL_WINDOW")
        self.assertEqual(self.dimension["breadth"], "REGIONAL_HAZARD_WINDOW")
        self.assertEqual(self.dimension["what_surprised"], "NOT_ESTABLISHED")

    def test_climatology_does_not_become_forecast_surprise(self):
        comparison = self.dimension["baseline_comparison"]
        self.assertEqual(comparison["forecast_surprise"], "NOT_ESTABLISHED")
        self.assertNotIn("+1", json.dumps(self.dimension))
        self.assertNotIn("forecast error", json.dumps(self.dimension).lower())

    def test_hazard_does_not_become_impact_or_attribution(self):
        for forbidden_field in ("damage", "insured_loss", "economic_impact", "supply_chain_impact", "climate_attribution", "enso_attribution"):
            self.assertNotIn(forbidden_field, self.dimension)
        self.assertIn("damage", " ".join(self.dimension["limitations"]).lower())
        self.assertIn("attribution", " ".join(self.dimension["limitations"]).lower())
        self.assertEqual(self.dimension["common_driver_context"]["causal_status"], "NOT_A_CAUSAL_CLAIM")

    def test_no_downstream_or_actor_population_is_created(self):
        for field in ("actor_state_assertions", "implementation_claims", "relationships", "risks_regimes", "scenarios", "forecasts", "outcomes", "negative_evidence", "competing_hypotheses", "model_disagreements"):
            self.assertEqual(self.package[field], [])
        self.assertEqual(self.package["production_state"]["actors"], 0)
        self.assertEqual(self.package["production_state"]["components"], 5)
        self.assertEqual(self.package["production_state"]["snapshots"], 3)
        self.assertEqual(self.package["production_state"]["admissions"], 3)
        self.assertEqual(self.package["production_state"]["baseline_components"], 0)

    def test_candidate_dependency_is_explicit_but_dispositions_are_independent(self):
        self.assertEqual(self.dimension["baseline_ref"], BASELINE_REVISION_ID)
        self.assertEqual({row["candidate_id"] for row in self.package["candidate_dispositions"]}, {BASELINE_REVISION_ID, DIMENSION_REVISION_ID})
        self.assertTrue(all(row["decision"] is None for row in self.package["candidate_dispositions"]))

    def test_historical_effective_and_knowledge_time_are_separate(self):
        self.assertIsNone(self.dimension["effective_at"])
        self.assertEqual(self.dimension["effective_period"]["start_local"], "2025-11-01")
        self.assertEqual(self.dimension["effective_period"]["end_local"], "2026-04-30")
        self.assertEqual(self.dimension["known_at_utc"], "2026-09-05T23:35:00Z")
        self.assertEqual(self.package["constructed_at_utc"], CONSTRUCTION_CUTOFF)
        self.assertNotEqual(self.dimension["known_at_utc"], self.package["constructed_at_utc"])

    def test_completed_historical_state_has_no_freshness_policy_or_current_claim(self):
        self.assertNotIn("freshness", self.dimension)
        self.assertIn("no current Australian cyclone-risk claim", " ".join(self.dimension["limitations"]))
        self.assertIn("no current freshness policy", " ".join(self.dimension["limitations"]))

    def test_shared_source_family_does_not_become_independent_corroboration(self):
        uncertainty = next(row for row in self.dimension["uncertainties"] if row["type"] == "PROVENANCE_SOURCE")
        self.assertIn("one institutional source family", uncertainty["description"])
        self.assertIn("not independent corroboration", uncertainty["description"])

    def test_model_provenance_is_fail_honest(self):
        provenance = self.dimension["model_provenance"]
        self.assertEqual(provenance["model_identity"], "UNAVAILABLE")
        self.assertEqual(provenance["model_version"], "UNAVAILABLE")
        self.assertEqual(provenance["factual_evidence_status"], "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION")

    def test_candidates_are_internal_review_pending_and_unadmitted(self):
        for candidate in (self.baseline, self.dimension):
            self.assertEqual(candidate["review_state"], "UNDER_REVIEW")
            self.assertEqual(candidate["lifecycle_state"], "UNRESOLVED")
            self.assertIsNone(candidate["reviewed_at_utc"])
            self.assertIsNone(candidate["admitted_at_utc"])
            self.assertIsNone(candidate["admission_transaction_id"])
            self.assertEqual(candidate["visibility"], "INTERNAL_ONLY")
        self.assertEqual(self.package["proposed_snapshot"]["write_targets"], [])

    def test_fingerprints_are_deterministic_and_separate(self):
        again = build_climate_candidate(ROOT)
        self.assertEqual(self.package, again)
        self.assertNotEqual(self.package["baseline_candidate_fingerprint"], self.package["dimension_candidate_fingerprint"])
        self.assertEqual(self.package["source_manifest_sha256"], fingerprint(self.package["source_manifest"]))

    def test_tampered_manifest_or_candidate_fails_validation(self):
        changed = deepcopy(self.package)
        changed["source_manifest"][0]["object"]["tampered"] = True
        self.assertNotEqual(changed["source_manifest_sha256"], fingerprint(changed["source_manifest"]))
        self.assertTrue(validate_climate_candidate_package(changed))
        changed = deepcopy(self.package)
        changed["dimension_assessment_candidate"]["realised_measurements"][0]["value"] = 12
        self.assertTrue(validate_climate_candidate_package(changed))

    def test_build_does_not_mutate_governed_or_production_state(self):
        build_climate_candidate(ROOT)
        self.assertEqual(self.protected_before, _hashes())
        self.assertEqual(self.package["production_state"]["writes"], [])

    def test_retained_package_matches_builder_when_present(self):
        if PACKAGE_PATH.exists():
            retained = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
            # The retained Step 14A artifact predates later Step 14C
            # admissions.  Its candidate and lineage remain identical; the
            # mutable repository population note is not candidate semantics.
            retained.pop("production_state", None)
            current = deepcopy(self.package)
            current.pop("production_state", None)
            self.assertEqual(retained, current)


if __name__ == "__main__":
    unittest.main()
