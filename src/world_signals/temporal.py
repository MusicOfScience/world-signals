from __future__ import annotations

import re
from dataclasses import dataclass, field

MONTH_TOKEN_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
SEASON_TIMING_TYPES = {
    "MONTH_BOUNDED_SEASON_WINDOW",
    "MULTI_PHASE_SEASON_WINDOW",
}
SEASON_WINDOW_MODELS = {
    "MONTH_BOUNDED_SEASON_WINDOW": "MONTH_BOUNDED_SINGLE_PHASE",
    "MULTI_PHASE_SEASON_WINDOW": "MONTH_BOUNDED_MULTI_PHASE",
}
NATIVE_CALENDAR_TIMING_TYPE = "SOURCE_NATIVE_CALENDAR_DATE"
EXACT_TIMING_FIELDS = (
    "start_local",
    "end_local",
    "start_utc",
    "end_utc",
    "date_earliest",
    "date_latest",
    "publication_datetime",
)


@dataclass
class TemporalValidation:
    errors: list[str] = field(default_factory=list)


def month_ordinal(token: str) -> int:
    match = MONTH_TOKEN_RE.fullmatch(str(token or ""))
    if not match:
        raise ValueError(f"invalid month token: {token!r}")
    year = int(match.group(1))
    month = int(match.group(2))
    return year * 12 + month - 1


def validate_source_native_calendar_date(record: dict) -> TemporalValidation:
    """Validate an authoritative date that is exact only in the source calendar.

    The object deliberately carries no Gregorian civil date until a competent
    source supplies an authoritative mapping.  It can therefore be canonical
    and CONFIRMED without being schedulable in the Gregorian calendar layer.
    """
    result = TemporalValidation()
    if record.get("timing_type") != NATIVE_CALENDAR_TIMING_TYPE:
        return result

    oid = record.get("occurrence_id", "<missing>")
    required_text = (
        "native_calendar_system",
        "native_calendar_month",
        "source_native_date_label",
    )
    for field_name in required_text:
        if not str(record.get(field_name) or "").strip():
            result.errors.append(f"{oid}: source-native calendar date requires {field_name}")

    native_year = record.get("native_calendar_year")
    if not isinstance(native_year, int) or native_year <= 0:
        result.errors.append(f"{oid}: source-native calendar date requires positive integer native_calendar_year")
    native_day = record.get("native_calendar_day")
    if not isinstance(native_day, int) or not 1 <= native_day <= 31:
        result.errors.append(f"{oid}: source-native calendar date requires native_calendar_day in 1..31")

    if record.get("gregorian_resolution_status") != "UNRESOLVED_AUTHORITATIVE_CONVERSION":
        result.errors.append(
            f"{oid}: SOURCE_NATIVE_CALENDAR_DATE requires gregorian_resolution_status=UNRESOLVED_AUTHORITATIVE_CONVERSION"
        )
    if record.get("publication_time_semantics") != "SOURCE_NATIVE_DATE_ONLY":
        result.errors.append(
            f"{oid}: SOURCE_NATIVE_CALENDAR_DATE requires publication_time_semantics=SOURCE_NATIVE_DATE_ONLY"
        )
    if record.get("time_precision") != "DAY":
        result.errors.append(f"{oid}: SOURCE_NATIVE_CALENDAR_DATE requires time_precision=DAY")
    if record.get("time_status") not in (None, "NOT_APPLICABLE"):
        result.errors.append(f"{oid}: SOURCE_NATIVE_CALENDAR_DATE requires time_status=NOT_APPLICABLE")
    if record.get("time_basis") not in (None, "NOT_APPLICABLE"):
        result.errors.append(f"{oid}: SOURCE_NATIVE_CALENDAR_DATE requires time_basis=NOT_APPLICABLE")

    for field_name in EXACT_TIMING_FIELDS:
        if record.get(field_name) not in (None, ""):
            result.errors.append(
                f"{oid}: unresolved source-native calendar date must not populate Gregorian timing field {field_name}"
            )
    return result


