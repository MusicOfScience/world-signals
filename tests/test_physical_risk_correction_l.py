from pathlib import Path
import importlib.util, json, unittest

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'data/coverage/PHYSICAL_RISK_CORRECTION_L_PLAN_v0.1.json').read_text(encoding='utf-8'))
SPEC=importlib.util.spec_from_file_location('correction_l',ROOT/'scripts/check_physical_risk_correction_l.py')
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class PhysicalRiskCorrectionLTests(unittest.TestCase):
    def test_scope_is_one_fiji_occurrence_not_cosmetic_pair_filling(self):
        self.assertEqual(len(PLAN['occurrences']),1)
        self.assertEqual(len(PLAN['series']),1)
        self.assertEqual(len(PLAN['source_plan']),1)
        self.assertEqual(PLAN['occurrences'][0]['occurrence_id'],'WSO-RISK-A-0001')
        self.assertEqual(PLAN['occurrences'][0]['series_id'],'WSER-RISK-SWP-TC')
        self.assertEqual(PLAN['source_plan'][0]['source_id'],'WSSRC-RISK-004')

    def test_imd_remains_deferred_official_source_conflict(self):
        self.assertEqual(len(PLAN['deferred_candidates']),1)
        item=PLAN['deferred_candidates'][0]
        self.assertEqual(item['candidate_id'],'WSFR-RISK-NIO-TC')
        self.assertEqual(item['state'],'OFFICIAL_SOURCE_DEFINITION_CONFLICT')
        assertions={x['assertion'] for x in item['assertions']}
        self.assertTrue(any('April-June' in x for x in assertions))
        self.assertTrue(any('April-May' in x for x in assertions))
        self.assertNotIn('WSER-RISK-NIO-TC',{x['series_id'] for x in PLAN['occurrences']})
        self.assertEqual(item['provisional_region'],'Cross-regional / Global')

    def test_fiji_occurrence_uses_month_native_semantics_only(self):
        occurrence=MOD.build_occurrence(PLAN['occurrences'][0])
        self.assertEqual(occurrence['timing_type'],'MONTH_BOUNDED_SEASON_WINDOW')
        self.assertEqual(occurrence['publication_time_semantics'],'SEASONAL_MONTH_RANGE')
        self.assertEqual(occurrence['time_precision'],'MONTH')
        self.assertEqual(occurrence['source_native_window_label'],'November–April')
        self.assertEqual(occurrence['season_phases'],[{
            'phase_id':'PHASE_1','start_month':'2026-11','end_month':'2027-04',
            'boundary_precision':'MONTH','source_label':'November–April'
        }])
        for field in ('start_local','end_local','start_utc','end_utc','date_earliest','date_latest','publication_datetime'):
            self.assertIsNone(occurrence[field],field)

    def test_fiji_source_is_manual_provenance_with_automation_hold(self):
        source=PLAN['source_plan'][0]
        self.assertEqual(source['canonical_provenance_use'],'MANUAL_INFORMATIONAL_REFERENCE_ONLY')
        self.assertEqual(source['automated_monitoring_use'],'PROHIBITED_OR_RIGHTS_HOLD')
        self.assertEqual(source['verification_mode'],'RIGHTS_HELD_MANUAL_ONLY')
        self.assertEqual(source['monitoring_readiness_status'],'RIGHTS_OR_LICENSE_HOLD')

    def test_postconditions_keep_writes_and_live_monitor_changes_off(self):
        post=PLAN['postconditions']
        self.assertEqual(post['canonical_record_count'],669)
        self.assertEqual(post['source_registry_count'],222)
        self.assertFalse(post['automatic_canonical_commit'])
        self.assertFalse(post['google_calendar_write'])
        self.assertFalse(post['scheduled_live_monitor_change'])

if __name__=='__main__': unittest.main()
