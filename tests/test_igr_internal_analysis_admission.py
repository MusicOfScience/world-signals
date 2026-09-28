"""Step 14F: exact owner authority, atomic admission and two publication gates."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from world_signals import igr_analysis_admission as admission
from world_signals.analysis import validate_analysis, public_analysis_projection
from world_signals.analysis_publication import review_publication_errors
from world_signals.analysis_revision_projection import public_analysis_projection_with_revision_contract
from world_signals.official_projection_review import AUDIT_AXES, validate_official_projection_review
from world_signals.world_state_history import fingerprint


class IGRInternalAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviews = admission.load(ROOT, admission.REVIEWS_PATH)
        cls.evidence = admission.load(ROOT, admission.EVIDENCE_PATH)
        cls.schema = admission.load(ROOT, "data/analysis/schema.json")
        cls.canonical = admission.load(ROOT, "data/canonical/registry.json")
        cls.row = next(r for r in cls.reviews["reviews"] if r["analysis_id"] == admission.ANALYSIS_ID)
        cls.extension = cls.row["official_projection_review"]
        cls.transaction = admission.load(ROOT, admission.TRANSACTION_PATH)
        cls.package = admission.verify_package(ROOT)

    def project(self, reviews=None, revision=False):
        function = public_analysis_projection_with_revision_contract if revision else public_analysis_projection
        return function(self.schema, self.evidence, reviews or self.reviews, self.canonical)

    def pre_state(self, root):
        for directory in ("data", "web"):
            shutil.copytree(ROOT / directory, root / directory)
        for p in (admission.REVIEW_PATH, admission.TRANSACTION_PATH):
            (root / p).unlink()
        reviews, evidence = deepcopy(self.reviews), deepcopy(self.evidence)
        reviews["reviews"] = [r for r in reviews["reviews"] if r["analysis_id"] != admission.ANALYSIS_ID]
        reviews.pop("publication_decisions")
        reviews["version"] = evidence["version"] = "0.18"
        evidence["evidence"] = [e for e in evidence["evidence"] if e["evidence_id"] not in admission.EVIDENCE_MAPPING.values()]
        for p, value in ((admission.REVIEWS_PATH, reviews), (admission.EVIDENCE_PATH, evidence)):
            (root / p).write_text(admission.encoded(value))

    def construct(self, root, decision=admission.DISPOSITIONS):
        return admission.construct(root, self.transaction["reviewed_at_utc"],
                                   self.transaction["admitted_at_utc"], human_decision=decision)

    def test_exact_retained_pins_and_package_immutable(self):
        before = {name: (ROOT / "data/analysis" / name).read_bytes() for name in admission.FILES.values()}
        self.assertEqual({k: v["semantic_fingerprint"] for k, v in admission.verify_package(ROOT).items()}, admission.PINS)
        self.assertEqual(before, {n: (ROOT / "data/analysis" / n).read_bytes() for n in before})

    def test_separable_human_dispositions(self):
        review = admission.load(ROOT, admission.REVIEW_PATH)
        self.assertEqual(review["dispositions"], admission.DISPOSITIONS)
        self.assertEqual(review["dispositions"]["independent_historical_backtest"], "DEFER")
        self.assertFalse(review["public_projection_permitted"])

    def test_exact_internal_identity_review_state_and_content_cutoff(self):
        self.assertEqual((self.row["analysis_id"], self.row["review_state"], self.row["analysis_as_of_utc"]),
                         (admission.ANALYSIS_ID, "REVIEWED", "2026-09-28T16:25:00Z"))
        self.assertLess(self.row["analysis_as_of_utc"], self.transaction["reviewed_at_utc"])
        self.assertLessEqual(self.transaction["reviewed_at_utc"], self.transaction["admitted_at_utc"])

    def test_canonical_and_factual_spine_unchanged_except_evidence_mapping(self):
        expected = admission.remap(self.package["analysis_candidate"]["review"])
        expected["review_state"] = "REVIEWED"
        self.assertEqual({k: v for k, v in self.row.items() if k != "official_projection_review"}, expected)

    def test_no_synthetic_actual_surprise_market_or_second_order(self):
        self.assertEqual(self.row["what_happened"]["actuals"], [])
        self.assertEqual(self.row["what_surprised"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(self.row["what_moved"], [])
        self.assertEqual(self.row["second_order_effects"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(self.row["what_appears_connected"]["causal_status"], "NOT_A_CAUSAL_CLAIM")
        self.assertEqual(self.row["what_appears_connected"]["confidence"], "LOW")

    def test_permanent_evidence_mapping_and_no_candidate_ids(self):
        rows = [e for e in self.evidence["evidence"] if e["evidence_id"] in admission.EVIDENCE_MAPPING.values()]
        self.assertEqual(rows, admission.remap(self.package["analysis_candidate"]["candidate_local_evidence"]))
        self.assertTrue(all(e["canonical_provenance_effect"] == "NONE" for e in rows))
        self.assertNotIn("WSEV-CANDIDATE-", json.dumps(self.reviews))
        self.assertNotIn("WSEV-CANDIDATE-", json.dumps(self.evidence))

    def test_exact_review_and_evidence_populations(self):
        self.assertEqual((self.reviews["version"], len(self.reviews["reviews"])), ("0.19", 23))
        self.assertEqual((self.evidence["version"], len(self.evidence["evidence"])), ("0.19", 100))
        self.assertEqual(sum(bool(r.get("revision_of_analysis_id")) for r in self.reviews["reviews"]), 1)

    def test_all_reviews_have_exactly_one_explicit_decision(self):
        self.assertEqual(review_publication_errors(self.reviews), [])
        decisions = self.reviews["publication_decisions"]
        self.assertEqual(list(decisions.values()).count("PUBLIC"), 22)
        self.assertEqual(list(decisions.values()).count("INTERNAL_ONLY"), 1)

    def test_missing_decision_fails_native_and_public(self):
        for missing in (admission.ANALYSIS_ID, self.reviews["reviews"][0]["analysis_id"]):
            rows = deepcopy(self.reviews); del rows["publication_decisions"][missing]
            self.assertFalse(validate_analysis(self.schema, self.evidence, rows, self.canonical).ok)
            with self.assertRaisesRegex(ValueError, "UNCLASSIFIED_ANALYSIS_PUBLICATION_REVIEW"):
                self.project(rows)

    def test_missing_table_is_not_implicit_public(self):
        rows = deepcopy(self.reviews); rows.pop("publication_decisions")
        self.assertFalse(validate_analysis(self.schema, self.evidence, rows, self.canonical).ok)
        with self.assertRaises(ValueError): self.project(rows)

    def test_unknown_disposition_or_dangling_decision_fails(self):
        for key, value in ((admission.ANALYSIS_ID, "DEFAULT"), ("UNKNOWN", "PUBLIC")):
            rows = deepcopy(self.reviews); rows["publication_decisions"][key] = value
            with self.assertRaises(ValueError): self.project(rows)

    def test_draft_cannot_be_public(self):
        rows = deepcopy(self.reviews); rows["reviews"][0]["review_state"] = "DRAFT"
        with self.assertRaisesRegex(ValueError, "DRAFT_ANALYSIS_PUBLICATION_PROHIBITED"): self.project(rows)

    def test_field_allowlist_applies_even_after_object_gate(self):
        for index in (0, -1):
            rows = deepcopy(self.reviews); rows["reviews"][index]["unknown_secret"] = "never leak"
            with self.assertRaisesRegex(ValueError, "UNCLASSIFIED_ANALYSIS_PUBLICATION_FIELD"): self.project(rows)

    def test_internal_extension_counts_native_audit_and_unresolved_preserved(self):
        self.assertEqual(validate_official_projection_review(self.extension), ())
        self.assertEqual(tuple(len(self.extension[k]) for k in ("projection_outputs", "model_assumptions", "sensitivity_cases")), (25, 15, 8))
        self.assertEqual(self.extension["assumption_audit"], self.package["assumption_audit"]["assumption_audit"])
        for audit in self.extension["assumption_audit"]: self.assertTrue(set(AUDIT_AXES) <= audit.keys())
        mortality = next(a for a in self.extension["assumption_audit"] if a["assumption_id"].endswith("MORTALITY"))
        self.assertIn("trajectory judgement remains unresolved", mortality["current_trajectory"]["finding"])

    def test_scores_ratings_grades_remain_prohibited(self):
        for key in ("score", "rating", "grade"):
            extension = deepcopy(self.extension); extension["assumption_audit"][0][key] = 1
            self.assertTrue(validate_official_projection_review(extension))

    def test_independent_backtest_deferred_not_relabelled(self):
        self.assertEqual(self.extension["admission_review"]["independent_historical_backtest_status"], "DEFERRED")
        self.assertEqual([r["comparability"] for r in self.extension["historical_backtest"]],
                         ["QUALIFIED_COMPARISON", "QUALIFIED_COMPARISON", "NOT_DIRECTLY_COMPARABLE"])
        self.assertIsNone(self.extension["historical_backtest"][-1]["error"])
        self.assertEqual(self.extension["error_interpretation"], "MODEL_ERROR_IS_NOT_EVIDENCE_OF_BAD_FAITH")

    def test_dependency_map_exact_internal_structure_without_transitive_edges(self):
        self.assertEqual(self.extension["dependency_map"], self.package["assumption_audit"]["dependency_map"])
        self.assertTrue(all(e["production_relationship"] is False for e in self.extension["dependency_map"]))
        self.assertEqual(self.extension["admission_review"]["dependency_map_disposition"], "INTERNAL_MODEL_STRUCTURE")

    def test_same_origin_and_model_output_are_not_corroboration(self):
        self.assertIn("NOT_INDEPENDENT", self.extension["corroboration_policy"])
        self.assertEqual(self.extension["admission_review"]["model_provenance"]["factual_evidence_status"],
                         "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION")

    def test_public_reviews_evidence_readiness_exclude_igr(self):
        projected = self.project()
        self.assertEqual(len(projected["reviews"]), 22)
        text = json.dumps(projected)
        for secret in (admission.ANALYSIS_ID, "official_projection_review", *admission.EVIDENCE_MAPPING.values()):
            self.assertNotIn(secret, text)

    def test_revision_projection_has_same_public_reviews_and_policy(self):
        self.assertEqual(self.project()["reviews"], self.project(revision=True)["reviews"])

    def test_legacy_public_semantics_match_admission_baseline(self):
        projected = self.project()
        for key in ("review_dataset_version", "evidence_registry_version"): projected["metadata"].pop(key)
        self.assertEqual(fingerprint(projected), self.transaction["legacy_public_semantic_fingerprint"])

    def test_brief_uses_public_review_and_never_internal_igr(self):
        from world_signals.public_briefing import build_public_briefing
        outlook = json.loads((ROOT / "docs/data/outlook.json").read_text())
        calendar = json.loads((ROOT / "docs/data/events.json").read_text())
        brief = build_public_briefing(outlook, calendar, self.project(revision=True))
        self.assertEqual(brief, json.loads((ROOT / "docs/data/briefing.json").read_text()))
        self.assertNotIn(admission.ANALYSIS_ID, json.dumps(brief))

    def test_real_transaction_poststate_and_object_hashes_validate(self):
        self.assertEqual(len(admission.validate_admitted(ROOT, exact_post_state=True)["reviews"]), 22)
        self.assertEqual(fingerprint(self.row), self.transaction["production_review_sha256"])
        self.assertEqual(fingerprint(self.extension), self.transaction["internal_extension_sha256"])

    def test_explicit_owner_decision_required_no_default(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.pre_state(root)
            for decision in (None, {}, {**admission.DISPOSITIONS, "public_analysis": "ACCEPT"}):
                with self.assertRaisesRegex(ValueError, "explicit exact owner"): self.construct(root, decision)

    def test_construct_reproduces_and_inputs_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.pre_state(root)
            before = admission.protected_hashes(root)
            a, b = self.construct(root), self.construct(root)
            self.assertEqual(a, b)
            self.assertEqual(before, admission.protected_hashes(root))
            self.assertEqual(a[admission.TRANSACTION_PATH]["production_review_sha256"], self.transaction["production_review_sha256"])

    def test_tampered_retained_candidate_blocks_no_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.pre_state(root)
            p = root / "data/analysis" / admission.FILES["analysis_candidate"]
            value = json.loads(p.read_text()); value["review"]["scope"] = "tampered"
            p.write_text(admission.encoded(value)); before = admission.protected_hashes(root)
            with self.assertRaises(ValueError): self.construct(root)
            self.assertEqual(before, admission.protected_hashes(root))

    def test_atomic_transaction_failure_rolls_back_all_targets(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.pre_state(root); targets = self.construct(root)
            before = {p: (root / p).read_bytes() for p in (admission.REVIEWS_PATH, admission.EVIDENCE_PATH)}
            real = admission.validate_admitted
            def fail_actual(path, **kwargs):
                if path == root: raise ValueError("injected post-write failure")
                return real(path, **kwargs)
            with patch.object(admission, "validate_admitted", side_effect=fail_actual):
                with self.assertRaisesRegex(ValueError, "injected"): admission.materialize(root, targets)
            self.assertEqual(before, {p: (root / p).read_bytes() for p in before})
            self.assertFalse((root / admission.REVIEW_PATH).exists())
            self.assertFalse((root / admission.TRANSACTION_PATH).exists())

    def test_exact_bounded_success_and_protected_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.pre_state(root); before = admission.protected_hashes(root)
            admission.materialize(root, self.construct(root))
            self.assertEqual(before, admission.protected_hashes(root))
            self.assertEqual(len(admission.validate_admitted(root)["reviews"]), 22)

    def test_prestate_drift_blocks_materialization(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.pre_state(root); targets = self.construct(root)
            p = root / admission.EVIDENCE_PATH; p.write_text(p.read_text() + "\n")
            before = p.read_bytes()
            with self.assertRaisesRegex(ValueError, "pre-state changed"): admission.materialize(root, targets)
            self.assertEqual(p.read_bytes(), before)

    def test_no_arbitrary_target_in_materializer(self):
        with self.assertRaisesRegex(ValueError, "exact bounded targets"):
            admission.materialize(ROOT, {"data/forecasts/forecasts.json": {}})

    def test_historical_admission_is_not_a_permanent_evidence_population_ceiling(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for directory in ("data", "web"): shutil.copytree(ROOT / directory, root / directory)
            evidence = admission.load(root, admission.EVIDENCE_PATH)
            extra = deepcopy(evidence["evidence"][0]); extra["evidence_id"] = "WSEV-SYNTHETIC-UNRELATED"
            evidence["evidence"].append(extra)
            (root / admission.EVIDENCE_PATH).write_text(admission.encoded(evidence))
            self.assertEqual(len(admission.validate_admitted(root)["reviews"]), 22)
            with self.assertRaisesRegex(ValueError, "post-state mismatch"):
                admission.validate_admitted(root, exact_post_state=True)

    def test_protected_upstream_and_web_hashes_match_transaction(self):
        for path, digest in self.transaction["protected_input_hashes"].items():
            # Recovery snapshot is an expressly derived, regenerated count surface.
            if path == "data/status/current_state.json": continue
            self.assertEqual(admission.byte_hash((ROOT / path).read_bytes()), digest, path)

    def test_world_state_counts_and_no_downstream_write_targets(self):
        for filename, key, expected in (("components", "components", 5), ("snapshots", "snapshots", 3),
                                         ("admission_transactions", "transactions", 3)):
            self.assertEqual(len(admission.load(ROOT, "data/world_state/" + filename + ".json")[key]), expected)
        self.assertEqual(self.transaction["downstream_write_targets"], [])

    def test_internal_reader_keeps_model_refs_out_of_factual_evidence_namespace(self):
        from world_signals.world_state_read import read_world_state, WORLD_STATE_DIMENSIONS
        request = {"contract_version": "0.1", "as_of_utc": "2026-09-29T00:00:00Z",
                   "scope": {"jurisdictions": ["*"], "dimensions": sorted(WORLD_STATE_DIMENSIONS), "actor_ids": None},
                   "include_negative_evidence": False, "input_policy": "ACCEPTED_REVIEWED_HEADS_ONLY"}
        result = read_world_state(request)
        self.assertIn(admission.ANALYSIS_ID, json.dumps(result["source_manifest"]))
        # Exact review objects intentionally retain the internal extension. Only
        # manifest identities, not nested model refs, denote factual source rows.
        self.assertFalse(any(r["object_id"].startswith(("WSASM-", "WSPROJ-", "WSSENS-"))
                             for r in result["source_manifest"]))


if __name__ == "__main__": unittest.main()
