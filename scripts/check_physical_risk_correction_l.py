#!/usr/bin/env python3
from __future__ import annotations

import copy, hashlib, json
from pathlib import Path

from src.world_signals.validation import validate_registry

ROOT=Path(__file__).resolve().parents[1]
load=lambda p: json.loads((ROOT/p).read_text(encoding='utf-8'))


def aid(item:dict)->str:
    material='|'.join(str(item.get(k) or '') for k in ('occurrence_id','series_id','source_id','canonical_name','source_native_window_label'))
    return 'WSA-'+hashlib.sha256(material.encode()).hexdigest()[:16]


def build_occurrence(item:dict)->dict:
    assertion=aid(item)
    return {
      'occurrence_id':item['occurrence_id'],'series_id':item['series_id'],'external_source_id':None,
      'canonical_name':item['canonical_name'],'short_calendar_title':'SW Pacific tropical cyclone season 2026–27',
      'category':'PHYSICAL_CLIMATE_RISK','subcategory':'tropical_cyclone_risk_window',
      'jurisdiction':'South-West Pacific / RSMC Nadi area of responsibility','region':'Oceania / Pacific',
      'institution':'Fiji Meteorological and Hydrological Services / RSMC Nadi Tropical Cyclone Centre',
      'event_type':'PHYSICAL_RISK_WINDOW','record_class':'OCCURRENCE','certainty_status':'CONFIRMED',
      'activation_mode':'AUTHORITATIVE_RECURRING_RULE','lifecycle_status':'PLANNED',
      'condition_state':'NOT_REQUIRED','condition_description':None,'trigger_source_id':None,
      'trigger_assertion_id':None,'triggered_at':None,'trigger_verification_status':'NOT_APPLICABLE',
      'timing_type':'MONTH_BOUNDED_SEASON_WINDOW','season_window_model':'MONTH_BOUNDED_SINGLE_PHASE',
      'season_phases':copy.deepcopy(item['season_phases']),'source_native_window_label':item['source_native_window_label'],
      'start_local':None,'end_local':None,'source_timezone':None,'start_utc':None,'end_utc':None,
      'date_earliest':None,'date_latest':None,'publication_datetime':None,'time_precision':'MONTH',
      'all_day_semantics':False,'reference_period':'2026–27 tropical cyclone season',
      'time_status':'NOT_APPLICABLE','time_basis':'NOT_APPLICABLE','source_id':item['source_id'],
      'primary_source_assertion_id':assertion,'last_successful_assertion_id':assertion,
      'status_history':[{'as_of':'2026-09-04','certainty_status':'CONFIRMED','lifecycle_status':'PLANNED'}],
      'first_announced_at':None,'first_discovered_at':'2026-09-03','last_verified_at':'2026-09-04',
      'next_verification_due':'SOURCE_SPECIFIC','parent_occurrence_id':None,'related_occurrence_ids':[],
      'related_documents':[],'intrinsic_importance':'MEDIUM_HIGH','expected_market_sensitivity':'LOW',
      'geopolitical_sensitivity':'LOW','transmission_channels':['shipping_logistics','tourism','insurance','food_supply','energy_infrastructure','critical_infrastructure','trade','fiscal_risk'],
      'render_policy':'INCLUDE','visibility_tier':'BACKGROUND','signal_object_class':'PHYSICAL_RISK_WINDOW',
      'publication_time_semantics':'SEASONAL_MONTH_RANGE','physical_shock_routing':'ROUTE_ACTUAL_EVENT_TO_SHOCK_REGISTER',
      'observed_market_response':None,'expected_market_sensitivity_basis':'Structural exposure context, not a discrete market catalyst; actual cyclones are separate Shock/Live Intelligence objects.',
      'publication_bundle_type':'NOT_APPLICABLE','render_cluster_key':None,'calendar_aggregation_policy':'STANDALONE_WINDOW_RAIL',
      'coverage_program_id':'WSCP-PHYSICAL-RISK-CORRECTION-L','coverage_repair_reason':'PACIFIC_PHYSICAL_RISK_REGIONAL_COVERAGE_AND_MONTH_PRECISION_ONTOLOGY_SAMPLE',
      'population_horizon_policy':'CURRENT_RELEVANT_RECURRING_CYCLE_ONLY',
      'selection_rationale':'One current relevant structural season only; no synthetic civil-day boundaries or unlocated 2026–27 activity forecast.',
      'notes':'Standing structural exposure window only. Cyclones can occur outside November–April; no cyclone-count forecast is stored here.'
    }


