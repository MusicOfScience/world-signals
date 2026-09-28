"""Step 14G candidate-only signposts for the admitted Australian IGR review.

This module assembles a deterministic review artifact from already governed
Analysis material. It does not create monitoring routes, observations,
Forecasts, World State, or production signpost records.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .world_state_history import fingerprint


ANALYSIS_ID = "WSAN-AU-IGR-20260921-001"
REVIEW_AS_OF = "2026-09-28T20:32:40Z"
PROCEDURE = "world-state-step14g-assumption-signposts-v1"
OBSERVATION_TYPES = {
    "LEVEL", "RATE", "TREND", "COMPOSITION", "POLICY_STATE",
    "IMPLEMENTATION_STATE", "MODEL_REVISION", "STRUCTURAL_BREAK_INDICATOR",
}
EVIDENCE_DIRECTIONS = {
    "CONSISTENT_WITH_ASSUMPTION", "IN_TENSION_WITH_ASSUMPTION", "AMBIGUOUS",
    "NOT_COMPARABLE",
}
PRESENT_STATES = EVIDENCE_DIRECTIONS | {"NOT_ENOUGH_EVIDENCE"}
ESCALATIONS = {"OBSERVE", "REVIEW_DUE", "STRUCTURAL_REASSESSMENT_REQUIRED"}


# These definitions operationalise only assumptions for which an observable
# quantity or explicit policy/implementation state can be described. The
# persistence rules are analyst-review gates, not automatic falsification.
_SIGNPOSTS = [
    ("PRODUCTIVITY-CYCLE", "PRODUCTIVITY", "Annual labour productivity growth", "PC_USING_ABS", "RATE", "ABS/PC compatible annual national-accounts vintage", "Quarterly; interpret annual growth as a noisy cycle measure", "One annual print is contextual only; seek at least 12 comparable quarters across three years before routine review", "A sustained three-year underlying divergence, or a material historical/method revision, triggers review; one quarter does not", "Revisions, cycle position, hours/output denominator differences, industry mix and services measurement", ["PC-PRODUCTIVITY2026Q2"], "AMBIGUOUS", "The admitted -0.2% year-to-June-2026 observation is one annual growth measure and does not test a 1.2% long-run convergence assumption."),
    ("PRODUCTIVITY-UNDERLYING", "PRODUCTIVITY", "Underlying labour productivity, MFP, capital deepening and hours/output revisions", "ABS_WITH_PRODUCTIVITY_COMMISSION_CONTEXT", "TREND", "Comparable national-accounts and productivity vintages; separate labour productivity, MFP and capital deepening", "Annual, with quarterly releases retained as components", "At least three years of comparable revised observations; inspect hours/output and services methods separately", "Review if the multi-year underlying path remains materially away from the convergence path or official methods/vintage change", "Revisions, cyclical utilisation, capital quality, industry composition and service-output measurement", ["PC-PRODUCTIVITY2026Q2", "IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "Current admitted evidence lacks a sufficiently long, revision-stable decomposition of MFP, capital deepening and services measurement."),
    ("PRODUCTIVITY-METHOD", "PRODUCTIVITY", "Official productivity measurement or IGR model-vintage revision", "ABS_AND_AU_TREASURY", "MODEL_REVISION", "Compare published methodology and vintage notes; do not splice incompatible series", "Release/event driven", "One confirmed material methodology or model-basis revision is sufficient for analyst review, not for a state conclusion", "Material revision to measurement, source series, or Treasury long-run productivity basis triggers reassessment", "Routine rebasing or benchmark revisions may change historical levels without changing the underlying mechanism", ["IGR2026-MAIN", "PC-PRODUCTIVITY2026Q2"], "NOT_COMPARABLE", "No later admitted methodology or model-vintage revision is present in the bounded evidence."),
    ("FERTILITY-PERIOD", "FERTILITY", "Registered-period TFR and age-specific fertility rates", "ABS", "RATE", "Distinguish registration-year TFR from occurrence-year and age-specific series; comparable ABS vintage", "Annual", "At least three consecutive comparable annual observations can trigger review of period rates, not completed cohort fertility", "Review if low period fertility persists across multiple years and age-specific profiles show no timing catch-up", "Birth registration lag, revisions, postponement and tempo effects", ["ABS-BIRTHS2024", "IGR2026-MAIN"], "AMBIGUOUS", "The admitted 2024 registered-birth TFR is 1.481 births per woman; it is not completed cohort fertility and does not resolve postponement."),
    ("FERTILITY-COHORT", "FERTILITY", "Cohort completed fertility and later-age catch-up", "ABS", "COMPOSITION", "Cohort-by-age fertility profiles through sufficiently mature reproductive ages", "Annual cohort updates; completed cohort comparison is slow-moving", "Require mature cohort evidence and age-specific catch-up analysis; a single period TFR cannot trigger structural reassessment", "Review only when cohort completion indicates persistently lower completed family size rather than delayed timing", "Cohort censoring, migration, registration and compositional effects", ["ABS-BIRTHS2024", "IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "No admitted mature-cohort completed-fertility observation is pinned."),
    ("MIGRATION-FLOW", "MIGRATION", "Annual net overseas migration (NOM)", "ABS", "RATE", "ABS annual NOM definition and revised moving annual totals; compare with 235,000/year technical convention without treating it as a forecast", "Quarterly releases; annual flow assessment", "At least three annual observations under comparable definitions before treating a deviation as durable", "Persistent multi-year deviation or a verified statistical-definition break triggers review; one post-pandemic high year does not", "Moving annual totals, estimate revisions, temporary/permanent mix and policy changes", ["ABS-POP2026Q1", "IGR2026-MAIN"], "IN_TENSION_WITH_ASSUMPTION", "The admitted year-to-March-2026 NOM of 292,100 is above 235,000, but is one moving annual total and not evidence of a durable long-run regime."),
    ("MIGRATION-COMPOSITION", "MIGRATION", "Visa composition, age/skill mix, temporary/permanent balance and absorption constraints", "ABS_AND_AU_TREASURY", "COMPOSITION", "Compare like visa and population categories; separately examine housing/infrastructure capacity evidence", "Annual and policy-event driven", "Several annual comparable cohorts, unless a formal durable policy regime change is enacted", "A durable policy change or persistent composition shift with independently measured absorption constraints triggers review", "Category changes, visa processing, student flows and housing supply lags", ["ABS-POP2026Q1", "IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "The admitted NOM and population snapshots do not establish visa composition, skill mix or absorption constraints."),
    ("PARTICIPATION-DELIVERY", "PARTICIPATION", "Age-sex cohort participation, employment, average hours, underemployment and constraints", "ABS", "COMPOSITION", "Cohort/lifecycle series with employment and hours; separate caring, health/disability and older-worker channels where measured", "Monthly releases as context; annual cohort and hours review", "At least four quarters for short-run context and three annual comparable observations for structural review", "Review if persistent cohort/hours delivery diverges after composition, underemployment and method are considered", "Survey error, population weights, hours mix, underemployment and Supplementary Survey methodology", ["ABS-LABOUR2026M8", "IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "The admitted 67.0% trend participation rate for people 15+ is aggregate and explicitly not comparable to the IGR's structural cohort participation rule."),
    ("AI-ADOPTION", "AI_DIFFUSION", "Business AI adoption, complementary capital, task exposure and organisational re-design", "ABS_OR_REVIEWED_FIRST_PARTY_SERIES_REQUIRED", "COMPOSITION", "Separate adoption, investment, exposure, substitution/reallocation and complementary organisational change", "Annual where representative series exist", "At least three annual evidence sets; adoption alone never validates realised productivity gains", "Review when adoption and complementary investment are measurable and linked to later realised productivity evidence", "Selection bias, self-reporting, task exposure not equal use, displacement and sector composition", ["IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "No admitted representative AI adoption, investment or task-exposure time series is linked to the IGR claim."),
    ("AI-REALISATION", "AI_DIFFUSION", "Measured productivity outcomes associated with AI diffusion", "ABS_WITH_REVIEWED_PRODUCTIVITY_EVIDENCE_REQUIRED", "TREND", "Link measured productivity to adoption/investment while accounting for sector, capital and labour reallocation", "Annual productivity evidence; multi-year horizon", "Multiple years and explicit identification limits; adoption up alone is not evidence that 1.2% is achieved", "Review if sustained realised productivity evidence or a verified model-basis revision materially changes the productivity mechanism", "Attribution, lags, intangible investment, service output and survivor bias", ["PC-PRODUCTIVITY2026Q2", "IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "The single admitted productivity observation is not AI-attributed and cannot validate an AI contribution."),
    ("ENERGY-DELIVERY", "ENERGY_TRANSITION", "Project commitment through approval, construction, connection and observed generation/storage/transmission", "AEMO_DCCEEW_GOVERNED_SERIES_GAP", "IMPLEMENTATION_STATE", "Keep SAID, DECIDED, AUTHORISED, IMPLEMENTED and OBSERVED distinct; connect project identifiers across stages", "Quarterly project pipeline and annual observed system delivery", "A single announcement is not delivery; assess multiple project/system outcomes over several years", "Review if verified delivery or persistent delivery shortfall changes the model's implementation premise; formal policy/system redesign may trigger structural review", "Project cancellations, connection queues, capacity factors, curtailment and transmission bottlenecks", ["IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "No independently governed AEMO/DCCEEW project-to-observed-delivery series is pinned; no monitoring route is created."),
    ("ENERGY-COST-RELIABILITY", "ENERGY_TRANSITION", "Observed generation mix, storage/transmission availability, system costs, reliability and transport-excise erosion", "AEMO_DCCEEW_GOVERNED_SERIES_GAP", "LEVEL", "Source-native operational and fiscal measures with consistent coverage; physical damages remain separately bounded", "Quarterly operations; annual costs and fiscal measures", "Multiple annual outcomes or one verified structural system/policy change; commitments alone do not suffice", "Review if measured cost/reliability or excise-base changes materially alter the IGR pathway; physical climate damage requires its own observed series", "Weather variability, fuel prices, outage mix, system boundaries and partial damage model", ["IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "No admitted independent operational cost/reliability/physical-damage panel is available for this candidate."),
    ("FISCAL-POLICY", "TAX_CEILING", "Enacted tax settings and formal policy changes versus maintained 24.2% of GDP model convention", "AU_TREASURY_MANUAL_ONLY", "POLICY_STATE", "Distinguish technical closure from enacted law, annual Budget decisions and observed receipts", "Budget/event driven", "A verified enacted material policy change can trigger immediate model-basis review; a Budget that merely retains the cap does not validate it", "Structural reassessment if tax-cap basis changes or enacted settings invalidate the maintained convention", "Announcements versus legislation, future offset discretion and cyclical denominator effects", ["IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "The 24.2% ceiling is a maintained policy setting, not perpetual law; no independent current receipts/policy panel is admitted here."),
    ("FISCAL-OUTCOMES", "TAX_CEILING", "Observed tax receipts/GDP, spending, debt and interest-cost paths", "AU_TREASURY_MANUAL_ONLY", "TREND", "Use audited/official fiscal outturns and consistent denominators; separate model convention from realised outcome", "Annual Budget/outturn; quarterly where authoritative", "Several annual outturns before trend review; explicit law or accounting-basis revision can trigger immediate review", "Review on persistent outturn divergence or model-basis change; no inference from one Budget holding a convention", "Nominal GDP revisions, one-off receipts, policy offsets and accounting changes", ["IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "No independent multi-year fiscal outturn panel is pinned to this candidate."),
    ("HEALTH-COST", "HEALTH_COST", "Age-sex adjusted program health spending and non-demographic unit-cost growth", "AIHW_GOVERNED_SERIES_GAP", "TREND", "Separate demographic volume, service mix, price/unit cost and program coverage; compare definitions to IGR method", "Annual", "At least three comparable annual age-adjusted releases; no inference from aggregate spending alone", "Review if persistent comparable unit-cost divergence or model/method revision materially changes extrapolation", "Coverage/rebate changes, program transfer, service mix, demographics and price deflators", ["IGR2026-MAIN"], "NOT_ENOUGH_EVIDENCE", "No independent, age-sex adjusted health-cost panel is included in admitted evidence; AIHW source coverage is a gap, not a route."),
]


_ASSUMPTION_SUMMARIES = {
    "PRODUCTIVITY": ("AMBIGUOUS", "OBSERVE", "The admitted -0.2% annual labour-productivity growth observation for the year to June 2026 is one cyclical/revisable print, not evidence against or confirmation of the 1.2% underlying long-run convention.", "At least 12 comparable quarters across three years for routine structural review; a confirmed material measurement/model revision can trigger earlier review."),
    "FERTILITY": ("NOT_ENOUGH_EVIDENCE", "OBSERVE", "The admitted 2024 registered-period TFR is 1.481 births per woman versus the IGR assumption value 1.34; this numerical difference is not a like-for-like test without aligning period/cohort basis and vintage, and no mature-cohort evidence is admitted.", "Multiple annual age-specific observations plus mature cohort completion/catch-up evidence."),
    "MIGRATION": ("IN_TENSION_WITH_ASSUMPTION", "OBSERVE", "Annual NOM of 292,100 to March 2026 is above the 235,000/year technical convention for this window, but one moving annual total is not a durable long-run regime shift.", "At least three annual comparable observations or a verified durable policy/definition regime change."),
    "PARTICIPATION": ("NOT_ENOUGH_EVIDENCE", "OBSERVE", "The 67.0% trend aggregate for age 15+ is not the IGR's cohort/lifecycle structural rule; hours, age-sex cohorts and underemployment are not fully linked.", "Four quarters for context and three annual comparable cohort/hours observations for structural review."),
    "AI_DIFFUSION": ("NOT_ENOUGH_EVIDENCE", "OBSERVE", "No representative adoption/complementary-capital series or AI-attributed realised productivity evidence is admitted. Adoption alone would not validate productivity.", "Multiple annual adoption/investment observations plus later realised productivity evidence with explicit attribution limits."),
    "ENERGY_TRANSITION": ("NOT_ENOUGH_EVIDENCE", "OBSERVE", "No independently governed project-to-implementation/observed-delivery and cost/reliability series is pinned. Announcements are not implementation or delivered generation.", "Linked project stages and multiple years of observed system outcomes; material formal policy/system redesign may trigger review."),
    "TAX_CEILING": ("NOT_ENOUGH_EVIDENCE", "OBSERVE", "The 24.2% of GDP ceiling is a maintained model policy setting, not enacted perpetual law. No independent multi-year fiscal outturn panel is pinned.", "A verified enacted policy/model-basis change can trigger review immediately; otherwise multiple annual outturns."),
    "HEALTH_COST": ("NOT_ENOUGH_EVIDENCE", "OBSERVE", "The IGR describes an age-sex adjusted cost method, but no independent comparable current cost panel is in the admitted evidence.", "At least three comparable annual age-adjusted unit-cost observations."),
}


_OMITTED = {
    "MORTALITY": "No linked current age-sex mortality/life-table observation is included; the candidate does not create a new demographic monitoring series.",
    "INFLATION": "A short-run inflation series is not operationalised as a signpost for the IGR's maintained long-run target-midpoint convention in this tranche; existing monetary Forecasts remain separate.",
    "COMMODITY_PRICES": "The long-run real-price anchor is a technical convention and no IGR-linked commodity-price observation/vintage comparison is included in the admitted evidence package.",
    "DEBT_YIELDS": "The debt-yield closure is internally coupled and the candidate has no matched current yield path/model comparison suitable for this operational layer.",
    "AGED_CARE_COST": "No independent age-sex adjusted aged-care cost/service-use panel is pinned; keep distinct from broader health cost rather than infer it.",
    "NDIS_REFORMS": "This is a maintained policy/model setting with unresolved implementation and short scheme history; no linked reviewed NDIS outturn series is included.",
    "RETIREMENT": "The microsimulation assumption needs cohort/wealth/means-testing evidence not represented in the admitted observed-evidence set.",
}


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def build_candidate(root: Path, *, reviews_dataset: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build from current admitted IGR data; fail if identity/epistemics drift."""
    dataset = deepcopy(reviews_dataset) if reviews_dataset is not None else _read_json(root, "data/analysis/event_reviews.json")
    transaction = _read_json(root, "data/analysis/STEP14F_AU_IGR_INTERNAL_ANALYSIS_ADMISSION_TRANSACTION.json")
    review = next((row for row in dataset["reviews"] if row.get("analysis_id") == ANALYSIS_ID), None)
    if review is None or review.get("review_state") != "REVIEWED":
        raise ValueError("admitted REVIEWED IGR Analysis is required")
    if fingerprint(review) != transaction.get("production_review_sha256"):
        raise ValueError("admitted Analysis hash differs from Step 14F transaction")
    if dataset.get("publication_decisions", {}).get(ANALYSIS_ID) != "INTERNAL_ONLY":
        raise ValueError("IGR Analysis must remain INTERNAL_ONLY")
    extension = review.get("official_projection_review")
    if not isinstance(extension, dict) or extension.get("visibility") != "INTERNAL_ONLY":
        raise ValueError("internal official_projection_review required")
    if fingerprint(extension) != transaction.get("internal_extension_sha256"):
        raise ValueError("official-projection extension hash differs from Step 14F transaction")
    assumptions = {row["assumption_id"]: row for row in extension["model_assumptions"]}
    selected_keys = {row[1] for row in _SIGNPOSTS}
    assumption_by_suffix = {key.rsplit("-", 1)[-1]: value for key, value in assumptions.items()}
    if not selected_keys <= set(assumption_by_suffix):
        raise ValueError("selected IGR assumptions must resolve in admitted Analysis")
    observed = {row["observation_candidate_id"]: row for row in extension.get("observed_evidence", [])}
    assets = {row["asset_id"]: row for row in extension["source_manifest"]}

    sources: list[dict[str, Any]] = [
        {"source_id": f"ANALYSIS:{ANALYSIS_ID}", "layer": "ANALYSIS", "object_id": ANALYSIS_ID,
         "revision_id": None, "object_sha256": transaction["production_review_sha256"], "epistemic_class": "REVIEWED_ANALYSIS"},
        {"source_id": "ANALYSIS_EXTENSION:" + ANALYSIS_ID, "layer": "ANALYSIS", "object_id": ANALYSIS_ID + ":official_projection_review",
         "revision_id": None, "object_sha256": transaction["internal_extension_sha256"], "epistemic_class": "MODEL_ASSUMPTIONS_AND_OFFICIAL_PROJECTIONS"},
    ]
    for asset_id, asset in sorted(assets.items()):
        sources.append({"source_id": asset_id, "layer": "ANALYSIS_SOURCE_ASSET", "object_id": asset_id,
                        "revision_id": asset.get("vintage"), "object_sha256": asset["sha256"],
                        "epistemic_class": asset["source_class"], "source_family": asset["source_family"]})
    for obs_id, obs in sorted(observed.items()):
        sources.append({"source_id": obs_id, "layer": "ANALYSIS_OBSERVED_EVIDENCE", "object_id": obs_id,
                        "revision_id": obs.get("reference_period"), "object_sha256": fingerprint(obs),
                        "epistemic_class": obs["epistemic_class"]})
    source_by_id = {row["source_id"]: row for row in sources}

    signposts = []
    for ordinal, item in enumerate(_SIGNPOSTS, 1):
        suffix, key, metric, family, observation_type, basis, frequency, persistence, structural, risks, refs, direction, state_note = item
        if direction == "NOT_ENOUGH_EVIDENCE":
            direction = "NOT_COMPARABLE"
        assumption = assumption_by_suffix.get(key)
        if assumption is None:
            raise ValueError(f"missing assumption: {key}")
        source_refs = [{"source_id": ref, "locator": f"{ref}: admitted IGR source/evidence"} for ref in refs]
        for ref in refs:
            if ref not in source_by_id:
                raise ValueError(f"signpost references unavailable source {ref}")
        signposts.append({
            "signpost_id": f"WSIGN-AU-IGR-{ordinal:02d}-{suffix}",
            "assumption_id": assumption["assumption_id"],
            "metric_or_observation": metric,
            "source_family": family,
            "observation_type": observation_type,
            "comparison_basis": basis,
            "observation_frequency": frequency,
            "minimum_persistence": persistence,
            "direction_of_evidence": direction,
            "structural_break_condition": structural,
            "review_trigger": f"Request analyst review only if this condition is evidenced: {structural}. It cannot itself falsify the long-horizon assumption or promote another layer.",
            "false_positive_risks": risks,
            "source_refs": source_refs,
            "limitations": [state_note, "No probability, score, ranking, or automatic disposition is produced."],
            "present_evidence_state": direction,
        })

    summaries = []
    for key in sorted(selected_keys):
        assumption = assumption_by_suffix[key]
        state, escalation, rationale, minimum = _ASSUMPTION_SUMMARIES[key]
        ev_refs = []
        for obs in observed.values():
            if any(ref["asset_id"] in {s["source_id"] for s in sources} for ref in obs.get("source_refs", [])):
                if key in {"FERTILITY", "MIGRATION", "PARTICIPATION", "PRODUCTIVITY"}:
                    # Exact mapping is intentionally explicit, not domain/name inferred.
                    allowed = {"FERTILITY": {"WSOBAUD-TFR2024"}, "MIGRATION": {"WSOBAUD-NOM2026Q1", "WSOBAUD-POP2026Q1"},
                               "PARTICIPATION": {"WSOBAUD-LF2026M8"}, "PRODUCTIVITY": {"WSOBAUD-PRODUCTIVITY2026Q2"}}[key]
                    if obs["observation_candidate_id"] in allowed:
                        ev_refs.append(obs["observation_candidate_id"])
        summaries.append({"assumption_id": assumption["assumption_id"], "assumption_statement": assumption["statement"],
                          "assumption_value_or_rule": assumption["value_or_rule"], "present_evidence_state": state,
                          "review_workflow_state": escalation, "current_signpost_evidence": sorted(ev_refs),
                          "why": rationale, "minimum_evidence_to_change_state": minimum,
                          "next_useful_observation": next(row["metric_or_observation"] for row in signposts if row["assumption_id"] == assumption["assumption_id"]),
                          "limitation": "Present evidence relationship only; not a probability, Forecast, falsification, or World State assessment."})

    source_gaps = [
        {"assumption_id": "WSASM-AU-IGR-2026-PRODUCTIVITY", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Revision-stable multi-year decomposition of labour productivity, MFP, capital deepening, hours/output and service measurement.", "route_created": False},
        {"assumption_id": "WSASM-AU-IGR-2026-FERTILITY", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Age-specific and mature-cohort completed-fertility series capable of distinguishing postponement from lower completed family size.", "route_created": False},
        {"assumption_id": "WSASM-AU-IGR-2026-MIGRATION", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Several comparable annual NOM observations plus visa, age/skill and temporary/permanent composition and absorption context.", "route_created": False},
        {"assumption_id": "WSASM-AU-IGR-2026-PARTICIPATION", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Comparable age-sex cohort participation linked to employment, average hours, underemployment and relevant constraints.", "route_created": False},
        {"assumption_id": "WSASM-AU-IGR-2026-AI_DIFFUSION", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Representative business adoption, complementary investment and task/reallocation series linked to measured productivity.", "route_created": False},
        {"assumption_id": "WSASM-AU-IGR-2026-ENERGY_TRANSITION", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Governed project-stage, grid connection, generation/storage/transmission, system cost and reliability observations from suitable first-party families.", "route_created": False},
        {"assumption_id": "WSASM-AU-IGR-2026-HEALTH_COST", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Comparable age-sex adjusted health program cost and non-demographic unit-cost series.", "route_created": False},
        {"assumption_id": "WSASM-AU-IGR-2026-TAX_CEILING", "gap_code": "SOURCE_COVERAGE_GAP", "needed": "Multi-year fiscal outturns and authoritative enacted-policy references distinguished from the maintained 24.2% convention.", "route_created": False},
    ]
    candidate = {
        "contract": "WORLD_SIGNALS_ASSUMPTION_SIGNPOST_CANDIDATE",
        "contract_version": "0.1",
        "status": "REVIEW_PENDING",
        "classification": "CANDIDATE_ONLY_NOT_PRODUCTION",
        "analysis_id": ANALYSIS_ID,
        "analysis_review_state": "REVIEWED",
        "analysis_visibility": "INTERNAL_ONLY",
        "candidate_as_of_utc": REVIEW_AS_OF,
        "analysis_content_as_of_utc": review.get("analysis_as_of_utc"),
        "historical_backtest_disposition": "DEFERRED",
        "procedure": {"procedure_id": PROCEDURE, "version": "1", "model_output_is_factual_evidence": False},
        "bounded_current_evidence": deepcopy(list(observed.values())),
        "selected_assumptions": summaries,
        "omitted_assumptions": [{"assumption_id": assumption_by_suffix[key]["assumption_id"], "reason": reason} for key, reason in _OMITTED.items()],
        "signposts": signposts,
        "source_coverage_gaps": source_gaps,
        "workflow_policy": {"states": sorted(ESCALATIONS), "ranking_permitted": False, "score_permitted": False,
                            "probability_permitted": False, "automatic_falsification": False,
                            "automatic_analysis_revision": False, "automatic_world_state_mutation": False,
                            "source_automation_activation": False,
                            "bridge": ["new governed observation", "signpost evaluation", "assumption review", "analyst reassessment", "separately reviewed Analysis revision if warranted"]},
        "prohibited_promotions": ["FORECAST", "SCENARIO", "SIGNAL", "RELATIONSHIP", "RISK", "WORLD_STATE", "OUTCOME", "ANALYSIS_REVISION", "PUBLIC_PROJECTION"],
        "source_manifest": sources,
        "source_manifest_sha256": fingerprint(sources),
        "limitations": [
            "Evidence is bounded to the admitted internal IGR Analysis package available at the stated cutoff; no external research or new OSINT sweep was performed.",
            "The official IGR is a long-horizon conditional model, not a WORLD SIGNALS Forecast; present short-run movement is not long-horizon falsification.",
            "Some signposts identify useful source families without governed, linked series. These are explicit coverage gaps, not monitoring routes.",
            "Escalation states control analyst attention only and do not represent severity, confidence, or truth.",
            "Independent historical backtest remains DEFERRED; no disposition is changed here.",
            "All current classifications are review-pending candidate judgments and do not alter production Analysis or downstream layers.",
        ],
        "write_targets": [],
        "public_projection_permitted": False,
    }
    candidate["semantic_fingerprint"] = fingerprint(candidate)
    validate_candidate(candidate)
    return candidate


def validate_candidate(candidate: dict[str, Any]) -> tuple[str, ...]:
    """Strict validator for the Step 14G retained candidate, not production schema."""
    errors: list[str] = []
    try:
        json.dumps(candidate, allow_nan=False)
    except (TypeError, ValueError):
        return ("candidate must be finite JSON",)
    if candidate.get("contract") != "WORLD_SIGNALS_ASSUMPTION_SIGNPOST_CANDIDATE" or candidate.get("status") != "REVIEW_PENDING":
        errors.append("candidate identity/status must remain review-pending")
    if candidate.get("classification") != "CANDIDATE_ONLY_NOT_PRODUCTION":
        errors.append("candidate-only classification required")
    if candidate.get("analysis_visibility") != "INTERNAL_ONLY" or candidate.get("public_projection_permitted") is not False:
        errors.append("internal-only publication boundary required")
    if candidate.get("write_targets") != []:
        errors.append("candidate must have no write targets")
    sources = candidate.get("source_manifest")
    if not isinstance(sources, list) or not sources or candidate.get("source_manifest_sha256") != fingerprint(sources):
        errors.append("source manifest fingerprint mismatch")
        sources = []
    source_ids = [row.get("source_id") for row in sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("duplicate source manifest identity")
    for row in sources:
        if not isinstance(row.get("object_sha256"), str) or len(row["object_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["object_sha256"]):
            errors.append("source manifest object hash required")
    selected = candidate.get("selected_assumptions", [])
    assumptions = {row.get("assumption_id") for row in selected}
    if not selected or len(assumptions) != len(selected):
        errors.append("selected assumption identities must be nonempty and unique")
    signposts = candidate.get("signposts", [])
    ids = [row.get("signpost_id") for row in signposts]
    if not signposts or len(ids) != len(set(ids)):
        errors.append("signpost identities must be nonempty and unique")
    for row in signposts:
        if row.get("assumption_id") not in assumptions:
            errors.append("signpost assumption reference does not resolve")
        for field in ("metric_or_observation", "source_family", "comparison_basis", "observation_frequency",
                      "minimum_persistence", "structural_break_condition", "review_trigger"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{field} is required")
        if row.get("observation_type") not in OBSERVATION_TYPES:
            errors.append("invalid observation type")
        if row.get("direction_of_evidence") not in EVIDENCE_DIRECTIONS:
            errors.append("invalid evidence direction")
        refs = row.get("source_refs")
        if not refs or any(ref.get("source_id") not in source_ids or not isinstance(ref.get("locator"), str) or not ref["locator"].strip() for ref in refs):
            errors.append("signpost source reference does not resolve")
        if not row.get("false_positive_risks") or not row.get("limitations"):
            errors.append("false-positive risks and limitations required")
    for summary in selected:
        if summary.get("review_workflow_state") not in ESCALATIONS:
            errors.append("invalid analyst review escalation")
        if summary.get("present_evidence_state") not in PRESENT_STATES:
            errors.append("invalid present evidence state")
    if candidate.get("historical_backtest_disposition") != "DEFERRED":
        errors.append("independent historical backtest disposition must remain DEFERRED")
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key in value:
                normalized = str(key).lower().replace("-", "_")
                tokens = set(normalized.split("_"))
                if "permitted" not in tokens and tokens & {"score", "probability", "rank", "ranking"}:
                    errors.append("scores, probabilities and ranking are prohibited")
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(candidate)
    expected = fingerprint({key: value for key, value in candidate.items() if key != "semantic_fingerprint"})
    if candidate.get("semantic_fingerprint") != expected:
        errors.append("semantic fingerprint mismatch")
    return tuple(dict.fromkeys(errors))


def render_summary(candidate: dict[str, Any]) -> str:
    """Deterministic human-readable summary of the exact candidate object."""
    lines = [
        "# Step 14G — IGR assumption signposts (review pending)", "",
        f"Candidate: `{candidate['semantic_fingerprint']}`",
        f"Evidence cutoff: `{candidate['candidate_as_of_utc']}`",
        f"Analysis: `{candidate['analysis_id']}` — `{candidate['analysis_visibility']}`", "",
        "This is candidate-only analyst-review material. It does not falsify the IGR, create a WORLD SIGNALS Forecast, or assess World State.", "",
        "## Present evidence assessments", "",
        "| Assumption | Evidence relationship | Workflow | Current basis |", "|---|---|---|---|",
    ]
    for row in candidate["selected_assumptions"]:
        lines.append(f"| `{row['assumption_id']}` | {row['present_evidence_state']} | {row['review_workflow_state']} | {row['why']} |")
    lines += ["", "## Coverage gaps", ""]
    for gap in candidate["source_coverage_gaps"]:
        lines.append(f"- `{gap['assumption_id']}` — {gap['needed']} No source route created.")
    lines += ["", "## Limits", ""]
    lines.extend(f"- {item}" for item in candidate["limitations"])
    lines += ["", "No production write targets. Public projection is prohibited. Independent historical backtest remains DEFERRED.", ""]
    return "\n".join(lines)


def candidate_json(candidate: dict[str, Any]) -> str:
    return json.dumps(candidate, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
