from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import (
    parse_cellar_identifier_notice,
    parse_cellar_legal_relation_diagnostics,
)


class CellarMetadataTests(unittest.TestCase):
    def test_extracts_only_relations_attached_to_requested_work(self):
        rdf='''<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                 xmlns:cdm="http://publications.europa.eu/ontology/cdm#"
                 xmlns:owl="http://www.w3.org/2002/07/owl#">
          <rdf:Description rdf:about="http://publications.europa.eu/resource/cellar/base">
            <cdm:resource_legal_is_amended_by_resource_legal rdf:resource="http://publications.europa.eu/resource/cellar/amender"/>
            <cdm:resource_legal_consolidated_by_resource_legal rdf:resource="http://publications.europa.eu/resource/cellar/consolidation"/>
            <owl:sameAs rdf:resource="http://publications.europa.eu/resource/celex/32024R2847"/>
          </rdf:Description>
          <rdf:Description rdf:about="http://publications.europa.eu/resource/cellar/linked">
            <cdm:resource_legal_repealed_by_resource_legal rdf:resource="http://publications.europa.eu/resource/cellar/unrelated"/>
            <owl:sameAs rdf:resource="http://publications.europa.eu/resource/celex/32025R9999"/>
          </rdf:Description>
        </rdf:RDF>'''
        relations=parse_cellar_legal_relation_diagnostics(rdf,base_celex="32024R2847")
        self.assertEqual(relations,[
            {
                "predicate":"resource_legal_consolidated_by_resource_legal",
                "target_uri":"http://publications.europa.eu/resource/cellar/consolidation",
                "subject_uri":"http://publications.europa.eu/resource/cellar/base",
            },
            {
                "predicate":"resource_legal_is_amended_by_resource_legal",
                "target_uri":"http://publications.europa.eu/resource/cellar/amender",
                "subject_uri":"http://publications.europa.eu/resource/cellar/base",
            },
        ])

    def test_identifier_notice_extracts_celex_without_number_inference(self):
        xml='''<?xml version="1.0"?>
        <notice>
          <identifier>32025R0327</identifier>
          <sameAs>http://publications.europa.eu/resource/celex/32025R0327</sameAs>
          <identifier>ELI:http://data.europa.eu/eli/reg/2025/327/oj</identifier>
        </notice>'''
        parsed=parse_cellar_identifier_notice(xml)
        self.assertEqual(parsed["celex_ids"],["32025R0327"])
        self.assertIn("http://publications.europa.eu/resource/celex/32025R0327",parsed["resource_uris"])


if __name__=="__main__": unittest.main()
