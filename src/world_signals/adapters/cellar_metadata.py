from __future__ import annotations

from xml.etree import ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes
from .cellar import cellar_celex_url

RDF_NS="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_RESOURCE = "{"+RDF_NS+"}resource"
RDF_ABOUT = "{"+RDF_NS+"}about"
LEGAL_RELATION_TERMS=("amend","consolid","correct","repeal","replace","modify")


def fetch_cellar_rdf_notice(
    celex: str,
    *,
    timeout: int = 30,
    inferred: bool = True,
) -> tuple[bytes, FetchSnapshot]:
    """Fetch a machine-readable Cellar RDF object notice for a CELEX work.

    The inferred notice is used by default because amendment/consolidation
    inverse relations may be inferred by Cellar. This is metadata retrieval,
    not publication-content scraping.
    """
    accept="application/rdf+xml" if inferred else "application/rdf+xml;notice=non-inferred"
    return fetch_bytes(cellar_celex_url(celex),timeout=timeout,accept=accept)


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
    """Extract legal relations from a Cellar RDF notice.

    When ``base_celex`` is supplied, only predicates attached to the RDF
    subject representing that legal work are returned. This is essential:
    an inferred Cellar object notice is a graph and can also contain metadata
    about linked resources. Relations on those linked subjects must not be
    misattributed to the base act.
    """
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
            key=(local,target)
            if key in seen:
                continue
            seen.add(key)
            relations.append({
                "predicate":local,
                "target_uri":target,
                "subject_uri":subject_uri,
            })
    relations.sort(key=lambda x:(x["predicate"],x["target_uri"]))
    return relations
