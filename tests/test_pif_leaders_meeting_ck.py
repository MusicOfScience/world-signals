from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


PLAN = load("data/coverage/PIF_LEADERS_MEETING_CK_PLAN_v0.1.json")
TARGET_ID = "WSO-INT-A-0001"
SERIES_ID = "WSER-INT-PIF-LEADERS"
PRIMARY_SOURCE_ID = "WSSRC-INT-012"
SUPPORT_SOURCE_ID = "WSSRC-INT-036"


class PIFLeadersMeetingCKContractTests(unittest.TestCase):
    def test_ck_preserves_existing_stable_identity(self):
        target = PLAN["preconditions"]["required_existing_occurrence"]
        self.assertEqual(PLAN["base_main_sha"], "286af17018562fe211db47dd22112a75b842a367")
        self.assertEqual(target["occurrence_id"], TARGET_ID)
        self.assertEqual(target["series_id"], SERIES_ID)
        self.assertEqual(target["canonical_name"], "55th Pacific Islands Forum Leaders Meeting")
        self.assertEqual(target["source_id"], PRIMARY_SOURCE_ID)
        self.assertEqual(target["host_binding_id"], "WSHB-PIF-2026-PW")
        self.assertEqual(target["institution_key"], "PACIFIC_ISLANDS_FORUM")
        self.assertEqual(target["lifecycle_status"], "ACTIVE")
        self.assertEqual(PLAN["change"]["change_type"], "LIFECYCLE_COMPLETION")

    def test_exact_timing_and_sensitivity_contract_is_not_repaired(self):
        target = PLAN["preconditions"]["required_existing_occurrence"]
        expected = {
            "timing_type": "MULTI_DAY_LOCAL",
            "start_local": "2026-08-30",
            "end_local": "2026-09-04",
            "source_timezone": "Pacific/Palau",
            "start_utc": None,
            "end_utc": None,
            "time_precision": "DAY",
            "all_day_semantics": True,
            "time_status": "CONFIRMED",
            "time_basis": "EXPLICIT_AUTHORITATIVE_SCHEDULE",
            "intrinsic_importance": "HIGH",
            "expected_market_sensitivity": "MEDIUM_HIGH",
            "geopolitical_sensitivity": "HIGH",
        }
        for key, value in expected.items():
            self.assertEqual(target[key], value, key)

    def test_source_roles_and_automation_boundary(self):
        primary = PLAN["preconditions"]["required_existing_primary_source"]
        support = PLAN["supporting_source"]
        self.assertEqual(primary["source_id"], PRIMARY_SOURCE_ID)
        self.assertEqual(primary["canonical_dependency_count"], 1)
        self.assertEqual(primary["monitoring_readiness_status"], "RIGHTS_AUDIT_REQUIRED")
        self.assertEqual(support["source_id"], SUPPORT_SOURCE_ID)
        self.assertEqual(support["canonical_dependency_count"], 0)
        self.assertEqual(support["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(support["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(support["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertFalse(support["monitor_route_authorised"])

    def test_failed_guarded_attempts_are_preserved(self):
        failed = PLAN["failed_attempts"]
        self.assertEqual(
            [(row["run_id"], row["job_id"]) for row in failed],
            [(34420349551, 102694182730), (34420540385, 102694756573)],
        )
        self.assertTrue(all(row["governed_write_occurred"] is False for row in failed))

    def test_2027_host_context_does_not_become_a_date(self):
        future = PLAN["future_host_context"]
        self.assertEqual(future["year"], 2027)
        self.assertEqual(future["host_country"], "New Zealand")
        self.assertEqual(future["host_city"], "Auckland")
        self.assertFalse(future["exact_dates_found"])
        self.assertFalse(future["canonical_dated_occurrence_authorised"])
        self.assertTrue(future["rule_generated_date_prohibited"])

    def test_ck_write_and_promotion_gates_are_closed(self):
        self.assertTrue(all(value is False for value in PLAN["authority_gates"].values()))
        boundary = "\n".join(PLAN["protected_boundaries"])
        self.assertIn("Do not create a replacement PIF occurrence or series", boundary)
        self.assertIn("Do not create a 2027 dated occurrence", boundary)
        self.assertIn("Do not activate a PIF Monitor route", boundary)
        self.assertIn("Do not touch OPEC CE quarantine material", boundary)


class PIFLeadersMeetingCKRepositoryStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load("data/canonical/registry.json")
        cls.sources = load("data/sources/registry.json")
        cls.ledger = load("data/changes/ledger.json")
        cls.overlay = load("data/coverage/biosecurity_overlay.json")
        cls.expectations = load("data/monitor/expectations.json")
        cls.live = load("data/live_intelligence/observations.json")
        cls.analysis = load("data/analysis/event_reviews.json")
        cls.by_occ = {row["occurrence_id"]: row for row in cls.registry["records"]}
        cls.by_source = {row["source_id"]: row for row in cls.sources["sources"]}
        cls.by_change = {row["change_id"]: row for row in cls.ledger["changes"]}

    def test_existing_pif_identity_is_unique_and_obsolete_identity_absent(self):
        self.assertIn(TARGET_ID, self.by_occ)
        self.assertEqual(self.by_occ[TARGET_ID]["series_id"], SERIES_ID)
        self.assertEqual(
            sum(1 for row in self.registry["records"] if row.get("series_id") == SERIES_ID),
            1,
        )
        self.assertFalse(any(row.get("series_id") == "WSER-INT-PIF-LM" for row in self.registry["records"]))
        self.assertNotIn("WSO-INT-PIF-LM-055-2026", self.by_occ)

    def test_repository_is_exact_ck_prestate_or_reviewed_descendant(self):
        row = self.by_occ[TARGET_ID]
        if row["lifecycle_status"] == "ACTIVE":
            self.assertEqual(str(self.registry["version"]), "0.41")
            self.assertEqual(self.registry["record_count"], 689)
            self.assertEqual(str(self.sources["version"]), "2.03")
            self.assertEqual(len(self.sources["sources"]), 257)
            self.assertEqual(str(self.ledger["version"]), "0.27")
            self.assertEqual(len(self.ledger["changes"]), 62)
            self.assertNotIn(SUPPORT_SOURCE_ID, self.by_source)
            self.assertNotIn(PLAN["change"]["change_id"], self.by_change)
            return

        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertGreaterEqual(float(self.registry["version"]), 0.42)
        self.assertEqual(self.registry["record_count"], 690)
        self.assertGreaterEqual(len(self.sources["sources"]), 258)
        self.assertGreaterEqual(len(self.ledger["changes"]), 63)
        self.assertIn(SUPPORT_SOURCE_ID, self.by_source)
        self.assertIn(PLAN["change"]["change_id"], self.by_change)

    def test_materialized_pif_semantics_if_completed(self):
        row = self.by_occ[TARGET_ID]
        if row["lifecycle_status"] != "COMPLETED":
            self.skipTest("CK lifecycle completion not materialised yet")
        self.assertEqual(row["series_id"], SERIES_ID)
        self.assertEqual(row["canonical_name"], "55th Pacific Islands Forum Leaders Meeting")
        self.assertEqual(row["category"], "INTERNATIONAL_INSTITUTIONS")
        self.assertEqual(row["subcategory"], "leaders_summit")
        self.assertEqual(row["jurisdiction"], "Pacific")
        self.assertEqual(row["region"], "Oceania / Pacific")
        self.assertEqual(row["institution"], "Pacific Islands Forum")
        self.assertEqual(row["event_type"], "INSTITUTIONAL_MEETING")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertEqual(row["timing_type"], "MULTI_DAY_LOCAL")
        self.assertEqual(row["start_local"], "2026-08-30")
        self.assertEqual(row["end_local"], "2026-09-04")
        self.assertEqual(row["source_timezone"], "Pacific/Palau")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertEqual(row["time_status"], "CONFIRMED")
        self.assertTrue(row["all_day_semantics"])
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])
        self.assertEqual(row["source_id"], PRIMARY_SOURCE_ID)
        self.assertEqual(row["primary_source_assertion_id"], "WSA-99e20d013c0dc998")
        self.assertEqual(row["last_successful_assertion_id"], PLAN["change"]["completion_source_assertion_id"])
        self.assertEqual(row["intrinsic_importance"], "HIGH")
        self.assertEqual(row["expected_market_sensitivity"], "MEDIUM_HIGH")
        self.assertEqual(row["geopolitical_sensitivity"], "HIGH")
        self.assertEqual(row["host_binding_id"], "WSHB-PIF-2026-PW")
        self.assertEqual(row["host_jurisdiction"], "Palau")
        self.assertEqual(row["host_city"], "Koror")
        self.assertEqual(row["last_verified_at"], "2026-09-10")
        self.assertEqual(row["status_history"][-1]["lifecycle_status"], "COMPLETED")
        self.assertIn("not inferred from elapsed time", row["status_history"][-1]["change_reason"])
        self.assertTrue(any(doc.get("source_id") == SUPPORT_SOURCE_ID for doc in row["related_documents"]))

    def test_materialized_source_and_ledger_roles_if_completed(self):
        row = self.by_occ[TARGET_ID]
        if row["lifecycle_status"] != "COMPLETED":
            self.skipTest("CK lifecycle completion not materialised yet")
        primary = self.by_source[PRIMARY_SOURCE_ID]
        support = self.by_source[SUPPORT_SOURCE_ID]
        self.assertEqual(primary["canonical_dependency_count"], 1)
        self.assertEqual(primary["authoritative_url"], "https://55piflm.gov.pw/")
        self.assertEqual(primary["monitoring_readiness_status"], "RIGHTS_AUDIT_REQUIRED")
        self.assertEqual(support["canonical_dependency_count"], 0)
        self.assertEqual(support["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(support["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertNotIn("live_adapter_id", support)
        change = self.by_change[PLAN["change"]["change_id"]]
        self.assertEqual(change["occurrence_id"], TARGET_ID)
        self.assertEqual(change["change_type"], "LIFECYCLE_COMPLETION")
        self.assertEqual(change["old_values"]["lifecycle_status"], "ACTIVE")
        self.assertEqual(change["new_values"]["lifecycle_status"], "COMPLETED")

    def test_no_2027_pif_occurrence_created_by_ck(self):
        pif_rows = [row for row in self.registry["records"] if row.get("series_id") == SERIES_ID]
        self.assertEqual(len(pif_rows), 1)
        self.assertFalse(any("2027" in row.get("occurrence_id", "") for row in pif_rows))

    def test_immediate_ck_boundary_has_no_monitor_or_downstream_population(self):
        # CK-boundary assertions only; later separately reviewed descendants may grow these layers.
        if str(self.expectations.get("version")) == "0.28":
            self.assertFalse(
                any(
                    adapter.get("source_id") in {PRIMARY_SOURCE_ID, SUPPORT_SOURCE_ID}
                    or TARGET_ID in (adapter.get("canonical_occurrence_ids") or [])
                    for adapter in self.expectations.get("adapters", [])
                )
            )
        if len(self.live.get("observations", [])) == 7:
            self.assertFalse(
                any(
                    link.get("occurrence_id") == TARGET_ID
                    for obs in self.live.get("observations", [])
                    for link in (obs.get("canonical_links") or [])
                    if isinstance(link, dict)
                )
            )
        if len(self.analysis.get("reviews", [])) == 22:
            self.assertFalse(
                any(review.get("canonical_occurrence_id") == TARGET_ID for review in self.analysis.get("reviews", []))
            )


if __name__ == "__main__":
    unittest.main()
