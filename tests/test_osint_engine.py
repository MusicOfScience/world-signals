from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from world_signals.osint_engine import (  # noqa: E402
    ObservationCandidate,
    build_review_queue,
    build_signal_candidates,
    build_story_clusters,
    candidate_corroboration,
    deduplicate_candidates,
    normalise_records,
    parse_payload,
    persistence_state,
    permission_decision,
    production_promotion_policy,
    retrieve_route,
    run_once,
    validate_cohort,
)


UTC = timezone.utc
NOW = datetime(2026, 9, 27, 0, 0, tzinfo=UTC)


def source(source_id="S1", provider="First Party", *, allowed=True):
    return {
        "source_id": source_id,
        "institution": provider,
        "domain": "monetary_policy",
        "automated_monitoring_use": "CLEARED" if allowed else "PROHIBITED_OR_RIGHTS_HOLD",
        "automated_retrieval_permission": "OFFICIAL_RSS_INTERFACE" if allowed else "PRODUCTION_AUTOMATION_HOLD",
        "ingestion_permission": "PUBLIC_FACTS_ALLOWED" if allowed else "MANUAL_ONLY_RIGHTS_HOLD",
        "monitor_endpoints": [{"url": "https://example.test/feed"}],
    }


def route(source_id="S1", route_id="r1"):
    return {"source_id": source_id, "route_id": route_id, "endpoint": "https://example.test/feed",
            "transport": "RSS_XML", "parser": "rss_atom_metadata_v1", "cadence": "daily"}


RSS = b"""<?xml version='1.0'?><rss><channel><item><guid>doc-1</guid><title>Policy decision</title><description>Official statement.</description><link>https://example.test/doc-1?utm_source=x</link><pubDate>Sun, 27 Sep 2026 00:00:00 GMT</pubDate></item></channel></rss>"""


class Response:
    status = 200
    headers = {"Content-Type": "application/rss+xml"}

    def __init__(self, payload=RSS):
        self.payload = payload

    def read(self):
        return self.payload


