#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from src.world_signals.validation import validate_registry

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/coverage/SOURCE_GOVERNANCE_P0_BACKFILL_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"

APPLY_ENV = "WORLD_SIGNALS_ALLOW_P0_GOVERNANCE_APPLY"
APPLY_VALUE = "YES"
COLOMBIA_ADAPTER_ID = "COLOMBIA_SUIN_DECREE_111_1996"
OLD_COLOMBIA_SOURCE_ID = "WSSRC-REG4-001"
NEW_COLOMBIA_SOURCE_ID = "WSSRC-REG4-002"

OLD_RUNTIME_LITERAL = '"adapter_id":"COLOMBIA_SUIN_DECREE_111_1996","source_id":"WSSRC-REG4-001",'
NEW_RUNTIME_LITERAL = (
    '"adapter_id":"COLOMBIA_SUIN_DECREE_111_1996",'
    '"source_id":configs["COLOMBIA_SUIN_DECREE_111_1996"]["source_id"],'
)

MODERN_GOVERNANCE_FIELDS = (
    "canonical_provenance_use",
    "automated_monitoring_use",
    "verification_mode",
    "monitoring_readiness_status",
)

TRANSFER_TO_MACHINE_SOURCE = (
    "live_adapter_id",
    "live_validation_evidence",
    "live_validation_reviewed_at",
    "endpoint_route_validation_state",
    "runtime_environment_health_state",
    "last_successful_research_verification_at",
    "endpoint_route_validated_at",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_bytes_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sources_by_id(source_registry: dict) -> dict[str, dict]:
    return {source.get("source_id"): source for source in source_registry.get("sources", [])}


def _configs_by_id(expectations: dict) -> dict[str, dict]:
    return {adapter.get("adapter_id"): adapter for adapter in expectations.get("adapters", [])}


def _assert_exact_fields(record: dict, expected: dict, label: str, errors: list[str]) -> None:
    for key, value in expected.items():
        if record.get(key) != value:
            errors.append(
                f"{label} {key}: expected {value!r}, found {record.get(key)!r}"
            )


def preflight(
    canonical: dict,
    source_registry: dict,
    expectations: dict,
    runtime_text: str,
    plan: dict,
) -> None:
    p = plan["preconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(p["canonical_registry_version"]):
        errors.append(
            f"canonical version {canonical.get('version')!r} != {p['canonical_registry_version']!r}"
        )
    if canonical.get("record_count") != p["canonical_record_count"]:
        errors.append("canonical record_count precondition failed")
    if len(canonical.get("records", [])) != p["canonical_record_count"]:
        errors.append("canonical records length precondition failed")

    if str(source_registry.get("version")) != str(p["source_registry_version"]):
        errors.append(
            f"source version {source_registry.get('version')!r} != {p['source_registry_version']!r}"
        )
    if len(source_registry.get("sources", [])) != p["source_count"]:
        errors.append("source count precondition failed")

    if str(expectations.get("version")) != str(p["monitor_expectations_version"]):
        errors.append(
            f"expectations version {expectations.get('version')!r} != {p['monitor_expectations_version']!r}"
        )

    sources = _sources_by_id(source_registry)
    for source_id in p["required_source_ids"]:
        if source_id not in sources:
            errors.append(f"required source missing: {source_id}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in sources:
            errors.append(f"new source id already exists: {source_id}")

    for source_id, spec in plan["source_updates"].items():
        if source_id not in sources:
            continue
        _assert_exact_fields(
            sources[source_id],
            spec.get("expected") or {},
            f"source {source_id}",
            errors,
        )

    configs = _configs_by_id(expectations)
    adapter = configs.get(p["colombia_adapter_id"])
    if adapter is None:
        errors.append(f"Colombia adapter missing: {p['colombia_adapter_id']}")
    elif adapter.get("source_id") != p["colombia_adapter_source_id"]:
        errors.append(
            "Colombia adapter source precondition failed: "
            f"{adapter.get('source_id')!r} != {p['colombia_adapter_source_id']!r}"
        )

    old_runtime_count = runtime_text.count(OLD_RUNTIME_LITERAL)
    if old_runtime_count != 2:
        errors.append(
            f"expected exactly 2 hard-coded Colombia runtime source literals, found {old_runtime_count}"
        )
    if NEW_RUNTIME_LITERAL in runtime_text:
        errors.append("config-driven Colombia runtime source literal already present")

    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("monitor expectations automatic_canonical_commit must remain false")
    if expectations.get("google_calendar_write") is not False:
        errors.append("monitor expectations google_calendar_write must remain false")

    if errors:
        raise SystemExit("P0 GOVERNANCE PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def transform_runtime_text(runtime_text: str) -> str:
    count = runtime_text.count(OLD_RUNTIME_LITERAL)
    if count != 2:
        raise ValueError(
            f"refusing runtime transformation: expected exactly 2 old Colombia source literals, found {count}"
        )
    transformed = runtime_text.replace(OLD_RUNTIME_LITERAL, NEW_RUNTIME_LITERAL)
    if OLD_RUNTIME_LITERAL in transformed:
        raise ValueError("old Colombia source literal remains after runtime transformation")
    if transformed.count(NEW_RUNTIME_LITERAL) != 2:
        raise ValueError("config-driven Colombia source expression count is not exactly 2")
    return transformed


def build_post_state(
    canonical: dict,
    source_registry: dict,
    expectations: dict,
    runtime_text: str,
    plan: dict,
) -> tuple[dict, dict, str, dict]:
    """Return post-state copies. Canonical is read-only and never returned mutated."""
    sources_out = copy.deepcopy(source_registry)
    expectations_out = copy.deepcopy(expectations)
    runtime_out = transform_runtime_text(runtime_text)

    sources = _sources_by_id(sources_out)
    colombia_old = sources[OLD_COLOMBIA_SOURCE_ID]
    historical_transfer = {
        key: copy.deepcopy(colombia_old[key])
        for key in TRANSFER_TO_MACHINE_SOURCE
        if key in colombia_old and colombia_old.get(key) is not None
    }

    for source_id, spec in plan["source_updates"].items():
        source = sources[source_id]
        source.update(copy.deepcopy(spec.get("set") or {}))
        if "replace_monitor_endpoints" in spec:
            source["monitor_endpoints"] = copy.deepcopy(spec["replace_monitor_endpoints"])
        for key in spec.get("drop_current_live_fields") or []:
            source.pop(key, None)

    history_entry = copy.deepcopy(plan["colombia_source_identity_history_entry"])
    history = colombia_old.setdefault("source_identity_history", [])
    if history_entry not in history:
        history.append(history_entry)

    new_sources = copy.deepcopy(plan["new_sources"])
    if len(new_sources) != 1 or new_sources[0].get("source_id") != NEW_COLOMBIA_SOURCE_ID:
        raise ValueError("plan must define exactly one new Colombia machine source")
    colombia_new = new_sources[0]
    for key, value in historical_transfer.items():
        colombia_new.setdefault(key, value)
    colombia_new["source_identity_origin"] = {
        "split_from_source_id": OLD_COLOMBIA_SOURCE_ID,
        "effective_date": history_entry["effective_date"],
        "reason": history_entry["reason"],
    }

    # Monitoring priority belongs to the machine route after decomposition.
    if colombia_old.get("monitoring_priority_score") is not None:
        colombia_new.setdefault(
            "monitoring_priority_score",
            colombia_old.get("monitoring_priority_score"),
        )

    sources_out["sources"].append(colombia_new)
    sources_out["version"] = plan["postconditions"]["source_registry_version"]
    sources_out["reference_date"] = plan["review_date"]

    configs = _configs_by_id(expectations_out)
    colombia_config = configs[COLOMBIA_ADAPTER_ID]
    monitor_update = plan["monitor_expectation_update"]
    colombia_config["source_id"] = monitor_update["set_source_id"]
    colombia_config["required_manual_verification_source_ids"] = copy.deepcopy(
        monitor_update["required_manual_verification_source_ids"]
    )
    colombia_config["source_role_contract"] = copy.deepcopy(
        monitor_update["source_role_contract"]
    )
    expectations_out["version"] = plan["postconditions"]["monitor_expectations_version"]

    report = validate_post_state(
        canonical,
        sources_out,
        expectations_out,
        runtime_out,
        plan,
    )
    return sources_out, expectations_out, runtime_out, report


def validate_post_state(
    canonical: dict,
    source_registry: dict,
    expectations: dict,
    runtime_text: str,
    plan: dict,
) -> dict:
    post = plan["postconditions"]
    errors: list[str] = []

    if str(canonical.get("version")) != str(post["canonical_registry_version"]):
        errors.append("canonical version changed")
    if canonical.get("record_count") != post["canonical_record_count"]:
        errors.append("canonical record count changed")
    if len(canonical.get("records", [])) != post["canonical_record_count"]:
        errors.append("canonical records length changed")

    if str(source_registry.get("version")) != str(post["source_registry_version"]):
        errors.append("post source registry version mismatch")
    if len(source_registry.get("sources", [])) != post["source_count"]:
        errors.append(
            f"post source count {len(source_registry.get('sources', []))} != {post['source_count']}"
        )
    source_ids = [s.get("source_id") for s in source_registry.get("sources", [])]
    if len(source_ids) != len(set(source_ids)):
        errors.append("duplicate source_id after migration")

    if str(expectations.get("version")) != str(post["monitor_expectations_version"]):
        errors.append("post monitor expectations version mismatch")
    adapters = expectations.get("adapters", [])
    if len(adapters) != post["configured_monitor_adapter_count"]:
        errors.append("configured monitor adapter count changed")
    primary_source_ids = {a.get("source_id") for a in adapters if a.get("source_id")}
    if len(primary_source_ids) != post["configured_monitor_primary_source_count"]:
        errors.append("configured monitor primary-source count changed")

    configs = _configs_by_id(expectations)
    colombia_config = configs.get(COLOMBIA_ADAPTER_ID) or {}
    if colombia_config.get("source_id") != post["colombia_machine_sentinel_source_id"]:
        errors.append("Colombia machine source did not move to WSSRC-REG4-002")
    if colombia_config.get("required_manual_verification_source_ids") != post[
        "colombia_required_manual_verification_source_ids"
    ]:
        errors.append("Colombia manual-verification source contract mismatch")
    role_contract = colombia_config.get("source_role_contract") or {}
    if role_contract.get("machine_sentinel_source_id") != NEW_COLOMBIA_SOURCE_ID:
        errors.append("Colombia role contract machine source mismatch")
    if role_contract.get("manual_clause_verification_source_id") != OLD_COLOMBIA_SOURCE_ID:
        errors.append("Colombia role contract manual source mismatch")

    if expectations.get("automatic_canonical_commit") is not False:
        errors.append("automatic canonical commit changed")
    if expectations.get("google_calendar_write") is not False:
        errors.append("Google Calendar write policy changed")

    sources = _sources_by_id(source_registry)
    if NEW_COLOMBIA_SOURCE_ID not in sources:
        errors.append("new Colombia machine source missing")
    if OLD_COLOMBIA_SOURCE_ID not in sources:
        errors.append("stable Colombia legal source identity missing")

    configured_missing: list[str] = []
    for source_id in sorted(primary_source_ids):
        source = sources.get(source_id)
        if source is None:
            errors.append(f"configured source absent from source registry: {source_id}")
            continue
        missing = [field for field in MODERN_GOVERNANCE_FIELDS if not source.get(field)]
        if missing:
            configured_missing.append(f"{source_id}:{','.join(missing)}")
    if configured_missing:
        errors.append(
            "configured monitor sources missing modern governance: "
            + "; ".join(configured_missing)
        )

    old = sources.get(OLD_COLOMBIA_SOURCE_ID) or {}
    new = sources.get(NEW_COLOMBIA_SOURCE_ID) or {}
    if old.get("canonical_dependency_count") != 1:
        errors.append("stable Colombia SUIN source lost canonical dependency")
    if new.get("canonical_dependency_count") != 0:
        errors.append("new Colombia machine source must have zero canonical dependency")
    if old.get("verification_mode") != "MANUAL_AUTHORITATIVE_RECHECK":
        errors.append("stable Colombia SUIN source is not manual authoritative verification")
    if new.get("verification_mode") != "AUTOMATED_PILOT":
        errors.append("new Colombia machine source is not automated pilot")
    if new.get("required_authoritative_verification_source_ids") != [OLD_COLOMBIA_SOURCE_ID]:
        errors.append("new Colombia machine source does not require SUIN authoritative verification")

    if runtime_text.count(NEW_RUNTIME_LITERAL) != 2:
        errors.append("runtime code does not use config-driven Colombia source exactly twice")
    if OLD_RUNTIME_LITERAL in runtime_text:
        errors.append("hard-coded old Colombia runtime source remains")

    validation = validate_registry(canonical, source_registry)
    errors.extend(validation.errors)

    if errors:
        raise ValueError("P0 GOVERNANCE POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return {
        "project": "WORLD SIGNALS",
        "transaction": "SOURCE_GOVERNANCE_P0_BACKFILL",
        "status": "PASS",
        "canonical_registry_version": canonical.get("version"),
        "canonical_record_count": canonical.get("record_count"),
        "source_registry_version": source_registry.get("version"),
        "source_count": len(source_registry.get("sources", [])),
        "monitor_expectations_version": expectations.get("version"),
        "configured_monitor_adapter_count": len(adapters),
        "configured_monitor_primary_source_ids": sorted(primary_source_ids),
        "colombia_machine_sentinel_source_id": colombia_config.get("source_id"),
        "colombia_required_manual_verification_source_ids": colombia_config.get(
            "required_manual_verification_source_ids"
        ),
        "configured_monitor_sources_with_missing_modern_governance": 0,
        "automatic_canonical_commit": False,
        "google_calendar_write": False,
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the guarded post-state. Requires explicit environment gate.",
    )
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    canonical_raw = CANONICAL_PATH.read_bytes()
    canonical_hash_before = stable_bytes_hash(canonical_raw)
    canonical = json.loads(canonical_raw.decode("utf-8"))
    source_registry = load(SOURCES_PATH)
    expectations = load(EXPECTATIONS_PATH)
    runtime_text = LIVE_RUNNER_PATH.read_text(encoding="utf-8")

    preflight(canonical, source_registry, expectations, runtime_text, plan)
    sources_out, expectations_out, runtime_out, report = build_post_state(
        canonical,
        source_registry,
        expectations,
        runtime_text,
        plan,
    )
    report["mode"] = "APPLY" if args.apply else "CHECK_ONLY"
    report["canonical_sha256_before"] = canonical_hash_before

    if args.apply:
        if os.getenv(APPLY_ENV) != APPLY_VALUE:
            raise SystemExit(
                f"refusing --apply without {APPLY_ENV}={APPLY_VALUE}"
            )
        write_json(SOURCES_PATH, sources_out)
        write_json(EXPECTATIONS_PATH, expectations_out)
        LIVE_RUNNER_PATH.write_text(runtime_out, encoding="utf-8")

        canonical_hash_after = stable_bytes_hash(CANONICAL_PATH.read_bytes())
        report["canonical_sha256_after"] = canonical_hash_after
        report["canonical_unchanged"] = canonical_hash_before == canonical_hash_after
        if not report["canonical_unchanged"]:
            raise SystemExit("CANONICAL GUARD FAILED: canonical registry bytes changed")
    else:
        report["canonical_sha256_after"] = canonical_hash_before
        report["canonical_unchanged"] = True

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
