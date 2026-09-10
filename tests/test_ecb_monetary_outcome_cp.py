from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.ecb_monetary_outcome_cp import (
    ASSERTION_ID,
    CHANGE_ID,
    EVIDENCE_ID,
    OBSERVATION_ID,
    OCCURRENCE_ID,
    OUTCOME_SOURCE_ID,
    SERIES_ID,
    TARGET_CANONICAL_VERSION,
    TARGET_LEDGER_VERSION,
    TARGET_LIVE_VERSION,
    TARGET_OVERLAY_VERSION,
    build_target_state,
    target_canonical_registry,
    target_change_ledger,
    target_evidence,
    target_live_schema,
    target_observations,
    target_overlay,
    validate_cp_contract,
)
from world_signals.live_intelligence import public_live_intelligence_projection, validate_live_intelligence
from world_signals.validation import validate_registry
from world_signals.analytical_overlays import validate_biosecurity_overlay

PLAN = ROOT / "data/live_intelligence/ECB_MONETARY_OUTCOME_CP_PRODUCTION_PLAN_v0.1.json"
PAYLOAD = ROOT / "data/live_intelligence/ECB_MONETARY_OUTCOME_CP_PAYLOAD_v0.1.json"
CANONICAL = ROOT / "data/canonical/registry.json"
SOURCES = ROOT / "data/sources/registry.json"
LEDGER = ROOT / "data/changes/ledger.json"
OVERLAY = ROOT / "data/coverage/biosecurity_overlay.json"
SCHEMA = ROOT / "data/live_intelligence/schema.json"
OBSERVATIONS = ROOT / "data/live_intelligence/observations.json"
EVIDENCE = ROOT / "data/live_intelligence/evidence_registry.json"
MONITOR = ROOT / "data/monitor/expectations.json"
ANALYSIS_REVIEWS = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE = ROOT / "data/analysis/evidence_registry.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ECBMonetaryOutcomeCPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN)
        cls.payload = load(PAYLOAD)
        cls.registry = load(CANONICAL)
        cls.sources = load(SOURCES)
        cls.ledger = load(LEDGER)
        cls.overlay = load(OVERLAY)
        cls.schema = load(SCHEMA)
        cls.observations = load(OBSERVATIONS)
        cls.evidence = load(EVIDENCE)

    def simulate(self):
        return build_target_state(
            self.registry, self.sources, self.ledger, self.overlay,
            self.schema, self.observations, self.evidence,
            self.payload, self.plan,
        )

    def test_plan_freezes_exact_prestate_and_ordered_target(self):
        p = self.plan["preconditions"]
        target = self.plan["expected_post_state"]
        self.assertEqual(self.plan["base_main_sha"], "e1f5c97c183381f7d29bf6957aecd87cacaa96a0")
        self.assertEqual(p["canonical_registry_version"], "0.42")
        self.assertEqual(p["change_ledger_version"], "0.28")
        self.assertEqual(p["live_schema_version"], "0.11")
        self.assertEqual(p["live_observation_count"], 10)
        self.assertEqual(p["live_evidence_count"], 14)
        self.assertEqual(target["canonical_registry_version"], TARGET_CANONICAL_VERSION)
        self.assertEqual(target["change_ledger_version"], TARGET_LEDGER_VERSION)
        self.assertEqual(target["live_schema_version"], TARGET_LIVE_VERSION)
        self.assertEqual(target["live_observation_count"], 11)
        self.assertEqual(target["live_evidence_count"], 15)
        self.assertEqual(self.plan["ordering_contract"][0], "Stage 1 must complete and validate the existing Canonical anchor before Stage 2 may materialise.")

    def test_primary_evidence_is_ecb_and_secondary_source_not_required(self):
        p = self.plan["primary_evidence"]
        self.assertEqual(p["registered_source_id"], OUTCOME_SOURCE_ID)
        self.assertIn("ecb.mp260910~314e508016", p["decision_url"])
        self.assertEqual(p["decision_publication_utc"], "2026-09-10T12:15:00Z")
        self.assertEqual(p["statement_publication_utc"], "2026-09-10T13:00:00Z")
        self.assertEqual(p["new_rate_levels"], {
            "deposit_facility_percent": 2.5,
            "main_refinancing_operations_percent": 2.65,
            "marginal_lending_facility_percent": 2.9,
        })
        self.assertEqual(p["effective_date"], "2026-09-16")
        self.assertFalse(p["secondary_source_required"])

    def test_payload_is_bounded_to_rate_decision(self):
        row = self.payload["live_observation"]
        ev = self.payload["live_evidence"][0]
        self.assertEqual(row["observation_id"], OBSERVATION_ID)
        self.assertEqual(row["observation_type"], "POLICY_DEVELOPMENT")
        self.assertEqual(row["verification_state"], "PRIMARY_CONFIRMED")
        self.assertEqual(row["canonical_links"], [{"occurrence_id": OCCURRENCE_ID, "relationship": "OUTCOME_OF"}])
        self.assertEqual(row["evidence_refs"], [EVIDENCE_ID])
        self.assertEqual(row["jurisdictions"], ["Euro area"])
        self.assertEqual(row["regions"], ["Europe"])
        self.assertEqual(row["domain_tags"], ["ECONOMICS", "MARKETS"])
        self.assertIsNone(row["revision_of_observation_id"])
        self.assertNotIn("event_time", row)
        self.assertEqual(ev["evidence_class"], "PRIMARY_OFFICIAL")
        self.assertEqual(ev["provider"], "European Central Bank")
        self.assertEqual(ev["publication_time"], {"precision": "EXACT_TIMESTAMP", "published_at_utc": "2026-09-10T12:15:00Z"})
        self.assertEqual(ev["canonical_provenance_effect"], "NONE")
        joined = " ".join(self.payload["scope_exclusions"]).lower()
        for boundary in ("projections", "expectation", "asset-price", "source registry", "analysis", "opec"):
            self.assertIn(boundary, joined)

    def test_simulated_stage_one_preserves_canonical_identity_and_clock(self):
        post_registry, _, _, _, _, _ = self.simulate()
        before = next(r for r in self.registry["records"] if r["occurrence_id"] == OCCURRENCE_ID)
        after = next(r for r in post_registry["records"] if r["occurrence_id"] == OCCURRENCE_ID)
        self.assertEqual(after["series_id"], SERIES_ID)
        self.assertEqual(after["lifecycle_status"], "COMPLETED")
        self.assertEqual(after["certainty_status"], "CONFIRMED")
        self.assertEqual(after["last_successful_assertion_id"], ASSERTION_ID)
        for key in (
            "canonical_name", "source_id", "primary_source_assertion_id", "timing_type",
            "start_local", "end_local", "source_timezone", "start_utc", "end_utc",
            "time_precision", "time_status", "time_basis", "intrinsic_importance",
            "expected_market_sensitivity", "geopolitical_sensitivity", "parent_occurrence_id",
            "related_occurrence_ids",
        ):
            self.assertEqual(after.get(key), before.get(key), key)
        self.assertEqual(after["start_local"], "2026-09-10T14:15:00")
        self.assertEqual(after["source_timezone"], "Europe/Berlin")
        self.assertEqual(after["start_utc"], "2026-09-10T12:15:00Z")

    def test_stage_two_cannot_link_to_planned_anchor(self):
        planned_registry = copy.deepcopy(self.registry)
        target = next(r for r in planned_registry["records"] if r["occurrence_id"] == OCCURRENCE_ID)
        target["lifecycle_status"] = "PLANNED"
        with self.assertRaisesRegex(ValueError, "COMPLETED ECB Canonical anchor"):
            target_observations(self.observations, self.payload, self.plan, planned_registry)

    def test_simulated_final_state_validates(self):
        post_registry, post_ledger, post_overlay, post_schema, post_obs, post_ev = self.simulate()
        self.assertEqual(validate_cp_contract(post_registry, self.sources, post_ledger, post_overlay, post_schema, post_obs, post_ev, self.plan), [])
        reg = validate_registry(post_registry, self.sources)
        self.assertTrue(reg.ok, reg.errors)
        overlay_errors = validate_biosecurity_overlay(post_registry, post_overlay)
        self.assertEqual(overlay_errors, [])
        live = validate_live_intelligence(post_schema, post_ev, post_obs, post_registry)
        self.assertTrue(live.ok, live.errors)

    def test_live_schema_preserves_cm_and_closes_public_gates(self):
        _, _, _, post_schema, post_obs, post_ev = self.simulate()
        self.assertEqual(post_schema["correction_conflict_policy"], self.schema["correction_conflict_policy"])
        self.assertFalse(post_schema["population_policy"]["automatic_ingestion_allowed"])
        self.assertFalse(post_schema["population_policy"]["public_observation_projection_allowed"])
        self.assertFalse(post_schema["public_projection_policy"]["observation_projection_allowed"])
        public = public_live_intelligence_projection(post_schema, post_ev, post_obs, self.simulate()[0])
        self.assertEqual(public["observations"], [])

    def test_source_monitor_and_analysis_populations_remain_unmodified(self):
        monitor = load(MONITOR)
        reviews = load(ANALYSIS_REVIEWS)
        analysis_evidence = load(ANALYSIS_EVIDENCE)
        self.assertEqual(len(self.sources["sources"]), 258)
        self.assertEqual(len(monitor["adapters"]), 26)
        self.assertEqual(len(reviews["reviews"]), 22)
        self.assertEqual(len(analysis_evidence["evidence"]), 97)
        self.assertFalse(monitor["automatic_canonical_commit"])
        self.assertFalse(monitor["google_calendar_write"])
        source = next(s for s in self.sources["sources"] if s["source_id"] == OUTCOME_SOURCE_ID)
        self.assertEqual(source["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(source["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")

    def test_change_ledger_and_overlay_are_bounded(self):
        _, post_ledger, post_overlay, _, _, _ = self.simulate()
        self.assertEqual(len(post_ledger["changes"]), 64)
        change = post_ledger["changes"][-1]
        self.assertEqual(change["change_id"], CHANGE_ID)
        self.assertEqual(change["occurrence_id"], OCCURRENCE_ID)
        self.assertEqual(change["change_type"], "LIFECYCLE_COMPLETION")
        self.assertEqual(post_overlay["version"], TARGET_OVERLAY_VERSION)
        self.assertEqual(post_overlay["canonical_checkpoint"], {"registry_version": TARGET_CANONICAL_VERSION, "record_count": 689})
        before_semantics = {k: v for k, v in self.overlay.items() if k not in {"version", "canonical_checkpoint"}}
        after_semantics = {k: v for k, v in post_overlay.items() if k not in {"version", "canonical_checkpoint"}}
        self.assertEqual(after_semantics, before_semantics)

    def test_target_transforms_are_idempotent_after_simulation(self):
        post_registry, post_ledger, post_overlay, post_schema, post_obs, post_ev = self.simulate()
        self.assertEqual(target_canonical_registry(post_registry, self.payload, self.plan), post_registry)
        self.assertEqual(target_change_ledger(post_ledger, self.payload, self.plan), post_ledger)
        self.assertEqual(target_overlay(post_overlay, self.plan), post_overlay)
        self.assertEqual(target_live_schema(post_schema, self.plan), post_schema)
        self.assertEqual(target_observations(post_obs, self.payload, self.plan, post_registry), post_obs)
        self.assertEqual(target_evidence(post_ev, self.payload, self.plan), post_ev)

    def test_population_overflow_fails_closed(self):
        post_registry, _, _, post_schema, post_obs, post_ev = self.simulate()
        overflow = copy.deepcopy(post_obs)
        extra = copy.deepcopy(self.payload["live_observation"])
        extra["observation_id"] = "WSLI-TEST-CP-OVERFLOW"
        overflow["observations"].append(extra)
        report = validate_live_intelligence(post_schema, post_ev, overflow, post_registry)
        self.assertFalse(report.ok)
        self.assertTrue(any("exceeds reviewed policy maximum" in err for err in report.errors), report.errors)


if __name__ == "__main__":
    unittest.main()
