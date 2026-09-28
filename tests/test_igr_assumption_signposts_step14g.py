"""Step 14G candidate-only IGR assumption signpost contract and boundaries."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from world_signals.igr_assumption_signposts import (  # noqa: E402
    ANALYSIS_ID, EVIDENCE_DIRECTIONS, OBSERVATION_TYPES, build_candidate,
    candidate_json, render_summary, validate_candidate,
)
from world_signals.world_state_history import fingerprint  # noqa: E402


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


class IgrAssumptionSignpostsStep14GTests(unittest.TestCase):
    def setUp(self):
        self.candidate = build_candidate(ROOT)

    def test_production_igr_remains_reviewed_internal_and_pinned(self):
        dataset = read("data/analysis/event_reviews.json")
        review = next(row for row in dataset["reviews"] if row["analysis_id"] == ANALYSIS_ID)
        self.assertEqual(review["review_state"], "REVIEWED")
        self.assertEqual(dataset["publication_decisions"][ANALYSIS_ID], "INTERNAL_ONLY")
        self.assertEqual(review["analysis_as_of_utc"], "2026-09-28T16:25:00Z")
        self.assertEqual(self.candidate["historical_backtest_disposition"], "DEFERRED")

    def test_candidate_is_deterministic_review_pending_and_internal_only(self):
        second = build_candidate(ROOT)
        self.assertEqual(self.candidate, second)
        self.assertEqual(validate_candidate(self.candidate), ())
        self.assertEqual(self.candidate["status"], "REVIEW_PENDING")
        self.assertEqual(self.candidate["classification"], "CANDIDATE_ONLY_NOT_PRODUCTION")
        self.assertEqual(self.candidate["write_targets"], [])
        self.assertIs(self.candidate["public_projection_permitted"], False)
        self.assertEqual(candidate_json(self.candidate), candidate_json(second))
        self.assertEqual(render_summary(self.candidate), render_summary(second))

    def test_retained_json_and_summary_match_deterministic_builder(self):
        retained = read("data/analysis/STEP14G_AU_IGR_ASSUMPTION_SIGNPOSTS_REVIEW_PENDING.json")
        summary = (ROOT / "data/analysis/STEP14G_AU_IGR_ASSUMPTION_SIGNPOSTS_REVIEW_PENDING.md").read_text(encoding="utf-8")
        self.assertEqual(retained, self.candidate)
        self.assertEqual(summary, render_summary(self.candidate))

    def test_only_selected_assumptions_have_material_observable_signposts(self):
        suffixes = {row["assumption_id"].rsplit("-", 1)[-1] for row in self.candidate["selected_assumptions"]}
        self.assertEqual(suffixes, {"PRODUCTIVITY", "FERTILITY", "MIGRATION", "PARTICIPATION", "AI_DIFFUSION", "ENERGY_TRANSITION", "TAX_CEILING", "HEALTH_COST"})
        omitted = {row["assumption_id"].rsplit("-", 1)[-1]: row["reason"] for row in self.candidate["omitted_assumptions"]}
        self.assertEqual(set(omitted), {"MORTALITY", "INFLATION", "COMMODITY_PRICES", "DEBT_YIELDS", "AGED_CARE_COST", "NDIS_REFORMS", "RETIREMENT"})
        self.assertTrue(all(reason for reason in omitted.values()))
        self.assertEqual(len(self.candidate["signposts"]), 15)

    def test_assumption_refs_and_source_hashes_are_exact_and_resolved(self):
        dataset = read("data/analysis/event_reviews.json")
        review = next(row for row in dataset["reviews"] if row["analysis_id"] == ANALYSIS_ID)
        assumption_ids = {row["assumption_id"] for row in review["official_projection_review"]["model_assumptions"]}
        refs = {row["source_id"] for row in self.candidate["source_manifest"]}
        for row in self.candidate["signposts"]:
            self.assertIn(row["assumption_id"], assumption_ids)
            self.assertTrue(row["source_refs"])
            self.assertTrue(all(ref["source_id"] in refs for ref in row["source_refs"]))
        self.assertEqual(self.candidate["source_manifest_sha256"], fingerprint(self.candidate["source_manifest"]))
        observed = {row["observation_candidate_id"]: row for row in self.candidate["bounded_current_evidence"]}
        self.assertEqual(observed["WSOBAUD-PRODUCTIVITY2026Q2"]["value"], -0.2)
        self.assertEqual(observed["WSOBAUD-TFR2024"]["value"], 1.481)
        self.assertEqual(observed["WSOBAUD-NOM2026Q1"]["value"], 292100)
        self.assertEqual(observed["WSOBAUD-LF2026M8"]["value"], 67.0)

    def test_vocabularies_and_persistence_are_enforced(self):
        self.assertTrue({row["observation_type"] for row in self.candidate["signposts"]} <= OBSERVATION_TYPES)
        self.assertTrue({row["direction_of_evidence"] for row in self.candidate["signposts"]} <= EVIDENCE_DIRECTIONS)
        self.assertTrue(all(row["minimum_persistence"].strip() for row in self.candidate["signposts"]))
        changed = deepcopy(self.candidate)
        changed["signposts"][0]["minimum_persistence"] = ""
        changed["semantic_fingerprint"] = fingerprint({k: v for k, v in changed.items() if k != "semantic_fingerprint"})
        self.assertIn("minimum_persistence is required", validate_candidate(changed))

    def test_scores_probabilities_and_rankings_are_prohibited(self):
        for field in ("score", "probability", "rank", "ranking"):
            changed = deepcopy(self.candidate)
            changed[field] = 1
            changed["semantic_fingerprint"] = fingerprint({k: v for k, v in changed.items() if k != "semantic_fingerprint"})
            self.assertTrue(any("prohibited" in err for err in validate_candidate(changed)))

    def test_current_assessments_are_evidence_bounded_and_no_escalations_are_claimed(self):
        states = {row["assumption_id"].rsplit("-", 1)[-1]: row for row in self.candidate["selected_assumptions"]}
        self.assertEqual(states["PRODUCTIVITY"]["present_evidence_state"], "AMBIGUOUS")
        self.assertIn("one cyclical/revisable print", states["PRODUCTIVITY"]["why"])
        self.assertEqual(states["FERTILITY"]["present_evidence_state"], "NOT_ENOUGH_EVIDENCE")
        self.assertEqual(states["MIGRATION"]["present_evidence_state"], "IN_TENSION_WITH_ASSUMPTION")
        self.assertIn("one moving annual total", states["MIGRATION"]["why"])
        self.assertEqual(states["PARTICIPATION"]["present_evidence_state"], "NOT_ENOUGH_EVIDENCE")
        self.assertEqual(states["AI_DIFFUSION"]["present_evidence_state"], "NOT_ENOUGH_EVIDENCE")
        self.assertEqual(states["ENERGY_TRANSITION"]["present_evidence_state"], "NOT_ENOUGH_EVIDENCE")
        self.assertEqual(states["TAX_CEILING"]["present_evidence_state"], "NOT_ENOUGH_EVIDENCE")
        self.assertEqual(states["HEALTH_COST"]["present_evidence_state"], "NOT_ENOUGH_EVIDENCE")
        self.assertEqual({row["review_workflow_state"] for row in states.values()}, {"OBSERVE"})

    def test_domain_temporal_rules_prevent_short_run_falsification(self):
        by_id = {row["signpost_id"]: row for row in self.candidate["signposts"]}
        productivity = next(row for row in by_id.values() if "PRODUCTIVITY-CYCLE" in row["signpost_id"])
        fertility = next(row for row in by_id.values() if "FERTILITY-PERIOD" in row["signpost_id"])
        migration = next(row for row in by_id.values() if "MIGRATION-FLOW" in row["signpost_id"])
        participation = next(row for row in by_id.values() if "PARTICIPATION-DELIVERY" in row["signpost_id"])
        self.assertIn("12 comparable quarters", productivity["minimum_persistence"])
        self.assertIn("not completed cohort fertility", fertility["minimum_persistence"])
        self.assertIn("three annual observations", migration["minimum_persistence"])
        self.assertIn("three annual comparable observations", participation["minimum_persistence"])

    def test_ai_energy_fiscal_and_health_boundaries_are_explicit(self):
        by_tag = {row["signpost_id"].split("-")[-1]: row for row in self.candidate["signposts"]}
        ai = next(row for row in self.candidate["signposts"] if "AI-ADOPTION" in row["signpost_id"])
        self.assertIn("adoption alone", ai["minimum_persistence"])
        energy = next(row for row in self.candidate["signposts"] if "ENERGY-DELIVERY" in row["signpost_id"])
        self.assertIn("SAID, DECIDED, AUTHORISED, IMPLEMENTED and OBSERVED", energy["comparison_basis"])
        fiscal = next(row for row in self.candidate["signposts"] if "FISCAL-POLICY" in row["signpost_id"])
        self.assertIn("does not validate", fiscal["minimum_persistence"])
        gaps = {row["assumption_id"].rsplit("-", 1)[-1] for row in self.candidate["source_coverage_gaps"]}
        self.assertTrue({"AI_DIFFUSION", "ENERGY_TRANSITION", "HEALTH_COST", "TAX_CEILING"} <= gaps)
        self.assertTrue(all(row["route_created"] is False for row in self.candidate["source_coverage_gaps"]))

    def test_candidate_cannot_promote_to_downstream_or_change_backtest(self):
        self.assertEqual(self.candidate["historical_backtest_disposition"], "DEFERRED")
        self.assertTrue({"WORLD_STATE", "RELATIONSHIP", "FORECAST", "SCENARIO", "RISK", "ANALYSIS_REVISION"} <= set(self.candidate["prohibited_promotions"]))
        changed = deepcopy(self.candidate)
        changed["historical_backtest_disposition"] = "ACCEPTED"
        changed["semantic_fingerprint"] = fingerprint({k: v for k, v in changed.items() if k != "semantic_fingerprint"})
        self.assertIn("independent historical backtest disposition must remain DEFERRED", validate_candidate(changed))

    def test_tampered_production_igr_fails_closed(self):
        dataset = read("data/analysis/event_reviews.json")
        review = next(row for row in dataset["reviews"] if row["analysis_id"] == ANALYSIS_ID)
        review["official_projection_review"]["limitations"].append("synthetic mutation")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            build_candidate(ROOT, reviews_dataset=dataset)

    def test_production_and_public_boundaries_are_byte_unchanged(self):
        paths = [
            "data/analysis/event_reviews.json", "data/analysis/evidence_registry.json",
            "data/analysis/schema.json", "data/canonical/registry.json", "data/sources/registry.json",
            "data/live_intelligence/observations.json", "data/live_intelligence/evidence_registry.json",
            "data/signals/signals.json", "data/relationships/relationships.json",
            "data/forecasts/forecasts.json", "data/scenarios/scenarios.json",
            "data/risks/risks.json", "data/outcomes/outcomes.json",
            "docs/data/analysis.json", "docs/data/brief.json",
        ]
        before = {path: sha(path) for path in paths if (ROOT / path).exists()}
        build_candidate(ROOT)
        self.assertEqual(before, {path: sha(path) for path in before})
        self.assertEqual(self.candidate["write_targets"], [])


if __name__ == "__main__":
    unittest.main()
