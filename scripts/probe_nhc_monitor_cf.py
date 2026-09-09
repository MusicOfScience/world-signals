from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "monitor" / "NHC_ATLANTIC_SEASON_CF_ENDPOINT_PROBE_v0.1.json"
OUT_MD = ROOT / "data" / "monitor" / "NHC_ATLANTIC_SEASON_CF_ENDPOINT_PROBE_v0.1.md"
TARGET_OCCURRENCES = ("WSO-COM-A-0049", "WSO-COM-A-0050")
SOURCE_ID = "WSSRC-RISK-002"
USER_AGENT = "WORLD-SIGNALS/0.1 (+https://github.com/MusicOfScience/world-signals; bounded source-governance endpoint review)"
MAX_BYTES = 2_000_000

ENDPOINTS = {
    "climatology": "https://www.nhc.noaa.gov/climo/",
    "rss_directory": "https://www.nhc.noaa.gov/mobile/rss.html",
    "atlantic_outlook_rss": "https://www.nhc.noaa.gov/xml/TWOAT.xml",
    "atlantic_basin_rss": "https://www.nhc.noaa.gov/index-at.xml",
    "robots": "https://www.nhc.noaa.gov/robots.txt",
    "rights": "https://www.weather.gov/disclaimer/",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def textify(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch(name: str, url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read(MAX_BYTES + 1)
            truncated = len(raw) > MAX_BYTES
            if truncated:
                raw = raw[:MAX_BYTES]
            body = textify(raw)
            headers = response.headers
            return {
                "name": name,
                "url": url,
                "ok": 200 <= response.status < 300,
                "http_status": response.status,
                "content_type": headers.get("Content-Type"),
                "content_length_header": headers.get("Content-Length"),
                "retrieved_bytes": len(raw),
                "truncated": truncated,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "body": body,
                "error": None,
            }
    except HTTPError as exc:
        raw = exc.read(MAX_BYTES)
        return {
            "name": name,
            "url": url,
            "ok": False,
            "http_status": exc.code,
            "content_type": exc.headers.get("Content-Type") if exc.headers else None,
            "content_length_header": exc.headers.get("Content-Length") if exc.headers else None,
            "retrieved_bytes": len(raw),
            "truncated": False,
            "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "body": textify(raw),
            "error": f"HTTPError {exc.code}",
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "name": name,
            "url": url,
            "ok": False,
            "http_status": None,
            "content_type": None,
            "content_length_header": None,
            "retrieved_bytes": 0,
            "truncated": False,
            "sha256": None,
            "body": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def has_season_semantics(text: str) -> bool:
    lower = text.lower()
    # Permit minor wording drift while requiring all semantic anchors.
    return (
        "atlantic" in lower
        and "hurricane season" in lower
        and "june 1" in lower
        and "november 30" in lower
    )


def public_domain_marker(text: str) -> bool:
    lower = text.lower()
    return "public domain" in lower and ("government" in lower or "national weather service" in lower)


def main() -> int:
    registry = load(ROOT / "data" / "canonical" / "registry.json")
    sources = load(ROOT / "data" / "sources" / "registry.json")
    source = next(row for row in sources["sources"] if row.get("source_id") == SOURCE_ID)
    occurrences = [row for row in registry["records"] if row.get("occurrence_id") in TARGET_OCCURRENCES]
    if {row["occurrence_id"] for row in occurrences} != set(TARGET_OCCURRENCES):
        raise SystemExit("CF NHC probe target occurrences not found exactly")
    if {row.get("source_id") for row in occurrences} != {SOURCE_ID}:
        raise SystemExit("CF NHC probe target source identity drift")

    fetched = {name: fetch(name, url) for name, url in ENDPOINTS.items()}
    climo = fetched["climatology"]
    rss_directory = fetched["rss_directory"]
    outlook = fetched["atlantic_outlook_rss"]
    basin = fetched["atlantic_basin_rss"]
    rights = fetched["rights"]

    semantics = {
        "climatology_has_atlantic_june1_nov30": has_season_semantics(climo["body"]),
        "rss_directory_identifies_atlantic_outlook_feed": "TWOAT.xml" in rss_directory["body"],
        "rss_directory_identifies_atlantic_basin_feed": "index-at.xml" in rss_directory["body"],
        "atlantic_outlook_is_machine_readable": outlook["ok"] and ("xml" in (outlook["content_type"] or "").lower() or "rss" in outlook["body"].lower()),
        "atlantic_outlook_current_payload_has_season_semantics": has_season_semantics(outlook["body"]),
        "atlantic_basin_is_machine_readable": basin["ok"] and ("xml" in (basin["content_type"] or "").lower() or "rss" in basin["body"].lower()),
        "rights_page_has_public_domain_marker": public_domain_marker(rights["body"]),
    }

    # A viable season-boundary monitor must observe the semantic authority itself.
    # RSS can corroborate operational publication, but feed activity cannot prove a
    # change to the official season definition.
    route = {
        "semantic_authority": "climatology",
        "operational_corroboration": ["rss_directory", "atlantic_outlook_rss"],
        "climatology_machine_retrieval_viable": bool(climo["ok"] and semantics["climatology_has_atlantic_june1_nov30"]),
        "rss_only_route_permitted": False,
        "candidate_route_viable": bool(
            climo["ok"]
            and semantics["climatology_has_atlantic_june1_nov30"]
            and rss_directory["ok"]
            and semantics["rss_directory_identifies_atlantic_outlook_feed"]
            and outlook["ok"]
            and semantics["atlantic_outlook_is_machine_readable"]
            and rights["ok"]
            and semantics["rights_page_has_public_domain_marker"]
        ),
        "automatic_canonical_commit": False,
        "positive_evidence_policy": "SEMANTIC_BASELINE_DRIFT_GENERATES_REVIEW_CANDIDATE_NO_DIRECT_EVENT_MUTATION",
        "negative_evidence_policy": "RSS_ABSENCE_OR_STORM_INACTIVITY_IS_SOURCE_HEALTH_ONLY_NOT_EVENT_DATE_EVIDENCE",
    }

    def endpoint_public(row: dict) -> dict:
        return {key: value for key, value in row.items() if key != "body"}

    occurrence_snapshot = []
    for row in sorted(occurrences, key=lambda x: x["occurrence_id"]):
        occurrence_snapshot.append(
            {
                key: row.get(key)
                for key in (
                    "occurrence_id", "series_id", "canonical_name", "institution", "jurisdiction", "region",
                    "category", "event_type", "lifecycle_status", "certainty_status", "start_local", "end_local",
                    "timing_type", "time_precision", "time_status", "source_id", "primary_source_assertion_id",
                    "last_successful_assertion_id", "last_verified_at",
                )
            }
        )

    source_snapshot = {
        key: source.get(key)
        for key in (
            "source_id", "institution", "jurisdiction", "domain", "endpoint_role", "authoritative_url", "source_type",
            "canonical_provenance_use", "automated_monitoring_use", "verification_mode", "monitoring_readiness_status",
            "activation_status", "parser_type", "rights_evidence_url", "rights_reviewed_at", "automated_retrieval_permission",
            "licence_review_status", "redistribution_permission",
        )
    }

    result = {
        "project": "WORLD SIGNALS",
        "dataset": "NHC_ATLANTIC_SEASON_CF_ENDPOINT_PROBE",
        "version": "0.1",
        "purpose": "Bounded endpoint and semantic review for a possible Source/Change Monitor route covering the Atlantic hurricane season definition; no Canonical mutation.",
        "opec_quarantine_respected": True,
        "source_snapshot": source_snapshot,
        "canonical_occurrences": occurrence_snapshot,
        "endpoints": {name: endpoint_public(row) for name, row in fetched.items()},
        "semantic_checks": semantics,
        "route_assessment": route,
        "retention_policy": "NO_REMOTE_SOURCE_BODY_STORED; only endpoint metadata, SHA-256, booleans and bounded local registry snapshots are persisted.",
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# WORLD SIGNALS — NHC Atlantic season CF endpoint probe v0.1",
        "",
        "This is a bounded endpoint/semantic probe. It does not create a Monitor route or mutate Canonical data.",
        "",
        "## Boundary",
        "",
        "- OPEC remains quarantined and is unrelated to this route.",
        "- NHC climatology is treated as the semantic authority for the official Atlantic season definition.",
        "- NHC RSS is operational corroboration only; storm/feed activity is never evidence that the official June 1 / November 30 season boundary changed.",
        "- No fetched source body is persisted.",
        "",
        "## Canonical targets",
        "",
    ]
    for row in occurrence_snapshot:
        lines.append(
            f"- `{row['occurrence_id']}` — {row.get('canonical_name')}; lifecycle `{row.get('lifecycle_status')}`; "
            f"start `{row.get('start_local')}`; end `{row.get('end_local')}`; source `{row.get('source_id')}`."
        )
    lines.extend(["", "## Endpoint results", "", "| Endpoint | HTTP | Type | Bytes | SHA-256 |", "|---|---:|---|---:|---|"])
    for name, row in fetched.items():
        lines.append(f"| {name} | {row.get('http_status') or '—'} | {row.get('content_type') or '—'} | {row.get('retrieved_bytes')} | `{row.get('sha256') or '—'}` |")
    lines.extend(["", "## Semantic checks", ""])
    for key, value in semantics.items():
        lines.append(f"- {key}: **{'PASS' if value else 'NO'}**")
    lines.extend(
        [
            "",
            "## Route assessment",
            "",
            f"- climatology machine retrieval viable: **{route['climatology_machine_retrieval_viable']}**",
            f"- RSS-only route permitted: **{route['rss_only_route_permitted']}**",
            f"- paired candidate route viable: **{route['candidate_route_viable']}**",
            "- positive evidence: semantic baseline drift may create a review candidate only; no direct Canonical mutation.",
            "- negative evidence: RSS absence, no active storms, or feed failure is source-health evidence only.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "PASS", "candidate_route_viable": route["candidate_route_viable"], "outputs": [str(OUT_JSON.relative_to(ROOT)), str(OUT_MD.relative_to(ROOT))]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
