let DATA;
let MONITORS={metadata:{},routes:[]};
let PUBLIC_STATUS={};
let SOURCES={metadata:{},sources:[]};
let CHANGES={changes:[]};
let futureOnly = true;
let activeView = 'calendar';
let calendarCursor = new Date();
calendarCursor = new Date(calendarCursor.getFullYear(), calendarCursor.getMonth(), 1);
let selectedDay = null;

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));
const SEASON_TIMING_TYPES = new Set(['MONTH_BOUNDED_SEASON_WINDOW','MULTI_PHASE_SEASON_WINDOW']);
const REFERENCE_TIMEZONE = 'Australia/Melbourne';
let detailOpener = null;
let detailHistoryPushed = false;
let detailReturnHash = '';
let detailReturnScrollY = 0;
const today = new Date();
today.setHours(0,0,0,0);

function localDateKey(d){
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
function localMonthKey(d){
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
}
function parseCivilDate(raw){
  if(!raw) return null;
  const m = String(raw).slice(0,10).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? new Date(Number(m[1]), Number(m[2])-1, Number(m[3])) : null;
}
function parseMonthSortProxy(raw){
  const m=String(raw??'').match(/^(\d{4})-(\d{2})$/);
  if(!m) return null;
  const month=Number(m[2]);
  if(month<1||month>12) return null;
  return new Date(Number(m[1]),month-1,1);
}
function isSeasonWindow(e){
  return SEASON_TIMING_TYPES.has(e.timing_type) && Array.isArray(e.season_phases) && e.season_phases.length>0;
}
function seasonSortDate(e){
  if(!isSeasonWindow(e)) return null;
  return parseMonthSortProxy(e.season_phases[0]?.start_month);
}
function seasonLastMonth(e){
  if(!isSeasonWindow(e)) return null;
  return e.season_phases[e.season_phases.length-1]?.end_month||null;
}
function eventDate(e){
  if(e.start_utc){const d=new Date(e.start_utc);return isNaN(d)?null:d;}
  if(e.start_local) return parseCivilDate(e.start_local);
  if(e.date_earliest && (!e.date_latest || e.date_earliest===e.date_latest)) return parseCivilDate(e.date_earliest);
  return null;
}
function eventSortDate(e){
  return eventDate(e)||seasonSortDate(e);
}
function eventDateKey(e){
  if(isSeasonWindow(e)) return null;
  if(e.start_utc){const d=new Date(e.start_utc);return isNaN(d)?null:localDateKey(d);}
  if(e.start_local) return String(e.start_local).slice(0,10);
  if(e.date_earliest && (!e.date_latest || e.date_earliest===e.date_latest)) return e.date_earliest;
  return null;
}
function seasonWindowLabel(e){
  if(!isSeasonWindow(e)) return '';
  if(e.source_native_window_label) return String(e.source_native_window_label);
  return e.season_phases.map(p=>p.source_label).filter(Boolean).join(' · ');
}
function windowLabel(e){
  if(isSeasonWindow(e)) return seasonWindowLabel(e);
  if(e.date_earliest){
    return `${e.date_earliest}${e.date_latest&&e.date_latest!==e.date_earliest?` → ${e.date_latest}`:''}`;
  }
  return 'TBC';
}
function formatWhen(e){
  if(isSeasonWindow(e)){
    return `<strong>${esc(seasonWindowLabel(e))}</strong><br><span class="meta">month-bounded seasonal window · no day boundary asserted</span>`;
  }
  if(e.start_utc){
    const d=new Date(e.start_utc);
    return `<strong>${d.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'})}</strong><br><span class="meta">device time · source ${esc(e.source_timezone)}</span>`;
  }
  if(e.start_local){
    const raw=esc(e.start_local.replace('T',' '));
    const end=e.end_local?` → ${esc(e.end_local.replace('T',' '))}`:'';
    return `<strong>${raw}</strong>${end}<br><span class="meta">${esc(e.source_timezone||e.timing_type)}</span>`;
  }
  if(e.date_earliest){
    const end=e.date_latest && e.date_latest!==e.date_earliest?` → ${esc(e.date_latest)}`:'';
    return `<strong>${esc(e.date_earliest)}</strong>${end}<br><span class="meta">${esc(e.timing_type)}</span>`;
  }
  return '<strong>TBC</strong>';
}
function compactWhen(e){
  if(isSeasonWindow(e)) return '';
  if(e.start_utc){const d=new Date(e.start_utc);return d.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});}
  if(e.start_local && e.start_local.includes('T')) return e.start_local.slice(11,16);
  if(e.end_local && String(e.end_local).slice(0,10)!==String(e.start_local).slice(0,10)) return `→ ${String(e.end_local).slice(5,10)}`;
  return '';
}
function seasonIsCurrentOrFuture(e){
  if(!isSeasonWindow(e)) return false;
  const last=seasonLastMonth(e);
  return !!last && last>=localMonthKey(today);
}
function humanToken(value){return String(value??'').replaceAll('_',' ').toLowerCase();}
function displayToken(value){
  const text=humanToken(value).replace(/\s+/g,' ').trim();
  return text ? text.charAt(0).toUpperCase()+text.slice(1) : 'Not recorded';
}
function jurisdictionLabel(e){
  return Array.isArray(e.jurisdiction) ? e.jurisdiction.join(', ') : (e.jurisdiction||e.region||'Jurisdiction not recorded');
}
function isUnrated(value){return !value || /unrated|pending calibration/i.test(String(value));}
function formatInstant(raw,timeZone){
  if(!raw || !timeZone) return null;
  const date=new Date(raw);
  if(Number.isNaN(date.getTime())) return null;
  try{
    return new Intl.DateTimeFormat('en-AU',{
      timeZone,
      weekday:'short',day:'numeric',month:'short',year:'numeric',
      hour:'numeric',minute:'2-digit',timeZoneName:'short'
    }).format(date);
  }catch(_){return null;}
}
function formatCivil(raw,includeTime=false){
  const match=String(raw??'').match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/);
  if(!match) return raw ? String(raw).replace('T',' ') : null;
  const date=new Date(Date.UTC(Number(match[1]),Number(match[2])-1,Number(match[3])));
  const day=new Intl.DateTimeFormat('en-AU',{timeZone:'UTC',weekday:'short',day:'numeric',month:'short',year:'numeric'}).format(date);
  if(!includeTime || !match[4]) return day;
  const hour=Number(match[4]), minute=match[5];
  const clock=new Intl.DateTimeFormat('en-AU',{hour:'numeric',minute:'2-digit',hour12:true,timeZone:'UTC'}).format(new Date(Date.UTC(1970,0,1,hour,Number(minute))));
  return `${day} · ${clock}`;
}
function formatCivilRange(start,end,includeTime=false){
  const first=formatCivil(start,includeTime);
  const last=end && end!==start ? formatCivil(end,includeTime) : null;
  return last ? `${first} → ${last}` : first;
}
function sourceLocalTime(e){
  if(e.start_utc && e.source_timezone) return formatInstant(e.start_utc,e.source_timezone);
  if(e.start_utc) return formatInstant(e.start_utc,'UTC');
  if(e.start_local) return formatCivilRange(e.start_local,e.end_local,/[T]/.test(e.start_local));
  if(e.date_earliest || e.date_latest) return formatCivilRange(e.date_earliest||e.date_latest,e.date_latest||e.date_earliest);
  if(isSeasonWindow(e)) return seasonWindowLabel(e);
  if(e.source_native_date_label) return e.source_native_date_label;
  return 'No schedulable date asserted';
}
function timingDisplay(e){
  if(e.start_utc){
    const source=sourceLocalTime(e);
    const reference=formatInstant(e.start_utc,REFERENCE_TIMEZONE);
    const utc=formatInstant(e.start_utc,'UTC');
    return {kind:'exact',source,reference,utc,sourceZone:e.source_timezone||'UTC'};
  }
  if(isSeasonWindow(e)) return {kind:'window',source:seasonWindowLabel(e)||'Source-native seasonal window',note:'Month precision only; no day boundary is asserted.'};
  if(e.source_native_date_label) return {kind:'native',source:e.source_native_date_label,nativeCalendar:displayToken(e.native_calendar_system),note:'Exact in the source calendar; no authoritative Gregorian conversion is projected.'};
  if(e.start_local){
    const hasTime=/[T]/.test(e.start_local);
    const isRange=Boolean(e.end_local&&e.end_local!==e.start_local);
    return {kind:isRange?'window':(hasTime?'local':'date'),source:sourceLocalTime(e),sourceZone:e.source_timezone||'source timezone not recorded',note:hasTime&&!e.start_utc?'A canonical UTC instant is not projected, so no reference-time conversion is asserted.':isRange?'This is a source-local date window; no exact instant is asserted.':''};
  }
  if(e.date_earliest||e.date_latest) return {kind:'window',source:sourceLocalTime(e),note:displayToken(e.timing_type)};
  return {kind:'tbc',source:'TBC',note:'The authoritative source has not supplied a schedulable date.'};
}
function timingLabel(kind){
  return ({exact:'Exact time',local:'Source-local time',date:'Civil date',window:'Date window',native:'Source-native date',tbc:'Timing'}[kind]||'Timing');
}
function stateSummary(e){
  const lifecycle={PLANNED:'Upcoming',ACTIVE:'Active',COMPLETED:'Completed',POSTPONED:'Postponed',CANCELLED:'Cancelled'}[e.lifecycle]||displayToken(e.lifecycle);
  const certainty={CONFIRMED:'Confirmed',PROVISIONAL:'Provisional',TBC:'Time or date TBC',EXPECTED_WINDOW:'Expected window'}[e.certainty]||displayToken(e.certainty);
  return {lifecycle,certainty};
}
function detailHistory(e){
  return (CHANGES.changes||[]).filter(change=>change.occurrence_id===e.occurrence_id)
    .sort((a,b)=>String(a.reviewed_at||a.committed_at||'').localeCompare(String(b.reviewed_at||b.committed_at||'')));
}
function changeDate(change){
  const raw=change.reviewed_at||change.committed_at;
  if(!raw) return 'Date not recorded';
  const date=new Date(raw);
  return Number.isNaN(date.getTime())?String(raw):date.toLocaleDateString('en-AU',{day:'numeric',month:'short',year:'numeric'});
}
function changeTransition(change){
  const oldValues=change.old_values||{}, newValues=change.new_values||{};
  const parts=[];
  for(const key of ['certainty_status','lifecycle_status','start_local','start_utc','date_earliest','date_latest']){
    if(oldValues[key]!==undefined || newValues[key]!==undefined){
      const oldValue=oldValues[key]===undefined?'not recorded':oldValues[key];
      const newValue=newValues[key]===undefined?'not recorded':newValues[key];
      parts.push(`${displayToken(key)}: ${displayToken(oldValue)} → ${displayToken(newValue)}`);
    }
  }
  return parts;
}
function publicContext(e){
  const rows=[];
  if(!isUnrated(e.intrinsic_importance)) rows.push(`<dt>Importance</dt><dd>${esc(displayToken(e.intrinsic_importance))}</dd>`);
  if(!isUnrated(e.expected_market_sensitivity)) rows.push(`<dt>Expected market sensitivity</dt><dd>${esc(displayToken(e.expected_market_sensitivity))}</dd>`);
  if(!rows.length) return '';
  return `<section class="detail-section" aria-labelledby="detailContextTitle"><h3 id="detailContextTitle">Why it may matter</h3><p class="detail-section-intro">Public governed context only. These dimensions are not a forecast and do not assert that the event will move markets.</p><dl class="detail-grid detail-grid-compact">${rows.join('')}</dl></section>`;
}
function detailSource(e){
  const sourceName=e.source_institution||e.institution||e.source_id||'Authoritative source not recorded';
  return `<section class="detail-section" aria-labelledby="detailSourceTitle"><h3 id="detailSourceTitle">Source</h3><p class="detail-source-name"><strong>${esc(sourceName)}</strong><span>${esc(jurisdictionLabel(e))}</span></p>${e.source_url?`<a class="detail-source-link" href="${esc(e.source_url)}" target="_blank" rel="noopener">Open authoritative source ↗</a>`:'<p class="meta">No public source link is projected for this occurrence.</p>'}</section>`;
}
function detailHistorySection(e){
  const changes=detailHistory(e);
  const entries=changes.length?changes.slice().reverse().map(change=>{
    const transition=changeTransition(change);
    return `<article class="detail-history-entry"><div><strong>${esc(displayToken(change.change_type||'Reviewed change'))}</strong><span>${esc(changeDate(change))}</span></div>${transition.length?`<ul>${transition.map(item=>`<li>${esc(item)}</li>`).join('')}</ul>`:''}${(change.review_basis||[]).length?`<details class="detail-nested"><summary>Review basis</summary><ul>${change.review_basis.map(item=>`<li>${esc(item)}</li>`).join('')}</ul></details>`:''}<p class="meta">Change ${esc(change.change_id||'not recorded')}${change.registry_version_before||change.registry_version_after?` · registry ${esc(change.registry_version_before||'?')} → ${esc(change.registry_version_after||'?')}`:''}</p></article>`;
  }).join(''):'<p class="meta">No reviewed changes are currently projected for this occurrence.</p>';
  return `<details class="detail-section detail-disclosure"><summary><span>History</span><small>${changes.length?`${changes.length} reviewed change${changes.length===1?'':'s'}`:'No reviewed changes projected'}</small></summary><div class="detail-disclosure-body"><p class="detail-section-intro">The current state above remains primary. This history records how WORLD SIGNALS changed its understanding of the occurrence.</p>${entries}</div></details>`;
}
function detailProvenance(e){
  const rows=[];
  if(e.time_basis) rows.push(`<dt>Timing basis</dt><dd>${esc(displayToken(e.time_basis))}</dd>`);
  if(e.time_precision) rows.push(`<dt>Supported precision</dt><dd>${esc(displayToken(e.time_precision))}</dd>`);
  if(e.time_status) rows.push(`<dt>Time status</dt><dd>${esc(displayToken(e.time_status))}</dd>`);
  if(e.reference_period) rows.push(`<dt>Reference period</dt><dd>${esc(e.reference_period)}</dd>`);
  if(e.publication_datetime) rows.push(`<dt>Source publication time</dt><dd>${esc(formatCivil(e.publication_datetime,true))}${e.source_timezone?` · ${esc(e.source_timezone)}`:''}</dd>`);
  if(e.last_verified_at) rows.push(`<dt>Last verified</dt><dd>${esc(e.last_verified_at)}</dd>`);
  return `<details class="detail-section detail-disclosure"><summary><span>Method / provenance</span><small>How the public record is supported</small></summary><div class="detail-disclosure-body"><p class="detail-section-intro">This is a read-only public projection. It preserves source-native timing and does not expose private review or runtime material.</p><dl class="detail-grid detail-grid-compact">${rows.join('')||'<dt>Provenance</dt><dd>Public source and timing fields are available above.</dd>'}</dl></div></details>`;
}
function detailTechnical(e){
  const rows=[
    ['Occurrence ID',e.occurrence_id],['Series ID',e.series_id],['Event type',e.event_type],
    ['Source ID',e.source_id],['Source timezone',e.source_timezone],['Registry version',DATA.metadata?.registry_version]
  ].filter(([,value])=>value);
  if(e.start_utc) rows.push(['UTC instant',e.start_utc]);
  return `<details class="detail-section detail-disclosure"><summary><span>Technical details</span><small>Stable identifiers and machine-readable timing</small></summary><div class="detail-disclosure-body"><dl class="detail-grid detail-grid-compact">${rows.map(([label,value])=>`<dt>${esc(label)}</dt><dd><code>${esc(value)}</code></dd>`).join('')}</dl></div></details>`;
}
function detailTiming(e){
  const timing=timingDisplay(e);
  const state=stateSummary(e);
  const status=`<div class="detail-state-line"><span class="detail-state detail-state-${esc(String(e.certainty||'').toLowerCase())}">${esc(state.certainty)}</span><span>${esc(state.lifecycle)}</span></div>`;
  let body='';
  if(timing.kind==='exact') body=`<div class="detail-time-grid"><div class="detail-time-primary"><span>Source-local time · ${esc(timing.sourceZone)}</span><strong>${esc(timing.source)}</strong></div><div class="detail-time-secondary"><span>Melbourne reference · ${REFERENCE_TIMEZONE}</span><strong>${esc(timing.reference)}</strong></div></div><details class="detail-nested detail-utc"><summary>Show UTC</summary><p><strong>${esc(timing.utc)}</strong><span>Canonical UTC instant used for conversion.</span></p></details>`;
  else body=`<div class="detail-time-primary detail-time-single"><span>${esc(timingLabel(timing.kind))}${timing.sourceZone?` · ${esc(timing.sourceZone)}`:''}</span><strong>${esc(timing.source)}</strong>${timing.nativeCalendar?`<small>${esc(timing.nativeCalendar)}</small>`:''}</div>${timing.note?`<p class="detail-timing-note">${esc(timing.note)}</p>`:''}`;
  return `<section class="detail-section detail-timing" aria-labelledby="detailTimingTitle"><div class="detail-section-heading"><h3 id="detailTimingTitle">Timing</h3>${status}</div>${body}</section>`;
}
function copyText(text,status,success='Copied',failure='Copy unavailable in this browser'){
  const task=navigator.clipboard?.writeText(text);
  if(task?.then){
    task.then(()=>{status.textContent=success;}).catch(()=>{status.textContent=failure;});
    return;
  }
  const fallback=document.createElement('textarea');
  fallback.value=text;
  fallback.setAttribute('readonly','');
  fallback.style.position='fixed';
  fallback.style.opacity='0';
  document.body.appendChild(fallback);
  fallback.select();
  try{status.textContent=document.execCommand('copy')?success:failure;}
  catch(error){status.textContent=failure;}
  finally{fallback.remove();}
}
function publicCalendarUrl(){
  const url=new URL('world-signals.ics',window.location.href);
  url.hash='';
  return url.toString();
}
function eventShareUrl(e){
  const url=new URL(window.location.href);
  url.hash=detailHash(e.occurrence_id);
  return url.toString();
}
function eventSummaryText(e,{includeLink=true}={}){
  const state=stateSummary(e);
  const timing=timingDisplay(e);
  const lines=[e.canonical_name||e.title];
  if(timing.kind==='exact'){
    lines.push(`Source-local: ${timing.source} (${timing.sourceZone})`);
    lines.push(`Melbourne reference: ${timing.reference}`);
  }else{
    lines.push(`${timingLabel(timing.kind)}: ${timing.source}`);
    if(timing.nativeCalendar) lines.push(timing.nativeCalendar);
  }
  lines.push(`Status: ${state.certainty}${state.lifecycle?` · ${state.lifecycle}`:''}`);
  const source=e.institution||e.source_name||'';
  if(source) lines.push(`Source: ${source}`);
  if(includeLink) lines.push(`Public link: ${eventShareUrl(e)}`);
  return lines.join('\n');
}
function copyDetailLink(){
  const status=$('#detailCopyStatus');
  const e=DATA?.events.find(x=>x.occurrence_id===$('#detail').dataset.eventId);
  if(e) copyText(eventShareUrl(e),status,'Public link copied');
}
function copyEventSummary(){
  const status=$('#detailCopyStatus');
  const e=DATA?.events.find(x=>x.occurrence_id===$('#detail').dataset.eventId);
  if(e) copyText(eventSummaryText(e),status,'Event summary copied');
}
async function shareEvent(){
  const status=$('#detailCopyStatus');
  const e=DATA?.events.find(x=>x.occurrence_id===$('#detail').dataset.eventId);
  if(!e) return;
  if(typeof navigator.share!=='function'){
    status.textContent='Native sharing is not available here; use Copy event summary.';
    return;
  }
  try{
    await navigator.share({title:e.canonical_name||e.title,text:eventSummaryText(e,{includeLink:false}),url:eventShareUrl(e)});
    status.textContent='Share sheet opened';
  }catch(error){
    if(error?.name!=='AbortError') status.textContent='Sharing is unavailable here';
  }
}
function copyCalendarUrl(){
  copyText(publicCalendarUrl(),$('#calendarCopyStatus'),'Calendar URL copied');
}
function detailHash(id){return `#event=${encodeURIComponent(id)}`;}
function finishDetailClose(){
  const dialog=$('#detail');
  if(dialog.open) dialog.close();
  const opener=detailOpener;
  const scrollY=detailReturnScrollY;
  detailOpener=null;
  detailHistoryPushed=false;
  if(opener && typeof opener.focus==='function') opener.focus({preventScroll:true});
  if(Number.isFinite(scrollY)) window.requestAnimationFrame(()=>window.scrollTo(0,scrollY));
}
function closeDetail(){
  const dialog=$('#detail');
  if(!dialog.open) return;
  if(detailHistoryPushed && window.location.hash===detailHash(dialog.dataset.eventId)){
    window.history.back();
    return;
  }
  if(window.location.hash.startsWith('#event=')){
    const base=window.location.pathname+window.location.search+(detailReturnHash||'');
    window.history.replaceState({},'',base);
  }
  finishDetailClose();
}
function openDetailFromLocation(){
  if(!window.location.hash.startsWith('#event=') || !DATA) return;
  const id=decodeURIComponent(window.location.hash.slice('#event='.length));
  showDetail(id,{fromHash:true});
}
function showDetail(id,{fromHash=false}={}){
  const e=DATA?.events.find(x=>x.occurrence_id===id);
  if(!e){if($('#detail').open) finishDetailClose();return;}
  const dialog=$('#detail');
  if(!fromHash && window.location.hash!==detailHash(id)){
    detailOpener=document.activeElement;
    detailReturnHash=window.location.hash;
    detailReturnScrollY=window.scrollY;
    window.history.pushState({worldSignalsEvent:id,returnHash:detailReturnHash,returnScrollY:detailReturnScrollY},'',detailHash(id));
    detailHistoryPushed=true;
  }else if(fromHash){
    detailReturnHash='';
    detailReturnScrollY=window.scrollY;
  }
  dialog.dataset.eventId=id;
  const state=stateSummary(e);
  const changes=detailHistory(e);
  $('#detailUpdated').textContent=changes.length?`Last reviewed change ${changeDate(changes[changes.length-1])}`:'';
  $('#detailBody').innerHTML=`<p class="eyebrow">${esc(displayToken(e.category))} · ${esc(jurisdictionLabel(e))}</p><h2 id="detailTitle">${esc(e.canonical_name||e.title)}</h2><p id="detailSummary" class="detail-summary">${esc(e.institution||'Institution not recorded')} · ${esc(jurisdictionLabel(e))} · ${esc(state.certainty)}</p><div class="detail-actions"><button id="copyDetailLink" type="button" class="detail-copy">Copy public link</button><button id="copyEventSummary" type="button" class="detail-copy">Copy event summary</button><button id="shareEvent" type="button" class="detail-copy" hidden>Share</button><span id="detailCopyStatus" class="meta" aria-live="polite"></span></div><p class="detail-calendar-note">This public event is included in the <a href="world-signals.ics">calendar subscription</a>.</p>${detailTiming(e)}${publicContext(e)}${e.notes?`<section class="detail-section" aria-labelledby="detailNotesTitle"><h3 id="detailNotesTitle">Public context</h3><p>${esc(e.notes)}</p></section>`:''}${detailSource(e)}${detailHistorySection(e)}${detailProvenance(e)}${detailTechnical(e)}`;
  $('#copyDetailLink').addEventListener('click',copyDetailLink);
  $('#copyEventSummary').addEventListener('click',copyEventSummary);
  if(typeof navigator.share==='function') $('#shareEvent').hidden=false;
  $('#shareEvent').addEventListener('click',shareEvent);
  dialog.showModal();
  $('#closeDetail').focus({preventScroll:true});
}
function options(id,values){
  const el=$(id);
  [...new Set(values.filter(Boolean))].sort().forEach(v=>el.insertAdjacentHTML('beforeend',`<option>${esc(v)}</option>`));
}
function renderStats(){
  const m=DATA.metadata;
  $('#stats').innerHTML=`<div class="stat"><b>${m.record_count}</b><span>canonical occurrences</span></div><div class="stat"><b>${Object.keys(m.region_counts).length}</b><span>regions</span></div><div class="stat"><b>${Object.keys(m.category_counts).length}</b><span>categories</span></div><div class="stat"><b>${MONITORS.routes.length}</b><span>configured live monitor routes</span></div>`;
}
function melbourneClock(){
  return new Intl.DateTimeFormat('en-AU',{timeZone:'Australia/Melbourne',dateStyle:'medium',timeStyle:'short'}).format(new Date());
}
function publicHorizonCounts(){
  const now=Date.now();
  const ends=[24*60*60*1000,7*24*60*60*1000,30*24*60*60*1000].map(offset=>now+offset);
  return ends.map(end=>DATA.events.filter(event=>{
    if(event.lifecycle==='CANCELLED') return false;
    const date=eventSortDate(event);
    return date && date.getTime()>=now && date.getTime()<end;
  }).length);
}
function renderProductBrief(){
  const [next24,next7,next30]=publicHorizonCounts();
  $('#next24Count').textContent=next24;
  $('#next7Count').textContent=next7;
  $('#next30Count').textContent=next30;
  $('#referenceClock').textContent=`Melbourne · ${melbourneClock()}`;
  $('#horizonClock').textContent=`Melbourne · ${melbourneClock()}`;
  $('#asOfLabel').textContent=`As of ${melbourneClock()} · display context only`;
  const live=PUBLIC_STATUS.live_intelligence||{};
  const forecast=PUBLIC_STATUS.forecasts||{};
  $('#publicStatus').innerHTML=`
    <div class="status-row"><span class="status-dot neutral"></span><div><strong>Public calendar available</strong><small>${esc(PUBLIC_STATUS.canonical?.count||DATA.events.length)} known events · read-only</small></div></div>
    <div class="status-row"><span class="status-dot closed"></span><div><strong>NOW intelligence is selective</strong><small>${esc(live.internal_count||0)} reviewed observations internal · ${esc(live.public_count||0)} public</small></div></div>
    <div class="status-row"><span class="status-dot closed"></span><div><strong>Forecast values remain closed</strong><small>${esc(forecast.count||0)} pilot forecasts · publication gate closed</small></div></div>`;
  $('#forecastStatusCopy').textContent=`${forecast.count||0} pilot forecasts are maintained under review. Their values and claims remain closed on the public site until publication governance permits them.`;
}
function renderThemes(){
  const counts=new Map();
  DATA.events.forEach(event=>counts.set(event.category,(counts.get(event.category)||0)+1));
  const rows=[...counts.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8);
  $('#themeList').innerHTML=rows.map(([name,count])=>`<a class="theme-row" href="#horizon"><span>${esc(humanToken(name))}</span><strong>${count}</strong><small>calendar occurrences</small></a>`).join('');
}
function renderSources(){
  const rows=(SOURCES.sources||[]).slice(0,12);
  const total=SOURCES.metadata?.source_count||rows.length;
  const routes=SOURCES.metadata?.configured_live_monitor_routes||MONITORS.routes.length;
  $('#sourceSummary').textContent=`${total} governed sources · ${routes} actively configured routes`;
  $('#sourceList').innerHTML=rows.map(source=>`<article class="source-row"><div><strong>${esc(source.institution||source.source_id)}</strong><span>${esc(source.jurisdiction||'Jurisdiction not recorded')} · ${esc(humanToken(source.domain||'domain not recorded'))}</span></div><div><span class="source-role">${esc(humanToken(source.source_type||'governed source'))}</span><small>${esc(source.publication_status||'status not recorded')}</small></div>${source.authoritative_url?`<a href="${esc(source.authoritative_url)}" target="_blank" rel="noopener">Authoritative source ↗</a>`:''}</article>`).join('')+`<p class="source-more">Showing a representative public registry view. The full source registry is governed separately; monitored routes are not the same as all governed sources.</p>`;
}
function baseFiltered(){
  const q=$('#search').value.toLowerCase().trim();
  const region=$('#region').value, cat=$('#category').value, cer=$('#certainty').value, vis=$('#visibility').value;
  return DATA.events.filter(e=>{
    const phaseLabels=(e.season_phases||[]).map(p=>p.source_label).join(' ');
    const hay=[e.title,e.canonical_name,e.institution,e.jurisdiction,e.category,e.subcategory,e.source_native_window_label,phaseLabels].join(' ').toLowerCase();
    return (!q||hay.includes(q))&&(!region||e.region===region)&&(!cat||e.category===cat)&&(!cer||e.certainty===cer)&&(!vis||e.visibility_tier===vis);
  });
}
function indexFiltered(){
  return baseFiltered().filter(e=>{
    if(!futureOnly) return true;
    if(e.lifecycle==='ACTIVE') return true;
    if(isSeasonWindow(e)) return seasonIsCurrentOrFuture(e);
    const d=eventDate(e);
    return !d||d>=today;
  }).sort((a,b)=>(eventSortDate(a)?.getTime()??Infinity)-(eventSortDate(b)?.getTime()??Infinity));
}
function eventCard(e){
  return `<article class="event" data-id="${esc(e.occurrence_id)}"><div class="when">${formatWhen(e)}</div><div><h2>${esc(e.title)}</h2><div class="meta">${esc(e.institution)} · ${esc(jurisdictionLabel(e))}</div><div class="tags"><span class="tag certainty-${esc(e.certainty)}">${esc(displayToken(e.certainty))}</span><span class="tag">${esc(displayToken(e.category))}</span></div></div><div class="source"><b>${esc(e.region)}</b><br>${esc(e.source_institution||e.source_id||'Source not recorded')}</div></article>`;
}
function attachEventClicks(root=document){
  root.querySelectorAll('[data-event-id]').forEach(el=>el.addEventListener('click',ev=>{ev.stopPropagation();showDetail(el.dataset.eventId);}));
  root.querySelectorAll('.event[data-id]').forEach(el=>el.addEventListener('click',()=>showDetail(el.dataset.id)));
}
function renderIndex(){
  const rows=indexFiltered();
  $('#resultCount').textContent=`${rows.length} visible events`;
  $('#events').innerHTML=rows.slice(0,300).map(eventCard).join('')+(rows.length>300?'<div class="event"><div></div><div>Showing first 300 results. Narrow the filters.</div></div>':'');
  attachEventClicks($('#events'));
}
function monthBounds(){
  const start=new Date(calendarCursor.getFullYear(),calendarCursor.getMonth(),1);
  const end=new Date(calendarCursor.getFullYear(),calendarCursor.getMonth()+1,0);
  return {start,end,startKey:localDateKey(start),endKey:localDateKey(end),monthKey:localMonthKey(start)};
}
function seasonOverlapsMonth(e,monthKey){
  return isSeasonWindow(e) && e.season_phases.some(p=>p.start_month<=monthKey && p.end_month>=monthKey);
}
function windowsForMonth(rows,startKey,endKey,monthKey){
  return rows.filter(e=>{
    if(eventDateKey(e)) return false;
    if(isSeasonWindow(e)) return seasonOverlapsMonth(e,monthKey);
    if(!e.date_earliest && !e.date_latest) return false;
    const a=e.date_earliest||e.date_latest, b=e.date_latest||e.date_earliest;
    return a<=endKey && b>=startKey;
  }).sort((a,b)=>(eventSortDate(a)?.getTime()??Infinity)-(eventSortDate(b)?.getTime()??Infinity));
}
function chooseDefaultDay(byDay){
  const now=new Date();
  if(calendarCursor.getFullYear()===now.getFullYear() && calendarCursor.getMonth()===now.getMonth()) return localDateKey(now);
  const keys=[...byDay.keys()].sort();
  return keys[0]||localDateKey(new Date(calendarCursor.getFullYear(),calendarCursor.getMonth(),1));
}
function renderDayPanel(byDay){
  const rows=(byDay.get(selectedDay)||[]).sort((a,b)=>(eventDate(a)?.getTime()??0)-(eventDate(b)?.getTime()??0));
  const d=parseCivilDate(selectedDay);
  const label=d?d.toLocaleDateString(undefined,{weekday:'long',day:'numeric',month:'long',year:'numeric'}):selectedDay;
  $('#dayAgendaTitle').textContent=label;
  $('#dayAgendaCount').textContent=`${rows.length} event${rows.length===1?'':'s'}`;
  $('#dayAgendaBody').innerHTML=rows.length?rows.map(e=>`<button class="day-agenda-event" data-event-id="${esc(e.occurrence_id)}"><span>${compactWhen(e)}</span><strong>${esc(e.title)}</strong><small>${esc(e.institution)} · ${esc(e.certainty)}</small></button>`).join(''):'<p class="empty">No exact-date canonical events on this day under the current filters.</p>';
  attachEventClicks($('#dayAgendaBody'));
}
function renderCalendar(){
  const rows=baseFiltered();
  const {start,startKey,endKey,monthKey}=monthBounds();
  $('#monthLabel').textContent=start.toLocaleDateString(undefined,{month:'long',year:'numeric'});
  const byDay=new Map();
  rows.forEach(e=>{
    const key=eventDateKey(e);
    if(!key||key<startKey||key>endKey) return;
    if(!byDay.has(key)) byDay.set(key,[]);
    byDay.get(key).push(e);
  });
  if(!selectedDay || selectedDay.slice(0,7)!==startKey.slice(0,7)) selectedDay=chooseDefaultDay(byDay);

  const mondayIndex=(start.getDay()+6)%7;
  const gridStart=new Date(start); gridStart.setDate(start.getDate()-mondayIndex);
  const cells=[];
  for(let i=0;i<42;i++){
    const d=new Date(gridStart); d.setDate(gridStart.getDate()+i);
    const key=localDateKey(d), inMonth=d.getMonth()===start.getMonth();
    const events=(byDay.get(key)||[]).sort((a,b)=>(eventDate(a)?.getTime()??0)-(eventDate(b)?.getTime()??0));
    const isToday=key===localDateKey(new Date()), isSelected=key===selectedDay;
    const chips=events.slice(0,3).map(e=>`<button class="calendar-event" data-event-id="${esc(e.occurrence_id)}" title="${esc(e.title)}"><span class="calendar-time">${esc(compactWhen(e))}</span><span class="calendar-event-title">${esc(e.title)}</span></button>`).join('');
    const extra=events.length>3?`<span class="calendar-more">+${events.length-3} more</span>`:'';
    cells.push(`<div class="calendar-day ${inMonth?'':'outside'} ${events.length?'has-events':''} ${isToday?'today':''} ${isSelected?'selected':''}" data-day="${key}" role="button" tabindex="0" aria-label="${key}, ${events.length} events"><div class="day-number">${d.getDate()}${events.length?`<span class="day-count">${events.length}</span>`:''}</div>${chips}${extra}</div>`);
  }
  $('#calendarGrid').innerHTML=`<div class="weekday">Mon</div><div class="weekday">Tue</div><div class="weekday">Wed</div><div class="weekday">Thu</div><div class="weekday">Fri</div><div class="weekday weekend">Sat</div><div class="weekday weekend">Sun</div>${cells.join('')}`;
  $('#calendarGrid').querySelectorAll('.calendar-day').forEach(el=>{
    const select=()=>{selectedDay=el.dataset.day;renderCalendar();};
    el.addEventListener('click',select);
    el.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();select();}});
  });
  attachEventClicks($('#calendarGrid'));
  renderDayPanel(byDay);

  const windows=windowsForMonth(rows,startKey,endKey,monthKey);
  $('#windowCount').textContent=`${windows.length} window${windows.length===1?'':'s'}`;
  $('#calendarWindows').innerHTML=windows.length?windows.map(e=>`<button class="window-event" data-event-id="${esc(e.occurrence_id)}"><span>${esc(windowLabel(e))}</span><strong>${esc(e.title)}</strong><small>${esc(e.certainty)} · ${esc(e.institution)}${isSeasonWindow(e)?' · month precision':''}</small></button>`).join(''):'<p class="empty">No month-precision or expected-window events overlap this month under the current filters.</p>';
  attachEventClicks($('#calendarWindows'));
  $('#calendarResultCount').textContent=`${[...byDay.values()].reduce((n,x)=>n+x.length,0)} exact-date events · ${windows.length} windows`;
}
function renderMonitors(){
  const routes=MONITORS.routes||[];
  $('#monitorRoutes').innerHTML=routes.length?routes.map(route=>{
    const policy=route.positive_evidence_policy||route.change_policy||'Review-only source evidence';
    return `<article class="monitor-route"><div class="monitor-route-head"><div><p class="eyebrow">${esc(route.adapter_id)}</p><h3>${esc(route.source_institution||route.source_id)}</h3><p class="meta">${esc(route.jurisdiction)} · ${esc(route.domain)}</p></div><span class="monitor-mode">READ ONLY</span></div><dl><dt>Role</dt><dd>${esc(humanToken(route.monitor_role))}</dd><dt>Cadence</dt><dd>${esc(humanToken(route.cadence))}</dd><dt>Canonical scope</dt><dd>${(route.canonical_occurrence_ids||[]).map(x=>`<code>${esc(x)}</code>`).join(' ')||'None'}</dd><dt>Positive evidence</dt><dd>${esc(humanToken(policy))}</dd><dt>Source failure</dt><dd>${esc(humanToken(route.source_failure_policy))}</dd><dt>Registry readiness</dt><dd>${esc(humanToken(route.registry_monitoring_readiness||'pending registry promotion'))}</dd></dl><p class="monitor-foot">Runtime health is intentionally not claimed here. The scheduled GitHub Action emits a fresh source-health report and any review candidates as artefacts.</p></article>`;
  }).join(''):'<p class="empty">No live monitor routes are configured in this build.</p>';
}
function setView(view){
  activeView=view;
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
  $('#calendarView').hidden=view!=='calendar';
  $('#indexView').hidden=view!=='index';
  $('#monitorsView').hidden=view!=='monitors';
  $('.controls').hidden=view==='monitors';
  render();
}
function render(){
  if(!DATA)return;
  if(activeView==='calendar') renderCalendar();
  else if(activeView==='index') renderIndex();
  else renderMonitors();
}
async function main(){
  const [eventResponse,monitorResponse,statusResponse,sourcesResponse,changesResponse]=await Promise.all([
    fetch('data/events.json'),
    fetch('data/monitor_routes.json'),
    fetch('data/public_status.json'),
    fetch('data/sources.json'),
    fetch('data/changes.json')
  ]);
  if(!eventResponse.ok) throw new Error(`events.json ${eventResponse.status}`);
  DATA=await eventResponse.json();
  if(monitorResponse.ok) MONITORS=await monitorResponse.json();
  if(statusResponse.ok) PUBLIC_STATUS=await statusResponse.json();
  if(sourcesResponse.ok) SOURCES=await sourcesResponse.json();
  if(changesResponse.ok) CHANGES=await changesResponse.json();
  renderProductBrief();
  renderThemes();
  renderSources();
  renderStats();
  options('#region',DATA.events.map(x=>x.region));
  options('#category',DATA.events.map(x=>x.category));
  options('#certainty',DATA.events.map(x=>x.certainty));
  options('#visibility',DATA.events.map(x=>x.visibility_tier));
  document.querySelectorAll('.controls input,.controls select').forEach(x=>x.addEventListener('input',render));
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
  $('#futureOnly').addEventListener('click',()=>{futureOnly=!futureOnly;$('#futureOnly').setAttribute('aria-pressed',String(futureOnly));renderIndex();});
  $('#prevMonth').addEventListener('click',()=>{calendarCursor=new Date(calendarCursor.getFullYear(),calendarCursor.getMonth()-1,1);selectedDay=null;renderCalendar();});
  $('#nextMonth').addEventListener('click',()=>{calendarCursor=new Date(calendarCursor.getFullYear(),calendarCursor.getMonth()+1,1);selectedDay=null;renderCalendar();});
  $('#todayMonth').addEventListener('click',()=>{const n=new Date();calendarCursor=new Date(n.getFullYear(),n.getMonth(),1);selectedDay=localDateKey(n);renderCalendar();});
  $('#copyCalendarUrl').addEventListener('click',copyCalendarUrl);
  $('#closeDetail').addEventListener('click',closeDetail);
  $('#detail').addEventListener('cancel',event=>{event.preventDefault();closeDetail();});
  window.addEventListener('popstate',()=>{
    if(window.location.hash.startsWith('#event=')) openDetailFromLocation();
    else if($('#detail').open) finishDetailClose();
  });
  window.addEventListener('hashchange',()=>{
    if(window.location.hash.startsWith('#event=')) openDetailFromLocation();
    else if($('#detail').open) finishDetailClose();
  });
  setView('calendar');
  openDetailFromLocation();
}
main().catch(err=>{
  console.error(err);
  document.body.insertAdjacentHTML('beforeend',`<div class="fatal">WORLD SIGNALS could not load the site projection: ${esc(err.message)}</div>`);
});
