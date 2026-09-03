import json
from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.adapters import parse_rba_fsr_rss, parse_socrata_metadata

class AdapterParserTests(unittest.TestCase):
    def test_rba_rss2_parser(self):
        xml='''<?xml version="1.0"?><rss><channel><item><title>Financial Stability Review – April 2026</title><link>https://www.rba.gov.au/publications/fsr/2026/apr/</link><guid>fsr-2026-apr</guid><pubDate>Fri, 24 Apr 2026 11:30:00 +1000</pubDate></item></channel></rss>'''
        items=parse_rba_fsr_rss(xml)
        self.assertEqual(len(items),1)
        self.assertIn("Financial Stability Review",items[0].title)
        self.assertTrue(items[0].pub_date_iso.startswith("2026-04-24T11:30:00"))

    def test_rba_rdf_namespaced_parser(self):
        xml='''<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rss="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/"><rss:item rdf:about="https://www.rba.gov.au/publications/fsr/2026/mar/"><rss:title>Financial Stability Review - March 2026</rss:title><rss:link>https://www.rba.gov.au/publications/fsr/2026/mar/</rss:link><dc:date>2026-03-19T11:30:00+11:00</dc:date></rss:item></rdf:RDF>'''
        items=parse_rba_fsr_rss(xml)
        self.assertEqual(len(items),1)
        self.assertEqual(items[0].title,"Financial Stability Review - March 2026")
        self.assertEqual(items[0].link,"https://www.rba.gov.au/publications/fsr/2026/mar/")
        self.assertTrue(items[0].pub_date_iso.startswith("2026-03-19T11:30:00"))

    def test_socrata_metadata_parser(self):
        payload={
            "id":"fiev-nid6",
            "name":"Lista de normas cargadas en el Sistema Único de Información Normativa SUIN-Juriscol",
            "rowsUpdatedAt":1780000000,
            "metadataUpdatedAt":1780000100,
            "columns":[
                {"name":"Tipo de norma","fieldName":"tipo_de_norma","dataTypeName":"text"},
                {"name":"Año","fieldName":"ano","dataTypeName":"number"},
            ],
        }
        meta=parse_socrata_metadata(json.dumps(payload),expected_id="fiev-nid6")
        self.assertEqual(meta.dataset_id,"fiev-nid6")
        self.assertEqual(len(meta.columns),2)
        self.assertEqual(meta.columns[0].field_name,"tipo_de_norma")

if __name__=="__main__": unittest.main()
