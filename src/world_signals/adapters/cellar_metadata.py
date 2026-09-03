from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import re
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes
from .cellar import cellar_celex_url

RDF_NS="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_RESOURCE = "{"+RDF_NS+"}resource"
RDF_ABOUT = "{"+RDF_NS+"}about"
LEGAL_RELATION_TERMS=("amend","consolid","correct","repeal","replace","modify")
CELEX_TOKEN_RE=re.compile(r"\b(?:0\d{4}[A-Z]\d{4}-\d{8}|3\d{4}[A-Z]\d{4})\b",re.IGNORECASE)


@dataclass(frozen=True)
class CellarLegalTopology:
    base_celex: str
    amendment_target_uris: tuple[str,...]
    correction_target_uris: tuple[str,...]
    consolidation_target_uris: tuple[str,...]
    repeal_target_uris: tuple[str,...]
    topology_sha256: str

    def as_dict(self) -> dict:
        data=asdict(self)
        for key in (
            "amendment_target_uris","correction_target_uris",
            "consolidation_target_uris","repeal_target_uris",
        ):
            data[key]=list(data[key])
        return data


def fetch_cellar_rdf_notice(
    celex: str,
    *,
    timeout: int = 30,
    inferred: bool = True,
) -> tuple[bytes, FetchSnapshot]:
    """Fetch a machine-readable Cellar RDF object notice for a CELEX work."""
    accept="application/rdf+xml" if inferred else "application/rdf+xml;notice=non-inferred"
    return fetch_bytes(cellar_celex_url(celex),timeout=timeout,accept=accept)


def fetch_cellar_identifier_notice(
    resource_uri: str,
    *,
    timeout: int = 30,
) -> tuple[bytes, FetchSnapshot]:
    """Fetch the official Cellar identifier notice for a known resource URI."""
    parsed=urlparse(str(resource_uri))
    if parsed.scheme not in {"http","https"} or parsed.hostname != "publications.europa.eu":
        raise AdapterError(f"unsupported Cellar identifier resource URI: {resource_uri!r}")
    if not parsed.path.startswith("/resource/"):
        raise AdapterError(f"not a Publications Office resource URI: {resource_uri!r}")
    return fetch_bytes(
        str(resource_uri),
        timeout=timeout,
        accept="application/xml;notice=identifiers",
    )


def parse_cellar_identifier_notice(body: bytes | str) -> dict:
    """Extract CELEX synonyms and other URI identifiers from an identifier notice."""
    raw=body.encode("utf-8") if isinstance(body,str) else body
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"Cellar identifier notice was not valid XML: {exc}") from exc

    celex=[]
    uris=[]
    for element in root.iter():
        values=[]
        if element.text and element.text.strip():
            values.append(element.text.strip())
        values.extend(v for v in element.attrib.values() if v)
        for value in values:
            for match in CELEX_TOKEN_RE.findall(value):
                token=match.upper()
                if token not in celex:
                    celex.append(token)
            if value.startswith(("http://","https://")) and value not in uris:
                uris.append(value)

    return {
        "celex_ids":sorted(celex),
        "resource_uris":sorted(uris),
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}",1)[-1] if "}" in tag else tag


def _subject_matches_celex(subject: ET.Element, celex: str) -> bool:
    token=str(celex).strip().upper()
    about=(subject.attrib.get(RDF_ABOUT) or "").upper()
    if about.endswith("/CELEX/"+token):
        return True
    for child in list(subject):
        target=(child.attrib.get(RDF_RESOURCE) or "").upper()
        if target.endswith("/CELEX/"+token):
            return True
        text=(child.text or "").strip().upper()
        if text in {token,"CELEX:"+token}:
            return True
    return False


def parse_cellar_legal_relation_diagnostics(
    body: bytes | str,
    *,
    base_celex: str | None = None,
) -> list[dict]:
    """Extract legal relations from a Cellar RDF notice, optionally work-scoped."""
    raw=body.encode("utf-8") if isinstance(body,str) else body
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"Cellar RDF notice was not valid XML: {exc}") from exc

    subjects=[node for node in root.iter() if node.attrib.get(RDF_ABOUT)]
    if base_celex is not None:
        subjects=[node for node in subjects if _subject_matches_celex(node,base_celex)]
        if not subjects:
            raise AdapterError(f"Cellar RDF notice did not expose a subject for CELEX {base_celex}")

    relations=[]
    seen=set()
    for subject in subjects:
        subject_uri=subject.attrib.get(RDF_ABOUT)
        for element in list(subject):
            target=element.attrib.get(RDF_RESOURCE)
            if not target:
                continue
            local=_local_name(element.tag)
            lower=local.lower()
            if not any(term in lower for term in LEGAL_RELATION_TERMS):
                continue
            key=(local,target,subject_uri)
            if key in seen:
                continue
            seen.add(key)
            relations.append({
                "predicate":local,
                "target_uri":target,
                "subject_uri":subject_uri,
            })
    relations.sort(key=lambda x:(x["predicate"],x["target_uri"],x.get("subject_uri") or ""))
    return relations


def normalize_cellar_legal_topology(
    relations: list[dict],
    *,
    base_celex: str,
) -> CellarLegalTopology:
    """Collapse duplicate CDM relation predicates into a stable legal topology.

    The topology records only incoming relations capable of changing the legal
    state of the tracked act: amendments, corrigenda/corrections, consolidations
    and repeal relations. Outgoing ``amends`` relations are intentionally
    excluded. Consolidation component/fragment URIs are collapsed to the root
    consolidation resource.
    """
    base=str(base_celex).strip().upper()
    base_uri_suffix="/celex/"+base
    amendments=set()
    corrections=set()
    consolidations=set()
    repeals=set()

    for rel in relations:
        subject=(rel.get("subject_uri") or "")
        if not subject.endswith(base_uri_suffix):
            continue
        predicate=(rel.get("predicate") or "").lower()
        target=rel.get("target_uri")
        if not target:
            continue

        if "amended_by" in predicate:
            amendments.add(target)
        elif "corrected_by" in predicate:
            corrections.add(target)
        elif "consolidated_by" in predicate or "basis_for_act_consolidated" in predicate:
            # CDM may expose expression/component URIs such as _0000010. The
            # legal-state identity is the root consolidated act resource.
            tail=target.rsplit("/",1)[-1]
            root_tail=re.sub(r"_\d+$","",tail)
            consolidations.add(target[: -len(tail)] + root_tail)
        elif "repealed_by" in predicate:
            repeals.add(target)

    payload={
        "base_celex":base,
        "amendment_target_uris":sorted(amendments),
        "correction_target_uris":sorted(corrections),
        "consolidation_target_uris":sorted(consolidations),
        "repeal_target_uris":sorted(repeals),
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    digest=sha256(raw.encode("utf-8")).hexdigest()
    return CellarLegalTopology(
        base_celex=base,
        amendment_target_uris=tuple(payload["amendment_target_uris"]),
        correction_target_uris=tuple(payload["correction_target_uris"]),
        consolidation_target_uris=tuple(payload["consolidation_target_uris"]),
        repeal_target_uris=tuple(payload["repeal_target_uris"]),
        topology_sha256=digest,
    )
