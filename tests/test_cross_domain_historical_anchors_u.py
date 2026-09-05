from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_cross_domain_historical_anchors_u import (
    build_post_state,
    overlay_semantics,
    preflight,
)
from src.world_signals.analysis import analysis_population_readiness


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class CrossDomainHistoricalAnchorsUTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load("data/coverage/CROSS_DOMAIN_HISTORICAL_ANCHORS_U_PLAN_v0.1.json")
        cls.registry = load("data/canonical/registry.json")
        cls.schema = load("data/canonical/schema.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.analysis_schema = load("data/analysis/schema.json")
        cls.analysis_reviews = load("data/analysis/event_reviews.json")
        cls.analysis_evidence = load("data/analysis/evidence_registry.json")

    def state(self):
        return (
            str(self.registry.get("version")),
            len(self.registry.get("records", [])),
            str(self.sources.get("version")),
            len(self.sources.get("sources", [])),
            str(self.ledger.get("version")),
            len(self.ledger.get("changes", [])),
        )

    def is_exact_pre(self):
        return self.state() == ("0.29", 678, "1.71", 236, "0.16", 48)

    def simulated_or_live_post(self):
        if self.is_exact_pre():
            preflight(
                self.registry,
                self.schema,
                self.sources,
                self.ledger,
                self.overlay,
                self.analysis_schema,
                self.analysis_reviews,
                self.analysis_evidence,
                self.plan,
            )
            return build_post_state(
                deepcopy(self.registry),
                deepcopy(self.schema),
                deepcopy(self.sources),
                deepcopy(self.ledger),
                deepcopy(self.overlay),
                deepcopy(self.analysis_schema),
                deepcopy(self.analysis_reviews),
                deepcopy(self.analysis_evidence),
                self.plan,
                "2026-09-06T03:30:00+10:00",
            )
        return self.registry, self.sources, self.ledger, self.overlay, {
            "readiness": analysis_population_readiness(
                self.analysis_schema, self.analysis_reviews, self.registry
            )
        }

    def test_repository_is_exact_pre_or_u_descendant(self):
        if self.is_exact_pre():
            return
        self.assertGreaterEqual(tuple(map(int, str(self.registry["version"]).split("."))), (0, 30))
        self.assertGreaterEqual(len(self.registry["records"]), 681)
        self.assertGreaterEqual(tuple(map(int, str(self.sources["version"]).split("."))), (1, 72))
        self.assertGreaterEqual(len(self.sources["sources"]), 237)
        self.assertGreaterEqual(tuple(map(int, str(self.ledger["version"]).split("."))), (0, 17))
        self.assertGreaterEqual(len(self.ledger["changes"]), 51)
        self.assertEqual(str(self.schema["version"]), "0.52")

    def test_u_uses_three_existing_series_and_one_new_source(self):
        anchors = self.plan["anchors"]
        self.assertEqual(
            [row["occurrence_id"] for row in anchors],
            ["WSO-BWC-WG-2026-S08", "WSO-WOAH-GS-093", "WSO-FIS-NP-BUDGET-2083"],
        )
        existing_series = {row.get("series_id") for row in self.registry["records"]}
        for row in anchors:
            self.assertIn(row["series_id"], existing_series)
        self.assertEqual([row["source_id"] for row in self.plan["new_sources"]], ["WSSRC-INT-034"])
        self.assertFalse(self.plan["guardrails"]["new_series_allowed"])

    def test_simulation_preserves_preexisting_layers(self):
        if not self.is_exact_pre():
            self.skipTest("exact mutation-boundary simulation is exercised from U pre-state")
        before_registry = digest(self.registry)
        before_schema = digest(self.schema)
        before_reviews = digest(self.analysis_reviews)
        before_evidence = digest(self.analysis_evidence)
        post_registry, post_sources, post_ledger, post_overlay, _ = self.simulated_or_live_post()
        self.assertEqual(digest(self.registry), before_registry)
        self.assertEqual(digest(self.schema), before_schema)
        self.assertEqual(digest(self.analysis_reviews), before_reviews)
        self.assertEqual(digest(self.analysis_evidence), before_evidence)
        self.assertEqual(post_registry["records"][:678], self.registry["records"])
        self.assertEqual(post_ledger["changes"][:48], self.ledger["changes"])
        self.assertEqual(overlay_semantics(post_overlay), overlay_semantics(self.overlay))
        self.assertEqual((post_registry["version"], len(post_registry["records"])), ("0.30", 681))
        self.assertEqual((post_sources["version"], len(post_sources["sources"])), ("1.72", 237))
        self.assertEqual((post_ledger["version"], len(post_ledger["changes"])), ("0.17", 51))

    def test_completed_anchor_semantics_are_exact_without_synthetic_time(self):
        post_registry, *_ = self.simulated_or_live_post()
        by_id = {row["occurrence_id"]: row for row in post_registry["records"]}
        bwc = by_id["WSO-BWC-WG-2026-S08"]
        woah = by_id["WSO-WOAH-GS-093"]
        nepal = by_id["WSO-FIS-NP-BUDGET-2083"]

        for row in (bwc, woah, nepal):
            self.assertEqual(row["lifecycle_status"], "COMPLETED")
            self.assertEqual(row["certainty_status"], "CONFIRMED")
            self.assertEqual(row["population_tranche"], "ANALYSIS_HISTORICAL_ANCHOR_U")
            self.assertEqual(len(row["status_history"]), 1)
            self.assertIn("not inferred from elapsed time", row["status_history"][0]["change_reason"])

        self.assertEqual((bwc["start_local"], bwc["end_local"]), ("2026-02-09", "2026-02-13"))
        self.assertEqual(bwc["source_timezone"], "Europe/Zurich")
        self.assertIsNone(bwc["start_utc"])
        self.assertTrue(bwc["all_day_semantics"])

        self.assertEqual((woah["start_local"], woah["end_local"]), ("2026-05-18", "2026-05-22"))
        self.assertEqual(woah["source_timezone"], "Europe/Paris")
        self.assertIsNone(woah["start_utc"])
        self.assertTrue(woah["all_day_semantics"])

        self.assertIsNone(nepal["start_local"])
        self.assertIsNone(nepal["start_utc"])
        self.assertEqual(nepal["source_native_date_label"], "15 Jestha 2083")
        self.assertEqual(nepal["native_calendar_system"], "BIKRAM_SAMBAT_NEPAL")
        self.assertEqual(nepal["native_calendar_year"], 2083)
        self.assertEqual(nepal["gregorian_resolution_status"], "UNRESOLVED_AUTHORITATIVE_CONVERSION")
        self.assertEqual(nepal["publication_time_semantics"], "SOURCE_NATIVE_DATE_ONLY")

    def test_primary_taxonomy_is_not_distorted_by_biosecurity_relationships(self):
        post_registry, *_ = self.simulated_or_live_post()
        by_id = {row["occurrence_id"]: row for row in post_registry["records"]}
        self.assertEqual(by_id["WSO-BWC-WG-2026-S08"]["category"], "INTERNATIONAL_INSTITUTIONS")
        self.assertEqual(by_id["WSO-BWC-WG-2026-S08"]["event_type"], "TREATY_WORKING_GROUP_SESSION")
        self.assertEqual(by_id["WSO-WOAH-GS-093"]["category"], "AGRICULTURE_FOOD")
        self.assertEqual(by_id["WSO-WOAH-GS-093"]["event_type"], "GOVERNANCE_ASSEMBLY_SESSION")
        self.assertEqual(by_id["WSO-FIS-NP-BUDGET-2083"]["event_type"], "FISCAL_POLICY_PROCESS")

    def test_source_identity_and_dependency_boundary(self):
        _, post_sources, *_ = self.simulated_or_live_post()
        by_id = {row["source_id"]: row for row in post_sources["sources"]}
        self.assertEqual(by_id["WSSRC-INT-034"]["canonical_dependency_count"], 1)
        self.assertIn("past", by_id["WSSRC-INT-034"]["endpoint_role"].lower())
        self.assertEqual(by_id["WSSRC-INT-034"]["automated_retrieval_permission"], "PRODUCTION_AUTOMATION_HOLD")
        self.assertEqual(by_id["WSSRC-INT-033"]["canonical_dependency_count"], 2)
        self.assertEqual(by_id["WSSRC-FIS-026"]["canonical_dependency_count"], 2)
        self.assertEqual(by_id["WSSRC-FIS-027"]["canonical_dependency_count"], 0)

    def test_change_ledger_records_each_historical_admission(self):
        _, _, post_ledger, *_ = self.simulated_or_live_post()
        by_occ = {row["occurrence_id"]: row for row in post_ledger["changes"]}
        for item in self.plan["anchors"]:
            change = by_occ[item["occurrence_id"]]
            self.assertEqual(change["change_type"], "HISTORICAL_OCCURRENCE_ADMISSION")
            self.assertEqual(change["old_values"], {"canonical_presence": False})
            self.assertTrue(change["new_values"]["canonical_presence"])
            self.assertTrue(change["canonical_mutation_committed"])

    def test_biosecurity_overlay_semantics_stay_series_level(self):
        _, _, _, post_overlay, _ = self.simulated_or_live_post()
        if self.is_exact_pre():
            self.assertEqual(overlay_semantics(post_overlay), overlay_semantics(self.overlay))
            self.assertEqual(post_overlay["version"], "0.5")
            self.assertEqual(post_overlay["canonical_checkpoint"], {"registry_version": "0.30", "record_count": 681})
        memberships = {
            row["series_id"]: row for row in post_overlay.get("canonical_series_memberships", [])
        }
        self.assertEqual(memberships["WSER-INT-BWC-WG-STRENGTHENING"]["canonical_primary_category"], "INTERNATIONAL_INSTITUTIONS")
        self.assertEqual(memberships["WSER-AGF-WOAH-GENERAL-SESSION"]["canonical_primary_category"], "AGRICULTURE_FOOD")

    def test_u_expands_analytical_choice_without_mutating_analysis_at_u_transaction(self):
        post_registry, *_rest, report = self.simulated_or_live_post()
        readiness = report.get("readiness") or analysis_population_readiness(
            self.analysis_schema, self.analysis_reviews, post_registry
        )
        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 12)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 8)
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 7)
        self.assertEqual(readiness["broad_population_state"], "READY_FOR_CONTROLLED_EXPANSION")
        self.assertFalse(self.plan["guardrails"]["analysis_mutation"])
        u_ids = {"WSO-BWC-WG-2026-S08", "WSO-WOAH-GS-093", "WSO-FIS-NP-BUDGET-2083"}
        self.assertTrue(u_ids <= {row["occurrence_id"] for row in post_registry["records"]})
        if self.analysis_reviews["version"] == "0.4" and len(self.analysis_reviews["reviews"]) == 8:
            reviewed = set(readiness["reviewed_occurrence_ids"])
            for occurrence_id in u_ids | {"WSO-ddb70f8ff05a58fb"}:
                self.assertNotIn(occurrence_id, reviewed)
            self.assertEqual((self.analysis_evidence["version"], len(self.analysis_evidence["evidence"])), ("0.4", 21))
        else:
            self.assertGreaterEqual(tuple(int(part) for part in self.analysis_reviews["version"].split(".")), (0, 4))
            self.assertGreaterEqual(len(self.analysis_reviews["reviews"]), 8)
            self.assertGreaterEqual(tuple(int(part) for part in self.analysis_evidence["version"].split(".")), (0, 4))
            self.assertGreaterEqual(len(self.analysis_evidence["evidence"]), 21)

    def test_global_write_gates_remain_closed(self):
        guardrails = self.plan["guardrails"]
        self.assertFalse(guardrails["canonical_schema_mutation"])
        self.assertFalse(guardrails["analysis_mutation"])
        self.assertFalse(guardrails["monitor_configuration_mutation"])
        self.assertFalse(guardrails["calendar_write"])
        self.assertFalse(guardrails["automatic_canonical_commit"])


if __name__ == "__main__":
    unittest.main()
