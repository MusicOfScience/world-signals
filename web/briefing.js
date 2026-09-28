(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

  function utcDateLabel(value){
    const date=new Date(value);
    return Number.isNaN(date.getTime()) ? 'Date not recorded' : date.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'}).toUpperCase();
  }

  function human(value){return String(value ?? '').replaceAll('_',' ').toLowerCase();}

  function forecastScan(row){
    const value=row.forecast_value||{};
    if(row.forecast_type==='NUMERIC_POINT'){
      return {primary:`${value.estimate} ${value.unit}`, detail:'numeric point forecast'};
    }
    const outcomes=[...(value.outcomes||[])];
    const highest=Math.max(...outcomes.map(outcome=>Number(outcome.probability)));
    const leaders=outcomes.filter(outcome=>Number(outcome.probability)===highest);
    return {
      primary:leaders.map(outcome=>`${outcome.label} ${Math.round(Number(outcome.probability)*100)}%`).join(' · '),
      detail:outcomes.length>1?`${outcomes.length} declared outcomes · full distribution in Outlook`:'categorical forecast'
    };
  }

  function eventDate(event){
    if(event.start_utc){
      const date=new Date(event.start_utc);
      return Number.isNaN(date.getTime())?null:date;
    }
    if(event.start_local){
      const date=new Date(event.start_local);
      return Number.isNaN(date.getTime())?null:date;
    }
    if(event.date_earliest && (!event.date_latest || event.date_earliest===event.date_latest)){
      const date=new Date(`${event.date_earliest}T00:00:00`);
      return Number.isNaN(date.getTime())?null:date;
    }
    return null;
  }

  function eventWhen(event){
    if(event.start_utc){
      const date=new Date(event.start_utc);
      return Number.isNaN(date.getTime())?'Exact date recorded':date.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
    }
    if(event.start_local) return `${event.start_local.replace('T',' ')}${event.source_timezone?` · ${event.source_timezone}`:''}`;
    return event.date_earliest||'Exact date recorded';
  }

  function nextCalendarEvent(briefing, events){
    const allowed=new Set(briefing.calendar?.candidate_occurrence_ids||[]);
    return events
      .filter(event=>allowed.has(event.occurrence_id) && event.lifecycle!=='CANCELLED')
      .map(event=>({event,date:eventDate(event)}))
      .filter(row=>row.date && row.date.getTime()>=Date.now())
      .sort((a,b)=>a.date-b.date || String(a.event.occurrence_id).localeCompare(String(b.event.occurrence_id)))[0]?.event||null;
  }

  function forecastLane(briefing, outlook){
    const rows=new Map((outlook.forecasts||[]).map(row=>[row.forecast_id,row]));
    const selected=(briefing.forecast_resolution?.forecast_ids||[]).map(id=>rows.get(id)).filter(Boolean);
    if(!selected.length) return `<div class="briefing-lane"><p class="briefing-lane-label">NEXT TO RESOLVE</p><p class="briefing-empty">No open public Forecast currently occupies this lane.</p></div>`;
    const date=briefing.forecast_resolution.resolution_date_utc;
    const passed=new Date(date).getTime()<Date.now();
    return `<div class="briefing-lane">
      <p class="briefing-lane-label">NEXT TO RESOLVE</p>
      <time class="briefing-lane-date" datetime="${esc(date)}">${esc(utcDateLabel(date))}</time>
      <ul class="briefing-lane-list">${selected.map(row=>{
        const scan=forecastScan(row);
        return `<li class="briefing-lane-item"><a href="#forecast-${esc(row.forecast_id)}">${esc(row.institution)}</a><strong>${esc(scan.primary)}</strong><span>${esc(scan.detail)}</span></li>`;
      }).join('')}</ul>
      <p class="briefing-lane-note">${passed?'Resolution date passed · Outcome pending':'Forecast open'} · full distribution and cutoff in <a href="#outlook">Outlook</a>.</p>
    </div>`;
  }

  function calendarLane(briefing, events){
    const event=nextCalendarEvent(briefing,events);
    if(!event) return `<div class="briefing-lane"><p class="briefing-lane-label">NEXT ON THE CALENDAR</p><p class="briefing-empty">No exact-date occurrence currently resolves this lane. <a href="#horizonWindows">See windows in view →</a></p></div>`;
    const jurisdiction=Array.isArray(event.jurisdiction)?event.jurisdiction.join(', '):(event.jurisdiction||event.region||'');
    return `<div class="briefing-lane">
      <p class="briefing-lane-label">NEXT ON THE CALENDAR</p>
      <time class="briefing-lane-date" datetime="${esc(event.start_utc||event.start_local||event.date_earliest)}">${esc(eventWhen(event))}</time>
      <ul class="briefing-lane-list"><li class="briefing-lane-item"><a href="#event=${encodeURIComponent(event.occurrence_id)}">${esc(event.title)}</a><span>${esc(event.institution)}${jurisdiction?` · ${esc(jurisdiction)}`:''}</span><small>${esc(event.certainty||'timing recorded')} · exact-date public Calendar occurrence</small></li></ul>
    </div>`;
  }

  function analysisLane(briefing, analysis){
    const id=briefing.latest_reviewed_analysis?.analysis_id;
    const row=(analysis.reviews||[]).find(item=>item.analysis_id===id && item.review_state==='REVIEWED_SAMPLE');
    if(!row) return `<div class="briefing-lane"><p class="briefing-lane-label">LATEST REVIEWED</p><p class="briefing-empty">No reviewed public Analysis currently occupies this lane.</p></div>`;
    const summary=row.what_happened?.summary||'No governed summary recorded.';
    const causal=row.what_appears_connected?.causal_status;
    return `<div class="briefing-lane">
      <p class="briefing-lane-label">LATEST REVIEWED</p>
      <time class="briefing-lane-date" datetime="${esc(row.analysis_as_of_utc)}">${esc(utcDateLabel(row.analysis_as_of_utc))}</time>
      <ul class="briefing-lane-list"><li class="briefing-lane-item"><a class="briefing-analysis-link" href="#analysisView">${esc(row.canonical_institution||row.analysis_id)}</a><strong>${esc(row.scope||'Reviewed event analysis')}</strong><p class="briefing-analysis-summary">${esc(summary)}</p>${causal?`<span class="briefing-analysis-status">${esc(human(causal))}</span>`:''}</li></ul>
    </div>`;
  }

  function render(briefing,outlook,events,analysis){
    const target=document.querySelector('#briefingLanes');
    if(!target) return;
    target.innerHTML=forecastLane(briefing,outlook)+calendarLane(briefing,events)+analysisLane(briefing,analysis);
    target.querySelectorAll('.briefing-analysis-link').forEach(link=>link.addEventListener('click',event=>{
      if(typeof window.showAnalysisView!=='function') return;
      event.preventDefault();
      window.showAnalysisView();
      document.querySelector('#analysisView')?.scrollIntoView({block:'start'});
    }));
  }

  async function load(){
    try{
      const responses=await Promise.all([
        fetch('data/briefing.json'),
        fetch('data/outlook.json'),
        fetch('data/events.json'),
        fetch('data/analysis.json'),
      ]);
      if(responses.some(response=>!response.ok)) throw new Error('public Brief projection unavailable');
      const [briefing,outlook,events,analysis]=await Promise.all(responses.map(response=>response.json()));
      render(briefing,outlook,events.events||[],analysis);
    } catch(error){
      const target=document.querySelector('#briefingLanes');
      if(target) target.innerHTML=`<p class="briefing-empty">The Brief could not be loaded: ${esc(error.message)}</p>`;
    }
  }

  load();
})();
