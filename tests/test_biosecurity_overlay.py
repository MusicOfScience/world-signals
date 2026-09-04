from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analytical_overlays import (
    biosecurity_overlay_summary,
    validate_biosecurity_overlay,
)


class BiosecurityOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
        cls.overlay = json.loads((ROOT / "data/coverage/biosecurity_overlay.json").read_text(encoding="utf-8"))

    def test_live_overlay_validates_at_checkpoint(self):
        self.assertEqual(validate_biosecurity_overlay(self.registry, self.overlay), [])

    def test_only_existing_five_who_series_are_canonical_memberships(self):
        expected = {
            "WSER-HEALTH-WHA",
            "WSER-HEALTH-WHO-EB",
            "WSER-HEALTH-WHO-IGWG",
            "WSER-HEALTH-WHO-PBAC",
            "WSER-HEALTH-WHO-RC",
        }
        memberships = self.overlay["canonical_series_memberships"]
        self.assertEqual({x["series_id"] for x in memberships}, expected)
        self.assertTrue(all(x["canonical_institution"] == "World Health Organization" for x in memberships))
        self.assertTrue(all(x["canonical_primary_category"] == "HEALTH_BIOSECURITY" for x in memberships))
        summary = biosecurity_overlay_summary(self.registry, self.overlay)
        self.assertEqual(summary["mapped_canonical_series_count"], 5)
        self.assertEqual(summary["mapped_canonical_occurrence_count"], 10)

    def test_candidate_nodes_are_explicitly_noncanonical_and_have_no_canonical_ids(self):
        expected = {
            "BIO-CAND-WOAH",
            "BIO-CAND-IPPC-CPM",
            "BIO-CAND-BWC",
            "BIO-CAND-AFRICA-CDC",
        }
        nodes = self.overlay["candidate_nodes"]
        self.assertEqual({x["candidate_node_id"] for x in nodes}, expected)
        for node in nodes:
            self.assertEqual(node["canonical_status"], "NOT_CANONICAL_AT_V0.20")
            self.assertNotIn("series_id", node)
            self.assertNotIn("occurrence_id", node)

    def test_one_health_is_relation_not_primary_system(self):
        relation = next(x for x in self.overlay["relationships"] if x["relationship_id"] == "ONE_HEALTH")
        self.assertEqual(relation["relationship_type"], "CROSS_CUTTING")
        self.assertNotIn("ONE_HEALTH", {x["system_id"] for x in self.overlay["systems"]})

    def test_validation_does_not_mutate_canonical_registry(self):
        before = json.dumps(self.registry, sort_keys=True, separators=(",", ":"))
        validate_biosecurity_overlay(self.registry, self.overlay)
        after = json.dumps(self.registry, sort_keys=True, separators=(",", ":"))
        self.assertEqual(after, before)

    def test_unknown_canonical_series_fails_closed(self):
        overlay = deepcopy(self.overlay)
        overlay["canonical_series_memberships"][0]["series_id"] = "WSER-DOES-NOT-EXIST"
        errors = validate_biosecurity_overlay(self.registry, overlay)
        self.assertTrue(any("does not exist" in error for error in errors))

    def test_primary_category_redefinition_fails_closed(self):
        overlay = deepcopy(self.overlay)
        overlay["canonical_series_memberships"][0]["canonical_primary_category"] = "INTERNATIONAL_INSTITUTIONS"
        errors = validate_biosecurity_overlay(self.registry, overlay)
        self.assertTrue(any("primary category mismatch" in error for error in errors))

    def test_candidate_becoming_canonical_requires_overlay_review(self):
        overlay = deepcopy(self.overlay)
        overlay["candidate_nodes"][0]["institution"] = "World Health Organization"
        errors = validate_biosecurity_overlay(self.registry, overlay)
        self.assertTrue(any("already canonical" in error for error in errors))

    def test_overlay_does_not_authorize_population_or_canonical_mutation(self):
        summary = biosecurity_overlay_summary(self.registry, self.overlay)
        self.assertFalse(summary["canonical_mutation_authorized"])
        self.assertFalse(summary["event_population_authorized"])
        self.assertTrue(self.overlay["principles"]["overlay_is_not_population_authority"])


if __name__ == "__main__":
    unittest.main()
