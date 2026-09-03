from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Mapping
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

USER_AGENT = "WORLD-SIGNALS/0.2 (+https://github.com/MusicOfScience/world-signals)"


class AdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchSnapshot:
    url: str
    resolved_url: str
    status: int
    content_type: str
    body_sha256: str
    body_bytes: int

    def as_dict(self) -> dict:
        return asdict(self)


def fetch_bytes(
    url: str,
    *,
    timeout: int = 30,
    accept: str = "*/*",
    headers: Mapping[str, str] | None = None,
) -> tuple[bytes, FetchSnapshot]:
    request_headers={"User-Agent": USER_AGENT, "Accept": accept}
    if headers:
        request_headers.update({str(k):str(v) for k,v in headers.items()})
    req=Request(url, headers=request_headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body=resp.read()
            status=getattr(resp, "status", 200)
            ctype=resp.headers.get("Content-Type", "")
            resolved_url=resp.geturl()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise AdapterError(f"fetch failed for {url}: {exc}") from exc
    if not body:
        raise AdapterError(f"empty response body from {url}")
    snap=FetchSnapshot(
        url=url,
        resolved_url=resolved_url,
        status=int(status),
        content_type=ctype,
        body_sha256=sha256(body).hexdigest(),
        body_bytes=len(body),
    )
    return body, snap
