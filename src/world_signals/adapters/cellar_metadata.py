from __future__ import annotations

from xml.etree import ElementTree as ET

from .base import AdapterError, FetchSnapshot, fetch_bytes
from .cellar import cellar_celex_url

RDF_RESOURCE = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"
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


def parse_cellar_legal_relation_diagnostics(body: bytes | str) -> list[dict]:
    """Extract legal relationship predicates and target URIs from Cellar RDF.

    This deliberately does not map a relation to a canonical event change.
    It is a route-discovery diagnostic used to determine whether Cellar's
    machine metadata exposes amendment/consolidation topology reliably.
    """
    raw=body.encode("utf-8") if isinstance(body,str) else body
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AdapterError(f"Cellar RDF notice was not valid XML: {exc}") from exc

    relations=[]
    seen=set()
    for element in root.iter():
        target=element.attrib.get(RDF_RESOURCE)
        if not target:
            continue
        tag=element.tag
        local=tag.rsplit("}",1)[-1] if "}" in tag else tag
        lower=local.lower()
        if not any(term in lower for term in LEGAL_RELATION_TERMS):
            continue
        key=(local,target)
        if key in seen:
            continue
        seen.add(key)
        relations.append({"predicate":local,"target_uri":target})
    relations.sort(key=lambda x:(x["predicate"],x["target_uri"]))
    return relations