def main()->int:
    reg=load('data/canonical/registry.json'); src=load('data/sources/registry.json')
    schema=load('data/canonical/schema.json'); plan=load('data/coverage/PHYSICAL_RISK_CORRECTION_L_PLAN_v0.1.json')
    pre=plan['preconditions']; post=plan['postconditions']; errors=[]
    if (str(reg.get('version')),reg.get('record_count'),len(reg.get('records',[]))) != (pre['canonical_registry_version'],668,668): errors.append('canonical checkpoint mismatch')
    if str(src.get('version'))!=pre['source_registry_version'] or len(src.get('sources',[]))!=221: errors.append('source checkpoint mismatch')
    if str(schema.get('version'))!=pre['schema_version']: errors.append('schema checkpoint mismatch')
    oids={r.get('occurrence_id') for r in reg['records']}; series={r.get('series_id') for r in reg['records']}; sids={s.get('source_id') for s in src['sources']}
    if any(x in oids for x in pre['required_absent_occurrence_ids']): errors.append('planned occurrence identity already exists')
    if any(x in series for x in pre['required_absent_series_ids']): errors.append('planned series identity already exists')
    if any(x in sids for x in pre['required_absent_source_ids']): errors.append('planned source identity already exists')
    if any(str(x or '').startswith('WSO-RISK-') for x in oids): errors.append('dedicated WSO-RISK namespace no longer empty')
    if len(plan['occurrences'])!=1 or len(plan['source_plan'])!=1 or len(plan['series'])!=1: errors.append('Correction L must remain a one-occurrence sample')
    deferred=plan['deferred_candidates']; texts={x['assertion'] for x in deferred[0]['assertions']} if len(deferred)==1 else set()
    if len(deferred)!=1 or deferred[0].get('state')!='OFFICIAL_SOURCE_DEFINITION_CONFLICT' or len(texts)!=2 or not any('April-June' in x for x in texts) or not any('April-May' in x for x in texts): errors.append('IMD official-source conflict was weakened or lost')
    cv=schema['controlled_vocabularies']
    if 'SEASONAL_MONTH_RANGE' not in cv['publication_time_semantics'] or 'MONTH_BOUNDED_SEASON_WINDOW' not in cv['timing_type']: errors.append('month-native ontology not ready')
    if errors: raise SystemExit('PRECONDITION FAILED:\n- '+'\n- '.join(errors))

    clone=copy.deepcopy(reg); sclone=copy.deepcopy(src)
    source=copy.deepcopy(plan['source_plan'][0]); occurrence=build_occurrence(plan['occurrences'][0])
    sclone['sources'].append(source); sclone['version']=post['source_registry_version']; sclone['reference_date']='2026-09-04'
    clone['records'].append(occurrence); clone['version']=post['canonical_registry_version']; clone['record_count']=len(clone['records']); clone['reference_date']='2026-09-04'

    checks=[
      (clone['record_count']==669,'canonical clone must contain 669 records'),
      (len(sclone['sources'])==222,'source clone must contain 222 sources'),
      (occurrence['publication_time_semantics']=='SEASONAL_MONTH_RANGE','seasonal month semantic changed'),
      (occurrence['activation_mode']=='AUTHORITATIVE_RECURRING_RULE','activation mode changed'),
      (occurrence['lifecycle_status']=='PLANNED','lifecycle changed'),
      (occurrence['season_phases']==[{'phase_id':'PHASE_1','start_month':'2026-11','end_month':'2027-04','boundary_precision':'MONTH','source_label':'November–April'}],'Fiji phase changed'),
      (all(occurrence[k] is None for k in ('start_local','end_local','start_utc','end_utc','date_earliest','date_latest','publication_datetime')),'synthetic exact/day timing present'),
      (source['canonical_provenance_use']=='MANUAL_INFORMATIONAL_REFERENCE_ONLY','canonical provenance rights changed'),
      (source['automated_monitoring_use']=='PROHIBITED_OR_RIGHTS_HOLD','automation rights hold changed'),
      (source['verification_mode']=='RIGHTS_HELD_MANUAL_ONLY','verification mode changed'),
      (not any(r.get('series_id')=='WSER-RISK-NIO-TC' for r in clone['records']),'IMD leaked into canonical clone'),
      (not any(s.get('source_id')=='WSSRC-RISK-005' for s in sclone['sources']),'IMD leaked into source clone'),
      (post['automatic_canonical_commit'] is False and post['google_calendar_write'] is False and post['scheduled_live_monitor_change'] is False,'safety postconditions changed')
    ]
    errors=[msg for ok,msg in checks if not ok]
    report=validate_registry(clone,sclone)
    errors.extend(report.errors)
    if errors: raise SystemExit('POSTCONDITION FAILED:\n- '+'\n- '.join(errors))
    print(json.dumps({'status':'PASS','mode':'CHECK_ONLY','canonical':'0.19/668 -> 0.20/669','sources':'1.50/221 -> 1.51/222','admit':['WSO-RISK-A-0001'],'defer':['WSFR-RISK-NIO-TC'],'automatic_canonical_commit':False,'google_calendar_write':False,'validator_warnings':len(report.warnings)},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
