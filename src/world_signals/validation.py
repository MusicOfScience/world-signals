from __future__ import annotations
from dataclasses import dataclass, field

from .temporal import validate_season_window, validate_source_native_calendar_date

TIMED_TYPES = {"LOCAL_DATETIME", "LOCAL_DATETIME_RANGE", "TIMED_EVENT"}

@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    @property
    def ok(self) -> bool:
        return not self.errors

def validate_registry(registry: dict, source_registry: dict | None = None) -> ValidationReport:
    report = ValidationReport()
    records = registry.get("records", [])
    if registry.get("record_count") != len(records):
        report.errors.append(f"record_count={registry.get('record_count')} but records={len(records)}")

    ids = [r.get("occurrence_id") for r in records]
    if len(ids) != len(set(ids)):
        report.errors.append("duplicate occurrence_id detected")

    source_ids = set()
    if source_registry:
        source_ids = {s.get("source_id") for s in source_registry.get("sources", [])}

    for r in records:
        oid = r.get("occurrence_id", "<missing>")
        if not r.get("series_id"):
            report.errors.append(f"{oid}: missing series_id")
        if isinstance(r.get("region"), list):
            report.errors.append(f"{oid}: region must be scalar, not list")
        if r.get("timing_type") in TIMED_TYPES:
            if not r.get("source_timezone"):
                report.errors.append(f"{oid}: timed event missing source_timezone")
            if not r.get("start_utc"):
                report.warnings.append(f"{oid}: timed event missing start_utc (legacy/backfill candidate)")

        for temporal_report in (
            validate_season_window(r),
            validate_source_native_calendar_date(r),
        ):
            report.errors.extend(temporal_report.errors)

        sid = r.get("source_id")
        if source_registry and sid and sid not in source_ids:
            report.errors.append(f"{oid}: source_id {sid} absent from source registry")
        if r.get("certainty_status") not in {"CONFIRMED", "PROVISIONAL", "TBC", "EXPECTED_WINDOW"}:
            report.warnings.append(f"{oid}: unrecognised certainty_status {r.get('certainty_status')}")
    return report
