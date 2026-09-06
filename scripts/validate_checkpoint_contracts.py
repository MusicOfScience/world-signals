from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import apply_analysis_revision_contract_ba as apply_ba
import apply_japan_fies_live_analysis_az as apply_az


@dataclass
class ContractValidationResult:
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _run(label: str, callback, errors: list[str]) -> None:
    try:
        callback()
    except (AssertionError, KeyError, TypeError, ValueError, SystemExit) as exc:
        errors.append(f"{label}: {exc}")


def validate_current_checkpoint_descendants() -> ContractValidationResult:
    """Re-run materialised BA and AZ helpers as read-only descendant checks."""

    result = ContractValidationResult()

    def ba() -> None:
        plan = apply_ba.load(apply_ba.PLAN_PATH)
        apply_ba.assert_preconditions(plan)
        target = apply_ba.simulate()
        apply_ba.assert_target(plan, target)

    def az() -> None:
        plan = apply_az.load(apply_az.PLAN_PATH)
        payload = apply_az.load(apply_az.PAYLOAD_PATH)
        apply_az.assert_preconditions(plan)
        target = apply_az.simulate(plan, payload)
        apply_az.assert_target(plan, target)

    _run("BA descendant contract", ba, result.errors)
    _run("AZ descendant contract", az, result.errors)
    return result


def main() -> None:
    result = validate_current_checkpoint_descendants()
    if not result.ok:
        for error in result.errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("Checkpoint descendant contracts: PASS")


if __name__ == "__main__":
    main()
