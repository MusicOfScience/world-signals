from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.adapters import parse_cellar_legal_relation_diagnostics


class CellarMetadataTests(unittest.TestCase):
    def test_extracts_legal_relation_targets_only(self):
        rdf='''<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                 xmlns:cdm="http://publications.europa.eu/ontology/cdm#"
                 xmlns:owl="http://www.w3.org/2002/07/owl#">
          <rdf:Description rdf:about="http://publications.europa.eu/resource/cellar/base">
            <cdm:resource_legal_is_amended_by_resource_legal rdf:resource="http://publications.europa.eu/resource/cellar/amender"/>
            <cdm:resource_legal_consolidated_by_resource_legal rdf:resource="http://publications.europa.eu/resource/cellar/consolidation"/>
            <owl:sameAs rdf:resource="http://publications.europa.eu/resource/celex/32024R2847"/>
          </rdf:Description>
        </rdf:RDF>'''
        relations=parse_cellar_legal_relation_diagnostics(rdf)
        self.assertEqual(relations,[
            {
                "predicate":"resource_legal_consolidated_by_resource_legal",
                "target_uri":"http://publications.europa.eu/resource/cellar/consolidation",
            },
            {
                "predicate":"resource_legal_is_amended_by_resource_legal",
                "target_uri":"http://publications.europa.eu/resource/cellar/amender",
            },
        ])


if __name__=="__main__": unittest.main()
