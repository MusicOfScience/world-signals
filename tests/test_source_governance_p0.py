from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/apply_source_governance_p0.py"
SPEC = importlib.util.spec_from_file_location("apply_source_governance_p0", MODULE_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MIGRATION)

PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P0_BACKFILL_PLAN_v0.1.json"


class P0GovernanceMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def _synthetic_pre_state(self):
        plan = self.plan
        p = plan["preconditions"]

        sources = []
        for source_id, spec in plan["source_updates"].items():
            row = {"source_id": source_id, "institution": source_id}
            row.update(copy.deepcopy(spec.get("expected") or {}))
            row["monitoring_readiness_status"] = spec["expected"]["monitoring_readiness_status"]
            if source_id == "WSSRC-REG4-001":
                row.update(
                    {
                        "monitoring_priority_score": 230,
                        "live_adapter_id": "COLOMBIA_SUIN_DECREE_111_1996",
                        "live_validation_evidence": {"result": "historical-pass"},
                        "live_validation_reviewed_at": "2026-09-03T04:05:00+10:00",
                        "endpoint_route_validation_state": "PARSER_VALIDATED",
                        "runtime_environment_health_state": "HEALTHY",
                    }
                )
            sources.append(row)

        while len(sources) < p["source_count"]:
            i = len(sources)
            sources.append(
                {
                    "source_id": f"DUMMY-{i:03d}",
                    "institution": f"Dummy {i}",
                    "monitoring_readiness_status": "ENDPOINT_REVIEW_REQUIRED",
                }
            )

        registry_records = [
            {
                "occurrence_id": f"O-{i:03d}",
                "series_id": f"S-{i:03d}",
                "region": "Synthetic",
                "timing_type": "DATE_ONLY",
                "certainty_status": "CONFIRMED",
                "source_id": "WSSRC-REG4-001",
            }
            for i in range(p["canonical_record_count"])
        ]
        canonical = {
            "version": p["canonical_registry_version"],
            "record_count": p["canonical_record_count"],
            "records": registry_records,
        }

        expectations = {
            "version": p["monitor_expectations_version"],
            "automatic_canonical_commit": False,
            "google_calendar_write": False,
            "adapters": [
                {"adapter_id": "RBA_FSR_RSS", "source_id": "WSSRC-FIN-001"},
                {
                    "adapter_id": "COLOMBIA_SUIN_DECREE_111_1996",
                    "source_id": "WSSRC-REG4-001",
                },
                {"adapter_id": "EU_CELLAR_CRA_ARTICLE_71", "source_id": "WSSRC-TECH-001"},
                {"adapter_id": "EU_CBAM_VERIFICATION_RULE", "source_id": "WSSRC-TRD-005"},
                {"adapter_id": "EU_CBAM_CERTIFICATE_SALE_RULE", "source_id": "WSSRC-TRD-005"},
                {"adapter_id": "EU_CBAM_ANNUAL_DEADLINE_RULE", "source_id": "WSSRC-TRD-006"},
            ],
        }
        runtime_text = (
            "before\n"
            + MIGRATION.OLD_RUNTIME_LITERAL
            + "\nmiddle\n"
            + MIGRATION.OLD_RUNTIME_LITERAL
            + "\nafter\n"
        )
        source_registry = {
            "version": p["source_registry_version"],
            "sources": sources,
        }
        return canonical, source_registry, expectations, runtime_text

    def test_script_executes_as_cli_from_repository_root(self):
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--apply", result.stdout)

    def test_plan_splits_colombia_without_reassigning_canonical_source(self):
        plan = self.plan
        self.assertEqual(
            plan["monitor_expectation_update"]["set_source_id"],
            "WSSRC-REG4-002",
        )
        self.assertEqual(
            plan["monitor_expectation_update"]["required_manual_verification_source_ids"],
            ["WSSRC-REG4-001"],
        )
        self.assertEqual(
            plan["source_updates"]["WSSRC-REG4-001"]["strategy"],
            "RETAIN_SOURCE_ID_AND_NARROW_TO_SUIN_OPERATIVE_LEGAL_TEXT",
        )
        self.assertEqual(plan["new_sources"][0]["canonical_dependency_count"], 0)
        self.assertFalse(plan["principles"]["automatic_canonical_commit"])
        self.assertFalse(plan["principles"]["google_calendar_write"])

    def test_runtime_transform_replaces_exactly_two_hardcoded_source_ids(self):
        text = MIGRATION.OLD_RUNTIME_LITERAL + "\n" + MIGRATION.OLD_RUNTIME_LITERAL
        transformed = MIGRATION.transform_runtime_text(text)
        self.assertNotIn(MIGRATION.OLD_RUNTIME_LITERAL, transformed)
        self.assertEqual(transformed.count(MIGRATION.NEW_RUNTIME_LITERAL), 2)

    def test_runtime_transform_fails_closed_on_wrong_count(self):
        with self.assertRaises(ValueError):
            MIGRATION.transform_runtime_text(MIGRATION.OLD_RUNTIME_LITERAL)
        with self.assertRaises(ValueError):
            MIGRATION.transform_runtime_text(
                MIGRATION.OLD_RUNTIME_LITERAL * 3
            )

    def test_check_transaction_keeps_canonical_unchanged_and_hits_exact_post_state(self):
        canonical, sources, expectations, runtime_text = self._synthetic_pre_state()
        canonical_before = copy.deepcopy(canonical)

        MIGRATION.preflight(
            canonical,
            sources,
            expectations,
            runtime_text,
            self.plan,
        )
        new_sources, new_expectations, new_runtime, report = MIGRATION.build_post_state(
            canonical,
            sources,
            expectations,
            runtime_text,
            self.plan,
        )

        self.assertEqual(canonical, canonical_before)
        self.assertEqual(new_sources["version"], "1.52")
        self.assertEqual(len(new_sources["sources"]), 223)
        self.assertEqual(new_expectations["version"], "0.7")
        self.assertEqual(report["configured_monitor_adapter_count"], 6)
        self.assertEqual(
            report["configured_monitor_sources_with_missing_modern_governance"],
            0,
        )
        self.assertTrue(report["automatic_canonical_commit"] is False)
        self.assertTrue(report["google_calendar_write"] is False)
        self.assertEqual(new_runtime.count(MIGRATION.NEW_RUNTIME_LITERAL), 2)

    def test_colombia_live_validation_evidence_moves_to_machine_source(self):
        canonical, sources, expectations, runtime_text = self._synthetic_pre_state()
        new_sources, new_expectations, _, _ = MIGRATION.build_post_state(
            canonical,
            sources,
            expectations,
            runtime_text,
            self.plan,
        )
        by_id = {row["source_id"]: row for row in new_sources["sources"]}
        old = by_id["WSSRC-REG4-001"]
        new = by_id["WSSRC-REG4-002"]

        self.assertNotIn("live_adapter_id", old)
        self.assertEqual(new["live_adapter_id"], "COLOMBIA_SUIN_DECREE_111_1996")
        self.assertEqual(new["live_validation_evidence"]["result"], "historical-pass")
        self.assertEqual(old["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
        self.assertEqual(new["verification_mode"], "AUTOMATED_PILOT")
        self.assertEqual(
            new["required_authoritative_verification_source_ids"],
            ["WSSRC-REG4-001"],
        )
        config = {
            row["adapter_id"]: row for row in new_expectations["adapters"]
        }["COLOMBIA_SUIN_DECREE_111_1996"]
        self.assertEqual(config["source_id"], "WSSRC-REG4-002")
        self.assertEqual(
            config["required_manual_verification_source_ids"],
            ["WSSRC-REG4-001"],
        )


if __name__ == "__main__":
    unittest.main()