def validate_season_window(record: dict) -> TemporalValidation:
    """Validate source-native month-bounded season semantics.

    Month tokens are year-qualified YYYY-MM values. They are deliberately not
    converted to civil-day boundaries in canonical state.
    """
    result = TemporalValidation()
    timing_type = record.get("timing_type")
    if timing_type not in SEASON_TIMING_TYPES:
        return result

    oid = record.get("occurrence_id", "<missing>")
    phases = record.get("season_phases")
    expected_model = SEASON_WINDOW_MODELS[timing_type]
    if record.get("season_window_model") != expected_model:
        result.errors.append(
            f"{oid}: {timing_type} requires season_window_model={expected_model}"
        )
    if record.get("publication_time_semantics") != "SEASONAL_MONTH_RANGE":
        result.errors.append(
            f"{oid}: month-bounded season requires publication_time_semantics=SEASONAL_MONTH_RANGE"
        )

    if not isinstance(phases, list) or not phases:
        result.errors.append(f"{oid}: {timing_type} requires non-empty season_phases")
        return result

    if timing_type == "MONTH_BOUNDED_SEASON_WINDOW" and len(phases) != 1:
        result.errors.append(f"{oid}: MONTH_BOUNDED_SEASON_WINDOW requires exactly one phase")
    if timing_type == "MULTI_PHASE_SEASON_WINDOW" and len(phases) < 2:
        result.errors.append(f"{oid}: MULTI_PHASE_SEASON_WINDOW requires at least two phases")

    if record.get("time_precision") != "MONTH":
        result.errors.append(f"{oid}: month-bounded season requires time_precision=MONTH")
    if record.get("time_status") not in (None, "NOT_APPLICABLE"):
        result.errors.append(f"{oid}: month-bounded season requires time_status=NOT_APPLICABLE")
    if record.get("time_basis") not in (None, "NOT_APPLICABLE"):
        result.errors.append(f"{oid}: month-bounded season requires time_basis=NOT_APPLICABLE")

    for field_name in EXACT_TIMING_FIELDS:
        if record.get(field_name) not in (None, ""):
            result.errors.append(
                f"{oid}: month-bounded season must not populate exact/day timing field {field_name}"
            )

    phase_ids: set[str] = set()
    previous_end: int | None = None
    for index, phase in enumerate(phases, start=1):
        if not isinstance(phase, dict):
            result.errors.append(f"{oid}: season phase {index} must be an object")
            continue
        phase_id = str(phase.get("phase_id") or "")
        if not phase_id:
            result.errors.append(f"{oid}: season phase {index} requires phase_id")
        elif phase_id in phase_ids:
            result.errors.append(f"{oid}: duplicate season phase_id {phase_id}")
        phase_ids.add(phase_id)

        start = phase.get("start_month")
        end = phase.get("end_month")
        try:
            start_ord = month_ordinal(start)
            end_ord = month_ordinal(end)
        except ValueError:
            result.errors.append(
                f"{oid}: season phase {index} requires YYYY-MM start_month and end_month"
            )
            continue
        if end_ord < start_ord:
            result.errors.append(f"{oid}: season phase {index} ends before it starts")
        if phase.get("boundary_precision") != "MONTH":
            result.errors.append(f"{oid}: season phase {index} requires boundary_precision=MONTH")
        if not phase.get("source_label"):
            result.errors.append(f"{oid}: season phase {index} requires source_label")

        if previous_end is not None:
            if start_ord <= previous_end:
                result.errors.append(f"{oid}: season phases overlap or are out of order")
            elif timing_type == "MULTI_PHASE_SEASON_WINDOW" and start_ord == previous_end + 1:
                result.errors.append(
                    f"{oid}: adjacent phases are continuous and must not use MULTI_PHASE_SEASON_WINDOW"
                )
        previous_end = end_ord

    if not record.get("source_native_window_label"):
        result.errors.append(f"{oid}: month-bounded season requires source_native_window_label")

    return result
