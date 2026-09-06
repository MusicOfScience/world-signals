from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AK_TEST_PATH = ROOT / "tests/test_exact_market_measurement_contract_ak.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


OLD_SETUP = '''        if cls.production_schema.get("version") == "0.3":
            cls.candidate_schema = transform_schema(cls.production_schema, cls.plan)
            cls.candidate_source = transform_analysis_source(source)
        elif cls.production_schema.get("version") == "0.4":
            cls.candidate_schema = copy.deepcopy(cls.production_schema)
            cls.candidate_source = source
        else:
            raise AssertionError(f"unexpected Analysis schema version {cls.production_schema.get('version')}")
'''

NEW_SETUP = '''        version = tuple(int(part) for part in cls.production_schema.get("version", "").split("."))
        if version == (0, 3):
            cls.candidate_schema = transform_schema(cls.production_schema, cls.plan)
            cls.candidate_source = transform_analysis_source(source)
        elif version >= (0, 4):
            # AK freezes the historical v0.3 -> v0.4 contract transition, not a
            # permanent ceiling on legitimate later Analysis schema descendants.
            cls.candidate_schema = copy.deepcopy(cls.production_schema)
            cls.candidate_source = source
        else:
            raise AssertionError(f"unexpected Analysis schema version {cls.production_schema.get('version')}")
'''

OLD_TEST = '''    def test_candidate_schema_is_v04_without_populating_exact_rows(self) -> None:
        self.assertIn(self.production_schema["version"], {"0.3", "0.4"})
        self.assertEqual(self.candidate_schema["version"], "0.4")
        self.assertIn("MARKET_DATA_RIGHTS", self.candidate_schema["controlled_vocabularies"]["evidence_role"])
'''

NEW_TEST = '''    def test_candidate_schema_preserves_ak_contract_on_live_descendant(self) -> None:
        production_version = tuple(int(part) for part in self.production_schema["version"].split("."))
        candidate_version = tuple(int(part) for part in self.candidate_schema["version"].split("."))
        self.assertGreaterEqual(production_version, (0, 3))
        self.assertGreaterEqual(candidate_version, (0, 4))
        if production_version == (0, 3):
            self.assertEqual(self.candidate_schema["version"], "0.4")
        else:
            self.assertEqual(self.candidate_schema["version"], self.production_schema["version"])
        self.assertIn("MARKET_DATA_RIGHTS", self.candidate_schema["controlled_vocabularies"]["evidence_role"])
'''


def target_text(current: str) -> str:
    text = current
    if NEW_SETUP not in text:
        require(OLD_SETUP in text, "AY AK descendant repair setup prestate drift")
        text = text.replace(OLD_SETUP, NEW_SETUP, 1)
    if NEW_TEST not in text:
        require(OLD_TEST in text, "AY AK descendant repair assertion prestate drift")
        text = text.replace(OLD_TEST, NEW_TEST, 1)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    require(args.apply != args.check_only, "choose exactly one of --apply or --check-only")

    current = AK_TEST_PATH.read_text(encoding="utf-8")
    target = target_text(current)
    require(target != current or NEW_SETUP in current, "AY AK repair produced no reviewed target")

    if args.apply:
        AK_TEST_PATH.write_text(target, encoding="utf-8")

    print(
        "AY AK descendant repair validated: historical v0.3->v0.4 path frozen; "
        "live descendants v0.4+ exercise unchanged AK exact-market invariants"
    )


if __name__ == "__main__":
    main()
