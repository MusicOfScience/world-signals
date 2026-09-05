#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
AUDIT_PATH = ROOT / "data/analysis/PRIORITY_REGION_ANALYSIS_S_TRANSACTION_AUDIT_v0.1.md"

PRE = {
    "canonical_version": "0.29",
    "canonical_count": 678,
    "schema_version": "0.2",
    "reviews_version": "0.2",
    "review_count": 2,
    "evidence_version": "0.2",
    "evidence_count": 5,
}
POST = {
    "reviews_version": "0.3",
    "review_count": 6,
    "evidence_version": "0.3",
    "evidence_count": 14,
    "readiness": "READY_FOR_CONTROLLED_EXPANSION",
}

NEW_ANALYSIS_IDS = {
    "WSAN-IN-GDP-2026Q1-001",
    "WSAN-ID-BI-202608-001",
    "WSAN-EG-CBE-20260820-001",
    "WSAN-AR-CPI-202607-001",
}
NEW_EVIDENCE_IDS = {
    "WSEV-IN-GDP-PIB-20260831",
    "WSEV-IN-GDP-REUTERS-20260831",
    "WSEV-IN-GDP-REUTERS-20260901",
    "WSEV-ID-BI-BI-20260819",
    "WSEV-ID-BI-REUTERS-20260819",
    "WSEV-EG-CBE-CBE-20260820",
    "WSEV-EG-CBE-HC-20260819",
    "WSEV-AR-CPI-INDEC-20260813",
    "WSEV-AR-CPI-REUTERS-20260813",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upstream_hashes() -> dict[str, str]:
    return {
        "canonical": file_hash(CANONICAL_PATH),
        "canonical_schema": file_hash(CANONICAL_SCHEMA_PATH),
        "sources": file_hash(SOURCES_PATH),
        "ledger": file_hash(LEDGER_PATH),
        "overlay": file_hash(OVERLAY_PATH),
        "expectations": file_hash(EXPECTATIONS_PATH),
        "operations": file_hash(OPERATIONS_PATH),
        "analysis_schema": file_hash(ANALYSIS_SCHEMA_PATH),
    }


def evidence_rows() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "WSEV-IN-GDP-PIB-20260831",
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "Ministry of Statistics & Programme Implementation / Press Information Bureau",
            "host_or_distribution": "Press Information Bureau, Government of India",
            "title": "Quarterly Estimates of Gross Domestic Product for the First Quarter (April-June) of 2026-27",
            "url": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2304949&lang=1&reg=48",
            "published_at": "2026-08-31T16:00:00+05:30",
            "roles": ["OFFICIAL_OUTCOME"],
            "supports": [
                "Real GDP grew 7.8 percent year-on-year in Q1 FY2026-27.",
                "The release was posted at 4:00 PM India time on 31 August 2026.",
            ],
            "analytical_use": "FACTUAL_METADATA_AND_SHORT_PARAPHRASE",
            "canonical_provenance_effect": "NONE",
        },
        {
            "evidence_id": "WSEV-IN-GDP-REUTERS-20260831",
            "evidence_class": "REPUTABLE_NEWSWIRE",
            "provider": "Reuters",
            "host_or_distribution": "Reuters",
            "title": "India smashes growth forecasts as investment surges in April-June",
            "url": "https://www.reuters.com/business/indias-gdp-grows-78-april-june-2026-08-31/",
            "published_at": "2026-08-31",
            "roles": ["EXPECTATION_BENCHMARK", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "Reuters reported Q1 FY2026-27 real GDP growth of 7.8 percent year-on-year against economists' projections of 7.1 percent.",
                "The article identifies high oil prices and geopolitical uncertainty as external risks around the growth outlook.",
            ],
            "analytical_use": "LINK_AND_FACTUAL_PARAPHRASE_ONLY",
            "canonical_provenance_effect": "NONE",
        },
        {
            "evidence_id": "WSEV-IN-GDP-REUTERS-20260901",
            "evidence_class": "REPUTABLE_NEWSWIRE",
            "provider": "Reuters",
            "host_or_distribution": "Reuters",
            "title": "RBI intervention, dollar flows push Indian rupee to two-month peak",
            "url": "https://www.reuters.com/business/rbi-intervention-dollar-flows-push-indian-rupee-two-month-peak-2026-09-01/",
            "published_at": "2026-09-01T11:33:32Z",
            "roles": ["MARKET_OBSERVATION", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "The rupee ended at 94.9500 INR per USD, 0.2 percent stronger than the previous close.",
                "Reuters identified RBI dollar-selling intervention and flow-related dollar supply from foreign banks as the principal immediate drivers.",
                "Reuters also reported that the previous day's strong growth data improved sentiment toward the rupee.",
                "Higher global yields, higher oil prices and renewed US-Iran tensions were simultaneous external headwinds.",
            ],
            "analytical_use": "LINK_AND_FACTUAL_PARAPHRASE_ONLY",
            "canonical_provenance_effect": "NONE",
        },
        {
            "evidence_id": "WSEV-ID-BI-BI-20260819",
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "Bank Indonesia",
            "host_or_distribution": "Bank Indonesia",
            "title": "BI-Rate Held at 5.75%: Strengthening Stability, Supporting Economic Growth",
            "url": "https://www.bi.go.id/en/publikasi/ruang-media/news-release/Pages/sp_2816226.aspx",
            "published_at": "2026-08-19T18:00:00+07:00",
            "roles": ["OFFICIAL_OUTCOME", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "The 18-19 August 2026 Board of Governors Meeting held BI-Rate at 5.75 percent.",
                "The Deposit Facility rate remained 4.75 percent and the Lending Facility rate 6.50 percent.",
                "BI explicitly cited rupiah stability amid heightened global volatility and the Middle East war, inflation within target and sustainable growth.",
            ],
            "analytical_use": "FACTUAL_METADATA_AND_SHORT_PARAPHRASE",
            "canonical_provenance_effect": "NONE",
        },
        {
            "evidence_id": "WSEV-ID-BI-REUTERS-20260819",
            "evidence_class": "REPUTABLE_NEWSWIRE",
            "provider": "Reuters",
            "host_or_distribution": "Kontan syndication",
            "title": "Indonesia Central Bank Holds Rates Steady at 5.75%, as Expected",
            "url": "https://english.kontan.co.id/news/indonesia-central-bank-holds-rates-steady-at-575-as-expected",
            "published_at": "2026-08-19T14:38:00+07:00",
            "roles": ["EXPECTATION_BENCHMARK", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "All but one of 28 economists polled by Reuters expected BI to hold the benchmark rate at 5.75 percent.",
                "The decision was the first rate-setting meeting under interim governor Destry Damayanti after the prior governor's resignation.",
            ],
            "analytical_use": "LINK_AND_FACTUAL_PARAPHRASE_ONLY",
            "canonical_provenance_effect": "NONE",
            "distribution_note": "The Kontan page identifies Reuters as source. It is analytical evidence only and not canonical event provenance.",
        },
        {
            "evidence_id": "WSEV-EG-CBE-CBE-20260820",
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "Central Bank of Egypt",
            "host_or_distribution": "Central Bank of Egypt",
            "title": "MPC Press Release 20 August 2026",
            "url": "https://www.cbe.org.eg/en/news-publications/news/2026/08/20/15/17/mpc-press-release-20-august-2026",
            "published_at": "2026-08-20",
            "roles": ["OFFICIAL_OUTCOME", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "The overnight deposit rate remained 19.00 percent and overnight lending rate 20.00 percent.",
                "The main-operation and discount rates remained 19.50 percent.",
                "Monthly headline and core inflation were 0.0 percent in July and below expectations.",
                "CBE retained upside-risk warnings around regional hostilities and fiscal-consolidation pass-through.",
            ],
            "analytical_use": "FACTUAL_METADATA_AND_SHORT_PARAPHRASE",
            "canonical_provenance_effect": "NONE",
        },
        {
            "evidence_id": "WSEV-EG-CBE-HC-20260819",
            "evidence_class": "OTHER_REVIEWED",
            "provider": "HC Securities & Investment",
            "host_or_distribution": "HC Securities & Investment",
            "title": "HC expects the MPC to hold interest rates at its 20 August meeting",
            "url": "https://www.hc-si.com/hc-expects-the-mpc-to-hold-interest-rates-at-its-20-august-meeting",
            "published_at": "2026-08-19",
            "roles": ["EXPECTATION_BENCHMARK", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "HC Securities expected the CBE MPC to keep interest rates unchanged at its 20 August meeting.",
                "Its rationale included accelerated inflation pressure and higher energy costs alongside a comparatively resilient external position.",
            ],
            "analytical_use": "LINK_AND_FACTUAL_PARAPHRASE_ONLY",
            "canonical_provenance_effect": "NONE",
        },
        {
            "evidence_id": "WSEV-AR-CPI-INDEC-20260813",
            "evidence_class": "PRIMARY_OFFICIAL",
            "provider": "INDEC",
            "host_or_distribution": "INDEC",
            "title": "Índice de precios al consumidor — July 2026 technical report surface",
            "url": "https://www.indec.gob.ar/Nivel4/Tema/3/5/31",
            "published_at": "2026-08-13",
            "roles": ["OFFICIAL_OUTCOME"],
            "supports": [
                "Historical first-party verification in tranche R recorded the 13 August 2026 July CPI technical report and a 2.1 percent month-on-month national CPI increase.",
                "The INDEC URL is a rolling official publication surface; this analytical citation does not replace canonical R provenance.",
            ],
            "analytical_use": "FACTUAL_METADATA_AND_SHORT_PARAPHRASE",
            "canonical_provenance_effect": "NONE",
            "distribution_note": "Rolling first-party publication surface. The canonical R assertion preserves the historical occurrence verification independently of this analytical record.",
        },
        {
            "evidence_id": "WSEV-AR-CPI-REUTERS-20260813",
            "evidence_class": "REPUTABLE_NEWSWIRE",
            "provider": "Reuters",
            "host_or_distribution": "Reuters",
            "title": "Argentina monthly inflation rises in July to 2.1%",
            "url": "https://www.reuters.com/world/americas/argentina-monthly-inflation-rises-july-21-2026-08-13/",
            "published_at": "2026-08-13T19:20:07Z",
            "roles": ["EXPECTATION_BENCHMARK", "CONTEXT_OR_ALTERNATIVE"],
            "supports": [
                "July CPI rose 2.1 percent month-on-month versus analyst expectations of 2.0 percent.",
                "June CPI had been 1.9 percent and year-on-year CPI rose to 33.8 percent from 33.5 percent.",
                "Recreation and culture recorded the largest price increases, driven by winter-holiday packages, followed by restaurants and hotels.",
            ],
            "analytical_use": "LINK_AND_FACTUAL_PARAPHRASE_ONLY",
            "canonical_provenance_effect": "NONE",
        },
    ]


