"""Step 14D candidate epistemics; no online retrieval or production admission."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from world_signals.official_projection_candidate import (
    AUDIT_AXES, FILES, ProjectionCandidateError, inspect_step14d,
    protected_file_hashes, seal, validate_package,
)
from world_signals.world_state_history import fingerprint


def load_package(root=ROOT):
    return {key: json.loads((root / "data/analysis" / name).read_text()) for key, name in FILES.items()}


def relink(package):
    for key in ("evidence_manifest", "projection_inventory", "extension_candidate"):
        package[key] = seal(package[key])
    package["assumption_audit"]["inventory_fingerprint"] = package["projection_inventory"]["semantic_fingerprint"]
    package["assumption_audit"] = seal(package["assumption_audit"])
    links = package["analysis_candidate"]["official_projection_review"]
    for key, name in (("inventory_fingerprint", "projection_inventory"), ("audit_fingerprint", "assumption_audit"), ("evidence_manifest_fingerprint", "evidence_manifest"), ("extension_fingerprint", "extension_candidate")):
        links[key] = package[name]["semantic_fingerprint"]
    package["analysis_candidate"] = seal(package["analysis_candidate"])
    return package


class OfficialProjectionCandidateTests(unittest.TestCase):
    def setUp(self):
        self.package = load_package()
        self.inventory = self.package["projection_inventory"]
        self.audit = self.package["assumption_audit"]
        self.review = self.package["analysis_candidate"]["review"]

    def reject(self, mutation, message):
        mutation(self.package)
        relink(self.package)
        with self.assertRaisesRegex(ProjectionCandidateError, message):
            validate_package(self.package)

    def test_retained_package_valid_and_deterministic_without_mutation(self):
        before = fingerprint(self.package)
        a = validate_package(self.package)
        b = validate_package(deepcopy(self.package))
        self.assertEqual(a, b)
        self.assertEqual(before, fingerprint(self.package))
        self.assertEqual((a["projection_count"], a["assumption_count"]), (25, 15))

    def test_unsealed_tampering_and_broken_links_fail(self):
        self.inventory["projection_outputs"][0]["value"] = 99
        with self.assertRaisesRegex(ProjectionCandidateError, "fingerprint"):
            validate_package(self.package)
        self.package["projection_inventory"] = seal(self.inventory)
        with self.assertRaisesRegex(ProjectionCandidateError, "inventory mismatch|linked candidate"):
            validate_package(self.package)

    def test_native_analysis_and_current_identity_resolve_read_only(self):
        before = protected_file_hashes(ROOT)
        result = inspect_step14d(ROOT)
        self.assertEqual(result["native_analysis_candidate_check"], "PASS")
        self.assertEqual(result["mutation_check"], "PASS")
        self.assertEqual(before, protected_file_hashes(ROOT))

    def test_required_bundle_and_original_vintages_hash_pinned(self):
        rows = {r["asset_id"]: r for r in self.package["evidence_manifest"]["assets"]}
        for key in ("IGR2026-MAIN", "IGR2026-FACTSHEET", "IGR2026-CHARTS", "IGR2023-MAIN", "IGR2002-MAIN"):
            self.assertEqual(len(rows[key]["sha256"]), 64)
            self.assertTrue(rows[key]["url"].startswith("https://treasury.gov.au/"))
        self.assertEqual(len(self.package["evidence_manifest"]["chart_members"]), 14)
        self.assertEqual(rows["IGR2023-MAIN"]["source_class"], "PRIOR_OFFICIAL_PROJECTION")

    def test_bad_asset_hash_rejected(self):
        self.reject(lambda p: p["evidence_manifest"]["assets"][0].update(sha256="bad"), "SHA256")

    def test_asset_manifest_mismatch_rejected(self):
        self.reject(lambda p: p["evidence_manifest"].update(asset_manifest_sha256="0" * 64), "asset manifest")

    def test_chart_member_tampering_rejected(self):
        self.reject(lambda p: p["evidence_manifest"]["chart_members"][0].update(sha256="0" * 64), "chart manifest")

    def test_future_or_naive_retrieval_rejected(self):
        for timestamp in ("2026-09-30T00:00:00Z", "2026-09-28T16:25:00"):
            with self.subTest(timestamp=timestamp):
                p = load_package()
                p["evidence_manifest"]["assets"][0]["retrieved_at_utc"] = timestamp
                p["evidence_manifest"]["asset_manifest_sha256"] = fingerprint(p["evidence_manifest"]["assets"])
                with self.assertRaises(ProjectionCandidateError):
                    validate_package(relink(p))

    def test_treasury_family_is_precision_not_corroboration(self):
        assets = self.package["evidence_manifest"]["assets"]
        self.assertEqual({r["source_family"] for r in assets if r["asset_id"] in {"IGR2026-MAIN", "IGR2026-FACTSHEET", "IGR2026-CHARTS", "IGR2023-MAIN"}}, {"AU_TREASURY"})
        self.assertIn("NOT_INDEPENDENT", self.audit["corroboration_policy"])

    def test_publication_observation_assumption_projection_are_distinct(self):
        self.assertEqual(self.inventory["projection_framework"]["publication_fact"]["epistemic_class"], "PUBLICATION_FACT")
        self.assertTrue(all(r["epistemic_class"] == "OBSERVED_EVIDENCE" for r in self.inventory["observed_evidence"]))
        self.assertTrue(all(r["epistemic_class"] == "MODEL_ASSUMPTION" for r in self.inventory["model_assumptions"]))
        self.assertTrue(all(r["projection_class"] == "OFFICIAL_PROJECTION" for r in self.inventory["projection_outputs"]))
        self.assertEqual(self.review["what_happened"]["actuals"], [])

    def test_projection_cannot_be_forecast_or_actual(self):
        self.reject(lambda p: p["projection_inventory"]["projection_outputs"][0].update(projection_class="FORECAST"), "future output")

    def test_future_actuals_fail_even_if_resealed(self):
        self.reject(lambda p: p["analysis_candidate"]["review"]["what_happened"].update(actuals=[{"value": 39.3, "year": "2065-66"}]), "future projections")

    def test_units_horizons_and_refs_required(self):
        for field in ("unit", "horizon", "reference_year", "assumption_refs", "source_refs"):
            with self.subTest(field=field):
                p = load_package()
                p["projection_inventory"]["projection_outputs"][0][field] = [] if field.endswith("refs") else ""
                with self.assertRaises(ProjectionCandidateError):
                    validate_package(relink(p))

    def test_output_rejects_nan(self):
        self.inventory["projection_outputs"][0]["value"] = float("nan")
        with self.assertRaises(ValueError):
            seal(self.inventory)  # Native deterministic hash rejects non-JSON values.

    def test_unresolved_source_and_assumption_rejected(self):
        self.reject(lambda p: p["projection_inventory"]["projection_outputs"][0]["source_refs"][0].update(asset_id="MISSING"), "unresolved")

    def test_policy_setting_not_empirical_extrapolation(self):
        rows = {r["assumption_id"].split("2026-")[1]: r for r in self.inventory["model_assumptions"]}
        self.assertEqual(rows["TAX_CEILING"]["basis_kind"], "MAINTAINED_POLICY_SETTING")
        self.assertEqual(rows["FERTILITY"]["basis_kind"], "EMPIRICAL_EXTRAPOLATION")
        self.assertEqual(rows["PRODUCTIVITY"]["value_or_rule"], 1.2)
        self.assertEqual(rows["MIGRATION"]["value_or_rule"], 235000)

    def test_reclassifying_policy_as_empirical_blocks_candidate(self):
        self.reject(lambda p: next(r for r in p["projection_inventory"]["model_assumptions"] if r["assumption_type"] == "FISCAL_POLICY_SETTING").update(basis_kind="EMPIRICAL_EXTRAPOLATION"), "policy premise")

    def test_treasury_projection_cannot_substitute_for_observed_data(self):
        self.reject(lambda p: p["projection_inventory"]["observed_evidence"][0]["source_refs"][0].update(asset_id="IGR2026-MAIN"), "observed audit values")

    def test_sensitivity_cases_have_separate_shocks_horizons_and_limits(self):
        self.assertEqual(len(self.inventory["sensitivity_cases"]), 8)
        for row in self.inventory["sensitivity_cases"]:
            self.assertEqual(row["epistemic_class"], "SENSITIVITY_CASE")
            self.assertTrue(row["shock"] and row["results"] and row["limitations"])
        ai = next(r for r in self.inventory["sensitivity_cases"] if r["sensitivity_id"].endswith("-AI"))
        self.assertIn("decade end only", ai["horizon"])

    def test_minister_cannot_establish_technical_projection(self):
        self.reject(lambda p: p["projection_inventory"]["projection_outputs"][0]["source_refs"][0].update(asset_id="MINISTER2026"), "ministerial/prior")

    def test_ministerial_framing_stays_policy_claim(self):
        self.reject(lambda p: p["projection_inventory"]["projection_framework"]["ministerial_framing"].update(epistemic_class="OBSERVED_EVIDENCE"), "framing")

    def test_six_transition_treatments_not_equally_modelled(self):
        rows = {r["transition"]: r for r in self.inventory["major_transitions"]}
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows["GEOPOLITICAL_FRAGMENTATION"]["treatment"], "QUALITATIVE_CONTEXT")
        self.assertEqual(rows["INTERGENERATIONAL_EQUITY"]["treatment"], "DESCRIPTIVE_AND_POLICY_CONTEXT")
        ai = next(r for r in self.inventory["model_assumptions"] if r["assumption_id"].endswith("AI_DIFFUSION"))
        self.assertIn("no separately identified", ai["value_or_rule"])

    def test_each_audit_has_all_ten_locatable_qualitative_axes(self):
        for row in self.audit["assumption_audit"]:
            self.assertEqual(set(row) - {"assumption_id"}, set(AUDIT_AXES))
            for axis in AUDIT_AXES:
                self.assertTrue(row[axis]["finding"] and row[axis]["source_refs"] and row[axis]["limitations"])

    def test_removing_any_axis_blocks_candidate_validation(self):
        for axis in AUDIT_AXES:
            with self.subTest(axis=axis):
                p = load_package()
                del p["assumption_audit"]["assumption_audit"][0][axis]
                with self.assertRaisesRegex(ProjectionCandidateError, "audit axis"):
                    validate_package(relink(p))

    def test_scores_and_aggregate_verdict_fail(self):
        for key in ("quality_score", "global_confidence_score", "overall_verdict", "rating"):
            with self.subTest(key=key):
                p = load_package()
                p["assumption_audit"]["assumption_audit"][0][key] = 7
                with self.assertRaisesRegex(ProjectionCandidateError, "scores"):
                    validate_package(relink(p))

    def test_backtest_keeps_original_and_observed_vintages(self):
        rows = self.audit["historical_backtest"]
        self.assertEqual(len(rows), 3)
        self.assertEqual({r["original_vintage"] for r in rows}, {"2002"})
        self.assertTrue(all("2023" in r["observed_vintage"] for r in rows))
        prod = next(r for r in rows if r["metric"] == "Labour productivity")
        self.assertEqual(prod["error"], -0.6)
        self.assertIn("1.75", prod["method_basis"])
        self.assertEqual(self.audit["error_interpretation"], "MODEL_ERROR_IS_NOT_EVIDENCE_OF_BAD_FAITH")

    def test_noncomparable_backtest_has_no_error(self):
        row = next(r for r in self.audit["historical_backtest"] if r["comparability"] == "NOT_DIRECTLY_COMPARABLE")
        self.assertIsNone(row["error"])
        self.reject(lambda p: next(r for r in p["assumption_audit"]["historical_backtest"] if r["comparability"] == "NOT_DIRECTLY_COMPARABLE").update(error=5.8), "noncomparable error")

    def test_revised_later_report_cannot_replace_original_backtest_vintage(self):
        self.reject(lambda p: p["assumption_audit"]["historical_backtest"][0].update(original_vintage="2023"), "original backtest vintage")

    def test_bad_backtest_arithmetic_fails(self):
        self.reject(lambda p: p["assumption_audit"]["historical_backtest"][0].update(error=99), "backtest arithmetic")

    def test_comparisons_match_horizon_and_do_not_become_surprise(self):
        rows = [r for r in self.audit["projection_comparison"] if r["comparability"] == "MATCHED_HORIZON_MODEL_REVISION"]
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r["prior_horizon"] == r["current_horizon"] == "2062-63" for r in rows))
        self.assertEqual(self.review["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(self.review["what_was_expected"]["benchmarks"], [])
        self.reject(lambda p: p["assumption_audit"]["projection_comparison"][0].update(current_horizon="2065-66"), "unlike horizons")

    def test_noncomparable_real_dollar_levels_have_no_difference(self):
        row = self.audit["projection_comparison"][-1]
        self.assertEqual(row["comparability"], "NOT_DIRECTLY_COMPARABLE")
        self.assertIsNone(row["difference"])
        self.assertIn("price bases differ", row["method_basis"])

    def test_rounded_chart_difference_does_not_suppress_report_presentation(self):
        row = next(r for r in self.audit["projection_comparison"] if r["metric"] == "Structural participation15+")
        self.assertEqual(row["difference"], 1.5)
        self.assertIn("1.4ppt", row["limitations"][0])
        self.assertIn("unrounded", row["limitations"][0])

    def test_no_market_movement_or_observed_second_order_effect(self):
        self.assertEqual(self.review["what_moved"], [])
        self.assertEqual(self.review["second_order_effects"]["status"], "NOT_ESTABLISHED")
        self.reject(lambda p: p["analysis_candidate"]["review"]["second_order_effects"].update(status="OBSERVED"), "projected effects")

    def test_no_model_confidence_uplift_or_factual_corroboration(self):
        prov = self.package["analysis_candidate"]["model_provenance"]
        self.assertEqual(prov["model_version"], "UNAVAILABLE")
        self.reject(lambda p: p["analysis_candidate"]["model_provenance"].update(model_version="guessed"), "cannot be guessed")

    def test_dependency_edges_are_typed_and_not_relationships(self):
        self.assertEqual(len(self.audit["dependency_map"]), 11)
        self.assertTrue(all(r["production_relationship"] is False for r in self.audit["dependency_map"]))
        self.reject(lambda p: p["assumption_audit"]["dependency_map"][0].update(epistemic_class="CAUSAL_FACT"), "edge class")

    def test_relationship_promotion_and_confidence_inflation_fail(self):
        for mutation in (
            lambda p: p["assumption_audit"]["dependency_map"][0].update(production_relationship=True),
            lambda p: p["assumption_audit"].update(corroboration_policy="COUNT_REPORT_AND_FACTSHEET_SEPARATELY"),
        ):
            p = load_package()
            mutation(p)
            with self.assertRaises(ProjectionCandidateError):
                validate_package(relink(p))

    def test_candidate_falsifiers_are_material_and_no_outcome_exists(self):
        self.assertEqual(len(self.review["falsifiers"]), 9)
        self.assertTrue(all(r["summary"] and r["evidence_refs"] for r in self.review["falsifiers"]))
        self.assertEqual(self.review["second_order_effects"]["evidence_refs"], [])

    def test_failed_mutation_proof_blocks_candidate(self):
        self.reject(lambda p: p["evidence_manifest"].update(protected_input_fingerprint_after="0" * 64), "mutation proof")

    def test_explicit_feedback_retained_without_transitive_inference(self):
        edges = {(r["from_ref"], r["to_ref"]) for r in self.audit["dependency_map"]}
        debt = "WSPROJ-AU-IGR-2026-GROSS_DEBT"
        interest = "WSPROJ-AU-IGR-2026-INTEREST"
        self.assertIn((debt, interest), edges)
        self.assertIn((interest, debt), edges)
        self.assertNotIn((debt, debt), edges)

    def test_dimension_mapping_is_non_admitted_context(self):
        self.assertTrue(all(r["current_state_claim"] is False for r in self.audit["dimension_mapping_candidates"]))
        self.reject(lambda p: p["assumption_audit"]["dimension_mapping_candidates"][0].update(current_state_claim=True), "not World State")

    def test_review_is_not_automatic_or_aggregate(self):
        questions = self.audit["human_review_questions"]
        self.assertEqual(len(questions), 5)
        self.assertTrue(all(r["decision"] is None for r in questions.values()))
        self.assertEqual(questions["historical_backtest"]["recommended_disposition"], "DEFER")
        self.reject(lambda p: p["assumption_audit"]["human_review_questions"]["analysis"].update(decision="ACCEPT"), "automatic review")

    def test_schema_extension_is_not_production_schema_or_admission(self):
        ext = self.package["extension_candidate"]
        self.assertFalse(ext["production_schema_change"] or ext["production_admission_permitted"])
        schema = json.loads((ROOT / "data/analysis/schema.json").read_text())
        self.assertNotIn("official_projection_review", json.dumps(schema))

    def test_nonempty_write_target_public_flag_or_accepted_candidate_fail(self):
        for field, value in (("write_targets", ["data/analysis/event_reviews.json"]), ("public_projection_permitted", True), ("review_state", "ACCEPTED"), ("visibility", "PUBLIC_ELIGIBLE")):
            with self.subTest(field=field):
                p = load_package()
                p["analysis_candidate"][field] = value
                with self.assertRaises(ProjectionCandidateError):
                    validate_package(relink(p))

    def test_production_populations_do_not_contain_candidates(self):
        for relative in ("data/analysis/event_reviews.json", "data/analysis/evidence_registry.json", "data/world_state/components.json", "data/forecasts/forecasts.json", "data/scenarios/scenarios.json", "data/risks/states.json", "data/relationships/relationships.json"):
            text = (ROOT / relative).read_text()
            self.assertNotIn("WSAN-AU-IGR-20260921-001", text)
            self.assertNotIn("WSPROJ-AU-IGR-2026-", text)
            self.assertNotIn("WSASM-AU-IGR-2026-", text)

    def test_public_build_does_not_include_candidate_analysis_or_inventory(self):
        for name in ("analysis.json", "outlook.json", "briefing.json"):
            path = ROOT / "docs/data" / name
            self.assertTrue(path.exists(), "build site before integration tests")
            text = path.read_text()
            self.assertNotIn("WSAN-AU-IGR-20260921-001", text)
            self.assertNotIn("WSPROJ-AU-IGR-2026-", text)

    def test_selected_object_tamper_fails_but_unrelated_registry_growth_is_not_a_ceiling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("data/analysis", "data/canonical", "data/sources", "data/monitor", "web"):
                shutil.copytree(ROOT / relative, root / relative)
            path = root / "data/canonical/registry.json"
            registry = json.loads(path.read_text())
            registry["version"] = "unrelated-container-metadata-change"
            path.write_text(json.dumps(registry))
            result = inspect_step14d(root)
            self.assertIn("data/canonical/registry.json", result["historical_file_drift"])
            igr = next(r for r in registry["records"] if r["occurrence_id"] == "WSO-FIS-AU-IGR-20260921")
            igr["event_name"] = "tampered"
            path.write_text(json.dumps(registry))
            before = protected_file_hashes(root)
            with self.assertRaisesRegex(ProjectionCandidateError, "object mismatch"):
                inspect_step14d(root)
            self.assertEqual(before, protected_file_hashes(root))


if __name__ == "__main__":
    unittest.main()
