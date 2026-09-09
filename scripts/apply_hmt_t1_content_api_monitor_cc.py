from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data/sources/registry.json"
MONITOR_PATH = ROOT / "data/monitor/expectations.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SMOKE_PATH = ROOT / "scripts/run_adapter_smoke.py"
LIVE_PATH = ROOT / "scripts/run_live_monitor.py"

BASE_SHA = "67de150ac1175c59ccfa3a844c1dcecd1dc2b4ed"
CANONICAL_SOURCE_ID = "WSSRC-MKT-012"
MONITOR_SOURCE_ID = "WSSRC-MKT-014"
ADAPTER_ID = "HMT_T1_CONTENT_API"
OCCURRENCE_ID = "WSO-MKT-A-0016"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def insert_once(path: Path, anchor: str, insertion: str) -> None:
    text = path.read_text(encoding="utf-8")
    if insertion in text:
        raise AssertionError(f"{path.name}: CC insertion already present; refusing pre-state transaction re-run")
    if text.count(anchor) != 1:
        raise AssertionError(f"{path.name}: expected one anchor, found {text.count(anchor)}")
    path.write_text(text.replace(anchor, insertion + anchor, 1), encoding="utf-8")


def main() -> None:
    canonical_bytes_before = CANONICAL_PATH.read_bytes()
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCE_PATH)
    monitor = load(MONITOR_PATH)

    assert canonical.get("version") == "0.41" and len(canonical.get("records", [])) == 689
    assert sources.get("version") == "2.01" and len(sources.get("sources", [])) == 256
    assert monitor.get("version") == "0.26" and len(monitor.get("adapters", [])) == 24
    assert monitor.get("automatic_canonical_commit") is False
    assert monitor.get("google_calendar_write") is False
    assert not any(s.get("source_id") == MONITOR_SOURCE_ID for s in sources["sources"])
    assert not any(a.get("adapter_id") == ADAPTER_ID for a in monitor["adapters"])

    canonical_source = [s for s in sources["sources"] if s.get("source_id") == CANONICAL_SOURCE_ID]
    assert len(canonical_source) == 1
    canonical_source_before = deepcopy(canonical_source[0])
    canonical_source_digest = stable(canonical_source_before)

    rows = [r for r in canonical["records"] if r.get("occurrence_id") == OCCURRENCE_ID]
    assert len(rows) == 1
    row = rows[0]
    expected = {
        "series_id": "WSER-MKT-UK-T1",
        "source_id": CANONICAL_SOURCE_ID,
        "category": "CORPORATE_FINANCIAL_MARKET_STRUCTURE",
        "activation_mode": "CONDITIONAL",
        "certainty_status": "PROVISIONAL",
        "condition_state": "PENDING_DEPENDENCY",
        "start_local": "2027-10-11",
        "time_status": "PROVISIONAL",
        "timing_type": "JURISDICTIONAL_CIVIL_DATE",
    }
    for key, value in expected.items():
        assert row.get(key) == value, (key, row.get(key), value)

    new_source = {
        "source_id": MONITOR_SOURCE_ID,
        "institution": "HM Treasury / GOV.UK",
        "jurisdiction": "United Kingdom",
        "domain": "corporate_financial_market_structure",
        "endpoint_role": "Official GOV.UK Content API dependency sentinel for UK T+1 policy note",
        "authoritative_url": "https://www.gov.uk/api/content/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk",
        "source_type": "official_content_api",
        "information_supplied": "Machine-readable public revision, withdrawal and pending-policy semantic markers for the HM Treasury UK T+1 policy note; not authoritative legal-completion state",
        "future_schedule_horizon": "single conditional 2027 implementation occurrence",
        "typical_advance_notice": "policy-document revision driven",
        "machine_readable_available": "JSON Content API",
        "source_timezone": "Europe/London",
        "recommended_verification_cadence": "daily",
        "activation_status": "ACTIVE",
        "parser_type": "JSON_GOVUK_CONTENT_API_DEPENDENCY_SENTINEL",
        "parser_version": "hmt-t1-content-api-0.1",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_ONE_REQUEST_PASS_2026_09_09",
        "known_limitations": [
            "The Content API policy note is not legal-completion authority for laying, Parliamentary approval, making or commencement of a statutory instrument.",
            "A public_updated_at change, withdrawal notice or pending-marker change is review evidence only and requires separate authoritative UK legal verification.",
            "Raw transport/body hash change alone is not legal-state evidence.",
            "The monitor must not automatically fetch the human page, parent publication, draft SI attachment, legislation.gov.uk, Parliament, search routes or other follow-ups."
        ],
        "backup_source": None,
        "notes": "Monitor-only machine identity. Existing WSSRC-MKT-012 remains Canonical policy/dependency authority.",
        "licence_constraints": "Open Government Licence v3.0 attribution/reuse conditions apply; third-party material remains excluded where identified.",
        "ingestion_permission": "BOUNDED_FIRST_PARTY_CONTENT_API_METADATA_AND_MINIMAL_SEMANTIC_STATE_ALLOWED",
        "licence_review_status": "CLEARED_OPEN_GOVERNMENT_LICENCE_V3",
        "automated_retrieval_permission": "CLEARED_DOCUMENTED_PUBLIC_CONTENT_API_SINGLE_OBJECT_LOW_RATE",
        "redistribution_permission": "OGL_V3_WITH_ATTRIBUTION_CONDITIONS; WORLD_SIGNALS DOES_NOT_REPUBLISH_POLICY_BODY",
        "rights_evidence_url": "https://www.gov.uk/help/terms-conditions",
        "rights_summary": "Most GOV.UK content is Crown copyright and available under the Open Government Licence v3.0; the documented Content API provides JSON access for applications, including keeping incorporated GOV.UK content up to date.",
        "automation_summary": "Exactly one request per run to the exact HM Treasury Content API object. No page, attachment, legislation, Parliament, parent-publication or search follow-ups are permitted automatically. Observations generate review candidates only.",
        "rights_reviewed_at": "2026-09-09",
        "rights_review_scope": "CC_FIRST_PARTY_CONTENT_API_AND_OGL_REVIEW",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_FIRST_PARTY_CONTENT_API_NO_AUTO_COMMIT",
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": "2026-09-09",
        "monitoring_activation_status": "LIVE_READ_ONLY_DEPENDENCY_SENTINEL_NO_AUTO_COMMIT",
        "canonical_provenance_use": "MONITOR_ONLY_NOT_CANONICAL_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "governance_backfill_reviewed_at": "2026-09-09",
        "governance_backfill_basis": "GOV.UK exposes a documented Content API and the HM Treasury policy note is OGL-covered. Clearance is narrowly scoped to one low-rate API object and does not confer legal-state authority.",
        "live_adapter_id": ADAPTER_ID,
        "monitor_endpoints": [
            {
                "endpoint_role": "hmt_t1_policy_note_content_api",
                "url": "https://www.gov.uk/api/content/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk",
                "transport": "JSON",
                "completeness_scope": "EXACT_SINGLE_POLICY_NOTE_OBJECT",
                "preferred_for_monitoring": True
            }
        ],
        "automated_monitoring_scope": {
            "cadence": "DAILY",
            "request_budget_per_run": 1,
            "content_api_request_count": 1,
            "human_page_request_count": 0,
            "parent_publication_request_count": 0,
            "attachment_request_count": 0,
            "legislation_followup_request_count": 0,
            "parliament_followup_request_count": 0,
            "search_request_count": 0
        },
        "live_validation_evidence": {
            "pressure_audit_run_id": 34322353722,
            "pressure_audit_job_id": 102371643902,
            "content_api_contract_run_id": 34322468430,
            "content_api_contract_job_id": 102372012320,
            "observed_at": "2026-09-09",
            "http_status": 200,
            "content_type": "application/json; charset=utf-8",
            "content_id": "b6b2d2f2-eae6-4564-9ed1-338abb8ca2f2",
            "public_updated_at": "2025-11-20T09:30:10+00:00",
            "request_count": 1,
            "followup_request_count": 0,
            "automatic_commit_allowed": False
        }
    }
    sources["sources"].append(new_source)
    sources["version"] = "2.02"

    adapter = {
        "adapter_id": ADAPTER_ID,
        "source_id": MONITOR_SOURCE_ID,
        "canonical_occurrence_ids": [OCCURRENCE_ID],
        "monitor_role": "CONDITIONAL_LEGISLATIVE_DEPENDENCY_SENTINEL",
        "cadence": "DAILY",
        "baseline_public_updated_at": "2025-11-20T09:30:10+00:00",
        "machine_identity": {
            "content_id": "b6b2d2f2-eae6-4564-9ed1-338abb8ca2f2",
            "base_path": "/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk",
            "title": "Policy note – Mandating T+1 settlement in the UK",
            "document_type": "html_publication",
            "schema_name": "html_publication"
        },
        "baseline_pending_markers": {
            "draft_not_final": "This is a draft SI and should not be treated as final",
            "intends_lay_final": "intends to lay the final SI",
            "affirmative_procedure": "subject to the affirmative procedure",
            "both_houses": "approved by both Houses of Parliament",
            "implementation_date": "11 October 2027"
        },
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_OR_DEPENDENCY_STATE_MUTATION",
        "positive_change_policy": "GENERATE_HMT_T1_DEPENDENCY_REVIEW_CANDIDATE_REQUIRE_SEPARATE_AUTHORITATIVE_UK_LEGAL_VERIFICATION",
        "raw_transport_hash_policy": "RAW_TRANSPORT_OR_BODY_HASH_CHANGE_ALONE_IS_NOT_LEGAL_STATE_EVIDENCE",
        "withdrawal_policy": "GENERATE_REVIEW_CANDIDATE_NO_CANCELLATION_INFERENCE",
        "request_budget_per_run": 1,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "condition_state_authority": False,
        "canonical_datetime_mutation_allowed": False,
        "automatic_attachment_fetch_allowed": False,
        "automatic_parent_page_fetch_allowed": False,
        "automatic_legislation_followup_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False
    }
    monitor["adapters"].append(adapter)
    monitor["version"] = "0.27"

    dump(SOURCE_PATH, sources)
    dump(MONITOR_PATH, monitor)

    smoke_import_anchor = "from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy\n"
    smoke_import = "from world_signals.adapters.hmt_t1_content_api import fetch_hmt_t1_content_api\n"
    insert_once(SMOKE_PATH, smoke_import_anchor, smoke_import)
    smoke_anchor = "    try:\n        sarb_items,sarb_snap=fetch_sarb_publications_rss()\n"
    smoke_block = '''    try:\n        hmt_state,hmt_snap=fetch_hmt_t1_content_api()\n        report["results"].append({\n            "adapter":"HMT_T1_CONTENT_API",\n            "status":"PASS",\n            "source_id":"WSSRC-MKT-014",\n            "snapshot":hmt_snap.as_dict(),\n            "content_id":hmt_state.content_id,\n            "public_updated_at":hmt_state.public_updated_at,\n            "withdrawn":hmt_state.withdrawn,\n            "pending_markers":hmt_state.pending_markers,\n            "semantic_sha256":hmt_state.semantic_sha256,\n            "request_budget_per_run":1,\n            "followup_request_count":0,\n            "condition_state_authority":False,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({"adapter":"HMT_T1_CONTENT_API","status":"FAIL","source_id":"WSSRC-MKT-014","error":str(exc),"canonical_action":"NONE"})\n\n'''
    insert_once(SMOKE_PATH, smoke_anchor, smoke_block)

    live_import_anchor = "from world_signals.cbn_mpc_monitor import fetch_cbn_robots_policy, cbn_mpc_schedule_review_candidates\n"
    live_import = "from world_signals.adapters.hmt_t1_content_api import fetch_hmt_t1_content_api\nfrom world_signals.hmt_t1_monitor import hmt_t1_dependency_review_candidate\n"
    insert_once(LIVE_PATH, live_import_anchor, live_import)
    live_anchor = '    if "SARB_MPC_STATEMENTS_RSS" in configs:\n'
    live_block = '''    if "HMT_T1_CONTENT_API" in configs:\n        hmt_config=configs["HMT_T1_CONTENT_API"]\n        try:\n            hmt_state,hmt_snap=fetch_hmt_t1_content_api()\n            report["source_health"].append({\n                "adapter_id":"HMT_T1_CONTENT_API",\n                "source_id":hmt_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":hmt_snap.as_dict(),\n                "content_id":hmt_state.content_id,\n                "public_updated_at":hmt_state.public_updated_at,\n                "withdrawn":hmt_state.withdrawn,\n                "pending_markers":hmt_state.pending_markers,\n                "semantic_sha256":hmt_state.semantic_sha256,\n                "request_budget_per_run":1,\n                "request_count":1,\n                "followup_request_count":0,\n                "human_page_request_count":0,\n                "parent_publication_request_count":0,\n                "attachment_request_count":0,\n                "legislation_followup_request_count":0,\n                "parliament_followup_request_count":0,\n                "search_request_count":0,\n                "schedule_authority":False,\n                "clock_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "condition_state_authority":False,\n                "canonical_datetime_mutation_allowed":False,\n                "automatic_new_occurrence_creation_allowed":False,\n                "automatic_live_or_analysis_promotion_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidate,observation=hmt_t1_dependency_review_candidate(registry.get("records",[]),hmt_state,hmt_config)\n            _append_candidate(report,candidate,observation)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"HMT_T1_CONTENT_API",\n                "source_id":hmt_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "event_state_inference":"NONE",\n                "condition_state_inference":"NONE",\n                "automatic_followup_fetch_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    insert_once(LIVE_PATH, live_anchor, live_block)

    sources_after = load(SOURCE_PATH)
    canonical_source_after = [s for s in sources_after["sources"] if s.get("source_id") == CANONICAL_SOURCE_ID]
    assert len(canonical_source_after) == 1
    assert canonical_source_after[0] == canonical_source_before
    assert stable(canonical_source_after[0]) == canonical_source_digest
    assert CANONICAL_PATH.read_bytes() == canonical_bytes_before
    assert sources_after["version"] == "2.02" and len(sources_after["sources"]) == 257
    monitor_after = load(MONITOR_PATH)
    assert monitor_after["version"] == "0.27" and len(monitor_after["adapters"]) == 25
    assert monitor_after["automatic_canonical_commit"] is False
    assert monitor_after["google_calendar_write"] is False
    print(json.dumps({
        "status":"MATERIALISED",
        "base_sha":BASE_SHA,
        "canonical":[canonical["version"],len(canonical["records"])],
        "sources":[sources_after["version"],len(sources_after["sources"])],
        "monitor":[monitor_after["version"],len(monitor_after["adapters"])],
        "canonical_source_id":CANONICAL_SOURCE_ID,
        "canonical_source_sha256":canonical_source_digest,
        "new_source_id":MONITOR_SOURCE_ID,
        "adapter_id":ADAPTER_ID,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