def review_rows() -> list[dict[str, Any]]:
    as_of = "2026-09-05T15:31:00Z"
    return [
        {
            "analysis_id": "WSAN-IN-GDP-2026Q1-001",
            "review_state": "REVIEWED_SAMPLE",
            "review_phase": "POST_EVENT",
            "analysis_as_of_utc": as_of,
            "canonical_occurrence_id": "WSO-HIST-R-IN-GDP-2026Q1",
            "canonical_series_id": "WSER-MAC-IN-GDP",
            "canonical_event_type": "DATA_RELEASE",
            "canonical_institution": "Ministry of Statistics and Programme Implementation",
            "canonical_release_utc": "2026-08-31T10:30:00Z",
            "scope": "Q1 FY2026-27 India GDP release, consensus surprise and next-session rupee observation with intervention and flow contamination preserved",
            "what_happened": {
                "summary": "India's official Q1 FY2026-27 GDP release reported real GDP growth of 7.8 percent year-on-year.",
                "actuals": [
                    {
                        "metric": "real_gdp_yoy",
                        "value": 7.8,
                        "unit": "percent",
                        "evidence_refs": ["WSEV-IN-GDP-PIB-20260831"],
                    }
                ],
                "evidence_refs": ["WSEV-IN-GDP-PIB-20260831"],
            },
            "what_was_expected": {
                "summary": "Reuters reported economists' projections of 7.1 percent year-on-year growth.",
                "benchmarks": [
                    {
                        "metric": "real_gdp_yoy",
                        "value": 7.1,
                        "unit": "percent",
                        "benchmark_type": "MARKET_FORECAST",
                        "evidence_refs": ["WSEV-IN-GDP-REUTERS-20260831"],
                    }
                ],
                "evidence_refs": ["WSEV-IN-GDP-REUTERS-20260831"],
            },
            "what_surprised": {
                "status": "UPSIDE",
                "summary": "Real GDP growth exceeded the cited economist forecast by 0.7 percentage points. This is a data surprise, not a claim that the release dominated subsequent asset pricing.",
                "comparisons": [
                    {
                        "comparison_kind": "QUANTITATIVE",
                        "metric": "real_gdp_yoy",
                        "actual": 7.8,
                        "expected": 7.1,
                        "difference_percentage_points": 0.7,
                    }
                ],
                "evidence_refs": [
                    "WSEV-IN-GDP-PIB-20260831",
                    "WSEV-IN-GDP-REUTERS-20260831",
                ],
            },
            "what_moved": [
                {
                    "movement_id": "WSMV-IN-GDP-20260901-INRUSD",
                    "movement_type": "FX_SPOT",
                    "movement_representation": "CHANGE_AND_ENDPOINT",
                    "instrument_or_measure": "Indian rupee versus US dollar",
                    "before_value": None,
                    "after_value": 94.95,
                    "unit": "INR_per_USD",
                    "change": 0.2,
                    "change_unit": "percent_rupee_appreciation",
                    "direction": "INR_STRONGER",
                    "measurement_window": "Reuters-reported 1 September 2026 close versus the previous close, one session after the GDP release",
                    "measurement_precision": "SOURCE_REPORTED_CHANGE_AND_ENDPOINT",
                    "independently_reconstructed": False,
                    "evidence_refs": ["WSEV-IN-GDP-REUTERS-20260901"],
                }
            ],
            "what_appears_connected": {
                "interaction_type": "OBSERVATION_CONTEXT",
                "causal_status": "OBSERVED_ASSOCIATION",
                "confidence": "LOW",
                "summary": "Reuters reported that the previous day's strong growth data improved sentiment toward the rupee, so a supportive association is observable. The same report identified RBI intervention and flow-related dollar supply as the principal immediate drivers; GDP is therefore not promoted as the dominant cause.",
                "evidence_refs": [
                    "WSEV-IN-GDP-REUTERS-20260831",
                    "WSEV-IN-GDP-REUTERS-20260901",
                ],
            },
            "what_may_be_noise": [
                {
                    "summary": "The rupee move occurred against a global bond sell-off, higher oil prices and renewed US-Iran tensions, all of which could independently affect the currency.",
                    "evidence_refs": ["WSEV-IN-GDP-REUTERS-20260901"],
                }
            ],
            "alternative_explanations": [
                {
                    "summary": "RBI dollar-selling intervention was identified by Reuters as a principal immediate driver of rupee strength.",
                    "evidence_refs": ["WSEV-IN-GDP-REUTERS-20260901"],
                },
                {
                    "summary": "Flow-related dollar supply from foreign banks and infrastructure-fund inflows also supported the rupee independently of the GDP surprise.",
                    "evidence_refs": ["WSEV-IN-GDP-REUTERS-20260901"],
                },
            ],
            "second_order_effects": {
                "status": "NOT_ESTABLISHED",
                "summary": "No distinct second-order policy, trade, investment or political outcome is established in this packet. The stronger GDP print may alter subsequent forecasts, but that remains a watch item until separately observed and evidenced.",
            },
            "falsifiers": [
                "If higher-frequency evidence shows rupee strengthening materially preceded publication of the GDP result, the GDP-linked association should be weakened.",
                "If RBI intervention and identified flow effects fully explain the move without a measurable post-data component, the GDP connection should be downgraded to observation context only.",
                "If later contemporaneous evidence identifies another dominant domestic catalyst, connection confidence should remain low or be reduced further.",
            ],
            "analytical_conclusion": "India's Q1 GDP beat the cited consensus by 0.7 percentage points. The next-session rupee strengthening is analytically relevant only as a low-confidence association: Reuters explicitly identified central-bank intervention and dollar flows as stronger immediate drivers while describing the GDP beat as supportive sentiment.",
            "canonical_mutation_prohibited": True,
            "google_calendar_write": False,
        },
        {
            "analysis_id": "WSAN-ID-BI-202608-001",
            "review_state": "REVIEWED_SAMPLE",
            "review_phase": "POST_EVENT",
            "analysis_as_of_utc": as_of,
            "canonical_occurrence_id": "WSO-HIST-R-ID-BI-202608",
            "canonical_series_id": "WSER-REG-ID-BI",
            "canonical_event_type": "MONETARY_POLICY_DECISION_PROCESS",
            "canonical_institution": "Bank Indonesia",
            "canonical_release_utc": None,
            "scope": "18-19 August 2026 Bank Indonesia Board of Governors decision process and evidence-backed expectation comparison",
            "what_happened": {
                "summary": "Bank Indonesia held BI-Rate at 5.75 percent, the Deposit Facility rate at 4.75 percent and the Lending Facility rate at 6.50 percent.",
                "actuals": [
                    {"metric": "bi_rate", "value": 5.75, "unit": "percent", "evidence_refs": ["WSEV-ID-BI-BI-20260819"]},
                    {"metric": "deposit_facility_rate", "value": 4.75, "unit": "percent", "evidence_refs": ["WSEV-ID-BI-BI-20260819"]},
                    {"metric": "lending_facility_rate", "value": 6.5, "unit": "percent", "evidence_refs": ["WSEV-ID-BI-BI-20260819"]},
                ],
                "evidence_refs": ["WSEV-ID-BI-BI-20260819"],
            },
            "what_was_expected": {
                "summary": "Reuters reported that 27 of 28 economists expected BI to hold the benchmark rate at 5.75 percent.",
                "benchmarks": [
                    {
                        "metric": "bi_rate",
                        "value": 5.75,
                        "unit": "percent",
                        "benchmark_type": "MARKET_CONSENSUS_DECISION",
                        "evidence_refs": ["WSEV-ID-BI-REUTERS-20260819"],
                    }
                ],
                "evidence_refs": ["WSEV-ID-BI-REUTERS-20260819"],
            },
            "what_surprised": {
                "status": "NO_CLEAR_SURPRISE",
                "summary": "The 5.75 percent hold matched the overwhelming Reuters poll expectation. No separate guidance surprise is established by the evidence admitted to this packet.",
                "comparisons": [
                    {
                        "comparison_kind": "QUANTITATIVE",
                        "metric": "bi_rate",
                        "actual": 5.75,
                        "expected": 5.75,
                        "difference_percentage_points": 0.0,
                    }
                ],
                "evidence_refs": [
                    "WSEV-ID-BI-BI-20260819",
                    "WSEV-ID-BI-REUTERS-20260819",
                ],
            },
            "what_moved": [],
            "what_appears_connected": {
                "interaction_type": "OBSERVATION_CONTEXT",
                "causal_status": "NOT_A_CAUSAL_CLAIM",
                "confidence": "LOW",
                "summary": "No discrete post-decision rupiah, rates or equity movement is promoted from the reviewed evidence. The packet records the expected hold and its policy context without manufacturing a market-reaction narrative.",
                "evidence_refs": ["WSEV-ID-BI-BI-20260819"],
            },
            "what_may_be_noise": [
                {
                    "summary": "BI itself identified heightened global volatility and the Middle East war as material rupiah-stability context, while the Reuters-syndicated report notes the decision occurred during a leadership transition.",
                    "evidence_refs": [
                        "WSEV-ID-BI-BI-20260819",
                        "WSEV-ID-BI-REUTERS-20260819",
                    ],
                }
            ],
            "alternative_explanations": [],
            "second_order_effects": {
                "status": "NOT_ESTABLISHED",
                "summary": "No distinct later currency, growth, political or capital-flow effect is established here. Policy continuity under interim leadership is context, not a demonstrated second-order outcome.",
            },
            "falsifiers": [
                "If reliable high-frequency evidence establishes a discrete post-decision market move with a clean window, `what_moved` should be revisited rather than remaining empty.",
                "If a stronger pre-decision source shows expectations were materially split despite the Reuters poll, the NO_CLEAR_SURPRISE classification should be re-examined.",
            ],
            "analytical_conclusion": "Bank Indonesia delivered the overwhelmingly expected 5.75 percent hold. The reviewed evidence does not justify promoting a discrete market reaction, so the packet preserves a null movement result rather than forcing a tradable narrative.",
            "canonical_mutation_prohibited": True,
            "google_calendar_write": False,
        },
        {
            "analysis_id": "WSAN-EG-CBE-20260820-001",
            "review_state": "REVIEWED_SAMPLE",
            "review_phase": "POST_EVENT",
            "analysis_as_of_utc": as_of,
            "canonical_occurrence_id": "WSO-HIST-R-EG-CBE-20260820",
            "canonical_series_id": "WSER-REGJ-EG-CBE-MPC",
            "canonical_event_type": "MONETARY_POLICY_DECISION",
            "canonical_institution": "Central Bank of Egypt",
            "canonical_release_utc": None,
            "scope": "20 August 2026 CBE MPC decision, institutional expectation benchmark and explicitly unpromoted market reaction",
            "what_happened": {
                "summary": "The Central Bank of Egypt kept its overnight deposit rate at 19.00 percent, overnight lending rate at 20.00 percent, and both main-operation and discount rates at 19.50 percent.",
                "actuals": [
                    {"metric": "overnight_deposit_rate", "value": 19.0, "unit": "percent", "evidence_refs": ["WSEV-EG-CBE-CBE-20260820"]},
                    {"metric": "overnight_lending_rate", "value": 20.0, "unit": "percent", "evidence_refs": ["WSEV-EG-CBE-CBE-20260820"]},
                ],
                "evidence_refs": ["WSEV-EG-CBE-CBE-20260820"],
            },
            "what_was_expected": {
                "summary": "HC Securities & Investment explicitly expected the MPC to keep rates unchanged at the 20 August meeting.",
                "benchmarks": [
                    {
                        "metric": "policy_stance",
                        "value": "HOLD",
                        "unit": "decision",
                        "benchmark_type": "OTHER_DEFENSIBLE_EXPECTATION",
                        "evidence_refs": ["WSEV-EG-CBE-HC-20260819"],
                    }
                ],
                "evidence_refs": ["WSEV-EG-CBE-HC-20260819"],
            },
            "what_surprised": {
                "status": "NO_CLEAR_SURPRISE",
                "summary": "The unchanged stance matched the admitted pre-decision institutional expectation. S does not turn a single institutional forecast into a synthetic consensus distribution.",
                "comparisons": [
                    {
                        "comparison_kind": "QUALITATIVE",
                        "metric": "policy_stance",
                        "actual": "CBE policy rates unchanged",
                        "expected": "HC Securities expected policy rates to remain unchanged",
                        "direction": "MATCHED_EXPECTATION",
                    }
                ],
                "evidence_refs": [
                    "WSEV-EG-CBE-CBE-20260820",
                    "WSEV-EG-CBE-HC-20260819",
                ],
            },
            "what_moved": [],
            "what_appears_connected": {
                "interaction_type": "OBSERVATION_CONTEXT",
                "causal_status": "NOT_A_CAUSAL_CLAIM",
                "confidence": "LOW",
                "summary": "The reviewed evidence establishes the decision and one defensible expectation benchmark but not a clean post-decision market movement. No market-causality statement is made.",
                "evidence_refs": [
                    "WSEV-EG-CBE-CBE-20260820",
                    "WSEV-EG-CBE-HC-20260819",
                ],
            },
            "what_may_be_noise": [
                {
                    "summary": "CBE and HC both identify regional geopolitical turbulence and energy/fiscal inflation pressures as material background conditions, while CBE also reported softer-than-expected monthly inflation.",
                    "evidence_refs": [
                        "WSEV-EG-CBE-CBE-20260820",
                        "WSEV-EG-CBE-HC-20260819",
                    ],
                }
            ],
            "alternative_explanations": [],
            "second_order_effects": {
                "status": "NOT_ESTABLISHED",
                "summary": "No subsequent exchange-rate, treasury-yield, inflation-expectations or political effect is established in this sample. The hold itself is the observed first-order policy outcome.",
            },
            "falsifiers": [
                "If a broader and more representative pre-decision expectation survey shows a materially different central expectation, the NO_CLEAR_SURPRISE classification should be reconsidered.",
                "If clean high-frequency market evidence later establishes a discrete reaction to the CBE decision, `what_moved` should be populated with that evidence rather than inferred retrospectively.",
            ],
            "analytical_conclusion": "CBE held rates unchanged, matching the admitted HC Securities expectation. The reviewed evidence does not establish a discrete market reaction, so the packet stops at policy outcome and context rather than constructing a causal market story.",
            "canonical_mutation_prohibited": True,
            "google_calendar_write": False,
        },
        {
            "analysis_id": "WSAN-AR-CPI-202607-001",
            "review_state": "REVIEWED_SAMPLE",
            "review_phase": "POST_EVENT",
            "analysis_as_of_utc": as_of,
            "canonical_occurrence_id": "WSO-HIST-R-AR-CPI-202607",
            "canonical_series_id": "WSER-REG2-AR-CPI",
            "canonical_event_type": "OFFICIAL_STATISTICAL_RELEASE",
            "canonical_institution": "INDEC",
            "canonical_release_utc": None,
            "scope": "Argentina July 2026 national CPI release, modest consensus surprise and composition context without a promoted market move",
            "what_happened": {
                "summary": "Argentina's national CPI rose 2.1 percent month-on-month in July 2026.",
                "actuals": [
                    {"metric": "national_cpi_mom", "value": 2.1, "unit": "percent", "evidence_refs": ["WSEV-AR-CPI-INDEC-20260813"]}
                ],
                "evidence_refs": ["WSEV-AR-CPI-INDEC-20260813"],
            },
            "what_was_expected": {
                "summary": "Reuters reported analyst expectations of 2.0 percent month-on-month inflation.",
                "benchmarks": [
                    {
                        "metric": "national_cpi_mom",
                        "value": 2.0,
                        "unit": "percent",
                        "benchmark_type": "MARKET_FORECAST",
                        "evidence_refs": ["WSEV-AR-CPI-REUTERS-20260813"],
                    }
                ],
                "evidence_refs": ["WSEV-AR-CPI-REUTERS-20260813"],
            },
            "what_surprised": {
                "status": "UPSIDE",
                "summary": "Monthly CPI was 0.1 percentage point above the cited analyst expectation. The difference is modest and is not by itself evidence of a material market or policy shock.",
                "comparisons": [
                    {
                        "comparison_kind": "QUANTITATIVE",
                        "metric": "national_cpi_mom",
                        "actual": 2.1,
                        "expected": 2.0,
                        "difference_percentage_points": 0.1,
                    }
                ],
                "evidence_refs": [
                    "WSEV-AR-CPI-INDEC-20260813",
                    "WSEV-AR-CPI-REUTERS-20260813",
                ],
            },
            "what_moved": [],
            "what_appears_connected": {
                "interaction_type": "OBSERVATION_CONTEXT",
                "causal_status": "NOT_A_CAUSAL_CLAIM",
                "confidence": "LOW",
                "summary": "No discrete post-release FX, sovereign-rate or equity movement is promoted from the reviewed evidence. The packet records the modest data surprise and price-composition context only.",
                "evidence_refs": [
                    "WSEV-AR-CPI-INDEC-20260813",
                    "WSEV-AR-CPI-REUTERS-20260813",
                ],
            },
            "what_may_be_noise": [
                {
                    "summary": "Reuters reports that recreation and culture, particularly winter-holiday packages, led monthly price increases, followed by restaurants and hotels. Seasonal/category composition therefore matters when interpreting the 0.1-point headline surprise.",
                    "evidence_refs": ["WSEV-AR-CPI-REUTERS-20260813"],
                }
            ],
            "alternative_explanations": [],
            "second_order_effects": {
                "status": "NOT_ESTABLISHED",
                "summary": "No distinct subsequent monetary-policy, exchange-rate, fiscal or political effect is established by this sample. The modest upside surprise remains an observed data fact rather than a promoted transmission story.",
            },
            "falsifiers": [
                "If a later reconstruction establishes a discrete and temporally clean Argentine market reaction to the CPI release, `what_moved` should be populated with source-backed measurements.",
                "If the relevant contemporaneous consensus benchmark is revised materially away from 2.0 percent, the magnitude or direction of the surprise should be recalculated.",
            ],
            "analytical_conclusion": "Argentina's July CPI was a modest 0.1 percentage point upside surprise relative to the cited analyst expectation. No defensible discrete market move is established, so the packet preserves the surprise without forcing a market-causality narrative.",
            "canonical_mutation_prohibited": True,
            "google_calendar_write": False,
        },
    ]


