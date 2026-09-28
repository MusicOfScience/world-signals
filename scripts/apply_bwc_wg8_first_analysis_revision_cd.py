from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.analysis import validate_analysis
from world_signals.analysis_revision import production_analysis_revision_count, validate_analysis_revisions
from world_signals.live_analysis_bridge import production_live_input_count

PLAN_PATH = ROOT / "data/analysis/BWC_WG8_FIRST_REVISION_CD_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
MONITOR_PATH = ROOT / "data/monitor/expectations.json"
LIVE_SCHEMA_PATH = ROOT / "data/live_intelligence/schema.json"
LIVE_OBSERVATIONS_PATH = ROOT / "data/live_intelligence/observations.json"
LIVE_EVIDENCE_PATH = ROOT / "data/live_intelligence/evidence_registry.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"

PARENT_ID = "WSAN-BWC-WG8-2026-001"
CHILD_ID = "WSAN-BWC-WG8-2026-002"
NEW_EVIDENCE_IDS = {
    "WSEV-BWC-WG9-UN-INDICO-20260817",
    "WSEV-BWC-WG9-SHIB-REV7-20260827",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def assert_pre_state(plan: dict[str, Any]) -> None:
    c = load(CANONICAL_PATH)
    s = load(SOURCES_PATH)
    m = load(MONITOR_PATH)
    ls = load(LIVE_SCHEMA_PATH)
    lo = load(LIVE_OBSERVATIONS_PATH)
    le = load(LIVE_EVIDENCE_PATH)
    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    pre = plan["pre_state"]

    assert (c["version"], len(c["records"])) == (pre["canonical_version"], pre["canonical_count"])
    assert (s["version"], len(s["sources"])) == (pre["source_registry_version"], pre["source_count"])
    assert (m["version"], len(m["adapters"])) == (pre["monitor_version"], pre["monitor_adapter_count"])
    assert m["automatic_canonical_commit"] is False
    assert m["google_calendar_write"] is False
    assert (ls["version"], len(lo["observations"]), len(le["evidence"])) == (
        pre["live_version"], pre["live_observation_count"], pre["live_evidence_count"]
    )
    assert schema["version"] == pre["analysis_schema_version"]
    assert (reviews["version"], len(reviews["reviews"])) == (
        pre["analysis_reviews_version"], pre["analysis_review_count"]
    )
    assert (evidence["version"], len(evidence["evidence"])) == (
        pre["analysis_evidence_version"], pre["analysis_evidence_count"]
    )
    assert production_analysis_revision_count(reviews) == pre["production_analysis_revision_count"]
    assert production_live_input_count(reviews) == pre["production_live_input_count"]

    by_id = {r["analysis_id"]: r for r in reviews["reviews"]}
    assert PARENT_ID in by_id
    assert CHILD_ID not in by_id
    evidence_ids = {r["evidence_id"] for r in evidence["evidence"]}
    assert not (NEW_EVIDENCE_IDS & evidence_ids)

    policy = schema["analysis_revision_policy"]
    assert policy["mode"] == "FOUNDATION_ONLY_NO_PRODUCTION_REVISIONS"
    assert policy["production_analysis_revisions_allowed"] is False
    assert policy["public_revision_metadata_projection_allowed"] is False
    assert policy["automatic_latest_analysis_selection_allowed"] is False
    assert policy["public_revision_head_collapse_allowed"] is False


def new_evidence_rows() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "WSEV-BWC-WG9-UN-INDICO-20260817",
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "United Nations Office at Geneva / Indico.UN",
            "host_or_distribution": "United Nations Indico",
            "title": "Ninth Session of the Working Group on the Strengthening of the Biological Weapons Convention",
            "url": "https://indico.un.org/event/1018822/timetable/?view=standard_numbered",
            "published_at": None,
            "roles": ["SECOND_ORDER_OBSERVATION", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "The ninth session of the Working Group on the Strengthening of the Biological Weapons Convention took place in Geneva from 17 to 21 August 2026.",
                "The ninth session is observed institutional follow-through after the February 2026 eighth session; occurrence of the meeting does not itself establish substantive consensus or adoption of a final package."
            ],
            "analytical_use": "FACTUAL_METADATA_AND_SHORT_PARAPHRASE",
            "canonical_provenance_effect": "NONE"
        },
        {
            "evidence_id": "WSEV-BWC-WG9-SHIB-REV7-20260827",
            "evidence_class": "ACADEMIC_OR_INSTITUTIONAL",
            "provider": "Sussex Harvard Information Bank / CBW Events",
            "host_or_distribution": "SHIB-CBW Events catalogue",
            "title": "Biological Weapons Convention Working Group plus associated Meetings of States Parties",
            "url": "https://shib-temp.cbw-events.org.uk/bwc-wg_plus_msp/",
            "published_at": None,
            "roles": ["SECOND_ORDER_OBSERVATION", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "The specialist catalogue records BWC/WG/9/CRP.1/Rev.7 dated 27 August 2026 with the title 'Revised draft final report of the Working Group on the Strengthening of the Convention'.",
                "The catalogue links that record to the corresponding UNODA Documents Library file; WORLD SIGNALS uses this row only for document identity, date and draft-status label, not to infer agreement on individual passages."
            ],
            "analytical_use": "FACTUAL_METADATA_AND_SHORT_PARAPHRASE",
            "canonical_provenance_effect": "NONE",
            "distribution_note": "Primary document URL retained for provenance/navigation: https://docs-library.unoda.org/Biological_Weapons_Convention_-Working_Group_on_the_strengthening_of_the_ConventionNinth_session_(2026)/2026-08-27_BWC_WG_9_CRP1_Rev7.pdf . CD does not infer PDF-body semantics from this catalogue record."
        }
    ]


