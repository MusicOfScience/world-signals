#!/usr/bin/env python3
"""Read-only validation of the governed internal signpost stores."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.assumption_signposts import (  # noqa: E402
    DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH, SCHEMA_PATH, _validate_materialized,
    build_human_review_brief,
)


def main() -> int:
    paths = [ROOT / relative for relative in (SCHEMA_PATH, DEFINITIONS_PATH, GAPS_PATH, SNAPSHOTS_PATH)]
    if not all(path.is_file() for path in paths):
        print("FAIL: signpost production stores are incomplete")
        return 1
    try:
        _validate_materialized(ROOT, exact_post_state=False)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1
    import json
    definitions = json.loads((ROOT / DEFINITIONS_PATH).read_text(encoding="utf-8"))
    gaps = json.loads((ROOT / GAPS_PATH).read_text(encoding="utf-8"))
    snapshots = json.loads((ROOT / SNAPSHOTS_PATH).read_text(encoding="utf-8"))
    brief = build_human_review_brief(ROOT)
    print(f"PASS: {len(definitions['definitions'])} internal signpost definitions")
    print(f"PASS: {len(gaps['gaps'])} source-coverage gaps; routes created=0")
    print(f"PASS: {len(snapshots['snapshots'])} immutable assessment snapshot(s); public=false")
    print(f"PASS: internal review summary rendered ({len(brief.splitlines())} lines)")
    print("PASS: validation is read-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
