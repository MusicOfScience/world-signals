#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path, PurePosixPath
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.io import load_json
from world_signals.review_state import reduce_review_state
from world_signals.runtime_projection import prohibited_field_hits, public_runtime_projection

OUT=ROOT/"artifacts/retained-review-public.json"
CONTRACT=ROOT/"data/monitor/review_candidate_state_contract.json"
DECISIONS=ROOT/"data/monitor/review_decisions.json"
MAX_RETAINED_SUCCESSFUL_RUNS=400


def dump(payload: dict) -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def github_headers(token: str) -> dict[str,str]:
    return {
        "Authorization":f"Bearer {token}",
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"WORLD-SIGNALS-retained-review-state",
    }


def request(url: str,token: str) -> bytes:
    with urlopen(Request(url,headers=github_headers(token)),timeout=30) as response:
        return response.read()


def request_json(url: str,token: str) -> dict:
    return json.loads(request(url,token).decode("utf-8"))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def download_artifact(url: str,token: str) -> bytes:
    opener=build_opener(_NoRedirect)
    try:
        response=opener.open(Request(url,headers=github_headers(token)),timeout=30)
    except HTTPError as exc:
        if exc.code not in (301,302,303,307,308):
            raise
        location=exc.headers.get("Location")
        if not location:
            raise ValueError("artifact download redirect omitted signed storage location")
    else:
        with response:
            return response.read()
    with urlopen(Request(location,headers={"User-Agent":"WORLD-SIGNALS-retained-review-state"}),timeout=30) as response:
        return response.read()


def safe_candidate_path(raw: str) -> str:
    path=PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe candidate path in monitor manifest: {raw}")
    value=str(path)
    if not value.startswith("review_candidates/live/") or not value.endswith(".json"):
        raise ValueError(f"candidate path outside expected runtime directory: {raw}")
    return value


def current_configuration() -> dict:
    registry=load_json(ROOT/"data/canonical/registry.json")
    sources=load_json(ROOT/"data/sources/registry.json")
    expectations=load_json(ROOT/"data/monitor/expectations.json")
    policy=load_json(ROOT/"data/monitor/operations_policy.json")
    return {
        "canonical_registry_version":registry.get("version"),
        "source_registry_version":sources.get("version"),
        "monitor_expectations_version":expectations.get("version"),
        "monitor_operations_policy_version":policy.get("version"),
    }


def parse_archive(blob: bytes,current: dict,api_run: dict) -> dict:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names=set(archive.namelist())
        report_path="artifacts/live-monitor.json"
        manifest_path="review_candidates/live/manifest.json"
        if report_path not in names or manifest_path not in names:
            raise ValueError(f"monitor run {api_run.get('id')} missing report or candidate manifest")
        report=json.loads(archive.read(report_path).decode("utf-8"))
        manifest=json.loads(archive.read(manifest_path).decode("utf-8"))
        candidates=[]
        for raw_path in manifest.get("files") or []:
            candidate_path=safe_candidate_path(raw_path)
            if candidate_path not in names:
                raise ValueError(f"candidate listed in manifest but missing from run {api_run.get('id')}: {candidate_path}")
            candidates.append(json.loads(archive.read(candidate_path).decode("utf-8")))

    # Reuse the public-runtime validator as a safety gate. Its return value is not
    # persisted here; the retained reducer still receives the raw candidates only
    # in build memory so it can derive proposition identity.
    public_runtime_projection(report,manifest,candidates,current)

    context=report.get("workflow_context") or {}
    api_run_id=str(api_run.get("id"))
    report_run_id=str(context.get("github_run_id"))
    if report_run_id not in ("None","",api_run_id):
        raise ValueError(f"monitor artefact run id mismatch api={api_run_id} report={report_run_id}")
    api_run_number=int(api_run.get("run_number") or 0)
    report_run_number=context.get("github_run_number")
    if report_run_number not in (None,"") and int(report_run_number)!=api_run_number:
        raise ValueError(
            f"monitor artefact run number mismatch api={api_run_number} report={report_run_number}"
        )
    return {
        "run_number":api_run_number,
        "run_id":api_run_id,
        "run_at":report.get("run_at"),
        "candidates":candidates,
    }


def _parse_api_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)


def retained_runs(base: str,token: str,activation_run: int,cutoff: datetime) -> list[dict]:
    found=[]
    page=1
    reached_activation=False
    while page<=10 and not reached_activation:
        payload=request_json(
            base+f"/actions/workflows/live-monitor.yml/runs?status=completed&per_page=100&page={page}",
            token,
        )
        runs=payload.get("workflow_runs") or []
        if not runs:
            break
        for run in runs:
            run_number=int(run.get("run_number") or 0)
            if run_number<=activation_run:
                reached_activation=True
                break
            created=_parse_api_time(run.get("created_at"))
            if created is not None and created<cutoff:
                reached_activation=True
                break
            found.append(run)
        page+=1
    return sorted(found,key=lambda run:int(run.get("run_number") or 0))