class OSINTEngineTests(unittest.TestCase):
    def test_permission_is_explicit_and_manual_only_is_not_fetched(self):
        calls = []

        def opener(*args, **kwargs):
            calls.append(True)
            return Response()

        retrieval, payload, _ = retrieve_route(route(), source(allowed=False), opener=opener, now=NOW)
        self.assertEqual(retrieval.result_state, "PERMISSION_HOLD")
        self.assertIsNone(payload)
        self.assertEqual(calls, [])

    def test_cohort_rejects_unreviewed_source_and_accepts_explicit_route(self):
        cohort = {"routes": [route()]}
        self.assertEqual(validate_cohort({"sources": [source()]}, cohort), [])
        self.assertTrue(validate_cohort({"sources": [source(allowed=False)]}, cohort))

    def test_fetch_failure_and_parser_failure_create_no_candidate(self):
        def fail(*args, **kwargs):
            raise OSError("offline")

        retrieval, payload, _ = retrieve_route(route(), source(), opener=fail, now=NOW)
        self.assertEqual(retrieval.result_state, "NETWORK_ERROR")
        self.assertIsNone(payload)
        with self.assertRaises(Exception):
            parse_payload(b"not xml", "RSS_XML")

    def test_rss_normalises_publication_and_retrieval_times_separately(self):
        retrieval, payload, _ = retrieve_route(route(), source(), opener=lambda *a, **k: Response(), now=NOW)
        records = parse_payload(payload, "RSS_XML")
        candidates, duplicates = normalise_records(records, source(), route(), retrieval.payload_sha256, retrieval.retrieved_at)
        self.assertEqual(duplicates, 0)
        self.assertEqual(candidates[0].publication_time, "2026-09-27T00:00:00Z")
        self.assertEqual(candidates[0].retrieval_time, "2026-09-27T00:00:00Z")
        self.assertEqual(candidates[0].canonical_url, "https://example.test/doc-1")

    def test_unchanged_payload_does_not_create_duplicate_candidate(self):
        records = parse_payload(RSS, "RSS_XML")
        first, _ = normalise_records(records, source(), route(), "payload-hash", "2026-09-27T00:00:00Z")
        second, duplicates = normalise_records(records, source(), route(), "payload-hash", "2026-09-27T01:00:00Z",
                                               {first[0].document_key})
        self.assertEqual(second, [])
        self.assertEqual(duplicates, 1)

    def test_same_document_collapses_lineage_but_independent_providers_remain(self):
        records = parse_payload(RSS, "RSS_XML")
        a, _ = normalise_records(records, source("S1", "Provider A"), route("S1", "r1"), "hash-a", "2026-09-27T00:00:00Z")
        b, _ = normalise_records(records, source("S2", "Provider A"), route("S2", "r2"), "hash-a", "2026-09-27T00:00:00Z")
        c, _ = normalise_records(records, source("S3", "Provider B"), route("S3", "r3"), "hash-b", "2026-09-27T00:00:00Z")
        merged, duplicates = deduplicate_candidates(a + b + c)
        self.assertEqual(len(merged), 2)
        self.assertEqual(duplicates, 1)
        self.assertEqual(candidate_corroboration(merged)["distinct_ultimate_provider_count"], 2)

    def test_correction_is_distinct_and_contradiction_is_retained_for_review(self):
        records = [{"source_native_id": "c1", "title": "Correction to release", "factual_text": "revised data",
                    "canonical_url": "https://example.test/c1", "publication_time": "2026-09-27T00:00:00Z"}]
        values, _ = normalise_records(records, source(), route(), "hash-c", "2026-09-27T01:00:00Z")
        self.assertEqual(values[0].candidate_state, "POSSIBLE_CORRECTION")
        self.assertEqual(values[0].change_kind, "CORRECTION")
        values[0].candidate_state = "CONFLICT"
        self.assertEqual(values[0].candidate_state, "CONFLICT")

    def test_unknown_entity_cannot_become_authoritative_identity(self):
        values, _ = normalise_records([{"source_native_id": "e1", "title": "Unknown institution", "factual_text": "fact",
                                        "canonical_url": "https://example.test/e1"}], source(), route(), "hash-e", "2026-09-27T00:00:00Z")
        self.assertEqual(values[0].entities[0]["entity_id"], "S1")
        self.assertEqual(values[0].entities[0]["resolution_state"], "SOURCE_REGISTRY_ID")
        self.assertIn("UNREVIEWED", values[0].lineage["independence_status"])

    def test_story_clustering_does_not_merge_distinct_domains_or_unrelated_words(self):
        records = parse_payload(RSS, "RSS_XML")
        a, _ = normalise_records(records, source(), route(), "hash-a", "2026-09-27T00:00:00Z")
        b, _ = normalise_records([{**records[0], "source_native_id": "doc-2", "title": "Policy decision shipping"}],
                                 {**source(), "domain": "logistics_supply_chains"}, route(), "hash-b", "2026-09-27T01:00:00Z")
        clusters = build_story_clusters(a + b)
        self.assertEqual(len(clusters), 2)

    def test_persistence_requires_time_separation(self):
        records = parse_payload(RSS, "RSS_XML")
        a, _ = normalise_records(records, source("S1", "A"), route(), "ha", "2026-09-27T00:00:00Z")
        b, _ = normalise_records([{**records[0], "source_native_id": "doc-2", "pubDate": ""}], source("S2", "B"), route(), "hb", "2026-09-27T01:00:00Z")
        self.assertEqual(persistence_state(a + b), "BURST_ONLY")
        b[0].publication_time = "2026-09-28T00:00:00Z"
        self.assertEqual(persistence_state(a + b), "PERSISTENT_CANDIDATE")

    def test_signal_candidate_is_explanatory_and_never_production_signal(self):
        records = parse_payload(RSS, "RSS_XML")
        a, _ = normalise_records(records, source("S1", "A"), route(), "ha", "2026-09-27T00:00:00Z")
        b, _ = normalise_records([{**records[0], "source_native_id": "doc-2"}], source("S2", "B"), route(), "hb", "2026-09-28T00:00:00Z")
        b[0].publication_time = "2026-09-28T00:00:00Z"
        signals = build_signal_candidates(a + b)
        self.assertEqual(len(signals), 1)
        self.assertIn("review", signals[0].rationale.lower())
        self.assertEqual(production_promotion_policy()["signal_candidate_to_governed_signal"], "REVIEWED_TRANSACTION_REQUIRED")

    def test_cross_domain_convergence_is_a_candidate_prompt_not_causation(self):
        records = parse_payload(RSS, "RSS_XML")
        a, _ = normalise_records(records, source("S1", "Provider A"), route(), "ha", "2026-09-27T00:00:00Z")
        b, _ = normalise_records([{**records[0], "source_native_id": "doc-2", "title": "Shipping disruption"}],
                                 {**source("S2", "Provider B"), "domain": "logistics_supply_chains"}, route("S2", "r2"), "hb", "2026-09-28T00:00:00Z")
        signals = build_signal_candidates(a + b)
        convergence = next(item for item in signals if item.signal_class == "CROSS_DOMAIN_CONVERGENCE_CANDIDATE")
        self.assertEqual(convergence.domains, ["logistics_supply_chains", "monetary_policy"])
        self.assertEqual(convergence.source_lineage_summary["causal_claim"], "PROHIBITED")

    def test_run_is_read_only_and_runtime_only(self):
        registry = {"sources": [source()]}
        cohort = {"routes": [route()]}
        run = run_once(registry, cohort, opener=lambda *a, **k: Response(), now=NOW)
        self.assertEqual(len(run.retrievals), 1)
        self.assertEqual(run.retrievals[0].result_state, "SUCCESS")
        queue = build_review_queue(run.retrievals, run.observation_candidates, run.signal_candidates)
        self.assertEqual(queue["public_projection"], "CLOSED")
        self.assertEqual(production_promotion_policy()["canonical_mutation"], "FORBIDDEN")

    def test_runtime_state_prevents_reprocessing_unchanged_feed(self):
        registry = {"sources": [source()]}
        cohort = {"routes": [route()]}
        with tempfile.TemporaryDirectory() as directory:
            first = run_once(registry, cohort, opener=lambda *a, **k: Response(), runtime_dir=Path(directory), now=NOW)
            second = run_once(registry, cohort, opener=lambda *a, **k: Response(), runtime_dir=Path(directory), now=NOW)
        self.assertEqual(len(first.observation_candidates), 1)
        self.assertEqual(second.observation_candidates, [])
        self.assertEqual(second.retrievals[0].result_state, "NO_NEW_INFORMATION")
        queue = build_review_queue(second.retrievals, second.observation_candidates, second.signal_candidates)
        self.assertEqual(queue["items"], [])

    def test_runtime_state_accepts_new_item_without_recreating_old_item(self):
        registry = {"sources": [source()]}
        cohort = {"routes": [route()]}
        changed = RSS.replace(b"</channel>", b"<item><guid>doc-2</guid><title>Second release</title><description>New fact.</description><link>https://example.test/doc-2</link><pubDate>Mon, 28 Sep 2026 00:00:00 GMT</pubDate></item></channel>")
        responses = iter([Response(RSS), Response(changed)])
        with tempfile.TemporaryDirectory() as directory:
            first = run_once(registry, cohort, opener=lambda *a, **k: next(responses), runtime_dir=Path(directory), now=NOW)
            second = run_once(registry, cohort, opener=lambda *a, **k: next(responses), runtime_dir=Path(directory), now=NOW)
        self.assertEqual(len(first.observation_candidates), 1)
        self.assertEqual([item.source_native_id for item in second.observation_candidates], ["doc-2"])
        self.assertEqual(second.run_mode, "INCREMENTAL")
        self.assertEqual(second.observation_candidates[0].freshness_state, "INCREMENTAL_CURRENT")
        self.assertEqual(second.observation_candidates[0].novelty_state, "NEW_TO_CHECKPOINT")

    def test_first_run_is_explicit_bootstrap_and_does_not_generate_current_signal(self):
        registry = {"sources": [source()]}
        cohort = {"routes": [route()]}
        with tempfile.TemporaryDirectory() as directory:
            run = run_once(registry, cohort, opener=lambda *a, **k: Response(), runtime_dir=Path(directory), now=NOW)
        self.assertEqual(run.run_mode, "BOOTSTRAP")
        self.assertEqual(run.observation_candidates[0].freshness_state, "BOOTSTRAP_HISTORY")
        self.assertEqual(run.observation_candidates[0].novelty_state, "BOOTSTRAP_INVENTORY")
        self.assertEqual(run.signal_candidates, [])
        self.assertEqual(run.metrics["bootstrap_records"], 1)

    def test_historical_item_discovered_after_checkpoint_is_not_current_novelty(self):
        records = parse_payload(RSS, "RSS_XML")
        values, _ = normalise_records(records, source(), route(), "old", "2026-09-27T00:00:00Z",
                                       run_mode="INCREMENTAL", checkpoint_retrieved_at="2026-09-26T00:00:00Z")
        self.assertEqual(values[0].freshness_state, "INCREMENTAL_CURRENT")
        values, _ = normalise_records(records, source(), route(), "old", "2026-09-27T00:00:00Z",
                                       run_mode="INCREMENTAL", checkpoint_retrieved_at="2026-09-28T00:00:00Z")
        self.assertEqual(values[0].freshness_state, "INCREMENTAL_HISTORICAL_DISCOVERY")
        self.assertEqual(build_signal_candidates(values), [])

    def test_changed_source_native_record_is_a_revision_not_a_new_question(self):
        records = parse_payload(RSS, "RSS_XML")
        first, _ = normalise_records(records, source(), route(), "payload-a", "2026-09-27T00:00:00Z",
                                      run_mode="BOOTSTRAP")
        states = {first[0].document_key: {"candidate_id": first[0].candidate_id, "payload_sha256": first[0].payload_sha256,
                                          "record_sha256": first[0].record_sha256}}
        revised_records = [{**records[0], "factual_text": "Correction: official statement revised."}]
        revised, duplicates = normalise_records(revised_records, source(), route(), "payload-b", "2026-09-28T00:00:00Z",
                                                existing_document_keys={first[0].document_key},
                                                existing_document_states=states,
                                                run_mode="INCREMENTAL",
                                                checkpoint_retrieved_at="2026-09-27T00:00:00Z")
        self.assertEqual(duplicates, 0)
        self.assertEqual(len(revised), 1)
        self.assertEqual(revised[0].change_kind, "CORRECTION")
        self.assertEqual(revised[0].freshness_state, "INCREMENTAL_REVISION")
        self.assertEqual(revised[0].novelty_state, "REVISION_TO_CHECKPOINT")
        self.assertEqual(revised[0].revision_of_candidate_id, first[0].candidate_id)
        self.assertNotEqual(revised[0].candidate_id, first[0].candidate_id)

    def test_parser_version_change_does_not_replay_seen_identity(self):
        records = parse_payload(RSS, "RSS_XML")
        first, _ = normalise_records(records, source(), route(), "payload-a", "2026-09-27T00:00:00Z",
                                      run_mode="BOOTSTRAP")
        second, duplicates = normalise_records(records, source(), {**route(), "parser": "rss_atom_metadata_v2"},
                                               "payload-a", "2026-09-28T00:00:00Z",
                                               existing_document_keys={first[0].document_key},
                                               existing_document_states={first[0].document_key: {
                                                   "candidate_id": first[0].candidate_id,
                                                   "payload_sha256": first[0].payload_sha256,
                                                   "record_sha256": first[0].record_sha256}},
                                               run_mode="INCREMENTAL")
        self.assertEqual(second, [])
        self.assertEqual(duplicates, 1)

    def test_no_public_candidate_projection_and_no_forecast_or_governed_write(self):
        policy = production_promotion_policy()
        self.assertEqual(policy["public_candidate_projection"], "CLOSED")
        self.assertEqual(policy["forecast_mutation"], "FORBIDDEN")
        self.assertEqual(policy["observation_candidate_to_governed_observation"], "REVIEWED_TRANSACTION_REQUIRED")

    def test_runtime_objects_are_json_serialisable(self):
        records = parse_payload(RSS, "RSS_XML")
        values, _ = normalise_records(records, source(), route(), "hash", "2026-09-27T00:00:00Z")
        json.dumps([value.__dict__ for value in values])


if __name__ == "__main__":
    unittest.main()
