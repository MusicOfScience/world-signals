(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const human = value => String(value ?? '').replaceAll('_',' ').toLowerCase();
  let loaded = false;

  function valueBlock(values){
    const entries=Object.entries(values||{});
    if(!entries.length) return '<span class="history-empty">None recorded</span>';
    return `<dl class="history-values">${entries.map(([key,value])=>`<dt>${esc(human(key))}</dt><dd>${esc(value===null?'null':typeof value==='object'?JSON.stringify(value):value)}</dd>`).join('')}</dl>`;
  }

  function formatReviewedAt(raw){
    if(!raw) return 'review time not recorded';
    const d=new Date(raw);
    return Number.isNaN(d.getTime())?String(raw):d.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
  }

  function renderChange(change,eventMap){
    const event=eventMap.get(change.occurrence_id);
    const title=event?.title||event?.canonical_name||change.occurrence_id;
    const basis=(change.review_basis||[]).map(item=>`<li>${esc(item)}</li>`).join('');
    const transition=(change.registry_version_before||change.registry_version_after)
      ? `${esc(change.registry_version_before||'?')} → ${esc(change.registry_version_after||'?')}`
      : 'not recorded';
    return `<article class="history-card">
      <div class="history-card-head">
        <div><p class="eyebrow">${esc(human(change.change_type))}</p><h3>${esc(title)}</h3><p class="meta"><code>${esc(change.occurrence_id)}</code> · ${esc(formatReviewedAt(change.reviewed_at))}</p></div>
        <span class="history-state">${esc(human(change.review_state||'reviewed'))}</span>
      </div>
      <div class="history-diff">
        <section><h4>Previously</h4>${valueBlock(change.old_values)}</section>
        <section><h4>Reviewed state</h4>${valueBlock(change.new_values)}</section>
      </div>
      <details>
        <summary>Why this changed</summary>
        ${basis?`<ul>${basis}</ul>`:'<p class="history-empty">No review basis recorded in this ledger entry.</p>'}
        <p class="meta">Change ID <code>${esc(change.change_id)}</code> · registry ${transition} · ${esc(human(change.commit_mode||'commit mode not recorded'))}</p>
      </details>
    </article>`;
  }

  async function loadHistory(){
    if(loaded) return;
    const target=document.querySelector('#historyCards');
    const count=document.querySelector('#historyCount');
    target.innerHTML='<p class="empty">Loading reviewed change history…</p>';
    try{
      const [changesResponse,eventsResponse]=await Promise.all([fetch('data/changes.json'),fetch('data/events.json')]);
      if(!changesResponse.ok) throw new Error(`changes.json ${changesResponse.status}`);
      if(!eventsResponse.ok) throw new Error(`events.json ${eventsResponse.status}`);
      const ledger=await changesResponse.json();
      const events=await eventsResponse.json();
      const eventMap=new Map((events.events||[]).map(event=>[event.occurrence_id,event]));
      const rows=[...(ledger.changes||[])].sort((a,b)=>String(b.reviewed_at||b.committed_at||'').localeCompare(String(a.reviewed_at||a.committed_at||'')));
      count.textContent=`${rows.length} reviewed change${rows.length===1?'':'s'} · ledger v${ledger.version||'?'}`;
      target.innerHTML=rows.length?rows.map(change=>renderChange(change,eventMap)).join(''):'<p class="empty">No reviewed changes are recorded.</p>';
      loaded=true;
    } catch(error){
      target.innerHTML=`<p class="empty">Change history could not be loaded: ${esc(error.message)}</p>`;
    }
  }

  function showHistory(){
    document.querySelector('#calendarView').hidden=true;
    document.querySelector('#indexView').hidden=true;
    document.querySelector('#monitorsView').hidden=true;
    document.querySelector('#historyView').hidden=false;
    document.querySelector('.controls').hidden=true;
    document.querySelectorAll('.viewtabs button').forEach(button=>button.setAttribute('aria-pressed',String(button.id==='historyTab')));
    loadHistory();
  }

  function hideHistory(){
    document.querySelector('#historyView').hidden=true;
    document.querySelector('#historyTab').setAttribute('aria-pressed','false');
  }

  document.querySelector('#historyTab').addEventListener('click',showHistory);
  document.querySelectorAll('.viewtabs button[data-view]').forEach(button=>button.addEventListener('click',hideHistory));
})();
