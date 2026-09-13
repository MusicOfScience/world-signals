from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
import re
from typing import Any


DATASET = "CROSS_DOMAIN_RISK_OVERLAY_PUBLIC"
LAYER = "DERIVED_READ_ONLY_RISK_LENS_NONCANONICAL"

DOMAIN_DEFINITIONS = (
    {
        "domain_id": "GEOPOLITICAL_GOVERNANCE",
        "label": "Geopolitics and governance",
        "categories": {"ELECTIONS_GOVERNANCE", "INTERNATIONAL_INSTITUTIONS"},
        "channels": {
            "arms_control", "geopolitical_security", "geopolitics", "governance",
            "international_law", "peace_process", "political_governance",
            "political_stability", "politics", "regional_cooperation",
            "regional_governance", "security", "settlement",
        },
    },
    {
        "domain_id": "TRADE_SUPPLY_CHAINS",
        "label": "Trade, sanctions and supply chains",
        "categories": {"TRADE_SANCTIONS_INDUSTRIAL_POLICY"},
        "channels": {
            "agricultural_trade", "industrial_policy", "shipping", "shipping/logistics",
            "shipping_logistics", "supply_chains", "tariffs", "trade",
        },
    },
    {
        "domain_id": "ENERGY_RESOURCES",
        "label": "Energy and strategic resources",
        "categories": {"ENERGY_COMMODITIES"},
        "channels": {
            "clean_energy", "commodities", "energy", "energy_infrastructure",
            "energy_security", "energy_transition", "power_demand", "power_systems",
        },
    },
    {
        "domain_id": "MACRO_MONETARY",
        "label": "Macro and monetary policy",
        "categories": {"MACROECONOMIC_RELEASE", "MONETARY_FINANCIAL_POLICY"},
        "channels": {
            "China_policy", "consumer_demand", "consumption", "economic_policy",
            "growth", "households", "housing", "inflation", "monetary_policy",
            "policy_rates", "prices", "rates",
        },
    },
    {
        "domain_id": "FINANCIAL_SOVEREIGN",
        "label": "Financial and sovereign stress",
        "categories": {
            "CORPORATE_FINANCIAL_MARKET_STRUCTURE", "FINANCIAL_STABILITY_REGULATION",
            "FISCAL_SOVEREIGN_FINANCE",
        },
        "channels": {
            "bank_capital", "banking", "banking_resilience", "credit", "credit_supply",
            "currencies", "currency", "debt", "equities", "expenditure_ceiling",
            "federal_revenue", "finance", "financial_markets", "financial_stability",
            "fiscal_policy", "fiscal_risk", "government_expenditure", "insurance",
            "investment", "liquidity", "market_structure", "nonbank_finance",
            "prudential_regulation", "public_investment", "public_spending",
            "sovereign_bonds", "sovereign_finance", "state_budget", "tax_policy",
            "taxation", "volatility", "yield_curves",
        },
    },
    {
        "domain_id": "HEALTH_BIOSECURITY",
        "label": "Health and biosecurity",
        "categories": {"HEALTH_BIOSECURITY"},
        "channels": {
            "animal_health", "antimicrobial_resistance", "biosecurity", "biotechnology",
            "health", "health_security", "pharmaceuticals", "public_health",
            "veterinary_standards", "zoonotic_risk",
        },
    },
    {
        "domain_id": "CLIMATE_PHYSICAL",
        "label": "Climate and physical risk",
        "categories": {"CLIMATE_ENVIRONMENT", "PHYSICAL_CLIMATE_RISK"},
        "channels": {
            "adaptation", "biodiversity", "carbon_markets", "climate", "climate_policy",
            "land_use", "resource_management", "tourism", "water_resources",
        },
    },
    {
        "domain_id": "TECHNOLOGY_INFRASTRUCTURE",
        "label": "Technology and critical infrastructure",
        "categories": {"TECHNOLOGY_CRITICAL_INFRASTRUCTURE"},
        "channels": {
            "AI", "critical_infrastructure", "cybersecurity", "digital_governance",
            "digital_tax_systems", "dual_use_technology", "essential_services",
            "semiconductors", "technology", "technology_policy",
        },
    },
    {
        "domain_id": "FOOD_AGRICULTURE",
        "label": "Food and agriculture",
        "categories": {"AGRICULTURE_FOOD"},
        "channels": {
            "agriculture_food", "food_security", "food_supply", "livestock",
        },
    },
)

