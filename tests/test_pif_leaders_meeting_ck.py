from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


PLAN = load("data/coverage/PIF_LEADERS_MEETING_CK_PLAN_v0.1.json")


class PIFLeadersMeetingCKContractTests(unittest.TestCase):
    def test_frozen_identity_and_timing_contract(self):
        occurrence = PLAN["occurrence"]
        timing = occurrence["timing"]
        self.assertEqual(PLAN["base_main_sha"], "286af17018562fe211db47dd22112a75b842a367")
        self.assertEqual(occurrence["occurrence_id"], "WSO-INT-PIF-LM-055-2026")
        self.assertEqual(occurrence["series_id"], "WSER-INT-PIF-LM")
        self.assertEqual(occurrence["source_id"], "WSSRC-INT-012")
        self.assertEqual(occurrence["completion_source_id"], "WSSRC-INT-036")
        self.assertEqual(occurrence["category"], "INTERNATIONAL_INSTITUTIONS")
        self.assertEqual(occurrence["region"], "Oceania / Pacific")
        self.assertEqual(occurrence["event_type"], "INSTITUTIONAL_MEETING")
        self.assertEqual(occurrence["certainty_status"], "CONFIRMED")
        self.assertEqual(occurrence["lifecycle_status"], "COMPLETED")
        self.assertEqual(
            timing,
            {
                "timing_type": "MULTI_DAY_LOCAL",
                "start_local": "2026-08-30",
                "end_local": "2026-09-04",
                "source_timezone": "Pacific/Palau",
                "start_utc": None,
                "end_utc": None,
                "time_precision": "DAY_RANGE",
                "all_day_semantics": True,
                "time_status": "CONFIRMED",
                "time_basis": "EXPLICIT_AUTHORITATIVE_SCHEDULE",
            },
        )

    def test_primary_and_supporting_source_roles_are_separate(self):
        primary = PLAN["preconditions"]["required_existing_primary_source"]
        support = PLAN["supporting_source"]
        self.assertEqual(primary["source_id"], "WSSRC-INT-012")
        self.assertEqual(primary["canonical_dependency_count"], 0)
        self.assertEqual(support["source_id"], "WSSRC-INT-036")
        self.assertEqual(support["canonical_dependency_count"], 0)
        self.assertEqual(support["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(support["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(support["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertFalse(support["monitor_route_authorised"])

    def test_2027_host_context_does_not_become_a_date(self):
        future = PLAN["future_host_context"]
        self.assertEqual(future["year"], 2027)
        self.assertEqual(future["host_country"], "New Zealand")
        self.assertEqual(future["host_city"], "Auckland")
        self.assertFalse(future["exact_dates_found"])
        self.assertFalse(future["canonical_dated_occurrence_authorised"])
        self.assertTrue(future["rule_generated_date_prohibited"])

    def test_ck_write_and_promotion_gates_are_closed(self):
        gates = PLAN["authority_gates"]
        self.assertTrue(gates)
        self.assertTrue(all(value is False for value in gates.values()))
        boundary = "\n".join(PLAN["protected_boundaries"])
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

    def test_repository_is_either_exact_prestate_or_reviewed_ck_descendant(self):
        oid = PLAN["occurrence"]["occurrence_id"]
        if oid not in self.by_occ:
            self.assertEqual(str(self.registry["version"]), "0.41")
            self.assertEqual(self.registry["record_count"], 689)
            self.assertEqual(str(self.sources["version"]), "2.03")
            self.assertEqual(len(self.sources["sources"]), 257)
            self.assertEqual(str(self.ledger["version"]), "0.27")
            self.assertEqual(len(self.ledger["changes"]), 62)
            return

        self.assertGreaterEqual(self.registry["record_count"], 690)
        self.assertGreaterEqual(len(self.sources["sources"]), 258)
        self.assertGreaterEqual(len(self.ledger["changes"]), 63)
        self.assertIn("WSSRC-INT-036", self.by_source)
        self.assertIn(PLAN["occurrence"]["change_id"], self.by_change)

    def test_materialized_pif_semantics_if_present(self):
        item = PLAN["occurrence"]
        row = self.by_occ.get(item["occurrence_id"])
        if row is None:
            self.skipTest("CK not materialised yet")
        self.assertEqual(row["series_id"], item["series_id"])
        self.assertEqual(row["canonical_name"], item["canonical_name"])
        self.assertEqual(row["category"], "INTERNATIONAL_INSTITUTIONS")
        self.assertEqual(row["region"], "Oceania / Pacific")
        self.assertEqual(row["institution"], "Pacific Islands Forum")
        self.assertEqual(row["event_type"], "INSTITUTIONAL_MEETING")
        self.assertEqual(row["certainty_status"], "CONFIRMED")
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["timing_type"], "MULTI_DAY_LOCAL")
        self.assertEqual(row["start_local"], "2026-08-30")
        self.assertEqual(row["end_local"], "2026-09-04")
        self.assertEqual(row["source_timezone"], "Pacific/Palau")
        self.assertEqual(row["time_precision"], "DAY_RANGE")
        self.assertEqual(row["time_status"], "CONFIRMED")
        self.assertTrue(row["all_day_semantics"])
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])
        self.assertEqual(row["source_id"], "WSSRC-INT-012")
        self.assertEqual(row["last_successful_assertion_id"], item["completion_source_assertion_id"])
        self.assertEqual(row["population_tranche"], "PIF_LEADERS_MEETING_CK")

    def test_materialized_source_roles_if_present(self):
        if PLAN["occurrence"]["occurrence_id"] not in self.by_occ:
            self.skipTest("CK not materialised yet")
        primary = self.by_source["WSSRC-INT-012"]
        support = self.by_source["WSSRC-INT-036"]
        self.assertEqual(primary["canonical_dependency_count"], 1)
        self.assertEqual(primary["authoritative_url"], "https://55piflm.gov.pw/")
        self.assertEqual(primary["source_timezone"], "Pacific/Palau")
        self.assertEqual(support["canonical_dependency_count"], 0)
        self.assertEqual(support["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(support["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertNotIn("live_adapter_id", support)

    def test_ck_does_not_create_a_2027_pif_occurrence(self):
        pif_rows = [row for row in self.registry["records"] if row.get("series_id") == "WSER-INT-PIF-LM"]
        if not pif_rows:
            self.assertEqual(pif_rows, [])
            return
        self.assertTrue(any(row["occurrence_id"] == "WSO-INT-PIF-LM-055-2026" for row in pif_rows))
        self.assertFalse(any("2027" in row.get("occurrence_id", "") for row in pif_rows))

    def test_immediate_ck_boundary_has_no_monitor_or_downstream_population(self):
        # This is a CK-boundary assertion, not a permanent prohibition on a later separately reviewed route.
        if str(self.expectations.get("version")) == "0.28":
            self.assertFalse(
                any(
                    adapter.get("source_id") in {"WSSRC-INT-012", "WSSRC-INT-036"}
                    or "WSO-INT-PIF-LM-055-2026" in (adapter.get("canonical_occurrence_ids") or [])
                    for adapter in self.expectations.get("adapters", [])
                )
            )
        if len(self.live.get("observations", [])) == 7:
            self.assertFalse(
                any(
                    link.get("occurrence_id") == "WSO-INT-PIF-LM-055-2026"
                    for obs in self.live.get("observations", [])
                    for link in (obs.get("canonical_links") or [])
                    if isinstance(link, dict)
                )
            )
        if len(self.analysis.get("reviews", [])) == 22:
            self.assertFalse(
                any(
                    review.get("canonical_occurrence_id") == "WSO-INT-PIF-LM-055-2026"
                    for review in self.analysis.get("reviews", [])
                )
            )


if __name__ == "__main__":
    unittest.main()
