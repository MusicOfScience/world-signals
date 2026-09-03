import unittest

from src.world_signals.coverage import build_coverage_audit


class CoverageAuditTests(unittest.TestCase):
    def setUp(self):
        self.registry={
            "version":"test",
            "reference_date":"2026-09-03",
            "records":[
                {"series_id":"S1","region":"Region A","category":"MACROECONOMIC_RELEASE","institution":"Inst A","source_id":"SRC1","canonical_name":"A1"},
                {"series_id":"S1","region":"Region A","category":"MACROECONOMIC_RELEASE","institution":"Inst A","source_id":"SRC1","canonical_name":"A2"},
                {"series_id":"S1","region":"Region A","category":"MACROECONOMIC_RELEASE","institution":"Inst A","source_id":"SRC1","canonical_name":"A3"},
                {"series_id":"S2","region":"Region B","category":"FISCAL_SOVEREIGN_FINANCE","institution":"Inst B","source_id":"SRC2","canonical_name":"B1"},
                {"series_id":"S3","region":"Region B","category":"ELECTIONS_GOVERNANCE","institution":"Inst C","source_id":"SRC3","canonical_name":"B2"},
            ],
        }
        self.sources={"sources":[
            {"source_id":"SRC1","monitoring_readiness_status":"PILOT_VALIDATED_NO_AUTO_COMMIT"},
            {"source_id":"SRC2","monitoring_readiness_status":"MANUAL_ONLY_RIGHTS_HOLD"},
            {"source_id":"SRC3","monitoring_readiness_status":"ENDPOINT_REVIEW_REQUIRED"},
        ]}

    def test_occurrence_density_does_not_replace_series_diversity(self):
        audit=build_coverage_audit(self.registry,self.sources)
        by_region={x["region"]:x for x in audit["by_region"]}
        self.assertEqual(by_region["Region A"]["occurrence_count"],3)
        self.assertEqual(by_region["Region A"]["unique_series_count"],1)
        self.assertEqual(by_region["Region A"]["occurrences_per_series"],3.0)
        self.assertEqual(by_region["Region B"]["occurrence_count"],2)
        self.assertEqual(by_region["Region B"]["unique_series_count"],2)

    def test_high_frequency_series_is_visible(self):
        audit=build_coverage_audit(self.registry,self.sources)
        self.assertEqual(audit["high_frequency_series"][0]["series_id"],"S1")
        self.assertEqual(audit["high_frequency_series"][0]["occurrence_count"],3)

    def test_source_readiness_is_descriptive_not_population_rule(self):
        audit=build_coverage_audit(self.registry,self.sources)
        readiness=audit["source_readiness"]["monitoring_readiness_status_counts"]
        self.assertEqual(readiness["PILOT_VALIDATED_NO_AUTO_COMMIT"],1)
        self.assertEqual(readiness["MANUAL_ONLY_RIGHTS_HOLD"],1)
        self.assertTrue(audit["methodology"]["quota_filling_prohibited"])
        self.assertTrue(audit["methodology"]["machine_readability_is_not_importance"])

    def test_monetary_macro_share_uses_occurrences_but_is_labelled_as_such(self):
        audit=build_coverage_audit(self.registry,self.sources)
        self.assertEqual(audit["totals"]["monetary_plus_macro_occurrence_count"],3)
        self.assertEqual(audit["totals"]["monetary_plus_macro_occurrence_share"],0.6)


if __name__=="__main__":
    unittest.main()
