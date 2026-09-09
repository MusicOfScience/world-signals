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


def repair_apply_helper() -> None:
    path = "scripts/apply_nhc_atlantic_season_monitor_ci.py"
    replace_once(
        path,
        'RUNNER = ROOT / "scripts/run_live_monitor.py"\nROADMAP = ROOT / "ROADMAP.md"\n',
        'RUNNER = ROOT / "scripts/run_live_monitor.py"\nADAPTER_EXPORTS = ROOT / "src/world_signals/adapters/__init__.py"\nROADMAP = ROOT / "ROADMAP.md"\n',
    )
    replace_once(
        path,
        '\ndef patch_runner(text: str) -> str:\n',
        '''\ndef patch_adapter_exports(text: str) -> str:
    if "from .nhc_atlantic_season import (" in text:
        raise RuntimeError("NHC adapter export surface already present")
    marker = "from .nass_asb_ical import (\\n"
    if text.count(marker) != 1:
        raise RuntimeError("NHC adapter export insertion marker drift")
    block = ''' + '"""' + '''from .nhc_atlantic_season import (
    NHC_ATLANTIC_OUTLOOK_RSS_URL,
    NHC_CLIMATOLOGY_URL,
    NHC_ROBOTS_URL,
    NHC_RIGHTS_URL,
    NHCAtlanticSeasonDefinition,
    fetch_nhc_atlantic_climatology,
    fetch_nhc_atlantic_outlook_health,
    parse_nhc_atlantic_climatology_html,
    validate_nhc_rss_xml,
)
''' + '"""' + '''
    return text.replace(marker, block + marker, 1)


def patch_runner(text: str) -> str:
''',
    )
    replace_once(
        path,
        '    roadmap_text = ROADMAP.read_text(encoding="utf-8")\n    assert_prestate(canonical, sources, expectations)\n',
        '    roadmap_text = ROADMAP.read_text(encoding="utf-8")\n    adapter_exports_text = ADAPTER_EXPORTS.read_text(encoding="utf-8")\n    new_adapter_exports = patch_adapter_exports(adapter_exports_text)\n    assert_prestate(canonical, sources, expectations)\n',
    )
    replace_once(
        path,
        '    RUNNER.write_text(new_runner, encoding="utf-8")\n    ROADMAP.write_text(new_roadmap, encoding="utf-8")\n',
        '    RUNNER.write_text(new_runner, encoding="utf-8")\n    ADAPTER_EXPORTS.write_text(new_adapter_exports, encoding="utf-8")\n    ROADMAP.write_text(new_roadmap, encoding="utf-8")\n',
    )


def repair_activation_test() -> None:
    path = "tests/test_nhc_atlantic_season_activation_ci.py"
    replace_once(
        path,
        '    ADAPTER_ID,\n    CANONICAL,\n',
        '    ADAPTER_EXPORTS,\n    ADAPTER_ID,\n    CANONICAL,\n',
    )
    replace_once(
        path,
        '    assert_prestate,\n    build_poststate,\n',
        '    assert_prestate,\n    build_poststate,\n    patch_adapter_exports,\n',
    )
    marker = '''    def test_runtime_wiring_is_present_in_simulated_or_poststate(self):
'''
    new_test = '''    def test_adapter_package_exports_nhc_fetchers_in_simulated_or_poststate(self):
        exports = ADAPTER_EXPORTS.read_text(encoding="utf-8")
        if "from .nhc_atlantic_season import (" not in exports:
            exports = patch_adapter_exports(exports)
        self.assertIn("fetch_nhc_atlantic_climatology", exports)
        self.assertIn("fetch_nhc_atlantic_outlook_health", exports)
        self.assertIn("NHC_CLIMATOLOGY_URL", exports)
        self.assertIn("NHC_ATLANTIC_OUTLOOK_RSS_URL", exports)

''' + marker
    replace_once(path, marker, new_test)


def main() -> int:
    repair_apply_helper()
    repair_activation_test()
    print("CI_NHC_EXPORT_REPAIR_PREPARED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
