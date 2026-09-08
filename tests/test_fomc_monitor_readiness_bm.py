from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.apply_fomc_monitor_readiness_bm as tx
import scripts.repair_bl_source_ceiling_bm as bl_repair


class FOMCMonitorReadinessBMTests(unittest.TestCase):
    def _live_state(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        monitor = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        return canonical, sources, monitor

    def test_bm_is_readiness_truth_repair_not_production_activation(self):
        canonical, sources, monitor = self._live_state()
        self.assertEqual((canonical["version"], len(canonical["records"])), ("0.41", 689))
        self.assertEqual((monitor["version"], len(monitor["adapters"])), ("0.12", 10))
        self.assertFalse(monitor["automatic_canonical_commit"])
        self.assertFalse(monitor["google_calendar_write"])
        self.assertFalse(any(row.get("source_id") == tx.SOURCE_ID for row in monitor["adapters"]))

        if sources["version"] == "1.85":
            post = tx.build_post_state()
        else:
            self.assertEqual(sources["version"], tx.TARGET_SOURCE_VERSION)
            post = sources

        self.assertEqual(len(post["sources"]), 247)
        target = next(row for row in post["sources"] if row["source_id"] == tx.SOURCE_ID)
        self.assertEqual(target["canonical_dependency_count"], 44)
        self.assertEqual(target["automated_monitoring_use"], "ENDPOINT_REVIEW_REQUIRED")
        self.assertEqual(target["automated_retrieval_permission"], "PENDING_ENDPOINT_OPERATIONAL_REVIEW")
        self.assertEqual(target["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(target["parser_type"], "HTML_FOMC_SCHEDULE_READINESS_ADAPTER")
        self.assertEqual(target["parser_version"], "fomc-schedule-readiness-0.2")
        self.assertEqual(
            target["monitoring_readiness_status"],
            "PILOT_ADAPTER_LIVE_VALIDATED_PERMISSION_HOLD",
        )
        self.assertEqual(
            target["monitoring_activation_status"],
            "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE",
        )
        self.assertIn("reachability", target["automation_summary"].lower())
        self.assertIn("not treated as automated-retrieval permission", target["automation_summary"])

    def test_exact_prestate_simulation_changes_only_fomc_source_row(self):
        _, sources, _ = self._live_state()
        if sources["version"] != "1.85":
            self.skipTest("exact BM transform comparison belongs to post-BL source pre-state")
        post = tx.build_post_state()
        self.assertEqual(post["version"], "1.86")
        self.assertEqual(post["reference_date"], "2026-09-08")
        pre_by_id = {row["source_id"]: row for row in sources["sources"]}
        post_by_id = {row["source_id"]: row for row in post["sources"]}
        self.assertEqual(set(pre_by_id), set(post_by_id))
        changed = [source_id for source_id in pre_by_id if pre_by_id[source_id] != post_by_id[source_id]]
        self.assertEqual(changed, [tx.SOURCE_ID])
        for source_id in pre_by_id:
            if source_id != tx.SOURCE_ID:
                self.assertEqual(post_by_id[source_id], pre_by_id[source_id], source_id)

    def test_fomc_canonical_scope_and_precision_are_unchanged(self):
        canonical, _, _ = self._live_state()
        rows = [row for row in canonical["records"] if row.get("source_id") == tx.SOURCE_ID]
        self.assertEqual(len(rows), 44)
        self.assertEqual({row.get("series_id") for row in rows}, tx.EXPECTED_SERIES)
        self.assertEqual({row.get("source_timezone") for row in rows}, {"America/New_York"})
        self.assertEqual(sum(row.get("time_precision") == "DATE_RANGE" for row in rows), 11)
        self.assertEqual(sum(row.get("time_precision") == "MINUTE" for row in rows), 33)
        self.assertTrue(all(row.get("lifecycle_status") == "PLANNED" for row in rows))

    def test_live_analysis_ledger_and_overlay_populations_do_not_move(self):
        live = json.loads((ROOT / "data/live_intelligence/observations.json").read_text())
        live_evidence = json.loads((ROOT / "data/live_intelligence/evidence_registry.json").read_text())
        analysis = json.loads((ROOT / "data/analysis/event_reviews.json").read_text())
        analysis_evidence = json.loads((ROOT / "data/analysis/evidence_registry.json").read_text())
        ledger = json.loads((ROOT / "data/changes/ledger.json").read_text())
        overlay = json.loads((ROOT / "data/coverage/biosecurity_overlay.json").read_text())
        self.assertEqual((live["version"], len(live["observations"])), ("0.6", 6))
        self.assertEqual(len(live_evidence["evidence"]), 9)
        self.assertEqual((analysis["version"], len(analysis["reviews"])), ("0.17", 21))
        self.assertEqual(len(analysis_evidence["evidence"]), 95)
        self.assertEqual((ledger["version"], len(ledger["changes"])), ("0.27", 62))
        self.assertEqual(overlay["canonical_checkpoint"]["registry_version"], "0.41")
        self.assertEqual(overlay["canonical_checkpoint"]["record_count"], 689)

    def test_bl_descendant_repair_is_narrow_and_idempotent(self):
        original = (ROOT / "tests/test_japan_household_spending_monitor_bl.py").read_text()
        repaired = bl_repair.build_post_text(original)
        self.assertEqual(bl_repair.build_post_text(repaired), repaired)
        if repaired != original:
            self.assertIn("self.assertGreaterEqual(len(post_sources[\"sources\"]), 247)", repaired)
            self.assertIn("tuple(map(int, sources[\"version\"].split(\".\")))", repaired)
            self.assertNotIn('self.assertEqual(sources["version"], "1.85")', repaired)
        self.assertIn("JAPAN_HHSPEND_STATISTICS_DASHBOARD_API", repaired)
        self.assertIn("WSSRC-MAC-030", repaired)
        self.assertIn("WSSRC-MAC-024", repaired)


if __name__ == "__main__":
    unittest.main()