def detect_state(reviews: dict[str, Any], evidence: dict[str, Any]) -> str:
    ids = {row.get("analysis_id") for row in reviews.get("reviews", [])}
    eids = {row.get("evidence_id") for row in evidence.get("evidence", [])}
    if (
        reviews.get("version") == PRE["reviews_version"]
        and len(reviews.get("reviews", [])) == PRE["review_count"]
        and evidence.get("version") == PRE["evidence_version"]
        and len(evidence.get("evidence", [])) == PRE["evidence_count"]
        and not (ids & NEW_ANALYSIS_IDS)
        and not (eids & NEW_EVIDENCE_IDS)
    ):
        return "PRE"
    if (
        reviews.get("version") == POST["reviews_version"]
        and len(reviews.get("reviews", [])) == POST["review_count"]
        and evidence.get("version") == POST["evidence_version"]
        and len(evidence.get("evidence", [])) == POST["evidence_count"]
        and NEW_ANALYSIS_IDS <= ids
        and NEW_EVIDENCE_IDS <= eids
    ):
        return "POST"
    return "UNKNOWN"


def transform(
    schema: dict[str, Any],
    reviews: dict[str, Any],
    evidence: dict[str, Any],
    canonical: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from world_signals.analysis import analysis_population_readiness, validate_analysis

    if canonical.get("version") != PRE["canonical_version"] or len(canonical.get("records", [])) != PRE["canonical_count"]:
        raise SystemExit("PRECONDITION FAILED: canonical checkpoint is not v0.29 / 678")
    if schema.get("version") != PRE["schema_version"]:
        raise SystemExit("PRECONDITION FAILED: analysis schema is not v0.2")
    if detect_state(reviews, evidence) != "PRE":
        raise SystemExit("PRECONDITION FAILED: Analysis datasets are not exact S pre-state")

    canonical_by_id = {row.get("occurrence_id"): row for row in canonical.get("records", [])}
    expected = {
        "WSO-HIST-R-IN-GDP-2026Q1": ("South Asia", "DATA_RELEASE"),
        "WSO-HIST-R-ID-BI-202608": ("Southeast Asia", "MONETARY_POLICY_DECISION_PROCESS"),
        "WSO-HIST-R-EG-CBE-20260820": ("Africa", "MONETARY_POLICY_DECISION"),
        "WSO-HIST-R-AR-CPI-202607": ("Latin America", "OFFICIAL_STATISTICAL_RELEASE"),
    }
    for occurrence_id, (region, event_type) in expected.items():
        row = canonical_by_id.get(occurrence_id)
        if not row:
            raise SystemExit(f"PRECONDITION FAILED: missing canonical R anchor {occurrence_id}")
        if (row.get("region"), row.get("event_type"), row.get("lifecycle_status")) != (region, event_type, "COMPLETED"):
            raise SystemExit(f"PRECONDITION FAILED: canonical R anchor semantics drifted for {occurrence_id}")

    out_reviews = copy.deepcopy(reviews)
    out_evidence = copy.deepcopy(evidence)
    out_reviews["version"] = POST["reviews_version"]
    out_reviews["reference_date"] = "2026-09-06"
    out_reviews["canonical_checkpoint"] = {"registry_version": "0.29", "record_count": 678}
    out_reviews["reviews"].extend(review_rows())
    out_evidence["version"] = POST["evidence_version"]
    out_evidence["reference_date"] = "2026-09-06"
    out_evidence["evidence"].extend(evidence_rows())

    report = validate_analysis(schema, out_evidence, out_reviews, canonical)
    if not report.ok:
        raise SystemExit("SIMULATION FAILED: " + "; ".join(report.errors))
    readiness = analysis_population_readiness(schema, out_reviews, canonical)
    if readiness.get("broad_population_state") != POST["readiness"]:
        raise SystemExit(f"SIMULATION FAILED: unexpected readiness {readiness.get('broad_population_state')}")
    priority = {row["region"]: row for row in readiness["priority_geographic_stress_regions"]}
    for region in ("Africa", "South Asia", "Southeast Asia", "Latin America"):
        row = priority[region]
        if (row["eligible_completed_count"], row["reviewed_count"], row["state"]) != (1, 1, "REVIEWED_SAMPLE_PRESENT"):
            raise SystemExit(f"SIMULATION FAILED: priority readiness mismatch for {region}: {row}")
    if readiness.get("reviewed_occurrence_count") != 6:
        raise SystemExit("SIMULATION FAILED: reviewed occurrence count is not 6")
    if readiness.get("reviewed_event_type_diversity", 0) < 2:
        raise SystemExit("SIMULATION FAILED: event-type diversity gate not met")
    return out_reviews, out_evidence, readiness


def audit_text(readiness: dict[str, Any], hashes: dict[str, str]) -> str:
    priority = {row["region"]: row for row in readiness["priority_geographic_stress_regions"]}
    return f"""# WORLD SIGNALS — Priority-region Analysis S transaction audit v0.1

**Transaction date:** 2026-09-06  
**Canonical checkpoint:** v0.29 / 678 — unchanged  
**Analysis post-state:** reviews v0.3 / 6; evidence v0.3 / 14

## Added reviewed stress samples

- `WSAN-IN-GDP-2026Q1-001` — South Asia — India GDP — UPSIDE — one source-reported FX change+endpoint — LOW-confidence observed association.
- `WSAN-ID-BI-202608-001` — Southeast Asia — Bank Indonesia — NO_CLEAR_SURPRISE — no discrete market move promoted.
- `WSAN-EG-CBE-20260820-001` — Africa — Central Bank of Egypt — NO_CLEAR_SURPRISE — no discrete market move promoted.
- `WSAN-AR-CPI-202607-001` — Latin America — Argentina CPI — UPSIDE — no discrete market move promoted.

## Readiness result

Broad state: **`{readiness['broad_population_state']}`**.

This means only that the four priority geographic stress regions each contain at least one audited post-event sample and the minimum reviewed event-type-diversity gate is satisfied. It does **not** mean regional analytical completeness, representativeness or permission for uncontrolled population.

Priority-region state after S:

- Africa: {priority['Africa']['eligible_completed_count']} eligible / {priority['Africa']['reviewed_count']} reviewed / `{priority['Africa']['state']}`
- South Asia: {priority['South Asia']['eligible_completed_count']} eligible / {priority['South Asia']['reviewed_count']} reviewed / `{priority['South Asia']['state']}`
- Southeast Asia: {priority['Southeast Asia']['eligible_completed_count']} eligible / {priority['Southeast Asia']['reviewed_count']} reviewed / `{priority['Southeast Asia']['state']}`
- Latin America: {priority['Latin America']['eligible_completed_count']} eligible / {priority['Latin America']['reviewed_count']} reviewed / `{priority['Latin America']['state']}`

## Null-result discipline

Three of the four new packets intentionally carry `what_moved: []`. WORLD SIGNALS does not require a completed event to produce a discrete tradable reaction. India is the only new movement observation, and its GDP-to-rupee connection is LOW confidence because Reuters identifies RBI intervention and flow-related dollar supply as stronger immediate drivers.

## Protected upstream SHA-256

- canonical registry: `{hashes['canonical']}`
- canonical schema: `{hashes['canonical_schema']}`
- source registry: `{hashes['sources']}`
- change ledger: `{hashes['ledger']}`
- biosecurity overlay: `{hashes['overlay']}`
- monitor expectations: `{hashes['expectations']}`
- monitor operations policy: `{hashes['operations']}`
- Analysis schema: `{hashes['analysis_schema']}`

All are required to remain byte-identical through S.

## Write gates

- automatic canonical commit: **OFF**
- Google Calendar write: **OFF**
- canonical mutation from Analysis: **PROHIBITED**
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from world_signals.analysis import analysis_population_readiness, validate_analysis

    schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    evidence = load(EVIDENCE_PATH)
    canonical = load(CANONICAL_PATH)
    hashes = upstream_hashes()
    state = detect_state(reviews, evidence)

    if state == "POST":
        report = validate_analysis(schema, evidence, reviews, canonical)
        if not report.ok:
            raise SystemExit("POST-STATE INVALID: " + "; ".join(report.errors))
        readiness = analysis_population_readiness(schema, reviews, canonical)
        print(json.dumps({
            "mode": "POST_STATE_CHECK",
            "analysis_reviews_version": reviews["version"],
            "analysis_review_count": len(reviews["reviews"]),
            "analysis_evidence_version": evidence["version"],
            "analysis_evidence_count": len(evidence["evidence"]),
            "readiness": readiness["broad_population_state"],
            "new_analysis_ids": sorted(NEW_ANALYSIS_IDS),
            "new_evidence_ids": sorted(NEW_EVIDENCE_IDS),
        }, indent=2))
        return
    if state != "PRE":
        raise SystemExit("STATE FAILED: Analysis datasets are neither exact S pre-state nor reviewed post-state")

    out_reviews, out_evidence, readiness = transform(schema, reviews, evidence, canonical)
    result = {
        "mode": "CHECK_ONLY" if not args.apply else "APPLY",
        "post": {
            "analysis_reviews_version": out_reviews["version"],
            "analysis_review_count": len(out_reviews["reviews"]),
            "analysis_evidence_version": out_evidence["version"],
            "analysis_evidence_count": len(out_evidence["evidence"]),
            "canonical_checkpoint": out_reviews["canonical_checkpoint"],
            "readiness": readiness["broad_population_state"],
            "reviewed_event_type_diversity": readiness["reviewed_event_type_diversity"],
        },
        "new_analysis_ids": sorted(NEW_ANALYSIS_IDS),
        "new_evidence_ids": sorted(NEW_EVIDENCE_IDS),
    }
    print(json.dumps(result, indent=2))

    if not args.apply:
        return
    if os.environ.get("WORLD_SIGNALS_APPLY_ANALYSIS_S") != "YES":
        raise SystemExit("APPLY REFUSED: set WORLD_SIGNALS_APPLY_ANALYSIS_S=YES")

    write(REVIEWS_PATH, out_reviews)
    write(EVIDENCE_PATH, out_evidence)
    AUDIT_PATH.write_text(audit_text(readiness, hashes), encoding="utf-8")

    after = upstream_hashes()
    if after != hashes:
        changed = [key for key in hashes if hashes[key] != after[key]]
        raise SystemExit(f"POST-WRITE FAILED: protected upstream files changed: {changed}")
    report = validate_analysis(schema, load(EVIDENCE_PATH), load(REVIEWS_PATH), canonical)
    if not report.ok:
        raise SystemExit("POST-WRITE FAILED: " + "; ".join(report.errors))


if __name__ == "__main__":
    main()
