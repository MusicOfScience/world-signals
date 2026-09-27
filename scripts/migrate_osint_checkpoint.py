#!/usr/bin/env python3
"""Safely migrate a retained incremental OSINT checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.osint_checkpoint import CheckpointError, migrate_checkpoint  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="source", type=Path, required=True,
                        help="validated retained checkpoint source")
    parser.add_argument("--to", dest="target", type=Path, required=True,
                        help="new empty durable checkpoint target")
    args = parser.parse_args()
    try:
        source, target = migrate_checkpoint(args.source, args.target)
    except CheckpointError as exc:
        parser.error(str(exc))
    print(json.dumps({
        "source": source.as_dict(),
        "target": target.as_dict(),
        "byte_identical": source.manifest_sha256 == target.manifest_sha256,
        "semantic_equivalent": source.semantic_sha256 == target.semantic_sha256,
        "source_retained": source.path.exists(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
