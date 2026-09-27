#!/usr/bin/env python3
"""Inspect a lineage-aware World State successor review packet.

The default command is read-only.  ``--retain`` writes only explicitly named
non-governed audit evidence under ``data/world_state_audit``; it never writes
``data/world_state`` or upstream governed layers.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_successor import (  # noqa: E402
    WorldStateSuccessorReviewError,
    review_successor_lineage,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component-id", required=True)
    parser.add_argument("--knowledge-cutoff", required=True, help="explicit exact UTC knowledge cutoff")
    parser.add_argument("--retain", action="store_true", help="retain non-governed audit evidence explicitly")
    parser.add_argument("--output-stem", help="audit filename stem; required with --retain")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        packet = review_successor_lineage(args.component_id, args.knowledge_cutoff, root=ROOT)
        if args.retain:
            if not args.output_stem:
                raise WorldStateSuccessorReviewError("--output-stem is required with --retain")
            if not args.output_stem.startswith("STEP9B_"):
                raise WorldStateSuccessorReviewError("retained successor packet must use a STEP9B_ audit stem")
            audit_dir = ROOT / "data" / "world_state_audit"
            audit_dir.mkdir(parents=True, exist_ok=True)
            path = audit_dir / f"{args.output_stem}.json"
            path.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            summary = [
                "# WORLD SIGNALS — Step 9B successor review",
                "",
                "Status: READ_ONLY_AUDIT_EVIDENCE",
                f"Component: `{packet.get('component_id')}` / `{packet.get('component_revision_id')}`",
                f"Knowledge cutoff: `{packet.get('knowledge_cutoff_utc')}`",
                f"Disposition: `{packet.get('disposition')}`",
                f"Review warranted: `{packet.get('successor_review_warranted')}`",
                f"Review due: `{packet.get('review_due_at_utc')}`",
                f"Semantic fingerprint: `{packet.get('semantic_fingerprint')}`",
                "",
                "No successor was constructed or admitted. `write_targets` is `[]`; public projection is prohibited.",
            ]
            (audit_dir / f"{args.output_stem}.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
            packet["retained_paths"] = [str(path.relative_to(ROOT)), str((audit_dir / f"{args.output_stem}.md").relative_to(ROOT))]
        print(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except (WorldStateSuccessorReviewError, OSError, json.JSONDecodeError) as exc:
        print(f"World State successor review FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
