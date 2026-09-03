#!/usr/bin/env python3
from __future__ import annotations

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
from world_signals.runtime_projection import (
    prohibited_field_hits,
    public_runtime_projection,
    unavailable_runtime_projection,
)

OUT=ROOT/"artifacts/latest-monitor-public.json"
CONTRACT=ROOT/"data/monitor/public_runtime_projection_contract.json"


def dump(payload: dict) -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


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


def github_headers(token: str) -> dict[str,str]:
    return {
        "Authorization":f"Bearer {token}",
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"WORLD-SIGNALS-Pages-runtime-projection",
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
    """Download an Actions artefact without forwarding repo credentials.

    GitHub's archive endpoint returns a signed cross-host storage URL. Repository
    Authorization is valid for the GitHub API request, but must not be carried to
    the signed storage request.
    """
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

    signed=Request(location,headers={"User-Agent":"WORLD-SIGNALS-Pages-runtime-projection"})
    with urlopen(signed,timeout=30) as response:
        return response.read()


def safe_candidate_path(raw: str) -> str:
    path=PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe candidate path in monitor manifest: {raw}")
    value=str(path)
    if not value.startswith("review_candidates/live/") or not value.endswith(".json"):
        raise ValueError(f"candidate path outside expected runtime directory: {raw}")
    return value


def sanitize_archive(blob: bytes,current: dict) -> dict:
    contract=load_json(CONTRACT)
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names=set(archive.namelist())
        report_path="artifacts/live-monitor.json"
        manifest_path="review_candidates/live/manifest.json"
        if report_path not in names or manifest_path not in names:
            raise ValueError("monitor artefact missing report or candidate manifest")
        report=json.loads(archive.read(report_path).decode("utf-8"))
        manifest=json.loads(archive.read(manifest_path).decode("utf-8"))
        candidates=[]
        for raw_path in manifest.get("files") or []:
            candidate_path=safe_candidate_path(raw_path)
            if candidate_path not in names:
                raise ValueError(f"candidate listed in manifest but missing from artefact: {candidate_path}")
            candidates.append(json.loads(archive.read(candidate_path).decode("utf-8")))

    projection=public_runtime_projection(report,manifest,candidates,current)
    prohibited=set(contract.get("prohibited_field_names") or [])
    hits=prohibited_field_hits(projection,prohibited)
    if hits:
        raise ValueError("public runtime projection contains prohibited fields: "+", ".join(hits))
    projection["public_projection_contract_version"]=contract.get("version")
    return projection


def unavailable(reason: str,current: dict,**metadata) -> int:
    payload=unavailable_runtime_projection(reason,current)
    payload["public_projection_contract_version"]=load_json(CONTRACT).get("version")
    if metadata:
        payload["delivery_metadata"]=metadata
    dump(payload)
    print(f"Runtime projection unavailable: {reason}")
    return 0


def run_metadata(run: dict) -> dict:
    return {
        "github_run_id":run.get("id"),
        "github_run_number":run.get("run_number"),
        "event":run.get("event"),
        "conclusion":run.get("conclusion"),
        "created_at":run.get("created_at"),
        "updated_at":run.get("updated_at"),
        "head_sha":run.get("head_sha"),
    }


def main() -> int:
    current=current_configuration()
    token=os.getenv("GITHUB_TOKEN")
    repository=os.getenv("GITHUB_REPOSITORY")
    if not token or not repository:
        return unavailable("NO_GITHUB_ACTIONS_ARTIFACT_CONTEXT",current)

    base=f"https://api.github.com/repos/{repository}"
    try:
        runs=request_json(
            base+"/actions/workflows/live-monitor.yml/runs?status=completed&per_page=10",
            token,
        ).get("workflow_runs",[])
    except (HTTPError,URLError,TimeoutError,ValueError,json.JSONDecodeError):
        return unavailable("GITHUB_ACTIONS_RUN_INDEX_UNAVAILABLE_AT_BUILD",current)

    if not runs:
        return unavailable("NO_COMPLETED_MONITOR_RUN_FOUND",current)

    # Never hide a newer failed monitor behind an older green run. The public
    # Operations layer follows the latest completed run, whether publishable or not.
    run=runs[0]
    metadata=run_metadata(run)
    if run.get("conclusion")!="success":
        return unavailable("LATEST_MONITOR_RUN_NOT_SUCCESSFUL",current,**metadata)

    run_id=run.get("id")
    if not run_id:
        raise ValueError("latest completed successful monitor run has no id")
    try:
        artifacts=request_json(base+f"/actions/runs/{run_id}/artifacts?per_page=100",token).get("artifacts",[])
    except (HTTPError,URLError,TimeoutError,ValueError,json.JSONDecodeError):
        return unavailable("LATEST_MONITOR_ARTIFACT_INDEX_UNAVAILABLE_AT_BUILD",current,**metadata)

    wanted=f"world-signals-live-monitor-{run_id}"
    artifact=next((item for item in artifacts if item.get("name")==wanted and not item.get("expired")),None)
    if not artifact:
        return unavailable("LATEST_SUCCESSFUL_MONITOR_RUN_HAS_NO_RETAINED_ARTIFACT",current,**metadata)

    artifact_id=artifact.get("id")
    if not artifact_id:
        raise ValueError(f"matching monitor artefact for run {run_id} has no artifact id")
    try:
        blob=download_artifact(base+f"/actions/artifacts/{artifact_id}/zip",token)
    except (HTTPError,URLError,TimeoutError,ValueError) as exc:
        return unavailable(
            "LATEST_RETAINED_MONITOR_ARTIFACT_DOWNLOAD_UNAVAILABLE_AT_BUILD",
            current,
            **metadata,
            artifact_id=artifact_id,
            failure_class=type(exc).__name__,
        )

    # An artefact that exists but violates the projection contract is a build
    # failure. Silently suppressing malformed evidence would make the UX less safe.
    projection=sanitize_archive(blob,current)
    dump(projection)
    print(
        "Sanitized latest completed monitor run "
        f"{projection.get('github_run_id')} at {projection.get('run_at')} "
        f"status={projection.get('status')} alignment={projection.get('configuration_alignment',{}).get('state')}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
