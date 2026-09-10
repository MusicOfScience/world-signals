from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.apply_japan_household_spending_monitor_bl as tx
from world_signals.adapters.japan_statistics_dashboard import (
    AdapterError,
    JAPAN_HHSPEND_INDICATOR_CODE,
    JAPAN_HHSPEND_STAT_CODE,
    JAPAN_STATISTICS_DASHBOARD_API_DOCS,
    JAPAN_STATISTICS_DASHBOARD_DATA_API,
    JAPAN_STATISTICS_DASHBOARD_NO_DATA_MESSAGE,
    japan_household_spending_data_url,
    parse_japan_household_spending_data_json,
)
from world_signals.japan_household_spending_monitor import (
    japan_household_spending_review_candidates,
)


VALUE = {
    "@indicator": "0704010101000010000",
    "@unit": "116",
    "@stat": "00200561",
    "@regionCode": "00000",
    "@time": "20260700",
    "@cycle": "1",
    "@regionRank": "2",
    "@isSeasonal": "1",
    "@isProvisional": "0",
    "$": "301245",
}


def api_payload(
    values=None,
    *,
    input_time="20260700",
    status=0,
    message=None,
    uppercase_result_keys=False,
) -> str:
    statistical = None
    if values is not None:
        rows = [{"VALUE": deepcopy(row)} for row in values]
        statistical = {"DATA_INF": {"DATA_OBJ": rows}}
    if message is None:
        message = "Success." if status == 0 else "failure"
    if uppercase_result_keys:
        result = {"STATUS": str(status), "ERROR_MSG": message}
    else:
        result = {"status": str(status), "errorMsg": message, "date": "Tue Sep 08 08:27:29 JST 2026"}
    get_stats = {
        "RESULT": result,
        "PARAMETER": {"time": input_time},
    }
    if statistical is not None:
        get_stats["STATISTICAL_DATA"] = statistical
    return json.dumps({"GET_STATS": get_stats}, ensure_ascii=False)


def canonical_record(
    occurrence_id: str,
    release_date: str,
    *,
    lifecycle: str = "PLANNED",
) -> dict:
    return {
        "occurrence_id": occurrence_id,
        "series_id": "WSER-MAC-JP-HHSPEND",
        "source_id": "WSSRC-MAC-024",
        "source_timezone": "Asia/Tokyo",
        "start_local": release_date,
        "start_utc": None,
        "time_precision": "DAY",
        "certainty_status": "CONFIRMED",
        "lifecycle_status": lifecycle,
    }


def config(rows: list[tuple[str, str]]) -> dict:
    return {
        "adapter_id": "JAPAN_HHSPEND_STATISTICS_DASHBOARD_API",
        "source_id": "WSSRC-MAC-030",
        "canonical_occurrence_ids": [oid for oid, _ in rows],
        "tracked_releases": [
            {"occurrence_id": oid, "reference_period_code": period}
            for oid, period in rows
        ],
        "required_manual_verification_source_ids": ["WSSRC-MAC-029"],
        "automatic_commit_allowed": False,
    }


