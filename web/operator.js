(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const human = value => String(value ?? 'not recorded').replaceAll('_',' ').toLowerCase();
  const when = value => value ? new Date(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}) : 'not recorded';
  const card = (label, value, note='') => `<article class="card"><span class="card-label">${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`;
  function render(data){
    const system=data.system||{};
    const monitor=system.last_monitor_snapshot||{};
    const runtime=system.local_runtime||{};
    document.querySelector('#systemState').textContent=human(monitor.status||monitor.availability||'snapshot unavailable');
    document.querySelector('#systemGrid').innerHTML=[
      card('Last monitor sweep',when(monitor.run_at||monitor.retrieved_at),monitor.execution_mode||'No retained run embedded'),
      card('Healthy routes',monitor.healthy_adapter_count ?? '—','recorded at last sweep'),
      card('Degraded routes',monitor.degraded_adapter_count ?? '—','source-specific evidence only'),
      card('Checkpoint/runtime',runtime.availability||'not available','local operator evidence'),
    ].join('');
    const counts=runtime.candidate_counts||{};
    const examples=runtime.examples||[];
    document.querySelector('#reviewGrid').innerHTML=[
      card('Observation candidates',counts.observation_candidates||0,'review only · not public truth'),
      card('Signal candidates',counts.signal_candidates||0,'review only · no automatic admission'),
      card('Review items',counts.review_items||0,'local runtime evidence'),
      `<article class="card wide"><span class="card-label">Attention examples</span>${examples.length?`<ul>${examples.map(item=>`<li><code>${esc(item.id||'unidentified')}</code> · ${esc(human(item.kind))} · ${esc(item.source_id||'source not recorded')} · ${esc(human(item.state))}</li>`).join('')}</ul>`:'<small>No local candidate or review artefact was found.</small>'}</article>`,
    ].join('');
    const labels={canonical:'Canonical occurrences',sources:'Governed sources',monitor_routes:'Monitor routes',live_observations:'Live observations',signals:'Signals',relationships:'Relationships',risks:'Risks / regimes',scenarios:'Scenarios',forecasts:'Forecasts',outcomes:'Outcomes',evaluation:'Evaluation'};
    document.querySelector('#governedGrid').innerHTML=Object.entries(data.governed||{}).map(([key,item])=>`<article class="layer-card"><span>${esc(labels[key]||key)}</span><strong>${esc(item.count)}</strong><small>${esc(human(item.state||'active'))}</small></article>`).join('');
    document.querySelector('#forecastGrid').innerHTML=(data.forecasts||[]).map(item=>`<article class="forecast-card"><span class="card-label">${esc(item.forecast_id)}</span><h3>${esc(item.question)}</h3><dl><dt>Type</dt><dd>${esc(human(item.forecast_type))}</dd><dt>Issued</dt><dd>${esc(when(item.issuance))}</dd><dt>Cutoff</dt><dd>${esc(when(item.information_cutoff))}</dd><dt>State</dt><dd>${esc(human(item.lifecycle_state))} · ${esc(human(item.review_state))}</dd><dt>Resolution</dt><dd>${esc(when(item.resolution_window))}</dd><dt>Authority</dt><dd>${esc((item.resolution_source_ids||[]).join(', ')||'not recorded')}</dd></dl></article>`).join('')||'<p>No governed forecasts are present.</p>';
  }
  fetch('data/operator.json').then(response => { if(!response.ok) throw new Error(`operator.json ${response.status}`); return response.json(); }).then(render).catch(error => { document.body.insertAdjacentHTML('beforeend',`<p class="fatal">Operator data could not be loaded: ${esc(error.message)}</p>`); });
})();
