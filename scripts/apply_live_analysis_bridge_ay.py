from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import validate_analysis
from world_signals.live_analysis_bridge import (
    production_live_input_count,
    validate_live_analysis_bridge,
)

PLAN_PATH = ROOT / "data/analysis/LIVE_ANALYSIS_BRIDGE_AY_PLAN_v0.1.json"
SCHEMA_PATH = ROOT / "data/analysis/schema.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
VALIDATE_SCRIPT_PATH = ROOT / "scripts/validate_analysis.py"
BUILD_SCRIPT_PATH = ROOT / "scripts/build_site.py"
CI_PATH = ROOT / ".github/workflows/ci.yml"
STATUS_PATH = ROOT / "PROJECT_STATUS.md"
ROADMAP_PATH = ROOT / "ROADMAP.md"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def target_schema(current: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    if target.get("version") == "0.5":
        return target
    require(target.get("version") == "0.4", "AY requires Analysis schema v0.4 prestate")
    target["version"] = "0.5"
    target["reference_date"] = "2026-09-06"
    target["live_input_policy"] = {
        "mode": "FOUNDATION_ONLY_NO_PRODUCTION_LINKS",
        "production_live_inputs_allowed": False,
        "public_live_input_projection_allowed": False,
        "identity_selector": "observation_id",
        "story_id_selector_allowed": False,
        "latest_selector_allowed": False,
        "automatic_story_expansion_allowed": False,
        "transitive_live_evidence_migration_allowed": False,
        "upstream_live_mutation_allowed": False,
        "one_live_observation_may_support_multiple_analyses": True,
        "multiple_story_snapshots_require_explicit_observation_ids": True,
        "analysis_as_of_must_not_predate_live_observed_at": True,
        "future_production_population_requires_pressure_audit": True,
        "required_input_fields": [
            "observation_id",
            "roles",
            "analysis_sections",
        ],
        "allowed_input_fields": [
            "observation_id",
            "roles",
            "analysis_sections",
        ],
        "allowed_roles": [
            "FACTUAL_INPUT",
            "CONTEXT_OR_ALTERNATIVE_INPUT",
            "SECOND_ORDER_INPUT",
            "MARKET_OBSERVATION_INPUT",
        ],
    }
    additions = [
        "A prospective Live Intelligence input is selected by immutable observation_id, never by story_id, latest-state lookup or automatic story expansion.",
        "Live Intelligence inputs remain distinct from Analysis evidence; selecting a Live observation does not transitively migrate its evidence into the analytical evidence registry.",
        "Analysis may not mutate, revise, relabel or otherwise rewrite an upstream Live Intelligence observation through the input relationship.",
        "A developing Live story is consumed snapshot-by-snapshot: analyses requiring multiple states must identify each observation explicitly rather than infer a latest or complete story history.",
        "AY keeps production Live Intelligence inputs and public Live-input projection closed; the schema and validator contract are established before the first populated relationship.",
        "A future production Live Intelligence input requires a separate pressure audit and may not be opened merely because the AY contract validates hypothetical fixtures.",
    ]
    guardrails = list(target.get("guardrails") or [])
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    target["guardrails"] = guardrails
    return target


def target_validate_script(current: str) -> str:
    target = '''from pathlib import Path\nimport sys\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "src"))\n\nfrom world_signals.analysis import validate_analysis\nfrom world_signals.live_analysis_bridge import validate_live_analysis_bridge\nfrom world_signals.io import load_json\n\nschema = load_json(ROOT / "data/analysis/schema.json")\nevidence = load_json(ROOT / "data/analysis/evidence_registry.json")\nreviews = load_json(ROOT / "data/analysis/event_reviews.json")\ncanonical = load_json(ROOT / "data/canonical/registry.json")\nlive_observations = load_json(ROOT / "data/live_intelligence/observations.json")\n\nreport = validate_analysis(schema, evidence, reviews, canonical)\nif not report.ok:\n    for error in report.errors:\n        print(f"ERROR: {error}", file=sys.stderr)\n    raise SystemExit(1)\n\nbridge_report = validate_live_analysis_bridge(schema, reviews, live_observations)\nif not bridge_report.ok:\n    for error in bridge_report.errors:\n        print(f"ERROR: {error}", file=sys.stderr)\n    raise SystemExit(1)\n\nprint(\n    f"Validated {len(reviews.get('reviews', []))} analytical review(s), "\n    f"{len(evidence.get('evidence', []))} evidence record(s), "\n    "and prospective Live Intelligence input bridge: PASS"\n)\n'''
    if "prospective Live Intelligence input bridge: PASS" in current:
        return current
    require(
        "from world_signals.analysis import validate_analysis" in current
        and "report = validate_analysis(schema, evidence, reviews, canonical)" in current,
        "AY validate_analysis.py prestate drift",
    )
    return target


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    require(old in text, f"AY {label} prestate drift")
    return text.replace(old, new, 1)


def target_build_script(current: str) -> str:
    text = current
    text = replace_once(
        text,
        "from world_signals.analysis import public_analysis_projection, validate_analysis\n",
        "from world_signals.analysis import public_analysis_projection, validate_analysis\nfrom world_signals.live_analysis_bridge import validate_live_analysis_bridge\n",
        "build import",
    )
    text = replace_once(
        text,
        "analysis_report=validate_analysis(analysis_schema,analysis_evidence,analysis_reviews,reg)\nif not analysis_report.ok:\n    raise SystemExit(\"Analysis validation failed: \"+\"; \".join(analysis_report.errors))\n",
        "analysis_report=validate_analysis(analysis_schema,analysis_evidence,analysis_reviews,reg)\nif not analysis_report.ok:\n    raise SystemExit(\"Analysis validation failed: \"+\"; \".join(analysis_report.errors))\nbridge_report=validate_live_analysis_bridge(analysis_schema,analysis_reviews,live_observations)\nif not bridge_report.ok:\n    raise SystemExit(\"Live → Analysis bridge validation failed: \"+\"; \".join(bridge_report.errors))\n",
        "build bridge validation",
    )
    return text


def target_ci(current: str) -> str:
    old = "src/world_signals/live_intelligence.py src/world_signals/analysis.py"
    new = "src/world_signals/live_intelligence.py src/world_signals/analysis.py src/world_signals/live_analysis_bridge.py"
    if new in current:
        return current
    require(old in current, "AY CI py_compile prestate drift")
    return current.replace(old, new, 1)


def target_status(current: str) -> str:
    text = current
    text = replace_once(
        text,
        "# CURRENT RECOVERY OVERRIDE — POST-AW / AX EVOLVING-STATE LIVE INTELLIGENCE",
        "# CURRENT RECOVERY OVERRIDE — POST-AX / AY LIVE→ANALYSIS BRIDGE FOUNDATION",
        "PROJECT_STATUS title",
    )
    text = replace_once(
        text,
        "- Analysis schema: **v0.4**",
        "- Analysis schema: **v0.5**",
        "PROJECT_STATUS schema version",
    )
    marker = "## Current architecture decision\n\n"
    ay = (
        "AY establishes a **production-closed prospective Live Intelligence → Analysis input contract**. "
        "Analysis may eventually select immutable Live `observation_id` values as factual inputs, but AY leaves production `live_inputs` at **0**, public Live-input projection closed, and all 20 existing Analysis reviews / 91 evidence rows unchanged. Story IDs, latest-state selectors, automatic story expansion, transitive Live-evidence migration and upstream Live mutation are prohibited. A later pressure audit is required before the first real populated relationship.\n\n"
    )
    if ay not in text:
        require(marker in text, "AY PROJECT_STATUS architecture marker missing")
        text = text.replace(marker, marker + ay, 1)
    return text


def target_roadmap(current: str) -> str:
    old = '''## Stage 8 — prospective Live Intelligence → Analysis linkage — LATER\n\nOnce the Live Intelligence contract survives a real specimen, test whether Analysis can reference factual Live observations without copying them into analytical evidence or allowing Analysis to rewrite upstream observations.\n\nThe target relationship is:\n\n`factual observation -> optional canonical context -> analytical interpretation`\n\nnot:\n\n`headline -> inferred cause -> rewritten event`.\n'''
    new = '''## Stage 8 — prospective Live Intelligence → Analysis linkage — AY FOUNDATION DONE / PRODUCTION CLOSED\n\nAY establishes the executable bridge contract without populating a production relationship. Analysis may prospectively select immutable Live `observation_id` values as factual inputs while keeping those inputs distinct from Analysis evidence and prohibiting any rewrite of upstream Live records.\n\nThe target relationship remains:\n\n`factual observation -> optional canonical context -> analytical interpretation`\n\nnot:\n\n`headline -> inferred cause -> rewritten event`.\n\nAY admits no story selector, latest-state lookup or automatic story expansion: a developing story must be referenced snapshot-by-snapshot. Production `live_inputs` remain exactly zero and public Live-input projection remains closed. A later pressure audit must select and authorise the first real production relationship.\n'''
    if new in current:
        return current
    require(old in current, "AY ROADMAP Stage 8 prestate drift")
    return current.replace(old, new, 1)


def assert_preconditions(plan: dict[str, Any]) -> None:
    pre = plan["preconditions"]
    schema = load(SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    canonical = load(CANONICAL_PATH)

    require(schema.get("version") in {pre["analysis_schema_version"], "0.5"}, "AY Analysis schema version mismatch")
    require(reviews.get("version") == pre["analysis_reviews_version"], "AY Analysis reviews version mismatch")
    require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "AY Analysis review count mismatch")
    require(evidence.get("version") == pre["analysis_evidence_version"], "AY Analysis evidence version mismatch")
    require(len(evidence.get("evidence", [])) == pre["analysis_evidence_count"], "AY Analysis evidence count mismatch")
    require(live_schema.get("version") == pre["live_schema_version"], "AY Live schema version mismatch")
    require(len(live_observations.get("observations", [])) == pre["live_observation_count"], "AY Live observation count mismatch")
    require(len(live_evidence.get("evidence", [])) == pre["live_evidence_count"], "AY Live evidence count mismatch")
    require(canonical.get("version") == pre["canonical_registry_version"], "AY Canonical version mismatch")
    require(len(canonical.get("records", [])) == pre["canonical_occurrence_count"], "AY Canonical count mismatch")
    require(production_live_input_count(reviews) == 0, "AY requires zero production Live inputs")

    exact_count = sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )
    require(exact_count == pre["production_exact_timestamp_series_count"], "AY exact-series precondition mismatch")


