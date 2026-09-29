from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError
from world_signals.adapters.rba_mpb_decision_rss import (
    PARSER_VERSION,
    RBA_DECISION_SERIES,
    RBA_DECISION_TITLE,
    build_result_candidate,
    classify_decision_item,
    feed_path_allowed_by_robots,
    match_canonical_occurrence,
    parse_decision_page,
    parse_decision_rss,
    validate_decision_page_url,
)


RSS = f'''<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
 <item rdf:about="https://www.rba.gov.au/media-releases/2026/mr-26-27.html">
  <title>{RBA_DECISION_TITLE}</title>
  <link>https://www.rba.gov.au/media-releases/2026/mr-26-27.html</link>
  <description>At its meeting today, the Board decided to increase the cash rate target by 25 basis points to 4.60 per cent.</description>
  <dc:date>2026-09-29T14:30:00+10:00</dc:date>
 </item>
</rdf:RDF>'''

PAGE_INCREASE = f'''<html><body><h1>{RBA_DECISION_TITLE}</h1>
<p>Number 2026-27</p><p>Date 29 September 2026</p>
<p>At its meeting today, the Board decided to increase the cash rate target by 25 basis points to 4.60 per cent.</p>
<p>Today’s policy decision was unanimous.</p></body></html>'''

PAGE_UNCHANGED = f'''<html><body><h1>{RBA_DECISION_TITLE}</h1>
<p>Number 2026-19</p><p>Date 11 August 2026</p>
<p>At its meeting today, the Board decided to leave the cash rate target unchanged at 4.35 per cent.</p>
<p>Today’s policy decision was unanimous.</p></body></html>'''

OCCURRENCE = {
    "occurrence_id": "WSO-d2a7c4e4416b505b",
    "series_id": RBA_DECISION_SERIES,
    "start_utc": "2026-09-29T04:30:00Z",
    "lifecycle_status": "PLANNED",
}


