from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULE_PATH=ROOT/"scripts/apply_source_native_calendar_nepal_n.py"
SPEC=importlib.util.spec_from_file_location("apply_source_native_calendar_nepal_n",MODULE_PATH)
TX=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TX)

PLAN_PATH=ROOT/"data/coverage/SOURCE_NATIVE_CALENDAR_NEPAL_PLAN_v0.1.json"
RESEARCH_PATH=ROOT/"data/coverage/SOURCE_NATIVE_CALENDAR_NEPAL_AUDIT_v0.1.md"
SCHEMA_PATH=ROOT/"data/canonical/schema.json"
CANONICAL_PATH=ROOT/"data/canonical/registry.json"
SOURCES_PATH=ROOT/"data/sources/registry.json"
LEDGER_PATH=ROOT/"data/changes/ledger.json"
EXPECTATIONS_PATH=ROOT/"data/monitor/expectations.json"


class SourceNativeCalendarNepalNTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.research=RESEARCH_PATH.read_text(encoding="utf-8")
        cls.schema=json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.canonical=json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cls.sources=json.loads(SOURCES_PATH.read_text(encoding="utf-8"))

    def _is_pre(self):
        return (
            self.schema.get("version")=="0.51"
            and self.canonical.get("version")=="0.27"
            and len(self.canonical.get("records",[]))==673
            and self.sources.get("version")=="1.68"
            and len(self.sources.get("sources",[]))==231
        )

    def _is_post(self):
        oids={r.get("occurrence_id") for r in self.canonical.get("records",[])}
        source_ids={r.get("source_id") for r in self.sources.get("sources",[])}
        timing_vocab=(self.schema.get("controlled_vocabularies") or {}).get("timing_type",[])
        return (
            self.schema.get("version")=="0.52"
            and self.canonical.get("version")=="0.28"
            and len(self.canonical.get("records",[]))==674
            and self.sources.get("version")=="1.69"
            and len(self.sources.get("sources",[]))==233
            and "WSO-FIS-NP-BUDGET-2084" in oids
            and {"WSSRC-FIS-026","WSSRC-FIS-027"}.issubset(source_ids)
            and "SOURCE_NATIVE_CALENDAR_DATE" in timing_vocab
        )

    def _post_objects(self):
        if self._is_pre():
            TX.preflight(self.schema,self.canonical,self.sources,self.plan)
            schema,canonical,sources,_=TX.build_post_state(self.schema,self.canonical,self.sources,self.plan)
            return schema,canonical,sources
        if self._is_post():
            return self.schema,self.canonical,self.sources
        self.fail("repository is neither exact Nepal N pre-state nor reviewed post-state")

    def test_repository_is_exact_pre_or_post_state(self):
        self.assertTrue(self._is_pre() or self._is_post())
        schema,canonical,sources=self._post_objects()
        self.assertEqual(schema["version"],"0.52")
        self.assertEqual(canonical["version"],"0.28")
        self.assertEqual(len(canonical["records"]),674)
        self.assertEqual(sources["version"],"1.69")
        self.assertEqual(len(sources["sources"]),233)

    def test_scope_is_one_series_one_occurrence_two_sources(self):
        self.assertEqual(self.plan["preconditions"]["required_absent_series_ids"],["WSER-FIS-NP-FEDERAL-BUDGET"])
        self.assertEqual(self.plan["preconditions"]["required_absent_occurrence_ids"],["WSO-FIS-NP-BUDGET-2084"])
        self.assertEqual([s["source_id"] for s in self.plan["sources"]],["WSSRC-FIS-026","WSSRC-FIS-027"])

    def test_nepal_is_exact_native_date_and_gregorian_fields_are_empty(self):
        _,canonical,_=self._post_objects()
        row=next(r for r in canonical["records"] if r.get("occurrence_id")=="WSO-FIS-NP-BUDGET-2084")
        self.assertEqual(row["certainty_status"],"CONFIRMED")
        self.assertEqual(row["activation_mode"],"AUTHORITATIVE_RECURRING_RULE")
        self.assertEqual(row["timing_type"],"SOURCE_NATIVE_CALENDAR_DATE")
        self.assertEqual(row["native_calendar_system"],"BIKRAM_SAMBAT_NEPAL")
        self.assertEqual((row["native_calendar_year"],row["native_calendar_month"],row["native_calendar_day"]),(2084,"JESTHA",15))
        self.assertEqual(row["source_native_date_label"],"15 Jestha 2084")
        self.assertEqual(row["gregorian_resolution_status"],"UNRESOLVED_AUTHORITATIVE_CONVERSION")
        self.assertEqual(row["publication_time_semantics"],"SOURCE_NATIVE_DATE_ONLY")
        for field in ("start_local","end_local","start_utc","end_utc","date_earliest","date_latest","publication_datetime"):
            self.assertIsNone(row[field],field)

    def test_nepal_uses_existing_fiscal_process_taxonomy_without_deadline_mislabel(self):
        _,canonical,_=self._post_objects()
        row=next(r for r in canonical["records"] if r.get("occurrence_id")=="WSO-FIS-NP-BUDGET-2084")
        self.assertEqual(row["category"],"FISCAL_SOVEREIGN_FINANCE")
        self.assertEqual(row["subcategory"],"national_budget")
        self.assertEqual(row["event_type"],"FISCAL_POLICY_PROCESS")
        self.assertEqual(row["fiscal_process_milestone_type"],"BUDGET_PRESENTATION")
        self.assertIsNone(row["deadline_type"])
        self.assertIsNone(row["deadline_semantics"])

    def test_legal_authority_and_publication_source_are_separated(self):
        _,canonical,sources=self._post_objects()
        row=next(r for r in canonical["records"] if r.get("occurrence_id")=="WSO-FIS-NP-BUDGET-2084")
        self.assertEqual(row["source_id"],"WSSRC-FIS-026")
        self.assertEqual(row["legal_basis_source_id"],"WSSRC-FIS-026")
        self.assertIn("WSSRC-FIS-027",row["derivation_sources"])
        by_id={s["source_id"]:s for s in sources["sources"]}
        self.assertIn("Article 119",by_id["WSSRC-FIS-026"]["endpoint_role"])
        self.assertIn("budget",by_id["WSSRC-FIS-027"]["endpoint_role"].lower())
        self.assertEqual(by_id["WSSRC-FIS-026"]["canonical_dependency_count"],1)
        self.assertEqual(by_id["WSSRC-FIS-027"]["canonical_dependency_count"],0)

    def test_sources_are_manual_provenance_not_automation_permission(self):
        _,_,sources=self._post_objects()
        by_id={s["source_id"]:s for s in sources["sources"]}
        for sid in ("WSSRC-FIS-026","WSSRC-FIS-027"):
            row=by_id[sid]
            self.assertEqual(row["canonical_provenance_use"],"MANUAL_INFORMATIONAL_REFERENCE_ONLY")
            self.assertEqual(row["automated_monitoring_use"],"PROHIBITED_OR_RIGHTS_HOLD")
            self.assertEqual(row["verification_mode"],"RIGHTS_HELD_MANUAL_ONLY")
            self.assertEqual(row["monitoring_readiness_status"],"RIGHTS_AUDIT_REQUIRED")

    def test_schema_support_is_reusable_not_nepal_date_conversion(self):
        schema,_,_=self._post_objects()
        cv=schema["controlled_vocabularies"]
        self.assertIn("SOURCE_NATIVE_CALENDAR_DATE",cv["timing_type"])
        self.assertIn("SOURCE_NATIVE_DATE_ONLY",cv["publication_time_semantics"])
        self.assertIn("BIKRAM_SAMBAT_NEPAL",cv["native_calendar_system"])
        self.assertIn("UNRESOLVED_AUTHORITATIVE_CONVERSION",cv["gregorian_resolution_status"])
        self.assertIn("BUDGET_PRESENTATION",cv["fiscal_process_milestone_type"])
        for field in self.plan["schema_additions"]["timing_fields"]:
            self.assertIn(field,schema["event_occurrence_fields"]["timing"])

    def test_no_third_party_converter_or_synthetic_gregorian_date_in_plan(self):
        text=PLAN_PATH.read_text(encoding="utf-8")+"\n"+self.research
        lower=text.lower()
        self.assertNotIn("hamropatro",lower)
        self.assertNotIn("nepalicalendar",lower)
        self.assertNotIn("2027-05-29",text)
        self.assertIn("third-party",lower)
        self.assertIn("no gregorian date is inferred",lower)

    def test_physical_risk_hold_remains_explicit(self):
        hold=self.plan["holds"][0]
        self.assertEqual(hold["status"],"HOLD_OFFICIAL_DEFINITION_CONFLICT")
        self.assertIn("North Indian Ocean",hold["candidate"])
        self.assertIn("conflict",hold["reason"].lower())

    def test_global_write_gates_remain_closed(self):
        post=self.plan["postconditions"]
        self.assertFalse(post["automatic_canonical_commit"])
        self.assertFalse(post["google_calendar_write"])

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate mutation test is exercised only from exact pre-state")
        paths=(SCHEMA_PATH,CANONICAL_PATH,SOURCES_PATH,LEDGER_PATH,EXPECTATIONS_PATH)
        before={path:path.read_bytes() for path in paths}
        env=dict(os.environ)
        env.pop(TX.APPLY_ENV,None)
        proc=subprocess.run([sys.executable,str(MODULE_PATH),"--apply"],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertNotEqual(proc.returncode,0)
        self.assertIn("APPLY BLOCKED",proc.stdout+proc.stderr)
        for path,raw in before.items():
            self.assertEqual(path.read_bytes(),raw)


if __name__=="__main__":
    unittest.main()