def build_child(parent: dict[str, Any]) -> dict[str, Any]:
    child = deepcopy(parent)
    child["analysis_id"] = CHILD_ID
    child["analysis_as_of_utc"] = "2026-09-09T07:48:00Z"
    child["scope"] = (
        "BWC Working Group eighth session with newly admitted ninth-session institutional follow-through: "
        "preserving the eighth-session historical result while updating the later process dependency from prospective to observed"
    )
    child["what_appears_connected"] = {
        "interaction_type": "LEGAL_OR_OPERATIONAL_DEPENDENCY",
        "causal_status": "NOT_A_CAUSAL_CLAIM",
        "confidence": "HIGH",
        "summary": (
            "The eighth session sits inside the same consensus-based institutional process that continued through the ninth session in August 2026. "
            "The observed ninth-session occurrence and later Rev.7 draft-final-report identity are operational follow-through on the unresolved text, not evidence of external causality or final adoption."
        ),
        "evidence_refs": [
            "WSEV-BWC-WG8-UNODA-MANDATE",
            "WSEV-BWC-WG8-UNODA-OUTCOME",
            "WSEV-BWC-WG9-UN-INDICO-20260817",
            "WSEV-BWC-WG9-SHIB-REV7-20260827",
            "WSEV-BWC-WG10-UNODA-SCHEDULE"
        ]
    }
    child["what_may_be_noise"] = [
        {
            "summary": (
                "Revision numbers and draft-document proliferation are not scalar measures of negotiating success. "
                "The existence of BWC/WG/9/CRP.1/Rev.7 is used only as evidence that a document still labelled a revised draft final report existed after the ninth session."
            ),
            "evidence_refs": ["WSEV-BWC-WG9-SHIB-REV7-20260827"]
        },
        {
            "summary": (
                "The absence of a market-movement entry remains intentional. Institutional continuation does not require a market proxy and does not establish a security, health or geopolitical effect."
            ),
            "evidence_refs": ["WSEV-BWC-WG9-UN-INDICO-20260817"]
        }
    ]
    child["alternative_explanations"] = [
        {
            "summary": (
                "Continued work across the ninth and scheduled tenth sessions may reflect unresolved substantive differences, the Convention's consensus procedure, deliberate sequencing, or a combination. "
                "The chronology alone does not identify which explanation dominates."
            ),
            "evidence_refs": [
                "WSEV-BWC-WG8-UNODA-MANDATE",
                "WSEV-BWC-WG9-UN-INDICO-20260817",
                "WSEV-BWC-WG10-UNODA-SCHEDULE"
            ]
        }
    ]
    child["second_order_effects"] = {
        "status": "OBSERVED",
        "summary": (
            "The parent packet treated later-session continuation as a watch item. That follow-through is now observed: the ninth session took place on 17–21 August 2026 and the specialist document catalogue records a Rev.7 artefact dated 27 August that remained titled a revised draft final report. "
            "UNODA still schedules a tenth session for 7–11 December 2026. These facts establish continuation of the institutional pathway, not completion of the final consensus package."
        ),
        "evidence_refs": [
            "WSEV-BWC-WG9-UN-INDICO-20260817",
            "WSEV-BWC-WG9-SHIB-REV7-20260827",
            "WSEV-BWC-WG10-UNODA-SCHEDULE"
        ]
    }
    child["falsifiers"] = [
        "If an authoritative eighth-session record establishes that the substantive final strengthening report itself was adopted by consensus on 13 February 2026, the historical eighth-session conclusion must be revised.",
        "If an authoritative ninth-session record establishes that the Working Group's final consensus report was adopted during the ninth session, the CD conclusion that final consensus remained open after that session must be withdrawn.",
        "If BWC/WG/9/CRP.1/Rev.7 is shown to be a final adopted Working Group report rather than a revised draft artefact, the document-status interpretation must be corrected.",
        "If the scheduled tenth session is cancelled, materially rescheduled or superseded by an earlier final consensus mechanism, the forward watch point must be updated without rewriting either historical parent snapshot."
    ]
    child["analytical_conclusion"] = (
        "The parent conclusion about the eighth session stands: it advanced negotiating text and achieved procedural consensus without establishing adoption of the substantive final package. "
        "Newly admitted ninth-session evidence changes the follow-through assessment, not that history: later institutional continuation is now observed rather than merely prospective, while the post-session Rev.7 draft identity and still-scheduled tenth session do not establish final consensus."
    )
    child["revision_of_analysis_id"] = PARENT_ID
    child["analysis_revision_kind"] = "NEW_EVIDENCE"
    child["analysis_revision_reason"] = (
        "Admits evidence of the intervening ninth BWC Working Group session and the later Rev.7 draft-final-report identity, which were absent from the parent packet. "
        "This moves second-order follow-through from prospective to observed while preserving the parent eighth-session historical conclusion and unresolved final-consensus boundary."
    )
    return child


