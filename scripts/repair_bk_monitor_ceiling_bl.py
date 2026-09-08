from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tests/test_eurostat_monitor_bk.py"
APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BL"

OLD = '''        else:\n            self.assertEqual(sources["version"], "1.84")\n            self.assertEqual(expectations["version"], "0.11")\n            post_sources, post_expectations = sources, expectations\n            live = (ROOT / "scripts/run_live_monitor.py").read_text()\n            smoke = (ROOT / "scripts/run_adapter_smoke.py").read_text()\n            adapter_init = (ROOT / "src/world_signals/adapters/__init__.py").read_text()\n\n        self.assertEqual(len(post_sources["sources"]), 246)\n        self.assertEqual(len(post_expectations["adapters"]), 9)\n'''

NEW = '''        else:\n            # BK freezes its own Eurostat contribution, not a permanent ceiling on\n            # later independently reviewed source or monitor growth.\n            def dotted(value: str) -> tuple[int, ...]:\n                return tuple(int(part) for part in value.split("."))\n\n            self.assertGreaterEqual(dotted(sources["version"]), dotted("1.84"))\n            self.assertGreaterEqual(dotted(expectations["version"]), dotted("0.11"))\n            post_sources, post_expectations = sources, expectations\n            live = (ROOT / "scripts/run_live_monitor.py").read_text()\n            smoke = (ROOT / "scripts/run_adapter_smoke.py").read_text()\n            adapter_init = (ROOT / "src/world_signals/adapters/__init__.py").read_text()\n\n        self.assertGreaterEqual(len(post_sources["sources"]), 246)\n        self.assertGreaterEqual(len(post_expectations["adapters"]), 9)\n'''


def transformed(text: str) -> str:
    if NEW in text:
        return text
    count = text.count(OLD)
    if count != 1:
        raise RuntimeError(f"expected exactly one stale BK descendant ceiling, found {count}")
    result = text.replace(OLD, NEW, 1)
    # Substantive BK invariants must remain in the test after the repair.
    required = (
        'eurostat["automated_monitoring_use"], "CLEARED"',
        'eurostat["live_adapter_id"], "EUROSTAT_RELEASE_CALENDAR_ICS"',
        'self.assertFalse(adapter["automatic_commit_allowed"])',
        'self.assertFalse(post_expectations["automatic_canonical_commit"])',
        'self.assertFalse(post_expectations["google_calendar_write"])',
        'self.assertEqual(canonical["version"], "0.41")',
        'self.assertEqual(len(canonical["records"]), 689)',
    )
    for marker in required:
        if marker not in result:
            raise RuntimeError(f"BK substantive invariant missing after repair: {marker}")
    return result


def check() -> None:
    text = TARGET.read_text(encoding="utf-8")
    result = transformed(text)
    if result == text:
        print("BK monitor ceiling already descendant-safe")
    else:
        print("BK monitor ceiling descendant-safe repair: CHECK PASS")


def apply() -> None:
    if os.getenv(APPLY_ENV) != "1":
        raise SystemExit(f"refusing BL test repair: set {APPLY_ENV}=1")
    text = TARGET.read_text(encoding="utf-8")
    result = transformed(text)
    TARGET.write_text(result, encoding="utf-8")
    print("BK monitor ceiling descendant-safe repair applied")


def main() -> int:
    parser = argparse.ArgumentParser(description="Narrow BL repair for stale BK descendant count ceilings")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    apply() if args.apply else check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