PROHIBITED_OUTPUT_KEYS = {
    "causal_claim", "causal_status", "composite_score", "forecast", "likelihood",
    "probability", "risk_score", "severity_score",
}
EXACT_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _timing_anchor(record: dict) -> tuple[str | None, str]:
    for field in ("start_local", "start_utc"):
        raw = record.get(field)
        candidate = str(raw)[:10] if raw else ""
        if EXACT_DATE.fullmatch(candidate):
            return candidate, field.upper()
    earliest = record.get("date_earliest")
    latest = record.get("date_latest")
    if earliest and earliest == latest and EXACT_DATE.fullmatch(str(earliest)):
        return str(earliest), "EXACT_DATE_WINDOW"
    return None, "NO_EXACT_GREGORIAN_ANCHOR"


def _domain_ids(record: dict) -> list[str]:
    category = record.get("category")
    channels = set(record.get("transmission_channels") or [])
    return [
        definition["domain_id"]
        for definition in DOMAIN_DEFINITIONS
        if category in definition["categories"] or channels.intersection(definition["channels"])
    ]


def _event_row(record: dict) -> dict:
    anchor, anchor_basis = _timing_anchor(record)
    return {
        "occurrence_id": record.get("occurrence_id"),
        "series_id": record.get("series_id"),
        "title": record.get("short_calendar_title") or record.get("canonical_name"),
        "canonical_name": record.get("canonical_name"),
        "category": record.get("category"),
        "region": record.get("region"),
        "jurisdiction": record.get("jurisdiction"),
        "institution": record.get("institution"),
        "certainty_status": record.get("certainty_status"),
        "lifecycle_status": record.get("lifecycle_status"),
        "timing_type": record.get("timing_type"),
        "timing_anchor": anchor,
        "timing_anchor_basis": anchor_basis,
        "start_local": record.get("start_local"),
        "end_local": record.get("end_local"),
        "start_utc": record.get("start_utc"),
        "end_utc": record.get("end_utc"),
        "date_earliest": record.get("date_earliest"),
        "date_latest": record.get("date_latest"),
        "season_window_model": record.get("season_window_model"),
        "source_native_window_label": record.get("source_native_window_label"),
        "season_phases": list(record.get("season_phases") or []),
        "source_native_date_label": record.get("source_native_date_label"),
        "source_timezone": record.get("source_timezone"),
        "intrinsic_importance": record.get("intrinsic_importance"),
        "expected_market_sensitivity": record.get("expected_market_sensitivity"),
        "geopolitical_sensitivity": record.get("geopolitical_sensitivity"),
        "transmission_channels": list(record.get("transmission_channels") or []),
        "risk_domain_ids": _domain_ids(record),
        "source_freshness_risk": record.get("source_freshness_risk"),
    }


def _convergence_windows(events: list[dict]) -> list[dict]:
    weeks: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        if event.get("lifecycle_status") not in {"ACTIVE", "PLANNED"}:
            continue
        anchor = event.get("timing_anchor")
        if not anchor:
            continue
        anchor_date = date.fromisoformat(anchor)
        week_start = anchor_date - timedelta(days=anchor_date.weekday())
        weeks[week_start.isoformat()].append(event)

    rows = []
    for week_start, members in sorted(weeks.items()):
        categories = sorted({event["category"] for event in members if event.get("category")})
        domains = sorted({domain for event in members for domain in event.get("risk_domain_ids") or []})
        if len(members) < 2 or len(categories) < 2 or len(domains) < 2:
            continue
        start = date.fromisoformat(week_start)
        rows.append({
            "window_start": week_start,
            "window_end": (start + timedelta(days=6)).isoformat(),
            "timing_basis": "CALENDAR_WEEK_BUCKET_FROM_EXACT_CANONICAL_START",
            "interpretation": "DENSITY_ONLY_NOT_CAUSAL_OR_PROBABILISTIC",
            "event_count": len(members),
            "occurrence_ids": sorted(event["occurrence_id"] for event in members),
            "canonical_categories": categories,
            "risk_domain_ids": domains,
            "regions": sorted({event["region"] for event in members if event.get("region")}),
            "transmission_channels": sorted({
                channel for event in members for channel in event.get("transmission_channels") or []
            }),
        })
    return rows


