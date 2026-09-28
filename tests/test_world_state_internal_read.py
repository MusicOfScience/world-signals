"""Step 12D single-request internal intelligence view tests."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_history import DIMENSIONS  # noqa: E402
from world_signals.world_state_internal_read import (  # noqa: E402
    WorldStateInternalReadError,
    join_relationship_context,
    partition_assessments,
    read_internal_intelligence,
    validate_internal_read_request,
)
from world_signals.world_state_read import WorldStateReadError, read_world_state  # noqa: E402


def request(
    *,
    mode: str = "KNOWLEDGE_AS_OF",
    knowledge: str = "2026-09-29T00:00:00Z",
    effective: str | None = None,
    jurisdictions: list[str] | None = None,
    dimensions: list[str] | None = None,
) -> dict:
    return {
        "contract_version": "0.1",
        "query_mode": mode,
        "knowledge_cutoff_utc": knowledge,
        "effective_as_of_utc": effective,
        "scope": {
            "jurisdictions": jurisdictions or ["*"],
            "dimensions": dimensions or sorted(DIMENSIONS),
        },
        "include_negative_evidence": True,
        "include_withdrawn_history": False,
    }


def data_hashes() -> dict[str, str]:
    paths = [path for path in (ROOT / "data").rglob("*") if path.is_file()]
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


class WorldStateInternalReadTests(unittest.TestCase):
    def test_one_request_derives_coherent_reads(self):
        view = read_internal_intelligence(request(jurisdictions=["New Zealand"], dimensions=["MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS"]))
        self.assertEqual(view["query_coherence_check"]["status"], "PASS")
        self.assertEqual(view["derived_requests"]["synthesis"]["as_of_utc"], view["derived_requests"]["production"]["knowledge_cutoff_utc"])
        self.assertEqual(view["derived_requests"]["synthesis"]["scope"]["jurisdictions"], view["derived_requests"]["production"]["scope"]["jurisdictions"])
        self.assertEqual(view["derived_requests"]["synthesis"]["scope"]["dimensions"], view["derived_requests"]["production"]["scope"]["dimensions"])
        self.assertEqual(view["derived_requests"]["production"]["scope"]["systems"], [])
        self.assertEqual(view["derived_requests"]["production"]["scope"]["component_ids"], [])

    def test_internal_request_rejects_future_effective_time(self):
        with self.assertRaises(WorldStateInternalReadError):
            validate_internal_read_request(request(mode="EFFECTIVE_AS_OF", effective="2026-09-30T00:00:00Z", knowledge="2026-09-29T00:00:00Z"))

    def test_knowledge_request_derives_null_effective_time(self):
        normalized = validate_internal_read_request(request())
        self.assertIsNone(normalized["effective_as_of_utc"])
        self.assertIsNone(read_internal_intelligence(request())["derived_requests"]["production"]["effective_as_of_utc"])

    def test_legacy_dual_query_rejects_mismatched_cutoff_scope_and_filters(self):
        synthesis = {
            "contract_version": "0.1",
            "as_of_utc": "2026-09-29T00:00:00Z",
            "scope": {"jurisdictions": ["New Zealand"], "dimensions": ["MACROECONOMIC_FINANCIAL_CONDITIONS"], "actor_ids": None},
            "include_negative_evidence": True,
            "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY",
        }
        base = {
            "query_mode": "KNOWLEDGE_AS_OF",
            "knowledge_cutoff_utc": "2026-09-29T00:00:00Z",
            "effective_as_of_utc": None,
            "scope": {"jurisdictions": ["New Zealand"], "dimensions": ["MACROECONOMIC_FINANCIAL_CONDITIONS"], "systems": [], "component_ids": []},
            "include_withdrawn_history": False,
        }
        for mutation in (
            {"knowledge_cutoff_utc": "2026-09-28T00:00:00Z"},
            {"scope": {**base["scope"], "jurisdictions": ["Democratic Republic of the Congo"]}},
            {"scope": {**base["scope"], "dimensions": ["HEALTH_BIOSECURITY"]}},
            {"scope": {**base["scope"], "systems": ["RBNZ_OFFICIAL_CASH_RATE_DECISION"]}},
            {"scope": {**base["scope"], "component_ids": ["WSDIM-MACRO-NZ-RBNZ-OCR-202609-001"]}},
        ):
            query = deepcopy(base)
            query.update(mutation)
            with self.assertRaises(WorldStateReadError) as context:
                read_world_state(synthesis, production_query=query)
            self.assertIn("QUERY_COHERENCE_CHECK", str(context.exception))

    def test_health_is_current_and_rbnz_is_historical_without_currentness_claim(self):
        view = read_internal_intelligence(request())
        self.assertEqual(len(view["current_state"]), 1)
        self.assertEqual(view["current_state"][0]["dimension"], "HEALTH_BIOSECURITY")
        self.assertEqual(len(view["historical_state"]), 2)
        self.assertEqual({row["dimension"] for row in view["historical_state"]}, {"MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS"})
        self.assertEqual(view["review_required_state"], [])
        self.assertEqual(view["unknown_currentness_state"], [])

    def test_coverage_keeps_not_assessed_distinct(self):
        view = read_internal_intelligence(request(jurisdictions=["Democratic Republic of the Congo"], dimensions=["HEALTH_BIOSECURITY", "MACROECONOMIC_FINANCIAL_CONDITIONS"]))
        self.assertEqual(view["coverage"]["scoped_assessment_available"], ["HEALTH_BIOSECURITY"])
        self.assertEqual(view["coverage"]["current_scoped_assessment_available"], ["HEALTH_BIOSECURITY"])
        self.assertEqual(view["coverage"]["not_assessed"], ["MACROECONOMIC_FINANCIAL_CONDITIONS"])
        self.assertEqual(view["relationship_context"], [])

    def test_nz_macro_markets_query_selects_both_endpoints_and_one_historical_relationship(self):
        view = read_internal_intelligence(request(jurisdictions=["New Zealand"], dimensions=["MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS"]))
        relationship = view["relationship_context"][0]
        self.assertEqual(view["relationship_counts"], {"historical_accepted_in_scope": 1, "current_active_in_scope": 0})
        self.assertEqual(relationship["relationship_class"], "ASSOCIATION")
        self.assertEqual(relationship["confidence"], "MEDIUM")
        self.assertEqual(relationship["causal_status"], "NON_CAUSAL")
        self.assertEqual(relationship["production_relationship_fingerprint"], "778c99b558cdffc1a91d57f506426d73f580a1e16925358b97f736a982062e44")
        self.assertEqual({node["status"] for node in relationship["source_endpoints"] + relationship["target_endpoints"]}, {"SELECTED_IN_THIS_VIEW"})
        self.assertEqual(view["transmission_edge_count"], 0)

    def test_macro_only_has_partial_relationship_context_without_markets_coverage(self):
        view = read_internal_intelligence(request(jurisdictions=["New Zealand"], dimensions=["MACROECONOMIC_FINANCIAL_CONDITIONS"]))
        relationship = view["relationship_context"][0]
        self.assertEqual(relationship["context_status"], "PARTIAL_RELATIONSHIP_CONTEXT")
        self.assertEqual(relationship["target_endpoints"][0]["status"], "VALID_PRODUCTION_ENDPOINT_OUTSIDE_VIEW_SCOPE")
        self.assertNotIn("MARKETS_AS_SENSORS", view["coverage"]["scoped_assessment_available"])
        self.assertNotIn("MARKETS_AS_SENSORS", view["coverage"]["queried_dimensions"])

    def test_drc_health_query_excludes_rbnz_relationship(self):
        view = read_internal_intelligence(request(jurisdictions=["Democratic Republic of the Congo"], dimensions=["HEALTH_BIOSECURITY"]))
        self.assertEqual([row["dimension"] for row in view["current_state"]], ["HEALTH_BIOSECURITY"])
        self.assertEqual(view["relationship_context"], [])
        self.assertEqual(view["relationship_counts"]["historical_accepted_in_scope"], 0)

    def test_global_query_selects_three_components_and_one_historical_relationship(self):
        view = read_internal_intelligence(request())
        self.assertEqual(len(view["current_state"]) + len(view["historical_state"]), 3)
        self.assertEqual(view["relationship_counts"]["historical_accepted_in_scope"], 1)
        self.assertEqual(view["relationship_counts"]["current_active_in_scope"], 0)
        self.assertEqual(view["transmission_edge_count"], 0)

    def test_effective_relationship_is_retrospective_only_after_admission(self):
        before_admission = read_internal_intelligence(request(
            mode="EFFECTIVE_AS_OF",
            effective="2026-09-02T00:00:00Z",
            knowledge="2026-09-28T09:04:33Z",
            jurisdictions=["New Zealand"],
            dimensions=["MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS"],
        ))
        after_admission = read_internal_intelligence(request(
            mode="EFFECTIVE_AS_OF",
            effective="2026-09-02T00:00:00Z",
            knowledge="2026-09-29T00:00:00Z",
            jurisdictions=["New Zealand"],
            dimensions=["MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS"],
        ))
        self.assertEqual(before_admission["relationship_context"], [])
        self.assertEqual(after_admission["relationship_context"][0]["historical_status"], "HISTORICAL_RELATIONSHIP_KNOWN_LATER")

    def test_internal_read_is_deterministic_and_mutation_free(self):
        before = data_hashes()
        first = read_internal_intelligence(request())
        second = read_internal_intelligence(request())
        after = data_hashes()
        self.assertEqual(first["semantic_fingerprint"], second["semantic_fingerprint"])
        self.assertEqual(before, after)
        self.assertEqual(first["mutation_check"]["status"], "PASS")
        self.assertFalse(first["review_state"]["production_write_performed"])
        self.assertFalse(first["review_state"]["public_projection_permitted"])

    def test_no_successor_or_new_production_objects_are_created(self):
        view = read_internal_intelligence(request())
        self.assertFalse(view["review_state"]["successor_revision_created"])
        self.assertEqual(view["evidence_state"]["selected_counts"].get("relationship_history"), 1)
        self.assertEqual(view["production_state"]["component_count"], 3)
        self.assertEqual(view["production_state"]["production_counts"], {"actors": 0, "components": 5, "snapshots": 3, "admissions": 3})

    def test_synthetic_review_required_and_unknown_partitions_are_explicit(self):
        components = [
            {"component_id": "A", "component_type": "DIMENSION_ASSESSMENT", "revision_id": "A-R1", "object_sha256": "a" * 64, "dimension": "HEALTH_BIOSECURITY", "scope": {}},
            {"component_id": "B", "component_type": "DIMENSION_ASSESSMENT", "revision_id": "B-R1", "object_sha256": "b" * 64, "dimension": "MACROECONOMIC_FINANCIAL_CONDITIONS", "scope": {}},
        ]
        freshness = [{"component_id": "A", "status": "STALE_REVIEW_REQUIRED"}, {"component_id": "B", "status": "UNKNOWN"}]
        current_use = [{"component_id": "A", "status": "CURRENT_USE_REQUIRES_REVIEW"}, {"component_id": "B", "status": "UNKNOWN"}]
        partition = partition_assessments(components, freshness, current_use)
        self.assertEqual([row["component_id"] for row in partition["REVIEW_REQUIRED"]], ["A"])
        self.assertEqual([row["component_id"] for row in partition["UNKNOWN"]], ["B"])

    def test_endpoint_hash_mismatch_fails_closed(self):
        relationship = {
            "relationship_id": "REL",
            "revision_id": "REL-R1",
            "relationship_class": "ASSOCIATION",
            "directionality": "DIRECTED",
            "confidence": "MEDIUM",
            "causal_basis": [],
            "source_nodes": [{"node_id": "A", "revision_id": "A-R1", "object_sha256": "0" * 64}],
            "target_nodes": [],
        }
        components = [{"component_id": "A", "revision_id": "A-R1", "object_sha256": "a" * 64}]
        with self.assertRaises(WorldStateInternalReadError) as context:
            join_relationship_context([relationship], components, components, query_mode="KNOWLEDGE_AS_OF", effective_as_of_utc=None)
        self.assertIn("ENDPOINT_HASH_MISMATCH", str(context.exception))

    def test_scan_view_is_non_narrative_and_internal(self):
        view = read_internal_intelligence(request())
        self.assertFalse(view["review_state"]["new_synthesis_performed"])
        self.assertFalse(view["review_state"]["public_projection_permitted"])
        self.assertEqual(view["relationship_context"][0]["relationship_class"], "ASSOCIATION")
        self.assertNotIn("transmission", json_text(view["relationship_context"][0]).lower())


def json_text(value):
    import json
    return json.dumps(value, sort_keys=True)


if __name__ == "__main__":
    unittest.main()