class JapanHouseholdSpendingMonitorBLTests(unittest.TestCase):
    def test_official_api_identity_and_bounded_query_are_frozen(self):
        self.assertEqual(
            JAPAN_STATISTICS_DASHBOARD_API_DOCS,
            "https://dashboard.e-stat.go.jp/en/static/api",
        )
        self.assertEqual(
            JAPAN_STATISTICS_DASHBOARD_DATA_API,
            "https://dashboard.e-stat.go.jp/api/1.0/Json/getData?",
        )
        self.assertEqual(JAPAN_HHSPEND_INDICATOR_CODE, "0704010101000010000")
        self.assertEqual(JAPAN_HHSPEND_STAT_CODE, "00200561")
        url = japan_household_spending_data_url(
            time_from="20260700", time_to="20270200"
        )
        self.assertIn("IndicatorCode=0704010101000010000", url)
        self.assertIn("TimeFrom=20260700", url)
        self.assertIn("TimeTo=20270200", url)
        self.assertIn("RegionalRank=2", url)
        self.assertIn("IsSeasonalAdjustment=1", url)

    def test_parser_extracts_only_validated_value_rows_from_live_lowercase_shape(self):
        values = parse_japan_household_spending_data_json(api_payload([VALUE]))
        self.assertEqual(len(values), 1)
        row = values[0]
        self.assertEqual(row.reference_period_code, "20260700")
        self.assertEqual(row.value, "301245")
        self.assertFalse(row.is_provisional)
        self.assertEqual(row.indicator_code, JAPAN_HHSPEND_INDICATOR_CODE)
        self.assertEqual(row.stat_code, JAPAN_HHSPEND_STAT_CODE)
        self.assertEqual(row.region_code, "00000")

    def test_legacy_uppercase_result_keys_remain_parseable(self):
        values = parse_japan_household_spending_data_json(
            api_payload([VALUE], uppercase_result_keys=True)
        )
        self.assertEqual([row.reference_period_code for row in values], ["20260700"])

    def test_official_status_one_normal_no_data_is_empty_only_without_statistical_data(self):
        body = api_payload(
            None,
            input_time="20260800",
            status=1,
            message=JAPAN_STATISTICS_DASHBOARD_NO_DATA_MESSAGE,
        )
        self.assertIn("20260800", body)
        self.assertEqual(parse_japan_household_spending_data_json(body), [])

        with self.assertRaises(AdapterError):
            parse_japan_household_spending_data_json(
                api_payload(
                    [VALUE],
                    input_time="20260800",
                    status=1,
                    message=JAPAN_STATISTICS_DASHBOARD_NO_DATA_MESSAGE,
                )
            )

    def test_echoed_requested_month_is_not_data_availability(self):
        body = api_payload(
            None,
            input_time="20260800",
            status=1,
            message=JAPAN_STATISTICS_DASHBOARD_NO_DATA_MESSAGE,
        )
        self.assertIn("20260800", body)
        values = parse_japan_household_spending_data_json(body)
        self.assertEqual(values, [])

    def test_parser_fails_closed_on_identity_drift_duplicate_or_api_error(self):
        wrong = deepcopy(VALUE)
        wrong["@indicator"] = "wrong"
        with self.assertRaises(AdapterError):
            parse_japan_household_spending_data_json(api_payload([wrong]))
        with self.assertRaises(AdapterError):
            parse_japan_household_spending_data_json(api_payload([VALUE, VALUE]))
        with self.assertRaises(AdapterError):
            parse_japan_household_spending_data_json(api_payload(None, status=7))
        with self.assertRaises(AdapterError):
            parse_japan_household_spending_data_json(
                api_payload(None, status=1, message="unexpected status-one response")
            )

    def test_completed_occurrence_is_observation_only_even_when_data_present(self):
        values = parse_japan_household_spending_data_json(api_payload([VALUE]))
        records = [canonical_record("WSO-MAC-B-0041", "2026-09-04", lifecycle="COMPLETED")]
        candidates, observations = japan_household_spending_review_candidates(
            records,
            values,
            config([("WSO-MAC-B-0041", "20260700")]),
            now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(
            observations[0]["type"],
            "JAPAN_HHSPEND_COMPLETED_REFERENCE_PERIOD_DATA_AVAILABLE",
        )
        self.assertEqual(observations[0]["event_state_inference"], "NONE")

    def test_planned_absence_never_means_delay_cancellation_or_date_change(self):
        records = [canonical_record("WSO-MAC-B-0042", "2026-10-09")]
        candidates, observations = japan_household_spending_review_candidates(
            records,
            [],
            config([("WSO-MAC-B-0042", "20260800")]),
            now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc),
        )
        self.assertEqual(candidates, [])
        self.assertEqual(
            observations[0]["type"],
            "JAPAN_HHSPEND_DATA_NOT_YET_AVAILABLE_NO_EVENT_INFERENCE",
        )
        self.assertTrue(observations[0]["absence_is_not_cancellation_or_date_change"])
        self.assertEqual(observations[0]["event_state_inference"], "NONE")

    def test_early_data_presence_generates_review_without_schedule_inference(self):
        early = deepcopy(VALUE)
        early["@time"] = "20260800"
        values = parse_japan_household_spending_data_json(api_payload([early]))
        records = [canonical_record("WSO-MAC-B-0042", "2026-10-09")]
        candidates, observations = japan_household_spending_review_candidates(
            records,
            values,
            config([("WSO-MAC-B-0042", "20260800")]),
            now_utc=datetime(2026, 9, 8, tzinfo=timezone.utc),
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(
            candidate["candidate_type"],
            "JAPAN_HHSPEND_DATA_AVAILABLE_BEFORE_PLANNED_RELEASE_REVIEW",
        )
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertEqual(candidate["review_state"], "PENDING_SCHEDULE_AND_RESULT_REVIEW")
        self.assertEqual(candidate["old_value"]["canonical_start_local"], "2026-10-09")
        self.assertIsNone(candidate["old_value"]["canonical_start_utc"])
        self.assertTrue(candidate["new_value"]["no_schedule_change_inferred"])
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertEqual(
            observations[0]["type"],
            "JAPAN_HHSPEND_DATA_AVAILABLE_EARLY_REVIEW_REQUIRED",
        )

    def test_on_or_after_date_presence_requires_manual_completion_verification(self):
        august = deepcopy(VALUE)
        august["@time"] = "20260800"
        values = parse_japan_household_spending_data_json(api_payload([august]))
        records = [canonical_record("WSO-MAC-B-0042", "2026-10-09")]
        candidates, _ = japan_household_spending_review_candidates(
            records,
            values,
            config([("WSO-MAC-B-0042", "20260800")]),
            now_utc=datetime(2026, 10, 9, 3, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(
            candidate["candidate_type"],
            "JAPAN_HHSPEND_DATA_AVAILABLE_COMPLETION_REVIEW",
        )
        self.assertEqual(
            candidate["event_state_inference"],
            "POTENTIAL_COMPLETION_REQUIRES_MANUAL_VERIFICATION",
        )
        self.assertEqual(
            candidate["required_manual_verification_source_ids"],
            ["WSSRC-MAC-029"],
        )
        self.assertFalse(candidate["automatic_commit_allowed"])

    def test_scope_and_canonical_source_precision_are_fail_closed(self):
        records = [canonical_record("A", "2026-10-09")]
        cfg = config([("A", "20260800")])
        cfg["canonical_occurrence_ids"].append("B")
        with self.assertRaises(ValueError):
            japan_household_spending_review_candidates(records, [], cfg)

        bad_source = [canonical_record("A", "2026-10-09")]
        bad_source[0]["source_id"] = "WSSRC-MAC-030"
        with self.assertRaises(ValueError):
            japan_household_spending_review_candidates(
                bad_source, [], config([("A", "20260800")])
            )

        bad_precision = [canonical_record("A", "2026-10-09")]
        bad_precision[0]["time_precision"] = "MINUTE"
        with self.assertRaises(ValueError):
            japan_household_spending_review_candidates(
                bad_precision, [], config([("A", "20260800")])
            )

    def test_bl_pre_or_post_state_contract_and_source_decomposition(self):
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        pre_transaction = sources["version"] == "1.84" and expectations["version"] == "0.11"

        if pre_transaction:
            post_sources, post_expectations, live, smoke, adapter_init = tx.build_post_state()
            pre_by_id = {row["source_id"]: row for row in sources["sources"]}
            post_by_id = {row["source_id"]: row for row in post_sources["sources"]}
            self.assertEqual(set(post_by_id), set(pre_by_id) | {"WSSRC-MAC-030"})
            for source_id in pre_by_id:
                self.assertEqual(post_by_id[source_id], pre_by_id[source_id], source_id)
            self.assertEqual(post_expectations["adapters"][:9], expectations["adapters"])
        else:
            self.assertGreaterEqual(
                tuple(map(int, sources["version"].split("."))), (1, 85)
            )
            self.assertGreaterEqual(
                tuple(map(int, expectations["version"].split("."))), (0, 12)
            )
            post_sources, post_expectations = sources, expectations
            live = (ROOT / "scripts/run_live_monitor.py").read_text()
            smoke = (ROOT / "scripts/run_adapter_smoke.py").read_text()
            adapter_init = (ROOT / "src/world_signals/adapters/__init__.py").read_text()

        self.assertGreaterEqual(len(post_sources["sources"]), 247)
        self.assertGreaterEqual(len(post_expectations["adapters"]), 10)
        machine = next(row for row in post_sources["sources"] if row["source_id"] == "WSSRC-MAC-030")
        schedule = next(row for row in post_sources["sources"] if row["source_id"] == "WSSRC-MAC-024")
        self.assertEqual(machine["canonical_dependency_count"], 0)
        self.assertEqual(machine["automated_monitoring_use"], "CLEARED")
        self.assertEqual(machine["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(schedule["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(
            machine["source_role_contract"]["canonical_schedule_source_id"],
            "WSSRC-MAC-024",
        )
        route = next(
            row for row in post_expectations["adapters"]
            if row["adapter_id"] == "JAPAN_HHSPEND_STATISTICS_DASHBOARD_API"
        )
        self.assertEqual(route["source_id"], "WSSRC-MAC-030")
        self.assertEqual(len(route["canonical_occurrence_ids"]), 8)
        self.assertEqual(route["api_query"]["time_from"], "20260700")
        self.assertEqual(route["api_query"]["time_to"], "20270200")
        self.assertEqual(
            route["source_role_contract"]["canonical_schedule_source_id"],
            "WSSRC-MAC-024",
        )
        self.assertFalse(route["automatic_commit_allowed"])
        self.assertFalse(post_expectations["automatic_canonical_commit"])
        self.assertFalse(post_expectations["google_calendar_write"])
        self.assertIn("JAPAN_HHSPEND_STATISTICS_DASHBOARD_API", live)
        self.assertIn("JAPAN_HHSPEND_STATISTICS_DASHBOARD_API", smoke)
        self.assertIn("JAPAN_STATISTICS_DASHBOARD_DATA_API", adapter_init)

        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        hh = [row for row in canonical["records"] if row.get("series_id") == "WSER-MAC-JP-HHSPEND"]
        self.assertGreaterEqual(tuple(map(int, canonical["version"].split("."))), (0, 41))
        self.assertGreaterEqual(len(canonical["records"]), 689)
        self.assertEqual(len(hh), 8)
        self.assertTrue(all(row["source_id"] == "WSSRC-MAC-024" for row in hh))
        self.assertTrue(all(row["source_timezone"] == "Asia/Tokyo" for row in hh))
        self.assertTrue(all(row["time_precision"] == "DAY" for row in hh))
        self.assertTrue(all(row.get("start_utc") is None for row in hh))

        live_data = json.loads((ROOT / "data/live_intelligence/observations.json").read_text())
        analysis = json.loads((ROOT / "data/analysis/event_reviews.json").read_text())
        self.assertGreaterEqual(tuple(map(int, live_data["version"].split("."))), (0, 6))
        self.assertGreaterEqual(len(live_data["observations"]), 6)
        analysis_version = tuple(int(part) for part in analysis["version"].split("."))
        self.assertGreaterEqual(analysis_version, (0, 17))
        self.assertGreaterEqual(len(analysis["reviews"]), 21)


if __name__ == "__main__":
    unittest.main()
