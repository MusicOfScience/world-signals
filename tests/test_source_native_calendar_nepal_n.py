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
OVERLAY_PATH=ROOT/"data/coverage/biosecurity_overlay.json"
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
        cls.overlay=json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))

    def _is_pre(self):
        return (
            self.schema.get("version")=="0.51"
            and self.canonical.get("version")=="0.27"
            and len(self.canonical.get("records",[]))==673
            and self.sources.get("version")=="1.68"
            and len(self.sources.get("sources",[]))==231
            and self.overlay.get("version")=="0.2"
            and self.overlay.get("canonical_checkpoint")=={"registry_version":"0.27","record_count":673}
        )

    @staticmethod
    def _version_at_least(value, floor):
        try:
            current=tuple(int(x) for x in str(value).split("."))
            minimum=tuple(int(x) for x in str(floor).split("."))
        except ValueError:
            return False
        width=max(len(current),len(minimum))
        return current+(0,)*(width-len(current)) >= minimum+(0,)*(width-len(minimum))

    def _is_post(self):
        oids={r.get("occurrence_id") for r in self.canonical.get("records",[])}
        source_ids={r.get("source_id") for r in self.sources.get("sources",[])}
        timing_vocab=(self.schema.get("controlled_vocabularies") or {}).get("timing_type",[])
        checkpoint=self.overlay.get("canonical_checkpoint")
        return (
            self._version_at_least(self.schema.get("version"),"0.52")
            and self._version_at_least(self.canonical.get("version"),"0.28")
            and len(self.canonical.get("records",[]))>=674
            and self._version_at_least(self.sources.get("version"),"1.69")
            and len(self.sources.get("sources",[]))>=233
            and self._version_at_least(self.overlay.get("version"),"0.3")
            and checkpoint=={
                "registry_version":self.canonical.get("version"),
                "record_count":len(self.canonical.get("records",[])),
            }
            and "WSO-FIS-NP-BUDGET-2084" in oids
            and {"WSSRC-FIS-026","WSSRC-FIS-027"}.issubset(source_ids)
            and "SOURCE_NATIVE_CALENDAR_DATE" in timing_vocab
        )

    def _post_objects(self):
        if self._is_pre():
            TX.preflight(self.schema,self.canonical,self.sources,self.overlay,self.plan)
            schema,canonical,sources,overlay,_=TX.build_post_state(self.schema,self.canonical,self.sources,self.overlay,self.plan)
            return schema,canonical,sources,overlay
        if self._is_post():
            return self.schema,self.canonical,self.sources,self.overlay
        self.fail("repository is neither exact Nepal N pre-state nor reviewed post-state")

    def test_repository_is_exact_pre_or_post_state(self):
        self.assertTrue(self._is_pre() or self._is_post())
        schema,canonical,sources,overlay=self._post_objects()
        self.assertTrue(self._version_at_least(schema["version"],"0.52"))
        self.assertTrue(self._version_at_least(canonical["version"],"0.28"))
        self.assertGreaterEqual(len(canonical["records"]),674)
        self.assertTrue(self._version_at_least(sources["version"],"1.69"))
        self.assertGreaterEqual(len(sources["sources"]),233)
        self.assertTrue(self._version_at_least(overlay["version"],"0.3"))
        self.assertEqual(
            overlay["canonical_checkpoint"],
            {"registry_version":canonical["version"],"record_count":len(canonical["records"])},
        )

    def test_scope_is_one_series_one_occurrence_two_sources(self):
        self.assertEqual(self.plan["preconditions"]["required_absent_series_ids"],["WSER-FIS-NP-FEDERAL-BUDGET"])
        self.assertEqual(self.plan["preconditions"]["required_absent_occurrence_ids"],["WSO-FIS-NP-BUDGET-2084"])
        self.assertEqual([s["source_id"] for s in self.plan["sources"]],["WSSRC-FIS-026","WSSRC-FIS-027"])

    def test_overlay_alignment_changes_only_version_and_checkpoint(self):
        if self._is_pre():
            _,_,_,post_overlay,_=TX.build_post_state(self.schema,self.canonical,self.sources,self.overlay,self.plan)
            self.assertEqual(TX.overlay_semantic_payload(post_overlay),TX.overlay_semantic_payload(self.overlay))
            self.assertEqual(post_overlay["version"],"0.3")
            self.assertEqual(post_overlay["canonical_checkpoint"],{"registry_version":"0.28","record_count":674})
        else:
            self.assertTrue(self._version_at_least(self.overlay["version"],"0.3"))
            self.assertEqual(
                self.overlay["canonical_checkpoint"],
                {"registry_version":self.canonical["version"],"record_count":len(self.canonical["records"])},
            )
        memberships={r["series_id"] for r in self.overlay["canonical_series_memberships"]}
        self.assertNotIn("WSER-FIS-NP-FEDERAL-BUDGET",memberships)

    def test_nepal_is_exact_native_date_and_gregorian_fields_are_empty(self):
        _,canonical,_,_=self._post_objects()
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
        _,canonical,_,_=self._post_objects()
        row=next(r for r in canonical["records"] if r.get("occurrence_id")=="WSO-FIS-NP-BUDGET-2084")
        self.assertEqual(row["category"],"FISCAL_SOVEREIGN_FINANCE")
        self.assertEqual(row["subcategory"],"national_budget")
        self.assertEqual(row["event_type"],"FISCAL_POLICY_PROCESS")
        self.assertEqual(row["fiscal_process_milestone_type"],"BUDGET_PRESENTATION")
        self.assertIsNone(row["deadline_type"])
        self.assertIsNone(row["deadline_semantics"])

    def test_legal_authority_and_publication_source_are_separated(self):
        _,canonical,sources,_=self._post_objects()
        row=next(r for r in canonical["records"] if r.get("occurrence_id")=="WSO-FIS-NP-BUDGET-2084")
        self.assertEqual(row["source_id"],"WSSRC-FIS-026")
        self.assertEqual(row["legal_basis_source_id"],"WSSRC-FIS-026")
        self.assertIn("WSSRC-FIS-027",row["derivation_sources"])
        by_id={s["source_id"]:s for s in sources["sources"]}
        self.assertEqual(by_id["WSSRC-FIS-026"]["canonical_provenance_use"],"PRIMARY")
        self.assertEqual(by_id["WSSRC-FIS-027"]["canonical_provenance_use"],"SUPPORTING")
        self.assertEqual(by_id["WSSRC-FIS-026"]["automated_monitoring_use"],"HOLD")
        self.assertEqual(by_id["WSSRC-FIS-027"]["automated_monitoring_use"],"HOLD")

    def test_sources_are_manual_provenance_not_automation_permission(self):
        _,_,sources,_=self._post_objects()
        by_id={s["source_id"]:s for s in sources["sources"]}
        for source_id in ("WSSRC-FIS-026","WSSRC-FIS-027"):
            row=by_id[source_id]
            self.assertEqual(row["verification_mode"],"RIGHT_HELD_MANUAL_ONLY")
            self.assertEqual(row["automated_monitoring_use"],"HOLD")
            self.assertIn("NO_UNRESTRICTED",row["licence_constraints"])

    def test_schema_support_is_reusable_not_nepal_date_conversion(self):
        schema,_,_,_=self._post_objects()
        vocab=schema["controlled_vocabularies"]
        self.assertIn("SOURCE_NATIVE_CALENDAR_DATE",vocab["timing_type"])
        self.assertIn("SOURCE_NATIVE_DATE_ONLY",vocab["publication_time_semantics"])
        self.assertIn("BIKRAM_SAMBAT_NEPAL",vocab["native_calendar_system"])
        self.assertIn("UNRESOLVED_AUTHORITATIVE_CONVERSION",vocab["gregorian_resolution_status"])
        self.assertIn("BUDGET_PRESENTATION",vocab["fiscal_process_milestone_type"])
        self.assertNotIn("2027-05-29",json.dumps(schema))

    def test_no_third_party_converter_or_synthetic_gregorian_date_in_plan(self):
        text=json.dumps(self.plan).lower()
        self.assertNotIn("hamropatro",text)
        self.assertNotIn("nepalicalendar",text)
        self.assertNotIn("2027-05-29",text)
        self.assertEqual(self.plan["occurrence"]["gregorian_resolution_status"],"UNRESOLVED_AUTHORITATIVE_CONVERSION")

    def test_physical_risk_hold_remains_explicit(self):
        self.assertIn("HOLD_OFFICIAL_DEFINITION_CONFLICT",self.research)
        self.assertIn("North Indian Ocean",self.research)

    def test_global_write_gates_remain_closed(self):
        expectations=json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))
        self.assertFalse(expectations["automatic_canonical_commit"])
        self.assertFalse(expectations["google_calendar_write"])

    def test_apply_without_environment_gate_never_writes(self):
        if not self._is_pre():
            self.skipTest("apply-gate mutation test is exercised only from exact pre-state")
        before={p:p.read_bytes() for p in (SCHEMA_PATH,CANONICAL_PATH,SOURCES_PATH,OVERLAY_PATH)}
        env=os.environ.copy()
        env.pop("WORLD_SIGNALS_APPLY_NATIVE_CALENDAR_N",None)
        result=subprocess.run(
            [sys.executable,str(MODULE_PATH),"--apply"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode,0)
        self.assertIn("APPLY BLOCKED",result.stderr+result.stdout)
        after={p:p.read_bytes() for p in before}
        self.assertEqual(before,after)


if __name__=="__main__":
    unittest.main()
