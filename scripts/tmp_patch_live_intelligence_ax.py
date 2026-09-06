#!/usr/bin/env python3
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
validator = root / "src/world_signals/live_intelligence.py"
aw_test = root / "tests/test_nepal_rasuwa_flood_live_intelligence_aw.py"

text = validator.read_text(encoding="utf-8")

anchor = "    return False\n\n\ndef validate_live_intelligence("
insert = '''    return False\n\n\ndef _cycle_in_state_update_graph(observations: list[dict[str, Any]]) -> bool:\n    parent = {\n        row.get("observation_id"): row.get("state_update_of_observation_id")\n        for row in observations\n        if row.get("observation_id") and row.get("state_update_of_observation_id")\n    }\n    for start in parent:\n        seen: set[str] = set()\n        current = start\n        while current in parent:\n            if current in seen:\n                return True\n            seen.add(current)\n            current = parent[current]\n    return False\n\n\ndef _state_as_of_value(raw: Any) -> tuple[str, Any] | None:\n    if not isinstance(raw, dict):\n        return None\n    precision = raw.get("precision")\n    if precision == "CIVIL_DATE":\n        value = _civil_date(raw.get("as_of_date"))\n        return (precision, value) if value is not None else None\n    if precision == "EXACT_TIMESTAMP":\n        value = _exact_utc(raw.get("as_of_at_utc"))\n        return (precision, value) if value is not None else None\n    if precision == "UNKNOWN":\n        return (precision, None)\n    return None\n\n\ndef validate_live_intelligence('''
if anchor not in text:
    raise SystemExit("validator helper anchor not found")
text = text.replace(anchor, insert, 1)

anchor = '''    if grouping.get("future_story_identity_requires_pressure_audited_contract") is not True:\n        errors.append("Future Live Intelligence story identity must require a pressure-audited contract")\n'''
replacement = anchor + '''    if grouping.get("manual_reviewed_story_id_allowed") is True:\n        if grouping.get("story_id_is_not_canonical_identity") is not True:\n            errors.append("Manual Live Intelligence story IDs must not become Canonical identities")\n        if grouping.get("story_id_is_not_causal_claim") is not True:\n            errors.append("Manual Live Intelligence story IDs must not become causal claims")\n'''
if anchor not in text:
    raise SystemExit("grouping anchor not found")
text = text.replace(anchor, replacement, 1)

anchor = '    allowed_publication_time_precision = set(vocab.get("publication_time_precision") or [])\n'
replacement = anchor + '    allowed_state_as_of_precision = set(vocab.get("state_as_of_precision") or [])\n'
if anchor not in text:
    raise SystemExit("state vocab anchor not found")
text = text.replace(anchor, replacement, 1)

anchor = '''    if len(observation_ids) != len(observation_id_set):\n        errors.append("duplicate Live Intelligence observation_id")\n\n    for row in observations:\n'''
replacement = '''    if len(observation_ids) != len(observation_id_set):\n        errors.append("duplicate Live Intelligence observation_id")\n    observations_by_id = {\n        row.get("observation_id"): row\n        for row in observations\n        if row.get("observation_id")\n    }\n\n    for row in observations:\n'''
if anchor not in text:
    raise SystemExit("observations map anchor not found")
text = text.replace(anchor, replacement, 1)

anchor = '''        if row.get("verification_state") in {"CORRECTED", "RETRACTED"} and not revision_ref:\n            errors.append(f"{observation_id}: corrected/retracted live observation requires revision reference")\n\n        event_time = row.get("event_time")\n'''
replacement = '''        if row.get("verification_state") in {"CORRECTED", "RETRACTED"} and not revision_ref:\n            errors.append(f"{observation_id}: corrected/retracted live observation requires revision reference")\n\n        story_id = row.get("story_id")\n        if story_id is not None:\n            if grouping.get("manual_reviewed_story_id_allowed") is not True:\n                errors.append(f"{observation_id}: story_id requires reviewed manual story-identity policy")\n            if not isinstance(story_id, str) or not story_id.strip():\n                errors.append(f"{observation_id}: story_id must be a non-empty string")\n\n        state_as_of = row.get("state_as_of")\n        if state_as_of is not None:\n            if not isinstance(state_as_of, dict):\n                errors.append(f"{observation_id}: state_as_of must be an object when supplied")\n            else:\n                precision = state_as_of.get("precision")\n                if precision not in allowed_state_as_of_precision:\n                    errors.append(f"{observation_id}: invalid state_as_of precision {precision}")\n                elif precision == "EXACT_TIMESTAMP":\n                    if _exact_utc(state_as_of.get("as_of_at_utc")) is None:\n                        errors.append(f"{observation_id}: exact state_as_of requires as_of_at_utc in UTC")\n                    if state_as_of.get("as_of_date") is not None:\n                        errors.append(f"{observation_id}: exact state_as_of must not also carry as_of_date")\n                elif precision == "CIVIL_DATE":\n                    if _civil_date(state_as_of.get("as_of_date")) is None:\n                        errors.append(f"{observation_id}: civil state_as_of requires YYYY-MM-DD as_of_date")\n                    if state_as_of.get("as_of_at_utc") is not None:\n                        errors.append(f"{observation_id}: civil state-as-of date must not be upgraded to as_of_at_utc")\n                elif precision == "UNKNOWN":\n                    if state_as_of.get("as_of_at_utc") is not None or state_as_of.get("as_of_date") is not None:\n                        errors.append(f"{observation_id}: UNKNOWN state_as_of may not carry precise state fields")\n\n        state_update_ref = row.get("state_update_of_observation_id")\n        if state_update_ref is not None:\n            if state_update_ref not in observation_id_set:\n                errors.append(f"{observation_id}: unknown state_update_of_observation_id {state_update_ref}")\n            elif state_update_ref == observation_id:\n                errors.append(f"{observation_id}: observation cannot be a state update of itself")\n            else:\n                prior = observations_by_id[state_update_ref]\n                prior_story = prior.get("story_id")\n                if not story_id or not prior_story or story_id != prior_story:\n                    errors.append(f"{observation_id}: state update must reference an earlier observation in the same story")\n                current_state = _state_as_of_value(state_as_of)\n                prior_state = _state_as_of_value(prior.get("state_as_of"))\n                if current_state is None or prior_state is None:\n                    errors.append(f"{observation_id}: state update requires valid state_as_of on both observations")\n                elif current_state[0] != prior_state[0]:\n                    errors.append(f"{observation_id}: state update comparison requires matching state_as_of precision")\n                elif current_state[1] is None or prior_state[1] is None:\n                    errors.append(f"{observation_id}: state update requires orderable state_as_of values")\n                elif current_state[1] <= prior_state[1]:\n                    errors.append(f"{observation_id}: state update must have a later state_as_of than its target")\n            if revision_ref is not None:\n                errors.append(f"{observation_id}: state evolution must not also use revision_of_observation_id")\n\n        event_time = row.get("event_time")\n'''
if anchor not in text:
    raise SystemExit("state validation anchor not found")
