#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one repair target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"repaired {path}")


def canonical_floor_upper(path: str) -> None:
    replace_once(
        path,
        '        self.assertEqual((CANONICAL["version"], len(CANONICAL["records"])), ("0.41", 689))',
        '        self.assertGreaterEqual(tuple(map(int, CANONICAL["version"].split("."))), (0, 41))\n'
        '        self.assertGreaterEqual(len(CANONICAL["records"]), 689)',
    )


def canonical_floor_lower(path: str) -> None:
    replace_once(
        path,
        '        self.assertEqual((canonical["version"], len(canonical["records"])), ("0.41", 689))',
        '        self.assertGreaterEqual(tuple(map(int, canonical["version"].split("."))), (0, 41))\n'
        '        self.assertGreaterEqual(len(canonical["records"]), 689)',
    )


def main() -> int:
    # CG is a historical Live transaction helper. Its target BARMM identity stays
    # exact, but later reviewed Canonical descendants must not make --check fail.
    replace_once(
        "scripts/apply_barmm_pre_election_live_cg.py",
        '    require(canonical.get("version") == pre["canonical_registry_version"], "CG Canonical version drift")\n'
        '    require(len(canonical.get("records", [])) == pre["canonical_record_count"], "CG Canonical population drift")\n'
        '    version_tuple = lambda value: tuple(int(part) for part in str(value).split("."))',
        '    version_tuple = lambda value: tuple(int(part) for part in str(value).split("."))\n'
        '    require(version_tuple(canonical.get("version")) >= version_tuple(pre["canonical_registry_version"]), "CG Canonical version regressed below historical checkpoint")\n'
        '    require(len(canonical.get("records", [])) >= pre["canonical_record_count"], "CG Canonical population regressed below historical checkpoint")',
    )

    for path in (
        "tests/test_bsp_monetary_rss_activation_bs.py",
        "tests/test_cbsl_mpr_rss_activation_bt.py",
        "tests/test_fao_release_calendar_activation_bv.py",
        "tests/test_indec_cpi_calendar_activation_bu.py",
        "tests/test_japan_cpi_schedule_activation_bw.py",
        "tests/test_japan_mof_jgb_rss_activation_br.py",
    ):
        canonical_floor_upper(path)

    for path in (
        "tests/test_fomc_monitor_readiness_bm.py",
        "tests/test_hmt_t1_content_api_activation_cc.py",
        "tests/test_kenya_pfm_readiness_bn.py",
        "tests/test_japan_household_spending_monitor_bl.py",
    ):
        canonical_floor_lower(path)

    replace_once(
        "tests/test_eurostat_monitor_bk.py",
        '        self.assertEqual(canonical["version"], "0.41")\n        self.assertEqual(len(canonical["records"]), 689)',
        '        self.assertGreaterEqual(tuple(map(int, canonical["version"].split("."))), (0, 41))\n'
        '        self.assertGreaterEqual(len(canonical["records"]), 689)',
    )

    replace_once(
        "tests/test_nbs_native_rss_activation_bx.py",
        '        self.assertEqual((CANONICAL.get("version"), len(CANONICAL.get("records", []))), ("0.41", 689))',
        '        self.assertGreaterEqual(tuple(map(int, str(CANONICAL.get("version")).split("."))), (0, 41))\n'
        '        self.assertGreaterEqual(len(CANONICAL.get("records", [])), 689)',
    )

    replace_once(
        "tests/test_sarb_mpc_rss_activation_cb.py",
        "        self.assertEqual((self.c['version'],len(self.c['records'])),('0.41',689))",
        "        self.assertGreaterEqual(version_tuple(self.c['version']), version_tuple('0.41'))\n"
        "        self.assertGreaterEqual(len(self.c['records']), 689)",
    )

    # CI activation remains exact about its NHC route, but a later source-registry
    # descendant is legitimate and must not invalidate the historical activation.
    replace_once(
        "tests/test_nhc_atlantic_season_activation_ci.py",
        '            self.assertEqual((sources["version"], len(sources["sources"])), ("2.03", 257))\n'
        '            self.assertEqual((expectations["version"], len(expectations["adapters"])), ("0.28", 26))',
        '            self.assertGreaterEqual(tuple(map(int, sources["version"].split("."))), (2, 3))\n'
        '            self.assertGreaterEqual(len(sources["sources"]), 257)\n'
        '            self.assertEqual((expectations["version"], len(expectations["adapters"])), ("0.28", 26))',
    )

    # BM's historical boundaries become floors under reviewed descendants. The
    # overlay checkpoint must track current Canonical truth, not stay frozen at BM.
    replace_once(
        "tests/test_fomc_monitor_readiness_bm.py",
        '        self.assertEqual((ledger["version"], len(ledger["changes"])), ("0.27", 62))\n'
        '        self.assertEqual(overlay["canonical_checkpoint"]["registry_version"], "0.41")\n'
        '        self.assertEqual(overlay["canonical_checkpoint"]["record_count"], 689)',
        '        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())\n'
        '        self.assertGreaterEqual(_version_tuple(ledger["version"]), (0, 27))\n'
        '        self.assertGreaterEqual(len(ledger["changes"]), 62)\n'
        '        self.assertEqual(overlay["canonical_checkpoint"]["registry_version"], canonical["version"])\n'
        '        self.assertEqual(overlay["canonical_checkpoint"]["record_count"], len(canonical["records"]))',
    )

    # CD's read-only simulation protects the historical transaction itself. Once
    # CD is materialised, later reviewed Canonical/Ledger descendants are allowed;
    # keep their checkpoint floors while retaining exact hashes for untouched paths.
    replace_once(
        "tests/test_bwc_wg8_first_analysis_revision_cd.py",
        '                if path.startswith("data/live_intelligence/") or path in {"data/sources/registry.json", "data/monitor/expectations.json"}:\n'
        '                    continue\n'
        '                self.assertEqual(',
        '                if path.startswith("data/live_intelligence/") or path in {\n'
        '                    "data/canonical/registry.json",\n'
        '                    "data/sources/registry.json",\n'
        '                    "data/monitor/expectations.json",\n'
        '                    "data/changes/ledger.json",\n'
        '                }:\n'
        '                    continue\n'
        '                self.assertEqual(',
    )
    replace_once(
        "tests/test_bwc_wg8_first_analysis_revision_cd.py",
        '            source_registry = load(ROOT / "data/sources/registry.json")\n'
        '            monitor = load(ROOT / "data/monitor/expectations.json")',
        '            canonical = load(ROOT / "data/canonical/registry.json")\n'
        '            ledger = load(ROOT / "data/changes/ledger.json")\n'
        '            self.assertGreaterEqual(tuple(map(int, canonical["version"].split("."))), (0, 41))\n'
        '            self.assertGreaterEqual(len(canonical["records"]), 689)\n'
        '            self.assertGreaterEqual(tuple(map(int, ledger["version"].split("."))), (0, 27))\n'
        '            self.assertGreaterEqual(len(ledger["changes"]), 62)\n'
        '            source_registry = load(ROOT / "data/sources/registry.json")\n'
        '            monitor = load(ROOT / "data/monitor/expectations.json")',
    )

    # BE's 22/21 values are its historical readiness checkpoint, not a permanent
    # ceiling on later completed Canonical anchors.
    replace_once(
        "tests/test_opec_fallback_completion_be.py",
        '        self.assertEqual(readiness["eligible_completed_occurrence_count"], 22)\n'
        '        self.assertEqual(readiness["reviewed_occurrence_count"], 21)\n'
        '        self.assertEqual(22 - 21, self.plan["postconditions"]["completed_unreviewed_analysis_anchor_count"])',
        '        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 22)\n'
        '        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 21)\n'
        '        self.assertEqual(self.plan["postconditions"]["completed_unreviewed_analysis_anchor_count"], 1)',
    )

    # BG's specific provenance change remains addressable by stable change_id even
    # after later ledger entries are appended. Current recovery prose is derived.
    replace_once(
        "tests/test_opec_official_confirmation_bg.py",
        '        self.assertEqual(len(self.target["ledger"]["changes"]), 62)\n'
        '        change = self.target["ledger"]["changes"][-1]\n'
        '        self.assertEqual(change["change_id"], "WSCHANGE-5c0629586cdf3ce7")',
        '        self.assertGreaterEqual(len(self.target["ledger"]["changes"]), 62)\n'
        '        change = next(row for row in self.target["ledger"]["changes"] if row.get("change_id") == "WSCHANGE-5c0629586cdf3ce7")\n'
        '        self.assertEqual(change["change_id"], "WSCHANGE-5c0629586cdf3ce7")',
    )
    replace_once(
        "tests/test_opec_official_confirmation_bg.py",
        '            self.assertIn("Canonical Registry: **v0.41 / 689 occurrences**", status_source)\n'
        '            current_state = json.loads((ROOT / "data/status/current_state.json").read_text(encoding="utf-8"))\n'
        '            current_sources = current_state["sources"]',
        '            current_state = json.loads((ROOT / "data/status/current_state.json").read_text(encoding="utf-8"))\n'
        '            current_canonical = current_state["canonical"]\n'
        '            self.assertIn(f"Canonical Registry: **v{current_canonical[\'registry_version\']} / {current_canonical[\'occurrence_count\']} occurrences**", status_source)\n'
        '            current_sources = current_state["sources"]',
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
