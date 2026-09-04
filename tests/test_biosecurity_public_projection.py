import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.biosecurity_projection import public_biosecurity_projection


class BiosecurityPublicProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=json.loads((ROOT/"data/canonical/registry.json").read_text(encoding="utf-8"))
        cls.overlay=json.loads((ROOT/"data/coverage/biosecurity_overlay.json").read_text(encoding="utf-8"))
        cls.public=public_biosecurity_projection(cls.registry,cls.overlay)

    def test_public_projection_preserves_boundary(self):
        metadata=self.public["metadata"]
        self.assertEqual(metadata["canonical_registry_version"],"0.20")
        self.assertEqual(metadata["canonical_record_count"],669)
        self.assertEqual(metadata["mapped_canonical_series_count"],5)
        self.assertEqual(metadata["mapped_canonical_occurrence_count"],10)
        self.assertEqual(metadata["candidate_node_count"],4)
        self.assertFalse(metadata["candidate_nodes_are_canonical"])
        self.assertFalse(metadata["canonical_mutation_authorized"])
        self.assertFalse(metadata["event_population_authorized"])
        self.assertTrue(metadata["canonical_primary_categories_unchanged"])

    def test_candidate_projection_contains_no_canonical_ids(self):
        for node in self.public["candidate_nodes"]:
            self.assertNotIn("series_id",node)
            self.assertNotIn("occurrence_id",node)
            self.assertEqual(node["canonical_status"],"NOT_CANONICAL_AT_V0.20")

    def test_system_counts_make_who_concentration_visible(self):
        systems={row["system_id"]:row for row in self.public["systems"]}
        human=systems["BIO-HUMAN-HEALTH-GOVERNANCE"]
        self.assertEqual(human["canonical_series_count"],5)
        self.assertEqual(human["canonical_occurrence_count"],10)
        self.assertEqual(human["candidate_node_count"],1)
        self.assertEqual(systems["BIO-ANIMAL-ZOONOTIC-HEALTH"]["canonical_series_count"],0)
        self.assertEqual(systems["BIO-PLANT-PHYTOSANITARY-SECURITY"]["canonical_series_count"],0)
        self.assertEqual(systems["BIO-BIOLOGICAL-SECURITY-ARMS-CONTROL"]["canonical_series_count"],0)

    def test_browser_module_is_read_only_and_build_bundles_it(self):
        js=(ROOT/"web/biosecurity.js").read_text(encoding="utf-8")
        build=(ROOT/"scripts/build_site.py").read_text(encoding="utf-8")
        self.assertIn("fetch('data/biosecurity.json')",js)
        self.assertIn('NONCANONICAL CANDIDATE',js)
        self.assertIn('Biosecurity system map',js)
        self.assertNotIn('data/canonical/registry.json',js)
        self.assertNotIn("method:'POST'",js)
        self.assertNotIn('method:"POST"',js)
        self.assertNotIn('PUT',js)
        self.assertNotIn('DELETE',js)
        self.assertIn('web/biosecurity.js',build)
        self.assertIn('biosecurity.json',build)


if __name__=="__main__":
    unittest.main()
