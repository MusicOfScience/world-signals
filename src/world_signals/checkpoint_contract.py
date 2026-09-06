from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


@dataclass
class CheckpointContractReport:
    """Validation result for a historical-checkpoint descendant contract."""

    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def numeric_version(raw: Any) -> tuple[int, ...]:
    """Parse WORLD SIGNALS dotted numeric versions without float semantics.

    `0.10` must compare after `0.9`, so versions are integer tuples rather than
    decimal numbers. Empty, boolean and non-numeric versions are rejected.
    """

    if isinstance(raw, bool) or raw is None:
        raise ValueError(f"invalid numeric version {raw!r}")
    text = str(raw).strip()
    if not text:
        raise ValueError("numeric version is empty")
    parts = text.split(".")
    if any(not part.isdigit() for part in parts):
        raise ValueError(f"invalid numeric version {raw!r}")
    return tuple(int(part) for part in parts)


def version_at_least(actual: Any, floor: Any) -> bool:
    try:
        return numeric_version(actual) >= numeric_version(floor)
    except ValueError:
        return False


def validate_descendant_checkpoint(
    *,
    versions_at_least: Mapping[str, tuple[Any, Any]] | None = None,
    counts_at_least: Mapping[str, tuple[Any, int]] | None = None,
    exact_values: Mapping[str, tuple[Any, Any]] | None = None,
    required_markers: Mapping[str, tuple[str, Iterable[str]]] | None = None,
) -> CheckpointContractReport:
    """Validate only invariants owned by a materialised historical tranche.

    Historical apply helpers may require an exact prestate *before* their target
    exists. Once that target is materialised, later reviewed descendants are
    allowed to grow. Descendant validation therefore uses version/count floors
    plus genuinely immutable values or textual markers, rather than replaying
    unrelated historical registry ceilings.
    """

    report = CheckpointContractReport()

    for label, pair in (versions_at_least or {}).items():
        actual, floor = pair
        try:
            actual_version = numeric_version(actual)
            floor_version = numeric_version(floor)
        except ValueError as exc:
            report.errors.append(f"{label}: {exc}")
            continue
        if actual_version < floor_version:
            report.errors.append(
                f"{label}: version {actual!r} is below historical floor {floor!r}"
            )

    for label, pair in (counts_at_least or {}).items():
        actual, floor = pair
        if isinstance(actual, bool) or not isinstance(actual, int):
            report.errors.append(f"{label}: count {actual!r} is not an integer")
            continue
        if actual < floor:
            report.errors.append(
                f"{label}: count {actual} is below historical floor {floor}"
            )

    for label, pair in (exact_values or {}).items():
        actual, expected = pair
        if actual != expected:
            report.errors.append(
                f"{label}: immutable value {actual!r} != expected {expected!r}"
            )

    for label, pair in (required_markers or {}).items():
        text, markers = pair
        for marker in markers:
            if marker not in text:
                report.errors.append(f"{label}: missing required marker {marker!r}")

    return report
