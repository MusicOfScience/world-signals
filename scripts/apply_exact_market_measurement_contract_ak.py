#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import analysis_population_readiness, validate_analysis

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_IMPL_PATH = ROOT / "src/world_signals/analysis.py"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
PLAN_PATH = ROOT / "data/analysis/EXACT_MARKET_MEASUREMENT_CONTRACT_AK_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/analysis/EXACT_MARKET_MEASUREMENT_CONTRACT_AK_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_EXACT_MARKET_CONTRACT_AK"

PROTECTED = {
    "canonical registry": CANONICAL_PATH,
    "canonical schema": CANONICAL_SCHEMA_PATH,
    "source registry": SOURCES_PATH,
    "change ledger": LEDGER_PATH,
    "biosecurity overlay": OVERLAY_PATH,
    "monitor expectations": EXPECTATIONS_PATH,
    "monitor operations policy": OPERATIONS_PATH,
    "Analysis reviews": REVIEWS_PATH,
    "Analysis evidence": EVIDENCE_PATH,
}

EXACT_FIELDS = (
    "market_series_id",
    "market_timezone",
    "series_granularity",
    "event_anchor_utc",
    "before_observation_utc",
    "after_observation_utc",
    "data_use_basis",
    "data_use_evidence_ref",
    "public_projection_permitted",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
    ).strip()


