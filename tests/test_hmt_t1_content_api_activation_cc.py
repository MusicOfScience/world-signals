import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HMTT1ActivationCC(unittest.TestCase):
    def test_governed_poststate_and_gates(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        sources = json.loads((ROOT / "data/sources/registry.json").read_text())
        monitor = json.loads((ROOT / "data/monitor/expectations.json").read_text())
        self.assertEqual((canonical["version"], len(canonical["records"])), ("0.41", 689))
        self.assertEqual((sources["version"], len(sources["sources"])), ("2.02", 257))
        self.assertEqual((monitor["version"], len(monitor["adapters"])), ("0.27", 25))
        self.assertFalse(monitor["automatic_canonical_commit"])
        self.assertFalse(monitor["google_calendar_write"])

        old = [s for s in sources["sources"] if s.get("source_id") == "WSSRC-MKT-012"]
        new = [s for s in sources["sources"] if s.get("source_id") == "WSSRC-MKT-014"]
        self.assertEqual(len(old), 1)
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0]["automated_monitoring_use"], "CLEARED")
        self.assertEqual(new[0]["live_adapter_id"], "HMT_T1_CONTENT_API")
        self.assertEqual(new[0]["canonical_provenance_use"], "MONITOR_ONLY_NOT_CANONICAL_AUTHORITY")
        self.assertEqual(new[0]["automated_monitoring_scope"]["request_budget_per_run"], 1)
        self.assertEqual(new[0]["automated_monitoring_scope"]["legislation_followup_request_count"], 0)

        adapters = [a for a in monitor["adapters"] if a.get("adapter_id") == "HMT_T1_CONTENT_API"]
        self.assertEqual(len(adapters), 1)
        cfg = adapters[0]
        self.assertEqual(cfg["source_id"], "WSSRC-MKT-014")
        self.assertEqual(cfg["canonical_occurrence_ids"], ["WSO-MKT-A-0016"])
        self.assertEqual(cfg["monitor_role"], "CONDITIONAL_LEGISLATIVE_DEPENDENCY_SENTINEL")
        self.assertEqual(cfg["request_budget_per_run"], 1)
        for key in (
            "schedule_authority", "clock_authority", "lifecycle_authority", "certainty_authority",
            "condition_state_authority", "canonical_datetime_mutation_allowed",
            "automatic_attachment_fetch_allowed", "automatic_parent_page_fetch_allowed",
            "automatic_legislation_followup_allowed", "automatic_new_occurrence_creation_allowed",
            "automatic_live_or_analysis_promotion_allowed", "automatic_commit_allowed",
        ):
            self.assertIs(cfg[key], False, key)

    def test_exact_canonical_object_remains_conditional(self):
        canonical = json.loads((ROOT / "data/canonical/registry.json").read_text())
        rows = [r for r in canonical["records"] if r.get("occurrence_id") == "WSO-MKT-A-0016"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["source_id"], "WSSRC-MKT-012")
        self.assertEqual(row["series_id"], "WSER-MKT-UK-T1")
        self.assertEqual(row["activation_mode"], "CONDITIONAL")
        self.assertEqual(row["certainty_status"], "PROVISIONAL")
        self.assertEqual(row["condition_state"], "PENDING_DEPENDENCY")
        self.assertEqual(row["start_local"], "2027-10-11")


if __name__ == "__main__":
    unittest.main()
