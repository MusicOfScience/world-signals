from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/apply_ak_descendant_repair_ay.py"
AK_TEST = ROOT / "tests/test_exact_market_measurement_contract_ak.py"

spec = importlib.util.spec_from_file_location("apply_ak_descendant_repair_ay", HELPER)
assert spec and spec.loader
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class AKDescendantRepairAYTests(unittest.TestCase):
    def test_repair_is_narrow_and_preserves_historical_transform_path(self):
        current = AK_TEST.read_text(encoding="utf-8")
        target = helper.target_text(current)
        self.assertIn('if version == (0, 3):', target)
        self.assertIn('transform_schema(cls.production_schema, cls.plan)', target)
        self.assertIn('elif version >= (0, 4):', target)
        self.assertIn('self.assertGreaterEqual(candidate_version, (0, 4))', target)
        self.assertIn('self.assertEqual(self.candidate_schema["version"], "0.4")', target)
        self.assertNotIn('self.assertIn(self.production_schema["version"], {"0.3", "0.4"})', target)

    def test_repair_is_idempotent(self):
        current = AK_TEST.read_text(encoding="utf-8")
        target = helper.target_text(current)
        self.assertEqual(helper.target_text(target), target)


if __name__ == "__main__":
    unittest.main()