def protected_hashes() -> dict[str, str]:
    return {label: sha256(path) for label, path in PROTECTED.items()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def exact_timestamp_series_rows(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for movement in (review.get("what_moved") or [])
        if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
    )


def market_movement_rows(reviews: dict[str, Any]) -> int:
    return sum(
        1
        for review in reviews.get("reviews", [])
        for _movement in (review.get("what_moved") or [])
    )


def assert_pre(
    plan: dict[str, Any],
    canonical: dict[str, Any],
    sources: dict[str, Any],
    ledger: dict[str, Any],
    overlay: dict[str, Any],
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    pre = plan["preconditions"]
    require(
        (canonical.get("version"), len(canonical.get("records", []))) ==
        (pre["canonical_registry_version"], pre["canonical_record_count"]),
        "AK canonical pre-state mismatch",
    )
    require(
        (sources.get("version"), len(sources.get("sources", []))) ==
        (pre["source_registry_version"], pre["source_record_count"]),
        "AK source pre-state mismatch",
    )
    require(
        (ledger.get("version"), len(ledger.get("changes", []))) ==
        (pre["change_ledger_version"], pre["change_ledger_count"]),
        "AK ledger pre-state mismatch",
    )
    require(
        (overlay.get("version"), overlay.get("canonical_checkpoint")) ==
        (pre["biosecurity_overlay_version"], pre["biosecurity_overlay_checkpoint"]),
        "AK overlay pre-state mismatch",
    )
    require(schema.get("version") == pre["analysis_schema_version"], "AK Analysis schema pre-state mismatch")
    require(git_blob_sha(ANALYSIS_SCHEMA_PATH) == pre["analysis_schema_blob_sha"], "AK Analysis schema blob drifted")
    require(git_blob_sha(ANALYSIS_IMPL_PATH) == pre["analysis_validator_blob_sha"], "AK Analysis validator blob drifted")
    require(
        (reviews.get("version"), len(reviews.get("reviews", []))) ==
        (pre["analysis_reviews_version"], pre["analysis_review_count"]),
        "AK Analysis review pre-state mismatch",
    )
    require(
        (evidence.get("version"), len(evidence.get("evidence", []))) ==
        (pre["analysis_evidence_version"], pre["analysis_evidence_count"]),
        "AK Analysis evidence pre-state mismatch",
    )

    validation = validate_analysis(schema, evidence, reviews, canonical)
    require(validation.ok, "AK pre-state Analysis validation failed: " + "; ".join(validation.errors))
    readiness = analysis_population_readiness(schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == pre["eligible_completed_occurrence_count"], "AK eligible count drifted")
    require(readiness["reviewed_occurrence_count"] == pre["reviewed_occurrence_count"], "AK reviewed count drifted")
    require(readiness["reviewed_event_type_diversity"] == pre["reviewed_event_type_diversity"], "AK review diversity drifted")
    require(market_movement_rows(reviews) == pre["market_movement_row_count"], "AK market movement count drifted")
    require(exact_timestamp_series_rows(reviews) == pre["exact_timestamp_series_row_count"], "AK exact-series count drifted")


def transform_schema(schema: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    change = plan["schema_change"]
    require(schema.get("version") == change["from_version"], "AK schema transform called on wrong version")
    out = copy.deepcopy(schema)
    out["version"] = change["to_version"]
    out["reference_date"] = plan["reference_date"]

    vocab = out.setdefault("controlled_vocabularies", {})
    require("market_data_use_basis" not in vocab, "AK market_data_use_basis already exists")
    vocab["market_data_use_basis"] = list(change["new_controlled_vocabulary"]["market_data_use_basis"])
    evidence_roles = vocab.setdefault("evidence_role", [])
    new_rights_role = change["new_evidence_role"]
    require(new_rights_role not in evidence_roles, "AK market-data rights evidence role already exists")
    evidence_roles.append(new_rights_role)

    out["market_measurement_policy"] = {
        "canonical_event_time_and_market_measurement_precision_are_independent": True,
        "exact_timestamp_series": {
            "population_required": False,
            "required_fields": list(change["exact_timestamp_series_required_fields"]),
            "movement_representation": "PRE_POST_VALUES",
            "independently_reconstructed": True,
            "canonical_start_utc_required": True,
            "event_anchor_must_equal_canonical_start_utc": True,
            "observation_order": "before_observation_utc < event_anchor_utc <= after_observation_utc",
            "market_timezone_must_be_valid_iana": True,
            "market_observation_evidence_role_required": True,
            "allowed_market_observation_evidence_classes": ["PRIMARY_OFFICIAL", "MARKET_DATA_PROVIDER"],
            "data_use_basis_required": True,
            "data_use_evidence_role_required": "MARKET_DATA_RIGHTS",
            "data_use_evidence_ref_must_be_in_movement_evidence_refs": True,
            "allowed_market_data_rights_evidence_classes": ["PRIMARY_OFFICIAL", "MARKET_DATA_PROVIDER"],
            "public_projection_permitted_must_be_true": True,
            "exact_only_fields_prohibited_for_other_precision": True,
        },
        "rights_boundary": {
            "data_existence_does_not_establish_access_authority": True,
            "access_authority_does_not_establish_redistribution_authority": True,
            "licensed_internal_use_does_not_establish_public_projection_permission": True,
            "public_projection_permission_requires_provenance_backed_rights_evidence": True,
        },
    }

    guardrails = out.setdefault("guardrails", [])
    additions = [
        "Canonical event timing and market-measurement precision are independent: an exact canonical release timestamp never upgrades a market observation to EXACT_TIMESTAMP_SERIES.",
        "EXACT_TIMESTAMP_SERIES requires an independently reconstructed pre/post series with explicit UTC observations ordered around an event_anchor_utc copied from canonical start_utc; analytical evidence may not resolve or replace missing canonical timing.",
        "EXACT_TIMESTAMP_SERIES requires explicit market-series identity, valid IANA market timezone, series granularity and MARKET_OBSERVATION evidence from PRIMARY_OFFICIAL or MARKET_DATA_PROVIDER evidence.",
        "An exact-series data-use basis and public-projection permission must be provenance-backed by a referenced MARKET_DATA_RIGHTS evidence row from PRIMARY_OFFICIAL or MARKET_DATA_PROVIDER evidence; a bare permission boolean is insufficient.",
        "Exact market observations may enter the public Analysis dataset only when public_projection_permitted is explicitly true and the rights evidence supports that use; internal access or licensing alone does not establish redistribution permission.",
        "The absence of EXACT_TIMESTAMP_SERIES rows is acceptable and must never be treated as a quota to populate.",
    ]
    for addition in additions:
        require(addition not in guardrails, "AK schema guardrail already present")
        guardrails.append(addition)
    return out


def transform_analysis_source(source: str) -> str:
    require("EXACT_TIMESTAMP_SERIES" not in source, "AK validator already contains exact-series-specific logic")
    require("_parse_exact_utc" not in source, "AK exact UTC helper already exists")

    old_import = "from datetime import datetime\nfrom typing import Any\n"
    new_import = "from datetime import datetime, timezone\nfrom typing import Any\nfrom zoneinfo import ZoneInfo, ZoneInfoNotFoundError\n"
    require(source.count(old_import) == 1, "AK could not locate Analysis import anchor")
    source = source.replace(old_import, new_import, 1)

    parse_anchor = '''def _parse_iso(raw: str) -> bool:\n    try:\n        datetime.fromisoformat(raw.replace("Z", "+00:00"))\n        return True\n    except (TypeError, ValueError, AttributeError):\n        return False\n\n\n'''
    parse_insert = parse_anchor + '''def _parse_exact_utc(raw: Any) -> datetime | None:\n    if not isinstance(raw, str) or not raw.strip():\n        return None\n    try:\n        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))\n    except (TypeError, ValueError, AttributeError):\n        return None\n    if parsed.tzinfo is None or parsed.utcoffset() is None:\n        return None\n    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):\n        return None\n    return parsed.astimezone(timezone.utc)\n\n\ndef _valid_iana_timezone(raw: Any) -> bool:\n    if not isinstance(raw, str) or not raw.strip():\n        return False\n    try:\n        ZoneInfo(raw)\n        return True\n    except (ZoneInfoNotFoundError, ValueError):\n        return False\n\n\n'''
    require(source.count(parse_anchor) == 1, "AK could not locate ISO helper anchor")
    source = source.replace(parse_anchor, parse_insert, 1)

    vocab_anchor = '''    allowed_precision = set(vocab.get("measurement_precision", []))\n    allowed_second_order = set(vocab.get("second_order_status", []))\n    required_post_lifecycle = population_policy.get("post_event_anchor_lifecycle", "COMPLETED")\n'''
    vocab_insert = '''    allowed_precision = set(vocab.get("measurement_precision", []))\n    allowed_second_order = set(vocab.get("second_order_status", []))\n    allowed_market_data_use_basis = set(vocab.get("market_data_use_basis", []))\n    required_post_lifecycle = population_policy.get("post_event_anchor_lifecycle", "COMPLETED")\n'''
    require(source.count(vocab_anchor) == 1, "AK could not locate controlled-vocabulary anchor")
    source = source.replace(vocab_anchor, vocab_insert, 1)

    precision_anchor = '''            if movement.get("measurement_precision") not in allowed_precision:\n                errors.append(f"{analysis_id}/{movement_id}: invalid measurement_precision")\n'''
    precision_insert = '''            measurement_precision = movement.get("measurement_precision")\n            if measurement_precision not in allowed_precision:\n                errors.append(f"{analysis_id}/{movement_id}: invalid measurement_precision")\n'''
    require(source.count(precision_anchor) == 1, "AK could not locate movement precision anchor")
    source = source.replace(precision_anchor, precision_insert, 1)

    representation_anchor = '''            elif representation == "QUALITATIVE_ONLY":\n                if movement.get("measurement_precision") != "QUALITATIVE_ONLY":\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: qualitative movement requires QUALITATIVE_ONLY precision"\n                    )\n\n        connection = review.get("what_appears_connected") or {}\n'''
    exact_logic = '''            elif representation == "QUALITATIVE_ONLY":\n                if movement.get("measurement_precision") != "QUALITATIVE_ONLY":\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: qualitative movement requires QUALITATIVE_ONLY precision"\n                    )\n\n            exact_fields = (\n                "market_series_id",\n                "market_timezone",\n                "series_granularity",\n                "event_anchor_utc",\n                "before_observation_utc",\n                "after_observation_utc",\n                "data_use_basis",\n                "data_use_evidence_ref",\n                "public_projection_permitted",\n            )\n            if measurement_precision == "EXACT_TIMESTAMP_SERIES":\n                if representation != "PRE_POST_VALUES":\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires PRE_POST_VALUES"\n                    )\n                if independently_reconstructed is not True:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires independently_reconstructed=true"\n                    )\n                for field in ("market_series_id", "series_granularity"):\n                    if not str(movement.get(field) or "").strip():\n                        errors.append(\n                            f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires {field}"\n                        )\n                if not _valid_iana_timezone(movement.get("market_timezone")):\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires a valid IANA market_timezone"\n                    )\n                if movement.get("data_use_basis") not in allowed_market_data_use_basis:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires a reviewed data_use_basis"\n                    )\n                if movement.get("public_projection_permitted") is not True:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires public_projection_permitted=true"\n                    )\n\n                event_anchor = _parse_exact_utc(movement.get("event_anchor_utc"))\n                before_observation = _parse_exact_utc(movement.get("before_observation_utc"))\n                after_observation = _parse_exact_utc(movement.get("after_observation_utc"))\n                if event_anchor is None:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires UTC event_anchor_utc"\n                    )\n                if before_observation is None:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires UTC before_observation_utc"\n                    )\n                if after_observation is None:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires UTC after_observation_utc"\n                    )\n\n                canonical_anchor = _parse_exact_utc(canonical.get("start_utc")) if canonical else None\n                if canonical_anchor is None:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires an existing canonical start_utc"\n                    )\n                elif event_anchor is not None and event_anchor != canonical_anchor:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: event_anchor_utc must equal canonical start_utc"\n                    )\n                if (\n                    before_observation is not None\n                    and event_anchor is not None\n                    and after_observation is not None\n                    and not (before_observation < event_anchor <= after_observation)\n                ):\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: exact observations must satisfy before < event anchor <= after"\n                    )\n\n                movement_evidence_refs = movement.get("evidence_refs") or []\n                exact_evidence = [\n                    evidence_by_id[ref]\n                    for ref in movement_evidence_refs\n                    if ref in evidence_by_id\n                ]\n                qualified_market_evidence = [\n                    row\n                    for row in exact_evidence\n                    if "MARKET_OBSERVATION" in (row.get("roles") or [])\n                    and row.get("evidence_class") in {"PRIMARY_OFFICIAL", "MARKET_DATA_PROVIDER"}\n                ]\n                if not qualified_market_evidence:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires MARKET_OBSERVATION evidence from PRIMARY_OFFICIAL or MARKET_DATA_PROVIDER evidence"\n                    )\n\n                rights_ref = movement.get("data_use_evidence_ref")\n                if not isinstance(rights_ref, str) or not rights_ref.strip():\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: EXACT_TIMESTAMP_SERIES requires data_use_evidence_ref"\n                    )\n                elif rights_ref not in movement_evidence_refs:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: data_use_evidence_ref must be included in movement evidence_refs"\n                    )\n                else:\n                    rights_evidence = evidence_by_id.get(rights_ref)\n                    if (\n                        rights_evidence is None\n                        or "MARKET_DATA_RIGHTS" not in (rights_evidence.get("roles") or [])\n                        or rights_evidence.get("evidence_class") not in {"PRIMARY_OFFICIAL", "MARKET_DATA_PROVIDER"}\n                    ):\n                        errors.append(\n                            f"{analysis_id}/{movement_id}: data_use_evidence_ref must resolve to MARKET_DATA_RIGHTS evidence from PRIMARY_OFFICIAL or MARKET_DATA_PROVIDER evidence"\n                        )\n            else:\n                unexpected_exact_fields = [field for field in exact_fields if field in movement]\n                if unexpected_exact_fields:\n                    errors.append(\n                        f"{analysis_id}/{movement_id}: exact-series-only fields require EXACT_TIMESTAMP_SERIES precision: {unexpected_exact_fields}"\n                    )\n\n        connection = review.get("what_appears_connected") or {}\n'''
    require(source.count(representation_anchor) == 1, "AK could not locate movement representation anchor")
    source = source.replace(representation_anchor, exact_logic, 1)
    require(source.count("EXACT_TIMESTAMP_SERIES") >= 10, "AK transformed validator lacks exact-series contract")
    require(source.count("MARKET_DATA_RIGHTS") >= 1, "AK transformed validator lacks rights-provenance contract")
    return source


def load_candidate_module(source: str) -> types.ModuleType:
    name = "_world_signals_analysis_ak_candidate"
    module = types.ModuleType(name)
    module.__file__ = str(ANALYSIS_IMPL_PATH)
    module.__package__ = "world_signals"
    sys.modules[name] = module
    exec(compile(source, str(ANALYSIS_IMPL_PATH), "exec"), module.__dict__)
    return module


def candidate_state(plan: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any]]:
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    assert_pre(plan, canonical, sources, ledger, overlay, schema, reviews, evidence)

    new_schema = transform_schema(schema, plan)
    new_source = transform_analysis_source(ANALYSIS_IMPL_PATH.read_text(encoding="utf-8"))
    module = load_candidate_module(new_source)
    report = module.validate_analysis(new_schema, evidence, reviews, canonical)
    require(report.ok, "AK transformed validator rejects live Analysis state: " + "; ".join(report.errors))

    post = plan["postconditions"]
    require(new_schema.get("version") == post["analysis_schema_version"], "AK candidate schema version mismatch")
    readiness = module.analysis_population_readiness(new_schema, reviews, canonical)
    require(readiness["eligible_completed_occurrence_count"] == post["eligible_completed_occurrence_count"], "AK candidate eligible count mismatch")
    require(readiness["reviewed_occurrence_count"] == post["reviewed_occurrence_count"], "AK candidate reviewed count mismatch")
    require(readiness["reviewed_event_type_diversity"] == post["reviewed_event_type_diversity"], "AK candidate diversity mismatch")
    require(exact_timestamp_series_rows(reviews) == post["exact_timestamp_series_row_count"], "AK candidate exact-series count mismatch")

    meta = {
        "canonical": [canonical.get("version"), len(canonical.get("records", []))],
        "sources": [sources.get("version"), len(sources.get("sources", []))],
        "ledger": [ledger.get("version"), len(ledger.get("changes", []))],
        "overlay": [overlay.get("version"), overlay.get("canonical_checkpoint")],
        "schema": [schema.get("version"), new_schema.get("version")],
        "reviews": [reviews.get("version"), len(reviews.get("reviews", []))],
        "evidence": [evidence.get("version"), len(evidence.get("evidence", []))],
        "market_movement_rows": market_movement_rows(reviews),
        "exact_timestamp_series_rows": exact_timestamp_series_rows(reviews),
    }
    return new_schema, new_source, meta


def render_audit(plan: dict[str, Any], meta: dict[str, Any], protected_before: dict[str, str], protected_after: dict[str, str]) -> str:
    unchanged = protected_before == protected_after
    return f'''# WORLD SIGNALS — Exact market measurement contract AK transaction audit v0.1\n\n**Reference date:** {plan['reference_date']}\n**Exact base main:** `{plan['base_main_sha']}`\n**Mutation class:** Analysis methodology/schema validation only\n\n## Pre/post state\n\n- canonical: v{meta['canonical'][0]} / {meta['canonical'][1]} — unchanged\n- sources: v{meta['sources'][0]} / {meta['sources'][1]} — unchanged\n- change ledger: v{meta['ledger'][0]} / {meta['ledger'][1]} — unchanged\n- biosecurity overlay: v{meta['overlay'][0]} @ canonical {meta['overlay'][1]} — unchanged\n- Analysis schema: **v{meta['schema'][0]} → v{meta['schema'][1]}**\n- Analysis reviews: v{meta['reviews'][0]} / {meta['reviews'][1]} — unchanged\n- Analysis evidence: v{meta['evidence'][0]} / {meta['evidence'][1]} — unchanged\n- existing market-movement rows: {meta['market_movement_rows']} — unchanged\n- `EXACT_TIMESTAMP_SERIES` rows: **{meta['exact_timestamp_series_rows']} — unchanged at zero**\n\n## Contract added\n\n`EXACT_TIMESTAMP_SERIES` now requires independent pre/post values; an existing canonical `start_utc`; an `event_anchor_utc` equal to that canonical timestamp; explicit UTC observations ordered `before < anchor <= after`; market-series identity; valid IANA market timezone; series granularity; qualifying `MARKET_OBSERVATION` evidence; and a reviewed data-use basis whose public-projection permission is backed by referenced `MARKET_DATA_RIGHTS` evidence from a primary/official or market-data-provider record.\n\nNon-exact movement rows may not carry exact-series-only fields. Exact market evidence cannot resolve or replace missing canonical timing. Exact canonical event timing never upgrades market-measurement precision.\n\n## Rights boundary\n\nThe schema records that data existence, access authority and redistribution authority are separate. Exact observations stored in the public Analysis dataset require `public_projection_permitted=true` **and** a `data_use_evidence_ref` resolving to qualifying `MARKET_DATA_RIGHTS` evidence; a bare boolean or licensed internal access alone is insufficient.\n\n## Protected-state hash audit\n\nProtected datasets unchanged: **{unchanged}**\n\n```json\n{json.dumps({'before': protected_before, 'after': protected_after}, indent=2)}\n```\n\n## Deliberate non-actions\n\n- no canonical mutation\n- no source-registry mutation\n- no change-ledger mutation\n- no overlay or monitor mutation\n- no Analysis review/evidence population\n- no exact market-data ingestion\n- no Calendar write\n- no market-structure historical backfill\n- no auto-merge\n'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="simulate and validate without writes")
    parser.add_argument("--write", action="store_true", help="perform guarded schema/validator write")
    args = parser.parse_args()
    require(args.check ^ args.write, "choose exactly one of --check or --write")

    plan = load(PLAN_PATH)
    require(plan.get("base_main_sha") == "53e98457b70aa0dda4da490d5fe3210ce333ecae", "AK plan base SHA drifted")
    protected_before = protected_hashes()
    new_schema, new_source, meta = candidate_state(plan)
    protected_after_simulation = protected_hashes()
    require(protected_before == protected_after_simulation, "AK read-only simulation mutated protected state")

    if args.check:
        print("AK_CHECK_OK")
        print(json.dumps(meta, indent=2, ensure_ascii=False))
        return

    require(os.environ.get(APPLY_ENV) == "1", f"AK write requires {APPLY_ENV}=1")
    write_json(ANALYSIS_SCHEMA_PATH, new_schema)
    ANALYSIS_IMPL_PATH.write_text(new_source, encoding="utf-8")

    protected_after = protected_hashes()
    require(protected_before == protected_after, "AK write mutated protected datasets")

    # Re-import the newly written validator to prove the disk state, not merely the candidate string.
    module = load_candidate_module(ANALYSIS_IMPL_PATH.read_text(encoding="utf-8"))
    canonical = load(CANONICAL_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    report = module.validate_analysis(schema, evidence, reviews, canonical)
    require(report.ok, "AK written state failed Analysis validation: " + "; ".join(report.errors))
    require(schema.get("version") == plan["postconditions"]["analysis_schema_version"], "AK written schema version mismatch")
    require(exact_timestamp_series_rows(reviews) == 0, "AK write must not populate exact-series observations")

    AUDIT_PATH.write_text(render_audit(plan, meta, protected_before, protected_after), encoding="utf-8")
    print("AK_WRITE_OK")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
