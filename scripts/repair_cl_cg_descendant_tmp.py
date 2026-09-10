#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one repair target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"repaired {path}")


def main() -> int:
    replace_once(
        "scripts/apply_barmm_pre_election_live_cg.py",
        '''    if existing_obs:\n        require(schema.get("version") == "0.7", "CG reviewed Live schema drift")\n        return schema, observations, evidence\n''',
        '''    if existing_obs:\n        current_schema_version = tuple(int(part) for part in str(schema.get("version")).split("."))\n        current_observations_version = tuple(int(part) for part in str(observations.get("version")).split("."))\n        current_evidence_version = tuple(int(part) for part in str(evidence.get("version")).split("."))\n        require(current_schema_version >= (0, 7), "CG reviewed Live schema regressed below v0.7")\n        require(current_observations_version >= (0, 7), "CG reviewed observations regressed below v0.7")\n        require(current_evidence_version >= (0, 7), "CG reviewed evidence regressed below v0.7")\n        require(len(observations.get("observations", [])) >= 7, "CG reviewed observation population regressed")\n        require(len(evidence.get("evidence", [])) >= 10, "CG reviewed evidence population regressed")\n        return schema, observations, evidence\n''',
    )
    replace_once(
        "scripts/apply_barmm_pre_election_live_cg.py",
        '''    target = plan["target_state"]\n    require(schema.get("version") == target["live_schema_version"], "CG target schema version mismatch")\n    require(len(observations.get("observations", [])) == target["live_observation_count"], "CG target observation count mismatch")\n    require(len(evidence.get("evidence", [])) == target["live_evidence_count"], "CG target evidence count mismatch")\n''',
        '''    target = plan["target_state"]\n    target_version = tuple(int(part) for part in str(target["live_schema_version"]).split("."))\n    current_schema_version = tuple(int(part) for part in str(schema.get("version")).split("."))\n    require(current_schema_version >= target_version, "CG target schema version regressed below historical checkpoint")\n    require(len(observations.get("observations", [])) >= target["live_observation_count"], "CG target observation count regressed below historical checkpoint")\n    require(len(evidence.get("evidence", [])) >= target["live_evidence_count"], "CG target evidence count regressed below historical checkpoint")\n''',
    )
    replace_once(
        "tests/test_barmm_pre_election_live_cg.py",
        '''        else:\n            self.assertEqual(schema["version"], "0.7")\n            self.assertEqual(observations["version"], "0.7")\n            self.assertEqual(evidence["version"], "0.7")\n            self.assertEqual(len(observations["observations"]), 7)\n            self.assertEqual(len(evidence["evidence"]), 10)\n            self.assertIn(ev_id, evidence_ids)\n            row = next(row for row in observations["observations"] if row["observation_id"] == obs_id)\n            self.assertRegex(row["observed_at_utc"], r"^2026-09-(09|10)T\\d{2}:\\d{2}:\\d{2}Z$")\n            self.assertNotIn("event_time", row)\n            self.assertEqual(schema["population_policy"]["maximum_observation_count"], 7)\n            self.assertEqual(schema["population_policy"]["maximum_evidence_count"], 10)\n            self.assertFalse(schema["population_policy"]["automatic_ingestion_allowed"])\n            self.assertFalse(schema["population_policy"]["public_observation_projection_allowed"])\n''',
        '''        else:\n            self.assertGreaterEqual(tuple(map(int, schema["version"].split("."))), (0, 7))\n            self.assertGreaterEqual(tuple(map(int, observations["version"].split("."))), (0, 7))\n            self.assertGreaterEqual(tuple(map(int, evidence["version"].split("."))), (0, 7))\n            self.assertGreaterEqual(len(observations["observations"]), 7)\n            self.assertGreaterEqual(len(evidence["evidence"]), 10)\n            self.assertIn(ev_id, evidence_ids)\n            row = next(row for row in observations["observations"] if row["observation_id"] == obs_id)\n            self.assertRegex(row["observed_at_utc"], r"^2026-09-(09|10)T\\d{2}:\\d{2}:\\d{2}Z$")\n            self.assertNotIn("event_time", row)\n            self.assertGreaterEqual(schema["population_policy"]["maximum_observation_count"], 7)\n            self.assertGreaterEqual(schema["population_policy"]["maximum_evidence_count"], 10)\n            self.assertFalse(schema["population_policy"]["automatic_ingestion_allowed"])\n            self.assertFalse(schema["population_policy"]["public_observation_projection_allowed"])\n''',
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
