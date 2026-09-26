from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.signal_admission import (
    empty_signal_state_hash,
    signal_state_hash,
    validate_signal_admission_transaction,
)
from world_signals.signals import observation_digest, validate_signals, validate_signal_history


class SignalAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(relative):
            return json.loads((ROOT / relative).read_text(encoding="utf-8"))

        cls.schema = load("data/signals/schema.json")
        cls.signals = load("data/signals/signals.json")
        cls.transaction = load("data/signals/signal_admission_transaction_v1.json")
        cls.observations = load("data/live_intelligence/observations.json")
        cls.evidence = load("data/live_intelligence/evidence_registry.json")

    def test_current_reviewed_admission_passes(self):
        report = validate_signal_admission_transaction(
            self.schema, self.signals, self.observations, self.evidence, self.transaction
        )
        self.assertTrue(report.ok, report.errors)

    def test_populated_state_without_transaction_fails_closed(self):
        report = validate_signals(self.schema, self.signals, self.observations, self.evidence)
        self.assertFalse(report.ok)
        self.assertIn("requires a reviewed admission transaction", " ".join(report.errors))

    def test_admission_hashes_pin_empty_prestate_and_poststate(self):
        self.assertEqual(
            self.transaction["pre_state"]["sha256"],
            empty_signal_state_hash(self.schema["version"]),
        )
        self.assertEqual(self.transaction["post_state"]["sha256"], signal_state_hash(self.signals))

    def test_second_signal_cannot_enter_one_signal_tranche(self):
        signals = deepcopy(self.signals)
        second = deepcopy(signals["signals"][0])
        second["signal_id"] = "WSSIG-SECOND-REJECTED"
        second["revision_id"] = "WSSIG-SECOND-REJECTED-R1"
        signals["signals"].append(second)
        transaction = deepcopy(self.transaction)
        transaction["signal_ids"] = [row["signal_id"] for row in signals["signals"]]
        transaction["revision_ids"] = [row["revision_id"] for row in signals["signals"]]
        transaction["admission_limit"]["admitted_count"] = 2
        transaction["post_state"]["signal_count"] = 2
        transaction["post_state"]["sha256"] = signal_state_hash(signals)
        report = validate_signal_admission_transaction(
            self.schema, signals, self.observations, self.evidence, transaction
        )
        self.assertIn("tranche limit is one", " ".join(report.errors))

    def test_candidate_observation_id_cannot_bypass_governed_boundary(self):
        signals = deepcopy(self.signals)
        row = signals["signals"][0]
        row["observation_ids"][0] = "WSC-OBS-UNREVIEWED-CANDIDATE"
        row["observation_hashes"].pop("WSLI-HEALTH-COD-BVD-20260826-001")
        row["observation_hashes"]["WSC-OBS-UNREVIEWED-CANDIDATE"] = "candidate-hash"
        transaction = deepcopy(self.transaction)
        transaction["post_state"]["sha256"] = signal_state_hash(signals)
        report = validate_signal_admission_transaction(
            self.schema, signals, self.observations, self.evidence, transaction
        )
        joined = " ".join(report.errors)
        self.assertTrue("unknown observation_id" in joined or "candidate" in joined)

    def test_missing_observation_hash_fails(self):
        signals = deepcopy(self.signals)
        signals["signals"][0]["observation_hashes"].pop("WSLI-HEALTH-COD-BVD-20260826-001")
        transaction = deepcopy(self.transaction)
        transaction["post_state"]["sha256"] = signal_state_hash(signals)
        report = validate_signal_admission_transaction(
            self.schema, signals, self.observations, self.evidence, transaction
        )
        self.assertIn("immutable observation hashes", " ".join(report.errors))

    def test_single_observation_cannot_claim_persistence(self):
        observations = deepcopy(self.observations)
        evidence = deepcopy(self.evidence)
        row = deepcopy(self.signals["signals"][0])
        row["observation_ids"] = [row["observation_ids"][0]]
        row["evidence_refs"] = [row["evidence_refs"][0]]
        row["latest_supporting_observation_id"] = row["observation_ids"][0]
        row["baseline"]["observation_ids"] = [row["observation_ids"][0]]
        linked = next(
            item for item in observations["observations"] if item["observation_id"] == row["observation_ids"][0]
        )
        row["observation_hashes"] = {row["observation_ids"][0]: observation_digest(linked)}
        row["corroboration"]["distinct_provider_count"] = 1
        row["corroboration"]["independent_observation_count"] = 1
        row["evidence_lineage"] = [row["evidence_lineage"][0]]
        # The history validator must reject the claim before any admission can pass.
        report = validate_signal_history(self.schema, [row], observations, evidence)
        self.assertIn("multiple observation times", " ".join(report.errors))

    def test_production_forecast_and_downstream_populations_are_not_opened(self):
        forecasts = json.loads((ROOT / "data/forecasts/forecasts.json").read_text())
        relationships = json.loads((ROOT / "data/relationships/relationships.json").read_text())
        risks = json.loads((ROOT / "data/risks/states.json").read_text())
        scenarios = json.loads((ROOT / "data/scenarios/scenarios.json").read_text())
        self.assertEqual(len(forecasts["forecasts"]), 4)
        self.assertEqual(len(relationships["relationships"]), 0)
        self.assertEqual(len(risks["states"]), 0)
        self.assertEqual(len(scenarios["scenarios"]), 0)
        self.assertFalse(self.schema["public_projection_policy"]["signal_projection_allowed"])


if __name__ == "__main__":
    unittest.main()
