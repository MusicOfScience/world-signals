from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.apply_core_monitor_expansion_o as tx


class CoreMonitorExpansionOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical_path = ROOT / "data/canonical/registry.json"
        cls.sources_path = ROOT / "data/sources/registry.json"
        cls.expectations_path = ROOT / "data/monitor/expectations.json"
        cls.canonical = json.loads(cls.canonical_path.read_text(encoding="utf-8"))
        cls.sources = json.loads(cls.sources_path.read_text(encoding="utf-8"))
        cls.expectations = json.loads(cls.expectations_path.read_text(encoding="utf-8"))

    @staticmethod
    def _version_at_least(value, floor):
        try:
            current = tuple(int(x) for x in str(value).split("."))
            minimum = tuple(int(x) for x in str(floor).split("."))
        except ValueError:
            return False
        width = max(len(current), len(minimum))
        return current + (0,) * (width - len(current)) >= minimum + (0,) * (width - len(minimum))

    def _source(self, source_id: str) -> dict:
        return next(x for x in self.sources["sources"] if x["source_id"] == source_id)

    def test_repository_is_exact_pre_or_reviewed_post_lineage(self):
        state = (
            self.canonical["version"],
            len(self.canonical["records"]),
            self.sources["version"],
            len(self.sources["sources"]),
            self.expectations["version"],
            len(self.expectations["adapters"]),
        )
        exact_pre = state == ("0.28", 674, "1.69", 233, "0.7", 6)
        reviewed_post_or_descendant = (
            self._version_at_least(self.canonical["version"], "0.28")
            and len(self.canonical["records"]) >= 674
            and self._version_at_least(self.sources["version"], "1.70")
            and len(self.sources["sources"]) >= 233
            and self._version_at_least(self.expectations["version"], "0.8")
            and len(self.expectations["adapters"]) >= 7
        )
        self.assertTrue(exact_pre or reviewed_post_or_descendant, state)

    def test_o_tracked_canonical_scope_survives_descendant_population(self):
        self.assertTrue(self._version_at_least(self.canonical["version"], "0.28"))
        self.assertGreaterEqual(len(self.canonical["records"]), 674)
        ons_ids = {
            r["occurrence_id"]
            for r in self.canonical["records"]
            if r.get("source_id") == "WSSRC-MAC-006"
        }
        self.assertEqual(ons_ids, {occurrence_id for occurrence_id, _ in tx.ONS_TRACKED})
        self.assertEqual(len(ons_ids), 19)

    def test_global_write_gates_remain_closed(self):
        self.assertFalse(self.expectations["automatic_canonical_commit"])
        self.assertFalse(self.expectations["google_calendar_write"])
        for adapter in self.expectations["adapters"]:
            self.assertFalse(adapter.get("automatic_commit_allowed", False))

    def test_check_only_transform_is_exact_and_does_not_write(self):
        if self.sources["version"] != "1.69":
            self.skipTest("exact transform simulation is exercised only from pre-state")
        before = {
            "canonical": sha256(self.canonical_path.read_bytes()).hexdigest(),
            "sources": sha256(self.sources_path.read_bytes()).hexdigest(),
            "expectations": sha256(self.expectations_path.read_bytes()).hexdigest(),
        }
        post_sources, post_expectations, post_live, post_smoke = tx.build_post_state()
        after = {
            "canonical": sha256(self.canonical_path.read_bytes()).hexdigest(),
            "sources": sha256(self.sources_path.read_bytes()).hexdigest(),
            "expectations": sha256(self.expectations_path.read_bytes()).hexdigest(),
        }
        self.assertEqual(after, before)
        self.assertEqual(post_sources["version"], "1.70")
        self.assertEqual(len(post_sources["sources"]), 233)
        self.assertEqual(post_expectations["version"], "0.8")
        self.assertEqual(len(post_expectations["adapters"]), 7)
        self.assertIn("ONS_RELEASE_CALENDAR_RSS", post_live)
        self.assertIn("ONS_RELEASE_CALENDAR_RSS", post_smoke)

    def test_ons_post_contract_is_exact(self):
        if self.expectations["version"] == "0.7":
            post_sources, post_expectations, _, _ = tx.build_post_state()
        else:
            post_sources, post_expectations = self.sources, self.expectations
        ons = next(x for x in post_sources["sources"] if x["source_id"] == "WSSRC-MAC-006")
        adapter = next(x for x in post_expectations["adapters"] if x["adapter_id"] == "ONS_RELEASE_CALENDAR_RSS")
        self.assertEqual(ons["automated_monitoring_use"], "CLEARED")
        self.assertEqual(ons["live_adapter_id"], "ONS_RELEASE_CALENDAR_RSS")
        self.assertEqual(ons["monitoring_activation_status"], "LIVE_READ_ONLY_REVIEW_MONITOR_NO_AUTO_COMMIT")
        self.assertEqual(ons["live_validation_evidence"]["research_run_id"], 33969711355)
        self.assertEqual(ons["live_validation_evidence"]["canonical_identity_matches"], 19)
        self.assertEqual(ons["live_validation_evidence"]["datetime_mismatches"], 0)
        self.assertFalse(ons["live_validation_evidence"]["certainty_status_present_in_rss"])
        self.assertEqual(adapter["canonical_occurrence_ids"], [x[0] for x in tx.ONS_TRACKED])
        self.assertEqual(
            adapter["tracked_items"],
            [{"occurrence_id": occurrence_id, "feed_title": title} for occurrence_id, title in tx.ONS_TRACKED],
        )
        self.assertIn("NO_CANCELLATION", adapter["absence_policy"])
        self.assertIn("RSS_HAS_NO_CONFIRMED_PROVISIONAL_FIELD", adapter["certainty_policy"])
        self.assertFalse(adapter["automatic_commit_allowed"])

    def test_eurostat_permission_and_o_endpoint_hold_are_historical_not_descendant_ceiling(self):
        if self.sources["version"] == "1.69":
            post_sources = tx.transform_sources(self.sources)
        else:
            post_sources = self.sources
        eurostat = next(x for x in post_sources["sources"] if x["source_id"] == "WSSRC-MAC-005")
        self.assertEqual(eurostat["automated_monitoring_use"], "CLEARED")

        # O's exact reviewed state must remain provable. A later tranche may supersede
        # the endpoint-identity hold only by adding an explicit reviewed live route.
        if eurostat.get("monitoring_activation_status") == "ENDPOINT_IDENTITY_HOLD_NO_LIVE_ROUTE":
            self.assertEqual(eurostat["monitoring_readiness_status"], "HOLD_GENERATED_ICS_ENDPOINT_REDISCOVERY_REQUIRED")
            endpoint = next(
                e for e in eurostat["monitor_endpoints"]
                if e["url"] == "https://ec.europa.eu/eurostat/en/news/release-calendar"
            )
            self.assertEqual(endpoint["transport"], "HTML")
            self.assertFalse(endpoint["preferred_for_monitoring"])
            self.assertEqual(endpoint["route_validation_state"], "HTML_LANDING_PAGE_NOT_GENERATED_ICS_FEED")
        else:
            self.assertEqual(eurostat.get("monitoring_activation_status"), "LIVE_READ_ONLY_REVIEW_MONITOR_NO_AUTO_COMMIT")
            self.assertEqual(eurostat.get("live_adapter_id"), "EUROSTAT_RELEASE_CALENDAR_ICS")
            self.assertEqual(eurostat.get("monitoring_readiness_status"), "LIVE_VALIDATED_NO_AUTO_COMMIT")
            generated = [
                e for e in eurostat.get("monitor_endpoints", [])
                if e.get("url") == "https://ec.europa.eu/eurostat/o/calendars/eventsIcal?theme=0&category=0"
            ]
            self.assertEqual(len(generated), 1)
            self.assertTrue(generated[0]["preferred_for_monitoring"])
            self.assertEqual(generated[0]["semantic_format"], "RFC5545_VCALENDAR")

    def test_eurostat_was_not_silently_added_at_o_but_reviewed_descendant_may_activate_it(self):
        adapter_ids = {x["adapter_id"] for x in self.expectations["adapters"]}
        if self.expectations["version"] == "0.7":
            post = tx.transform_expectations(self.expectations)
            adapter_ids = {x["adapter_id"] for x in post["adapters"]}
            self.assertNotIn("EUROSTAT_RELEASE_CALENDAR_ICS", adapter_ids)
        else:
            self.assertIn("ONS_RELEASE_CALENDAR_RSS", adapter_ids)
            if "EUROSTAT_RELEASE_CALENDAR_ICS" in adapter_ids:
                eurostat = next(x for x in self.expectations["adapters"] if x["adapter_id"] == "EUROSTAT_RELEASE_CALENDAR_ICS")
                self.assertEqual(eurostat["source_id"], "WSSRC-MAC-005")
                self.assertFalse(eurostat["automatic_commit_allowed"])

    def test_research_preserves_monitor_layer_boundary(self):
        text = (ROOT / "data/monitor/CORE_MONITOR_EXPANSION_O_RESEARCH_v0.1.md").read_text(encoding="utf-8")
        self.assertIn("review candidates only", text.lower())
        self.assertIn("does not improve geographic coverage", text)
        self.assertIn("permission", text.lower())
        self.assertIn("operational endpoint readiness", text.lower())


if __name__ == "__main__":
    unittest.main()