def target_texts() -> dict[Path, str]:
    return {
        VALIDATE_SCRIPT_PATH: target_validate_script(VALIDATE_SCRIPT_PATH.read_text(encoding="utf-8")),
        BUILD_SCRIPT_PATH: target_build_script(BUILD_SCRIPT_PATH.read_text(encoding="utf-8")),
        CI_PATH: target_ci(CI_PATH.read_text(encoding="utf-8")),
        STATUS_PATH: target_status(STATUS_PATH.read_text(encoding="utf-8")),
        ROADMAP_PATH: target_roadmap(ROADMAP_PATH.read_text(encoding="utf-8")),
    }


def validate_target(schema: dict[str, Any]) -> None:
    reviews = load(REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    canonical = load(CANONICAL_PATH)
    analysis_report = validate_analysis(schema, evidence, reviews, canonical)
    require(analysis_report.ok, "AY target core Analysis validation failed: " + "; ".join(analysis_report.errors))
    bridge_report = validate_live_analysis_bridge(schema, reviews, live_observations)
    require(bridge_report.ok, "AY target bridge validation failed: " + "; ".join(bridge_report.errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the reviewed AY target")
    parser.add_argument("--check-only", action="store_true", help="simulate and validate without writes")
    args = parser.parse_args()
    require(args.apply != args.check_only, "choose exactly one of --apply or --check-only")

    plan = load(PLAN_PATH)
    assert_preconditions(plan)
    protected = [ROOT / path for path in plan["protected_paths"]]
    before = {path: stable_hash(path) for path in protected}

    schema = load(SCHEMA_PATH)
    target = target_schema(schema)
    texts = target_texts()
    validate_target(target)

    if args.apply:
        SCHEMA_PATH.write_text(json.dumps(target, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for path, content in texts.items():
            path.write_text(content, encoding="utf-8")

    after = {path: stable_hash(path) for path in protected}
    require(before == after, "AY protected dataset hash changed")

    print(
        "AY target validated: Analysis schema v0.5; "
        "20 reviews / 91 evidence unchanged; Live 3 / 4 unchanged; "
        "production live_inputs=0; public Live-input projection closed"
    )


if __name__ == "__main__":
    main()