class RbaDecisionPublicationCandidateTests(unittest.TestCase):
    def test_namespaced_rdf_feed_and_exact_item(self):
        items = parse_decision_rss(RSS)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, RBA_DECISION_TITLE)
        self.assertEqual(items[0].published_at, "2026-09-29T14:30:00+10:00")
        self.assertEqual(classify_decision_item(items[0]), "EXACT_TITLE")
        self.assertEqual(len(items[0].semantic_item_sha256), 64)

    def test_malformed_or_incomplete_feed_fails_closed(self):
        with self.assertRaises(AdapterError):
            parse_decision_rss("<rss><broken>")
        with self.assertRaises(AdapterError):
            parse_decision_rss("<rss><channel><item><title>missing fields</title></item></channel></rss>")
        with self.assertRaises(AdapterError):
            parse_decision_rss("<rss><channel/></rss>")

    def test_unrelated_and_near_match_are_not_guessed(self):
        unrelated = RSS.replace(RBA_DECISION_TITLE, "Payments System Board Update")
        self.assertEqual(classify_decision_item(parse_decision_rss(unrelated)[0]), "NOT_A_MONETARY_POLICY_DECISION")
        near = RSS.replace(RBA_DECISION_TITLE, "Statement by the Monetary Policy Board: Policy Decision")
        self.assertEqual(classify_decision_item(parse_decision_rss(near)[0]), "REVIEW_UNCLASSIFIED")

    def test_duplicate_identity_is_deduplicated_and_feed_order_irrelevant(self):
        duplicate = RSS.replace("</rdf:RDF>", RSS[RSS.index(" <item"):RSS.index("</rdf:RDF>")] + "</rdf:RDF>")
        self.assertEqual(len(parse_decision_rss(duplicate)), 1)

    def test_bounded_official_url(self):
        self.assertEqual(validate_decision_page_url("https://www.rba.gov.au/media-releases/2026/mr-26-27.html"),
                         "https://www.rba.gov.au/media-releases/2026/mr-26-27.html")
        for bad in (
            "http://www.rba.gov.au/media-releases/2026/mr-26-27.html",
            "https://evil.example/media-releases/2026/mr-26-27.html",
            "https://www.rba.gov.au/speeches/2026/mr-26-27.html",
            "https://www.rba.gov.au/media-releases/2026/mr-26-27.html?x=1",
        ):
            with self.subTest(url=bad), self.assertRaises(AdapterError):
                validate_decision_page_url(bad)

    def test_robots_rss_scope_is_allowed_and_disallow_fails_closed(self):
        current = """User-agent: *\nDisallow: /assets/\nDisallow: /search/\nDisallow: /s/\n"""
        blocked = """User-agent: *\nDisallow: /rss/\n"""
        self.assertTrue(feed_path_allowed_by_robots(current))
        self.assertFalse(feed_path_allowed_by_robots(blocked))
        with self.assertRaises(AdapterError):
            feed_path_allowed_by_robots("not a robots policy")

    def test_canonical_match_is_exact_series_and_publication_date(self):
        item = parse_decision_rss(RSS)[0]
        state, match = match_canonical_occurrence(item, [OCCURRENCE])
        self.assertEqual((state, match["occurrence_id"]), ("MATCHED", OCCURRENCE["occurrence_id"]))
        self.assertEqual(match_canonical_occurrence(item, [])[0], "NO_MATCH")
        self.assertEqual(match_canonical_occurrence(item, [OCCURRENCE, OCCURRENCE])[0], "AMBIGUOUS")
        other = dict(OCCURRENCE, series_id="OTHER")
        self.assertEqual(match_canonical_occurrence(item, [other])[0], "NO_MATCH")

    def test_extract_increase_and_unanimity_from_source_text(self):
        item = parse_decision_rss(RSS)[0]
        parsed = parse_decision_page(PAGE_INCREASE, item=item, resolved_url=item.link)
        self.assertEqual(parsed["cash_rate_target_percent"], 4.6)
        self.assertEqual(parsed["decision_direction"], "INCREASE")
        self.assertEqual(parsed["change_basis_points"], 25)
        self.assertIs(parsed["decision_unanimous"], True)
        self.assertEqual(parsed["rationale_classification"], "ISSUER_STATED_RATIONALE")

    def test_historical_unchanged_specimen_and_missing_vote_semantics(self):
        xml = RSS.replace("2026-09-29", "2026-08-11").replace("14:30:00", "14:30:00").replace("mr-26-27", "mr-26-19")
        item = parse_decision_rss(xml)[0]
        parsed = parse_decision_page(PAGE_UNCHANGED, item=item, resolved_url=item.link)
        self.assertEqual(parsed["cash_rate_target_percent"], 4.35)
        self.assertEqual(parsed["decision_direction"], "UNCHANGED")
        self.assertEqual(parsed["change_basis_points"], 0)
        self.assertIs(parsed["decision_unanimous"], True)
        without_vote = PAGE_UNCHANGED.replace("Today’s policy decision was unanimous.", "The Bank will continue to assess incoming data.")
        self.assertEqual(parse_decision_page(without_vote, item=item, resolved_url=item.link)["decision_unanimous"], "NOT_STATED")

    def test_historical_decrease_specimen(self):
        xml = RSS.replace("2026-09-29", "2025-08-12").replace("mr-26-27", "mr-25-22")
        item = parse_decision_rss(xml)[0]
        page = f'''<html><body><h1>{RBA_DECISION_TITLE}</h1>
        <p>Number 2025-22</p><p>Date 12 August 2025</p>
        <p>At its meeting today, the Board decided to lower the cash rate target by 25 basis points to 3.60 per cent.</p>
        </body></html>'''
        parsed = parse_decision_page(page, item=item, resolved_url=item.link)
        self.assertEqual(parsed["cash_rate_target_percent"], 3.6)
        self.assertEqual(parsed["decision_direction"], "DECREASE")
        self.assertEqual(parsed["change_basis_points"], -25)
        self.assertEqual(parsed["decision_unanimous"], "NOT_STATED")

    def test_page_identity_date_and_redirect_mismatches_fail(self):
        item = parse_decision_rss(RSS)[0]
        for page, resolved in (
            (PAGE_INCREASE.replace("2026-27", "2026-26"), item.link),
            (PAGE_INCREASE.replace("29 September 2026", "28 September 2026"), item.link),
            (PAGE_INCREASE, "https://other.example/release"),
            (PAGE_INCREASE.replace("increase the cash rate target by 25 basis points to 4.60", "made a decision"), item.link),
        ):
            with self.subTest(resolved=resolved), self.assertRaises(AdapterError):
                parse_decision_page(page, item=item, resolved_url=resolved)

    def test_candidate_requires_both_transport_hashes_and_is_idempotent(self):
        item = parse_decision_rss(RSS)[0]
        result = parse_decision_page(PAGE_INCREASE, item=item, resolved_url=item.link)
        feed_hash = sha256(RSS.encode()).hexdigest()
        page_hash = sha256(PAGE_INCREASE.encode()).hexdigest()
        args = dict(item=item, outcome=result, occurrence=OCCURRENCE,
                    feed_transport_sha256=feed_hash, page_transport_sha256=page_hash,
                    detected_at_utc="2026-09-29T10:35:00Z")
        first = build_result_candidate(**args)
        second = build_result_candidate(**(args | {"detected_at_utc": "2026-09-29T10:36:00Z"}))
        different_transport = build_result_candidate(**(args | {"feed_transport_sha256": "c" * 64, "page_transport_sha256": "d" * 64}))
        self.assertEqual(first["candidate_id"], "WSOUTCAND-AU-RBA-MPB-20260929-001")
        self.assertEqual(first["status"], "REVIEW_PENDING")
        self.assertEqual(first["semantic_fingerprint"], second["semantic_fingerprint"])
        self.assertEqual(first["semantic_fingerprint"], different_transport["semantic_fingerprint"])
        self.assertNotEqual(first["source_transport_hashes"], different_transport["source_transport_hashes"])
        self.assertNotEqual(first["detected_at_utc"], second["detected_at_utc"])
        self.assertEqual(first["automatic_actions"], [])
        with self.assertRaises(AdapterError):
            build_result_candidate(**(args | {"page_transport_sha256": ""}))
        self.assertEqual(PARSER_VERSION, "rba-mpb-decision-rss-v1")

    def test_candidate_builder_never_changes_occurrence_state(self):
        item = parse_decision_rss(RSS)[0]
        original = json.dumps(OCCURRENCE, sort_keys=True)
        result = parse_decision_page(PAGE_INCREASE, item=item, resolved_url=item.link)
        build_result_candidate(item=item, outcome=result, occurrence=OCCURRENCE,
            feed_transport_sha256="a" * 64, page_transport_sha256="b" * 64,
            detected_at_utc="2026-09-29T10:35:00Z")
        self.assertEqual(json.dumps(OCCURRENCE, sort_keys=True), original)
        self.assertEqual(OCCURRENCE["lifecycle_status"], "PLANNED")

    def test_real_canonical_and_schedule_monitor_remain_unchanged(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        records = canonical.get("records", canonical.get("occurrences", []))
        occurrence = next(row for row in records if row.get("occurrence_id") == OCCURRENCE["occurrence_id"])
        self.assertEqual(occurrence["series_id"], RBA_DECISION_SERIES)
        self.assertEqual(occurrence["start_local"], "2026-09-29T14:30:00")
        self.assertEqual(occurrence["start_utc"], "2026-09-29T04:30:00Z")
        self.assertEqual(occurrence["lifecycle_status"], "PLANNED")

        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        source_rows = sources.get("sources", sources.get("records", []))
        calendar_source = next(row for row in source_rows if row.get("source_id") == "WSSRC-CB-002")
        self.assertIn("schedules-events", json.dumps(calendar_source).lower())
        self.assertNotIn("rss-cb-media-releases.xml", json.dumps(calendar_source))

        monitor = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        route_rows = monitor.get("routes", monitor.get("expectations", monitor.get("adapters", [])))
        route = next(row for row in route_rows if row.get("adapter_id") == "RBA_MPB_CALENDAR")
        self.assertEqual(route["monitor_role"], "RBA_MPB_AUTHORITATIVE_SCHEDULE_CHANGE_SENTINEL")
        self.assertEqual(route["elapsed_time_policy"], "NO_COMPLETION_INFERENCE")
        self.assertIs(route["automatic_commit_allowed"], False)
        self.assertNotIn("RBA_MPB_DECISION_PUBLICATION_RSS", json.dumps(monitor))

    def test_retained_audit_hashes_and_fail_closed_live_status(self):
        def fingerprint(value):
            encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            return sha256(encoded.encode()).hexdigest()

        route_path = ROOT / "data/audit/STEP15B_RBA_DECISION_PUBLICATION_ROUTE_REVIEW_PENDING.json"
        route = json.loads(route_path.read_text())
        self.assertEqual(route["semantic_fingerprint"], fingerprint({k: v for k, v in route.items() if k != "semantic_fingerprint"}))
        audit = json.loads((ROOT / "data/audit/STEP15B_RBA_DECISION_PUBLICATION_AUDIT_v0.1.json").read_text())
        self.assertEqual(audit["route_candidate_semantic_fingerprint"], route["semantic_fingerprint"])
        self.assertEqual(audit["parser_semantic_contract_fingerprint"], fingerprint(audit["parser_semantic_contract"]))
        self.assertEqual(audit["source_manifest_semantic_fingerprint"], fingerprint(audit["source_manifest_semantics"]))
        self.assertEqual(audit["candidate_generation"]["real_result_candidate_created"], False)
        self.assertEqual(audit["status"], "T3_OBSERVED_T4_NOT_PROVEN")
        self.assertEqual(audit["production_write_targets"], [])
        self.assertEqual(audit["public_write_targets"], [])


if __name__ == "__main__":
    unittest.main()