def simulate() -> dict[str, Any]:
    plan = load(PLAN_PATH)
    assert_pre_state(plan)
    schema = deepcopy(load(ANALYSIS_SCHEMA_PATH))
    reviews = deepcopy(load(REVIEWS_PATH))
    evidence = deepcopy(load(ANALYSIS_EVIDENCE_PATH))
    canonical = load(CANONICAL_PATH)

    schema["version"] = "0.8"
    schema["reference_date"] = "2026-09-09"
    policy = schema["analysis_revision_policy"]
    policy["mode"] = "CONTROLLED_REVISION_LINEAGE"
    policy["production_analysis_revisions_allowed"] = True
    policy["maximum_production_analysis_revisions"] = 1
    policy["maximum_children_per_revision_parent"] = 1
    guardrail = (
        "CD v0.8 opens the pressure-audited controlled revision lineage to exactly one production Analysis revision; "
        "any second production revision requires another pressure audit and public revision-head collapse remains closed."
    )
    if guardrail not in schema["guardrails"]:
        schema["guardrails"].append(guardrail)

    evidence["version"] = "0.18"
    evidence["reference_date"] = "2026-09-09"
    evidence["evidence"].extend(new_evidence_rows())

    parent = next(r for r in reviews["reviews"] if r["analysis_id"] == PARENT_ID)
    parent_before = deepcopy(parent)
    reviews["version"] = "0.18"
    reviews["reference_date"] = "2026-09-09"
    reviews["reviews"].append(build_child(parent))
    assert next(r for r in reviews["reviews"] if r["analysis_id"] == PARENT_ID) == parent_before

    core = validate_analysis(schema, evidence, reviews, canonical)
    assert core.ok, core.errors
    revision = validate_analysis_revisions(schema, reviews)
    assert revision.ok, revision.errors

    return {"analysis_schema": schema, "reviews": reviews, "evidence": evidence}


def assert_target(plan: dict[str, Any], target: dict[str, Any]) -> None:
    post = plan["target_state"]
    schema = target["analysis_schema"]
    reviews = target["reviews"]
    evidence = target["evidence"]
    from world_signals.checkpoint_contract import version_at_least
    assert version_at_least(schema["version"], post["analysis_schema_version"])
    assert version_at_least(reviews["version"], post["analysis_reviews_version"])
    assert len(reviews["reviews"]) >= post["analysis_review_count"]
    assert version_at_least(evidence["version"], post["analysis_evidence_version"])
    assert len(evidence["evidence"]) >= post["analysis_evidence_count"]
    assert production_analysis_revision_count(reviews) == post["production_analysis_revision_count"]
    assert production_live_input_count(reviews) == post["production_live_input_count"]
    policy = schema["analysis_revision_policy"]
    expected = plan["analysis_revision_policy_target"]
    for key, value in expected.items():
        assert policy.get(key) == value, (key, policy.get(key), value)
    child = next(r for r in reviews["reviews"] if r["analysis_id"] == CHILD_ID)
    assert child["revision_of_analysis_id"] == PARENT_ID
    assert child["analysis_revision_kind"] == "NEW_EVIDENCE"
    assert child["canonical_occurrence_id"] == "WSO-BWC-WG-2026-S08"
    assert child["second_order_effects"]["status"] == "OBSERVED"


def main() -> None:
    plan = load(PLAN_PATH)
    protected_before = {p: stable_hash(ROOT / p) for p in plan["protected_paths"]}
    target = simulate()
    assert_target(plan, target)
    if "--check" in sys.argv:
        protected_after = {p: stable_hash(ROOT / p) for p in plan["protected_paths"]}
        assert protected_after == protected_before
        print("CD_FIRST_ANALYSIS_REVISION_DRY_RUN_PASS")
        return
    write_json(ANALYSIS_SCHEMA_PATH, target["analysis_schema"])
    write_json(REVIEWS_PATH, target["reviews"])
    write_json(ANALYSIS_EVIDENCE_PATH, target["evidence"])
    protected_after = {p: stable_hash(ROOT / p) for p in plan["protected_paths"]}
    assert protected_after == protected_before
    print("CD_FIRST_ANALYSIS_REVISION_MATERIALIZED")


if __name__ == "__main__":
    main()
