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
