from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_analysis_revision_contract_ba as apply_ba
import apply_japan_fies_live_analysis_az as apply_az
import validate_checkpoint_contracts as validate_contracts
from world_signals.checkpoint_contract import (
    numeric_version,
    validate_descendant_checkpoint,
    version_at_least,
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CheckpointContractBCTests(unittest.TestCase):
    def test_dotted_versions_are_numeric_not_decimal(self):
        self.assertGreater(numeric_version("0.10"), numeric_version("0.9"))
        self.assertTrue(version_at_least("1.81", "1.80"))
        self.assertFalse(version_at_least("0.6", "0.7"))
        self.assertFalse(version_at_least("not-a-version", "0.7"))

    def test_descendant_floors_allow_growth_but_exact_invariants_do_not_drift(self):
        report = validate_descendant_checkpoint(
            versions_at_least={
                "schema": ("0.9", "0.7"),
                "reviews": ("0.18", "0.17"),
            },
            counts_at_least={
                "review count": (25, 21),
                "evidence count": (110, 95),
            },
            exact_values={
                "stable occurrence": ("WSO-1", "WSO-1"),
                "same-anchor requirement": (True, True),
            },
        )
        self.assertTrue(report.ok, report.errors)

        bad = validate_descendant_checkpoint(
            versions_at_least={"schema": ("0.6", "0.7")},
            counts_at_least={"review count": (20, 21)},
            exact_values={"stable occurrence": ("WSO-2", "WSO-1")},
        )
        self.assertFalse(bad.ok)
        joined = " ".join(bad.errors)
        self.assertIn("below historical floor", joined)
        self.assertIn("immutable value", joined)

    def test_required_markers_preserve_semantics_without_freezing_current_counts(self):
        text = "Current state changed. AZ first production relationship remains preserved."
        report = validate_descendant_checkpoint(
            required_markers={
                "status": (text, ["AZ first production relationship remains preserved"])
            }
        )
        self.assertTrue(report.ok, report.errors)
        missing = validate_descendant_checkpoint(
            required_markers={"status": (text, ["BA revision-lineage contract"])}
        )
        self.assertFalse(missing.ok)

    def test_current_post_bb_state_satisfies_materialised_ba_and_az_descendant_contracts(self):
        result = validate_contracts.validate_current_checkpoint_descendants()
        self.assertTrue(result.ok, result.errors)

    def test_ba_schema_descendant_may_open_a_later_reviewed_gate_without_erasing_lineage(self):
        current = load(apply_ba.ANALYSIS_SCHEMA_PATH)
        descendant = deepcopy(current)
        descendant["version"] = "0.8"
        policy = descendant["analysis_revision_policy"]
        policy["mode"] = "CONTROLLED_REVISION_LINEAGE"
        policy["production_analysis_revisions_allowed"] = True
        policy["maximum_production_analysis_revisions"] = 1
        target = apply_ba.target_analysis_schema(descendant)
        self.assertEqual(target, descendant)

        malformed = deepcopy(descendant)
        malformed["analysis_revision_policy"]["same_canonical_occurrence_required"] = False
        with self.assertRaises(SystemExit):
            apply_ba.target_analysis_schema(malformed)

    def test_ba_status_descendant_is_not_keyed_to_historical_recovery_prose(self):
        current = apply_ba.STATUS_PATH.read_text(encoding="utf-8")
        future = current.replace(
            "- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**",
            "- production Analysis revisions: **1 / reviewed maximum 1 / public revision metadata projection CLOSED**",
            1,
        ).replace(
            "BA adds a **production-closed Analysis revision-lineage contract**",
            "Later recovery override intentionally omits BA historical prose",
            1,
        )
        self.assertEqual(apply_ba.target_status(future), future)

    def test_az_materialised_targets_do_not_downgrade_later_reviewed_versions_or_populations(self):
        payload = load(apply_az.PAYLOAD_PATH)

        reviews = load(apply_az.REVIEWS_PATH)
        descendant_reviews = deepcopy(reviews)
        descendant_reviews["version"] = "0.18"
        extra_review = deepcopy(descendant_reviews["reviews"][0])
        extra_review["analysis_id"] = "WSAN-BC-SYNTHETIC-DESCENDANT"
        descendant_reviews["reviews"].append(extra_review)
        self.assertEqual(
            apply_az.target_reviews(descendant_reviews, payload), descendant_reviews
        )

        observations = load(apply_az.LIVE_OBSERVATIONS_PATH)
        descendant_observations = deepcopy(observations)
        descendant_observations["version"] = "0.5"
        descendant_observations["population_state"] = "SYNTHETIC_REVIEWED_DESCENDANT"
        extra_observation = deepcopy(descendant_observations["observations"][0])
        extra_observation["observation_id"] = "WSLI-BC-SYNTHETIC-DESCENDANT"
        descendant_observations["observations"].append(extra_observation)
        self.assertEqual(
            apply_az.target_live_observations(descendant_observations, payload),
            descendant_observations,
        )

        evidence = load(apply_az.ANALYSIS_EVIDENCE_PATH)
        descendant_evidence = deepcopy(evidence)
        descendant_evidence["version"] = "0.18"
        extra_evidence = deepcopy(descendant_evidence["evidence"][0])
        extra_evidence["evidence_id"] = "WSEV-BC-SYNTHETIC-DESCENDANT"
        descendant_evidence["evidence"].append(extra_evidence)
        self.assertEqual(
            apply_az.target_analysis_evidence(descendant_evidence, payload),
            descendant_evidence,
        )

    def test_az_pre_materialisation_helpers_still_fail_closed_on_wrong_population(self):
        payload = load(apply_az.PAYLOAD_PATH)

        reviews = load(apply_az.REVIEWS_PATH)
        without_az = deepcopy(reviews)
        without_az["reviews"] = [
            row
            for row in without_az["reviews"]
            if row.get("analysis_id") != "WSAN-JP-FIES-202607-001"
        ]
        # Add unrelated rows so this is not the exact 20-review historical prestate.
        while len(without_az["reviews"]) <= 20:
            row = deepcopy(without_az["reviews"][0])
            row["analysis_id"] = f"WSAN-BC-WRONG-PRESTATE-{len(without_az['reviews'])}"
            without_az["reviews"].append(row)
        with self.assertRaises(SystemExit):
            apply_az.target_reviews(without_az, payload)

    def test_az_status_descendant_is_not_keyed_to_historical_recovery_prose(self):
        current = apply_az.STATUS_PATH.read_text(encoding="utf-8")
        future = current.replace(
            "- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**",
            "- production `live_inputs`: **2 / reviewed maximum 2 / public projection CLOSED**",
            1,
        ).replace(
            "AZ exercises the first **production Live Intelligence → Analysis relationship**",
            "Later recovery override intentionally omits AZ historical prose",
            1,
        )
        self.assertEqual(apply_az.target_status(future), future)

if __name__ == "__main__":
    unittest.main()