def _prohibited_key_hits(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in PROHIBITED_OUTPUT_KEYS:
                hits.append(child_path)
            hits.extend(_prohibited_key_hits(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_prohibited_key_hits(child, f"{path}[{index}]"))
    return hits


def validate_risk_projection(registry: dict, projection: dict) -> list[str]:
    errors: list[str] = []
    if projection.get("dataset") != DATASET:
        errors.append(f"dataset must be {DATASET}")
    if projection.get("layer") != LAYER:
        errors.append(f"layer must be {LAYER}")
    metadata = projection.get("metadata") or {}
    if metadata.get("canonical_registry_version") != registry.get("version"):
        errors.append("canonical registry checkpoint mismatch")
    for field in (
        "canonical_mutation_authorized", "event_population_authorized",
        "live_intelligence_inferred", "analysis_conclusions_inferred",
    ):
        if metadata.get(field) is not False:
            errors.append(f"metadata {field} must be false")

    known = {row.get("occurrence_id"): row for row in registry.get("records", [])}
    domain_ids = {definition["domain_id"] for definition in DOMAIN_DEFINITIONS}
    seen: set[str] = set()
    for event in projection.get("events") or []:
        occurrence_id = event.get("occurrence_id")
        source = known.get(occurrence_id)
        if not source:
            errors.append(f"unknown canonical occurrence {occurrence_id}")
            continue
        if occurrence_id in seen:
            errors.append(f"duplicate risk event {occurrence_id}")
        seen.add(occurrence_id)
        for field in (
            "series_id", "intrinsic_importance", "expected_market_sensitivity",
            "geopolitical_sensitivity", "transmission_channels", "lifecycle_status",
        ):
            if event.get(field) != source.get(field):
                errors.append(f"{occurrence_id} {field} diverges from canonical")
        unknown_domains = set(event.get("risk_domain_ids") or []) - domain_ids
        if unknown_domains:
            errors.append(f"{occurrence_id} has unknown risk domains: {sorted(unknown_domains)}")

    projected_ids = set(seen)
    for window in projection.get("convergence_windows") or []:
        if window.get("interpretation") != "DENSITY_ONLY_NOT_CAUSAL_OR_PROBABILISTIC":
            errors.append("convergence window interpretation must remain density-only")
        unknown = set(window.get("occurrence_ids") or []) - projected_ids
        if unknown:
            errors.append(f"convergence window has unknown occurrences: {sorted(unknown)}")

    hits = _prohibited_key_hits(projection)
    if hits:
        errors.append("prohibited scalar/causal fields present: " + ", ".join(hits))
    return errors


def public_risk_projection(registry: dict) -> dict:
    records = [
        row for row in registry.get("records", [])
        if row.get("render_policy") != "EXCLUDE"
    ]
    events = [_event_row(row) for row in records]
    events.sort(key=lambda row: (row.get("timing_anchor") or "9999-99-99", row.get("title") or ""))
    event_counts = Counter(domain for event in events for domain in event["risk_domain_ids"])
    series_by_domain: dict[str, set[str]] = defaultdict(set)
    for event in events:
        for domain in event["risk_domain_ids"]:
            if event.get("series_id"):
                series_by_domain[domain].add(event["series_id"])

    domains = [
        {
            "domain_id": definition["domain_id"],
            "label": definition["label"],
            "canonical_event_count": event_counts[definition["domain_id"]],
            "canonical_series_count": len(series_by_domain[definition["domain_id"]]),
        }
        for definition in DOMAIN_DEFINITIONS
    ]
    windows = _convergence_windows(events)
    projection = {
        "project": "WORLD SIGNALS",
        "dataset": DATASET,
        "version": "0.1",
        "layer": LAYER,
        "metadata": {
            "canonical_registry_version": registry.get("version"),
            "canonical_reference_date": registry.get("reference_date"),
            "canonical_record_count": len(registry.get("records", [])),
            "projected_event_count": len(events),
            "dated_event_count": sum(event["timing_anchor"] is not None for event in events),
            "undated_event_count": sum(event["timing_anchor"] is None for event in events),
            "expected_date_window_event_count": sum(
                event.get("date_earliest") is not None and event.get("date_latest") is not None
                and event["date_earliest"] != event["date_latest"]
                for event in events
            ),
            "source_native_window_event_count": sum(
                bool(event.get("season_phases")) for event in events
            ),
            "risk_domain_count": len(domains),
            "convergence_window_count": len(windows),
            "canonical_mutation_authorized": False,
            "event_population_authorized": False,
            "live_intelligence_inferred": False,
            "analysis_conclusions_inferred": False,
        },
        "risk_dimensions": [
            {
                "field": "intrinsic_importance",
                "meaning": "Governed importance classification; not event severity.",
            },
            {
                "field": "expected_market_sensitivity",
                "meaning": "Governed sensitivity classification; not a market forecast.",
            },
            {
                "field": "geopolitical_sensitivity",
                "meaning": "Governed sensitivity classification; not conflict likelihood.",
            },
            {
                "field": "transmission_channels",
                "meaning": "Potential channels already recorded in Canonical; not established causality.",
            },
        ],
        "domains": domains,
        "events": events,
        "convergence_windows": windows,
        "boundary_note": (
            "Derived read-only lens over existing Canonical records. It does not estimate probability, "
            "rank danger, assert causality, create events, consume private Live Intelligence, or alter "
            "Canonical, Monitor, Live Intelligence, Analysis, Change Ledger, or OPEC quarantine state."
        ),
    }
    errors = validate_risk_projection(registry, projection)
    if errors:
        raise ValueError("; ".join(errors))
    return projection
