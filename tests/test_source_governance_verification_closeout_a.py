from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts import apply_source_governance_verification_closeout_a as closeout
from world_signals.source_governance_audit import build_source_governance_audit


class VerificationCloseoutATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        cls.sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        cls.expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        cls.plan = json.loads((ROOT / "data/coverage/SOURCE_GOVERNANCE_VERIFICATION_CLOSEOUT_A_PLAN_v0.1.json").read_text())

    def test_selection_is_exact_and_vietnam_is_held(self):
        selected = set(self.plan["selection"]["selected_source_ids"])
        self.assertEqual(selected, set(self.plan["source_updates"]))
        self.assertEqual(len(selected), 7)
        self.assertNotIn("WSSRC-REG5-001", selected)
        self.assertEqual(self.plan["selection"]["held_source_ids"], ["WSSRC-REG5-001"])

    def test_canonical_dependency_truth_is_seven_single_dependencies(self):
        counts = Counter(r.get("source_id") for r in self.canonical["records"] if r.get("source_id"))
        for source_id in self.plan["selection"]["selected_source_ids"]:
            self.assertEqual(counts[source_id], 1)
        self.assertEqual(sum(counts[s] for s in self.plan["selection"]["selected_source_ids"]), 7)
        if counts["WSSRC-REG5-002"]:
            self.assertEqual(counts["WSSRC-REG5-001"], 0)
            self.assertEqual(counts["WSSRC-REG5-002"], 1)
        else:
            self.assertEqual(counts["WSSRC-REG5-001"], 1)

    def test_pre_or_post_closeout_state_is_exact(self):
        version = str(self.sources.get("version"))
        if version == self.plan["preconditions"]["source_registry_version"]:
            closeout.preflight(self.canonical, self.sources, self.expectations, self.plan)
            post, report = closeout.build_post_state(self.canonical, self.sources, self.expectations, self.plan)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(str(post["version"]), self.plan["postconditions"]["source_registry_version"])
            self.assertEqual(report["governance_audit"], self.plan["postconditions"]["expected_governance_audit"])
            before = closeout.sources_by_id(self.sources)
            after = closeout.sources_by_id(post)
            self.assertEqual(after["WSSRC-REG5-001"], before["WSSRC-REG5-001"])
            self.assertEqual(after["WSSRC-INT-010"]["canonical_dependency_count"], 1)
        elif tuple(int(p) for p in version.split(".")) >= tuple(int(p) for p in self.plan["postconditions"]["source_registry_version"].split(".")):
            by_id = closeout.sources_by_id(self.sources)
            for source_id, spec in self.plan["source_updates"].items():
                for key, value in spec["set"].items():
                    if (
                        source_id == "WSSRC-REG6-001"
                        and key == "verification_mode"
                        and by_id[source_id].get("monitoring_readiness_status")
                        in {
                            "PILOT_ADAPTER_LIVE_VALIDATED_PERMISSION_HOLD",
                            "PILOT_ADAPTER_LIVE_VALIDATED_VARIABLE_RUNTIME_PERMISSION_HOLD",
                        }
                    ):
                        # Verification Closeout A historically established MANUAL_AUTHORITATIVE_RECHECK.
                        # A later reviewed readiness tranche may advance the technical verification mode,
                        # but only while the separate endpoint-permission and production-route holds survive.
                        self.assertEqual(by_id[source_id].get("verification_mode"), "AUTOMATED_PILOT")
                        self.assertEqual(by_id[source_id].get("automated_monitoring_use"), "ENDPOINT_REVIEW_REQUIRED")
                        self.assertEqual(
                            by_id[source_id].get("automated_retrieval_permission"),
                            "ENDPOINT_OPERATIONAL_REVIEW_REQUIRED",
                        )
                        self.assertEqual(
                            by_id[source_id].get("monitoring_activation_status"),
                            "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE",
                        )
                        if by_id[source_id].get("monitoring_readiness_status") == "PILOT_ADAPTER_LIVE_VALIDATED_VARIABLE_RUNTIME_PERMISSION_HOLD":
                            self.assertEqual(
                                by_id[source_id].get("runtime_health_state"),
                                "VARIABLE_GITHUB_ACTIONS_403_200_403_2026_09_08",
                            )
                        self.assertFalse(
                            any(row.get("source_id") == source_id for row in self.expectations["adapters"])
                        )
                        continue
                    self.assertEqual(by_id[source_id].get(key), value, f"{source_id} {key}")
            vietnam = by_id["WSSRC-REG5-001"]
            self.assertEqual(vietnam.get("authoritative_url"), self.plan["preconditions"]["vietnam_hold"]["expected_authoritative_url"])
            if "WSSRC-REG5-002" in by_id:
                self.assertEqual(vietnam.get("verification_mode"), "MANUAL_AUTHORITATIVE_RECHECK")
                self.assertEqual(by_id["WSSRC-REG5-002"].get("canonical_dependency_count"), 1)
            else:
                self.assertNotIn("verification_mode", vietnam)
            if version == self.plan["postconditions"]["source_registry_version"]:
                self.assertEqual(closeout._audit_metrics(self.canonical, self.sources, self.expectations), self.plan["postconditions"]["expected_governance_audit"])
        else:
            self.fail(f"unexpected source registry version {version}")

    def test_present_dependency_helpers_match_after_simulation_or_transaction(self):
        if str(self.sources.get("version")) == self.plan["preconditions"]["source_registry_version"]:
            candidate, _ = closeout.build_post_state(self.canonical, self.sources, self.expectations, self.plan)
        else:
            candidate = self.sources
        counts = closeout.canonical_counts(self.canonical)
        mismatches = []
        for row in candidate["sources"]:
            if "canonical_dependency_count" in row:
                actual = counts.get(row.get("source_id"), 0)
                if row["canonical_dependency_count"] != actual:
                    mismatches.append((row.get("source_id"), row["canonical_dependency_count"], actual))
        self.assertEqual(mismatches, [])

    def test_audit_keeps_permission_inference_prohibitions(self):
        audit = build_source_governance_audit(self.canonical, self.sources, self.expectations)
        method = audit["methodology"]
        self.assertTrue(method["permission_inference_from_machine_readability_prohibited"])
        self.assertTrue(method["permission_inference_from_public_access_prohibited"])
        self.assertTrue(method["permission_inference_from_official_domain_prohibited"])
        self.assertTrue(method["permission_inference_from_successful_parser_prohibited"])

    def test_helper_cli_help_is_available(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/apply_source_governance_verification_closeout_a.py"), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Verification Closeout A", proc.stdout)


if __name__ == "__main__":
    unittest.main()
