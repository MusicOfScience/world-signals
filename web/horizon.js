(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[ch]));
  const human = value => String(value ?? '').replaceAll('_',' ').toLowerCase();
  const DAY_MS = 24 * 60 * 60 * 1000;
  const SEASON_TYPES = new Set(['MONTH_BOUNDED_SEASON_WINDOW','MULTI_PHASE_SEASON_WINDOW']);
  const OMIT_FROM_FUTURE = new Set(['CANCELLED']);

  const DOMAIN_GROUPS = new Map([
    ['MONETARY_FINANCIAL_POLICY','Economics / central banks / fiscal / markets'],
    ['MACROECONOMIC_RELEASE','Economics / central banks / fiscal / markets'],
    ['FISCAL_SOVEREIGN_FINANCE','Economics / central banks / fiscal / markets'],
    ['FINANCIAL_STABILITY_REGULATION','Economics / central banks / fiscal / markets'],
    ['CORPORATE_FINANCIAL_MARKET_STRUCTURE','Economics / central banks / fiscal / markets'],
    ['ELECTIONS_GOVERNANCE','Elections / politics'],
    ['INTERNATIONAL_INSTITUTIONS','Geopolitics / institutions'],
    ['TRADE_SANCTIONS_INDUSTRIAL_POLICY','Trade / sanctions'],
    ['ENERGY_COMMODITIES','Commodities / energy / food'],
    ['AGRICULTURE_FOOD','Commodities / energy / food'],
    ['CLIMATE_ENVIRONMENT','Climate / physical risk'],
    ['PHYSICAL_CLIMATE_RISK','Climate / physical risk'],
    ['TECHNOLOGY_CRITICAL_INFRASTRUCTURE','Technology / infrastructure'],
    ['HEALTH_BIOSECURITY','Health / biosecurity'],
  ]);

  const state = {events:[], changes:[], changeByOccurrence:new Map()};

  function startOfToday(){
    const d=new Date();
    d.setHours(0,0,0,0);
    return d;
  }

  function addDays(date, days){
    const d=new Date(date);
    d.setDate(d.getDate()+days);
    return d;
  }

  function civilDate(raw){
    const match=String(raw ?? '').slice(0,10).match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if(!match) return null;
    const d=new Date(Number(match[1]), Number(match[2])-1, Number(match[3]));
    d.setHours(0,0,0,0);
    return d;
  }

  function localDayForInstant(raw){
    if(!raw) return null;
    const d=new Date(raw);
    if(Number.isNaN(d.getTime())) return null;
    d.setHours(0,0,0,0);
    return d;
  }

  function eventInterval(event){
    if(event.start_utc){
      const start=localDayForInstant(event.start_utc);
      const end=event.end_utc?localDayForInstant(event.end_utc):start;
      return start ? {start,end:end||start,kind:'EXACT'} : null;
    }
    if(event.start_local){
      const start=civilDate(event.start_local);
      const end=event.end_local?civilDate(event.end_local):start;
      return start ? {start,end:end||start,kind:'EXACT'} : null;
    }
    if(event.date_earliest && (!event.date_latest || event.date_earliest===event.date_latest)){
      const start=civilDate(event.date_earliest);
      return start ? {start,end:start,kind:'EXACT'} : null;
    }
    return null;
  }

  function isSeasonWindow(event){
    return SEASON_TYPES.has(event.timing_type) &&
      Array.isArray(event.season_phases) &&
      event.season_phases.length>0;
  }

  function monthKey(date){
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}`;
  }

  function seasonInView(event, start, end){
    if(!isSeasonWindow(event)) return false;
    const first=monthKey(start), last=monthKey(end);
    return event.season_phases.some(phase => phase.start_month<=last && phase.end_month>=first);
  }

  function dateWindowInView(event, start, end){
    if(!event.date_earliest && !event.date_latest) return false;
    if(event.date_earliest && (!event.date_latest || event.date_earliest===event.date_latest)) return false;
    const a=civilDate(event.date_earliest||event.date_latest);
    const b=civilDate(event.date_latest||event.date_earliest);
    return !!a && !!b && a<=end && b>=start;
  }

  function domainFor(event){
    return DOMAIN_GROUPS.get(event.category) || human(event.category || 'Other');
  }

  function jurisdictions(event){
    const raw=event.jurisdiction;
    if(Array.isArray(raw)) return raw.filter(Boolean).map(String);
    return raw ? [String(raw)] : [];
  }

  function visibleUnderFilters(event){
    const q=document.querySelector('#horizonSearch').value.toLowerCase().trim();
    const domain=document.querySelector('#horizonDomain').value;
    const region=document.querySelector('#horizonRegion').value;
    const jurisdiction=document.querySelector('#horizonJurisdiction').value;
    const hay=[
      event.title,event.canonical_name,event.institution,event.region,event.category,event.subcategory,
      ...jurisdictions(event)
    ].join(' ').toLowerCase();
    return (!q || hay.includes(q)) &&
      (!domain || domainFor(event)===domain) &&
      (!region || event.region===region) &&
      (!jurisdiction || jurisdictions(event).includes(jurisdiction));
  }

  function changeTimestamp(change){
    return change?.reviewed_at || change?.committed_at || null;
  }

  function latestChanges(changes){
    const map=new Map();
    for(const change of changes){
      if(!change?.occurrence_id) continue;
      const current=map.get(change.occurrence_id);
      if(!current || String(changeTimestamp(change)||'') > String(changeTimestamp(current)||'')){
        map.set(change.occurrence_id, change);
      }
    }
    return map;
  }

  function recentChange(event){
    const change=state.changeByOccurrence.get(event.occurrence_id);
    const raw=changeTimestamp(change);
    if(!change || !raw) return null;
    const d=new Date(raw);
    if(Number.isNaN(d.getTime())) return null;
    const age=(Date.now()-d.getTime())/DAY_MS;
    return age>=-1 && age<=30 ? change : null;
  }

  function formatDeviceAndNative(event){
    if(event.start_utc){
      const d=new Date(event.start_utc);
      if(!Number.isNaN(d.getTime())){
        const device=d.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
        let native='';
        if(event.source_timezone){
          try {
            native=d.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short',timeZone:event.source_timezone});
          } catch (_) {
            native='';
          }
        }
        return {
          primary:device,
          secondary:native && native!==device
            ? `${native} · ${event.source_timezone}`
            : `source timezone ${event.source_timezone||'not recorded'}`
        };
      }
    }
    if(event.start_local){
      const end=event.end_local?` → ${String(event.end_local).replace('T',' ')}`:'';
      return {
        primary:`${String(event.start_local).replace('T',' ')}${end}`,
        secondary:event.source_timezone || human(event.timing_type)
      };
    }
    if(event.date_earliest){
      return {
        primary:event.date_latest && event.date_latest!==event.date_earliest
          ? `${event.date_earliest} → ${event.date_latest}`
          : event.date_earliest,
        secondary:human(event.timing_type)
      };
    }
    return {primary:'TBC',secondary:'source has not supplied a schedulable date'};
  }

  function seasonLabel(event){
    if(event.source_native_window_label) return String(event.source_native_window_label);
    return (event.season_phases||[]).map(p=>p.source_label).filter(Boolean).join(' · ') || 'month-precision window';
  }

  function sourceLink(event){
    return event.source_url
      ? `<a href="${esc(event.source_url)}" target="_blank" rel="noopener">authoritative source</a>`
      : `<span>${esc(event.source_id||'source not projected')}</span>`;
  }

  function metricLabel(value){
    if(!value) return 'not rated';
    return human(value);
  }

  function changeBlock(event){
    const change=recentChange(event);
    if(!change) return '';
    const raw=changeTimestamp(change);
    const d=new Date(raw);
    const when=Number.isNaN(d.getTime())?String(raw):d.toLocaleDateString(undefined,{dateStyle:'medium'});
    return `<div class="horizon-change"><strong>Changed recently</strong><span>${esc(human(change.change_type||'reviewed change'))} · ${esc(when)}</span></div>`;
  }

  function exactCard(event){
    const when=formatDeviceAndNative(event);
    const change=changeBlock(event);
    return `<article class="horizon-card" data-horizon-id="${esc(event.occurrence_id)}">
      <div class="horizon-when"><strong>${esc(when.primary)}</strong><span>${esc(when.secondary)}</span></div>
      <div class="horizon-card-main">
        <p class="horizon-domain">${esc(domainFor(event))}</p>
        <h3>${esc(event.title)}</h3>
        <p class="meta">${esc(event.institution)} · ${esc(jurisdictions(event).join(', ') || event.region)}</p>
        <div class="horizon-tags">
          <span>${esc(event.certainty||'TBC')}</span>
          <span>importance ${esc(metricLabel(event.intrinsic_importance))}</span>
          <span>market sensitivity ${esc(metricLabel(event.expected_market_sensitivity))}</span>
        </div>
        ${change}
      </div>
      <div class="horizon-source">${sourceLink(event)}</div>
    </article>`;
  }

  function windowCard(event){
    const label=isSeasonWindow(event)
      ? seasonLabel(event)
      : (event.date_latest && event.date_latest!==event.date_earliest
          ? `${event.date_earliest||'?'} → ${event.date_latest}`
          : event.date_earliest||event.date_latest||'TBC');
    return `<article class="horizon-window-card" data-horizon-id="${esc(event.occurrence_id)}">
      <div><p class="horizon-domain">${esc(domainFor(event))}</p><h3>${esc(event.title)}</h3>
        <p class="meta">${esc(event.institution)} · ${esc(jurisdictions(event).join(', ') || event.region)}</p></div>
      <div class="horizon-window-time"><strong>${esc(label)}</strong>
        <span>${isSeasonWindow(event)?'source-native month precision · no synthetic day':esc(human(event.timing_type))}</span></div>
      <div class="horizon-tags"><span>${esc(event.certainty||'TBC')}</span><span>importance ${esc(metricLabel(event.intrinsic_importance))}</span></div>
      <div class="horizon-source">${sourceLink(event)}</div>
    </article>`;
  }

  function attachDetails(root){
    root.querySelectorAll('[data-horizon-id]').forEach(card => {
      card.addEventListener('click', event => {
        if(event.target.closest('a')) return;
        if(typeof window.showDetail==='function') window.showDetail(card.dataset.horizonId);
      });
    });
  }

  function sortByStart(a,b){
    const ai=eventInterval(a), bi=eventInterval(b);
    return (ai?.start?.getTime() ?? Infinity) - (bi?.start?.getTime() ?? Infinity) ||
      String(a.title||'').localeCompare(String(b.title||''));
  }

  function renderLane(id, rows, empty){
    const target=document.querySelector(id);
    target.innerHTML=rows.length?rows.map(exactCard).join(''):`<p class="horizon-empty">${esc(empty)}</p>`;
    attachDetails(target);
  }

  function render(){
    const today=startOfToday();
    const tomorrow=addDays(today,1);
    const day7=addDays(today,7);
    const day8=addDays(today,8);
    const day30=addDays(today,30);

    const filtered=state.events.filter(visibleUnderFilters).filter(event=>!OMIT_FROM_FUTURE.has(event.lifecycle));
    const now=[], next7=[], next30=[], windows=[];

    for(const event of filtered){
      if(isSeasonWindow(event) || dateWindowInView(event,today,day30)){
        if(seasonInView(event,today,day30) || dateWindowInView(event,today,day30)) windows.push(event);
        continue;
      }
      const interval=eventInterval(event);
      if(!interval) continue;
      if(interval.start<=today && interval.end>=today){
        now.push(event);
      } else if(interval.start>=tomorrow && interval.start<=day7){
        next7.push(event);
      } else if(interval.start>=day8 && interval.start<=day30){
        next30.push(event);
      }
    }

    now.sort(sortByStart); next7.sort(sortByStart); next30.sort(sortByStart);
    windows.sort((a,b)=>String(a.date_earliest||a.source_native_window_label||'').localeCompare(String(b.date_earliest||b.source_native_window_label||'')));

    renderLane('#horizonNow',now,'No exact-date event is active today under these filters.');
    renderLane('#horizon7',next7,'No exact-date event starts in the next 7 days under these filters.');
    renderLane('#horizon30',next30,'No exact-date event starts on days 8–30 under these filters.');

    const windowTarget=document.querySelector('#horizonWindows');
    windowTarget.innerHTML=windows.length?windows.map(windowCard).join(''):'<p class="horizon-empty">No source-native windows overlap the next 30 days under these filters.</p>';
    attachDetails(windowTarget);

    document.querySelector('#horizonSummary').innerHTML=
      `<strong>${now.length+next7.length+next30.length}</strong> exact-date events in the 30-day horizon · `+
      `<strong>${windows.length}</strong> source-native window${windows.length===1?'':'s'} · `+
      `<span>registry v${esc(document.querySelector('#horizonSummary').dataset.registryVersion||'?')}</span>`;
  }

  function optionise(selector, values, label){
    const el=document.querySelector(selector);
    el.innerHTML=`<option value="">${esc(label)}</option>`+
      [...new Set(values.filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b)))
        .map(value=>`<option>${esc(value)}</option>`).join('');
  }

  function bindFilters(){
    ['#horizonSearch','#horizonDomain','#horizonRegion','#horizonJurisdiction'].forEach(selector=>{
      const el=document.querySelector(selector);
      el.addEventListener(el.tagName==='INPUT'?'input':'change',render);
    });
  }

  async function init(){
    const summary=document.querySelector('#horizonSummary');
    const clock=document.querySelector('#horizonClock');
    clock.textContent=new Date().toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
    summary.textContent='Loading canonical horizon…';
    try {
      const [eventsResponse,changesResponse]=await Promise.all([
        fetch('data/events.json'),
        fetch('data/changes.json')
      ]);
      if(!eventsResponse.ok) throw new Error(`events.json ${eventsResponse.status}`);
      if(!changesResponse.ok) throw new Error(`changes.json ${changesResponse.status}`);
      const eventProjection=await eventsResponse.json();
      const ledger=await changesResponse.json();
      state.events=eventProjection.events||[];
      state.changes=ledger.changes||[];
      state.changeByOccurrence=latestChanges(state.changes);
      summary.dataset.registryVersion=eventProjection.metadata?.registry_version||'?';

      optionise('#horizonDomain',state.events.map(domainFor),'All signal families');
      optionise('#horizonRegion',state.events.map(event=>event.region),'All regions');
      optionise('#horizonJurisdiction',state.events.flatMap(jurisdictions),'All jurisdictions');
      bindFilters();
      render();
    } catch (error) {
      summary.innerHTML=`<span class="horizon-error">Horizon could not be loaded: ${esc(error.message)}</span>`;
    }
  }

  init();
})();
