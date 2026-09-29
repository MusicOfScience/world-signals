(() => {
  const states = {
    PRE_EVENT: {
      title: 'RBA monetary policy decision',
      body: '<p class="now-meta">Due today · 2:30 pm AEST</p><p class="now-note">Scheduled decision. No outcome is shown in this state.</p>'
    },
    EVENT_TIME_PASSED_AWAITING_CONFIRMATION: {
      title: 'RBA monetary policy decision',
      body: '<p class="now-meta confirming">Decision time passed · Awaiting confirmed outcome</p><p class="now-note">Elapsed time does not confirm completion.</p>'
    },
    CONFIRMED_OUTCOME: {
      institution: 'RESERVE BANK OF AUSTRALIA',
      result: 'Cash rate raised to 4.60%',
      body: '<p class="now-meta">+25 bp · 29 September · RBA decision was unanimous</p><p class="now-note">FIXTURE ONLY · verified official-source result; not admitted to production.</p>'
    },
    CONFIRMED_OUTCOME_WITH_ANALYSIS: {
      institution: 'RESERVE BANK OF AUSTRALIA',
      result: 'Cash rate raised to 4.60%',
      body: '<p class="now-meta">+25 bp · 29 September · RBA decision was unanimous</p><p class="now-note">FIXTURE ONLY · not admitted to production.</p><a class="analysis-link" href="#analysis-destination">Read analysis →</a>'
    }
  };
  const select = document.querySelector('#prototype-state');
  const content = document.querySelector('#now-content');
  const clock = document.querySelector('#device-time');
  const render = () => {
    const state = states[select.value];
    const heading = state.result
      ? `<p class="analysis-source">${state.institution}</p><h2 class="now-result">${state.result}</h2>`
      : `<h2 class="now-title">${state.title}</h2>`;
    content.innerHTML = heading + state.body;
  };
  const updateDeviceTime = () => {
    clock.dateTime = new Date().toISOString();
    clock.textContent = new Intl.DateTimeFormat(undefined, {
      hour: 'numeric', minute: '2-digit', timeZoneName: 'short'
    }).format(new Date());
  };
  select.addEventListener('change', render);
  render();
  updateDeviceTime();
})();
