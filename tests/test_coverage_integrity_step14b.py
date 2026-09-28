import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.coverage_integrity import (
    EARLIER_SCHEDULED_OCCURRENCE,
    NO_EARLIER_SCHEDULED_OCCURRENCE,
    classify_strategic_publication_discovery,
    detect_earlier_scheduled_occurrences,
    validate_igr_recovery_candidate,
)
from world_signals.public_briefing import build_public_briefing
from world_signals.public_forecast_projection import build_public_forecast_projection


class Step14BCoverageIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forecasts_path = ROOT / "data/forecasts/forecasts.json"
        cls.registry_path = ROOT / "data/canonical/registry.json"
        cls.forecasts = json.loads(cls.forecasts_path.read_text(encoding="utf-8"))
        cls.registry = json.loads(cls.registry_path.read_text(encoding="utf-8"))

    def test_rba_forecast_target_is_not_next_scheduled_occurrence(self):
        row = next(item for item in self.forecasts["forecasts"] if item["forecast_id"] == "WS-FP-RBA-20261103")
        result = detect_earlier_scheduled_occurrences(
            row, self.registry, target_occurrence_id="WSO-7177a9874ef955d4"
        )
        self.assertEqual(result["classification"], EARLIER_SCHEDULED_OCCURRENCE)
        self.assertEqual(result["earlier_occurrences"][0]["occurrence_id"], "WSO-d2a7c4e4416b505b")
        self.assertEqual(result["target_start_utc"], "2026-11-03T03:30:00Z")
        self.assertFalse(result["automatic_forecast_backfill"])

    def test_generic_detector_has_no_warning_when_target_is_next(self):
        row = next(item for item in self.forecasts["forecasts"] if item["forecast_id"] == "WS-FP-RBA-20261103")
        changed = copy.deepcopy(row)
        changed["information_cutoff_at_utc"] = "2026-11-03T03:30:00Z"
        result = detect_earlier_scheduled_occurrences(
            changed, self.registry, target_occurrence_id="WSO-7177a9874ef955d4"
        )
        self.assertEqual(result["classification"], NO_EARLIER_SCHEDULED_OCCURRENCE)

    def test_public_projection_retains_target_and_chronology_without_forecast_mutation(self):
        before = hashlib.sha256(self.forecasts_path.read_bytes()).hexdigest()
        projection = build_public_forecast_projection(self.forecasts, self.registry)
        after = hashlib.sha256(self.forecasts_path.read_bytes()).hexdigest()
        self.assertEqual(before, after)
        rows = {row["forecast_id"]: row for row in projection["forecasts"]}
        rba = rows["WS-FP-RBA-20261103"]
        self.assertEqual(rba["forecast_target"]["occurrence_id"], "WSO-7177a9874ef955d4")
        self.assertEqual(rba["forecast_target"]["display_label"], "FORECAST TARGET / 3 NOV DECISION")
        self.assertEqual(
            rba["chronology"]["classification"],
            EARLIER_SCHEDULED_OCCURRENCE,
        )
        self.assertIn("no public Forecast was issued", json.dumps(rba["chronology"]))
        self.assertNotIn("forecast_provenance", json.dumps(projection))

    def test_brief_keeps_next_to_resolve_distinct_from_calendar_chronology(self):
        outlook = build_public_forecast_projection(self.forecasts, self.registry)
        briefing = build_public_briefing(outlook, {"events": []}, {"reviews": []})
        self.assertEqual(briefing["forecast_resolution"]["status"], "SELECTED")
        self.assertEqual(briefing["forecast_resolution"]["forecast_ids"], ["WS-FP-BOC-20261028", "WS-FP-FED-20261028"])
        self.assertIn("NEXT_TO_RESOLVE_IS_FORECAST_RESOLUTION", briefing["metadata"]["forecast_target_semantics"])
        self.assertTrue(any("not a claim about the next scheduled event" in item for item in briefing["limitations"]))

    def test_igr_candidate_is_review_gated_and_projection_only(self):
        path = ROOT / "data/coverage/STEP14B_AU_IGR_CANONICAL_RECOVERY_CANDIDATE_REVIEW_PENDING.json"
        candidate = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_igr_recovery_candidate(candidate), [])
        self.assertEqual(candidate["publication"]["first_announced_at"], "2026-09-09")
        self.assertEqual(candidate["publication"]["first_discovered_at_utc"], "2026-09-28T14:17:45Z")
        self.assertIsNone(candidate["publication"]["effective_utc"])
        self.assertEqual(candidate["event_type"], "INFORMATION_RELEASE")
        self.assertFalse(candidate["canonical_write_permitted"])

    def test_discovery_contract_distinguishes_exact_approximate_and_unrelated(self):
        self.assertEqual(
            classify_strategic_publication_discovery(
                publication_name="2026 Intergenerational Report",
                announcement_date="2026-09-09",
                release_date="2026-09-21",
                source_role="FIRST_PARTY_AUTHORITATIVE",
            ),
            "AUTHORITATIVE_FUTURE_PUBLICATION_ANNOUNCEMENT",
        )
        self.assertEqual(
            classify_strategic_publication_discovery(
                publication_name="2026 Intergenerational Report",
                announcement_date="2026-09-02",
                release_date=None,
                source_role="FIRST_PARTY_AUTHORITATIVE",
            ),
            "DISCOVERY_WATCH_CANDIDATE",
        )
        self.assertEqual(
            classify_strategic_publication_discovery(
                publication_name="generic ministerial statement",
                announcement_date="2026-09-09",
                release_date="2026-09-21",
                source_role="MEDIA_OR_UNVERIFIED",
            ),
            "NO_CANDIDATE",
        )

    def test_coverage_gap_and_source_candidates_are_not_production_state(self):
        gap = json.loads((ROOT / "data/coverage/STEP14B_AU_IGR_COVERAGE_GAP_AUDIT_v0.1.json").read_text())
        sources = json.loads((ROOT / "data/coverage/STEP14B_AU_TREASURY_SOURCE_GOVERNANCE_CANDIDATES_v0.1.json").read_text())
        self.assertEqual(gap["failure_class"], "PROSPECTIVE_DISCOVERY_MISS")
        self.assertEqual(gap["knowability"]["publicly_knowable_by"], "2026-09-09")
        self.assertTrue(gap["knowability"]["knowledge_time_not_backdated"])
        self.assertFalse(gap["production_writes"]["canonical"])
        self.assertEqual(len(sources["candidates"]), 2)
        self.assertFalse(sources["production_registry_write"])
        self.assertTrue(all(item["automatic_admission"] is False for item in sources["candidates"]))


if __name__ == "__main__":
    unittest.main()
