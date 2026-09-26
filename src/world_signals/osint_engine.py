"""Local-first OSINT candidate engine.

This module deliberately stops before governed Live Intelligence or Signal
promotion.  It retrieves only explicitly selected, rights-gated routes and
writes operational evidence beneath the ignored local runtime directory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import html
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


UTC = timezone.utc
ENGINE_VERSION = "osint-engine-0.2-incremental"
ALLOWED_RESULT_STATES = {
    "SUCCESS",
    "NO_NEW_INFORMATION",
    "HTTP_ERROR",
    "NETWORK_ERROR",
    "PARSER_ERROR",
    "PERMISSION_HOLD",
    "ENDPOINT_HOLD",
}
BLOCKED_WORDS = (
    "PROHIBITED",
    "HOLD",
    "PENDING",
    "NOT_AUDITED",
    "NOT_EXPRESSLY_GRANTED",
    "LICENSE_REQUIRED",
    "MANUAL_ONLY",
)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    try:
        result = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            result = parsedate_to_datetime(text)
        except (TypeError, ValueError, OverflowError):
            return None
    if result.tzinfo is None:
        return None
    return result.astimezone(UTC)


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical_url(value: str | None) -> str | None:
    if not value:
        return None
    parts = urlsplit(value.strip())
    if not parts.scheme or not parts.netloc:
        return value.strip()
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/",
                       urlencode(sorted(query)), ""))


def sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def document_identity_key(provider: str, native_id: str | None, canonical: str | None,
                          payload_hash: str) -> str:
    """Return an identity stable across URL/parser changes when native ID exists."""
    identity_payload = ({"provider": provider, "native": native_id}
                        if native_id else {"provider": provider, "url": canonical}
                        if canonical else {"provider": provider, "payload": payload_hash})
    return sha256_json(identity_payload)[:24]


@dataclass(frozen=True)
class RawRetrieval:
    source_id: str
    route_id: str
    endpoint: str
    retrieved_at: str
    result_state: str
    http_status: int | None
    content_type: str | None
    payload_sha256: str | None
    source_publication_time: str | None
    source_native_ids: tuple[str, ...]
    parser_version: str
    adapter_version: str
    error: str | None = None
    record_count: int = 0
    new_record_count: int = 0
    duplicate_record_count: int = 0
    checkpoint_state: str = "UNAVAILABLE"

    def __post_init__(self) -> None:
        if self.result_state not in ALLOWED_RESULT_STATES:
            raise ValueError(f"unknown retrieval result state: {self.result_state}")


@dataclass
class ObservationCandidate:
    candidate_id: str
    source_id: str
    route_ids: list[str]
    immediate_provider: str
    ultimate_provider: str
    source_native_id: str | None
    canonical_url: str | None
    payload_sha256: str
    publication_time: str | None
    effective_time: str | None
    retrieval_time: str
    title: str
    factual_text: str
    entities: list[dict[str, str]] = field(default_factory=list)
    jurisdictions: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    structured_values: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)
    candidate_state: str = "NEW"
    change_kind: str = "NEW"
    generation_rule: str = ENGINE_VERSION
    rationale: str = ""
    record_sha256: str = ""
    freshness_state: str = "UNKNOWN"
    novelty_state: str = "UNCLASSIFIED"
    first_seen_at: str | None = None
    revision_of_candidate_id: str | None = None

    @property
    def document_key(self) -> str:
        if self.source_native_id:
            return sha256_json({"provider": self.ultimate_provider, "native": self.source_native_id})[:24]
        if self.canonical_url:
            return sha256_json({"provider": self.ultimate_provider, "url": self.canonical_url})[:24]
        return sha256_json({"provider": self.ultimate_provider, "payload": self.payload_sha256})[:24]


@dataclass
class StoryCluster:
    cluster_id: str
    member_candidate_ids: list[str]
    rationale: str
    ultimate_providers: list[str]
    domains: list[str]
    earliest_publication_time: str | None
    latest_publication_time: str | None
    status: str = "OPERATIONAL_GROUPING_ONLY"


@dataclass
class SignalCandidate:
    candidate_id: str
    supporting_candidate_ids: list[str]
    signal_class: str
    direction: str | None
    suggested_materiality: str | None
    novelty: str | None
    persistence: str | None
    acceleration: str | None
    corroboration_summary: dict[str, Any]
    source_lineage_summary: dict[str, Any]
    contradictions: list[str]
    domains: list[str]
    entities: list[dict[str, str]]
    rationale: str
    review_priority: str
    generation_rule: str = ENGINE_VERSION


@dataclass
class RuntimeRun:
    run_id: str
    started_at: str
    completed_at: str | None
    routes_attempted: list[str]
    retrievals: list[RawRetrieval]
    observation_candidates: list[ObservationCandidate]
    duplicate_count: int
    story_clusters: list[StoryCluster]
    signal_candidates: list[SignalCandidate]
    conflicts: list[str]
    source_health: list[dict[str, Any]]
    run_mode: str = "UNKNOWN"
    checkpoint: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_cohort(registry: dict[str, Any], cohort: dict[str, Any]) -> list[str]:
    """Fail closed on route/rights mismatch; never infer permission."""
    sources = {row["source_id"]: row for row in registry.get("sources", [])}
    issues: list[str] = []
    for route in cohort.get("routes", []):
        sid = route.get("source_id")
        source = sources.get(sid)
        if source is None:
            issues.append(f"{sid}: source is absent from registry")
            continue
        auto_use = str(source.get("automated_monitoring_use") or "").upper()
        retrieval = str(source.get("automated_retrieval_permission") or "").upper()
        ingestion = str(source.get("ingestion_permission") or "").upper()
        if not auto_use.startswith("CLEARED"):
            issues.append(f"{sid}: automated_monitoring_use is not explicitly cleared ({auto_use or 'missing'})")
        for name, value in (("automated_retrieval_permission", retrieval), ("ingestion_permission", ingestion)):
            if not value or any(word in value for word in BLOCKED_WORDS):
                issues.append(f"{sid}: {name} is held or incomplete ({value or 'missing'})")
        registered = [ep.get("url") for ep in source.get("monitor_endpoints", [])]
        if route.get("endpoint") not in registered and route.get("transport") != "REST_JSON":
            issues.append(f"{sid}: cohort endpoint is not a registered preferred/known endpoint")
    return issues


def permission_decision(source: dict[str, Any], route: dict[str, Any]) -> tuple[bool, str]:
    if source.get("source_id") != route.get("source_id"):
        return False, "source/route identity mismatch"
    if not str(source.get("automated_monitoring_use") or "").upper().startswith("CLEARED"):
        return False, "automated monitoring use is not explicitly cleared"
    values = [source.get("automated_retrieval_permission"), source.get("ingestion_permission")]
    if any(not value or any(word in str(value).upper() for word in BLOCKED_WORDS) for value in values):
        return False, "retrieval or ingestion permission is held/incomplete"
    return True, "explicit cohort and source-registry permission match"


def _tag_text(node: ET.Element, name: str) -> str:
    for child in list(node):
        if child.tag.rsplit("}", 1)[-1].lower() == name.lower():
            return clean_text(child.text)
    return ""


def parse_rss(payload: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    records: list[dict[str, Any]] = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1].lower() not in {"item", "entry"}:
            continue
        link = _tag_text(node, "link")
        if not link:
            for child in list(node):
                if child.tag.rsplit("}", 1)[-1].lower() == "link":
                    link = child.attrib.get("href", "")
        native_id = _tag_text(node, "guid") or _tag_text(node, "id") or link
        title = _tag_text(node, "title")
        description = _tag_text(node, "description") or _tag_text(node, "summary") or _tag_text(node, "content")
        publication = _tag_text(node, "pubDate") or _tag_text(node, "published") or _tag_text(node, "updated")
        records.append({
            "source_native_id": native_id or None,
            "title": title,
            "factual_text": description,
            "canonical_url": canonical_url(link),
            "publication_time": iso_utc(parse_time(publication)),
        })
    return records


def parse_json_metadata(payload: bytes) -> list[dict[str, Any]]:
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON route did not return an object")
    title = data.get("title") or data.get("details", {}).get("title") if isinstance(data.get("details"), dict) else data.get("title")
    url = data.get("web_url") or data.get("url") or data.get("base_path")
    publication = data.get("public_updated_at") or data.get("first_published_at") or data.get("updated_at")
    summary = data.get("description") or data.get("summary") or data.get("publishing_app") or ""
    return [{
        "source_native_id": data.get("content_id") or data.get("base_path") or url,
        "title": clean_text(title),
        "factual_text": clean_text(summary),
        "canonical_url": canonical_url(url),
        "publication_time": iso_utc(parse_time(publication)),
        "structured_values": {"content_type": data.get("format") or data.get("document_type")},
    }]


def parse_payload(payload: bytes, transport: str) -> list[dict[str, Any]]:
    if "RSS" in transport or "XML" in transport:
        return parse_rss(payload)
    if "JSON" in transport:
        return parse_json_metadata(payload)
    raise ValueError(f"unsupported v1 transport: {transport}")


def retrieve_route(
    route: dict[str, Any],
    source: dict[str, Any],
    opener: Callable[..., Any] = urlopen,
    now: datetime | None = None,
) -> tuple[RawRetrieval, bytes | None, str]:
    allowed, reason = permission_decision(source, route)
    retrieved_at = iso_utc(now or utc_now()) or ""
    if not allowed:
        return RawRetrieval(route["source_id"], route["route_id"], route["endpoint"], retrieved_at,
                            "PERMISSION_HOLD", None, None, None, None, tuple(), route["parser"], ENGINE_VERSION, reason), None, reason
    request = Request(route["endpoint"], headers={"User-Agent": "WORLD-SIGNALS-OSINT/0.1 (read-only; local)"})
    try:
        response = opener(request, timeout=20)
        payload = response.read()
        content_type = response.headers.get("Content-Type") if getattr(response, "headers", None) else None
        retrieval = RawRetrieval(route["source_id"], route["route_id"], route["endpoint"], retrieved_at, "SUCCESS",
                                 getattr(response, "status", 200), content_type, sha256_bytes(payload), None, tuple(),
                                 route["parser"], ENGINE_VERSION)
        return retrieval, payload, "success"
    except Exception as exc:  # network failures are runtime health only
        state = "HTTP_ERROR" if getattr(exc, "code", None) else "NETWORK_ERROR"
        retrieval = RawRetrieval(route["source_id"], route["route_id"], route["endpoint"], retrieved_at, state,
                                 getattr(exc, "code", None), None, None, None, tuple(), route["parser"], ENGINE_VERSION,
                                 type(exc).__name__ + ": " + str(exc)[:240])
        return retrieval, None, str(exc)


def classify_change(title: str, factual_text: str) -> str:
    text = f"{title} {factual_text}".lower()
    if any(word in text for word in ("correction", "corrected", "erratum", "revised data")):
        return "CORRECTION"
    if any(word in text for word in ("update", "updated", "revision", "revised")):
        return "POSSIBLE_UPDATE"
    return "NEW"


def _provider(source: dict[str, Any]) -> str:
    return str(source.get("institution") or source.get("source_id"))


def normalise_records(
    records: Iterable[dict[str, Any]],
    source: dict[str, Any],
    route: dict[str, Any],
    payload_hash: str,
    retrieved_at: str,
    existing_document_keys: set[str] | None = None,
    existing_document_states: dict[str, dict[str, Any]] | None = None,
    run_mode: str = "INCREMENTAL",
    checkpoint_retrieved_at: str | None = None,
) -> tuple[list[ObservationCandidate], int]:
    existing_document_keys = existing_document_keys or set()
    existing_document_states = existing_document_states or {}
    provider = _provider(source)
    candidates: list[ObservationCandidate] = []
    duplicates = 0
    for raw in records:
        title = clean_text(raw.get("title"))
        text = clean_text(raw.get("factual_text"))
        native = clean_text(raw.get("source_native_id")) or None
        url = canonical_url(raw.get("canonical_url"))
        document_key = document_identity_key(provider, native, url, payload_hash)
        record_sha256 = sha256_json(raw)
        prior_state = existing_document_states.get(document_key)
        prior_record_sha256 = prior_state.get("record_sha256") if prior_state else None
        record_changed = bool(prior_state and prior_record_sha256 and prior_record_sha256 != record_sha256)
        if document_key in existing_document_keys and not record_changed:
            duplicates += 1
            continue
        change_kind = classify_change(title, text)
        revision_of = None
        if record_changed:
            if change_kind == "NEW":
                change_kind = "POSSIBLE_UPDATE"
            revision_of = prior_state.get("candidate_id")
        if run_mode == "BOOTSTRAP":
            freshness = "BOOTSTRAP_HISTORY"
        elif change_kind in {"CORRECTION", "POSSIBLE_UPDATE"}:
            freshness = "INCREMENTAL_REVISION"
        elif checkpoint_retrieved_at and parse_time(raw.get("publication_time")) and parse_time(raw.get("publication_time")) < parse_time(checkpoint_retrieved_at):
            freshness = "INCREMENTAL_HISTORICAL_DISCOVERY"
        elif raw.get("publication_time"):
            freshness = "INCREMENTAL_CURRENT"
        else:
            freshness = "INCREMENTAL_UNKNOWN_TIME"
        candidate_id = "WSC-OBS-" + document_key[:20]
        if revision_of:
            candidate_id += "-REV-" + payload_hash[:8]
        candidate = ObservationCandidate(
            candidate_id=candidate_id,
            source_id=source["source_id"], route_ids=[route["route_id"]],
            immediate_provider=provider, ultimate_provider=provider,
            source_native_id=native, canonical_url=url, payload_sha256=payload_hash,
            record_sha256=record_sha256,
            publication_time=raw.get("publication_time"), effective_time=raw.get("effective_time"),
            retrieval_time=retrieved_at, title=title, factual_text=text,
            entities=[{"label": provider, "entity_id": str(source["source_id"]), "resolution_state": "SOURCE_REGISTRY_ID"}],
            domains=[str(source.get("domain"))] if source.get("domain") else [],
            lineage={"source_ids": [source["source_id"]], "ultimate_provider_ids": [provider],
                     "shared_origin_key": document_key, "independence_status": "UNREVIEWED"},
            change_kind=change_kind,
            candidate_state=("POSSIBLE_CORRECTION" if change_kind == "CORRECTION"
                             else "POSSIBLE_UPDATE" if change_kind == "POSSIBLE_UPDATE"
                             else "NEW"),
            rationale="First-party route produced factual publication metadata; analytical importance remains for review.",
            freshness_state=freshness,
            novelty_state=("BOOTSTRAP_INVENTORY" if run_mode == "BOOTSTRAP"
                           else "REVISION_TO_CHECKPOINT" if revision_of
                           else "NEW_TO_CHECKPOINT"),
            first_seen_at=retrieved_at,
            revision_of_candidate_id=revision_of,
        )
        candidates.append(candidate)
    return candidates, duplicates


def deduplicate_candidates(candidates: Iterable[ObservationCandidate]) -> tuple[list[ObservationCandidate], int]:
    by_key: dict[str, ObservationCandidate] = {}
    duplicates = 0
    for candidate in candidates:
        key = (candidate.source_native_id or candidate.canonical_url or candidate.payload_sha256, candidate.ultimate_provider)
        prior = by_key.get(str(key))
        if prior is None:
            by_key[str(key)] = candidate
            continue
        duplicates += 1
        prior.route_ids = sorted(set(prior.route_ids + candidate.route_ids))
        prior.lineage["source_ids"] = sorted(set(prior.lineage.get("source_ids", []) + candidate.lineage.get("source_ids", [])))
        prior.lineage["deduplication_basis"] = "same_provider_and_native_identity_or_canonical_url"
        prior.rationale += " Duplicate route retained in lineage; not independent corroboration."
    return list(by_key.values()), duplicates


def candidate_corroboration(candidates: Iterable[ObservationCandidate]) -> dict[str, Any]:
    values = list(candidates)
    providers = sorted({item.ultimate_provider for item in values})
    documents = sorted({item.document_key for item in values})
    return {
        "candidate_count": len(values),
        "distinct_ultimate_provider_count": len(providers),
        "ultimate_providers": providers,
        "distinct_document_count": len(documents),
        "independence_status": "UNREVIEWED_REQUIRES_HUMAN_CONFIRMATION",
        "shared_origin_not_counted_as_independent": True,
    }


def persistence_state(candidates: Iterable[ObservationCandidate], minimum_gap_hours: int = 24) -> str:
    times = sorted(t for t in (parse_time(c.publication_time) for c in candidates) if t)
    if len(times) < 2:
        return "NOT_ESTABLISHED"
    return "PERSISTENT_CANDIDATE" if any(b - a >= timedelta(hours=minimum_gap_hours) for a, b in zip(times, times[1:])) else "BURST_ONLY"


def build_story_clusters(candidates: Iterable[ObservationCandidate], window_hours: int = 72) -> list[StoryCluster]:
    values = list(candidates)
    clusters: list[list[ObservationCandidate]] = []
    for candidate in values:
        tokens = set(re.findall(r"[a-z0-9]{5,}", (candidate.title + " " + candidate.factual_text).lower()))
        placed = False
        for cluster in clusters:
            prior = cluster[0]
            prior_tokens = set(re.findall(r"[a-z0-9]{5,}", (prior.title + " " + prior.factual_text).lower()))
            times = [parse_time(x.publication_time) for x in cluster + [candidate]]
            known = [x for x in times if x]
            close = not known or max(known) - min(known) <= timedelta(hours=window_hours)
            if close and (tokens & prior_tokens) and candidate.domains == prior.domains:
                cluster.append(candidate)
                placed = True
                break
        if not placed:
            clusters.append([candidate])
    output: list[StoryCluster] = []
    for cluster in clusters:
        times = [parse_time(x.publication_time) for x in cluster if parse_time(x.publication_time)]
        output.append(StoryCluster(
            cluster_id="WSC-STORY-" + sha256_json(sorted(x.candidate_id for x in cluster))[:20],
            member_candidate_ids=sorted(x.candidate_id for x in cluster),
            rationale="Operational grouping uses time proximity, token overlap and same declared domain; grouping is not factual identity.",
            ultimate_providers=sorted({x.ultimate_provider for x in cluster}),
            domains=sorted({domain for x in cluster for domain in x.domains}),
            earliest_publication_time=iso_utc(min(times)) if times else None,
            latest_publication_time=iso_utc(max(times)) if times else None,
        ))
    return output


def build_signal_candidates(candidates: Iterable[ObservationCandidate]) -> list[SignalCandidate]:
    values = [item for item in candidates if item.freshness_state == "INCREMENTAL_CURRENT"]
    by_domain: dict[str, list[ObservationCandidate]] = {}
    for item in values:
        for domain in item.domains or ["unclassified"]:
            by_domain.setdefault(domain, []).append(item)
    signals: list[SignalCandidate] = []
    for domain, items in sorted(by_domain.items()):
        corroboration = candidate_corroboration(items)
        persistence = persistence_state(items)
        if len(items) < 2 and persistence == "NOT_ESTABLISHED":
            continue
        priority = "HIGH" if corroboration["distinct_ultimate_provider_count"] >= 2 and persistence == "PERSISTENT_CANDIDATE" else "NORMAL"
        signals.append(SignalCandidate(
            candidate_id="WSC-SIG-" + sha256_json(sorted(x.candidate_id for x in items))[:20],
            supporting_candidate_ids=sorted(x.candidate_id for x in items),
            signal_class="PERSISTENT_OR_CORROBORATED_CHANGE_CANDIDATE",
            direction=None, suggested_materiality=None, novelty=None,
            persistence=persistence, acceleration=None,
            corroboration_summary=corroboration,
            source_lineage_summary={"ultimate_provider_count": corroboration["distinct_ultimate_provider_count"], "review_required": True},
            contradictions=[], domains=[domain], entities=[],
            rationale="Candidate-level nomination only; materiality, direction, contradiction and confidence require human review.",
            review_priority=priority,
        ))
    distinct_domains = sorted(by_domain)
    distinct_providers = sorted({item.ultimate_provider for item in values})
    if len(distinct_domains) >= 2 and len(distinct_providers) >= 2:
        corroboration = candidate_corroboration(values)
        signals.append(SignalCandidate(
            candidate_id="WSC-SIG-" + sha256_json({"domains": distinct_domains, "candidates": sorted(x.candidate_id for x in values)})[:20],
            supporting_candidate_ids=sorted(x.candidate_id for x in values),
            signal_class="CROSS_DOMAIN_CONVERGENCE_CANDIDATE",
            direction=None, suggested_materiality=None, novelty=None,
            persistence=persistence_state(values), acceleration=None,
            corroboration_summary=corroboration,
            source_lineage_summary={"domains": distinct_domains, "ultimate_provider_count": len(distinct_providers),
                                    "causal_claim": "PROHIBITED", "review_required": True},
            contradictions=[], domains=distinct_domains,
            entities=[json.loads(entity) for entity in sorted({json.dumps(entity, sort_keys=True) for item in values for entity in item.entities})],
            rationale="Cross-domain combination is a review prompt only; it does not establish a Relationship, Risk/Regime state or causation.",
            review_priority="HIGH",
        ))
    return signals


def build_review_queue(retrievals: Iterable[RawRetrieval], observations: Iterable[ObservationCandidate], signals: Iterable[SignalCandidate]) -> dict[str, Any]:
    return {
        "generated_by": ENGINE_VERSION,
        "public_projection": "CLOSED",
        "items": ([{"kind": "SOURCE_HEALTH", "priority": "HIGH", "source_id": r.source_id, "state": r.result_state,
                     "reason": r.error or "retrieval completed"} for r in retrievals if r.result_state not in {"SUCCESS", "NO_NEW_INFORMATION"}]
                   + [{"kind": "OBSERVATION_CANDIDATE", "priority": "NORMAL", "candidate_id": o.candidate_id,
                      "state": o.candidate_state, "reason": o.rationale} for o in observations]
                   + [{"kind": "SIGNAL_CANDIDATE", "priority": s.review_priority, "candidate_id": s.candidate_id,
                      "reason": s.rationale} for s in signals]),
        "priority_is_work_order_not_truth": True,
    }


def run_once(
    registry: dict[str, Any], cohort: dict[str, Any],
    opener: Callable[..., Any] = urlopen,
    runtime_dir: Path | None = None,
    now: datetime | None = None,
) -> RuntimeRun:
    issues = validate_cohort(registry, cohort)
    if issues:
        raise ValueError("OSINT cohort validation failed: " + "; ".join(issues))
    sources = {row["source_id"]: row for row in registry.get("sources", [])}
    started = now or utc_now()
    run_id = "OSINT-" + started.strftime("%Y%m%dT%H%M%SZ") + "-" + sha256_json(cohort)[:8]
    prior_retrievals: dict[tuple[str, str], dict[str, Any]] = {}
    prior_document_keys: set[str] = set()
    prior_document_states: dict[str, dict[str, Any]] = {}
    prior_checkpoint: dict[str, Any] = {}
    run_mode = "BOOTSTRAP"
    if runtime_dir and (runtime_dir / "latest.json").exists():
        try:
            prior = json.loads((runtime_dir / "latest.json").read_text(encoding="utf-8"))
            prior_retrievals = {
                (item.get("source_id"), item.get("route_id")): item
                for item in prior.get("retrievals", [])
            }
            prior_checkpoint = prior.get("checkpoint", {}) if isinstance(prior.get("checkpoint", {}), dict) else {}
            run_mode = "INCREMENTAL" if prior_retrievals else "BOOTSTRAP"
            prior_document_keys.update(str(key) for key in prior_checkpoint.get("seen_document_keys", []))
            for key, state in (prior_checkpoint.get("document_states", {}) or {}).items():
                if isinstance(state, dict):
                    prior_document_states[str(key)] = state
            for item in prior.get("observation_candidates", []):
                candidate = ObservationCandidate(**{key: value for key, value in item.items()
                                                    if key in ObservationCandidate.__dataclass_fields__})
                prior_document_keys.add(candidate.document_key)
                prior_document_states.setdefault(candidate.document_key, {
                    "candidate_id": candidate.candidate_id,
                    "payload_sha256": candidate.payload_sha256,
                    "record_sha256": candidate.record_sha256,
                    "source_native_id": candidate.source_native_id,
                })
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            # A corrupt runtime cache cannot become governed truth; start a fresh
            # candidate pass and leave the source-health issue visible in logs.
            prior_retrievals = {}
            prior_document_keys = set()
    retrievals: list[RawRetrieval] = []
    candidates: list[ObservationCandidate] = []
    duplicate_count = 0
    route_checkpoints: dict[str, Any] = {}
    raw_records_seen = 0
    for route in cohort.get("routes", []):
        retrieval, payload, _ = retrieve_route(route, sources[route["source_id"]], opener=opener, now=started)
        retrievals.append(retrieval)
        prior = prior_retrievals.get((retrieval.source_id, retrieval.route_id))
        checkpoint_time = (prior.get("retrieved_at") if prior else None)
        checkpoint_state = "INCREMENTAL" if prior else "BOOTSTRAP"
        if payload is None:
            retrievals[-1] = RawRetrieval(**{**asdict(retrieval), "checkpoint_state": checkpoint_state})
            route_checkpoints[route["route_id"]] = {
                "source_id": route["source_id"], "last_successful_retrieval_at": prior.get("retrieved_at") if prior else None,
                "payload_sha256": prior.get("payload_sha256") if prior else None,
                "parser_version": route["parser"], "adapter_version": ENGINE_VERSION,
                "last_processed_source_native_id": (prior.get("source_native_ids") or [None])[-1] if prior else None,
                "processed_source_native_id_count": len(prior.get("source_native_ids", [])) if prior else 0,
                "checkpoint_state": checkpoint_state,
            }
            continue
        if retrieval.result_state == "SUCCESS" and prior and prior.get("payload_sha256") == retrieval.payload_sha256:
            raw_records_seen += len(prior.get("source_native_ids", []))
            try:
                # Parse an unchanged payload only to hydrate legacy checkpoints
                # with per-record hashes. No candidates or signal support are
                # created on this path.
                for raw in parse_payload(payload, route["transport"]):
                    native = clean_text(raw.get("source_native_id")) or None
                    canonical = canonical_url(raw.get("canonical_url"))
                    key = document_identity_key(_provider(sources[route["source_id"]]), native, canonical,
                                                retrieval.payload_sha256 or "")
                    state = prior_document_states.get(key)
                    if state is not None and not state.get("record_sha256"):
                        state["record_sha256"] = sha256_json(raw)
            except Exception as exc:
                retrievals[-1] = RawRetrieval(**{**asdict(retrieval), "result_state": "PARSER_ERROR",
                                                 "error": type(exc).__name__ + ": " + str(exc)[:240],
                                                 "checkpoint_state": checkpoint_state})
                continue
            retrievals[-1] = RawRetrieval(**{**asdict(retrieval), "result_state": "NO_NEW_INFORMATION",
                                             "source_native_ids": tuple(prior.get("source_native_ids", [])),
                                             "source_publication_time": prior.get("source_publication_time"),
                                             "record_count": len(prior.get("source_native_ids", [])),
                                             "checkpoint_state": checkpoint_state})
            route_checkpoints[route["route_id"]] = {
                "source_id": route["source_id"], "last_successful_retrieval_at": retrieval.retrieved_at,
                "payload_sha256": retrieval.payload_sha256, "parser_version": route["parser"],
                "adapter_version": ENGINE_VERSION, "last_processed_source_native_id": (prior.get("source_native_ids") or [None])[-1],
                "processed_source_native_id_count": len(prior.get("source_native_ids", [])),
                "checkpoint_state": checkpoint_state,
            }
            continue
        try:
            records = parse_payload(payload, route["transport"])
            native_ids = tuple(str(x.get("source_native_id")) for x in records if x.get("source_native_id"))
            raw_records_seen += len(records)
            provider = _provider(sources[route["source_id"]])
            observed_document_states: dict[str, dict[str, Any]] = {}
            for raw in records:
                native = clean_text(raw.get("source_native_id")) or None
                canonical = canonical_url(raw.get("canonical_url"))
                key = document_identity_key(provider, native, canonical, retrieval.payload_sha256 or "")
                observed_document_states[key] = {
                    "candidate_id": None,
                    "payload_sha256": retrieval.payload_sha256,
                    "record_sha256": sha256_json(raw),
                    "source_native_id": native,
                }
            retrievals[-1] = RawRetrieval(**{**asdict(retrieval), "source_native_ids": native_ids,
                                             "source_publication_time": next((x.get("publication_time") for x in records if x.get("publication_time")), None)})
            new, dups = normalise_records(records, sources[route["source_id"]], route, retrieval.payload_sha256 or "", retrieval.retrieved_at,
                                           existing_document_keys=prior_document_keys,
                                           existing_document_states=prior_document_states,
                                           run_mode=run_mode,
                                           checkpoint_retrieved_at=checkpoint_time)
            candidates.extend(new)
            duplicate_count += dups
            for candidate in new:
                prior_document_keys.add(candidate.document_key)
                prior_document_states[candidate.document_key] = {
                    "candidate_id": candidate.candidate_id,
                    "payload_sha256": candidate.payload_sha256,
                    "record_sha256": candidate.record_sha256,
                    "source_native_id": candidate.source_native_id,
                }
            for key, state in observed_document_states.items():
                if key not in prior_document_states or not prior_document_states[key].get("record_sha256"):
                    prior_document_states[key] = state
            retrievals[-1] = RawRetrieval(**{**asdict(retrievals[-1]),
                                             "record_count": len(records), "new_record_count": len(new),
                                             "duplicate_record_count": dups, "checkpoint_state": checkpoint_state})
            route_checkpoints[route["route_id"]] = {
                "source_id": route["source_id"], "last_successful_retrieval_at": retrieval.retrieved_at,
                "payload_sha256": retrieval.payload_sha256, "parser_version": route["parser"],
                "adapter_version": ENGINE_VERSION, "last_processed_source_native_id": native_ids[-1] if native_ids else None,
                "processed_source_native_id_count": len(native_ids), "checkpoint_state": checkpoint_state,
            }
        except Exception as exc:
            retrievals[-1] = RawRetrieval(**{**asdict(retrieval), "result_state": "PARSER_ERROR", "error": type(exc).__name__ + ": " + str(exc)[:240]})
    candidates, deduped = deduplicate_candidates(candidates)
    duplicate_count += deduped
    clusters = build_story_clusters(candidates)
    signals = build_signal_candidates(candidates)
    completed = utc_now()
    metrics = {
        "raw_records_seen": raw_records_seen,
        "bootstrap_records": sum(item.freshness_state == "BOOTSTRAP_HISTORY" for item in candidates),
        "genuinely_new_records": sum(item.novelty_state == "NEW_TO_CHECKPOINT" for item in candidates),
        "current_incremental_records": sum(item.freshness_state == "INCREMENTAL_CURRENT" for item in candidates),
        "historical_discovery_records": sum(item.freshness_state == "INCREMENTAL_HISTORICAL_DISCOVERY" for item in candidates),
        "revision_candidates": sum(item.freshness_state == "INCREMENTAL_REVISION" for item in candidates),
        "duplicate_or_shared_origin_records": duplicate_count,
        "observation_candidates_requiring_review": len(candidates),
        "signal_candidates": len(signals),
        "promoted_observations": 0,
        "promoted_signals": 0,
    }
    run = RuntimeRun(run_id, iso_utc(started) or "", iso_utc(completed), [r["route_id"] for r in cohort.get("routes", [])],
                     retrievals, candidates, duplicate_count, clusters, signals,
                     [], [{"source_id": r.source_id, "state": r.result_state, "route_id": r.route_id} for r in retrievals],
                     run_mode=run_mode,
                     checkpoint={"run_mode": run_mode, "routes": route_checkpoints,
                                 "seen_document_keys": sorted(prior_document_keys),
                                 "document_states": prior_document_states},
                     metrics=metrics)
    if runtime_dir:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        (runtime_dir / "runs").mkdir(exist_ok=True)
        output = asdict(run)
        output["review_queue"] = build_review_queue(retrievals, candidates, signals)
        (runtime_dir / "runs" / f"{run_id}.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (runtime_dir / "latest.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return run


def production_promotion_policy() -> dict[str, Any]:
    return {
        "observation_candidate_to_governed_observation": "REVIEWED_TRANSACTION_REQUIRED",
        "signal_candidate_to_governed_signal": "REVIEWED_TRANSACTION_REQUIRED",
        "relationship_candidate_to_governed_relationship": "REVIEWED_TRANSACTION_REQUIRED",
        "canonical_mutation": "FORBIDDEN",
        "forecast_mutation": "FORBIDDEN",
        "public_candidate_projection": "CLOSED",
    }
