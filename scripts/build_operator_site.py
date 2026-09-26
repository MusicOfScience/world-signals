"""Build the local/private WORLD SIGNALS operator cockpit.

This output is deliberately separate from ``docs/``. It may contain local
runtime and review evidence, but it is ignored by Git and is never copied by
the public Pages build.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "operator"


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def layer(path: str, collection: str, state_key: str = "population_state") -> dict:
    payload = load(ROOT / path, {})
    return {
        "version": payload.get("version"),
        "count": len(payload.get(collection, [])),
        "state": payload.get(state_key),
    }


def local_runtime_summary() -> dict:
    runtime = ROOT / ".world-signals-runtime"
    files = list(runtime.rglob("*.json")) if runtime.exists() else []
    counts = {"observation_candidates": 0, "signal_candidates": 0, "review_items": 0}
    examples = []
    for path in files:
        payload = load(path, {})
        if not isinstance(payload, dict):
            continue
        for key, label in (
            ("observation_candidates", "observation_candidates"),
            ("signal_candidates", "signal_candidates"),
            ("items", "review_items"),
        ):
            values = payload.get(key)
            if isinstance(values, list):
                counts[label] += len(values)
                for item in values[:5]:
                    if isinstance(item, dict):
                        examples.append({
                            "kind": label,
                            "id": item.get("candidate_id") or item.get("review_item_id") or item.get("signal_candidate_id"),
                            "source_id": item.get("source_id"),
                            "state": item.get("review_state") or item.get("state") or "PENDING_REVIEW",
                        })
    return {
        "availability": "AVAILABLE_LOCAL_RUNTIME" if files else "NO_LOCAL_RUNTIME_ARTIFACT",
        "candidate_counts": counts,
        "examples": examples[:20],
    }


def build() -> Path:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    (OUTPUT / "data").mkdir(parents=True)
    for name in ("operator.html", "operator.js", "operator.css"):
        shutil.copy2(ROOT / "web" / name, OUTPUT / name)

    canonical = load(ROOT / "data/canonical/registry.json", {})
    sources = load(ROOT / "data/sources/registry.json", {})
    expectations = load(ROOT / "data/monitor/expectations.json", {})
    live = load(ROOT / "data/live_intelligence/observations.json", {})
    evaluation = load(ROOT / "data/evaluation/evaluation.json", {})
    forecasts = load(ROOT / "data/forecasts/forecasts.json", {})
    monitor = load(ROOT / "artifacts/latest-monitor-public.json", {})
    retained = load(ROOT / "artifacts/retained-review-public.json", {})

    payload = {
        "project": "WORLD SIGNALS",
        "cockpit": "LOCAL_PRIVATE_READ_ONLY",
        "system": {
            "last_monitor_snapshot": monitor if monitor else {"availability": "NO_RETAINED_SNAPSHOT"},
            "last_review_snapshot": retained if retained else {"availability": "NO_RETAINED_REVIEW_SNAPSHOT"},
            "local_runtime": local_runtime_summary(),
            "writes": {"canonical": False, "calendar": False, "browser_mutation": False},
        },
        "governed": {
            "canonical": {"version": canonical.get("version"), "count": len(canonical.get("records", []))},
            "sources": {"version": sources.get("version"), "count": len(sources.get("sources", []))},
            "monitor_routes": {"version": expectations.get("version"), "count": len(expectations.get("adapters", []))},
            "live_observations": {"version": live.get("version"), "count": len(live.get("observations", []))},
            "signals": layer("data/signals/signals.json", "signals"),
            "relationships": layer("data/relationships/relationships.json", "relationships"),
            "risks": layer("data/risks/states.json", "states"),
            "scenarios": layer("data/scenarios/scenarios.json", "scenarios"),
            "forecasts": layer("data/forecasts/forecasts.json", "forecasts"),
            "outcomes": layer("data/outcomes/outcomes.json", "outcomes"),
            "evaluation": {"version": evaluation.get("version"), "count": len(evaluation.get("evaluations", [])), "state": evaluation.get("evaluation_state")},
        },
        "forecasts": [
            {
                "forecast_id": item.get("forecast_id"),
                "question": item.get("question"),
                "forecast_type": item.get("forecast_type"),
                "issuance": item.get("issued_at_utc"),
                "information_cutoff": item.get("information_cutoff_at_utc"),
                "lifecycle_state": item.get("lifecycle_state"),
                "review_state": item.get("review_state"),
                "resolution_window": item.get("resolution", {}).get("window_start_at_utc"),
                "resolution_source_ids": item.get("resolution", {}).get("resolution_source_ids", []),
                "forecast_value": item.get("forecast_value"),
            }
            for item in forecasts.get("forecasts", [])
        ],
    }
    (OUTPUT / "data/operator.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print(f"Built local operator cockpit -> {build()}")
