from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.apply_kenya_pfm_readiness_bn as tx
from world_signals.adapters.kenya_law import parse_kenya_budget_policy_rule


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


class KenyaPFMReadinessBNTests(unittest.TestCase):
    def _live_state(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        monitor = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        return canonical, sources, monitor

    def test_bn_is_readiness_only_not_production_activation(self):
        canonical, sources, monitor = self._live_state()
        self.assertEqual((canonical["version"], len(canonical["records"])), ("0.41", 689))
        self.assertGreaterEqual(_version_tuple(monitor["version"]), (0, 12))
        self.assertGreaterEqual(len(monitor["adapters"]), 10)
        if monitor["version"] == "0.12":
            self.assertEqual(len(monitor["adapters"]), 10)
        self.assertFalse(monitor["automatic_canonical_commit"])
        self.assertFalse(monitor["google_calendar_write"])
        self.assertFalse(any(row.get("source_id") == tx.SOURCE_ID for row in monitor["adapters"]))

        if sources["version"] == "1.86":
            post = tx.build_post_state()
        else:
            self.assertGreaterEqual(tuple(map(int, sources["version"].split("."))), (1, 87))
            post = sources

        self.assertGreaterEqual(len(post["sources"]), 247)
        if post["version"] == "1.87":
            self.assertEqual(len(post["sources"]), 247)
        target = next(row for row in post["sources"] if row["source_id"] == tx.SOURCE_ID)
        self.assertEqual(target["parser_version"], "kenya-bps-rule-0.1")
        self.assertEqual(target["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(target["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(target["automated_retrieval_permission"], "ENDPOINT_OPERATIONAL_REVIEW_REQUIRED")
        self.assertEqual(
            target["monitoring_readiness_status"],
            "PILOT_ADAPTER_LIVE_VALIDATED_VARIABLE_RUNTIME_PERMISSION_HOLD",
        )
        self.assertEqual(target["monitoring_activation_status"], "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE")
        self.assertEqual(target["runtime_health_state"], "VARIABLE_GITHUB_ACTIONS_403_200_403_2026_09_08")
        self.assertIn("clears unattended polling", target["automation_summary"])
        self.assertIn("neither HTTP 200 nor public-domain legal content", target["automation_summary"])

    def test_exact_prestate_simulation_changes_only_kenya_source_row(self):
        _, sources, _ = self._live_state()
        if sources["version"] != "1.86":
            self.skipTest("exact BN transform comparison belongs to post-BM source pre-state")
        post = tx.build_post_state()
        self.assertEqual(post["version"], "1.87")
        pre_by_id = {row["source_id"]: row for row in sources["sources"]}
        post_by_id = {row["source_id"]: row for row in post["sources"]}
        self.assertEqual(set(pre_by_id), set(post_by_id))
        changed = [sid for sid in pre_by_id if pre_by_id[sid] != post_by_id[sid]]
        self.assertEqual(changed, [tx.SOURCE_ID])
        for sid in pre_by_id:
            if sid != tx.SOURCE_ID:
                self.assertEqual(post_by_id[sid], pre_by_id[sid], sid)

    def test_canonical_identity_taxonomy_and_temporal_semantics_are_unchanged(self):
        canonical, _, _ = self._live_state()
        deps = [
            row for row in canonical["records"]
            if row.get("source_id") == tx.SOURCE_ID or tx.SOURCE_ID in (row.get("source_ids") or [])
        ]
        self.assertEqual(len(deps), 1)
        row = deps[0]
        self.assertEqual(row["occurrence_id"], tx.OCCURRENCE_ID)
        self.assertEqual(row["series_id"], tx.SERIES_ID)
        self.assertEqual(row["category"], "FISCAL_SOVEREIGN_FINANCE")
        self.assertEqual(row["region"], "Africa")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertEqual(row["lifecycle_status"], "PLANNED")

    def test_rule_hash_tracks_statutory_rule_not_markup(self):
        a = parse_kenya_budget_policy_rule(
            '<html><body><h1>Public Finance Management Act</h1><p>The National Treasury shall submit the Budget Policy Statement approved in terms of subsection (1) to Parliament, by the 15th February in each year.</p></body></html>'
        )
        b = parse_kenya_budget_policy_rule(
            '<html><body><h1>Public Finance Management Act</h1><div>Unrelated amendment note</div><p>The National Treasury shall submit the Budget Policy Statement approved in terms of subsection (1) to Parliament, by the 15th February in each year.</p></body></html>'
        )
        self.assertEqual(a.rule_sha256, b.rule_sha256)
        self.assertEqual(a.rule_sha256, "3121afc21199d121650558d896055e91ab24a6ff01c62a27dfc797baeaaab50c")

    def test_variable_runtime_reachability_never_becomes_permission_or_event_state(self):
        _, sources, _ = self._live_state()
        post = tx.build_post_state() if sources["version"] == "1.86" else sources
        target = next(row for row in post["sources"] if row["source_id"] == tx.SOURCE_ID)
        evidence = target["live_validation_evidence"]
        self.assertEqual(evidence["historical_github_actions_current_route_status_2026_09_03"], 403)
        self.assertEqual(evidence["successful_probe_current_unversioned_http_status"], 200)
        self.assertEqual(evidence["successful_probe_baseline_2025_11_04_http_status"], 200)
        self.assertEqual(
            evidence["successful_probe_baseline_rule_sha256"],
            evidence["successful_probe_current_rule_sha256"],
        )
        self.assertEqual(evidence["subsequent_transaction_baseline_2025_11_04_http_status"], 403)
        self.assertEqual(
            evidence["subsequent_transaction_current_route_status"],
            "NOT_REQUESTED_AFTER_BASELINE_FAILURE",
        )
        self.assertEqual(target["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(target["automated_retrieval_permission"], "ENDPOINT_OPERATIONAL_REVIEW_REQUIRED")
        self.assertEqual(target["monitoring_activation_status"], "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE")


if __name__ == "__main__":
    unittest.main()
