from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/live_intelligence/BARMM_PRE_ELECTION_LIVE_CG_PLAN_v0.1.json").read_text(encoding="utf-8"))
PAYLOAD = json.loads((ROOT / "data/live_intelligence/BARMM_PRE_ELECTION_LIVE_CG_PAYLOAD_v0.1.json").read_text(encoding="utf-8"))


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class BarmmPreElectionLiveCGTests(unittest.TestCase):
    def test_plan_is_bounded_and_opec_is_not_a_target(self) -> None:
        self.assertEqual(PLAN["base_main_sha"], "6c96794cb553c6b34df93536141340c2af8db44a")
        self.assertEqual(PLAN["target"]["canonical_occurrence_id"], "WSO-EL-PH-BARMM-20260914")
        self.assertEqual(PLAN["target"]["canonical_relationship"], "CONTEXT_FOR")
        self.assertFalse(PLAN["target_state"]["automatic_canonical_commit"])
        self.assertFalse(PLAN["target_state"]["google_calendar_write"])
        self.assertNotIn("OPEC", json.dumps(PLAN["target"], sort_keys=True))
        self.assertNotIn("data/monitor/expectations.json", PLAN["authorized_governed_writes"])
        self.assertNotIn("data/canonical/registry.json", PLAN["authorized_governed_writes"])

    def test_payload_preserves_live_canonical_boundary(self) -> None:
        observation = PAYLOAD["observation_template"]
        self.assertEqual(observation["observation_type"], "INSTITUTIONAL_DEVELOPMENT")
        self.assertEqual(observation["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(observation["canonical_links"], [{"occurrence_id": "WSO-EL-PH-BARMM-20260914", "relationship": "CONTEXT_FOR"}])
        self.assertNotIn("event_time", observation)
        self.assertFalse(observation["automatic_canonical_commit"])
        self.assertFalse(observation["google_calendar_write"])
        evidence = PAYLOAD["live_evidence"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["evidence_class"], "PRIMARY_OFFICIAL")
        self.assertEqual(evidence[0]["canonical_provenance_effect"], "NONE")
        self.assertEqual(evidence[0]["publication_time"], {"precision": "CIVIL_DATE", "published_date": "2026-09-09"})

    def test_canonical_occurrence_identity_and_civil_date_survive(self) -> None:
        canonical = load("data/canonical/registry.json")
        matches = [row for row in canonical["records"] if row.get("occurrence_id") == "WSO-EL-PH-BARMM-20260914"]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        self.assertEqual(row["series_id"], "WSER-EL-PH-BARMM-PE")
        self.assertEqual(row["lifecycle_status"], "PLANNED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertEqual(row["timing_type"], "CIVIL_DATE")
        self.assertEqual(row["start_local"], "2026-09-14")
        self.assertEqual(row["source_timezone"], "Asia/Manila")
        self.assertIsNone(row["start_utc"])

    def test_repository_is_either_exact_prestate_or_reviewed_cg_state(self) -> None:
        schema = load("data/live_intelligence/schema.json")
        observations = load("data/live_intelligence/observations.json")
        evidence = load("data/live_intelligence/evidence_registry.json")
        ids = {row.get("observation_id") for row in observations["observations"]}
        evidence_ids = {row.get("evidence_id") for row in evidence["evidence"]}
        obs_id = PLAN["target"]["observation_id"]
        ev_id = PLAN["target"]["evidence_ids"][0]

        if obs_id not in ids:
            self.assertEqual(schema["version"], "0.6")
            self.assertEqual(len(observations["observations"]), 6)
            self.assertEqual(len(evidence["evidence"]), 9)
            self.assertNotIn(ev_id, evidence_ids)
        else:
            self.assertEqual(schema["version"], "0.7")
            self.assertEqual(observations["version"], "0.7")
            self.assertEqual(evidence["version"], "0.7")
            self.assertEqual(len(observations["observations"]), 7)
            self.assertEqual(len(evidence["evidence"]), 10)
            self.assertIn(ev_id, evidence_ids)
            row = next(row for row in observations["observations"] if row["observation_id"] == obs_id)
            self.assertRegex(row["observed_at_utc"], r"^2026-09-(09|10)T\d{2}:\d{2}:\d{2}Z$")
            self.assertNotIn("event_time", row)
            self.assertEqual(schema["population_policy"]["maximum_observation_count"], 7)
            self.assertEqual(schema["population_policy"]["maximum_evidence_count"], 10)
            self.assertFalse(schema["population_policy"]["automatic_ingestion_allowed"])
            self.assertFalse(schema["population_policy"]["public_observation_projection_allowed"])

    def test_simulation_is_green_without_writing(self) -> None:
        before = {
            path: (ROOT / path).read_bytes()
            for path in [
                "data/live_intelligence/schema.json",
                "data/live_intelligence/observations.json",
                "data/live_intelligence/evidence_registry.json",
            ]
        }
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/apply_barmm_pre_election_live_cg.py"), "--check", "--observed-at-utc", "2026-09-09T17:00:00Z"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CG_SIMULATION_VALID", proc.stdout)
        for path, content in before.items():
            self.assertEqual((ROOT / path).read_bytes(), content, path)


if __name__ == "__main__":
    unittest.main()
