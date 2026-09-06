from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/coverage/IMD_HEATWAVE_OUTLOOK_AT_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
SCRIPT_PATH = ROOT / "scripts/apply_imd_heatwave_outlook_at.py"
CORRECTION_L_PATH = ROOT / "data/coverage/PHYSICAL_RISK_CORRECTION_L_PLAN_v0.1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(value).split("."))


def load_apply_module():
    spec = importlib.util.spec_from_file_location("apply_imd_heatwave_outlook_at", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class IMDHeatwaveOutlookATTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load(PLAN_PATH)
        cls.canonical = load(CANONICAL_PATH)
        cls.schema = load(SCHEMA_PATH)
        cls.sources = load(SOURCES_PATH)
        cls.apply = load_apply_module()

    def live_or_simulated(self):
        pre = self.plan["preconditions"]
        if self.canonical.get("version") == pre["canonical_registry_version"]:
            canonical, sources, coverage = self.apply.build_post_state(self.plan)
            return canonical, sources, coverage
        self.assertGreaterEqual(version_tuple(self.canonical["version"]), version_tuple(self.plan["postconditions"]["canonical_registry_version"]))
        self.assertGreaterEqual(version_tuple(self.sources["version"]), version_tuple(self.plan["postconditions"]["source_registry_version"]))
        coverage = self.apply.build_coverage_audit(self.canonical, self.sources)
        return self.canonical, self.sources, coverage

    def target(self, canonical):
        rows = [row for row in canonical["records"] if row.get("occurrence_id") == "WSO-RISK-A-0002"]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def source(self, sources):
        rows = [row for row in sources["sources"] if row.get("source_id") == "WSSRC-RISK-005"]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_plan_is_frozen_to_exact_post_74_main(self):
        self.assertEqual(self.plan["base_main_sha"], "92bf6cba7506483dd861680924879b1ded0f4ddc")
        self.assertEqual(self.plan["preconditions"]["canonical_registry_version"], "0.37")
        self.assertEqual(self.plan["preconditions"]["canonical_record_count"], 687)
        self.assertEqual(self.plan["preconditions"]["source_registry_version"], "1.79")
        self.assertEqual(self.plan["preconditions"]["source_registry_count"], 242)
        self.assertEqual(self.plan["preconditions"]["canonical_schema_version"], "0.52")

    def test_existing_schema_already_supports_information_catalyst_semantics(self):
        vocab = self.schema["controlled_vocabularies"]
        self.assertIn("SCHEDULED_INFORMATION_CATALYST", vocab["signal_object_class"])
        self.assertIn("DATE_ONLY", vocab["publication_time_semantics"])
        self.assertIn("CIVIL_DATE", vocab["timing_type"])
        decisions = "\n".join(self.schema["design_decisions"])
        self.assertIn("dynamic annual season outlook", decisions)
        self.assertIn("PHYSICAL_RISK_WINDOW", decisions)

    def test_target_is_publication_event_not_heatwave_window(self):
        canonical, _, _ = self.live_or_simulated()
        row = self.target(canonical)
        self.assertEqual(row["category"], "PHYSICAL_CLIMATE_RISK")
        self.assertEqual(row["event_type"], "PHYSICAL_RISK_OUTLOOK_RELEASE")
        self.assertEqual(row["signal_object_class"], "SCHEDULED_INFORMATION_CATALYST")
        self.assertEqual(row["physical_shock_routing"], "NO_SHOCK_IN_THIS_RECORD")
        self.assertEqual(row["timing_type"], "CIVIL_DATE")
        self.assertEqual(row["start_local"], "2026-03-31")
        self.assertEqual(row["reference_period"], "April–June 2026 hot-weather and heatwave outlook; April 2026 rainfall and temperature outlook")
        self.assertIsNone(row["end_local"])
        self.assertIsNone(row["date_earliest"])
        self.assertIsNone(row["date_latest"])

    def test_date_only_semantics_do_not_invent_utc_timestamp(self):
        canonical, _, _ = self.live_or_simulated()
        row = self.target(canonical)
        self.assertEqual(row["source_timezone"], "Asia/Kolkata")
        self.assertEqual(row["time_precision"], "DAY")
        self.assertTrue(row["all_day_semantics"])
        self.assertEqual(row["publication_time_semantics"], "DATE_ONLY")
        self.assertIsNone(row["start_utc"])
        self.assertIsNone(row["end_utc"])
        self.assertIsNone(row["publication_datetime"])

    def test_completion_is_direct_publication_evidence_not_elapsed_date(self):
        canonical, _, _ = self.live_or_simulated()
        row = self.target(canonical)
        self.assertEqual(row["lifecycle_status"], "COMPLETED")
        self.assertEqual(row["status_history"][-1]["lifecycle_status"], "COMPLETED")
        self.assertIn("Dated first-party IMD press release", row["status_history"][-1]["evidence"])
        self.assertEqual(self.plan["safety"]["completion_basis"], "DIRECT_DATED_FIRST_PARTY_PUBLICATION")
        self.assertTrue(self.plan["safety"]["elapsed_date_never_implies_completion"])

    def test_source_is_manual_authoritative_reference_and_automation_held(self):
        _, sources, _ = self.live_or_simulated()
        row = self.source(sources)
        self.assertEqual(row["canonical_provenance_use"], "MANUAL_INFORMATIONAL_REFERENCE_ONLY")
        self.assertEqual(row["automated_monitoring_use"], "PROHIBITED_OR_RIGHTS_HOLD")
        self.assertEqual(row["verification_mode"], "RIGHTS_HELD_MANUAL_ONLY")
        self.assertEqual(row["monitoring_readiness_status"], "RIGHTS_OR_LICENSE_HOLD")
        self.assertIn("RSMC New Delhi copyright terms are not automatically imputed", row["notes"])

    def test_north_indian_ocean_conflict_remains_deferred(self):
        old = load(CORRECTION_L_PATH)
        deferred = old["deferred_candidates"]
        self.assertEqual(len(deferred), 1)
        self.assertEqual(deferred[0]["candidate_id"], "WSFR-RISK-NIO-TC")
        self.assertEqual(deferred[0]["state"], "OFFICIAL_SOURCE_DEFINITION_CONFLICT")
        assertions = {row["assertion"] for row in deferred[0]["assertions"]}
        self.assertTrue(any("April-June" in value for value in assertions))
        self.assertTrue(any("April-May" in value for value in assertions))
        canonical, sources, _ = self.live_or_simulated()
        self.assertFalse(any(row.get("series_id") == "WSER-RISK-NIO-TC" for row in canonical["records"]))
        self.assertFalse(any(row.get("source_id") == "WSSRC-RISK-006" for row in sources["sources"]))

    def test_post_sample_coverage_improves_but_does_not_clear_prompts(self):
        canonical, sources, coverage = self.live_or_simulated()
        if canonical.get("version") == self.plan["postconditions"]["canonical_registry_version"]:
            expected = self.plan["postconditions"]
            for key, value in expected["coverage_totals"].items():
                self.assertEqual(coverage["totals"][key], value)
            south_asia = next(row for row in coverage["by_region"] if row["region"] == "South Asia")
            for key, value in expected["south_asia"].items():
                self.assertEqual(south_asia[key], value)
            physical = next(row for row in coverage["by_category"] if row["category"] == "PHYSICAL_CLIMATE_RISK")
            for key, value in expected["physical_climate_risk"].items():
                self.assertEqual(physical[key], value)
        self.assertIn("South Asia", coverage["diagnostic_flags"]["regions_with_fewer_than_10_unique_series"])
        self.assertIn("South Asia", coverage["diagnostic_flags"]["regions_with_fewer_than_8_unique_institutions"])
        self.assertIn("PHYSICAL_CLIMATE_RISK", coverage["diagnostic_flags"]["categories_with_fewer_than_5_unique_series"])

    def test_no_future_recurrence_is_manufactured(self):
        canonical, _, _ = self.live_or_simulated()
        series_rows = [row for row in canonical["records"] if row.get("series_id") == "WSER-RISK-IN-HEAT-OUTLOOK"]
        if canonical.get("version") == self.plan["postconditions"]["canonical_registry_version"]:
            self.assertEqual(len(series_rows), 1)
        self.assertTrue(any(row.get("occurrence_id") == "WSO-RISK-A-0002" for row in series_rows))
        self.assertFalse(any(str(row.get("start_local") or "").startswith("2027-") for row in series_rows))
        self.assertTrue(self.plan["safety"]["no_future_cadence_inference"])

    def test_analysis_monitor_schema_and_ledger_are_protected(self):
        protected = set(self.plan["mutation_boundary"]["protected_unchanged_paths"])
        self.assertIn("data/canonical/schema.json", protected)
        self.assertIn("data/changes/ledger.json", protected)
        self.assertIn("data/monitor/expectations.json", protected)
        self.assertIn("data/analysis/event_reviews.json", protected)
        self.assertFalse(self.plan["postconditions"]["scheduled_live_monitor_change"])
        self.assertEqual(self.plan["postconditions"]["analysis_review_count"], 19)
        self.assertEqual(self.plan["postconditions"]["production_exact_timestamp_series_rows"], 0)

    def test_check_cli_is_read_only_on_exact_prestate(self):
        if self.canonical.get("version") != self.plan["preconditions"]["canonical_registry_version"]:
            self.skipTest("historical AT read-only transform is exercised only against exact post-#74 prestate")
        before_c = CANONICAL_PATH.read_bytes()
        before_s = SOURCES_PATH.read_bytes()
        result = subprocess.run([sys.executable, str(SCRIPT_PATH), "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(CANONICAL_PATH.read_bytes(), before_c)
        self.assertEqual(SOURCES_PATH.read_bytes(), before_s)
        self.assertIn("READ_ONLY_CHECK", result.stdout)


if __name__ == "__main__":
    unittest.main()
