(()=>{
  let COVERAGE=null;
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const human=s=>String(s??'').replaceAll('_',' ').toLowerCase();
  const pct=v=>Number.isFinite(Number(v))?`${(Number(v)*100).toFixed(1)}%`:'—';

  function rowFlagged(row,kind){
    const flags=COVERAGE?.diagnostic_flags||{};
    if(kind==='region'){
      return (flags.regions_with_fewer_than_10_unique_series||[]).includes(row.region)
        || (flags.regions_with_fewer_than_8_unique_institutions||[]).includes(row.region);
    }
    return (flags.categories_with_fewer_than_5_unique_series||[]).includes(row.category);
  }

  function table(rows,kind){
    const label=kind==='region'?'Region':'Category';
    const key=kind==='region'?'region':'category';
    return `<div class="coverage-table-wrap"><table class="coverage-table"><thead><tr><th>${label}</th><th>Occurrences</th><th>Series</th><th>Institutions</th><th>Sources</th><th>Occ/series</th></tr></thead><tbody>${rows.map(row=>`<tr class="${rowFlagged(row,kind)?'coverage-flagged':''}"><th scope="row">${esc(kind==='category'?human(row[key]):row[key])}${rowFlagged(row,kind)?'<span class="coverage-flag">review</span>':''}</th><td>${esc(row.occurrence_count)}</td><td>${esc(row.unique_series_count)}</td><td>${esc(row.unique_institution_count)}</td><td>${esc(row.unique_source_count)}</td><td>${esc(row.occurrences_per_series)}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function renderPrompts(){
    const f=COVERAGE.diagnostic_flags||{};
    const prompts=[];
    (f.regions_with_fewer_than_10_unique_series||[]).forEach(x=>prompts.push(`<li><strong>${esc(x)}</strong> has fewer than 10 distinct canonical series.</li>`));
    (f.regions_with_fewer_than_8_unique_institutions||[]).forEach(x=>prompts.push(`<li><strong>${esc(x)}</strong> has fewer than 8 distinct institutions.</li>`));
    (f.categories_with_fewer_than_5_unique_series||[]).forEach(x=>prompts.push(`<li><strong>${esc(human(x))}</strong> has fewer than 5 distinct series.</li>`));
    document.querySelector('#coveragePrompts').innerHTML=prompts.length?`<ul>${prompts.join('')}</ul><p class="meta">${esc(f.note||'These are review prompts, not population quotas.')}</p>`:'<p class="empty">No mechanical threshold prompts in this build.</p>';
  }

  function render(){
    if(!COVERAGE) return;
    const m=COVERAGE.metadata||{};
    document.querySelector('#coverageStats').innerHTML=`<div class="stat"><b>${esc(m.unique_series_count)}</b><span>distinct series</span></div><div class="stat"><b>${esc(m.unique_institution_count)}</b><span>institutions</span></div><div class="stat"><b>${esc(m.unique_source_count)}</b><span>canonical sources in use</span></div><div class="stat"><b>${pct(m.monetary_plus_macro_occurrence_share)}</b><span>occurrences from monetary + macro</span></div>`;
    document.querySelector('#coverageRegions').innerHTML=table(COVERAGE.by_region||[],'region');
    document.querySelector('#coverageCategories').innerHTML=table(COVERAGE.by_category||[],'category');
    renderPrompts();
    document.querySelector('#coverageFrequency').innerHTML=(COVERAGE.high_frequency_series||[]).map(row=>`<article class="coverage-frequency-row"><div><code>${esc(row.series_id)}</code><strong>${esc(row.institution)}</strong><span>${esc(row.region)} · ${esc(human(row.category))}</span></div><b>${esc(row.occurrence_count)}<small> occurrences</small></b></article>`).join('')||'<p class="empty">No recurrence concentration data in this build.</p>';
    document.querySelector('#coverageVersion').textContent=`Canonical v${m.canonical_registry_version||'—'} · reference ${m.canonical_reference_date||'—'} · ${m.occurrence_count||'—'} occurrences`;
  }

  async function loadCoverage(){
    if(COVERAGE){render();return;}
    const response=await fetch('data/coverage.json',{cache:'no-store'});
    if(!response.ok) throw new Error(`coverage projection ${response.status}`);
    COVERAGE=await response.json();
    render();
  }

  function showCoverage(){
    ['#calendarView','#indexView','#monitorsView','#operationsView','#historyView'].forEach(sel=>{const el=document.querySelector(sel);if(el)el.hidden=true;});
    document.querySelector('#coverageView').hidden=false;
    document.querySelector('.controls').hidden=true;
    document.querySelectorAll('.viewtabs button').forEach(button=>button.setAttribute('aria-pressed',String(button.id==='coverageTab')));
    loadCoverage().catch(error=>{
      document.querySelector('#coveragePrompts').innerHTML=`<p class="empty">Coverage projection unavailable: ${esc(error.message)}</p>`;
    });
  }

  function hideCoverage(){
    document.querySelector('#coverageView').hidden=true;
  }

  document.querySelector('#coverageTab').addEventListener('click',showCoverage);
  document.querySelectorAll('.viewtabs button:not(#coverageTab)').forEach(button=>button.addEventListener('click',hideCoverage));
})();
