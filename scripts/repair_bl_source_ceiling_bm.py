from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tests/test_japan_household_spending_monitor_bl.py"
APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BM"

OLD_VERSION_BLOCK = '''        else:\n            self.assertEqual(sources["version"], "1.85")\n            self.assertEqual(expectations["version"], "0.12")\n            post_sources, post_expectations = sources, expectations\n'''
NEW_VERSION_BLOCK = '''        else:\n            self.assertGreaterEqual(\n                tuple(map(int, sources["version"].split("."))), (1, 85)\n            )\n            self.assertGreaterEqual(\n                tuple(map(int, expectations["version"].split("."))), (0, 12)\n            )\n            post_sources, post_expectations = sources, expectations\n'''
OLD_COUNT_BLOCK = '''        self.assertEqual(len(post_sources["sources"]), 247)\n        self.assertEqual(len(post_expectations["adapters"]), 10)\n'''
NEW_COUNT_BLOCK = '''        self.assertGreaterEqual(len(post_sources["sources"]), 247)\n        self.assertGreaterEqual(len(post_expectations["adapters"]), 10)\n'''


def build_post_text(text: str | None = None) -> str:
    original = TARGET.read_text() if text is None else text
    already_repaired = NEW_VERSION_BLOCK in original and NEW_COUNT_BLOCK in original
    if already_repaired:
        if OLD_VERSION_BLOCK in original or OLD_COUNT_BLOCK in original:
            raise RuntimeError("BL descendant repair is in a mixed partial state")
        return original
    if original.count(OLD_VERSION_BLOCK) != 1:
        raise RuntimeError("expected exactly one historical BL version ceiling block")
    if original.count(OLD_COUNT_BLOCK) != 1:
        raise RuntimeError("expected exactly one historical BL population ceiling block")
    repaired = original.replace(OLD_VERSION_BLOCK, NEW_VERSION_BLOCK, 1)
    repaired = repaired.replace(OLD_COUNT_BLOCK, NEW_COUNT_BLOCK, 1)
    return repaired


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair BL historical source/count ceilings for reviewed descendants")
    parser.add_argument("--apply", action="store_true", help="write the repaired historical test harness")
    args = parser.parse_args()
    repaired = build_post_text()
    if not args.apply:
        print("BM BL descendant-safe harness repair check-only PASS")
        return 0
    if os.environ.get(APPLY_ENV) != "1":
        raise RuntimeError(f"refusing write without {APPLY_ENV}=1")
    TARGET.write_text(repaired)
    print("BM BL descendant-safe harness repair applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
