(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const human = value => String(value ?? '').replaceAll('_',' ').toLowerCase();
  let loaded = false;
  let DATA = null;
  let REVIEW_DATA = null;

  function recordedTime(raw){
    if(!raw) return 'no timestamp embedded';
    const d=new Date(raw);
    return Number.isNaN(d.getTime())?String(raw):d.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
  }

  function statusToken(raw){
    return raw || 'NOT_RECORDED_IN_REGISTRY';
  }

  function renderSummaryBlock(title, values){
    const entries=Object.entries(values||{});
    return `<section class="ops-summary-block"><h4>${esc(title)}</h4>${entries.length?`<div class="ops-summary-list">${entries.map(([key,count])=>`<div><span>${esc(human(key))}</span><b>${esc(count)}</b></div>`).join('')}</div>`:'<p class="empty">No values recorded.</p>'}</section>`;
  }

  function renderRoute(route){
    const evidence=route.last_recorded_evidence_at
      ? `<strong>${esc(recordedTime(route.last_recorded_evidence_at))}</strong><span>latest timestamp embedded in repository baseline/configuration</span>`
      : `<strong>No embedded timestamp</strong><span>configuration exists, but this static projection carries no baseline observation time</span>`;
    return `<article class="ops-route-card">
      <div class="ops-card-head">
        <div><p class="eyebrow">${esc(route.adapter_id)}</p><h3>${esc(route.source_institution||route.source_id)}</h3><p class="meta">${esc(route.jurisdiction||'jurisdiction not recorded')} · ${esc(route.domain||'domain not recorded')}</p></div>
        <span class="ops-static-badge">RECORDED ≠ LIVE</span>
      </div>
      <div class="ops-evidence-time">${evidence}</div>
      <dl class="ops-route-values">
        <dt>Role</dt><dd>${esc(human(route.monitor_role||'not recorded'))}</dd>
        <dt>Cadence</dt><dd>${esc(human(route.cadence||'not recorded'))}</dd>
        <dt>Canonical scope</dt><dd>${(route.canonical_occurrence_ids||[]).map(id=>`<code>${esc(id)}</code>`).join(' ')||'None'}</dd>
        <dt>Canonical provenance</dt><dd>${esc(human(statusToken(route.canonical_provenance_use)))}</dd>
        <dt>Automated monitoring</dt><dd>${esc(human(statusToken(route.automated_monitoring_use)))}</dd>
        <dt>Registry readiness</dt><dd>${esc(human(statusToken(route.monitoring_readiness_status)))}</dd>
      </dl>
    </article>`;
  }

  function sourceCard(source){
    const url=source.authoritative_url?`<a href="${esc(source.authoritative_url)}" target="_blank" rel="noreferrer">authoritative source ↗</a>`:'';
    return `<article class="ops-source-card">
      <div><p class="eyebrow"><code>${esc(source.source_id)}</code></p><h4>${esc(source.institution||'Institution not recorded')}</h4><p class="meta">${esc(source.jurisdiction||'jurisdiction not recorded')} · ${esc(source.domain||'domain not recorded')}</p></div>
      <div class="ops-source-statuses">
        <span><b>Provenance</b>${esc(human(statusToken(source.canonical_provenance_use)))}</span>
        <span><b>Automation</b>${esc(human(statusToken(source.automated_monitoring_use)))}</span>
        <span><b>Readiness</b>${esc(human(statusToken(source.monitoring_readiness_status)))}</span>
      </div>
      <div class="ops-source-foot"><span>rights reviewed: ${esc(source.rights_reviewed_at||'not recorded')}</span><span>research verified: ${esc(source.last_successful_research_verification_at||'not recorded')}</span>${url}</div>
    </article>`;
  }

  function renderSources(){
    if(!DATA) return;
    const query=(document.querySelector('#opsSourceSearch').value||'').trim().toLowerCase();
    const automation=document.querySelector('#opsAutomationFilter').value;
    const rows=(DATA.sources||[]).filter(source=>{
      const token=statusToken(source.automated_monitoring_use);
      const hay=[source.source_id,source.institution,source.jurisdiction,source.domain,source.source_type,source.monitoring_readiness_status,source.canonical_provenance_use,token].join(' ').toLowerCase();
      return (!query||hay.includes(query))&&(!automation||token===automation);
    });
    document.querySelector('#opsSourceCount').textContent=`${rows.length} of ${DATA.metadata.source_count} source records`;
    document.querySelector('#opsSources').innerHTML=rows.length?rows.map(sourceCard).join(''):'<p class="empty">No sources match the current filter.</p>';
  }

  function renderRuntimeHealth(health){
    return `<article class="ops-runtime-health-card">
      <div><p class="eyebrow">${esc(health.adapter_id||'adapter')}</p><h4>${esc(health.source_id||'source not recorded')}</h4></div>
      <span class="ops-health-state ops-health-${esc(String(health.state||'UNKNOWN').toLowerCase())}">${esc(human(health.state||'UNKNOWN'))}</span>
      ${(health.layer_states||[]).length?`<div class="ops-layer-list">${health.layer_states.map(layer=>`<span><b>${esc(human(layer.layer))}</b>${esc(human(layer.state||'unknown'))}${layer.failure_stage?` · ${esc(human(layer.failure_stage))}`:''}</span>`).join('')}</div>`:''}
    </article>`;
  }

  function renderRuntimeCandidate(candidate){
    return `<article class="ops-runtime-candidate">
      <div class="ops-card-head"><div><p class="eyebrow">${esc(human(candidate.candidate_type||'review candidate'))}</p><h4><code>${esc(candidate.candidate_id)}</code></h4></div><span class="ops-static-badge">REVIEW ONLY</span></div>
      <dl class="ops-route-values">
        <dt>Source</dt><dd><code>${esc(candidate.source_id||'not recorded')}</code></dd>
        <dt>Occurrence scope</dt><dd>${(candidate.occurrence_ids||[]).map(id=>`<code>${esc(id)}</code>`).join(' ')||'None'}</dd>
        <dt>Review state</dt><dd>${esc(human(candidate.review_state||'pending review'))}</dd>
        <dt>Changed fields</dt><dd>${(candidate.changed_fields||[]).map(field=>`<code>${esc(field)}</code>`).join(' ')||'Not represented as field diff'}</dd>
        <dt>Automatic commit</dt><dd>OFF</dd>
      </dl>
    </article>`;
  }

  function renderRuntime(runtime){
    const summary=document.querySelector('#opsRuntimeSummary');
    const health=document.querySelector('#opsRuntimeHealth');
    const candidates=document.querySelector('#opsRuntimeCandidates');
    const candidateCount=document.querySelector('#opsRuntimeCandidateCount');

    if(!runtime||runtime.availability!=='AVAILABLE'){
      summary.innerHTML=`<article class="ops-runtime-unavailable"><p class="eyebrow">NO RETAINED SNAPSHOT EMBEDDED</p><h3>Runtime evidence unavailable in this build</h3><p>${esc(human(runtime?.reason||'runtime projection unavailable'))}.</p><p class="meta">This does not imply source failure, monitor failure or event change.</p></article>`;
      health.innerHTML='';
      candidates.innerHTML='<p class="empty">No run-generated candidate snapshot is embedded.</p>';
      candidateCount.textContent='0 embedded candidates';
      return;
    }

    const alignment=runtime.configuration_alignment||{};
    const fields=Object.entries(alignment.fields||{});
    const mismatches=fields.filter(([,value])=>!value.matches);
    const executionMode=runtime.execution_mode||'UNSPECIFIED';
    const runLabel=executionMode==='GITHUB_ACTIONS'?'GitHub run':'Local run';
    const runIdentity=runtime.run_id||runtime.github_run_id||'not recorded';
    summary.innerHTML=`<article class="ops-runtime-run">
      <div class="ops-card-head"><div><p class="eyebrow">${esc(human(runtime.status||'unknown'))}</p><h3>${esc(recordedTime(runtime.run_at))}</h3><p class="meta">${esc(runLabel)} <code>${esc(runIdentity)}</code> · ${esc(human(executionMode))} · report schema ${esc(runtime.report_schema_version||'?')}</p></div><span class="ops-runtime-status">${esc(human(alignment.state||'alignment unknown'))}</span></div>
      <div class="ops-runtime-metrics"><span><b>${esc(runtime.healthy_adapter_count)}</b>healthy adapters</span><span><b>${esc(runtime.degraded_adapter_count)}</b>degraded adapters</span><span><b>${esc(runtime.candidate_count)}</b>review candidates</span><span><b>${runtime.canonical_unchanged?'YES':'NO'}</b>canonical unchanged</span></div>
      ${mismatches.length?`<div class="ops-alignment-warning"><strong>This retained run used an older configuration than the current site.</strong>${mismatches.map(([key,value])=>`<span>${esc(human(key))}: run ${esc(value.run)} · current ${esc(value.current)}</span>`).join('')}</div>`:'<p class="ops-alignment-ok">Run configuration matches the current canonical/source/monitor contract versions.</p>'}
      <p class="meta">This is a dated observation snapshot. It is not a claim that the sources remain in these states now.</p>
    </article>`;

    health.innerHTML=(runtime.source_health||[]).length?runtime.source_health.map(renderRuntimeHealth).join(''):'<p class="empty">No source-health summary was published for this run.</p>';
    const rows=runtime.candidates||[];
    candidateCount.textContent=`${rows.length} candidate${rows.length===1?'':'s'} in this run`;
    candidates.innerHTML=rows.length?rows.map(renderRuntimeCandidate).join(''):'<p class="empty">This retained run generated no review candidates.</p>';
  }

  function renderReviewItem(item){
    const decision=item.last_decision_state?`${human(item.last_decision_state)} · ${recordedTime(item.decided_at)}`:'none recorded';
    return `<article class="ops-review-item">
      <div class="ops-card-head">
        <div><p class="eyebrow">${esc(human(item.identity_mode||'review proposition'))}</p><h4><code>${esc(item.review_item_id)}</code></h4></div>
        <span class="ops-review-state ops-review-${esc(String(item.state||'unknown').toLowerCase())}">${esc(human(item.state||'unknown'))}</span>
      </div>
      <div class="ops-review-routing"><span><b>Attention</b>${esc(human(item.operator_attention_class||'not classified'))}</span><span><b>Next controlled step</b>${esc(human(item.operator_next_action||'not recorded'))}</span></div>
      <div class="ops-review-observation"><strong>${esc(item.observation_count||0)} observation${item.observation_count===1?'':'s'}</strong><span>first ${esc(recordedTime(item.first_observed_at))} · last ${esc(recordedTime(item.last_observed_at))}</span></div>
      <dl class="ops-route-values">
        <dt>Occurrence scope</dt><dd>${(item.occurrence_ids||[]).map(id=>`<code>${esc(id)}</code>`).join(' ')||'None'}</dd>
        <dt>Candidate types</dt><dd>${(item.candidate_types||[]).map(value=>`<code>${esc(value)}</code>`).join(' ')||'None'}</dd>
        <dt>Sources</dt><dd>${(item.source_ids||[]).map(value=>`<code>${esc(value)}</code>`).join(' ')||'Not recorded'}</dd>
        <dt>Evidence objects</dt><dd>${(item.candidate_ids||[]).map(value=>`<code>${esc(value)}</code>`).join(' ')||'Not recorded'}</dd>
        <dt>Proposed fields</dt><dd>${(item.proposed_change_fields||[]).map(value=>`<code>${esc(value)}</code>`).join(' ')||'None'}</dd>
        <dt>Recurrence</dt><dd>${esc(human(item.recurrence_state||'not recorded'))}</dd>
        <dt>Canonical alignment</dt><dd>${esc(human(item.canonical_alignment_state||'not evaluated'))}</dd>
        <dt>Last decision</dt><dd>${esc(decision)}</dd>
        <dt>Reobserved after decision</dt><dd>${item.reobserved_after_decision?'YES':'NO'}</dd>
        <dt>Automatic commit</dt><dd>OFF</dd>
      </dl>
    </article>`;
  }

  function renderReviewItems(){
    if(!REVIEW_DATA) return;
    const query=(document.querySelector('#opsReviewSearch').value||'').trim().toLowerCase();
    const state=document.querySelector('#opsReviewStateFilter').value;
    const attention=document.querySelector('#opsReviewAttentionFilter').value;
    const order=document.querySelector('#opsReviewSort').value;
    const attentionOrder={RECONCILIATION_REQUIRED:0,COMMIT_HANDOFF_REQUIRED:1,REOBSERVED_AFTER_DECISION:2,REPEATED_DECISION_REQUIRED:3,DECISION_REQUIRED:4,NO_ACTIVE_ACTION:5};
    const rows=(REVIEW_DATA.items||[]).filter(item=>{
      const hay=[item.review_item_id,item.identity_mode,item.state,item.operator_attention_class,item.operator_next_action,...(item.occurrence_ids||[]),...(item.candidate_types||[]),...(item.source_ids||[]),...(item.candidate_ids||[]),...(item.proposed_change_fields||[])].join(' ').toLowerCase();
      return (!query||hay.includes(query))&&(!state||item.state===state)&&(!attention||item.operator_attention_class===attention);
    });
    rows.sort((a,b)=>{
      if(order==='latest') return String(b.last_observed_at||'').localeCompare(String(a.last_observed_at||''))||String(a.review_item_id).localeCompare(String(b.review_item_id));
      if(order==='recurrence') return Number(b.observation_count||0)-Number(a.observation_count||0)||String(b.last_observed_at||'').localeCompare(String(a.last_observed_at||''));
      return (attentionOrder[a.operator_attention_class]??99)-(attentionOrder[b.operator_attention_class]??99)||String(b.last_observed_at||'').localeCompare(String(a.last_observed_at||''));
    });
    document.querySelector('#opsReviewCount').textContent=`${rows.length} of ${REVIEW_DATA.item_count||0} review items`;
    document.querySelector('#opsReviewItems').innerHTML=rows.length?rows.map(renderReviewItem).join(''):'<p class="empty">No retained review items match the current filters.</p>';
  }

  function renderReviewState(review){
    const summary=document.querySelector('#opsReviewSummary');
    const count=document.querySelector('#opsReviewCount');
    const localHorizon=review?.availability==='AVAILABLE_LOCAL_HORIZON';
    if(!review||(review.availability!=='AVAILABLE_RETAINED_HORIZON'&&!localHorizon)){
      REVIEW_DATA=null;
      count.textContent='review horizon unavailable';
      summary.innerHTML=`<article class="ops-runtime-unavailable"><p class="eyebrow">RETAINED REVIEW STATE UNAVAILABLE</p><h3>No complete retained-horizon projection in this build</h3><p>${esc(human(review?.availability||'review state unavailable'))}.</p><p class="meta">This is not interpreted as an empty review queue.</p></article>`;
      document.querySelector('#opsReviewItems').innerHTML='';
      return;
    }
    REVIEW_DATA=review;
    const stateEntries=Object.entries(review.state_counts||{});
    const states=[...new Set((review.items||[]).map(item=>item.state).filter(Boolean))].sort();
    const attentionClasses=[...new Set((review.items||[]).map(item=>item.operator_attention_class).filter(Boolean))].sort();
    document.querySelector('#opsReviewStateFilter').innerHTML='<option value="">All review states</option>'+states.map(value=>`<option value="${esc(value)}">${esc(human(value))}</option>`).join('');
    document.querySelector('#opsReviewAttentionFilter').innerHTML='<option value="">All attention classes</option>'+attentionClasses.map(value=>`<option value="${esc(value)}">${esc(human(value))}</option>`).join('');
    const horizonTitle=localHorizon
      ? `${esc(review.run_count_considered||0)} locally retained run${review.run_count_considered===1?'':'s'}`
      : `${esc(review.retention_days||'?')} retained days · activated after monitor run ${esc(review.activation_after_run_number||'?')}`;
    summary.innerHTML=`<article class="ops-review-horizon">
      <div class="ops-card-head"><div><p class="eyebrow">EVIDENCE HORIZON</p><h3>${horizonTitle}</h3></div><span class="ops-static-badge">${localHorizon?'LOCAL':'NOT PERMANENT'}</span></div>
      <div class="ops-runtime-metrics"><span><b>${esc(review.run_count_considered||0)}</b>successful runs reduced</span><span><b>${esc(review.item_count||0)}</b>review items</span><span><b>${esc(review.unsuccessful_run_count||0)}</b>unsuccessful runs</span><span><b>${review.evidence_horizon_complete?'YES':'NO'}</b>horizon complete</span></div>
      ${stateEntries.length?`<div class="ops-review-state-summary">${stateEntries.map(([state,n])=>`<span><b>${esc(n)}</b>${esc(human(state))}</span>`).join('')}</div>`:'<p class="ops-alignment-ok">No post-contract review proposition has been observed in the retained evidence horizon.</p>'}
      <p class="meta">A later run with no matching candidate does not resolve an earlier item. ${localHorizon?'Pre-migration Actions evidence is not silently inferred or imported. ':''}Manual decisions are repository-reviewed records; monitor and browser writes remain prohibited.</p>
    </article>`;
    renderReviewItems();
  }

  function render(data){
    DATA=data;
    const m=data.metadata||{};
    const gate=data.governance?.canonical_auto_commit_gate||{};
    document.querySelector('#opsStats').innerHTML=`
      <div class="stat"><b>${esc(m.source_count)}</b><span>source records</span></div>
      <div class="stat"><b>${esc(m.configured_monitor_route_count)}</b><span>configured monitor routes</span></div>
      <div class="stat"><b>${esc(m.reviewed_change_count)}</b><span>reviewed canonical changes</span></div>
      <div class="stat"><b>${esc(gate.state||'UNKNOWN')}</b><span>automatic commit gate</span></div>`;

    document.querySelector('#opsGovernanceSummary').innerHTML=[
      renderSummaryBlock('Canonical provenance use',data.source_governance_summary?.canonical_provenance_use),
      renderSummaryBlock('Automated monitoring use',data.source_governance_summary?.automated_monitoring_use),
      renderSummaryBlock('Verification mode',data.source_governance_summary?.verification_mode),
      renderSummaryBlock('Monitoring readiness',data.source_governance_summary?.monitoring_readiness_status),
    ].join('');

    document.querySelector('#opsRecordedRoutes').innerHTML=(data.configured_routes||[]).length
      ? data.configured_routes.map(renderRoute).join('')
      : '<p class="empty">No configured monitor routes are recorded.</p>';

    const evidence=gate.remaining_real_world_evidence||[];
    document.querySelector('#opsGate').innerHTML=`<div><p class="eyebrow">AUTO-COMMIT GATE</p><h3>${esc(gate.state||'UNKNOWN')}</h3><p>Parser success does not open this gate. The remaining requirements are real-world behavioural evidence.</p></div>${evidence.length?`<ol>${evidence.map(item=>`<li>${esc(human(item))}</li>`).join('')}</ol>`:''}`;

    const automationValues=[...new Set((data.sources||[]).map(source=>statusToken(source.automated_monitoring_use)))].sort();
    const select=document.querySelector('#opsAutomationFilter');
    select.innerHTML='<option value="">All automation states</option>'+automationValues.map(value=>`<option value="${esc(value)}">${esc(human(value))}</option>`).join('');
    renderSources();
  }

  async function loadOperations(){
    if(loaded) return;
    document.querySelector('#opsRecordedRoutes').innerHTML='<p class="empty">Loading recorded operations state…</p>';
    try{
      const [operationsResponse,runtimeResponse,reviewResponse]=await Promise.all([
        fetch('data/operations.json'),
        fetch('data/runtime.json'),
        fetch('data/review_state.json'),
      ]);
      if(!operationsResponse.ok) throw new Error(`operations.json ${operationsResponse.status}`);
      render(await operationsResponse.json());
      if(runtimeResponse.ok){
        renderRuntime(await runtimeResponse.json());
      }else{
        renderRuntime({availability:'UNAVAILABLE_AT_BUILD',reason:`runtime.json ${runtimeResponse.status}`});
      }
      if(reviewResponse.ok){
        renderReviewState(await reviewResponse.json());
      }else{
        renderReviewState({availability:`review_state.json ${reviewResponse.status}`});
      }
      loaded=true;
    } catch(error){
      document.querySelector('#opsRecordedRoutes').innerHTML=`<p class="empty">Operations data could not be loaded: ${esc(error.message)}</p>`;
      renderRuntime({availability:'UNAVAILABLE_AT_BUILD',reason:'operations data load failed'});
      renderReviewState({availability:'operations data load failed'});
    }
  }

  function showOperations(){
    document.querySelector('#calendarView').hidden=true;
    document.querySelector('#indexView').hidden=true;
    document.querySelector('#monitorsView').hidden=true;
    document.querySelector('#historyView').hidden=true;
    document.querySelector('#operationsView').hidden=false;
    document.querySelector('.controls').hidden=true;
    document.querySelector('#filterDisclosure').hidden=true;
    document.querySelectorAll('.viewtabs button').forEach(button=>button.setAttribute('aria-pressed',String(button.id==='operationsTab')));
    loadOperations();
  }

  function hideOperations(){
    document.querySelector('#operationsView').hidden=true;
    document.querySelector('#operationsTab').setAttribute('aria-pressed','false');
    document.querySelector('#filterDisclosure').hidden=false;
  }

  document.querySelector('#operationsTab').addEventListener('click',showOperations);
  document.querySelectorAll('.viewtabs button:not(#operationsTab)').forEach(button=>button.addEventListener('click',hideOperations));
  document.querySelector('#opsSourceSearch').addEventListener('input',renderSources);
  document.querySelector('#opsAutomationFilter').addEventListener('change',renderSources);
  document.querySelector('#opsReviewSearch').addEventListener('input',renderReviewItems);
  document.querySelector('#opsReviewStateFilter').addEventListener('change',renderReviewItems);
  document.querySelector('#opsReviewAttentionFilter').addEventListener('change',renderReviewItems);
  document.querySelector('#opsReviewSort').addEventListener('change',renderReviewItems);
})();
