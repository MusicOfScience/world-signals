"""Step 14E: native internal contract, legacy-public equivalence and no admission."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from world_signals.analysis import public_analysis_projection, validate_analysis
from world_signals.analysis_publication import PUBLIC_FIELDS, INTERNAL_FIELDS, publication_errors
from world_signals.analysis_revision_projection import public_analysis_projection_with_revision_contract
from world_signals.official_projection_candidate import FILES, protected_file_hashes
from world_signals.official_projection_review import (
    AUDIT_AXES, EPISTEMIC_CLASSES, EDGE_CLASSES, CORROBORATION, ERROR_INTERPRETATION,
    step14d_native_extension, validate_official_projection_review,
)
from world_signals.world_state_history import fingerprint
from world_signals.world_state_admission import load_production_state


def load(path):
    return json.loads((ROOT / path).read_text())


def generic_extension():
    ref = [{"asset_id": "SYNTHETIC-MODEL", "locator": "Table 1"}]
    assets = [{"asset_id": "SYNTHETIC-MODEL", "url": "https://example.invalid/model",
               "sha256": "a" * 64, "source_family": "SYNTHETIC_INSTITUTION",
               "source_class": "OFFICIAL_PROJECTION", "vintage": "2026"},
              {"asset_id": "SYNTHETIC-PRIOR", "url": "https://example.invalid/prior",
               "sha256": "b" * 64, "source_family": "SYNTHETIC_INSTITUTION",
               "source_class": "PRIOR_OFFICIAL_PROJECTION", "vintage": "2020"}]
    return {
        "contract_version": "0.1", "visibility": "INTERNAL_ONLY",
        "projection_framework": {"projection_horizon": "2040",
            "publication_fact": {"epistemic_class": "PUBLICATION_FACT", "statement": "Synthetic model published."}, "source_refs": ref},
        "projection_outputs": [{"projection_id": "OUTPUT-A", "metric": "synthetic population",
            "value": 10, "unit": "million persons", "projection_horizon": "2040", "reference_period": "2026",
            "epistemic_class": "OFFICIAL_PROJECTION", "assumption_refs": ["ASSUMPTION-A"],
            "sensitivity_refs": ["SENSITIVITY-A"], "comparison_refs": [], "source_refs": ref,
            "limitations": ["Conditional model, not observation."]}],
        "model_assumptions": [{"assumption_id": "ASSUMPTION-A", "assumption_type": "DEMOGRAPHIC_INPUT",
            "domain": "DEMOGRAPHY", "basis_kind": "EMPIRICAL_EXTRAPOLATION", "statement": "Synthetic continuation.",
            "value_or_rule": "Continuation", "unit": "source-native rule", "reference_period": "2026",
            "projection_horizon": "2040", "issuer_rationale": "Synthetic model method.", "source_refs": ref,
            "output_dependencies": ["OUTPUT-A"], "sensitivity_refs": ["SENSITIVITY-A"], "epistemic_class": "MODEL_ASSUMPTION"}],
        "sensitivity_cases": [{"sensitivity_id": "SENSITIVITY-A", "epistemic_class": "SENSITIVITY_CASE",
            "assumption_refs": ["ASSUMPTION-A"], "shock": {"delta": 1}, "unit": "percentage points",
            "projection_horizon": "2040", "results": {"population": 11}, "affected_output_refs": ["OUTPUT-A"],
            "source_refs": ref, "limitations": ["Conditional, no probability."]}],
        "assumption_audit": [{"assumption_id": "ASSUMPTION-A", **{axis: {
            "finding": "NOT_ESTABLISHED", "explanation": "No independent synthetic evidence.",
            "source_refs": ref, "limitations": ["Unresolved."]} for axis in AUDIT_AXES}}],
        "comparison_baseline": {"vintage": "2020", "horizon": "2040", "epistemic_class": "PRIOR_OFFICIAL_PROJECTION", "source_refs": [{"asset_id": "SYNTHETIC-PRIOR", "locator": "Table 1"}]},
        "source_manifest": assets, "source_manifest_sha256": fingerprint(assets),
        "corroboration_policy": CORROBORATION, "error_interpretation": ERROR_INTERPRETATION,
        "limitations": ["Test-only."], "dependency_map": [],
    }


class OfficialProjectionAnalysisContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = load("data/analysis/schema.json")
        self.evidence = load("data/analysis/evidence_registry.json")
        self.reviews = load("data/analysis/event_reviews.json")
        self.canonical = load("data/canonical/registry.json")
        self.ext = generic_extension()

    def reject(self, mutation, message):
        mutation(self.ext)
        errors = validate_official_projection_review(self.ext)
        self.assertTrue(errors)
        self.assertIn(message, "; ".join(errors))

    def test_legacy_reviews_evidence_and_optional_absence_validate(self):
        self.assertTrue(validate_analysis(self.schema, self.evidence, self.reviews, self.canonical).ok)
        legacy = [row for row in self.reviews["reviews"] if self.reviews["publication_decisions"][row["analysis_id"]] == "PUBLIC"]
        self.assertEqual(len(legacy), 22)
        self.assertTrue(all("official_projection_review" not in row for row in legacy))

    def test_generic_non_treasury_extension_valid(self):
        self.assertEqual(validate_official_projection_review(self.ext), ())

    def test_exact_step14d_readonly_native_compatibility_and_lossless_material(self):
        package = {k: load("data/analysis/" + name) for k, name in FILES.items()}
        before = fingerprint(package)
        native = step14d_native_extension(package)
        self.assertEqual(validate_official_projection_review(native), ())
        self.assertEqual(before, fingerprint(package))
        self.assertEqual([r["value"] for r in native["projection_outputs"]], [r["value"] for r in package["projection_inventory"]["projection_outputs"]])
        self.assertEqual(native["assumption_audit"], package["assumption_audit"]["assumption_audit"])
        self.assertEqual(native["dependency_map"], package["assumption_audit"]["dependency_map"])
        self.assertEqual(len(native["feedback_cycles"]), 1)
        review = deepcopy(package["analysis_candidate"]["review"])
        review["official_projection_review"] = native
        report = validate_analysis(self.schema, {"evidence": package["analysis_candidate"]["candidate_local_evidence"]}, {"reviews": [review]}, self.canonical)
        self.assertTrue(report.ok, report.errors)

    def test_future_projection_cannot_enter_actuals(self):
        for field in ("epistemic_class", "projection_class"):
            with self.subTest(field=field):
                self.reviews["reviews"][0]["what_happened"]["actuals"] = [{field: "OFFICIAL_PROJECTION", "value": 10}]
                self.assertFalse(validate_analysis(self.schema, self.evidence, self.reviews, self.canonical).ok)

    def test_publication_metadata_fact_may_be_actual_not_future_outcome(self):
        self.reviews["reviews"][0]["what_happened"]["actuals"] = [{"epistemic_class": "PUBLICATION_FACT", "metric": "publication_date", "value": "2026-09-02"}]
        self.assertTrue(validate_analysis(self.schema, self.evidence, self.reviews, self.canonical).ok)

    def test_output_and_assumption_identity_collision_rejected(self):
        self.reject(lambda e: e["model_assumptions"][0].update(assumption_id="OUTPUT-A"), "distinct")

    def test_policy_setting_not_empirical_assumption(self):
        self.ext["model_assumptions"][0].update(assumption_type="FISCAL_POLICY_SETTING", basis_kind="MAINTAINED_POLICY_SETTING")
        self.assertEqual(validate_official_projection_review(self.ext), ())
        self.reject(lambda e: e["model_assumptions"][0].update(basis_kind="EMPIRICAL_EXTRAPOLATION"), "policy")

    def test_sensitivity_horizon_required(self):
        self.reject(lambda e: e["sensitivity_cases"][0].pop("projection_horizon"), "horizon")

    def test_sensitivity_probability_and_scenario_identity_prohibited(self):
        for field in ("probability", "scenario_id", "forecast_id"):
            self.ext = generic_extension()
            self.reject(lambda e: e["sensitivity_cases"][0].update({field: 0.5}), "separate contract")

    def test_projection_cannot_reclassify_as_downstream_object(self):
        for category in ("FORECAST", "OBSERVATION", "WORLD_STATE", "SIGNAL", "OUTCOME"):
            self.ext = generic_extension()
            self.reject(lambda e: e["projection_outputs"][0].update(epistemic_class=category), "not Forecast")

    def test_ten_axes_all_required(self):
        for axis in AUDIT_AXES:
            self.ext = generic_extension()
            self.reject(lambda e: e["assumption_audit"][0].pop(axis), "ten audit")

    def test_unresolved_requires_explanation(self):
        self.reject(lambda e: e["assumption_audit"][0][AUDIT_AXES[0]].pop("explanation"), "explanation")

    def test_audit_scores_ratings_grades_recursive_rejected(self):
        for field in ("score", "rating", "grade", "overall_score", "assumption_quality_score", "quality_score"):
            self.ext = generic_extension()
            self.reject(lambda e: e["assumption_audit"][0][AUDIT_AXES[0]].update({field: 5}), "scores/ratings/grades")

    def comparison(self):
        self.ext["projection_comparison"] = [{"comparison_id": "C1", "prior_vintage": "2020", "current_vintage": "2026",
            "prior_horizon": "2040", "current_horizon": "2040", "comparability": "DIRECTLY_COMPARABLE",
            "method_basis": "Same synthetic model and unit.", "method_compatibility": "COMPATIBLE",
            "calculation_basis": "Matched synthetic units and horizon.", "prior_value": 9, "current_value": 10,
            "difference": 1, "unit": "million persons", "source_refs": [*self.ext["projection_outputs"][0]["source_refs"], {"asset_id": "SYNTHETIC-PRIOR", "locator": "Table 1"}]}]
        return self.ext["projection_comparison"][0]

    def test_direct_comparison_error_gated_and_arithmetic(self):
        self.comparison()
        self.assertEqual(validate_official_projection_review(self.ext), ())
        self.reject(lambda e: e["projection_comparison"][0].update(difference=7), "arithmetic")

    def test_noncomparable_forbids_error_and_difference(self):
        self.comparison().update(comparability="NOT_DIRECTLY_COMPARABLE", difference=None)
        self.assertEqual(validate_official_projection_review(self.ext), ())
        self.reject(lambda e: e["projection_comparison"][0].update(error=1), "noncomparable")

    def test_real_dollar_incompatible_basis_forbids_subtraction(self):
        self.comparison().update(unit="real AUD", value_basis={"prior": "2020 dollars", "current": "2026 dollars"})
        self.assertTrue(validate_official_projection_review(self.ext))
        self.ext["projection_comparison"][0]["value_basis"]["current"] = "2020 dollars"
        self.assertEqual(validate_official_projection_review(self.ext), ())

    def test_unlike_horizons_forbid_difference(self):
        self.comparison().update(current_horizon="2050")
        self.assertTrue(validate_official_projection_review(self.ext))

    def test_unestablished_or_incompatible_methods_block_calculation(self):
        for compatibility in ("INCOMPATIBLE", "NOT_ESTABLISHED", "QUALIFIED"):
            self.ext = generic_extension()
            self.comparison().update(method_compatibility=compatibility)
            self.assertTrue(validate_official_projection_review(self.ext))
        self.ext["projection_comparison"][0]["comparability"] = "QUALIFIED_COMPARISON"
        self.assertEqual(validate_official_projection_review(self.ext), ())

    def test_bad_faith_inference_not_model_error_policy(self):
        self.reject(lambda e: e.update(error_interpretation="MODEL_MISS_PROVES_MANIPULATION"), "bad faith")

    def edge(self):
        self.ext["dependency_map"] = [{"edge_id": "E1", "from_ref": "ASSUMPTION-A", "to_ref": "OUTPUT-A",
            "epistemic_class": "MODEL_DEFINED", "mechanism": "Synthetic model definition.", "production_relationship": False,
            "source_refs": self.ext["projection_outputs"][0]["source_refs"], "limitations": ["Not causal fact."]}]

    def test_dependency_vocabulary_and_no_relationship_promotion(self):
        self.edge()
        for label in EDGE_CLASSES:
            self.ext["dependency_map"][0]["epistemic_class"] = label
            self.assertEqual(validate_official_projection_review(self.ext), ())
        self.reject(lambda e: e["dependency_map"][0].update(production_relationship=True), "not Relationship")

    def test_dependency_unknown_refs_and_classes_fail(self):
        self.edge()
        self.reject(lambda e: e["dependency_map"][0].update(to_ref="MISSING"), "refs")

    def test_undeclared_cycle_rejected(self):
        self.edge()
        reverse = deepcopy(self.ext["dependency_map"][0])
        reverse.update(edge_id="E2", from_ref="OUTPUT-A", to_ref="ASSUMPTION-A")
        self.ext["dependency_map"].append(reverse)
        self.assertTrue(validate_official_projection_review(self.ext))

    def test_validation_no_transitive_generation_no_confidence_uplift(self):
        self.edge()
        before = fingerprint(self.ext)
        self.assertEqual(validate_official_projection_review(self.ext), ())
        self.assertEqual(before, fingerprint(self.ext))
        self.reject(lambda e: e.update(corroboration_policy="COUNT_DEPENDENT_OUTPUTS_AS_INDEPENDENT"), "confidence")

    def test_unknown_output_assumption_sensitivity_comparison_refs_fail(self):
        for field in ("assumption_refs", "sensitivity_refs", "comparison_refs"):
            self.ext = generic_extension()
            self.reject(lambda e: e["projection_outputs"][0].update({field: ["MISSING"]}), "unknown")

    def test_duplicate_ids_and_missing_provenance_fail(self):
        for section in ("projection_outputs", "model_assumptions", "sensitivity_cases"):
            self.ext = generic_extension()
            self.reject(lambda e: e[section].append(deepcopy(e[section][0])), "duplicate")
        self.ext = generic_extension()
        self.reject(lambda e: e["projection_outputs"][0].update(source_refs=[]), "source references")

    def test_source_hash_tampering_fails(self):
        self.reject(lambda e: e["source_manifest"][0].update(sha256="b" * 64), "manifest mismatch")

    def test_prior_baseline_must_resolve_exact_original_vintage(self):
        self.reject(lambda e: e["comparison_baseline"].update(vintage="2010"), "vintage provenance")

    def test_comparison_requires_original_source_not_just_later_reconstruction(self):
        self.comparison().update(source_refs=self.ext["projection_outputs"][0]["source_refs"])
        self.assertTrue(validate_official_projection_review(self.ext))

    def test_actual_publication_tag_cannot_mask_projection_tag(self):
        self.reviews["reviews"][0]["what_happened"]["actuals"] = [{"epistemic_class": "PUBLICATION_FACT", "projection_class": "OFFICIAL_PROJECTION", "value": 10}]
        self.assertFalse(validate_analysis(self.schema, self.evidence, self.reviews, self.canonical).ok)

    def test_nan_assumption_value_rejected(self):
        self.reject(lambda e: e["model_assumptions"][0].update(value_or_rule=float("nan")), "compliant")

    def test_missing_audit_source_and_limitations_rejected(self):
        for field in ("source_refs", "limitations"):
            self.ext = generic_extension()
            self.assertTrue(validate_official_projection_review({**self.ext, "assumption_audit": [
                {**self.ext["assumption_audit"][0], AUDIT_AXES[0]: {
                    **self.ext["assumption_audit"][0][AUDIT_AXES[0]], field: []}}
            ]}))

    def test_dependency_unknown_epistemic_class_rejected(self):
        self.edge()
        self.reject(lambda e: e["dependency_map"][0].update(epistemic_class="CAUSAL_FACT"), "not Relationship")

    def test_projection_numeric_range_and_qualitative_values(self):
        for value in (12.5, {"lower": 10, "upper": 12}, "Source-native conditional trajectory"):
            self.ext["projection_outputs"][0]["value"] = value
            self.assertEqual(validate_official_projection_review(self.ext), ())
        for value in (True, float("nan"), {"lower": 12, "upper": 10}):
            self.ext["projection_outputs"][0]["value"] = value
            self.assertTrue(validate_official_projection_review(self.ext))

    def test_malformed_horizon_and_container_fail(self):
        for horizon in (None, "", "not a period", "2040-13-40", {"start_date": "2040-01-01", "end_date": "2030-01-01"}):
            self.ext["projection_outputs"][0]["projection_horizon"] = horizon
            self.assertTrue(validate_official_projection_review(self.ext))
        self.assertTrue(validate_official_projection_review([]))

    def test_legacy_public_spine_and_evidence_semantically_equal(self):
        projection = public_analysis_projection_with_revision_contract(self.schema, self.evidence, self.reviews, self.canonical)
        for source, public in zip(self.reviews["reviews"], projection["reviews"]):
            self.assertFalse(publication_errors(source))
            for key in PUBLIC_FIELDS:
                if key in source:
                    self.assertEqual(public[key], source[key])
            self.assertFalse(set(INTERNAL_FIELDS) & public.keys())
            refs = {ref for section in PUBLIC_FIELDS for ref in self.find_refs(source.get(section))}
            self.assertEqual({r["evidence_id"] for r in public["evidence"]}, refs)
            for row in public["evidence"]:
                original = next(e for e in self.evidence["evidence"] if e["evidence_id"] == row["evidence_id"])
                for key, value in row.items():
                    self.assertEqual(value, original.get(key))

    @staticmethod
    def find_refs(value):
        if isinstance(value, dict):
            return [ref for k, v in value.items() for ref in (v if k == "evidence_refs" else OfficialProjectionAnalysisContractTests.find_refs(v))]
        if isinstance(value, list):
            return [ref for v in value for ref in OfficialProjectionAnalysisContractTests.find_refs(v)]
        return []

    def test_unknown_top_level_secret_fails_native_and_both_publishers(self):
        self.reviews["reviews"][0]["secret_internal_field"] = "never public"
        report = validate_analysis(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertIn("UNCLASSIFIED_ANALYSIS_PUBLICATION_FIELD", ";".join(report.errors))
        for projector in (public_analysis_projection, public_analysis_projection_with_revision_contract):
            with self.assertRaisesRegex(ValueError, "UNCLASSIFIED_ANALYSIS_PUBLICATION_FIELD"):
                projector(self.schema, self.evidence, self.reviews, self.canonical)

    def test_native_extension_omitted_by_both_public_paths(self):
        baseline = public_analysis_projection_with_revision_contract(self.schema, self.evidence, self.reviews, self.canonical)
        self.reviews["reviews"][0]["official_projection_review"] = self.ext
        self.assertTrue(validate_analysis(self.schema, self.evidence, self.reviews, self.canonical).ok)
        for projector in (public_analysis_projection, public_analysis_projection_with_revision_contract):
            result = projector(self.schema, self.evidence, self.reviews, self.canonical)
            self.assertNotIn("SYNTHETIC-MODEL", json.dumps(result))
            self.assertEqual(result["reviews"], baseline["reviews"])

    def test_internal_field_classification_and_unavailable_private_metadata(self):
        for field in INTERNAL_FIELDS:
            if field not in {"official_projection_review", "revision_of_analysis_id", "analysis_revision_kind", "analysis_revision_reason"}:
                self.reviews["reviews"][0][field] = {"private": "STEP14E_PRIVATE_SENTINEL"}
        public = public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)
        self.assertNotIn("STEP14E_PRIVATE_SENTINEL", json.dumps(public))

    def test_public_copy_does_not_alias_or_mutate_source(self):
        before = fingerprint(self.reviews)
        public = public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)
        public["reviews"][0]["what_happened"]["summary"] = "reader-side mutation"
        self.assertEqual(before, fingerprint(self.reviews))

    def test_schema_taxonomies_match_native_validator(self):
        ext = self.schema["optional_extensions"]["official_projection_review"]
        self.assertEqual(set(ext["epistemic_classes"]), EPISTEMIC_CLASSES)
        self.assertEqual(set(ext["dependency_classes"]), EDGE_CLASSES)
        self.assertEqual(ext["audit_axes"], list(AUDIT_AXES))
        self.assertFalse(ext["required"] or ext["public_projection_permitted"])

    def test_igr_not_public_and_world_state_counts_unchanged(self):
        self.assertNotIn("WSAN-AU-IGR-20260921-001", json.dumps(public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)))
        state = load_production_state(ROOT)
        self.assertEqual({key: len(state[key]) for key in ("components", "snapshots", "admissions", "actors")},
                         {"components": 5, "snapshots": 3, "admissions": 3, "actors": 0})

    def test_actual_production_and_upstream_readonly_hash_proof(self):
        before = protected_file_hashes(ROOT)
        public_analysis_projection(self.schema, self.evidence, self.reviews, self.canonical)
        package = {k: load("data/analysis/" + name) for k, name in FILES.items()}
        step14d_native_extension(package)
        self.assertEqual(before, protected_file_hashes(ROOT))


if __name__ == "__main__":
    unittest.main()
