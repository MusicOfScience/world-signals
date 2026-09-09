from __future__ import annotations

import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"data/monitor/SARB_MPC_RSS_CB_PLAN_v0.1.json"
CANONICAL=ROOT/"data/canonical/registry.json"
SOURCES=ROOT/"data/sources/registry.json"
EXPECTATIONS=ROOT/"data/monitor/expectations.json"

def load(p): return json.loads(p.read_text())

def check_poststate() -> None:
    plan=load(PLAN); c=load(CANONICAL); s=load(SOURCES); e=load(EXPECTATIONS)
    if (c.get("version"),len(c.get("records",[]))) != ("0.41",689): raise SystemExit("CB Canonical poststate drift")
    if (s.get("version"),len(s.get("sources",[]))) != ("2.01",256): raise SystemExit("CB Sources poststate drift")
    if (e.get("version"),len(e.get("adapters",[]))) != ("0.26",24): raise SystemExit("CB Monitor poststate drift")
    if e.get("automatic_canonical_commit") is not False or e.get("google_calendar_write") is not False: raise SystemExit("CB write gate drift")
    old=[x for x in s["sources"] if x.get("source_id")=="WSSRC-REG-006"]; new=[x for x in s["sources"] if x.get("source_id")=="WSSRC-REG-013"]; route=[x for x in e["adapters"] if x.get("adapter_id")=="SARB_MPC_STATEMENTS_RSS"]
    if len(old)!=1 or len(new)!=1 or len(route)!=1: raise SystemExit("CB source/route identity drift")
    if old[0].get("automated_monitoring_use")!="PROHIBITED_OR_RIGHTS_HOLD": raise SystemExit("CB improperly cleared held SARB Canonical source")
    if route[0].get("canonical_occurrence_ids") != ["WSO-REG-A-0009","WSO-REG-A-0010"]: raise SystemExit("CB occurrence allow-list drift")
    for k in plan["authority_gates"]:
        if route[0].get(k) is not False: raise SystemExit(f"CB authority gate drift: {k}")
    print("CB POSTSTATE CHECK PASS")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true"); args=ap.parse_args(); check_poststate()
if __name__=="__main__": main()
