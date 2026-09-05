(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const human = value => String(value ?? '').replaceAll('_',' ').toLowerCase();
  const signed = value => Number(value)>0 ? `+${value}` : String(value);
  let loaded = false;

  function ensureSurface(){
    if(!document.querySelector('link[href="analysis.css"]')){
      const link=document.createElement('link');
      link.rel='stylesheet';
      link.href='analysis.css';
      document.head.appendChild(link);
    }
    const tabs=document.querySelector('.viewtabs');
    if(tabs && !document.querySelector('#analysisTab')){
      tabs.insertAdjacentHTML('beforeend','<button id="analysisTab" aria-pressed="false">Analysis</button>');
    }
    if(!document.querySelector('#analysisView')){
      const anchor=document.querySelector('#historyView')||document.querySelector('main');
      const html=`<section id="analysisView" class="view-panel" hidden>
        <section class="analysis-intro">
          <div><p class="eyebrow">ANALYSIS</p><h2>What happened, what surprised, and what may merely coincide</h2><p>This is a read-only analytical layer linked to canonical occurrences. Expectations, observed responses, alternatives and falsifiers remain evidence-backed analytical objects; none can rewrite the canonical registry.</p><p id="analysisCount" class="meta"></p></div>
          <div class="analysis-boundary"><strong>Analytical boundary</strong><span>Canonical event truth: referenced, not rewritten</span><span>Expected ≠ actual</span><span>Movement ≠ cause</span><span>Alternatives / falsifiers: explicit</span><span>Canonical write: OFF</span><span>Google Calendar write: OFF</span></div>
        </section>
        <section id="analysisReadiness"><p class="empty">Population readiness loads with the analytical reviews.</p></section>
        <section id="analysisReviews"><p class="empty">Analytical reviews load when this view is opened.</p></section>
      </section>`;
      if(anchor?.id==='historyView') anchor.insertAdjacentHTML('beforebegin',html);
      else anchor?.insertAdjacentHTML('beforeend',html);
    }
  }

  function evidenceLinks(evidence){
    return (evidence||[]).map(item=>`<a class="analysis-source" href="${esc(item.url)}" target="_blank" rel="noopener noreferrer"><strong>${esc(item.provider)}</strong><span>${esc(item.title)}</span><small>${esc(human(item.evidence_class))} · ${esc(human((item.roles||[]).join(' / ')))}</small></a>`).join('');
  }

  function bullets(rows, empty='None established in this review.'){
    if(!rows || !rows.length) return `<p class="analysis-none">${esc(empty)}</p>`;
    return `<ul>${rows.map(row=>`<li>${esc(typeof row==='string'?row:row.summary)}</li>`).join('')}</ul>`;
  }

  function metricValue(row){
    const suffix=row.unit==='percent'?'%':row.unit==='basis_points'?' bp':'';
    return `${esc(row.value)}${suffix}`;
  }

  function metricTable(actuals, expected){
    const expectedMap=new Map((expected||[]).map(row=>[row.metric,row]));
    if(!actuals?.length) return '<p class="analysis-none">No structured actuals recorded.</p>';
    return `<div class="analysis-metrics">${actuals.map(row=>{
      const exp=expectedMap.get(row.metric);
      return `<div><span>${esc(human(row.metric))}</span><strong>${metricValue(row)}</strong><small>${exp?`expected ${metricValue(exp)}`:'no structured expectation benchmark'}</small></div>`;
    }).join('')}</div>`;
  }

  function movementHeadline(row){
    const representation=row.movement_representation;
    if(representation==='PRE_POST_VALUES'){
      return `${esc(row.before_value)} → ${esc(row.after_value)}`;
    }
    if(representation==='CHANGE_AND_ENDPOINT'){
      return `endpoint ${esc(row.after_value)} · change ${esc(signed(row.change))} ${esc(human(row.change_unit))}`;
    }
    return esc(row.summary||row.direction||'qualitative movement');
  }

  function movementCard(row){
    const detail=row.movement_representation==='PRE_POST_VALUES'
      ? `${esc(row.unit)} · ${esc(signed(row.change))} ${esc(human(row.change_unit))}`
      : `${esc(row.unit||'')} · ${esc(human(row.movement_representation||'representation not recorded'))}`;
    return `<article class="analysis-move"><div><p class="eyebrow">${esc(human(row.movement_type))}</p><h4>${esc(row.instrument_or_measure)}</h4></div><div class="analysis-move-values"><strong>${movementHeadline(row)}</strong><span>${detail}</span></div><p>${esc(row.measurement_window)}</p><small>${esc(human(row.measurement_precision))}${row.independently_reconstructed?' · independently reconstructed':' · source-reported, not independently reconstructed'}</small></article>`;
  }

  function canonicalTimingLabel(canonical){
    if(canonical.source_native_date_label){
      const calendar=canonical.native_calendar_system?human(canonical.native_calendar_system):'source-native calendar';
      const resolution=canonical.gregorian_resolution_status==='UNRESOLVED_AUTHORITATIVE_CONVERSION'
        ? 'Gregorian mapping unresolved by authoritative source'
        : human(canonical.gregorian_resolution_status||'Gregorian mapping status not recorded');
      return `${canonical.source_native_date_label} · ${calendar} · ${resolution}`;
    }
    if(canonical.start_utc){
      return new Date(canonical.start_utc).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
    }
    if(canonical.start_local){
      const span=canonical.end_local && canonical.end_local!==canonical.start_local
        ? `${canonical.start_local} – ${canonical.end_local}`
        : canonical.start_local;
      return canonical.source_timezone?`${span} · ${canonical.source_timezone}`:span;
    }
    if(canonical.date_earliest || canonical.date_latest){
      return `${canonical.date_earliest||'unresolved'} – ${canonical.date_latest||'unresolved'} · ${human(canonical.time_precision||'window')}`;
    }
    return 'canonical timing unresolved; no date inferred';
  }

  function section(title, body, className=''){
    return `<section class="analysis-section ${className}"><h3>${esc(title)}</h3>${body}</section>`;
  }

  function renderReadiness(readiness){
    if(!readiness) return '<p class="empty">Analysis population readiness is unavailable.</p>';
    const priority=(readiness.priority_geographic_stress_regions||[]).map(row=>`<div class="analysis-readiness-region"><div><strong>${esc(row.region)}</strong><span>${esc(human(row.state))}</span></div><small>${esc(row.eligible_completed_count)} completed canonical anchor${row.eligible_completed_count===1?'':'s'} · ${esc(row.reviewed_count)} reviewed</small></div>`).join('');
    return `<section class="analysis-readiness-shell">
      <div class="section-heading"><div><p class="eyebrow">POPULATION READINESS</p><h2>Can the current canonical registry support broader post-event analysis?</h2></div><span class="analysis-readiness-state">${esc(human(readiness.broad_population_state))}</span></div>
      <p class="analysis-readiness-explainer">This is an audit of available canonical anchors, not authority to create them. An elapsed date does not prove completion, and a missing historical anchor does not permit the Analysis layer to manufacture one.</p>
      <div class="analysis-readiness-metrics"><div><b>${esc(readiness.eligible_completed_occurrence_count)}</b><span>completed canonical anchors</span></div><div><b>${esc(readiness.reviewed_occurrence_count)}</b><span>reviewed samples</span></div><div><b>${esc(readiness.reviewed_event_type_diversity)}</b><span>reviewed event types</span></div><div><b>${esc(readiness.minimum_reviewed_event_type_diversity_before_broad_population)}</b><span>minimum event-type target</span></div></div>
      <div class="analysis-readiness-regions">${priority}</div>
      ${bullets(readiness.notes,'No readiness notes recorded.')}
    </section>`;
  }

  function renderReview(review){
    const expected=review.what_was_expected?.benchmarks||[];
    const happened=review.what_happened||{};
    const connection=review.what_appears_connected||{};
    const surprise=review.what_surprised||{};
    const second=review.second_order_effects||{};
    const canonical=review.canonical||{};
    const title=canonical.canonical_name||review.canonical_institution||review.analysis_id;
    const context=[canonical.region,canonical.category,canonical.event_type].filter(Boolean).map(human).join(' · ');
    return `<article class="analysis-review">
      <header class="analysis-review-head">
        <div><p class="eyebrow">${esc(review.analysis_id)}</p><h2>${esc(title)}</h2><p>${esc(review.scope)}</p><p class="meta"><code>${esc(review.canonical_occurrence_id)}</code> · ${esc(review.canonical_institution)}${context?` · ${esc(context)}`:''} · canonical timing: ${esc(canonicalTimingLabel(canonical))} · analysis as of ${esc(new Date(review.analysis_as_of_utc).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}))}</p></div>
        <div class="analysis-grade"><span>${esc(human(review.review_state))}</span><strong>${esc(human(connection.causal_status))}</strong><small>${esc(human(connection.confidence))} confidence</small></div>
      </header>
      <div class="analysis-grid">
        ${section('What happened',`<p>${esc(happened.summary)}</p>${metricTable(happened.actuals,expected)}`)}
        ${section('What was expected',`<p>${esc(review.what_was_expected?.summary)}</p>`)}
        ${section('What surprised',`<span class="analysis-surprise">${esc(human(surprise.status))}</span><p>${esc(surprise.summary)}</p>`)}
        ${section('What moved',(review.what_moved||[]).length?(review.what_moved||[]).map(movementCard).join(''):'<p class="analysis-none">No observed market response established.</p>')}
        ${section('What appears connected',`<p>${esc(connection.summary)}</p><div class="analysis-causal"><span>${esc(human(connection.causal_status))}</span><span>${esc(human(connection.confidence))} confidence</span></div>`)}
        ${section('What may be noise',bullets(review.what_may_be_noise))}
        ${section('Alternative explanations',bullets(review.alternative_explanations),'analysis-caution')}
        ${section('Second-order effects',`<span class="analysis-second-order">${esc(human(second.status))}</span><p>${esc(second.summary)}</p>`)}
        ${section('Falsifiers',bullets(review.falsifiers),'analysis-falsifiers')}
      </div>
      <section class="analysis-conclusion"><p class="eyebrow">ANALYTICAL CONCLUSION</p><p>${esc(review.analytical_conclusion)}</p></section>
      <section class="analysis-evidence"><div class="section-heading"><div><p class="eyebrow">ANALYTICAL EVIDENCE</p><h3>Sources used for interpretation</h3></div></div><p class="meta">These sources support this analysis packet only. They do not alter canonical event provenance.</p><div class="analysis-source-list">${evidenceLinks(review.evidence)}</div></section>
    </article>`;
  }

  async function loadAnalysis(){
    if(loaded) return;
    const target=document.querySelector('#analysisReviews');
    const readinessTarget=document.querySelector('#analysisReadiness');
    target.innerHTML='<p class="empty">Loading analytical reviews…</p>';
    readinessTarget.innerHTML='<p class="empty">Loading population readiness…</p>';
    try{
      const response=await fetch('data/analysis.json');
      if(!response.ok) throw new Error(`analysis.json ${response.status}`);
      const data=await response.json();
      document.querySelector('#analysisCount').textContent=`${data.metadata.review_count} reviewed analytical sample${data.metadata.review_count===1?'':'s'} · schema v${data.metadata.schema_version}`;
      readinessTarget.innerHTML=renderReadiness(data.readiness);
      target.innerHTML=(data.reviews||[]).length?(data.reviews||[]).map(renderReview).join(''):'<p class="empty">No analytical reviews are published.</p>';
      loaded=true;
    } catch(error){
      readinessTarget.innerHTML='<p class="empty">Analysis population readiness could not be loaded.</p>';
      target.innerHTML=`<p class="empty">Analytical reviews could not be loaded: ${esc(error.message)}</p>`;
    }
  }

  function showAnalysis(){
    ['#calendarView','#indexView','#monitorsView','#operationsView','#historyView'].forEach(selector=>{
      const node=document.querySelector(selector); if(node) node.hidden=true;
    });
    document.querySelector('#analysisView').hidden=false;
    document.querySelector('.controls').hidden=true;
    document.querySelectorAll('.viewtabs button').forEach(button=>button.setAttribute('aria-pressed',String(button.id==='analysisTab')));
    loadAnalysis();
  }

  function hideAnalysis(){
    document.querySelector('#analysisView').hidden=true;
    document.querySelector('#analysisTab').setAttribute('aria-pressed','false');
  }

  ensureSurface();
  document.querySelector('#analysisTab').addEventListener('click',showAnalysis);
  document.querySelectorAll('.viewtabs button:not(#analysisTab)').forEach(button=>button.addEventListener('click',hideAnalysis));
})();
