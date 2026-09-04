from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.source_governance_audit import build_source_governance_audit


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    registry=load(ROOT/"data/canonical/registry.json")
    sources=load(ROOT/"data/sources/registry.json")
    expectations=load(ROOT/"data/monitor/expectations.json")
    audit=build_source_governance_audit(registry,sources,expectations)
    out=ROOT/"artifacts/source-governance-audit.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    totals=audit["totals"]
    print(
        "SOURCE GOVERNANCE AUDIT",
        f"source={audit['source_registry_version']}",
        f"sources={totals['source_count']}",
        f"fully_explicit={totals['fully_explicit_governance_source_count']}",
        f"missing_any={totals['source_records_with_one_or_more_missing_governance_fields']}",
        f"priorities={totals['backfill_research_priority_counts']}",
        f"missing_fields={totals['missing_field_counts']}",
    )


if __name__=="__main__":
    main()
