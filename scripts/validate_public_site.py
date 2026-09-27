"""Validate the generated public Pages artefact and its privacy boundary."""

from __future__ import annotations

import json
import re
from pathlib import Path

PROHIBITED_FILENAMES = {
    "runtime.json",
    "review_state.json",
    ".world-signals-runtime",
}
PROHIBITED_JSON_KEYS = {
    "forecast_value",
    "observation_candidates",
    "signal_candidates",
    "candidate_queue",
    "runtime_checkpoint",
    "raw_payload_cache",
}


def _json_key_hits(value, path="$", hits=None, allow_public_forecast_value=False):
    if hits is None:
        hits = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PROHIBITED_JSON_KEYS and not (
                key == "forecast_value" and allow_public_forecast_value
            ):
                hits.append(f"{path}.{key}")
            _json_key_hits(child, f"{path}.{key}", hits, allow_public_forecast_value)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _json_key_hits(child, f"{path}[{index}]", hits, allow_public_forecast_value)
    return hits


def validate_public_site(site_dir: Path) -> list[str]:
    errors = []
    required = (
        "index.html",
        ".nojekyll",
        "world-signals.ics",
        "data/events.json",
        "data/public_status.json",
        "data/outlook.json",
    )
    for relative in required:
        path = site_dir / relative
        if not path.exists():
            errors.append(f"missing required public file: {relative}")
    if not site_dir.exists():
        return [f"public site directory does not exist: {site_dir}"]

    for path in site_dir.rglob("*"):
        if any(part in PROHIBITED_FILENAMES for part in path.parts):
            errors.append(f"prohibited private artefact path: {path.relative_to(site_dir)}")
        if path.is_file() and path.suffix == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON {path.relative_to(site_dir)}: {exc}")
                continue
            relative = path.relative_to(site_dir).as_posix()
            for hit in _json_key_hits(
                payload,
                allow_public_forecast_value=relative == "data/outlook.json",
            ):
                errors.append(f"prohibited private JSON field in {path.relative_to(site_dir)}: {hit}")

    index = site_dir / "index.html"
    if index.exists():
        html = index.read_text(encoding="utf-8")
        if re.search(r"(?:href|src)=['\"]/(?!/)", html):
            errors.append("index.html contains a root-relative asset/link that would break under /world-signals/")
    ics = site_dir / "world-signals.ics"
    if ics.exists() and "BEGIN:VCALENDAR" not in ics.read_text(encoding="utf-8"):
        errors.append("world-signals.ics is not an iCalendar document")
    return errors


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("site_dir", nargs="?", type=Path, default=Path(__file__).resolve().parents[1] / "docs")
    args = parser.parse_args()
    problems = validate_public_site(args.site_dir)
    if problems:
        raise SystemExit("Public site validation failed:\n- " + "\n- ".join(problems))
    print(f"Public site validation PASS: {args.site_dir}")