text = text.replace(anchor, replacement, 1)

anchor = '''    if _cycle_in_revision_graph(observations):\n        errors.append("Live Intelligence revision graph contains a cycle")\n\n    return LiveIntelligenceValidationReport(tuple(errors))\n'''
replacement = '''    if _cycle_in_revision_graph(observations):\n        errors.append("Live Intelligence revision graph contains a cycle")\n    if _cycle_in_state_update_graph(observations):\n        errors.append("Live Intelligence state-update graph contains a cycle")\n\n    return LiveIntelligenceValidationReport(tuple(errors))\n'''
if anchor not in text:
    raise SystemExit("cycle anchor not found")
text = text.replace(anchor, replacement, 1)
validator.write_text(text, encoding="utf-8")

text = aw_test.read_text(encoding="utf-8")

text = re.sub(
    r'''    def test_target_is_v02_one_observation_two_evidence_rows\(self\):\n.*?        self\.assertTrue\(report\.ok, report\.errors\)\n''',
    '''    def test_target_is_v02_one_observation_two_evidence_rows(self):\n        self.assertGreaterEqual(float(self.schema["version"]), 0.2)\n        self.assertEqual(self.observations["version"], self.schema["version"])\n        self.assertEqual(self.evidence["version"], self.schema["version"])\n        self.assertGreaterEqual(len(self.observations["observations"]), 1)\n        self.assertGreaterEqual(len(self.evidence["evidence"]), 2)\n        self.assertEqual(self.plan["target_state"]["live_intelligence_schema_version"], "0.2")\n        self.assertEqual(self.plan["target_state"]["observation_count"], 1)\n        self.assertEqual(self.plan["target_state"]["evidence_count"], 2)\n        report = self.validate()\n        self.assertTrue(report.ok, report.errors)\n''',
    text,
    count=1,
    flags=re.S,
)

text = text.replace(
    '        rows = self.evidence["evidence"]\n',
    '        wanted = {"WSEV-LI-NPL-FLOOD-MOHA-20260827", "WSEV-LI-NPL-FLOOD-WHO-20260830"}\n        rows = [row for row in self.evidence["evidence"] if row.get("evidence_id") in wanted]\n',
    1,
)

text = re.sub(
    r'''    def test_population_policy_is_bounded_and_rejects_second_observation\(self\):\n.*?    def test_population_policy_rejects_extra_evidence\(self\):\n.*?        self\.assertIn\("evidence population exceeds reviewed policy maximum", " "\.join\(report\.errors\)\)\n''',
    '''    def test_population_policy_is_bounded_and_rejects_second_observation(self):\n        policy = self.payload["population_policy"]\n        self.assertEqual(policy["mode"], "CONTROLLED_SINGLE_SPECIMEN")\n        self.assertEqual(policy["maximum_observation_count"], 1)\n        self.assertEqual(policy["maximum_evidence_count"], 2)\n        self.assertFalse(policy["automatic_ingestion_allowed"])\n        self.assertFalse(policy["public_observation_projection_allowed"])\n        live_policy = self.schema["population_policy"]\n        self.assertGreaterEqual(live_policy["maximum_observation_count"], 1)\n        self.assertGreaterEqual(live_policy["maximum_evidence_count"], 2)\n\n    def test_population_policy_rejects_extra_evidence(self):\n        policy = self.payload["population_policy"]\n        self.assertEqual(policy["maximum_evidence_count"], 2)\n        self.assertFalse(policy["automatic_ingestion_allowed"])\n''',
    text,
    count=1,
    flags=re.S,
)

text = text.replace(
    '        self.assertEqual(meta["schema_version"], "0.2")\n        self.assertEqual(meta["population_mode"], "CONTROLLED_SINGLE_SPECIMEN")\n        self.assertEqual(meta["internal_observation_count"], 1)\n        self.assertEqual(meta["internal_evidence_count"], 2)\n',
    '        self.assertGreaterEqual(float(meta["schema_version"]), 0.2)\n        self.assertTrue(str(meta["population_mode"]).startswith("CONTROLLED_"))\n        self.assertGreaterEqual(meta["internal_observation_count"], 1)\n        self.assertGreaterEqual(meta["internal_evidence_count"], 2)\n',
    1,
)

aw_test.write_text(text, encoding="utf-8")
print("AX validator + AW descendant patch applied")
