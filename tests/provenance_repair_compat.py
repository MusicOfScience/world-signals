from __future__ import annotations

BRAZIL_TSE = "WSSRC-EL-BR-001"
BRAZIL_CONSTITUTION = "WSSRC-EL-BR-002"
SNB = "WSSRC-CB-009"
BRAZIL_OCCURRENCE = "WSO-EL-A-0004"


def _by_source(source_registry: dict) -> dict[str, dict]:
    return {row.get("source_id"): row for row in source_registry.get("sources", [])}


def repair_a_active(source_registry: dict) -> bool:
    return BRAZIL_CONSTITUTION in _by_source(source_registry)


def assert_source_registry_compatible(testcase, source_registry: dict) -> None:
    """Accept the exact historical 223-source state or the reviewed repair-A lineage."""
    rows = source_registry.get("sources", [])
    by_id = _by_source(source_registry)
    if not repair_a_active(source_registry):
        testcase.assertEqual(len(rows), 223)
        testcase.assertNotIn(BRAZIL_CONSTITUTION, by_id)
        return

    version = tuple(int(part) for part in str(source_registry.get("version")).split("."))
    testcase.assertGreaterEqual(version, (1, 61))
    testcase.assertGreaterEqual(len(rows), 224)

    tse = by_id[BRAZIL_TSE]
    testcase.assertEqual(tse.get("canonical_dependency_count"), 3)
    testcase.assertEqual(tse.get("canonical_provenance_use"), "CLEARED_CURATED_FACTUAL_METADATA")
    testcase.assertEqual(tse.get("automated_monitoring_use"), "ENDPOINT_REVIEW_REQUIRED")
    testcase.assertEqual(tse.get("verification_mode"), "MANUAL_AUTHORITATIVE_RECHECK")

    snb = by_id[SNB]
    testcase.assertEqual(
        snb.get("authoritative_url"),
        "https://www.snb.ch/en/services-events/digital-services/event-schedule",
    )
    testcase.assertEqual(snb.get("canonical_dependency_count"), 18)
    testcase.assertEqual(snb.get("canonical_provenance_use"), "CLEARED_CURATED_FACTUAL_METADATA")
    testcase.assertEqual(snb.get("automated_monitoring_use"), "ENDPOINT_REVIEW_REQUIRED")
    testcase.assertEqual(snb.get("verification_mode"), "MANUAL_AUTHORITATIVE_RECHECK")

    constitution = by_id[BRAZIL_CONSTITUTION]
    testcase.assertEqual(constitution.get("canonical_dependency_count"), 1)
    testcase.assertEqual(constitution.get("canonical_provenance_use"), "CLEARED_CURATED_FACTUAL_METADATA")
    testcase.assertEqual(constitution.get("automated_monitoring_use"), "ENDPOINT_REVIEW_REQUIRED")
    testcase.assertEqual(constitution.get("verification_mode"), "MANUAL_AUTHORITATIVE_RECHECK")


def assert_held_sources_compatible(testcase, source_registry: dict, held_ids, missing_fields) -> None:
    by_id = _by_source(source_registry)
    active = repair_a_active(source_registry)
    for held_id in held_ids:
        if active and held_id in {BRAZIL_TSE, SNB}:
            expected = (
                "CLEARED_CURATED_FACTUAL_METADATA",
                "ENDPOINT_REVIEW_REQUIRED",
                "MANUAL_AUTHORITATIVE_RECHECK",
            )
            testcase.assertEqual(
                (
                    by_id[held_id].get("canonical_provenance_use"),
                    by_id[held_id].get("automated_monitoring_use"),
                    by_id[held_id].get("verification_mode"),
                ),
                expected,
            )
        else:
            for field in missing_fields:
                testcase.assertIn(by_id[held_id].get(field), (None, ""))


def assert_brazil_inauguration_compatible(testcase, canonical: dict) -> None:
    matches = [
        row for row in canonical.get("records", [])
        if row.get("occurrence_id") == BRAZIL_OCCURRENCE
    ]
    testcase.assertEqual(len(matches), 1)
    row = matches[0]
    testcase.assertEqual(row.get("start_local"), "2027-01-05")
    testcase.assertEqual(row.get("election_milestone_type"), "INAUGURATION_OR_ASSUMPTION")
    testcase.assertEqual(row.get("series_id"), "WSER-EL-BR-GEN")

    version = tuple(int(part) for part in str(canonical.get("version")).split("."))
    if version < (0, 21):
        testcase.assertEqual(row.get("source_id"), BRAZIL_TSE)
        testcase.assertEqual(row.get("institution"), "Tribunal Superior Eleitoral")
        testcase.assertEqual(row.get("election_date_basis"), "EXPLICIT_ELECTORAL_AUTHORITY_SCHEDULE")
        testcase.assertEqual(row.get("primary_source_assertion_id"), "WSA-024b7ec125f413d8")
        testcase.assertEqual(row.get("last_successful_assertion_id"), "WSA-024b7ec125f413d8")
    else:
        testcase.assertEqual(row.get("source_id"), BRAZIL_CONSTITUTION)
        testcase.assertEqual(row.get("institution"), "Presidency of the Republic of Brazil")
        testcase.assertEqual(row.get("election_date_basis"), "CONSTITUTIONAL_RULE_DERIVED")
        testcase.assertEqual(row.get("primary_source_assertion_id"), "WSA-66b042250a27801e")
        testcase.assertEqual(row.get("last_successful_assertion_id"), "WSA-66b042250a27801e")
