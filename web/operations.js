(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const human = value => String(value ?? '').replaceAll('_',' ').toLowerCase();
  let loaded = false;
  let DATA = null;

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
      ? `<strong>${esc(recordedTime(route.last_recorded_evidence_at))}</strong><span>latest timestamp embedded in the repository baseline/configuration</span>`
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
      const response=await fetch('data/operations.json');
      if(!response.ok) throw new Error(`operations.json ${response.status}`);
      render(await response.json());
      loaded=true;
    } catch(error){
      document.querySelector('#opsRecordedRoutes').innerHTML=`<p class="empty">Operations data could not be loaded: ${esc(error.message)}</p>`;
    }
  }

  function showOperations(){
    document.querySelector('#calendarView').hidden=true;
    document.querySelector('#indexView').hidden=true;
    document.querySelector('#monitorsView').hidden=true;
    document.querySelector('#historyView').hidden=true;
    document.querySelector('#operationsView').hidden=false;
    document.querySelector('.controls').hidden=true;
    document.querySelectorAll('.viewtabs button').forEach(button=>button.setAttribute('aria-pressed',String(button.id==='operationsTab')));
    loadOperations();
  }

  function hideOperations(){
    document.querySelector('#operationsView').hidden=true;
    document.querySelector('#operationsTab').setAttribute('aria-pressed','false');
  }

  document.querySelector('#operationsTab').addEventListener('click',showOperations);
  document.querySelectorAll('.viewtabs button:not(#operationsTab)').forEach(button=>button.addEventListener('click',hideOperations));
  document.querySelector('#opsSourceSearch').addEventListener('input',renderSources);
  document.querySelector('#opsAutomationFilter').addEventListener('change',renderSources);
})();