def main() -> int:
    contract=load_json(CONTRACT)
    decisions=load_json(DECISIONS)
    registry=load_json(ROOT/"data/canonical/registry.json")
    ledger=load_json(ROOT/"data/changes/ledger.json")
    current=current_configuration()
    activation_run=int((contract.get("activation") or {}).get("activation_after_run_number") or 0)
    retention_days=int((contract.get("retention_limit") or {}).get("current_monitor_artefact_retention_days") or 90)

    token=os.getenv("GITHUB_TOKEN")
    repository=os.getenv("GITHUB_REPOSITORY")
    if not token or not repository:
        state=reduce_review_state(
            [],canonical_records=registry.get("records",[]),decisions=decisions,
            change_ledger=ledger,contract=contract,
        )
        state["availability"]="UNAVAILABLE_NO_GITHUB_ACTIONS_CONTEXT"
        state["evidence_horizon_complete"]=False
        state["evidence_gaps"]=["NO_GITHUB_ACTIONS_ARTIFACT_CONTEXT"]
        dump(state)
        return 0

    now=datetime.now(timezone.utc)
    cutoff=now-timedelta(days=retention_days)
    base=f"https://api.github.com/repos/{repository}"
    api_runs=retained_runs(base,token,activation_run,cutoff)
    successful=[run for run in api_runs if run.get("conclusion")=="success"]
    unsuccessful=[run for run in api_runs if run.get("conclusion")!="success"]
    if len(successful)>MAX_RETAINED_SUCCESSFUL_RUNS:
        raise ValueError(
            f"retained successful run count {len(successful)} exceeds bounded v0.1 reducer ceiling {MAX_RETAINED_SUCCESSFUL_RUNS}"
        )

    reduced_inputs=[]
    missing_successful_artifacts=[]
    for run in successful:
        run_id=run.get("id")
        artifacts=request_json(base+f"/actions/runs/{run_id}/artifacts?per_page=100",token).get("artifacts",[])
        wanted=f"world-signals-live-monitor-{run_id}"
        artifact=next((item for item in artifacts if item.get("name")==wanted and not item.get("expired")),None)
        if not artifact:
            missing_successful_artifacts.append(f"SUCCESSFUL_RUN_{run_id}_MISSING_RETAINED_ARTIFACT")
            continue
        artifact_id=artifact.get("id")
        if not artifact_id:
            missing_successful_artifacts.append(f"SUCCESSFUL_RUN_{run_id}_ARTIFACT_ID_MISSING")
            continue
        blob=download_artifact(base+f"/actions/artifacts/{artifact_id}/zip",token)
        reduced_inputs.append(parse_archive(blob,current,run))

    # A supposedly complete retained-horizon state must not silently omit a
    # successful run. Missing successful evidence is a build failure rather than
    # an apparently empty review state.
    if missing_successful_artifacts:
        raise ValueError(
            "retained review evidence horizon missing successful-run artefacts: "
            +"; ".join(missing_successful_artifacts)
        )

    state=reduce_review_state(
        reduced_inputs,
        canonical_records=registry.get("records",[]),
        decisions=decisions,
        change_ledger=ledger,
        contract=contract,
        generated_at=now.isoformat(),
    )
    unsuccessful_gaps=[
        f"UNSUCCESSFUL_RUN_{run.get('run_number')}_{run.get('id')}_{run.get('conclusion')}"
        for run in unsuccessful
    ]
    state["availability"]="AVAILABLE_RETAINED_HORIZON"
    state["evidence_horizon_complete"]=not bool(unsuccessful_gaps)
    state["evidence_horizon_cutoff_at"]=cutoff.isoformat()
    state["successful_run_count"]=len(successful)
    state["unsuccessful_run_count"]=len(unsuccessful)
    state["unsuccessful_runs"]=[
        {
            "run_id":str(run.get("id")),
            "run_number":run.get("run_number"),
            "conclusion":run.get("conclusion"),
            "created_at":run.get("created_at"),
        }
        for run in unsuccessful
    ]
    state["evidence_gaps"]=unsuccessful_gaps

    prohibited=set(contract.get("prohibited_public_fields") or [])
    hits=prohibited_field_hits(state,prohibited)
    if hits:
        raise ValueError("retained review public state contains prohibited fields: "+", ".join(hits))

    dump(state)
    print(
        "Reduced retained review state: "
        f"runs={state['run_count_considered']} items={state['item_count']} "
        f"states={state['state_counts']} unsuccessful_runs={state['unsuccessful_run_count']} "
        f"horizon_complete={state['evidence_horizon_complete']}"
    )
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (HTTPError,URLError,TimeoutError,json.JSONDecodeError,zipfile.BadZipFile) as exc:
        raise SystemExit(f"retained review state fetch failed: {type(exc).__name__}: {exc}")
