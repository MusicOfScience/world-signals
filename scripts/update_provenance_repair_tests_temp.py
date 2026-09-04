from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
files = [ROOT / f"tests/test_source_governance_p1{x}.py" for x in "abcdefgh"]

imports = (
    "from provenance_repair_compat import (\n"
    "    assert_brazil_inauguration_compatible,\n"
    "    assert_held_sources_compatible,\n"
    "    assert_source_registry_compatible,\n"
    ")\n"
)

for path in files:
    text = path.read_text(encoding="utf-8")
    if "from provenance_repair_compat import" not in text:
        text = text.replace("import unittest\n", "import unittest\n\n" + imports, 1)

    text = text.replace(
        '        self.assertEqual(len(source_registry.get("sources", [])), 223)\n',
        '        assert_source_registry_compatible(self, source_registry)\n',
    )

    text = text.replace(
        '        held = by_id[HELD]\n'
        '        for field in self.plan["preconditions"]["required_missing_governance_fields"]:\n'
        '            self.assertIn(held.get(field), (None, ""))\n',
        '        assert_held_sources_compatible(\n'
        '            self, source_registry, {HELD},\n'
        '            self.plan["preconditions"]["required_missing_governance_fields"],\n'
        '        )\n',
    )

    text = text.replace(
        '        for held_id in HELD:\n'
        '            for field in self.plan["preconditions"]["required_missing_governance_fields"]:\n'
        '                self.assertIn(by_id[held_id].get(field), (None, ""))\n',
        '        assert_held_sources_compatible(\n'
        '            self, source_registry, HELD,\n'
        '            self.plan["preconditions"]["required_missing_governance_fields"],\n'
        '        )\n',
    )

    pattern = re.compile(
        r"    def (test_brazil_inauguration_guard[^\(]*)\(self\):\n.*?(?=    def test_script_executes_as_cli)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Brazil guard test block not found in {path.name}")
    name = match.group(1)
    replacement = (
        f"    def {name}(self):\n"
        "        assert_brazil_inauguration_compatible(self, self.canonical)\n\n"
    )
    text = pattern.sub(replacement, text, count=1)
    path.write_text(text, encoding="utf-8")

registry = ROOT / "tests/test_registry.py"
text = registry.read_text(encoding="utf-8")
text = text.replace(
    '        self.assertEqual(self.reg["version"],"0.20")\n'
    '        self.assertEqual(self.reg["record_count"],669)\n',
    '        self.assertIn(self.reg["version"], {"0.20", "0.21"})\n'
    '        self.assertEqual(self.reg["record_count"],669)\n'
    '        if self.reg["version"] == "0.21":\n'
    '            row=next(r for r in self.reg["records"] if r["occurrence_id"]=="WSO-EL-A-0004")\n'
    '            self.assertEqual(row["source_id"], "WSSRC-EL-BR-002")\n'
    '            self.assertEqual(row["start_local"], "2027-01-05")\n'
    '            self.assertEqual(row["election_date_basis"], "CONSTITUTIONAL_RULE_DERIVED")\n',
)
registry.write_text(text, encoding="utf-8")
print("patched", len(files), "historical P1 tests plus registry checkpoint test")
