import json
from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.adapters import (
    cellar_celex_url,
    eli_current_url,
    eli_current_fetch_url,
    parse_cra_article_71,
    parse_eli_current_state,
    parse_kenya_budget_policy_rule,
    parse_rba_fsr_rss,
    parse_socrata_metadata,
    parse_socrata_rows,
    resource_url,
)


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

    def test_socrata_rows_parser(self):
        payload=[{"tipo":"Decreto","n_mero":"111","a_o":"1996","vigencia":"Vigente"}]
        rows=parse_socrata_rows(json.dumps(payload))
        self.assertEqual(rows[0]["n_mero"],"111")
        self.assertEqual(rows[0]["a_o"],"1996")

    def test_socrata_resource_url_encodes_query(self):
        url=resource_url(where="n_mero='111' AND a_o='1996'",select="tipo,n_mero,a_o",limit=5)
        self.assertIn("resource/fiev-nid6.json",url)
        self.assertIn("%24where=",url)
        self.assertIn("%24select=",url)
        self.assertIn("%24limit=5",url)

    def test_kenya_budget_rule_parser_offline_fixture(self):
        html='''<html><body><h1>Public Finance Management Act</h1><p>25. Budget Policy Statement</p><p>The National Treasury shall submit the Budget Policy Statement approved in terms of subsection (1) to Parliament, by the 15th February in each year.</p></body></html>'''
        rule=parse_kenya_budget_policy_rule(html)
        self.assertEqual(rule.section,"25(2)")
        self.assertEqual(rule.deadline_month,2)
        self.assertEqual(rule.deadline_day,15)
        self.assertEqual(len(rule.rule_sha256),64)

    def test_cellar_celex_url(self):
        self.assertEqual(
            cellar_celex_url("32024R2847"),
            "https://publications.europa.eu/resource/celex/32024R2847",
        )

    def test_eli_current_identifier_and_operational_url(self):
        self.assertEqual(
            eli_current_url("reg",2024,2847),
            "https://data.europa.eu/eli/reg/2024/2847",
        )
        self.assertEqual(
            eli_current_fetch_url("reg",2024,2847),
            "https://eur-lex.europa.eu/eli/reg/2024/2847",
        )

    def test_eli_result_list_topology_parser(self):
        html='''<html><body><h1>Search Results</h1><section><p>CELEX number: 32025R0327</p><p>Regulation (EU) 2025/327 amending Regulation (EU) 2024/2847</p></section><section><h2>Consolidated text</h2><p>CELEX number: 02024R2847-20241120</p></section><h2>Search criteria</h2></body></html>'''
        state=parse_eli_current_state(html,base_celex="32024R2847")
        self.assertEqual(state.mode,"RESULT_LIST_WITH_UNCONSOLIDATED_MODIFIERS")
        self.assertEqual(state.consolidation_celex_ids,("02024R2847-20241120",))
        self.assertEqual(state.modifier_celex_ids,("32025R0327",))
        self.assertEqual(state.state_sha256,"30c7a5956a85dfa600de96c68f509b7a293197120ba57611d03b0c82a82c7fd3")

    def test_eli_current_document_topology_parser(self):
        html='''<html><body><h1>Document 02024R2847-20241120</h1><p>Consolidated text: Cyber Resilience Act</p></body></html>'''
        state=parse_eli_current_state(html,base_celex="32024R2847")
        self.assertEqual(state.mode,"CURRENT_DOCUMENT")
        self.assertEqual(state.consolidation_celex_ids,("02024R2847-20241120",))
        self.assertEqual(state.modifier_celex_ids,())

    def test_cra_article_71_parser_offline_fixture(self):
        html='''<html><body><h1>Cyber Resilience Act</h1><h2>Article 71 Entry into force and application</h2><p>This Regulation shall apply from 11 December 2027. However, Article 14 shall apply from 11 September 2026 and Chapter IV (Articles 35 to 51) shall apply from 11 June 2026.</p></body></html>'''
        rule=parse_cra_article_71(html)
        self.assertEqual(rule.celex,"32024R2847")
        self.assertEqual(rule.article,"71")
        self.assertEqual(rule.article_14_application_date,"2026-09-11")
        self.assertEqual(rule.general_application_date,"2027-12-11")
        self.assertEqual(rule.chapter_iv_application_date,"2026-06-11")
        self.assertEqual(len(rule.rule_sha256),64)

    def test_cra_article_71_parser_extracts_changed_date(self):
        html='''<html><body><h1>Cyber Resilience Act</h1><h2>Article 71 Entry into force and application</h2><p>This Regulation shall apply from 11 December 2027. However, Article 14 shall apply from 12 September 2026 and Chapter IV (Articles 35 to 51) shall apply from 11 June 2026.</p></body></html>'''
        changed=parse_cra_article_71(html)
        self.assertEqual(changed.article_14_application_date,"2026-09-12")
        self.assertNotEqual(changed.rule_sha256,"39f90548d36ac5b3ea301034e07201464edccc5412a026b3777e0f8217a0615f")


if __name__=="__main__": unittest.main()
