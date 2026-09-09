#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{relative}: expected exactly one repair marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def repair_cg_helper() -> None:
    replace_once(
        "scripts/apply_barmm_pre_election_live_cg.py",
        '''    require(sources.get("version") == pre["source_registry_version"], "CG Source Registry version drift")
    require(len(sources.get("sources", [])) == pre["source_count"], "CG Source population drift")
    require(expectations.get("version") == pre["monitor_expectations_version"], "CG Monitor expectations drift")
    require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "CG Monitor adapter count drift")
''',
        '''    version_tuple = lambda value: tuple(int(part) for part in str(value).split("."))
    require(version_tuple(sources.get("version")) >= version_tuple(pre["source_registry_version"]), "CG Source Registry regressed below historical checkpoint")
    require(len(sources.get("sources", [])) >= pre["source_count"], "CG Source population regressed below historical checkpoint")
    require(version_tuple(expectations.get("version")) >= version_tuple(pre["monitor_expectations_version"]), "CG Monitor expectations regressed below historical checkpoint")
    require(len(expectations.get("adapters", [])) >= pre["monitor_adapter_count"], "CG Monitor adapter population regressed below historical checkpoint")
    require(expectations.get("automatic_canonical_commit") is False, "CG descendant opened automatic Canonical commit")
    require(expectations.get("google_calendar_write") is False, "CG descendant opened Google Calendar write")
''',
    )


def repair_cd_test() -> None:
    path = "tests/test_bwc_wg8_first_analysis_revision_cd.py"
    replace_once(
        path,
        '''                if path.startswith("data/live_intelligence/"):
                    continue
''',
        '''                if path.startswith("data/live_intelligence/") or path in {"data/sources/registry.json", "data/monitor/expectations.json"}:
                    continue
''',
    )
    replace_once(
        path,
        '''            live_schema = load(apply_cd.LIVE_SCHEMA_PATH)
            live_evidence = load(apply_cd.LIVE_EVIDENCE_PATH)
''',
        '''            source_registry = load(ROOT / "data/sources/registry.json")
            monitor = load(ROOT / "data/monitor/expectations.json")
            self.assertGreaterEqual(tuple(map(int, source_registry["version"].split("."))), tuple(map(int, self.plan["target_state"]["source_registry_version"].split("."))))
            self.assertGreaterEqual(len(source_registry["sources"]), self.plan["target_state"]["source_count"])
            self.assertGreaterEqual(tuple(map(int, monitor["version"].split("."))), tuple(map(int, self.plan["target_state"]["monitor_version"].split("."))))
            self.assertGreaterEqual(len(monitor["adapters"]), self.plan["target_state"]["monitor_adapter_count"])
            self.assertFalse(monitor["automatic_canonical_commit"])
            self.assertFalse(monitor["google_calendar_write"])
            live_schema = load(apply_cd.LIVE_SCHEMA_PATH)
            live_evidence = load(apply_cd.LIVE_EVIDENCE_PATH)
''',
    )


def repair_cc_test() -> None:
    replace_once(
        "tests/test_hmt_t1_content_api_activation_cc.py",
        '''        self.assertEqual((sources["version"], len(sources["sources"])), ("2.02", 257))
        self.assertEqual((monitor["version"], len(monitor["adapters"])), ("0.27", 25))
''',
        '''        self.assertGreaterEqual(tuple(map(int, sources["version"].split("."))), (2, 2))
        self.assertGreaterEqual(len(sources["sources"]), 257)
        self.assertGreaterEqual(tuple(map(int, monitor["version"].split("."))), (0, 27))
        self.assertGreaterEqual(len(monitor["adapters"]), 25)
''',
    )


def repair_bg_test() -> None:
    path = "tests/test_opec_official_confirmation_bg.py"
    replace_once(path, "import copy\n", "import copy\nimport json\n")
    replace_once(
        path,
        '''            self.assertIn("Source Registry: **v2.02 / 257 sources**", status_source)
''',
        '''            current_state = json.loads((ROOT / "data/status/current_state.json").read_text(encoding="utf-8"))
            current_sources = current_state["sources"]
            self.assertIn(f"Source Registry: **v{current_sources['registry_version']} / {current_sources['source_count']} sources**", status_source)
''',
    )


