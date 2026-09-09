from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json

from .base import AdapterError, FetchSnapshot, fetch_bytes

HMT_T1_CONTENT_API = "https://www.gov.uk/api/content/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk"
HMT_T1_HUMAN_PAGE = "https://www.gov.uk/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk"
HMT_T1_CONTENT_ID = "b6b2d2f2-eae6-4564-9ed1-338abb8ca2f2"
HMT_T1_BASE_PATH = "/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk"
HMT_T1_TITLE = "Policy note – Mandating T+1 settlement in the UK"
HMT_T1_DOCUMENT_TYPE = "html_publication"
HMT_T1_SCHEMA_NAME = "html_publication"
HMT_T1_ACCEPT = "application/json"

PENDING_MARKERS = {
    "draft_not_final": "This is a draft SI and should not be treated as final",
    "intends_lay_final": "intends to lay the final SI",
    "affirmative_procedure": "subject to the affirmative procedure",
    "both_houses": "approved by both Houses of Parliament",
    "implementation_date": "11 October 2027",
}


@dataclass(frozen=True)
class HMTT1ContentState:
    content_id: str
    base_path: str
    title: str
    document_type: str
    schema_name: str
    first_published_at: str
    public_updated_at: str
    withdrawn: bool
    pending_markers: dict[str, bool]
    semantic_sha256: str

    def as_dict(self) -> dict:
        return asdict(self)


def _aware_iso(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise AdapterError(f"GOV.UK Content API missing {field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdapterError(f"GOV.UK Content API invalid {field}: {value!r}") from exc
    if parsed.tzinfo is None:
        raise AdapterError(f"GOV.UK Content API {field} lacks timezone: {value!r}")
    return value


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def parse_hmt_t1_content_api(body: bytes | str) -> HMTT1ContentState:
    raw = body.decode("utf-8") if isinstance(body, bytes) else body
    try:
        doc = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"GOV.UK Content API JSON parse failed: {exc}") from exc
    if not isinstance(doc, dict):
        raise AdapterError("GOV.UK Content API expected JSON object")

    exact = {
        "content_id": HMT_T1_CONTENT_ID,
        "base_path": HMT_T1_BASE_PATH,
        "title": HMT_T1_TITLE,
        "document_type": HMT_T1_DOCUMENT_TYPE,
        "schema_name": HMT_T1_SCHEMA_NAME,
    }
    for key, expected in exact.items():
        if doc.get(key) != expected:
            raise AdapterError(
                f"HMT T+1 Content API identity drift for {key}: expected {expected!r}, found {doc.get(key)!r}"
            )

    first_published_at = _aware_iso(doc.get("first_published_at"), "first_published_at")
    public_updated_at = _aware_iso(doc.get("public_updated_at"), "public_updated_at")
    details = doc.get("details")
    if not isinstance(details, dict) or not isinstance(details.get("body"), str):
        raise AdapterError("HMT T+1 Content API missing details.body")
    body_html = details["body"]
    pending_markers = {name: text in body_html for name, text in PENDING_MARKERS.items()}

    withdrawn_notice = doc.get("withdrawn_notice")
    if withdrawn_notice is not None and not isinstance(withdrawn_notice, dict):
        raise AdapterError("HMT T+1 Content API withdrawn_notice contract drift")
    withdrawn = withdrawn_notice is not None
    semantic = {
        "content_id": HMT_T1_CONTENT_ID,
        "public_updated_at": public_updated_at,
        "withdrawn": withdrawn,
        "pending_markers": pending_markers,
    }
    return HMTT1ContentState(
        content_id=HMT_T1_CONTENT_ID,
        base_path=HMT_T1_BASE_PATH,
        title=HMT_T1_TITLE,
        document_type=HMT_T1_DOCUMENT_TYPE,
        schema_name=HMT_T1_SCHEMA_NAME,
        first_published_at=first_published_at,
        public_updated_at=public_updated_at,
        withdrawn=withdrawn,
        pending_markers=pending_markers,
        semantic_sha256=_stable_hash(semantic),
    )


def fetch_hmt_t1_content_api(*, timeout: int = 30) -> tuple[HMTT1ContentState, FetchSnapshot]:
    body, snapshot = fetch_bytes(HMT_T1_CONTENT_API, timeout=timeout, accept=HMT_T1_ACCEPT)
    if snapshot.status != 200:
        raise AdapterError(f"HMT T+1 Content API returned HTTP {snapshot.status}")
    if "application/json" not in snapshot.content_type.lower():
        raise AdapterError(f"HMT T+1 Content API unexpected content type: {snapshot.content_type!r}")
    return parse_hmt_t1_content_api(body), snapshot
