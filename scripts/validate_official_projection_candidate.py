"""Offline read-only Step 14D candidate validation; no retrieval or writes."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from world_signals.official_projection_candidate import inspect_step14d

if __name__ == "__main__":
    try:
        result = inspect_step14d(ROOT)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps(result, indent=2, sort_keys=True))
