from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.live_intelligence import validate_live_intelligence


class LiveCorrectionConflictCMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(
            (ROOT / "data/live_intelligence/schema.json").read_text(encoding="utf-8")
        )
        cls.evidence = json.loads(
            (ROOT / "data/live_intelligence/evidence_registry.json").read_text(encoding="utf-8")
        )
        cls.observations = json.loads(
            (ROOT / "data/live_intelligence/observations.json").read_text(encoding="utf-8")
        )
        cls.canonical = json.loads(
            (ROOT / "data/canonical/registry.json").read_text(encoding="utf-8")
        )

    def opened_schema(self):
        schema = copy.deepcopy(self.schema)
        schema["population_policy"]["maximum_observation_count"] = 999
        schema["population_policy"]["maximum_evidence_count"] = 999
        return schema

    def evidence_row(
        self,
        evidence_id: str,
        *,
        provider: str = "Test authority",
        roles: list[str] | None = None,
    ) -> dict:
        return {
            "evidence_id": evidence_id,
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": provider,
            "title": f"Synthetic evidence {evidence_id}",
            "url": f"https://example.test/{evidence_id}",
            "roles": roles or ["FACTUAL_OBSERVATION"],
            "publication_time": {
                "precision": "CIVIL_DATE",
                "published_date": "2026-09-10",
            },
            "canonical_provenance_effect": "NONE",
        }

    def observation_row(
        self,
        observation_id: str,
        evidence_refs: list[str],
        *,
        observed_at_utc: str,
        verification_state: str = "PRIMARY_CONFIRMED",
    ) -> dict:
        return {
            "observation_id": observation_id,
            "observed_at_utc": observed_at_utc,
            "observation_type": "OFFICIAL_ANNOUNCEMENT",
            "verification_state": verification_state,
            "headline": f"Synthetic observation {observation_id}",
            "summary": "Synthetic fixture used only to exercise the CM Live contract.",
            "domain_tags": ["INSTITUTIONS"],
            "jurisdictions": ["Test jurisdiction"],
            "regions": ["Cross-regional / Global"],
            "evidence_refs": evidence_refs,
            "canonical_links": [],
            "revision_of_observation_id": None,
            "automatic_canonical_commit": False,
            "google_calendar_write": False,
        }

    def validate(self, schema, evidence, observations):
        return validate_live_intelligence(
            schema,
            evidence,
            observations,
            self.canonical,
        )

    def synthetic_state(self):
        return (
            self.opened_schema(),
            copy.deepcopy(self.evidence),
            copy.deepcopy(self.observations),
        )

    def test_cm_is_no_population_contract_descendant(self):
        self.assertEqual(self.schema["version"], "0.9")
        self.assertEqual(self.observations["version"], "0.9")
        self.assertEqual(self.evidence["version"], "0.9")
        self.assertEqual(len(self.observations["observations"]), 8)
        self.assertEqual(len(self.evidence["evidence"]), 11)
        self.assertEqual(self.schema["population_policy"]["maximum_observation_count"], 8)
        self.assertEqual(self.schema["population_policy"]["maximum_evidence_count"], 11)
        self.assertFalse(self.schema["population_policy"]["automatic_ingestion_allowed"])
        self.assertFalse(self.schema["public_projection_policy"]["observation_projection_allowed"])

        cm = self.schema["cm_checkpoint"]
        self.assertEqual(cm["schema_version"], "0.9")
        self.assertEqual(cm["observation_count"], 8)
        self.assertEqual(cm["evidence_count"], 11)
        self.assertEqual(cm["base_main_sha"], "1e4a6bbc8670fc36a452740401461f28e313c031")

        current_states = {
            row["verification_state"] for row in self.observations["observations"]
        }
        self.assertTrue(
            current_states.isdisjoint({"CONFLICTING_REPORTS", "CORRECTED", "RETRACTED"})
        )

        expected_observation_ids = {
            "WSLI-RISK-NPL-FLOOD-20260826-001",
            "WSLI-HEALTH-COD-BVD-20260826-001",
            "WSLI-HEALTH-COD-BVD-20260830-001",
            "WSLI-MAC-JPN-FIES-202607-001",
            "WSLI-GEO-VNM-MMR-SECURITY-20260905-001",
            "WSLI-INST-UNGA-CORRECTMAP-20260904-001",
            "WSLI-INST-PHL-BARMM-PREELECT-20260909-001",
            "WSLI-INST-PIF-PARTNER-FRAMEWORK-20260904-001",
        }
        self.assertEqual(
            {row["observation_id"] for row in self.observations["observations"]},
            expected_observation_ids,
        )
        report = self.validate(self.schema, self.evidence, self.observations)
        self.assertTrue(report.ok, report.errors)

    def test_cm_policy_is_explicit_and_non_adjudicative(self):
        policy = self.schema["correction_conflict_policy"]
        self.assertEqual(policy["mode"], "FOUNDATION_CONTRACT_NO_PRODUCTION_SPECIMEN")
        self.assertEqual(policy["minimum_unique_conflict_evidence_refs"], 2)
        self.assertEqual(policy["minimum_distinct_conflict_providers"], 2)
        self.assertEqual(policy["provider_identity_normalisation"], "STRIP_CASEFOLD")
        self.assertFalse(policy["conflict_requires_winner_selection"])
        self.assertFalse(policy["conflict_requires_synthetic_consensus"])
        self.assertTrue(policy["corrected_or_retracted_requires_correction_evidence"])
        self.assertTrue(policy["corrected_or_retracted_observed_at_must_follow_target"])

    def test_valid_corrected_observation_requires_prior_target_evidence_and_later_time(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].extend(
            [
                self.evidence_row("WSEV-CM-ORIGINAL"),
                self.evidence_row(
                    "WSEV-CM-CORRECTION",
                    roles=["FACTUAL_OBSERVATION", "CORRECTION_OR_REVISION"],
                ),
            ]
        )
        original = self.observation_row(
            "WSLI-CM-ORIGINAL",
            ["WSEV-CM-ORIGINAL"],
            observed_at_utc="2026-09-10T01:00:00Z",
        )
        corrected = self.observation_row(
            "WSLI-CM-CORRECTED",
            ["WSEV-CM-CORRECTION"],
            observed_at_utc="2026-09-10T02:00:00Z",
            verification_state="CORRECTED",
        )
        corrected["revision_of_observation_id"] = original["observation_id"]
        observations["observations"].extend([original, corrected])

        report = self.validate(schema, evidence, observations)
        self.assertTrue(report.ok, report.errors)

    def test_valid_retraction_uses_same_append_only_contract(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].extend(
            [
                self.evidence_row("WSEV-CM-RETRACT-ORIGINAL"),
                self.evidence_row(
                    "WSEV-CM-RETRACT",
                    roles=["CORRECTION_OR_REVISION"],
                ),
            ]
        )
        original = self.observation_row(
            "WSLI-CM-RETRACT-ORIGINAL",
            ["WSEV-CM-RETRACT-ORIGINAL"],
            observed_at_utc="2026-09-10T03:00:00Z",
        )
        retracted = self.observation_row(
            "WSLI-CM-RETRACTED",
            ["WSEV-CM-RETRACT"],
            observed_at_utc="2026-09-10T03:01:00Z",
            verification_state="RETRACTED",
        )
        retracted["revision_of_observation_id"] = original["observation_id"]
        observations["observations"].extend([original, retracted])
        report = self.validate(schema, evidence, observations)
        self.assertTrue(report.ok, report.errors)

    def test_corrected_or_retracted_without_correction_evidence_fails(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].append(self.evidence_row("WSEV-CM-NO-REVISION-ROLE"))
        original = self.observation_row(
            "WSLI-CM-BASE",
            ["WSEV-CM-NO-REVISION-ROLE"],
            observed_at_utc="2026-09-10T04:00:00Z",
        )
        corrected = self.observation_row(
            "WSLI-CM-BAD-CORRECTION",
            ["WSEV-CM-NO-REVISION-ROLE"],
            observed_at_utc="2026-09-10T05:00:00Z",
            verification_state="CORRECTED",
        )
        corrected["revision_of_observation_id"] = original["observation_id"]
        observations["observations"].extend([original, corrected])
        report = self.validate(schema, evidence, observations)
        self.assertIn(
            "requires evidence with CORRECTION_OR_REVISION role",
            " ".join(report.errors),
        )

    def test_corrected_or_retracted_must_be_observed_strictly_after_target(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].append(
            self.evidence_row(
                "WSEV-CM-CHRONOLOGY",
                roles=["CORRECTION_OR_REVISION"],
            )
        )
        original = self.observation_row(
            "WSLI-CM-CHRONOLOGY-BASE",
            ["WSEV-CM-CHRONOLOGY"],
            observed_at_utc="2026-09-10T06:00:00Z",
        )
        corrected = self.observation_row(
            "WSLI-CM-CHRONOLOGY-BAD",
            ["WSEV-CM-CHRONOLOGY"],
            observed_at_utc="2026-09-10T06:00:00Z",
            verification_state="CORRECTED",
        )
        corrected["revision_of_observation_id"] = original["observation_id"]
        observations["observations"].extend([original, corrected])
        report = self.validate(schema, evidence, observations)
        self.assertIn(
            "must be observed strictly later than revision target",
            " ".join(report.errors),
        )

    def test_corrected_or_retracted_without_revision_target_fails(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].append(
            self.evidence_row(
                "WSEV-CM-MISSING-TARGET",
                roles=["CORRECTION_OR_REVISION"],
            )
        )
        corrected = self.observation_row(
            "WSLI-CM-MISSING-TARGET",
            ["WSEV-CM-MISSING-TARGET"],
            observed_at_utc="2026-09-10T07:00:00Z",
            verification_state="CORRECTED",
        )
        observations["observations"].append(corrected)
        report = self.validate(schema, evidence, observations)
        self.assertIn(
            "corrected/retracted live observation requires revision reference",
            " ".join(report.errors),
        )

    def test_valid_conflicting_reports_requires_two_providers_and_description(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].extend(
            [
                self.evidence_row("WSEV-CM-CONFLICT-A", provider="Authority A"),
                self.evidence_row("WSEV-CM-CONFLICT-B", provider="Authority B"),
            ]
        )
        conflict = self.observation_row(
            "WSLI-CM-CONFLICT",
            ["WSEV-CM-CONFLICT-A", "WSEV-CM-CONFLICT-B"],
            observed_at_utc="2026-09-10T08:00:00Z",
            verification_state="CONFLICTING_REPORTS",
        )
        conflict["conflict_description"] = (
            "Authority A reports proposition X while Authority B reports incompatible proposition Y."
        )
        observations["observations"].append(conflict)
        report = self.validate(schema, evidence, observations)
        self.assertTrue(report.ok, report.errors)

    def test_conflicting_reports_requires_two_unique_evidence_records(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].append(
            self.evidence_row("WSEV-CM-CONFLICT-ONE", provider="Authority A")
        )
        conflict = self.observation_row(
            "WSLI-CM-CONFLICT-ONE",
            ["WSEV-CM-CONFLICT-ONE", "WSEV-CM-CONFLICT-ONE"],
            observed_at_utc="2026-09-10T09:00:00Z",
            verification_state="CONFLICTING_REPORTS",
        )
        conflict["conflict_description"] = "Two incompatible claims are reported."
        observations["observations"].append(conflict)
        report = self.validate(schema, evidence, observations)
        self.assertIn(
            "requires at least two unique evidence records",
            " ".join(report.errors),
        )

    def test_conflicting_reports_requires_distinct_normalised_providers(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].extend(
            [
                self.evidence_row("WSEV-CM-SAME-A", provider=" Test Authority "),
                self.evidence_row("WSEV-CM-SAME-B", provider="test authority"),
            ]
        )
        conflict = self.observation_row(
            "WSLI-CM-SAME-PROVIDER",
            ["WSEV-CM-SAME-A", "WSEV-CM-SAME-B"],
            observed_at_utc="2026-09-10T10:00:00Z",
            verification_state="CONFLICTING_REPORTS",
        )
        conflict["conflict_description"] = "Two incompatible claims are reported."
        observations["observations"].append(conflict)
        report = self.validate(schema, evidence, observations)
        self.assertIn(
            "requires evidence from at least two distinct providers",
            " ".join(report.errors),
        )

    def test_conflicting_reports_requires_non_empty_description(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].extend(
            [
                self.evidence_row("WSEV-CM-DESC-A", provider="Authority A"),
                self.evidence_row("WSEV-CM-DESC-B", provider="Authority B"),
            ]
        )
        conflict = self.observation_row(
            "WSLI-CM-NO-DESCRIPTION",
            ["WSEV-CM-DESC-A", "WSEV-CM-DESC-B"],
            observed_at_utc="2026-09-10T11:00:00Z",
            verification_state="CONFLICTING_REPORTS",
        )
        conflict["conflict_description"] = "   "
        observations["observations"].append(conflict)
        report = self.validate(schema, evidence, observations)
        self.assertIn(
            "CONFLICTING_REPORTS requires non-empty conflict_description",
            " ".join(report.errors),
        )

    def test_conflict_description_is_rejected_outside_conflict_state(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].append(self.evidence_row("WSEV-CM-STRAY-DESC"))
        row = self.observation_row(
            "WSLI-CM-STRAY-DESC",
            ["WSEV-CM-STRAY-DESC"],
            observed_at_utc="2026-09-10T12:00:00Z",
        )
        row["conflict_description"] = "This field must not decorate a non-conflicting row."
        observations["observations"].append(row)
        report = self.validate(schema, evidence, observations)
        self.assertIn(
            "conflict_description is only allowed for CONFLICTING_REPORTS",
            " ".join(report.errors),
        )

    def test_data_revision_remains_external_and_needs_no_prior_live_row(self):
        schema, evidence, observations = self.synthetic_state()
        evidence["evidence"].append(
            self.evidence_row(
                "WSEV-CM-DATA-REVISION",
                roles=["FACTUAL_OBSERVATION", "CORRECTION_OR_REVISION"],
            )
        )
        revision = self.observation_row(
            "WSLI-CM-DATA-REVISION",
            ["WSEV-CM-DATA-REVISION"],
            observed_at_utc="2026-09-10T13:00:00Z",
        )
        revision["observation_type"] = "DATA_REVISION"
        revision["revision_target_description"] = "Previously published external estimate."
        observations["observations"].append(revision)
        report = self.validate(schema, evidence, observations)
        self.assertTrue(report.ok, report.errors)

    def test_contract_policy_drift_fails_closed(self):
        schema = copy.deepcopy(self.schema)
        schema["correction_conflict_policy"]["minimum_distinct_conflict_providers"] = 1
        report = self.validate(schema, self.evidence, self.observations)
        self.assertIn(
            "minimum_distinct_conflict_providers=2",
            " ".join(report.errors),
        )


if __name__ == "__main__":
    unittest.main()
