from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError, FetchSnapshot
from world_signals.adapters.indec_calendar import (
    INDEC_TIMEZONE,
    fetch_indec_cpi_months,
    indec_routes_allowed,
    parse_indec_cpi_month,
)
from world_signals.indec_cpi_monitor import indec_cpi_calendar_review_candidates


IDENTITIES = [
    ("WSO-REG-B-0008", "Agosto de 2026", "2026-09-10", "Septiembre-2026"),
    ("WSO-REG-B-0009", "Septiembre de 2026", "2026-10-13", "Octubre-2026"),
    ("WSO-REG-B-0010", "Octubre de 2026", "2026-11-12", "Noviembre-2026"),
    ("WSO-REG-B-0011", "Noviembre de 2026", "2026-12-15", "Diciembre-2026"),
]


def title(reference_period_es: str) -> str:
    return f"Índice de precios al consumidor (IPC). Cobertura nacional. {reference_period_es}"


def fixture(reference_period_es: str, release_date: str, *, time_value: str = "16:00:00", ctz: str = INDEC_TIMEZONE) -> str:
    compact = release_date.replace("-", "")
    hhmmss = time_value.replace(":", "")
    start = f"{compact}T{hhmmss}"
    start_dt = datetime.strptime(start, "%Y%m%dT%H%M%S")
    end_dt = start_dt + timedelta(minutes=30)
    end = end_dt.strftime("%Y%m%dT%H%M%S")
    report = title(reference_period_es)
    encoded_report = report.replace("Í", "&#205;")
    href = (
        "https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={quote_plus(report)}&dates={start}/{end}&ctz={ctz}"
    ).replace("&", "&amp;")
    visible = time_value[:5] + "hs"
    return f'''<div class="nro-dia">{int(release_date[-2:])}</div>
<div class="cal-content text-calendario">{encoded_report}</div>
<div class="cal-content text-calendario text-center">{visible}</div>
<a href="{href}" target="_blank">agendar</a>'''


def release(reference_period_es: str, release_date: str, month_slug: str, *, time_value: str = "16:00:00"):
    return parse_indec_cpi_month(fixture(reference_period_es, release_date, time_value=time_value), month_slug=month_slug)


def canonical_records() -> list[dict]:
    rows=[]
    for occurrence_id, reference_period_es, release_date, _month_slug in IDENTITIES:
        rows.append({
            "occurrence_id": occurrence_id,
            "series_id": "WSER-REG2-AR-CPI",
            "source_id": "WSSRC-REG2-006",
            "region": "Latin America",
            "source_timezone": INDEC_TIMEZONE,
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "start_local": release_date,
            "start_utc": None,
            "all_day_semantics": True,
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        })
    return rows


def config() -> dict:
    return {
        "adapter_id": "INDEC_CPI_CALENDAR",
        "source_id": "WSSRC-REG2-009",
        "canonical_schedule_source_id": "WSSRC-REG2-006",
        "canonical_occurrence_ids": [x[0] for x in IDENTITIES],
        "identity_by_occurrence_id": {
            occurrence_id: {
                "reference_period_es": reference_period_es,
                "canonical_release_date": release_date,
                "authoritative_calendar_time": "16:00:00",
                "month_slug": month_slug,
            }
            for occurrence_id, reference_period_es, release_date, month_slug in IDENTITIES
        },
        "request_budget_per_run": 5,
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_completed_release_fetch_allowed": False,
        "automatic_google_fetch_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
    }


def releases() -> list:
    return [release(ref, date, slug) for _oid, ref, date, slug in IDENTITIES]


