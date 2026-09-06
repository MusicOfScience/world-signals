from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_barmm_parliamentary_election_bb as apply_bb


def version_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(raw).split("."))


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
        elif version_tuple(canonical.get("version", "0")) >= (0, 39) and canonical.get("record_count", 0) >= 689:
            # Freeze the reviewed BB historical checkpoint from a legitimate later descendant.
            # Later Canonical/source/ledger growth must not make the historical tranche fail,
            # but the BB artefacts themselves must remain exactly where the BB plan put them.
            post = cls.plan["postconditions"]
            canonical_count = post["canonical_record_count"]
            source_count = post["source_record_count"]
            ledger_count = post["change_ledger_count"]

            canonical_bb = copy.deepcopy(canonical)
            canonical_bb["version"] = post["canonical_registry_version"]
            canonical_bb["record_count"] = canonical_count
            canonical_bb["records"] = canonical_bb["records"][:canonical_count]

            sources_bb = copy.deepcopy(sources)
            sources_bb["version"] = post["source_registry_version"]
            sources_bb["sources"] = sources_bb["sources"][:source_count]

            ledger_bb = copy.deepcopy(ledger)
            ledger_bb["version"] = post["change_ledger_version"]
            ledger_bb["changes"] = ledger_bb["changes"][:ledger_count]

            overlay_bb = copy.deepcopy(overlay)
            overlay_bb["version"] = post["biosecurity_overlay_version"]
            overlay_bb["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

            # The stable BB objects must still be present in the frozen prefix.
            cls.assertions_for_descendant(canonical_bb, sources_bb, ledger_bb)

            cls.target = {
                "canonical": canonical_bb,
                "sources": sources_bb,
                "ledger": ledger_bb,
                "overlay": overlay_bb,
                "status": apply_bb.STATUS_PATH.read_text(encoding="utf-8"),
                "roadmap": apply_bb.ROADMAP_PATH.read_text(encoding="utf-8"),
            }
            cls.pre_canonical = {"records": canonical_bb["records"][:-1]}
            cls.pre_sources = {"sources": sources_bb["sources"][:-1]}
            cls.pre_ledger = {"changes": ledger_bb["changes"][:-1]}
            cls.pre_overlay = dict(overlay_bb)
            cls.pre_overlay["version"] = "0.13"
            cls.pre_overlay["canonical_checkpoint"] = {
                "registry_version": "0.38",
                "record_count": 688,
            }
        else:
            raise RuntimeError(
                "BB tests require exact prestate v0.38/688 or a legitimate descendant "
                f"containing reviewed BB poststate v0.39/689; got {canonical.get('version')}/{canonical.get('record_count')}"
            )

    @staticmethod
    def assertions_for_descendant(canonical: dict, sources: dict, ledger: dict) -> None:
        occurrence = canonical["records"][-1]
        source = sources["sources"][-1]
        change = ledger["changes"][-1]
        if occurrence.get("occurrence_id") != "WSO-EL-PH-BARMM-20260914":
            raise RuntimeError("BB historical occurrence is not preserved at its reviewed checkpoint")
        if source.get("source_id") != "WSSRC-EL-PH-001":
            raise RuntimeError("BB historical source is not preserved at its reviewed checkpoint")
        if change.get("change_id") != "WSCHANGE-138c3977e91ced60d8":
            raise RuntimeError("BB historical change is not preserved at its reviewed checkpoint")

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

    def test_historical_downstream_checkpoint_is_exact_but_later_reviewed_growth_is_allowed(self) -> None:
        post = self.plan["postconditions"]
        self.assertEqual(post["live_schema_version"], "0.4")
        self.assertEqual(post["live_observation_count"], 4)
        self.assertEqual(post["live_evidence_count"], 6)
        self.assertEqual(post["analysis_schema_version"], "0.7")
        self.assertEqual(post["analysis_reviews_version"], "0.17")
        self.assertEqual(post["analysis_review_count"], 21)
        self.assertEqual(post["analysis_evidence_count"], 95)
        self.assertEqual(post["production_live_input_count"], 1)
        self.assertEqual(post["production_analysis_revision_count"], 0)
        self.assertEqual(post["production_exact_timestamp_series_count"], 0)

        live_schema = apply_bb.load(apply_bb.LIVE_SCHEMA_PATH)
        live_observations = apply_bb.load(apply_bb.LIVE_OBSERVATIONS_PATH)
        live_evidence = apply_bb.load(apply_bb.LIVE_EVIDENCE_PATH)
        analysis_schema = apply_bb.load(apply_bb.ANALYSIS_SCHEMA_PATH)
        reviews = apply_bb.load(apply_bb.ANALYSIS_REVIEWS_PATH)
        analysis_evidence = apply_bb.load(apply_bb.ANALYSIS_EVIDENCE_PATH)
        apply_bb.assert_population_descendant_floors(
            post, live_schema, live_observations, live_evidence, analysis_schema, reviews, analysis_evidence
        )

        future_schema = copy.deepcopy(live_schema)
        future_schema["version"] = "0.5"
        future_observations = copy.deepcopy(live_observations)
        future_observations["version"] = "0.5"
        future_observations["observations"].append(copy.deepcopy(future_observations["observations"][0]))
        future_evidence = copy.deepcopy(live_evidence)
        future_evidence["version"] = "0.5"
        future_evidence["evidence"].append(copy.deepcopy(future_evidence["evidence"][0]))
        apply_bb.assert_population_descendant_floors(
            post, future_schema, future_observations, future_evidence, analysis_schema, reviews, analysis_evidence
        )

        below = copy.deepcopy(live_observations)
        below["observations"] = below["observations"][: post["live_observation_count"] - 1]
        with self.assertRaises(SystemExit):
            apply_bb.assert_population_descendant_floors(
                post, live_schema, below, live_evidence, analysis_schema, reviews, analysis_evidence
            )

    def test_bb_plan_freezes_no_downstream_pre_authorisation_without_current_status_coupling(self) -> None:
        gates = self.plan["gates"]
        self.assertFalse(gates["monitor_adapter_added"])
        self.assertFalse(gates["live_observation_added"])
        self.assertFalse(gates["analysis_review_or_revision_added"])
        self.assertFalse(gates["automatic_canonical_commit"])
        self.assertFalse(gates["google_calendar_write"])
        self.assertFalse(gates["utc_timestamp_fabricated"])
        self.assertFalse(gates["future_event_marked_completed"])

    def test_plan_keeps_opapru_context_out_of_canonical_source_population(self) -> None:
        self.assertEqual(self.plan["source"]["source_id"], "WSSRC-EL-PH-001")
        self.assertEqual(self.plan["occurrence"]["source_id"], "WSSRC-EL-PH-001")
        self.assertEqual(self.plan["preconditions"]["source_record_count"] + 1, self.plan["postconditions"]["source_record_count"])
        target_json = json.dumps(self.target["canonical"]["records"][-1], ensure_ascii=False)
        self.assertNotIn("peace.gov.ph", target_json)


if __name__ == "__main__":
    unittest.main()
