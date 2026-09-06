from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/coverage/IMD_HEATWAVE_OUTLOOK_AT_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
SCRIPT_PATH = ROOT / "scripts/apply_imd_heatwave_outlook_at_transaction.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


def load_module():
    spec = importlib.util.spec_from_file_location("apply_imd_heatwave_outlook_at_transaction", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class IMDHeatwaveOutlookATOverlayRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN_PATH)
        cls.canonical = load(CANONICAL_PATH)
        cls.sources = load(SOURCES_PATH)
        cls.overlay = load(OVERLAY_PATH)
        cls.txn = load_module()

    def live_or_simulated(self):
        pre = self.plan["preconditions"]
        post = self.plan["postconditions"]
        if (
            self.canonical.get("version") == pre["canonical_registry_version"]
            and self.overlay.get("version") == pre["biosecurity_overlay_version"]
        ):
            return self.txn.build_post_bundle(self.plan)
        self.assertGreaterEqual(version_tuple(self.canonical["version"]), version_tuple(post["canonical_registry_version"]))
        self.assertGreaterEqual(version_tuple(self.overlay["version"]), version_tuple(post["biosecurity_overlay_version"]))
        coverage = self.txn.build_coverage_audit(self.canonical, self.sources)
        return self.canonical, self.sources, self.overlay, coverage

    def test_repair_is_checkpoint_alignment_not_overlay_semantic_population(self):
        repair = self.plan["transaction_architecture_repair"]
        self.assertEqual(repair["trigger"], "FIRST_CONTROLLED_WRITE_FAILED_CLOSED_IN_FULL_REPOSITORY_SUITE")
        self.assertIn("Canonical checkpoint", repair["finding"])
        self.assertTrue(self.plan["safety"]["biosecurity_overlay_semantics_unchanged"])
        self.assertTrue(self.plan["safety"]["biosecurity_overlay_checkpoint_tracks_canonical"])

    def test_mutation_boundary_now_includes_overlay_checkpoint(self):
        boundary = self.plan["mutation_boundary"]
        self.assertIn("data/coverage/biosecurity_overlay.json", boundary["controlled_write_paths"])
        self.assertNotIn("data/coverage/biosecurity_overlay.json", boundary["protected_unchanged_paths"])
        self.assertEqual(boundary["overlay_allowed_change"], "VERSION_AND_CANONICAL_CHECKPOINT_ONLY")

    def test_simulated_or_live_overlay_tracks_canonical_exactly(self):
        canonical, _, overlay, _ = self.live_or_simulated()
        self.assertEqual(
            overlay["canonical_checkpoint"],
            {"registry_version": canonical["version"], "record_count": canonical["record_count"]},
        )
        if canonical["version"] == self.plan["postconditions"]["canonical_registry_version"]:
            self.assertEqual(overlay["version"], "0.13")
            self.assertEqual(overlay["canonical_checkpoint"], {"registry_version": "0.38", "record_count": 688})

    def test_overlay_semantics_are_identical_across_at_transition(self):
        pre = self.plan["preconditions"]
        if self.canonical.get("version") != pre["canonical_registry_version"]:
            self.skipTest("exact AT semantic diff belongs to post-#74 pre-state simulation")
        before = copy.deepcopy(self.overlay)
        _, _, after, _ = self.txn.build_post_bundle(self.plan)
        self.assertEqual(self.txn.overlay_semantics(before), self.txn.overlay_semantics(after))
        self.assertNotEqual(before["version"], after["version"])
        self.assertNotEqual(before["canonical_checkpoint"], after["canonical_checkpoint"])

    def test_imd_series_is_not_added_to_biosecurity_memberships(self):
        _, _, overlay, _ = self.live_or_simulated()
        memberships = {row.get("series_id") for row in overlay.get("canonical_series_memberships", [])}
        self.assertNotIn("WSER-RISK-IN-HEAT-OUTLOOK", memberships)

    def test_read_only_wrapper_check_is_non_mutating_on_exact_prestate(self):
        pre = self.plan["preconditions"]
        if self.canonical.get("version") != pre["canonical_registry_version"]:
            self.skipTest("read-only wrapper check belongs to exact post-#74 pre-state")
        before = {
            CANONICAL_PATH: CANONICAL_PATH.read_bytes(),
            SOURCES_PATH: SOURCES_PATH.read_bytes(),
            OVERLAY_PATH: OVERLAY_PATH.read_bytes(),
        }
        result = self.txn.run_check()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["overlay_post"], ["0.13", {"registry_version": "0.38", "record_count": 688}])
        for path, payload in before.items():
            self.assertEqual(path.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