class INDECCalendarAdapterTests(unittest.TestCase):
    def test_parser_cross_checks_entity_normalized_visible_row_and_embedded_calendar_metadata(self):
        item = release("Agosto de 2026", "2026-09-10", "Septiembre-2026")
        self.assertEqual(item.release_date, "2026-09-10")
        self.assertEqual(item.start_local, "2026-09-10T16:00:00")
        self.assertEqual(item.end_local, "2026-09-10T16:30:00")
        self.assertEqual(item.source_timezone, INDEC_TIMEZONE)
        self.assertEqual(item.reference_period, "Agosto de 2026")
        self.assertEqual(item.visible_time_label, "16:00hs")

    def test_parser_rejects_wrong_timezone(self):
        body = fixture("Agosto de 2026", "2026-09-10", ctz="UTC")
        with self.assertRaises(AdapterError):
            parse_indec_cpi_month(body, month_slug="Septiembre-2026")

    def test_parser_rejects_release_outside_requested_route_month(self):
        body = fixture("Agosto de 2026", "2026-10-10")
        with self.assertRaises(AdapterError):
            parse_indec_cpi_month(body, month_slug="Septiembre-2026")

    def test_parser_rejects_duplicate_cpi_identity(self):
        body = fixture("Agosto de 2026", "2026-09-10") * 2
        with self.assertRaises(AdapterError):
            parse_indec_cpi_month(body, month_slug="Septiembre-2026")

    def test_parser_rejects_visible_time_disagreement(self):
        body = fixture("Agosto de 2026", "2026-09-10").replace("16:00hs", "15:00hs")
        with self.assertRaises(AdapterError):
            parse_indec_cpi_month(body, month_slug="Septiembre-2026")

    def test_robots_empty_disallow_allows_exact_month_routes(self):
        robots="User-agent: *\nDisallow:\n"
        self.assertTrue(indec_routes_allowed(robots, [x[3] for x in IDENTITIES]))

    def test_robots_explicit_calendar_disallow_fails_closed(self):
        robots="User-agent: *\nDisallow: /Calendario/\n"
        self.assertFalse(indec_routes_allowed(robots, [x[3] for x in IDENTITIES]))

    @patch("world_signals.adapters.indec_calendar.fetch_bytes")
    def test_past_month_may_be_absent_from_rolling_calendar(self, mock_fetch):
        body = b'<div class="future-calendar-row">another future release</div>'
        mock_fetch.return_value = (
            body,
            FetchSnapshot(
                url="https://www.indec.gob.ar/Calendario/FiltrosCalendario/mes/Septiembre-2026/0",
                resolved_url="https://www.indec.gob.ar/Calendario/FiltrosCalendario/mes/Septiembre-2026/0",
                status=200,
                content_type="text/html; charset=utf-8",
                body_sha256="fixture",
                body_bytes=len(body),
            ),
        )
        releases_found, snapshots = fetch_indec_cpi_months(
            ["Septiembre-2026"],
            allow_absent_month_slugs={"Septiembre-2026"},
        )
        self.assertEqual(releases_found, [])
        self.assertEqual(len(snapshots), 1)

    @patch("world_signals.adapters.indec_calendar.fetch_bytes")
    def test_future_month_absence_still_fails_closed(self, mock_fetch):
        body = b'<div class="future-calendar-row">another future release</div>'
        mock_fetch.return_value = (
            body,
            FetchSnapshot(
                url="https://www.indec.gob.ar/Calendario/FiltrosCalendario/mes/Octubre-2026/0",
                resolved_url="https://www.indec.gob.ar/Calendario/FiltrosCalendario/mes/Octubre-2026/0",
                status=200,
                content_type="text/html; charset=utf-8",
                body_sha256="fixture",
                body_bytes=len(body),
            ),
        )
        with self.assertRaises(AdapterError):
            fetch_indec_cpi_months(["Octubre-2026"])


