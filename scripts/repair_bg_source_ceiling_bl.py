from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tests/test_opec_official_confirmation_bg.py"
APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BL"

OLD = '''    def test_target_is_exactly_one_provenance_change_with_no_population_growth(self):\n        self.assertEqual(len(self.target["canonical"]["records"]), 689)\n        self.assertEqual(len(self.target["sources"]["sources"]), 246)\n        self.assertEqual(len(self.target["ledger"]["changes"]), 62)\n        change = self.target["ledger"]["changes"][-1]\n'''

NEW = '''    def test_target_is_exactly_one_provenance_change_with_no_population_growth(self):\n        self.assertEqual(len(self.target["canonical"]["records"]), 689)\n        # BG itself added no source population: its frozen plan/postcondition remains\n        # exactly 246. Reviewed descendants may independently add later sources.\n        if self.target["sources"]["version"] == "1.83":\n            self.assertEqual(len(self.target["sources"]["sources"]), 246)\n        else:\n            self.assertGreaterEqual(_version_tuple(self.target["sources"]["version"]), (1, 83))\n            self.assertGreaterEqual(len(self.target["sources"]["sources"]), 246)\n        self.assertEqual(len(self.target["ledger"]["changes"]), 62)\n        change = self.target["ledger"]["changes"][-1]\n'''

REQUIRED = (
    'self.assertEqual(self.plan["postconditions"]["source_record_count"], 246)',
    'self.assertEqual(row["lifecycle_status"], "COMPLETED")',
    'self.assertIsNotNone(bg.related(row, bg.REUTERS_ID))',
    'self.assertIsNotNone(bg.related(row, bg.SPA_ID))',
    '"REQUIRED_WHEN_RETRIEVABLE"',
    'self.assertEqual(matches, [])',
    'self.assertIsNone(row["start_utc"])',
    'self.assertEqual(row["timing_type"], "CIVIL_DATE")',
)


def transformed(text: str) -> str:
    if NEW in text:
        result = text
    else:
        count = text.count(OLD)
        if count != 1:
            raise RuntimeError(f"expected exactly one stale BG source-count ceiling, found {count}")
        result = text.replace(OLD, NEW, 1)
    for marker in REQUIRED:
        if marker not in result:
            raise RuntimeError(f"BG substantive invariant missing after repair: {marker}")
    return result


def check() -> None:
    text = TARGET.read_text(encoding="utf-8")
    result = transformed(text)
    if result == text:
        print("BG source-count ceiling already descendant-safe")
    else:
        print("BG source-count descendant-safe repair: CHECK PASS")


def apply() -> None:
    if os.getenv(APPLY_ENV) != "1":
        raise SystemExit(f"refusing BL BG test repair: set {APPLY_ENV}=1")
    text = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(transformed(text), encoding="utf-8")
    print("BG source-count descendant-safe repair applied")


def main() -> int:
    parser = argparse.ArgumentParser(description="Narrow BL repair for stale BG source-count descendant ceiling")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    apply() if args.apply else check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
