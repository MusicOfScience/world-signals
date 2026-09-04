(() => {
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const human=value=>String(value??'').replaceAll('_',' ').toLowerCase();

  function ensureSection(){
    const view=document.querySelector('#operationsView');
    if(!view||document.querySelector('#opsBiosecuritySection')) return;
    const governance=document.querySelector('#opsGovernanceSummary')?.closest('.ops-section');
    const section=document.createElement('section');
    section.className='ops-section ops-biosecurity-section';
    section.id='opsBiosecuritySection';
    section.innerHTML=`
      <div class="section-heading"><div><p class="eyebrow">CROSS-DOMAIN COVERAGE</p><h3>Biosecurity system map</h3></div><span id="opsBiosecurityCount" class="meta"></span></div>
      <p class="meta">This is a noncanonical analytical/coverage overlay. It makes cross-system gaps visible without moving events between primary categories or turning research candidates into events.</p>
      <div id="opsBiosecuritySummary" class="ops-summary-grid"><p class="empty">Loading biosecurity overlay…</p></div>
      <div id="opsBiosecuritySystems" class="ops-sources"></div>
      <div class="section-heading ops-candidate-heading"><div><p class="eyebrow">NONCANONICAL RESEARCH NODES</p><h3>Institutions still behind admission gates</h3></div></div>
      <p class="meta">These nodes have no canonical series or occurrence IDs. They remain research backlog until source, timing, rights and admission review is complete.</p>
      <div id="opsBiosecurityCandidates" class="ops-sources"></div>`;
    if(governance) view.insertBefore(section,governance); else view.appendChild(section);
  }

  function systemCard(system){
    const canonical=system.canonical_series_count>0
      ? `<span class="ops-static-badge">CANONICAL SERIES MAPPED</span>`
      : `<span class="ops-static-badge">NO CANONICAL SERIES YET</span>`;
    return `<article class="ops-source-card">
      <div><p class="eyebrow"><code>${esc(system.system_id)}</code></p><h4>${esc(system.label)}</h4><p class="meta">${esc(system.description)}</p></div>
      <div class="ops-source-statuses">
        <span><b>Canonical series</b>${esc(system.canonical_series_count)}</span>
        <span><b>Canonical occurrences</b>${esc(system.canonical_occurrence_count)}</span>
        <span><b>Candidate nodes</b>${esc(system.candidate_node_count)}</span>
      </div>${canonical}
    </article>`;
  }

  function candidateCard(node){
    const link=node.authority_url?`<a href="${esc(node.authority_url)}" target="_blank" rel="noreferrer">institutional authority ↗</a>`:'';
    return `<article class="ops-source-card">
      <div class="ops-card-head"><div><p class="eyebrow"><code>${esc(node.candidate_node_id)}</code></p><h4>${esc(node.institution)}</h4></div><span class="ops-static-badge">NONCANONICAL CANDIDATE</span></div>
      <p>${esc(node.authority_basis)}</p>
      <dl class="ops-route-values">
        <dt>System</dt><dd>${(node.system_ids||[]).map(id=>`<code>${esc(id)}</code>`).join(' ')}</dd>
        <dt>Cross-cutting links</dt><dd>${(node.relationship_ids||[]).map(id=>`<code>${esc(id)}</code>`).join(' ')||'None recorded'}</dd>
        <dt>Status</dt><dd>${esc(human(node.canonical_status))}</dd>
        <dt>Next gate</dt><dd>${esc(node.next_gate)}</dd>
      </dl>${link}
    </article>`;
  }

  function render(data){
    const m=data.metadata||{};
    document.querySelector('#opsBiosecurityCount').textContent=`${m.mapped_canonical_series_count||0} mapped series · ${m.candidate_node_count||0} candidate nodes`;
    document.querySelector('#opsBiosecuritySummary').innerHTML=`
      <section class="ops-summary-block"><h4>Canonical footprint</h4><div class="ops-summary-list"><div><span>mapped WHO series</span><b>${esc(m.mapped_canonical_series_count||0)}</b></div><div><span>mapped occurrences</span><b>${esc(m.mapped_canonical_occurrence_count||0)}</b></div></div></section>
      <section class="ops-summary-block"><h4>Boundary</h4><div class="ops-summary-list"><div><span>candidate nodes canonical</span><b>NO</b></div><div><span>population authorised</span><b>NO</b></div><div><span>primary categories changed</span><b>NO</b></div></div></section>`;
    document.querySelector('#opsBiosecuritySystems').innerHTML=(data.systems||[]).map(systemCard).join('')||'<p class="empty">No biosecurity systems recorded.</p>';
    document.querySelector('#opsBiosecurityCandidates').innerHTML=(data.candidate_nodes||[]).map(candidateCard).join('')||'<p class="empty">No noncanonical candidate nodes recorded.</p>';
  }

  async function load(){
    ensureSection();
    try{
      const response=await fetch('data/biosecurity.json');
      if(!response.ok) throw new Error(`HTTP ${response.status}`);
      const data=await response.json();
      render(data);
    }catch(error){
      const target=document.querySelector('#opsBiosecuritySummary');
      if(target) target.innerHTML=`<article class="ops-runtime-unavailable"><p class="eyebrow">BIOSECURITY OVERLAY UNAVAILABLE</p><h3>No analytical overlay in this build</h3><p>${esc(error.message||error)}</p><p class="meta">This does not alter canonical coverage or imply candidate admission.</p></article>`;
    }
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',load,{once:true}); else load();
})();