class INDECCalendarComparatorTests(unittest.TestCase):
    def test_date_only_canonical_rows_generate_clock_enrichment_review_only(self):
        candidates, observations = indec_cpi_calendar_review_candidates(canonical_records(), releases(), config())
        self.assertEqual(len(candidates), 4)
        self.assertEqual({c["candidate_type"] for c in candidates}, {"INDEC_CPI_CLOCK_ENRICHMENT_REVIEW"})
        self.assertTrue(all(c["automatic_commit_allowed"] is False for c in candidates))
        self.assertTrue(all(c["canonical_clock_mutation_allowed"] is False for c in candidates))
        self.assertTrue(any(o["type"] == "INDEC_CALENDAR_MONITOR_HAS_NO_COMPLETION_CERTAINTY_OR_DIRECT_WRITE_AUTHORITY" for o in observations))

    def test_date_change_is_same_occurrence_review_not_new_identity(self):
        items = releases()
        items[1] = release("Septiembre de 2026", "2026-10-14", "Octubre-2026")
        candidates, _ = indec_cpi_calendar_review_candidates(canonical_records(), items, config())
        target = next(c for c in candidates if c["occurrence_ids"] == ["WSO-REG-B-0009"])
        self.assertEqual(target["candidate_type"], "INDEC_CPI_SCHEDULE_DATE_CHANGE_REVIEW")
        self.assertEqual(target["new_value"]["observed_release_date"], "2026-10-14")
        self.assertEqual(target["event_state_inference"], "NONE")

    def test_missing_report_is_review_evidence_not_cancellation_or_completion(self):
        items = releases()[1:]
        candidates, observations = indec_cpi_calendar_review_candidates(canonical_records(), items, config())
        target = next(c for c in candidates if c["occurrence_ids"] == ["WSO-REG-B-0008"])
        self.assertEqual(target["candidate_type"], "INDEC_CPI_EXPECTED_REPORT_ABSENT_SOURCE_MATCH_REVIEW")
        self.assertTrue(target["absence_is_not_cancellation_delay_completion_or_certainty_change"])
        self.assertTrue(any(o["type"] == "INDEC_CPI_EXPECTED_REPORT_ABSENT_FROM_CONFIGURED_MONTH_ROUTE" for o in observations))

    def test_missing_past_release_in_rolling_calendar_is_observation_only(self):
        items = releases()[1:]
        candidates, observations = indec_cpi_calendar_review_candidates(
            canonical_records(),
            items,
            config(),
            retired_month_slugs={"Septiembre-2026"},
        )
        self.assertFalse(any(c["occurrence_ids"] == ["WSO-REG-B-0008"] for c in candidates))
        retired = next(
            o for o in observations
            if o["type"] == "INDEC_CPI_PAST_RELEASE_REMOVED_FROM_ROLLING_CALENDAR"
        )
        self.assertTrue(retired["absence_is_not_completion_evidence"])
        self.assertEqual(retired["event_state_inference"], "NONE")

    def test_retired_month_must_be_within_configured_scope(self):
        with self.assertRaises(ValueError):
            indec_cpi_calendar_review_candidates(
                canonical_records(),
                releases(),
                config(),
                retired_month_slugs={"Enero-2027"},
            )

    def test_completed_occurrence_does_not_create_schedule_or_clock_action(self):
        rows = canonical_records()
        rows[0]["lifecycle_status"] = "COMPLETED"
        candidates, observations = indec_cpi_calendar_review_candidates(rows, releases(), config())
        self.assertFalse(any(c["occurrence_ids"] == ["WSO-REG-B-0008"] for c in candidates))
        self.assertTrue(any(o["type"] == "INDEC_CPI_COMPLETED_OCCURRENCE_CALENDAR_CORROBORATION_ONLY" for o in observations))

    def test_reviewed_timed_descendant_exact_match_is_observation_only(self):
        rows = canonical_records()
        rows[0].update({
            "time_precision": "MINUTE",
            "timing_type": "TIMED_EVENT",
            "start_local": "2026-09-10T16:00:00",
            "start_utc": "2026-09-10T19:00:00Z",
            "all_day_semantics": False,
        })
        candidates, observations = indec_cpi_calendar_review_candidates(rows, releases(), config())
        self.assertFalse(any(c["occurrence_ids"] == ["WSO-REG-B-0008"] for c in candidates))
        self.assertTrue(any(o["type"] == "INDEC_CPI_CALENDAR_EXACT_MATCH_NO_CHANGE" and o["occurrence_id"] == "WSO-REG-B-0008" for o in observations))

    def test_reviewed_timed_descendant_clock_drift_is_review_only(self):
        rows = canonical_records()
        rows[0].update({
            "time_precision": "MINUTE",
            "timing_type": "TIMED_EVENT",
            "start_local": "2026-09-10T16:00:00",
            "start_utc": "2026-09-10T19:00:00Z",
            "all_day_semantics": False,
        })
        items = releases()
        items[0] = release("Agosto de 2026", "2026-09-10", "Septiembre-2026", time_value="16:30:00")
        candidates, _ = indec_cpi_calendar_review_candidates(rows, items, config())
        target = next(c for c in candidates if c["occurrence_ids"] == ["WSO-REG-B-0008"])
        self.assertEqual(target["candidate_type"], "INDEC_CPI_CLOCK_CHANGE_REVIEW")
        self.assertFalse(target["canonical_clock_mutation_allowed"])

    def test_authority_gate_drift_fails_closed(self):
        bad = config()
        bad["schedule_authority"] = True
        with self.assertRaises(ValueError):
            indec_cpi_calendar_review_candidates(canonical_records(), releases(), bad)

    def test_duplicate_reference_period_fails_closed(self):
        items = releases()
        items.append(items[0])
        with self.assertRaises(ValueError):
            indec_cpi_calendar_review_candidates(canonical_records(), items, config())


if __name__ == "__main__":
    unittest.main()
