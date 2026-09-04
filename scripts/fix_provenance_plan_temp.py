from pathlib import Path
import json
p=Path('data/coverage/PROVENANCE_SCOPE_REPAIR_A_PLAN_v0.1.json')
data=json.loads(p.read_text(encoding='utf-8'))
row=data['preconditions']['brazil_inauguration']
rename={
'expected_source_id':'source_id',
'expected_institution':'institution',
'expected_election_date_basis':'election_date_basis',
'expected_start_local':'start_local',
'expected_primary_source_assertion_id':'primary_source_assertion_id',
'expected_last_successful_assertion_id':'last_successful_assertion_id',
}
for old,new in rename.items():
    row[new]=row.pop(old)
p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
