from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OpecQuarantineCfTests(unittest.TestCase):
    def test_quarantine_record_identifies_parked_lineage(self):
        record = ROOT / "OPEC_QUARANTINE.md"
        self.assertTrue(record.exists(), "OPEC quarantine record missing")
        text = record.read_text(encoding="utf-8")
        self.assertIn("feature/post-cd-pressure-audit-ce", text)
        self.assertIn("#113", text)
        self.assertIn("MANUAL REACTIVATION ONLY", text)
        self.assertIn("Descendant-safety", text)
        self.assertIn("Transaction timestamps", text)
        self.assertIn("Primary-source rights", text)
        self.assertIn("Stable event identity", text)

    def test_quarantined_ce_transaction_files_are_not_live(self):
        forbidden = {
            ".github/workflows/ce-materialize-opec-primary.yml",
            ".github/workflows/ce-post-cd-pressure-audit.yml",
            "data/coverage/OPEC_PRIMARY_PROVENANCE_CE_PLAN_v0.1.json",
            "data/coverage/OPEC_PRIMARY_PROVENANCE_CE_RESEARCH_v0.1.md",
            "scripts/apply_opec_primary_provenance_ce.py",
            "tests/test_opec_primary_provenance_ce.py",
        }
        live = sorted(path for path in forbidden if (ROOT / path).exists())
        self.assertEqual(
            live,
            [],
            "Quarantined CE OPEC machinery became live again; inspect OPEC_QUARANTINE.md "
            "and the preserved CE branch before deliberate reactivation",
        )


if __name__ == "__main__":
    unittest.main()
