let DATA;
let futureOnly = true;
let activeView = 'calendar';
let calendarCursor = new Date();
calendarCursor = new Date(calendarCursor.getFullYear(), calendarCursor.getMonth(), 1);
let selectedDay = null;

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today = new Date();
today.setHours(0,0,0,0);

function localDateKey(d){
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
function parseCivilDate(raw){
  if(!raw) return null;
  const m = String(raw).slice(0,10).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? new Date(Number(m[1]), Number(m[2])-1, Number(m[3])) : null;
}
function eventDate(e){
  if(e.start_utc){const d=new Date(e.start_utc);return isNaN(d)?null:d;}
  if(e.start_local) return parseCivilDate(e.start_local);
  if(e.date_earliest && (!e.date_latest || e.date_earliest===e.date_latest)) return parseCivilDate(e.date_earliest);
  return null;
}
function eventDateKey(e){
  if(e.start_utc){const d=new Date(e.start_utc);return isNaN(d)?null:localDateKey(d);}
  if(e.start_local) return String(e.start_local).slice(0,10);
  if(e.date_earliest && (!e.date_latest || e.date_earliest===e.date_latest)) return e.date_earliest;
  return null;
}
function formatWhen(e){
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
  if(e.start_utc){const d=new Date(e.start_utc);return d.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});}
  if(e.start_local && e.start_local.includes('T')) return e.start_local.slice(11,16);
  if(e.end_local && String(e.end_local).slice(0,10)!==String(e.start_local).slice(0,10)) return `→ ${String(e.end_local).slice(5,10)}`;
  return '';
}
function options(id,values){
  const el=$(id);
  [...new Set(values.filter(Boolean))].sort().forEach(v=>el.insertAdjacentHTML('beforeend',`<option>${esc(v)}</option>`));
}
function renderStats(){
  const m=DATA.metadata;
  $('#stats').innerHTML=`<div class="stat"><b>${m.record_count}</b><span>canonical occurrences</span></div><div class="stat"><b>${Object.keys(m.region_counts).length}</b><span>regions</span></div><div class="stat"><b>${Object.keys(m.category_counts).length}</b><span>categories</span></div><div class="stat"><b>0</b><span>automatic commits</span></div>`;
}
function baseFiltered(){
  const q=$('#search').value.toLowerCase().trim();
  const region=$('#region').value, cat=$('#category').value, cer=$('#certainty').value, vis=$('#visibility').value;
  return DATA.events.filter(e=>{
    const hay=[e.title,e.canonical_name,e.institution,e.jurisdiction,e.category,e.subcategory].join(' ').toLowerCase();
    return (!q||hay.includes(q))&&(!region||e.region===region)&&(!cat||e.category===cat)&&(!cer||e.certainty===cer)&&(!vis||e.visibility_tier===vis);
  });
}
function indexFiltered(){
  return baseFiltered().filter(e=>{
    const d=eventDate(e);
    return !futureOnly||!d||d>=today||e.lifecycle==='ACTIVE';
  }).sort((a,b)=>(eventDate(a)?.getTime()??Infinity)-(eventDate(b)?.getTime()??Infinity));
}
function eventCard(e){
  return `<article class="event" data-id="${esc(e.occurrence_id)}"><div class="when">${formatWhen(e)}</div><div><h2>${esc(e.title)}</h2><div class="meta">${esc(e.institution)} · ${esc(e.jurisdiction)}</div><div class="tags"><span class="tag certainty-${esc(e.certainty)}">${esc(e.certainty)}</span><span class="tag">${esc(e.category)}</span><span class="tag">${esc(e.visibility_tier)}</span></div></div><div class="source"><b>${esc(e.region)}</b><br>${esc(e.source_id)}<br><span class="meta">${esc(e.monitoring_readiness||'route not classified')}</span></div></article>`;
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
  return {start,end,startKey:localDateKey(start),endKey:localDateKey(end)};
}
function windowsForMonth(rows,startKey,endKey){
  return rows.filter(e=>{
    if(eventDateKey(e)) return false;
    if(!e.date_earliest && !e.date_latest) return false;
    const a=e.date_earliest||e.date_latest, b=e.date_latest||e.date_earliest;
    return a<=endKey && b>=startKey;
  }).sort((a,b)=>String(a.date_earliest||'').localeCompare(String(b.date_earliest||'')));
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
  const {start,end,startKey,endKey}=monthBounds();
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

  const windows=windowsForMonth(rows,startKey,endKey);
  $('#windowCount').textContent=`${windows.length} window${windows.length===1?'':'s'}`;
  $('#calendarWindows').innerHTML=windows.length?windows.map(e=>`<button class="window-event" data-event-id="${esc(e.occurrence_id)}"><span>${esc(e.date_earliest||'TBC')}${e.date_latest&&e.date_latest!==e.date_earliest?` → ${esc(e.date_latest)}`:''}</span><strong>${esc(e.title)}</strong><small>${esc(e.certainty)} · ${esc(e.institution)}</small></button>`).join(''):'<p class="empty">No month-precision or expected-window events overlap this month under the current filters.</p>';
  attachEventClicks($('#calendarWindows'));
  $('#calendarResultCount').textContent=`${[...byDay.values()].reduce((n,x)=>n+x.length,0)} exact-date events · ${windows.length} windows`;
}
function setView(view){
  activeView=view;
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
  $('#calendarView').hidden=view!=='calendar';
  $('#indexView').hidden=view!=='index';
  render();
}
function showDetail(id){
  const e=DATA.events.find(x=>x.occurrence_id===id); if(!e)return;
  $('#detailBody').innerHTML=`<p class="eyebrow">${esc(e.category)} · ${esc(e.region)}</p><h2>${esc(e.canonical_name)}</h2><dl class="detail-grid"><dt>Occurrence ID</dt><dd>${esc(e.occurrence_id)}</dd><dt>Series ID</dt><dd>${esc(e.series_id)}</dd><dt>Timing</dt><dd>${formatWhen(e)}</dd><dt>Certainty</dt><dd>${esc(e.certainty)}</dd><dt>Lifecycle</dt><dd>${esc(e.lifecycle)}</dd><dt>Institution</dt><dd>${esc(e.institution)}</dd><dt>Jurisdiction</dt><dd>${esc(e.jurisdiction)}</dd><dt>Importance</dt><dd>${esc(e.intrinsic_importance)}</dd><dt>Expected sensitivity</dt><dd>${esc(e.expected_market_sensitivity)}</dd><dt>Source</dt><dd>${e.source_url?`<a href="${esc(e.source_url)}" target="_blank" rel="noopener">${esc(e.source_institution||e.source_id)}</a>`:esc(e.source_id)}</dd><dt>Monitor route</dt><dd>${esc(e.monitoring_readiness)} / ${esc(e.automated_monitoring_use)}</dd><dt>Notes</dt><dd>${esc(e.notes)}</dd></dl>`;
  $('#detail').showModal();
}
function render(){
  if(!DATA)return;
  if(activeView==='calendar') renderCalendar(); else renderIndex();
}
async function main(){
  DATA=await fetch('data/events.json').then(r=>{if(!r.ok)throw new Error(`events.json ${r.status}`);return r.json();});
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
  $('#closeDetail').addEventListener('click',()=>$('#detail').close());
  setView('calendar');
}
main().catch(err=>{
  console.error(err);
  document.body.insertAdjacentHTML('beforeend',`<div class="fatal">WORLD SIGNALS could not load the site projection: ${esc(err.message)}</div>`);
});
