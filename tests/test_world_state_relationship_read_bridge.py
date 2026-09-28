"""Step 12C dual-track Relationship read bridge tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_read import DATA_PATHS, read_world_state  # noqa: E402


RELATIONSHIP_ID = "WSREL-NZ-RBNZ-OCR-MARKET-REPRICING-202609-001"
RELATIONSHIP_REVISION = f"{RELATIONSHIP_ID}-R1"
RELATIONSHIP_HASH = "778c99b558cdffc1a91d57f506426d73f580a1e16925358b97f736a982062e44"
ADMISSION_ID = "WS-REL-ADMISSION-NZ-RBNZ-20260928-001"
ADMISSION_FINGERPRINT = "f1a48a1a9429ccb3055ba7c776408f9cb07227a30aeb1df664be444bdfd49666"


def request(as_of: str, *, jurisdictions: list[str], dimensions: list[str]) -> dict:
    return {
        "contract_version": "0.1",
        "as_of_utc": as_of,
        "scope": {"jurisdictions": jurisdictions, "dimensions": dimensions, "actor_ids": None},
        "include_negative_evidence": True,
        "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
    }


def data_hashes() -> dict[str, str]:
    return {
        relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for relative in sorted(set(DATA_PATHS.values()))
    }


class WorldStateRelationshipReadBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rbnz_scope = {
            "jurisdictions": ["New Zealand"],
            "dimensions": ["MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS"],
        }

    def test_legacy_v01_checkpoint_remains_empty_and_separate(self):
        legacy = json.loads((ROOT / "data/relationships/relationships.json").read_text())
        production = json.loads((ROOT / "data/relationships/relationships_v0.2.json").read_text())
        self.assertEqual(legacy["relationships"], [])
        self.assertEqual(len(production["relationships"]), 1)

    def test_admission_boundary_is_not_review_boundary(self):
        for cutoff in ("2026-09-28T07:22:05Z", "2026-09-28T07:22:06Z", "2026-09-28T09:04:33Z"):
            proposal = read_world_state(request(cutoff, **self.rbnz_scope))
            self.assertEqual(proposal.get("relationship_history", []), [])
            self.assertEqual(proposal["production_populations"].get("relationship_historical_accepted", 0), 0)
        at_admission = read_world_state(request("2026-09-28T09:04:34Z", **self.rbnz_scope))
        self.assertEqual([row["revision_id"] for row in at_admission["relationship_history"]], [RELATIONSHIP_REVISION])

    def test_historical_subject_time_does_not_backdate_knowledge(self):
        proposal = read_world_state(request("2026-09-02T23:59:59Z", **self.rbnz_scope))
        self.assertEqual(proposal.get("relationship_history", []), [])

    def test_production_relationship_is_exactly_pinned_and_historical(self):
        proposal = read_world_state(request("2026-09-29T00:00:00Z", **self.rbnz_scope))
        row = proposal["relationship_history"][0]
        self.assertEqual(row["relationship_id"], RELATIONSHIP_ID)
        self.assertEqual(row["revision_id"], RELATIONSHIP_REVISION)
        self.assertEqual(row["relationship_class"], "ASSOCIATION")
        self.assertEqual(row["directionality"], "DIRECTED")
        self.assertEqual(row["confidence"], "MEDIUM")
        self.assertEqual(row["lifecycle_state"], "EXPIRED")
        self.assertEqual(row["current_active"], False)
        self.assertEqual(row["historical_status"], "HISTORICAL_ONLY")
        self.assertEqual(row["causal_basis"], [])
        self.assertEqual(row["visibility"], "INTERNAL_ONLY")
        manifest = {entry["layer"]: entry for entry in proposal["source_manifest"] if entry["layer"] in {"RELATIONSHIPS", "RELATIONSHIP_ADMISSION"}}
        self.assertEqual(manifest["RELATIONSHIPS"]["object_sha256"], RELATIONSHIP_HASH)
        self.assertEqual(row["admission_transaction_id"], ADMISSION_ID)
        self.assertEqual(row["admission_transaction_fingerprint"], ADMISSION_FINGERPRINT)
        self.assertEqual(proposal["relationship_context"]["current_active_relationships"], [])

    def test_scope_filter_excludes_rbnz_from_drc_health_query(self):
        proposal = read_world_state(request(
            "2026-09-29T00:00:00Z",
            jurisdictions=["Democratic Republic of the Congo"],
            dimensions=["HEALTH_BIOSECURITY"],
        ))
        self.assertEqual(proposal["relationship_history"], [])
        self.assertEqual(proposal["production_populations"]["relationships_v02_production"], 1)
        self.assertEqual(proposal["production_populations"]["relationship_historical_accepted"], 0)

    def test_active_graph_and_transmission_edges_remain_empty(self):
        proposal = read_world_state(request("2026-09-29T00:00:00Z", **self.rbnz_scope))
        self.assertEqual(proposal["relationships"], [])
        self.assertEqual(proposal["transmission_edges"], [])

    def test_legacy_downstream_selection_remains_empty(self):
        proposal = read_world_state(request("2026-09-29T00:00:00Z", **self.rbnz_scope))
        self.assertEqual(proposal["selected_inputs"]["relationships"], [])
        self.assertEqual(proposal["production_populations"]["relationships_v01_legacy"], 0)
        self.assertEqual(proposal["production_populations"]["risks_regimes"], 0)
        self.assertEqual(proposal["production_populations"]["scenarios"], 0)

    def test_forecast_cutoff_is_not_enriched_by_later_relationship_admission(self):
        proposal = read_world_state(request(
            "2026-09-29T00:00:00Z",
            jurisdictions=["*"],
            dimensions=[
                "MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS",
                "HEALTH_BIOSECURITY",
            ],
        ))
        self.assertEqual(len(proposal["relationship_history"]), 1)
        for forecast in proposal["forecast_outcome_references"]:
            self.assertLess(forecast["information_cutoff_at_utc"], "2026-09-28T09:04:34Z")
            self.assertNotIn(ADMISSION_ID, json.dumps(forecast, sort_keys=True))

    def test_v02_admission_and_read_are_mutation_free_and_deterministic(self):
        before = data_hashes()
        first = read_world_state(request("2026-09-29T00:00:00Z", **self.rbnz_scope))
        second = read_world_state(request("2026-09-29T00:00:00Z", **self.rbnz_scope))
        after = data_hashes()
        self.assertEqual(before, after)
        self.assertEqual(first["semantic_fingerprint"], second["semantic_fingerprint"])
        self.assertEqual(first["source_manifest"], second["source_manifest"])


if __name__ == "__main__":
    unittest.main()
