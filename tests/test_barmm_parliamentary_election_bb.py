from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_barmm_parliamentary_election_bb as apply_bb


class BarmmParliamentaryElectionBBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = json.loads(apply_bb.PLAN_PATH.read_text(encoding="utf-8"))
        canonical = apply_bb.load(apply_bb.CANONICAL_PATH)
        sources = apply_bb.load(apply_bb.SOURCES_PATH)
        ledger = apply_bb.load(apply_bb.LEDGER_PATH)
        overlay = apply_bb.load(apply_bb.OVERLAY_PATH)

        if canonical.get("version") == "0.38" and canonical.get("record_count") == 688:
            cls.target = apply_bb.simulate(cls.plan, "2026-09-06T21:30:00+10:00")
            cls.pre_canonical = canonical
            cls.pre_sources = sources
            cls.pre_ledger = ledger
            cls.pre_overlay = overlay
        elif canonical.get("version") == "0.39" and canonical.get("record_count") == 689:
            cls.target = {
                "canonical": canonical,
                "sources": sources,
                "ledger": ledger,
                "overlay": overlay,
                "status": apply_bb.STATUS_PATH.read_text(encoding="utf-8"),
                "roadmap": apply_bb.ROADMAP_PATH.read_text(encoding="utf-8"),
            }
            cls.pre_canonical = {"records": canonical["records"][:-1]}
            cls.pre_sources = {"sources": sources["sources"][:-1]}
            cls.pre_ledger = {"changes": ledger["changes"][:-1]}
            cls.pre_overlay = dict(overlay)
            cls.pre_overlay["version"] = "0.13"
            cls.pre_overlay["canonical_checkpoint"] = {
                "registry_version": "0.38",
                "record_count": 688,
            }
            apply_bb.assert_target(cls.plan, cls.target)
        else:
            raise RuntimeError(
                f"BB tests require exact prestate v0.38/688 or reviewed poststate v0.39/689; got {canonical.get('version')}/{canonical.get('record_count')}"
            )

    def test_exact_base_and_deterministic_identities(self) -> None:
        self.assertEqual(
            self.plan["exact_base_main_sha"],
            "b8c5372198e3141c4c3f79ace13083877447f71b",
        )
        item = self.plan["occurrence"]
        self.assertEqual(item["primary_source_assertion_id"], apply_bb.expected_assertion_id(item))
        self.assertEqual(item["change_id"], apply_bb.expected_change_id(item))
        self.assertEqual(item["change_id"], "WSCHANGE-138c3977e91ced60d8")

    def test_target_adds_exactly_one_source_occurrence_and_change(self) -> None:
        canonical = self.target["canonical"]
        sources = self.target["sources"]
        ledger = self.target["ledger"]
        self.assertEqual(canonical["version"], "0.39")
        self.assertEqual(canonical["record_count"], 689)
        self.assertEqual(len(canonical["records"]), len(self.pre_canonical["records"]) + 1)
        self.assertEqual(sources["version"], "1.81")
        self.assertEqual(len(sources["sources"]), len(self.pre_sources["sources"]) + 1)
        self.assertEqual(ledger["version"], "0.25")
        self.assertEqual(len(ledger["changes"]), len(self.pre_ledger["changes"]) + 1)
        self.assertEqual(canonical["records"][:-1], self.pre_canonical["records"])
        self.assertEqual(sources["sources"][:-1], self.pre_sources["sources"])
        self.assertEqual(ledger["changes"][:-1], self.pre_ledger["changes"])

    def test_barmm_occurrence_is_future_civil_date_not_timestamp(self) -> None:
        row = self.target["canonical"]["records"][-1]
        self.assertEqual(row["occurrence_id"], "WSO-EL-PH-BARMM-20260914")
        self.assertEqual(row["series_id"], "WSER-EL-PH-BARMM-PE")
        self.assertEqual(row["timing_type"], "CIVIL_DATE")
        self.assertEqual(row["start_local"], "2026-09-14")
        self.assertEqual(row["source_timezone"], "Asia/Manila")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])
        self.assertEqual(row["time_precision"], "DAY")
        self.assertTrue(row["all_day_semantics"])
        self.assertEqual(row["time_status"], "CONFIRMED")
        self.assertEqual(row["time_basis"], "EXPLICIT_SCHEDULE_TIME")
        self.assertEqual(row["lifecycle_status"], "PLANNED")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertNotIn("publication_bundle_type", row)

    def test_occurrence_uses_existing_election_semantics(self) -> None:
        row = self.target["canonical"]["records"][-1]
        self.assertEqual(row["category"], "ELECTIONS_GOVERNANCE")
        self.assertEqual(row["event_type"], "ELECTION_MILESTONE")
        self.assertEqual(row["election_process_id"], "WSEP-PH-BARMM-2026")
        self.assertEqual(row["election_milestone_type"], "POLL_GENERAL")
        self.assertEqual(row["election_date_basis"], "EXPLICIT_ELECTORAL_AUTHORITY_SCHEDULE")
        self.assertEqual(row["legal_activation_status"], "NOT_APPLICABLE")
        self.assertEqual(row["transition_resolution_mode"], "NO_SEPARATE_TRANSITION_MODEL")
        self.assertEqual(row["visibility_tier"], "ESSENTIAL")
        self.assertEqual(row["render_policy"], "INCLUDE")
        self.assertIsNone(row["observed_market_response"])

    def test_source_governance_keeps_automation_closed(self) -> None:
        source = self.target["sources"]["sources"][-1]
        self.assertEqual(source["source_id"], "WSSRC-EL-PH-001")
        self.assertEqual(source["institution"], "Commission on Elections (COMELEC), Philippines")
        self.assertEqual(source["canonical_dependency_count"], 1)
        self.assertEqual(source["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(source["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(source["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertEqual(source["monitoring_readiness_status"], "RIGHTS_AUDIT_REQUIRED")
        self.assertFalse(source["monitor_endpoints"][0]["preferred_for_monitoring"])
        self.assertIn("CANDIDATE_CONTENT_EXCLUDED", source["monitor_endpoints"][0]["completeness_scope"])

    def test_change_ledger_records_forward_admission_not_completion(self) -> None:
        change = self.target["ledger"]["changes"][-1]
        self.assertEqual(change["change_type"], "FORWARD_OCCURRENCE_ADMISSION")
        self.assertEqual(change["old_values"], {"canonical_presence": False})
        self.assertTrue(change["new_values"]["canonical_presence"])
        self.assertEqual(change["new_values"]["lifecycle_status"], "PLANNED")
        self.assertIsNone(change["new_values"]["start_utc"])
        self.assertEqual(change["new_values"]["election_milestone_type"], "POLL_GENERAL")
        self.assertEqual(change["review_state"], "APPROVED_FOR_CANONICAL_COMMIT")
        self.assertEqual(change["registry_version_before"], "0.38")
        self.assertEqual(change["registry_version_after"], "0.39")

    def test_overlay_advances_checkpoint_only(self) -> None:
        overlay = self.target["overlay"]
        self.assertEqual(overlay["version"], "0.14")
        self.assertEqual(
            overlay["canonical_checkpoint"],
            {"registry_version": "0.39", "record_count": 689},
        )
        self.assertEqual(
            apply_bb.overlay_semantics(overlay),
            apply_bb.overlay_semantics(self.pre_overlay),
        )

    def test_live_and_analysis_populations_are_not_touched(self) -> None:
        post = self.plan["postconditions"]
        live_observations = apply_bb.load(apply_bb.LIVE_OBSERVATIONS_PATH)
        live_evidence = apply_bb.load(apply_bb.LIVE_EVIDENCE_PATH)
        reviews = apply_bb.load(apply_bb.ANALYSIS_REVIEWS_PATH)
        analysis_evidence = apply_bb.load(apply_bb.ANALYSIS_EVIDENCE_PATH)
        self.assertEqual(len(live_observations["observations"]), post["live_observation_count"])
        self.assertEqual(len(live_evidence["evidence"]), post["live_evidence_count"])
        self.assertEqual(len(reviews["reviews"]), post["analysis_review_count"])
        self.assertEqual(len(analysis_evidence["evidence"]), post["analysis_evidence_count"])
        self.assertEqual(apply_bb.production_live_input_count(reviews), 1)
        self.assertEqual(apply_bb.production_analysis_revision_count(reviews), 0)
        self.assertEqual(apply_bb.exact_series_count(reviews), 0)

    def test_status_and_roadmap_advance_without_downstream_pre_authorisation(self) -> None:
        status = self.target["status"]
        roadmap = self.target["roadmap"]
        self.assertIn("Canonical Registry: **v0.39 / 689 occurrences**", status)
        self.assertIn("Source Registry: **v1.81 / 244 sources**", status)
        self.assertIn("reviewed Change Ledger: **v0.25 / 60 entries**", status)
        self.assertIn("No downstream population is pre-authorised", status)
        self.assertIn("BB — BARMM election source + Canonical coverage repair", roadmap)
        self.assertIn("no polling clock time, UTC timestamp, result or market response is invented", roadmap)

    def test_plan_keeps_opapru_context_out_of_canonical_source_population(self) -> None:
        self.assertEqual(self.plan["source"]["source_id"], "WSSRC-EL-PH-001")
        self.assertEqual(self.plan["occurrence"]["source_id"], "WSSRC-EL-PH-001")
        self.assertEqual(self.plan["preconditions"]["source_record_count"] + 1, self.plan["postconditions"]["source_record_count"])
        target_json = json.dumps(self.target["canonical"]["records"][-1], ensure_ascii=False)
        self.assertNotIn("peace.gov.ph", target_json)


if __name__ == "__main__":
    unittest.main()
