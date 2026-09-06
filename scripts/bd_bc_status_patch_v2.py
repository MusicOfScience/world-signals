from pathlib import Path


def replace_block(lines, start_text, end_text, replacement):
    starts = [i for i, line in enumerate(lines) if line.rstrip("\n") == start_text]
    if len(starts) != 1:
        raise SystemExit(f"expected one start {start_text!r}; found {len(starts)}")
    start = starts[0]
    end = None
    for i in range(start + 1, len(lines)):
        if lines[i].rstrip("\n") == end_text:
            end = i
            break
    if end is None:
        raise SystemExit(f"missing end {end_text!r}")
    return lines[:start] + [line + "\n" for line in replacement] + lines[end + 1:]


def replace_method(lines, method_name, replacement):
    starts = [i for i, line in enumerate(lines) if line.startswith(f"    def {method_name}(")]
    if len(starts) != 1:
        raise SystemExit(f"expected one method {method_name}; found {len(starts)}")
    start = starts[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("    def ") or lines[i].startswith("if __name__"):
            end = i
            break
    block = [line + "\n" for line in replacement] + ["\n"]
    return lines[:start] + block + lines[end:]


def write(path, lines):
    path.write_text("".join(lines), encoding="utf-8")


# BA target_status: exact historical transform remains; arbitrary later recovery override is documentation only.
p = Path("scripts/apply_analysis_revision_contract_ba.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
lines = replace_block(
    lines,
    "    if old_header not in current and new_header not in current:",
    "        return current",
    [
        "    if old_header not in current and new_header not in current:",
        "        # Later recovery overrides are mutable documentation, not governed BA state.",
        "        # BA descendant truth is enforced by Analysis schema/revision-policy invariants.",
        "        return current",
    ],
)
# BA assert_target: keep historical BA status assertion only when validating the BA-native recovery override.
lines = replace_block(
    lines,
    "    docs = validate_descendant_checkpoint(",
    "    require(docs.ok, \"BA target documentation drift: \" + \"; \".join(docs.errors))",
    [
        "    required_doc_markers = {",
        "        \"BA roadmap\": (target[\"roadmap\"], [\"BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot.\"]),",
        "    }",
        "    if target[\"status\"].startswith(\"# CURRENT RECOVERY OVERRIDE — POST-AZ / BA ANALYSIS REVISION FOUNDATION\"):",
        "        required_doc_markers[\"BA status\"] = (",
        "            target[\"status\"],",
        "            [\"BA adds a **production-closed Analysis revision-lineage contract**\"],",
        "        )",
        "    docs = validate_descendant_checkpoint(required_markers=required_doc_markers)",
        "    require(docs.ok, \"BA target documentation drift: \" + \"; \".join(docs.errors))",
    ],
)
write(p, lines)

# AZ target_status: exact AY->AZ transform remains; later current status is not a governed invariant.
p = Path("scripts/apply_japan_fies_live_analysis_az.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
lines = replace_block(
    lines,
    "    if ay_title not in current:",
    "        return current",
    [
        "    if ay_title not in current:",
        "        # Later recovery overrides are mutable documentation, not governed AZ state.",
        "        # AZ descendant truth is enforced by inaugural Live/Analysis identities and bridge invariants.",
        "        return current",
    ],
)
write(p, lines)

# BA historical regression: later status may omit historical BA prose.
p = Path("tests/test_analysis_revision_contract_ba.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
lines = replace_method(
    lines,
    "test_status_helper_preserves_later_descendant_only_with_frozen_ba_invariants",
    [
        "    def test_status_helper_preserves_later_descendant_without_recovery_prose_coupling(self):",
        "        current = apply_ba.STATUS_PATH.read_text(encoding=\"utf-8\")",
        "        first_header = current.splitlines()[0]",
        "        descendant_header = \"# CURRENT RECOVERY OVERRIDE — POST-BA / BB SYNTHETIC DESCENDANT\"",
        "        descendant = current.replace(first_header, descendant_header, 1).replace(",
        "            \"BA adds a **production-closed Analysis revision-lineage contract**\",",
        "            \"Later recovery override intentionally omits the historical BA paragraph\",",
        "            1,",
        "        )",
        "        self.assertEqual(apply_ba.target_status(descendant), descendant)",
    ],
)
write(p, lines)

# AZ historical regression: same rule.
p = Path("tests/test_japan_fies_live_analysis_az.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
lines = replace_method(
    lines,
    "test_status_helper_preserves_later_descendants_only_with_az_invariants",
    [
        "    def test_status_helper_preserves_later_descendant_without_recovery_prose_coupling(self):",
        "        current = apply_az.STATUS_PATH.read_text(encoding=\"utf-8\")",
        "        first_header = current.splitlines()[0]",
        "        descendant_header = \"# CURRENT RECOVERY OVERRIDE — POST-BA / BB SYNTHETIC DESCENDANT\"",
        "        descendant = current.replace(first_header, descendant_header, 1).replace(",
        "            \"AZ exercises the first **production Live Intelligence → Analysis relationship**\",",
        "            \"Later recovery override intentionally omits the historical AZ paragraph\",",
        "            1,",
        "        )",
        "        self.assertEqual(apply_az.target_status(descendant), descendant)",
    ],
)
write(p, lines)

# BC regressions explicitly encode the documentation/governed-state distinction.
p = Path("tests/test_checkpoint_contract_bc.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
lines = replace_method(
    lines,
    "test_ba_status_descendant_is_keyed_to_architecture_marker_not_zero_revision_ceiling",
    [
        "    def test_ba_status_descendant_is_not_keyed_to_historical_recovery_prose(self):",
        "        current = apply_ba.STATUS_PATH.read_text(encoding=\"utf-8\")",
        "        future = current.replace(",
        "            \"- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**\",",
        "            \"- production Analysis revisions: **1 / reviewed maximum 1 / public revision metadata projection CLOSED**\",",
        "            1,",
        "        ).replace(",
        "            \"BA adds a **production-closed Analysis revision-lineage contract**\",",
        "            \"Later recovery override intentionally omits BA historical prose\",",
        "            1,",
        "        )",
        "        self.assertEqual(apply_ba.target_status(future), future)",
    ],
)
lines = replace_method(
    lines,
    "test_az_status_descendant_preserves_first_relationship_without_freezing_cap",
    [
        "    def test_az_status_descendant_is_not_keyed_to_historical_recovery_prose(self):",
        "        current = apply_az.STATUS_PATH.read_text(encoding=\"utf-8\")",
        "        future = current.replace(",
        "            \"- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**\",",
        "            \"- production `live_inputs`: **2 / reviewed maximum 2 / public projection CLOSED**\",",
        "            1,",
        "        ).replace(",
        "            \"AZ exercises the first **production Live Intelligence → Analysis relationship**\",",
        "            \"Later recovery override intentionally omits AZ historical prose\",",
        "            1,",
        "        )",
        "        self.assertEqual(apply_az.target_status(future), future)",
    ],
)
write(p, lines)

print("BD BC status-descendant patch v2 applied")
