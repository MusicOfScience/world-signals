(() => {
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const human=value=>String(value??'').replaceAll('_',' ').toLowerCase();
  let data=null;
  let loaded=false;

  function ensureSurface(){
    if(!document.querySelector('link[href="risk.css"]')){
      const link=document.createElement('link');
      link.rel='stylesheet';
      link.href='risk.css';
      document.head.appendChild(link);
    }
    const tabs=document.querySelector('.viewtabs');
    if(tabs&&!document.querySelector('#riskTab')){
      tabs.insertAdjacentHTML('beforeend','<button id="riskTab" aria-pressed="false">Risk overlay</button>');
    }
    if(!document.querySelector('#riskView')){
      const anchor=document.querySelector('#historyView')||document.querySelector('main');
      const html=`<section id="riskView" class="view-panel" hidden>
        <section class="risk-intro">
          <div><p class="eyebrow">CROSS-DOMAIN RISK LENS</p><h2>Where governed signals cluster and how exposure may travel</h2><p>This read-only layer overlays existing Canonical events with their already governed importance, market sensitivity, geopolitical sensitivity and transmission channels. It shows signal density without inventing probability, severity or causality.</p><p id="riskCount" class="meta"></p></div>
          <div class="risk-boundary"><strong>Interpretation boundary</strong><span>Separate dimensions: preserved</span><span>Single danger score: absent</span><span>Probability estimate: absent</span><span>Coincidence ≠ causality</span><span>Private Live Intelligence: not consumed</span><span>Canonical write: OFF</span></div>
        </section>
        <section class="risk-controls" aria-label="Risk overlay filters">
          <select id="riskHorizon" aria-label="Risk horizon"><option value="30">Next 30 days</option><option value="90">Next 90 days</option><option value="365">Next 365 days</option><option value="all">All canonical records</option></select>
          <select id="riskDomain" aria-label="Risk domain"><option value="">All risk domains</option></select>
          <select id="riskRegion" aria-label="Risk region"><option value="">All regions</option></select>
          <select id="riskGeopolitical" aria-label="Geopolitical sensitivity"><option value="">All geopolitical sensitivities</option></select>
          <input id="riskSearch" type="search" aria-label="Search risk signals" placeholder="Search event, institution, channel…">
        </section>
        <section id="riskSummary" class="risk-summary"><p class="empty">Loading risk overlay…</p></section>
        <section class="risk-section">
          <div class="section-heading"><div><p class="eyebrow">CONVERGENCE WINDOWS</p><h3>Calendar-week signal density</h3></div><span id="riskWindowCount" class="meta"></span></div>
          <p class="meta">A window appears only when at least two planned or active events from at least two Canonical categories share a calendar week. This is timing density—not evidence that the events are connected.</p>
          <div id="riskWindows" class="risk-windows"></div>
        </section>
        <section class="risk-section">
          <div class="section-heading"><div><p class="eyebrow">EVENT LENS</p><h3>Dimensions kept separate</h3></div><span id="riskEventCount" class="meta"></span></div>
          <div id="riskEvents" class="risk-events"></div>
        </section>
      </section>`;
      if(anchor?.id==='historyView') anchor.insertAdjacentHTML('beforebegin',html);
      else anchor?.insertAdjacentHTML('beforeend',html);
    }
  }

  function parseDate(raw){
    const match=String(raw??'').match(/^(\d{4})-(\d{2})-(\d{2})$/);
    return match?new Date(Number(match[1]),Number(match[2])-1,Number(match[3])):null;
  }

  function localToday(){
    const now=new Date();
    return new Date(now.getFullYear(),now.getMonth(),now.getDate());
  }

  function horizonEnd(){
    const raw=document.querySelector('#riskHorizon').value;
    if(raw==='all') return null;
    const end=localToday();
    end.setDate(end.getDate()+Number(raw));
    return end;
  }

  function inHorizon(event){
    const end=horizonEnd();
    if(!end) return true;
    if(!['ACTIVE','PLANNED'].includes(event.lifecycle_status)) return false;
    const anchor=parseDate(event.timing_anchor);
    if(anchor) return anchor>=localToday()&&anchor<=end;
    const windowStart=parseDate(event.date_earliest);
    const windowEnd=parseDate(event.date_latest);
    if(windowStart&&windowEnd) return windowEnd>=localToday()&&windowStart<=end;
    const phases=event.season_phases||[];
    if(phases.length){
      const startMonth=phases[0]?.start_month;
      const endMonth=phases[phases.length-1]?.end_month;
      const todayMonth=`${localToday().getFullYear()}-${String(localToday().getMonth()+1).padStart(2,'0')}`;
      const horizonMonth=`${end.getFullYear()}-${String(end.getMonth()+1).padStart(2,'0')}`;
      return !!startMonth&&!!endMonth&&endMonth>=todayMonth&&startMonth<=horizonMonth;
    }
    return false;
  }

  function filteredEvents(){
    const domain=document.querySelector('#riskDomain').value;
    const region=document.querySelector('#riskRegion').value;
    const geopolitical=document.querySelector('#riskGeopolitical').value;
    const query=document.querySelector('#riskSearch').value.toLowerCase().trim();
    return (data.events||[]).filter(event=>{
      const hay=[event.title,event.institution,event.jurisdiction,event.category,event.source_native_window_label,...(event.transmission_channels||[])].join(' ').toLowerCase();
      return inHorizon(event)&&(!domain||(event.risk_domain_ids||[]).includes(domain))&&(!region||event.region===region)&&(!geopolitical||event.geopolitical_sensitivity===geopolitical)&&(!query||hay.includes(query));
    });
  }

  function relevantWindows(eventIds){
    const end=horizonEnd();
    const today=localToday();
    return (data.convergence_windows||[]).filter(window=>{
      const intersectsIds=(window.occurrence_ids||[]).some(id=>eventIds.has(id));
      if(!intersectsIds) return false;
      if(!end) return true;
      const start=parseDate(window.window_start);
      const finish=parseDate(window.window_end);
      return !!start&&!!finish&&finish>=today&&start<=end;
    });
  }

  function axis(label,value){
    const token=String(value||'UNRATED_PENDING_CALIBRATION');
    return `<div class="risk-axis" data-level="${esc(token)}"><span>${esc(label)}</span><strong>${esc(human(token))}</strong></div>`;
  }

  function when(event){
    if(event.timing_anchor) return `${event.timing_anchor} · ${human(event.timing_anchor_basis)}`;
    if(event.date_earliest||event.date_latest) return `${event.date_earliest||'?'} → ${event.date_latest||'?'} · expected window; no single day inferred`;
    if(event.source_native_window_label) return `${event.source_native_window_label} · source-native window; no day inferred`;
    if(event.source_native_date_label) return `${event.source_native_date_label} · no authoritative Gregorian anchor`;
    return 'Timing unresolved; no date inferred';
  }

  function eventCard(event){
    const domains=(event.risk_domain_ids||[]).map(id=>`<span>${esc(human(id))}</span>`).join('');
    const channels=(event.transmission_channels||[]).map(channel=>`<code>${esc(channel)}</code>`).join(' ');
    return `<article class="risk-event">
      <header><div><p class="eyebrow">${esc(event.category)} · ${esc(event.region)}</p><h4>${esc(event.title)}</h4><p class="meta">${esc(when(event))} · ${esc(event.lifecycle_status)} · <code>${esc(event.occurrence_id)}</code></p></div><div class="risk-domains">${domains}</div></header>
      <div class="risk-axes">${axis('Intrinsic importance',event.intrinsic_importance)}${axis('Market sensitivity',event.expected_market_sensitivity)}${axis('Geopolitical sensitivity',event.geopolitical_sensitivity)}</div>
      <p><strong>${esc(event.institution)}</strong> · ${esc(event.jurisdiction)}</p>
      <div class="risk-channels"><span>Recorded transmission channels</span><div>${channels||'<em>None recorded</em>'}</div></div>
    </article>`;
  }

  function windowCard(window,eventMap){
    const names=(window.occurrence_ids||[]).map(id=>eventMap.get(id)?.title||id);
    return `<article class="risk-window">
      <div><p class="eyebrow">${esc(window.window_start)} → ${esc(window.window_end)}</p><h4>${esc(window.event_count)} signals · ${esc(window.canonical_categories.length)} categories</h4><p>${names.map(esc).join(' · ')}</p></div>
      <div class="risk-window-meta"><span>${(window.risk_domain_ids||[]).map(id=>esc(human(id))).join(' · ')}</span><small>density only · no causal or probabilistic interpretation</small></div>
    </article>`;
  }

  function render(){
    if(!data) return;
    const events=filteredEvents();
    const ids=new Set(events.map(event=>event.occurrence_id));
    const windows=relevantWindows(ids);
    const eventMap=new Map((data.events||[]).map(event=>[event.occurrence_id,event]));
    const activeDomains=new Set(events.flatMap(event=>event.risk_domain_ids||[]));
    const highGeopolitical=events.filter(event=>['HIGH','MEDIUM_HIGH'].includes(event.geopolitical_sensitivity)).length;
    const highMarket=events.filter(event=>['HIGH','MEDIUM_HIGH'].includes(event.expected_market_sensitivity)).length;
    document.querySelector('#riskCount').textContent=`Canonical registry v${data.metadata.canonical_registry_version} · overlay v${data.version}`;
    document.querySelector('#riskSummary').innerHTML=`
      <div><b>${esc(events.length)}</b><span>signals in selected horizon</span></div>
      <div><b>${esc(activeDomains.size)}</b><span>risk domains represented</span></div>
      <div><b>${esc(highGeopolitical)}</b><span>high / medium-high geopolitical sensitivity</span></div>
      <div><b>${esc(highMarket)}</b><span>high / medium-high market sensitivity</span></div>`;
    document.querySelector('#riskWindowCount').textContent=`${windows.length} density window${windows.length===1?'':'s'}`;
    document.querySelector('#riskWindows').innerHTML=windows.length?windows.map(window=>windowCard(window,eventMap)).join(''):'<p class="empty">No cross-category convergence windows match these filters.</p>';
    document.querySelector('#riskEventCount').textContent=`${events.length} canonical signal${events.length===1?'':'s'}`;
    document.querySelector('#riskEvents').innerHTML=events.length?events.map(eventCard).join(''):'<p class="empty">No canonical signals match these filters.</p>';
  }

  function addOptions(selector,values,label){
    const target=document.querySelector(selector);
    [...new Set(values.filter(Boolean))].sort().forEach(value=>target.insertAdjacentHTML('beforeend',`<option value="${esc(value)}">${esc(label?label(value):value)}</option>`));
  }

  async function loadRisk(){
    if(loaded) return;
    try{
      const response=await fetch('data/risk_overlay.json');
      if(!response.ok) throw new Error(`risk_overlay.json ${response.status}`);
      data=await response.json();
      const domainLabels=new Map((data.domains||[]).map(domain=>[domain.domain_id,domain.label]));
      addOptions('#riskDomain',(data.domains||[]).map(domain=>domain.domain_id),value=>domainLabels.get(value));
      addOptions('#riskRegion',(data.events||[]).map(event=>event.region));
      addOptions('#riskGeopolitical',(data.events||[]).map(event=>event.geopolitical_sensitivity),human);
      document.querySelectorAll('.risk-controls input,.risk-controls select').forEach(control=>control.addEventListener('input',render));
      loaded=true;
      render();
    }catch(error){
      document.querySelector('#riskSummary').innerHTML=`<p class="empty">Risk overlay could not be loaded: ${esc(error.message)}</p>`;
    }
  }

  function showRisk(){
    ['#calendarView','#indexView','#monitorsView','#operationsView','#historyView','#analysisView'].forEach(selector=>{
      const node=document.querySelector(selector); if(node) node.hidden=true;
    });
    document.querySelector('#riskView').hidden=false;
    document.querySelector('.controls').hidden=true;
    document.querySelectorAll('.viewtabs button').forEach(button=>button.setAttribute('aria-pressed',String(button.id==='riskTab')));
    loadRisk();
  }

  function hideRisk(){
    document.querySelector('#riskView').hidden=true;
    document.querySelector('#riskTab').setAttribute('aria-pressed','false');
  }

  ensureSurface();
  document.querySelector('#riskTab').addEventListener('click',showRisk);
  document.querySelectorAll('.viewtabs button:not(#riskTab)').forEach(button=>button.addEventListener('click',hideRisk));
})();
