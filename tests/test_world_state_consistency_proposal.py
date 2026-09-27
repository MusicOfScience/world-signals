from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from retain_world_state_consistency_proposal import (  # noqa: E402
    DEFAULT_AS_OF_UTC,
    DEFAULT_REPOSITORY_REF,
    build_package,
    repository_provenance,
    validate_retained_package,
    validate_current_cutoff,
)
from world_signals.world_state_read import (  # noqa: E402
    DATA_PATHS,
)


def governed_hashes() -> dict[str, str]:
    return {
        key: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for key, path in sorted(DATA_PATHS.items())
    }


class WorldStateConsistencyProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = {
            "contract_version": "0.1",
            "as_of_utc": DEFAULT_AS_OF_UTC,
            "scope": {
                "jurisdictions": ["*"],
                "dimensions": [
                    "CONFLICT_MILITARY_ACTIVITY",
                    "STRATEGIC_GEOPOLITICAL_TENSION",
                    "POLITICAL_INSTITUTIONAL_STABILITY",
                    "MACROECONOMIC_FINANCIAL_CONDITIONS",
                    "TRADE_CAPITAL_ENERGY_FOOD_FLOWS",
                    "DEPENDENCIES_CHOKEPOINTS",
                    "MARKETS_AS_SENSORS",
                    "CLIMATE_PHYSICAL_RISK",
                    "HEALTH_BIOSECURITY",
                    "TECHNOLOGY_CRITICAL_INFRASTRUCTURE",
                ],
                "actor_ids": None,
            },
            "include_negative_evidence": True,
            "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
        }
        cls.package, cls.summary = build_package(cls.request, DEFAULT_REPOSITORY_REF)

    def test_package_is_explicitly_non_governed_and_review_pending(self):
        self.assertEqual(self.package["package_type"], "WORLD_STATE_CONSISTENCY_PROPOSAL")
        self.assertEqual(self.package["status"], "REVIEW_PENDING")
        self.assertFalse(self.package["production_world_state"])
        self.assertTrue(self.package["not_production_world_state"])
        self.assertTrue(self.package["no_write_targets"])
        self.assertEqual(self.package["review_state"]["write_targets"], [])
        self.assertFalse(self.package["public_projection_permitted"])

    def test_retained_cutoff_is_the_verified_pr156_merge_timestamp(self):
        self.assertEqual(DEFAULT_AS_OF_UTC, "2026-09-27T04:39:04Z")
        self.assertEqual(self.package["read_request"]["as_of_utc"], DEFAULT_AS_OF_UTC)
        self.assertEqual(len(self.package["repository_provenance"]["repository_sha"]), 40)

    def test_future_current_repository_cutoff_fails_closed(self):
        provenance = repository_provenance(DEFAULT_REPOSITORY_REF)
        later = datetime.fromisoformat(provenance["knowledge_cutoff_utc"].replace("Z", "+00:00")) + timedelta(seconds=1)
        future = later.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.assertRaises(ValueError):
            validate_current_cutoff(future, provenance)

    def test_empty_downstream_layers_and_no_sample_are_retained(self):
        self.assertEqual(self.summary["empty_production_layers"], ["relationships", "risks_regimes", "scenarios", "outcomes"])
        self.assertEqual(self.summary["evaluation_state"], "NO_SAMPLE")
        self.assertEqual(self.package["proposal"]["selected_inputs"]["relationships"], [])
        self.assertEqual(self.package["proposal"]["selected_inputs"]["risks_regimes"], [])
        self.assertEqual(self.package["proposal"]["selected_inputs"]["scenarios"], [])
        self.assertEqual(self.package["proposal"]["selected_inputs"]["outcomes"], [])

    def test_no_analytical_content_is_invented(self):
        proposal = self.package["proposal"]
        for field in (
            "actors", "implementation_claims", "dimension_assessments", "hypotheses",
            "transmission_edges", "negative_evidence", "baselines", "anomalies",
        ):
            self.assertEqual(proposal[field], [], field)
        self.assertFalse(self.summary["analytical_inference_made"])

    def test_manifest_and_fingerprints_are_retained(self):
        self.assertEqual(validate_retained_package(self.package), [])
        self.assertEqual(self.package["retained_package_validation"], [])
        self.assertTrue(all(len(row["object_sha256"]) == 64 for row in self.package["source_manifest"]))
        self.assertTrue(all("object" not in row for row in self.package["source_manifest"]))

    def test_repeated_build_is_reproducible(self):
        second, second_summary = build_package(self.request, DEFAULT_REPOSITORY_REF)
        self.assertEqual(self.package["source_manifest"], second["source_manifest"])
        self.assertEqual(self.package["source_manifest_sha256"], second["source_manifest_sha256"])
        self.assertEqual(self.package["semantic_proposal_fingerprint"], second["semantic_proposal_fingerprint"])
        self.assertEqual(self.summary, second_summary)

    def test_mutating_retained_source_object_fails_manifest_validation(self):
        package = deepcopy(self.package)
        package["source_manifest"][0]["object_sha256"] = "0" * 64
        errors = validate_retained_package(package)
        self.assertTrue(any("aggregate hash mismatch" in error for error in errors))

    def test_governed_inputs_are_unchanged_and_no_production_state_exists(self):
        before = governed_hashes()
        build_package(self.request, DEFAULT_REPOSITORY_REF)
        after = governed_hashes()
        self.assertEqual(before, after)
        self.assertFalse((ROOT / "data/world_state/state.json").exists())
        self.assertFalse((ROOT / "docs/world-state.json").exists())


if __name__ == "__main__":
    unittest.main()
