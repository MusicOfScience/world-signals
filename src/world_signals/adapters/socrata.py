from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from urllib.parse import urlencode

from .base import AdapterError, FetchSnapshot, fetch_bytes

COLOMBIA_DOMAIN = "www.datos.gov.co"
SUIN_DATASET_ID = "fiev-nid6"

@dataclass(frozen=True)
class SocrataColumn:
    name: str
    field_name: str
    data_type: str | None

    def as_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class SocrataMetadata:
    dataset_id: str
    name: str
    rows_updated_at: int | None
    metadata_updated_at: int | None
    columns: tuple[SocrataColumn, ...]

    def as_dict(self) -> dict:
        data=asdict(self)
        data["columns"]=[c.as_dict() for c in self.columns]
        return data

def metadata_url(dataset_id: str = SUIN_DATASET_ID, domain: str = COLOMBIA_DOMAIN) -> str:
    return f"https://{domain}/api/views/{dataset_id}"

def resource_url(
    *,
    dataset_id: str = SUIN_DATASET_ID,
    domain: str = COLOMBIA_DOMAIN,
    where: str | None = None,
    select: str | None = None,
    limit: int = 25,
) -> str:
    params={"$limit":str(limit)}
    if where:
        params["$where"]=where
    if select:
        params["$select"]=select
    return f"https://{domain}/resource/{dataset_id}.json?{urlencode(params)}"

def parse_socrata_metadata(body: bytes | str, *, expected_id: str | None = None) -> SocrataMetadata:
    raw=body.decode("utf-8") if isinstance(body, bytes) else body
    try:
        data=json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"Socrata metadata JSON parse failed: {exc}") from exc
    dataset_id=str(data.get("id") or "")
    if not dataset_id:
        raise AdapterError("Socrata metadata missing dataset id")
    if expected_id and dataset_id != expected_id:
        raise AdapterError(f"Socrata dataset id mismatch: expected {expected_id}, got {dataset_id}")
    name=str(data.get("name") or "").strip()
    if not name:
        raise AdapterError("Socrata metadata missing dataset name")
    columns=[]
    for col in data.get("columns") or []:
        field=str(col.get("fieldName") or "").strip()
        label=str(col.get("name") or "").strip()
        if field and label:
            columns.append(SocrataColumn(label, field, col.get("dataTypeName")))
    if not columns:
        raise AdapterError("Socrata metadata contained no usable columns")
    return SocrataMetadata(
        dataset_id=dataset_id,
        name=name,
        rows_updated_at=data.get("rowsUpdatedAt"),
        metadata_updated_at=data.get("metadataUpdatedAt"),
        columns=tuple(columns),
    )

def parse_socrata_rows(body: bytes | str) -> list[dict]:
    raw=body.decode("utf-8") if isinstance(body, bytes) else body
    try:
        data=json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"Socrata row JSON parse failed: {exc}") from exc
    if not isinstance(data,list):
        raise AdapterError("Socrata resource response was not a JSON array")
    rows=[]
    for row in data:
        if not isinstance(row,dict):
            raise AdapterError("Socrata resource contained a non-object row")
        rows.append(row)
    return rows

def fetch_suin_metadata(*, timeout: int = 30) -> tuple[SocrataMetadata, FetchSnapshot]:
    url=metadata_url()
    body,snapshot=fetch_bytes(url, timeout=timeout, accept="application/json")
    return parse_socrata_metadata(body, expected_id=SUIN_DATASET_ID), snapshot

def fetch_suin_rows(
    *,
    where: str | None = None,
    select: str | None = None,
    limit: int = 25,
    timeout: int = 30,
) -> tuple[list[dict], FetchSnapshot]:
    url=resource_url(where=where, select=select, limit=limit)
    body,snapshot=fetch_bytes(url, timeout=timeout, accept="application/json")
    return parse_socrata_rows(body), snapshot
