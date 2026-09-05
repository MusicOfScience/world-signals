(() => {
  const TARGET_TYPE='SOURCE_NATIVE_CALENDAR_DATE';
  const UNRESOLVED='UNRESOLVED_AUTHORITATIVE_CONVERSION';
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[ch]));
  const human=value=>String(value??'').replaceAll('_',' ').toLowerCase();

  function calendarName(value){
    if(value==='BIKRAM_SAMBAT_NEPAL') return 'Bikram Sambat (Nepal)';
    return human(value||'source-native calendar');
  }

  function sourceLink(event){
    return event.source_url
      ? `<a href="${esc(event.source_url)}" target="_blank" rel="noopener">authoritative source</a>`
      : `<span>${esc(event.source_id||'source not projected')}</span>`;
  }

  function card(event){
    return `<article class="native-date-card">
      <div class="native-date-when">
        <strong>${esc(event.source_native_date_label||'source-native date')}</strong>
        <span>${esc(calendarName(event.native_calendar_system))}</span>
      </div>
      <div class="native-date-main">
        <p class="native-date-domain">Exact in source calendar</p>
        <h4>${esc(event.title||event.canonical_name)}</h4>
        <p class="meta">${esc(event.institution||'')} · ${esc(event.jurisdiction||event.region||'')}</p>
        <div class="native-date-tags">
          <span>${esc(event.certainty||'TBC')}</span>
          <span>Gregorian resolution pending</span>
        </div>
        <p class="native-date-note">No synthetic civil date. This occurrence will enter the Gregorian horizon only when a competent source supplies an authoritative mapping.</p>
      </div>
      <div class="native-date-source">${sourceLink(event)}</div>
    </article>`;
  }

  async function init(){
    const target=document.querySelector('#nativeCalendarDates');
    const summary=document.querySelector('#nativeCalendarSummary');
    if(!target||!summary) return;
    summary.textContent='Loading source-native dates…';
    try {
      const response=await fetch('data/events.json');
      if(!response.ok) throw new Error(`events.json ${response.status}`);
      const projection=await response.json();
      const rows=(projection.events||[]).filter(event=>
        event.timing_type===TARGET_TYPE &&
        event.gregorian_resolution_status===UNRESOLVED &&
        event.lifecycle!=='CANCELLED'
      );
      rows.sort((a,b)=>String(a.source_native_date_label||'').localeCompare(String(b.source_native_date_label||'')));
      target.innerHTML=rows.length
        ? rows.map(card).join('')
        : '<p class="native-date-empty">No canonical source-native dates currently await authoritative Gregorian resolution.</p>';
      summary.innerHTML=rows.length
        ? `<strong>${rows.length}</strong> canonical occurrence${rows.length===1?'':'s'} exact in a source calendar but not yet Gregorian-schedulable.`
        : 'No unresolved source-native calendar dates.';
    } catch (error) {
      summary.textContent='Source-native date projection unavailable.';
      target.innerHTML=`<p class="native-date-empty">${esc(error.message)}</p>`;
    }
  }

  document.addEventListener('DOMContentLoaded',init);
})();
