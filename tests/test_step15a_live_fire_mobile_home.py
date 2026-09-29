from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Step15ALiveFireTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the browser-clock fixture")
    def test_brief_clock_boundary_and_open_document_are_deterministic(self):
        harness = r"""
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync('web/briefing.js', 'utf8');
const events = [
  {occurrence_id:'WSO-d2a7c4e4416b505b',title:'RBA rate decision',institution:'Reserve Bank of Australia',start_utc:'2026-09-29T04:30:00Z',lifecycle:'PLANNED',certainty:'CONFIRMED'},
  {occurrence_id:'WSO-90410e15e0eb58f9',title:'RBA press conference',institution:'Reserve Bank of Australia',start_utc:'2026-09-29T05:30:00Z',lifecycle:'PLANNED',certainty:'CONFIRMED'},
  {occurrence_id:'WSO-MAC-A-0013',title:'Australia CPI — August 2026',institution:'Australian Bureau of Statistics',start_utc:'2026-09-30T01:30:00Z',lifecycle:'PLANNED',certainty:'CONFIRMED'}
];
async function renderAt(initialTime, advanceTo) {
  let now = Date.parse(initialTime), html = '', fetchCount = 0, timers = 0, listeners = [];
  class FixtureDate extends Date { static now() { return now; } }
  const target = { set innerHTML(value) { html = value; }, get innerHTML() { return html; }, querySelectorAll() { return []; } };
  const document = { querySelector(selector) { return selector === '#briefingLanes' ? target : null; }, addEventListener(...args) { listeners.push(['document', ...args]); } };
  const window = { addEventListener(...args) { listeners.push(['window', ...args]); } };
  const sandbox = {
    Date: FixtureDate, document, window, console,
    setInterval(fn, ms) { timers += 1; return timers; },
    setTimeout(fn, ms) { timers += 1; return timers; },
    fetch: async url => {
      fetchCount += 1;
      const body = url.includes('briefing')
        ? {calendar:{candidate_occurrence_ids:events.map(event=>event.occurrence_id)},forecast_resolution:{forecast_ids:[]},latest_reviewed_analysis:null}
        : url.includes('outlook') ? {forecasts:[]}
        : url.includes('events') ? {events}
        : {reviews:[]};
      return {ok:true,json:async()=>body};
    }
  };
  vm.runInNewContext(source, sandbox);
  await new Promise(resolve=>setImmediate(resolve));
  const selected = () => (html.match(/href="#event=([^"]+)"/) || [])[1] || null;
  const beforeAdvance = selected();
  if (advanceTo) {
    now = Date.parse(advanceTo);
    await new Promise(resolve=>setImmediate(resolve));
  }
  return {selected:beforeAdvance,afterAdvance:selected(),fetchCount,timers,listeners,html};
}
(async()=>{
  const rows = {
    before: await renderAt('2026-09-29T04:29:00Z'),
    exact: await renderAt('2026-09-29T04:30:00Z'),
    after: await renderAt('2026-09-29T04:31:00Z'),
    evening: await renderAt('2026-09-29T09:13:00Z'),
    open: await renderAt('2026-09-29T04:29:00Z','2026-09-29T09:13:00Z')
  };
  process.stdout.write(JSON.stringify(rows));
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(
            ["node", "-e", harness], cwd=ROOT, check=True, capture_output=True, text=True
        )
        rows = json.loads(result.stdout)
        rba = "WSO-d2a7c4e4416b505b"
        self.assertEqual(rows["before"]["selected"], rba)
        self.assertEqual(rows["exact"]["selected"], rba)
        self.assertEqual(rows["after"]["selected"], "WSO-90410e15e0eb58f9")
        self.assertEqual(rows["evening"]["selected"], "WSO-MAC-A-0013")
        self.assertEqual(rows["open"]["selected"], rba)
        self.assertEqual(rows["open"]["afterAdvance"], rba)
        self.assertEqual(rows["open"]["fetchCount"], 4)
        self.assertEqual(rows["open"]["timers"], 0)
        self.assertEqual(rows["open"]["listeners"], [])
        self.assertNotIn("Decision completed", rows["after"]["html"])

    def test_current_rba_route_is_schedule_only_and_fail_closed(self):
        expectations = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        route = next(row for row in expectations["adapters"] if row["adapter_id"] == "RBA_MPB_CALENDAR")
        self.assertEqual(route["monitor_role"], "RBA_MPB_AUTHORITATIVE_SCHEDULE_CHANGE_SENTINEL")
        self.assertEqual(route["cadence"], "DAILY")
        self.assertEqual(route["elapsed_time_policy"], "NO_COMPLETION_INFERENCE")
        self.assertIs(route["automatic_commit_allowed"], False)
        self.assertEqual(route["request_budget_per_run"], 3)
        self.assertIn("WSO-d2a7c4e4416b505b", route["canonical_occurrence_ids"])

    def test_canonical_occurrence_is_still_planned_and_release_is_not_production_data(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        row = next(item for item in canonical["records"] if item["occurrence_id"] == "WSO-d2a7c4e4416b505b")
        self.assertEqual(row["lifecycle_status"], "PLANNED")
        self.assertEqual(row["start_local"], "2026-09-29T14:30:00")
        self.assertEqual(row["source_timezone"], "Australia/Sydney")
        public_events = json.loads((ROOT / "docs/data/events.json").read_text())["events"]
        public_event = next(item for item in public_events if item["occurrence_id"] == row["occurrence_id"])
        self.assertEqual(public_event["start_utc"], "2026-09-29T04:30:00Z")
        self.assertNotIn("4.60", json.dumps(public_event))
        self.assertNotIn("unanimous", json.dumps(public_event).lower())


class Step15AMobilePrototypeTests(unittest.TestCase):
    def test_prototype_is_outside_explicit_public_build_allowlist(self):
        builder = (ROOT / "scripts/build_site.py").read_text(encoding="utf-8")
        self.assertNotIn("prototypes/step15a-mobile-home", builder)
        self.assertNotIn("step15a-mobile-home", (ROOT / "web/index.html").read_text(encoding="utf-8"))

    def test_home_spine_is_compact_and_destinations_are_obvious(self):
        html = (ROOT / "prototypes/step15a-mobile-home/index.html").read_text(encoding="utf-8")
        labels = ["NOW", "NEXT", "OUTLOOK", "LATEST ANALYSIS", "EXPLORE"]
        positions = [html.index(f">{label}<") for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(html.count("<article id=\"analysis-destination\""), 1)
        self.assertEqual(html.count("<li><time"), 4)
        self.assertIn("Full Calendar →", html)
        self.assertIn("See forecasts →", html)
        self.assertIn("Read analysis →", html)
        self.assertNotIn("105 events", html)
        self.assertNotIn("NEXT 30 DAYS", html)
        self.assertNotIn("RESOLUTION CLOCK", html)

    def test_fixtures_separate_elapsed_time_from_governed_result_and_freshness(self):
        html = (ROOT / "prototypes/step15a-mobile-home/index.html").read_text(encoding="utf-8")
        js = (ROOT / "prototypes/step15a-mobile-home/app.js").read_text(encoding="utf-8")
        for state in (
            "PRE_EVENT",
            "EVENT_TIME_PASSED_AWAITING_CONFIRMATION",
            "CONFIRMED_OUTCOME",
            "CONFIRMED_OUTCOME_WITH_ANALYSIS",
        ):
            self.assertIn(state, js)
        self.assertIn("Awaiting confirmed outcome", js)
        self.assertIn("Elapsed time does not confirm completion", js)
        self.assertIn("FIXTURE ONLY", js)
        self.assertIn("No build timestamp published", html)
        self.assertIn("YOUR DEVICE TIME", html)
        self.assertNotIn("LIVE", html + js)
        self.assertIn("Australia CPI", html)

    def test_prototype_has_semantic_heading_outline_and_touch_sized_controls(self):
        html = (ROOT / "prototypes/step15a-mobile-home/index.html").read_text(encoding="utf-8")
        css = (ROOT / "prototypes/step15a-mobile-home/styles.css").read_text(encoding="utf-8")
        self.assertIn('href="#home"', html)
        self.assertIn('id="now-heading"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('id="prototype-state"', html)
        self.assertIn("min-height:44px", css)
        self.assertIn("focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)


if __name__ == "__main__":
    unittest.main()
