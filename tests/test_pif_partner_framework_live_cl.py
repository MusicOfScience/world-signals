from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_PLAN_v0.1.json").read_text(encoding="utf-8"))
PAYLOAD = json.loads((ROOT / "data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_PAYLOAD_v0.1.json").read_text(encoding="utf-8"))
TARGET_ID = PLAN["target"]["observation_id"]
EVIDENCE_ID = PLAN["target"]["evidence_ids"][0]
ANCHOR_ID = PLAN["target"]["canonical_occurrence_id"]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


class PIFPartnerFrameworkLiveCLContractTests(unittest.TestCase):
    def test_plan_is_bounded_to_live_and_exact_post_ck_main(self) -> None:
        self.assertEqual(PLAN["base_main_sha"], "aef4642863438e2170ae9a49160b7368c850b819")
        self.assertEqual(PLAN["selection"], "PIF_SCHEDULED_INSTITUTIONAL_OUTCOME")
        self.assertEqual(
            PLAN["authorized_governed_writes"],
            [
                "data/live_intelligence/schema.json",
                "data/live_intelligence/observations.json",
                "data/live_intelligence/evidence_registry.json",
            ],
        )
        self.assertTrue(all(value is False for value in PLAN["authority_gates"].values()))
        self.assertNotIn("data/canonical/registry.json", PLAN["authorized_governed_writes"])
        self.assertNotIn("data/monitor/expectations.json", PLAN["authorized_governed_writes"])
        self.assertNotIn("data/analysis/event_reviews.json", PLAN["authorized_governed_writes"])
        self.assertNotIn("OPEC", json.dumps(PLAN["target"], sort_keys=True))

    def test_payload_is_one_primary_confirmed_institutional_outcome(self) -> None:
        observation = PAYLOAD["observation_template"]
        self.assertEqual(observation["observation_id"], TARGET_ID)
        self.assertEqual(observation["observation_type"], "INSTITUTIONAL_DEVELOPMENT")
        self.assertEqual(observation["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(observation["domain_tags"], ["INSTITUTIONS", "GEOPOLITICS"])
        self.assertEqual(observation["jurisdictions"], [])
        self.assertEqual(observation["regions"], ["Oceania / Pacific"])
        self.assertEqual(
            observation["canonical_links"],
            [{"occurrence_id": ANCHOR_ID, "relationship": "OUTCOME_OF"}],
        )
        self.assertEqual(observation["evidence_refs"], [EVIDENCE_ID])
        self.assertNotIn("event_time", observation)
        self.assertFalse(observation["automatic_canonical_commit"])
        self.assertFalse(observation["google_calendar_write"])

        evidence = PAYLOAD["live_evidence"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["evidence_id"], EVIDENCE_ID)
        self.assertEqual(evidence[0]["evidence_class"], "PRIMARY_OFFICIAL")
        self.assertEqual(evidence[0]["canonical_provenance_effect"], "NONE")
        self.assertEqual(
            evidence[0]["publication_time"],
            {"precision": "CIVIL_DATE", "published_date": "2026-09-04"},
        )

    def test_waqa_wording_discrepancy_is_preserved_as_exclusion(self) -> None:
        excluded = PLAN["evidence_decision"]["excluded_after_fresh_preflight"]
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0]["subject"], "Waqa Moana")
        self.assertEqual(excluded[0]["australian_official_wording"], "unanimously endorsed")
        self.assertEqual(excluded[0]["indexed_final_communique_wording"], "agreed in principle")
        self.assertEqual(excluded[0]["decision"], "EXCLUDE_FROM_CL_LIVE_PAYLOAD")
        payload_text = json.dumps(PAYLOAD, sort_keys=True)
        self.assertNotIn("unanimously endorsed", payload_text)
        self.assertNotIn("agreed in principle", PAYLOAD["observation_template"]["summary"])

    def test_completed_pif_anchor_identity_and_time_are_unchanged(self) -> None:
        canonical = load("data/canonical/registry.json")
        matches = [row for row in canonical["records"] if row.get("occurrence_id") == ANCHOR_ID]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        expected = PLAN["required_anchor"]
        self.assertEqual(row["series_id"], expected["series_id"])
        self.assertEqual(row["canonical_name"], expected["canonical_name"])
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertEqual(row["timing_type"], "MULTI_DAY_LOCAL")
        self.assertEqual(row["start_local"], "2026-08-30")
        self.assertEqual(row["end_local"], "2026-09-04")
        self.assertEqual(row["source_timezone"], "Pacific/Palau")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])
        self.assertEqual(row["source_id"], "WSSRC-INT-012")
        self.assertEqual(row["last_successful_assertion_id"], "WSA-CK-cb548530485b6f03")

    def test_repository_is_exact_prestate_or_reviewed_cl_descendant(self) -> None:
        schema = load("data/live_intelligence/schema.json")
        observations = load("data/live_intelligence/observations.json")
        evidence = load("data/live_intelligence/evidence_registry.json")
        ids = {row.get("observation_id") for row in observations["observations"]}
        evidence_ids = {row.get("evidence_id") for row in evidence["evidence"]}

        if TARGET_ID not in ids:
            self.assertEqual(schema["version"], "0.7")
            self.assertEqual(observations["version"], "0.7")
            self.assertEqual(evidence["version"], "0.7")
            self.assertEqual(len(observations["observations"]), 7)
            self.assertEqual(len(evidence["evidence"]), 10)
            self.assertNotIn(EVIDENCE_ID, evidence_ids)
            return

        self.assertGreaterEqual(version_tuple(schema["version"]), (0, 8))
        self.assertGreaterEqual(version_tuple(observations["version"]), (0, 8))
        self.assertGreaterEqual(version_tuple(evidence["version"]), (0, 8))
        self.assertGreaterEqual(len(observations["observations"]), 8)
        self.assertGreaterEqual(len(evidence["evidence"]), 11)
        self.assertIn(EVIDENCE_ID, evidence_ids)
        row = next(row for row in observations["observations"] if row["observation_id"] == TARGET_ID)
        self.assertEqual(row["canonical_links"], [{"occurrence_id": ANCHOR_ID, "relationship": "OUTCOME_OF"}])
        self.assertEqual(row["regions"], ["Oceania / Pacific"])
        self.assertEqual(row["domain_tags"], ["INSTITUTIONS", "GEOPOLITICS"])
        self.assertNotIn("event_time", row)
        observed = datetime.fromisoformat(row["observed_at_utc"].replace("Z", "+00:00"))
        self.assertIsNotNone(observed.tzinfo)
        policy = schema["population_policy"]
        self.assertGreaterEqual(policy["maximum_observation_count"], 8)
        self.assertGreaterEqual(policy["maximum_evidence_count"], 11)
        self.assertFalse(policy["automatic_ingestion_allowed"])
        self.assertFalse(policy["public_observation_projection_allowed"])
        self.assertIn("cl_checkpoint", schema)

    def test_simulation_is_green_without_writing(self) -> None:
        paths = [
            "data/live_intelligence/schema.json",
            "data/live_intelligence/observations.json",
            "data/live_intelligence/evidence_registry.json",
        ]
        before = {path: (ROOT / path).read_bytes() for path in paths}
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/apply_pif_partner_framework_live_cl.py"),
                "--check",
                "--observed-at-utc",
                "2026-09-10T04:00:00Z",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CL_SIMULATION_VALID", proc.stdout)
        self.assertIn('"event_time_materialised": false', proc.stdout)
        for path, content in before.items():
            self.assertEqual((ROOT / path).read_bytes(), content, path)


if __name__ == "__main__":
    unittest.main()
