from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.apply_exact_market_measurement_contract_ak import (
    ANALYSIS_IMPL_PATH,
    ANALYSIS_SCHEMA_PATH,
    CANONICAL_PATH,
    EVIDENCE_PATH,
    PLAN_PATH,
    REVIEWS_PATH,
    load_candidate_module,
    transform_analysis_source,
    transform_schema,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ExactMarketMeasurementContractAKTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = load(PLAN_PATH)
        cls.production_schema = load(ANALYSIS_SCHEMA_PATH)
        cls.canonical = load(CANONICAL_PATH)
        cls.reviews = load(REVIEWS_PATH)
        cls.evidence = load(EVIDENCE_PATH)
        source = ANALYSIS_IMPL_PATH.read_text(encoding="utf-8")
        if cls.production_schema.get("version") == "0.3":
            cls.candidate_schema = transform_schema(cls.production_schema, cls.plan)
            cls.candidate_source = transform_analysis_source(source)
        elif cls.production_schema.get("version") == "0.4":
            cls.candidate_schema = copy.deepcopy(cls.production_schema)
            cls.candidate_source = source
        else:
            raise AssertionError(f"unexpected Analysis schema version {cls.production_schema.get('version')}")
        cls.module = load_candidate_module(cls.candidate_source)

    def exact_fixture(self) -> tuple[dict, dict, dict, dict, dict]:
        schema = copy.deepcopy(self.candidate_schema)
        canonical = copy.deepcopy(self.canonical)
        reviews = copy.deepcopy(self.reviews)
        evidence = copy.deepcopy(self.evidence)

        review = next(
            row for row in reviews["reviews"]
            if row.get("canonical_occurrence_id") == "WSO-MAC-A-0025"
        )
        movement = review["what_moved"][0]
        movement.update({
            "movement_representation": "PRE_POST_VALUES",
            "before_value": 48.0,
            "after_value": 57.0,
            "measurement_precision": "EXACT_TIMESTAMP_SERIES",
            "independently_reconstructed": True,
            "evidence_refs": ["WSEV-AK-SYNTHETIC-MARKET-SERIES"],
            "market_series_id": "AK.SYNTHETIC.RBA_PROBABILITY",
            "market_timezone": "Australia/Sydney",
            "series_granularity": "1 minute",
            "event_anchor_utc": "2026-09-02T01:30:00Z",
            "before_observation_utc": "2026-09-02T01:29:00Z",
            "after_observation_utc": "2026-09-02T01:31:00Z",
            "data_use_basis": "OPEN_REUSE_TERMS",
            "public_projection_permitted": True,
        })
        evidence["evidence"].append({
            "evidence_id": "WSEV-AK-SYNTHETIC-MARKET-SERIES",
            "evidence_class": "MARKET_DATA_PROVIDER",
            "provider": "Synthetic AK validation fixture",
            "host_or_distribution": "Synthetic AK validation fixture",
            "title": "Synthetic exact market series used only for contract validation",
            "url": "https://example.invalid/world-signals-ak-synthetic-market-series",
            "published_at": "2026-09-06T00:00:00Z",
            "roles": ["MARKET_OBSERVATION"],
            "supports": ["Synthetic pre/post observations for validator testing only."],
            "analytical_use": "SYNTHETIC_TEST_FIXTURE_ONLY",
            "canonical_provenance_effect": "NONE",
        })
        return schema, evidence, reviews, canonical, movement

    def errors_for(self, schema: dict, evidence: dict, reviews: dict, canonical: dict) -> tuple[str, ...]:
        return self.module.validate_analysis(schema, evidence, reviews, canonical).errors

    def test_candidate_schema_is_v04_without_populating_exact_rows(self) -> None:
        self.assertIn(self.production_schema["version"], {"0.3", "0.4"})
        self.assertEqual(self.candidate_schema["version"], "0.4")
        exact_rows = [
            movement
            for review in self.reviews["reviews"]
            for movement in (review.get("what_moved") or [])
            if movement.get("measurement_precision") == "EXACT_TIMESTAMP_SERIES"
        ]
        self.assertEqual(exact_rows, [])
        report = self.module.validate_analysis(
            self.candidate_schema, self.evidence, self.reviews, self.canonical
        )
        self.assertTrue(report.ok, report.errors)

    def test_valid_synthetic_exact_series_passes(self) -> None:
        schema, evidence, reviews, canonical, _ = self.exact_fixture()
        report = self.module.validate_analysis(schema, evidence, reviews, canonical)
        self.assertTrue(report.ok, report.errors)

    def test_exact_label_alone_does_not_confer_precision(self) -> None:
        schema, evidence, reviews, canonical, movement = self.exact_fixture()
        for field in (
            "market_series_id",
            "market_timezone",
            "series_granularity",
            "event_anchor_utc",
            "before_observation_utc",
            "after_observation_utc",
            "data_use_basis",
            "public_projection_permitted",
        ):
            movement.pop(field, None)
        movement["independently_reconstructed"] = False
        errors = self.errors_for(schema, evidence, reviews, canonical)
        joined = "\n".join(errors)
        self.assertIn("requires independently_reconstructed=true", joined)
        self.assertIn("requires market_series_id", joined)
        self.assertIn("requires UTC event_anchor_utc", joined)

    def test_event_anchor_must_equal_canonical_start_utc(self) -> None:
        schema, evidence, reviews, canonical, movement = self.exact_fixture()
        movement["event_anchor_utc"] = "2026-09-02T01:30:01Z"
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("event_anchor_utc must equal canonical start_utc" in error for error in errors), errors)

    def test_observations_must_be_ordered_around_event_anchor(self) -> None:
        schema, evidence, reviews, canonical, movement = self.exact_fixture()
        movement["before_observation_utc"] = "2026-09-02T01:30:30Z"
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("before < event anchor <= after" in error for error in errors), errors)

    def test_exact_series_requires_qualified_market_observation_evidence(self) -> None:
        schema, evidence, reviews, canonical, _ = self.exact_fixture()
        synthetic = next(row for row in evidence["evidence"] if row["evidence_id"] == "WSEV-AK-SYNTHETIC-MARKET-SERIES")
        synthetic["evidence_class"] = "REPUTABLE_NEWSWIRE"
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("MARKET_OBSERVATION evidence from PRIMARY_OFFICIAL or MARKET_DATA_PROVIDER" in error for error in errors), errors)

    def test_exact_series_requires_explicit_public_projection_permission(self) -> None:
        schema, evidence, reviews, canonical, movement = self.exact_fixture()
        movement["public_projection_permitted"] = False
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("public_projection_permitted=true" in error for error in errors), errors)

    def test_exact_series_requires_valid_iana_market_timezone(self) -> None:
        schema, evidence, reviews, canonical, movement = self.exact_fixture()
        movement["market_timezone"] = "UTC+10"
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("valid IANA market_timezone" in error for error in errors), errors)

    def test_exact_series_cannot_resolve_missing_canonical_time(self) -> None:
        schema, evidence, reviews, canonical, _ = self.exact_fixture()
        target = next(row for row in canonical["records"] if row.get("occurrence_id") == "WSO-MAC-A-0025")
        target["start_utc"] = None
        review = next(row for row in reviews["reviews"] if row.get("canonical_occurrence_id") == "WSO-MAC-A-0025")
        review["canonical_release_utc"] = None
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("requires an existing canonical start_utc" in error for error in errors), errors)

    def test_non_exact_rows_cannot_carry_exact_series_only_fields(self) -> None:
        schema, evidence, reviews, canonical, movement = self.exact_fixture()
        movement["measurement_precision"] = "SOURCE_REPORTED_PRE_POST"
        movement["independently_reconstructed"] = False
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("exact-series-only fields require EXACT_TIMESTAMP_SERIES precision" in error for error in errors), errors)

    def test_exact_utc_fields_reject_non_utc_offsets(self) -> None:
        schema, evidence, reviews, canonical, movement = self.exact_fixture()
        movement["before_observation_utc"] = "2026-09-02T11:29:00+10:00"
        errors = self.errors_for(schema, evidence, reviews, canonical)
        self.assertTrue(any("requires UTC before_observation_utc" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