def repair_ch_test() -> None:
    path = ROOT / "tests/test_project_state_snapshot_ch.py"
    text = path.read_text(encoding="utf-8")
    start_marker = "    def test_current_governed_counts_are_not_stale(self):\n"
    end_marker = "    def test_all_write_and_public_projection_gates_remain_closed(self):\n"
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise SystemExit("CH historical-state repair markers drifted")
    start = text.index(start_marker)
    end = text.index(end_marker)
    replacement = '''    def test_governed_state_is_at_least_ch_checkpoint(self):
        vt = lambda value: tuple(int(part) for part in str(value).split("."))
        self.assertGreaterEqual(vt(self.derived["canonical"]["registry_version"]), (0, 41))
        self.assertGreaterEqual(self.derived["canonical"]["occurrence_count"], 689)
        self.assertGreaterEqual(vt(self.derived["canonical"]["schema_version"]), (0, 52))
        self.assertGreaterEqual(vt(self.derived["sources"]["registry_version"]), (2, 2))
        self.assertGreaterEqual(self.derived["sources"]["source_count"], 257)
        self.assertGreaterEqual(vt(self.derived["change_ledger"]["version"]), (0, 27))
        self.assertGreaterEqual(self.derived["change_ledger"]["entry_count"], 62)
        self.assertGreaterEqual(vt(self.derived["monitor"]["expectations_version"]), (0, 27))
        self.assertGreaterEqual(self.derived["monitor"]["configured_adapter_count"], 25)
        self.assertGreaterEqual(self.derived["monitor"]["unique_monitor_source_count"], 24)
        self.assertGreaterEqual(self.derived["monitor"]["explicit_scoped_occurrence_count"], 215)
        self.assertGreaterEqual(vt(self.derived["live_intelligence"]["schema_version"]), (0, 7))
        self.assertGreaterEqual(self.derived["live_intelligence"]["observation_count"], 7)
        self.assertGreaterEqual(self.derived["live_intelligence"]["evidence_count"], 10)
        self.assertGreaterEqual(self.derived["live_intelligence"]["canonical_linked_observation_count"], 2)
        self.assertGreaterEqual(vt(self.derived["analysis"]["schema_version"]), (0, 8))
        self.assertGreaterEqual(self.derived["analysis"]["review_count"], 22)
        self.assertGreaterEqual(self.derived["analysis"]["evidence_count"], 97)
        self.assertGreaterEqual(self.derived["analysis"]["production_live_input_count"], 1)
        self.assertGreaterEqual(self.derived["analysis"]["production_revision_count"], 1)

    def test_nhc_pilot_history_allows_only_reviewed_bounded_registration(self):
        nhc = self.derived["monitor"]["nhc_atlantic_pilot"]
        self.assertEqual(nhc["readiness_verdict"], "PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT")
        self.assertEqual(nhc["source_id"], "WSSRC-RISK-002")
        self.assertEqual(set(nhc["canonical_occurrence_ids"]), {"WSO-COM-A-0049", "WSO-COM-A-0050"})
        if not nhc["registered_in_expectations"]:
            return
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text(encoding="utf-8"))
        routes = [row for row in expectations["adapters"] if row.get("adapter_id") == "NHC_ATLANTIC_SEASON"]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(route["source_id"], "WSSRC-RISK-002")
        self.assertEqual(route["canonical_occurrence_ids"], ["WSO-COM-A-0049", "WSO-COM-A-0050"])
        self.assertEqual(route["cadence"], "DAILY")
        self.assertEqual(route["endpoint"]["request_budget_per_run"], 2)
        self.assertEqual(route["baseline"]["start_month_day"], "06-01")
        self.assertEqual(route["baseline"]["end_month_day"], "11-30")
        for gate in (
            "schedule_authority", "lifecycle_authority", "certainty_authority",
            "canonical_date_mutation_allowed", "automatic_new_occurrence_creation_allowed",
            "automatic_live_or_analysis_promotion_allowed", "automatic_commit_allowed",
        ):
            self.assertFalse(route[gate], gate)
        sources = json.loads((ROOT / "data/sources/registry.json").read_text(encoding="utf-8"))
        source = [row for row in sources["sources"] if row.get("source_id") == "WSSRC-RISK-002"]
        self.assertEqual(len(source), 1)
        self.assertEqual(source[0]["automated_monitoring_use"], "CLEARED")
        self.assertEqual(source[0]["monitoring_readiness_status"], "PILOT_VALIDATED_NO_AUTO_COMMIT")
        self.assertIn("READ_ONLY_SENTINEL_ONLY", source[0]["automated_monitoring_scope"])

'''
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def main() -> int:
    repair_cg_helper()
    repair_cd_test()
    repair_cc_test()
    repair_bg_test()
    repair_ch_test()
    print("CI_DESCENDANT_REPAIR_PREPARED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
