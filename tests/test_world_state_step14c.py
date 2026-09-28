from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_production import derive_current_use  # noqa: E402
from world_signals.world_state_step14c import (  # noqa: E402
    BASELINE_ID,
    CLIMATE_ADMISSION_ID,
    CLIMATE_REVIEW_ID,
    DIMENSION_ID,
    EXPECTED_BASELINE_FINGERPRINT,
    EXPECTED_DIMENSION_FINGERPRINT,
    EXPECTED_PACKAGE_FINGERPRINT,
    EXPECTED_SOURCE_MANIFEST,
    IGR_ADMISSION_ID,
    IGR_OCCURRENCE_ID,
    IGR_SERIES_ID,
    IGR_REVIEW_ID,
    Step14CError,
    TREASURY_SOURCE_IDS,
    build_climate_transaction,
    build_source_canonical_transaction,
    materialize_step14c,
)


TIMES = {"reviewed_at_utc": "2026-09-28T16:00:00Z", "admitted_at_utc": "2026-09-28T16:00:01Z"}


def copy_step14c_inputs(destination: Path) -> None:
    for relative in ("data/world_state", "data/world_state_audit", "data/coverage", "data/sources", "data/canonical"):
        source = ROOT / relative
        if source.exists():
            shutil.copytree(source, destination / relative)
    components_path = destination / "data/world_state/components.json"
    components = json.loads(components_path.read_text())
    components["components"] = [row for row in components["components"] if row.get("component_id") not in {BASELINE_ID, DIMENSION_ID}]
    components_path.write_text(json.dumps(components, indent=2) + "\n")
    snapshots_path = destination / "data/world_state/snapshots.json"
    snapshots = json.loads(snapshots_path.read_text())
    snapshots["snapshots"] = [row for row in snapshots["snapshots"] if row.get("snapshot_series_id") != "WSSNAP-CLIMATE-AU-TCSEASON-2025-26"]
    snapshots_path.write_text(json.dumps(snapshots, indent=2) + "\n")
    admissions_path = destination / "data/world_state/admission_transactions.json"
    admissions = json.loads(admissions_path.read_text())
    admissions["transactions"] = [row for row in admissions["transactions"] if row.get("transaction_id") != CLIMATE_ADMISSION_ID]
    admissions_path.write_text(json.dumps(admissions, indent=2) + "\n")
    sources_path = destination / "data/sources/registry.json"
    sources = json.loads(sources_path.read_text())
    sources["sources"] = [row for row in sources["sources"] if row.get("source_id") not in TREASURY_SOURCE_IDS]
    sources["version"] = "2.04"
    sources_path.write_text(json.dumps(sources, indent=2) + "\n")
    canonical_path = destination / "data/canonical/registry.json"
    canonical = json.loads(canonical_path.read_text())
    canonical["records"] = [row for row in canonical["records"] if row.get("occurrence_id") != IGR_OCCURRENCE_ID and row.get("series_id") != IGR_SERIES_ID]
    canonical["record_count"] = len(canonical["records"])
    canonical["version"] = "0.43"
    canonical["reference_date"] = "2026-09-10"
    canonical_path.write_text(json.dumps(canonical, indent=2) + "\n")


def file_hashes(root: Path) -> dict[str, str]:
    paths = [path for relative in ("data/world_state", "data/sources", "data/canonical", "data/coverage") for path in (root / relative).rglob("*") if path.is_file()]
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


class Step14CAdmissionTests(unittest.TestCase):
    def test_retained_step14a_package_is_exactly_pinned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            built = build_climate_transaction(root, **TIMES)
        self.assertEqual(built["package"]["source_manifest_sha256"], EXPECTED_SOURCE_MANIFEST)
        self.assertEqual(built["package"]["baseline_candidate_fingerprint"], EXPECTED_BASELINE_FINGERPRINT)
        self.assertEqual(built["package"]["dimension_candidate_fingerprint"], EXPECTED_DIMENSION_FINGERPRINT)
        self.assertEqual(built["package"]["candidate_semantic_fingerprint"], EXPECTED_PACKAGE_FINGERPRINT)

    def test_climate_admission_is_historical_and_internal_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            built = build_climate_transaction(root, **TIMES)
        rows = {row["component_id"]: row for row in built["components"]}
        self.assertEqual(set(rows), {BASELINE_ID, DIMENSION_ID})
        for row in rows.values():
            self.assertEqual(row["review_state"], "ACCEPTED")
            self.assertEqual(row["lifecycle_state"], "EXPIRED")
            self.assertEqual(row["visibility"], "INTERNAL_ONLY")
            self.assertEqual(row["review_transaction_id"], CLIMATE_REVIEW_ID)
            self.assertEqual(row["admission_transaction_id"], CLIMATE_ADMISSION_ID)
        self.assertEqual(derive_current_use(rows[BASELINE_ID], {"status": "NO_FRESHNESS_POLICY"})["status"], "HISTORICAL_ONLY")
        self.assertEqual(derive_current_use(rows[DIMENSION_ID], {"status": "NO_FRESHNESS_POLICY"})["status"], "HISTORICAL_ONLY")
        self.assertEqual(built["snapshot"]["lifecycle_state"], "EXPIRED")
        self.assertFalse(built["transaction"]["public_projection_permitted"])

    def test_climate_measurements_and_scope_are_preserved_without_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            built = build_climate_transaction(root, **TIMES)
        dimension = next(row for row in built["components"] if row["component_id"] == DIMENSION_ID)
        self.assertEqual(dimension["dimension"], "CLIMATE_PHYSICAL_RISK")
        self.assertEqual(dimension["scope"]["jurisdictions"], ["Australia"])
        self.assertEqual({row["value"] for row in dimension["realised_measurements"]}, {11, 7, 2, 4})
        self.assertEqual(dimension["what_surprised"], "NOT_ESTABLISHED")
        self.assertEqual(dimension["direction"], "NOT_ASSESSED")
        self.assertEqual(dimension["qualitative_confidence"], "NOT_ASSESSED")
        self.assertEqual(dimension["anomaly_refs"], [])
        self.assertEqual(built["snapshot"]["empty_queried_domains"], built["package"]["known_empty_or_unsupported_domains"])

    def test_source_and_canonical_transaction_is_manual_only_and_non_analytical(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            built = build_source_canonical_transaction(root, **TIMES)
        self.assertEqual([row["source_id"] for row in built["sources"]], list(TREASURY_SOURCE_IDS))
        for source in built["sources"]:
            self.assertEqual(source["verification_mode"], "MANUAL_AUTHORITATIVE_RECHECK")
            self.assertEqual(source["monitoring_activation_status"], "PRODUCTION_AUTOMATION_HOLD")
            self.assertEqual(source["monitor_endpoints"], [])
            self.assertEqual(source["automated_monitoring_use"], "MANUAL_ONLY_RIGHTS_HOLD")
        occurrence = built["canonical"]
        self.assertEqual(occurrence["series_id"], IGR_SERIES_ID)
        self.assertEqual(occurrence["occurrence_id"], IGR_OCCURRENCE_ID)
        self.assertEqual(occurrence["start_local"], "2026-09-21")
        self.assertIsNone(occurrence["start_utc"])
        self.assertEqual(occurrence["time_precision"], "DAY")
        self.assertEqual(occurrence["first_announced_at"], "2026-09-09")
        self.assertEqual(occurrence["first_discovered_at"], "2026-09-28T14:17:45Z")
        self.assertIsNone(occurrence["recurrence"])
        self.assertEqual(built["canonical"]["related_documents"][0]["document_types"], ["MAIN_REPORT", "FACT_SHEET", "CHART_DATA"])
        self.assertEqual(built["transaction"]["transaction_id"], IGR_ADMISSION_ID)
        self.assertFalse(built["transaction"]["analytical_promotion"])
        self.assertFalse(built["transaction"]["public_projection_permitted"])

    def test_builders_are_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            before = file_hashes(root)
            build_climate_transaction(root, **TIMES)
            build_source_canonical_transaction(root, **TIMES)
            self.assertEqual(before, file_hashes(root))

    def test_bad_retained_package_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            package_path = root / "data/world_state_audit/STEP14A_AU_TROPICAL_CYCLONE_CANDIDATE_REVIEW_PENDING.json"
            package = json.loads(package_path.read_text())
            package["candidate_semantic_fingerprint"] = "0" * 64
            package_path.write_text(json.dumps(package))
            before = file_hashes(root)
            with self.assertRaises(Step14CError):
                materialize_step14c(root, **TIMES)
            self.assertEqual(before, file_hashes(root))

    def test_independent_transactions_materialise_expected_counts_on_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            result = materialize_step14c(root, **TIMES)
            components = json.loads((root / "data/world_state/components.json").read_text())["components"]
            snapshots = json.loads((root / "data/world_state/snapshots.json").read_text())["snapshots"]
            admissions = json.loads((root / "data/world_state/admission_transactions.json").read_text())["transactions"]
            sources = json.loads((root / "data/sources/registry.json").read_text())["sources"]
            canonical = json.loads((root / "data/canonical/registry.json").read_text())["records"]
            self.assertEqual(len(components), 5)
            self.assertEqual(len(snapshots), 3)
            self.assertEqual(len(admissions), 3)
            self.assertEqual(len(sources), 260)
            self.assertEqual(len(canonical), 690)
            self.assertEqual(result["climate"]["transaction_id"], CLIMATE_ADMISSION_ID)
            self.assertEqual(result["sources_and_canonical"]["transaction_id"], IGR_ADMISSION_ID)
            self.assertTrue((root / "data/world_state_audit/STEP14C_AU_TC_COMPONENT_REVIEW_ACCEPTED.json").exists())
            self.assertTrue((root / "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_REVIEW_ACCEPTED.json").exists())
            self.assertTrue((root / "data/coverage/STEP14C_AU_IGR_SOURCE_CANONICAL_ADMISSION_TRANSACTION.json").exists())

    def test_source_transaction_failure_does_not_apply_climate_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_step14c_inputs(root)
            source_path = root / "data/coverage/STEP14B_AU_TREASURY_SOURCE_GOVERNANCE_CANDIDATES_v0.1.json"
            source = json.loads(source_path.read_text())
            source["review_state"] = "REJECTED"
            source_path.write_text(json.dumps(source))
            before = file_hashes(root)
            with self.assertRaises(Step14CError):
                materialize_step14c(root, **TIMES)
            self.assertEqual(before, file_hashes(root))


if __name__ == "__main__":
    unittest.main()
