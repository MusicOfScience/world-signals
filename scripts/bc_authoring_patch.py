from __future__ import annotations

from pathlib import Path


def replace_between(text: str, start: str, end: str, new: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[:i] + new.rstrip() + "\n\n" + text[j + 1 :]


def patch_ba() -> None:
    path = Path("scripts/apply_analysis_revision_contract_ba.py")
    text = path.read_text(encoding="utf-8")

    anchor = "from world_signals.analysis import validate_analysis\n"
    addition = "from world_signals.checkpoint_contract import validate_descendant_checkpoint, version_at_least\n"
    if addition not in text:
        if anchor not in text:
            raise SystemExit("BA import anchor drift")
        text = text.replace(anchor, anchor + addition, 1)

    new_target_schema = '''def target_analysis_schema(current: dict[str, Any]) -> dict[str, Any]:
    if current.get("version") != "0.6":
        policy = current.get("analysis_revision_policy") or {}
        required_fields = set(policy.get("required_revision_fields") or [])
        require(
            set(target_revision_policy()["required_revision_fields"]).issubset(required_fields),
            "BA Analysis descendant lost required revision fields",
        )
        report = validate_descendant_checkpoint(
            versions_at_least={
                "BA Analysis schema": (current.get("version"), "0.7"),
            },
            exact_values={
                "BA parent preservation": (policy.get("parent_snapshot_must_remain_present"), True),
                "BA same Canonical occurrence": (policy.get("same_canonical_occurrence_required"), True),
                "BA as-of advancement": (policy.get("analysis_as_of_must_strictly_advance"), True),
                "BA cycle prohibition": (policy.get("cycles_prohibited"), True),
                "BA Live/Analysis lineage separation": (policy.get("live_revision_and_analysis_revision_are_distinct"), True),
                "BA upstream Canonical mutation": (policy.get("upstream_canonical_mutation_allowed"), False),
                "BA upstream Live mutation": (policy.get("upstream_live_mutation_allowed"), False),
                "BA upstream monitor mutation": (policy.get("upstream_monitor_mutation_allowed"), False),
                "BA Calendar write": (policy.get("google_calendar_write_allowed"), False),
            },
        )
        require(
            report.ok,
            "BA Analysis descendant contract failed: " + "; ".join(report.errors),
        )
        return deepcopy(current)

    target = deepcopy(current)
    target["version"] = "0.7"
    target["reference_date"] = "2026-09-06"
    target["analysis_revision_policy"] = target_revision_policy()

    additions = [
        "BA v0.7 introduces a prospective Analysis revision-lineage contract while production revisions remain closed and the existing 21 reviewed snapshots remain unchanged.",
        "A future Analysis revision must be a new immutable analysis_id with an explicit direct parent, preserved parent snapshot, same Canonical occurrence and strictly later analysis_as_of_utc; silent in-place analytical history rewrite is prohibited.",
        "Live observations never automatically revise Analysis, Live revision/state-update lineage remains distinct from Analysis revision lineage, automatic latest-Analysis selection remains prohibited, and further production revision population requires another pressure audit.",
    ]
    guardrails = list(target.get("guardrails") or [])
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    target["guardrails"] = guardrails
    return target'''
    text = replace_between(text, "def target_analysis_schema", "\ndef target_status", new_target_schema)

    new_target_status = '''def target_status(current: str) -> str:
    old_header = "# CURRENT RECOVERY OVERRIDE — POST-AY / AZ FIRST PRODUCTION LIVE→ANALYSIS LINK"
    new_header = "# CURRENT RECOVERY OVERRIDE — POST-AZ / BA ANALYSIS REVISION FOUNDATION"
    if old_header not in current and new_header not in current:
        report = validate_descendant_checkpoint(
            required_markers={
                "BA PROJECT_STATUS descendant": (
                    current,
                    ["BA adds a **production-closed Analysis revision-lineage contract**"],
                )
            }
        )
        require(
            report.ok,
            "BA status descendant is missing frozen BA architecture: " + "; ".join(report.errors),
        )
        return current
    text = current.replace(old_header, new_header, 1)
    text = text.replace("- Analysis schema: **v0.6**", "- Analysis schema: **v0.7**", 1)

    live_line = "- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**\n"
    revision_line = "- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**\n"
    if revision_line not in text:
        require(live_line in text, "BA status could not locate production live-input line")
        text = text.replace(live_line, live_line + revision_line, 1)

    marker = "## Current architecture decision\n\n"
    paragraph = (
        "BA adds a **production-closed Analysis revision-lineage contract** before any further Live or bridge population. "
        "A future revision must be a new immutable Analysis snapshot with an explicit direct parent, preserved prior snapshot, "
        "the same Canonical occurrence and a strictly later `analysis_as_of_utc`. Automatic latest-head selection, public revision "
        "metadata projection and all upstream writes remain closed. BA adds no production revision, no Live observation and no Analysis evidence.\n\n"
    )
    if paragraph not in text:
        require(marker in text, "BA status could not locate architecture-decision marker")
        text = text.replace(marker, marker + paragraph, 1)

    stale = (
        "The next audit should decide whether prospective Live Intelligence → Analysis linkage now creates more architectural value "
        "than another isolated Live specimen. Japan household spending remains a valid held Analysis specimen, not a queue-completion obligation."
    )
    replacement = (
        "After BA, another pressure audit must decide whether the first real Analysis revision, a fifth Live observation, or a second "
        "production Live→Analysis relationship creates the highest marginal contract pressure. None is a population quota."
    )
    if stale in text:
        text = text.replace(stale, replacement, 1)
    return text'''
    text = replace_between(text, "def target_status", "\ndef target_roadmap", new_target_status)

    old = '    if heading in current:\n        return current\n'
    new = '    if heading in current or "BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot." in current:\n        return current\n'
    if old not in text:
        raise SystemExit("BA roadmap descendant anchor drift")
    text = text.replace(old, new, 1)

    new_preconditions = '''def assert_preconditions(plan: dict[str, Any]) -> None:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    expectations = load(EXPECTATIONS_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    materialised = version_at_least(analysis_schema.get("version"), "0.7")
    if not materialised:
        require(canonical.get("version") == pre["canonical_registry_version"], "BA Canonical version drift")
        require(len(canonical.get("records", [])) == pre["canonical_record_count"], "BA Canonical count drift")
        require(sources.get("version") == pre["source_registry_version"], "BA Source version drift")
        require(len(sources.get("sources", [])) == pre["source_count"], "BA Source count drift")
        require(ledger.get("version") == pre["change_ledger_version"], "BA Change Ledger version drift")
        require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "BA Change Ledger count drift")
        require(expectations.get("version") == pre["monitor_expectations_version"], "BA monitor version drift")
        require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "BA monitor adapter count drift")
        require(live_schema.get("version") == pre["live_schema_version"], "BA Live schema drift")
        require(len(live_observations.get("observations", [])) == pre["live_observation_count"], "BA Live observation count drift")
        require(len(live_evidence.get("evidence", [])) == pre["live_evidence_count"], "BA Live evidence count drift")
        require(analysis_schema.get("version") == pre["analysis_schema_version"], "BA Analysis schema drift")
        require(reviews.get("version") == pre["analysis_reviews_version"], "BA Analysis reviews version drift")
        require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "BA Analysis review count drift")
        require(analysis_evidence.get("version") == pre["analysis_evidence_version"], "BA Analysis evidence version drift")
        require(len(analysis_evidence.get("evidence", [])) == pre["analysis_evidence_count"], "BA Analysis evidence count drift")
        require(production_live_input_count(reviews) == pre["production_live_input_count"], "BA production live-input drift")
        require(production_analysis_revision_count(reviews) == 0, "BA requires zero pre-existing Analysis revisions")
        require(exact_series_count(reviews) == pre["production_exact_timestamp_series_count"], "BA exact-series drift")
        return

    report = validate_descendant_checkpoint(
        versions_at_least={
            "BA Analysis schema": (analysis_schema.get("version"), "0.7"),
            "BA Analysis reviews": (reviews.get("version"), pre["analysis_reviews_version"]),
            "BA Analysis evidence": (analysis_evidence.get("version"), pre["analysis_evidence_version"]),
            "BA Live schema": (live_schema.get("version"), pre["live_schema_version"]),
        },
        counts_at_least={
            "BA Analysis review population": (len(reviews.get("reviews", [])), pre["analysis_review_count"]),
            "BA Analysis evidence population": (len(analysis_evidence.get("evidence", [])), pre["analysis_evidence_count"]),
            "BA Live observation population": (len(live_observations.get("observations", [])), pre["live_observation_count"]),
            "BA Live evidence population": (len(live_evidence.get("evidence", [])), pre["live_evidence_count"]),
            "BA production Live inputs": (production_live_input_count(reviews), pre["production_live_input_count"]),
        },
    )
    require(report.ok, "BA descendant precondition failed: " + "; ".join(report.errors))
    target_analysis_schema(analysis_schema)'''
    text = replace_between(text, "def assert_preconditions", "\ndef simulate", new_preconditions)

    new_assert_target = '''def assert_target(plan: dict[str, Any], target: dict[str, Any]) -> None:
    schema = target["analysis_schema"]
    reviews = load(REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    canonical = load(CANONICAL_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)

    target_analysis_schema(schema)
    exact_foundation = (
        schema.get("version") == "0.7"
        and len(reviews.get("reviews", [])) == 21
        and len(evidence.get("evidence", [])) == 95
        and production_analysis_revision_count(reviews) == 0
        and production_live_input_count(reviews) == 1
    )
    if exact_foundation:
        require(schema.get("analysis_revision_policy") == target_revision_policy(), "BA revision policy drift")
        require(exact_series_count(reviews) == 0, "BA target must preserve EXACT_TIMESTAMP_SERIES=0")
    else:
        report = validate_descendant_checkpoint(
            versions_at_least={
                "BA target Analysis schema": (schema.get("version"), "0.7"),
                "BA target reviews": (reviews.get("version"), "0.17"),
                "BA target evidence": (evidence.get("version"), "0.17"),
            },
            counts_at_least={
                "BA target review population": (len(reviews.get("reviews", [])), 21),
                "BA target evidence population": (len(evidence.get("evidence", [])), 95),
                "BA target production Live inputs": (production_live_input_count(reviews), 1),
            },
        )
        require(report.ok, "BA target descendant failed: " + "; ".join(report.errors))

    core = validate_analysis(schema, evidence, reviews, canonical)
    require(core.ok, "BA target core Analysis validation failed: " + "; ".join(core.errors))
    revisions = validate_analysis_revisions(schema, reviews)
    require(revisions.ok, "BA target revision validation failed: " + "; ".join(revisions.errors))
    bridge = validate_live_analysis_bridge(schema, reviews, live_observations)
    require(bridge.ok, "BA target Live→Analysis bridge validation failed: " + "; ".join(bridge.errors))
    live = validate_live_intelligence(live_schema, live_evidence, live_observations, canonical)
    require(live.ok, "BA target Live validation failed: " + "; ".join(live.errors))

    docs = validate_descendant_checkpoint(
        required_markers={
            "BA status": (target["status"], ["BA adds a **production-closed Analysis revision-lineage contract**"]),
            "BA roadmap": (target["roadmap"], ["BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot."]),
        }
    )
    require(docs.ok, "BA target documentation drift: " + "; ".join(docs.errors))'''
    text = replace_between(text, "def assert_target", "\ndef write_target", new_assert_target)
    path.write_text(text, encoding="utf-8")


def patch_az() -> None:
    path = Path("scripts/apply_japan_fies_live_analysis_az.py")
    text = path.read_text(encoding="utf-8")

    anchor = "from world_signals.analysis import analysis_population_readiness, validate_analysis\n"
    addition = "from world_signals.checkpoint_contract import validate_descendant_checkpoint, version_at_least\n"
    if addition not in text:
        if anchor not in text:
            raise SystemExit("AZ import anchor drift")
        text = text.replace(anchor, anchor + addition, 1)

    new_preconditions = '''def assert_preconditions(plan: dict[str, Any]) -> None:
    pre = plan["pre_state"]
    canonical = load(CANONICAL_PATH)
    sources = load(SOURCES_PATH)
    ledger = load(LEDGER_PATH)
    expectations = load(EXPECTATIONS_PATH)
    live_schema = load(LIVE_SCHEMA_PATH)
    live_observations = load(LIVE_OBSERVATIONS_PATH)
    live_evidence = load(LIVE_EVIDENCE_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(REVIEWS_PATH)
    analysis_evidence = load(ANALYSIS_EVIDENCE_PATH)

    selection = plan["selection"]
    live_present = any(
        row.get("observation_id") == selection["live_observation_id"]
        for row in live_observations.get("observations", [])
    )
    analysis_present = any(
        row.get("analysis_id") == selection["analysis_id"]
        for row in reviews.get("reviews", [])
    )
    require(live_present == analysis_present, "AZ partial materialisation detected")

    target = canonical_target(canonical, selection["canonical_occurrence_id"])
    require(target.get("series_id") == selection["canonical_series_id"], "AZ target series drift")
    require(target.get("jurisdiction") == "Japan", "AZ target jurisdiction drift")
    require((target.get("region") or target.get("broad_region")) == "East Asia", "AZ target region drift")
    require(target.get("category") == "MACROECONOMIC_RELEASE", "AZ target category drift")
    require(target.get("event_type") == "DATA_RELEASE", "AZ target event type drift")
    require(target.get("lifecycle_status") == "COMPLETED", "AZ target must already be COMPLETED")
    require(target.get("source_timezone") == "Asia/Tokyo", "AZ target timezone drift")
    require(target.get("start_local") == "2026-09-04", "AZ target civil date drift")
    require(target.get("time_precision") == "DAY", "AZ target time precision drift")
    require(target.get("start_utc") is None, "AZ must not start from a fabricated Canonical UTC")

    if not live_present:
        require(canonical.get("version") == pre["canonical_registry_version"], "AZ Canonical version drift")
        require(len(canonical.get("records", [])) == pre["canonical_record_count"], "AZ Canonical count drift")
        require(sources.get("version") == pre["source_registry_version"], "AZ Source version drift")
        require(len(sources.get("sources", [])) == pre["source_count"], "AZ Source count drift")
        require(ledger.get("version") == pre["change_ledger_version"], "AZ Change Ledger version drift")
        require(len(ledger.get("changes", [])) == pre["change_ledger_count"], "AZ Change Ledger count drift")
        require(expectations.get("version") == pre["monitor_expectations_version"], "AZ monitor version drift")
        require(len(expectations.get("adapters", [])) == pre["monitor_adapter_count"], "AZ monitor adapter count drift")
        require(live_schema.get("version") == pre["live_schema_version"], "AZ Live schema drift")
        require(len(live_observations.get("observations", [])) == pre["live_observation_count"], "AZ Live observation count drift")
        require(len(live_evidence.get("evidence", [])) == pre["live_evidence_count"], "AZ Live evidence count drift")
        require(analysis_schema.get("version") == pre["analysis_schema_version"], "AZ Analysis schema drift")
        require(reviews.get("version") == pre["analysis_reviews_version"], "AZ reviews version drift")
        require(len(reviews.get("reviews", [])) == pre["analysis_review_count"], "AZ review count drift")
        require(analysis_evidence.get("version") == pre["analysis_evidence_version"], "AZ Analysis evidence version drift")
        require(len(analysis_evidence.get("evidence", [])) == pre["analysis_evidence_count"], "AZ Analysis evidence count drift")
        require(production_live_input_count(reviews) == pre["production_live_input_count"], "AZ live-input prestate drift")
        require(exact_series_count(reviews) == pre["production_exact_timestamp_series_count"], "AZ exact-series prestate drift")
        return

    post = plan["target_state"]
    report = validate_descendant_checkpoint(
        versions_at_least={
            "AZ Live schema": (live_schema.get("version"), post["live_schema_version"]),
            "AZ Analysis schema": (analysis_schema.get("version"), post["analysis_schema_version"]),
            "AZ reviews dataset": (reviews.get("version"), post["analysis_reviews_version"]),
            "AZ evidence dataset": (analysis_evidence.get("version"), post["analysis_evidence_version"]),
        },
        counts_at_least={
            "AZ Live observations": (len(live_observations.get("observations", [])), post["live_observation_count"]),
            "AZ Live evidence": (len(live_evidence.get("evidence", [])), post["live_evidence_count"]),
            "AZ Analysis reviews": (len(reviews.get("reviews", [])), post["analysis_review_count"]),
            "AZ Analysis evidence": (len(analysis_evidence.get("evidence", [])), post["analysis_evidence_count"]),
            "AZ production Live inputs": (production_live_input_count(reviews), post["production_live_input_count"]),
        },
    )
    require(report.ok, "AZ descendant precondition failed: " + "; ".join(report.errors))'''
    text = replace_between(text, "def assert_preconditions", "\ndef target_live_schema", new_preconditions)

    new_live_schema = '''def target_live_schema(current: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if current.get("version") != "0.3":
        require(
            version_at_least(current.get("version"), "0.4"),
            "AZ Live schema requires v0.3 prestate or v0.4+ reviewed descendant",
        )
        return deepcopy(current)
    target = deepcopy(current)
    target["version"] = "0.4"
    target["reference_date"] = "2026-09-06"
    target["ax_checkpoint"] = {
        "schema_version": "0.3",
        "observations_version": "0.3",
        "evidence_version": "0.3",
        "population_state": "CONTROLLED_MULTI_SNAPSHOT_SPECIMEN",
        "observation_count": 3,
        "evidence_count": 4,
        "post_merge_main_sha": "0a7608ab56116d0f65ffd1492a3da87bcbf35f47",
        "historical_contract": "AX v0.3 preserved the AW Nepal shock and added two reviewed DRC evolving-state snapshots while public projection, automatic ingestion and automatic story clustering remained closed.",
    }
    target["population_policy"] = {
        "mode": "CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN",
        "production_population_allowed": True,
        "evidence_population_allowed": True,
        "maximum_observation_count": 4,
        "maximum_evidence_count": 6,
        "automatic_ingestion_allowed": False,
        "existing_analysis_evidence_migration_allowed": False,
        "public_observation_projection_allowed": False,
        "reason": "AZ adds exactly one reviewed Japan FIES economic-data observation with a real OUTCOME_OF Canonical link and two primary-official Live evidence rows. Further Live population requires another pressure audit.",
    }
    guardrails = [
        item
        for item in (target.get("guardrails") or [])
        if not item.startswith("AX v0.3 allows only")
        and not item.startswith("Public observation projection, automatic ingestion")
    ]
    additions = [
        "AX v0.3 is a frozen historical checkpoint of three observations and four evidence rows; legitimate later descendants may grow only through a separately pressure-audited contract.",
        "AZ v0.4 adds exactly one reviewed ECONOMIC_DATA_OBSERVATION for Japan July 2026 FIES and does not convert the same release's retrospective April-June data-vintage note into synthetic prior Live history.",
        "A scheduled Live economic-data observation may link OUTCOME_OF a real completed Canonical occurrence without changing Canonical identity, provenance or timing.",
        "Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain prohibited in AZ v0.4.",
        "A fifth Live observation or broader ingestion requires another pressure audit.",
    ]
    for item in additions:
        if item not in guardrails:
            guardrails.append(item)
    target["guardrails"] = guardrails
    return target'''
    text = replace_between(text, "def target_live_schema", "\ndef target_live_observations", new_live_schema)

    new_live_observations = '''def target_live_observations(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    row = deepcopy(payload["live_observation"])
    ids = {item.get("observation_id") for item in target.get("observations", [])}
    if row["observation_id"] in ids:
        return target
    require(len(target.get("observations", [])) == 3, "AZ expected exactly three pre-existing Live observations")
    target["observations"].append(row)
    target["version"] = "0.4"
    target["reference_date"] = "2026-09-06"
    target["population_state"] = "CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN"
    target["scope_note"] = "Bounded reviewed internal Live Intelligence store: AW Nepal shock, AX DRC evolving-state pair, and one AZ Japan FIES Canonical-linked economic-data specimen. Public projection and automatic ingestion remain closed."
    return target'''
    text = replace_between(text, "def target_live_observations", "\ndef target_live_evidence", new_live_observations)

    new_live_evidence = '''def target_live_evidence(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    payload_ids = {row["evidence_id"] for row in payload["live_evidence"]}
    existing = {row.get("evidence_id") for row in target.get("evidence", [])}
    present = payload_ids & existing
    if present == payload_ids:
        return target
    require(not present, "AZ partial Live evidence materialisation detected")
    require(len(target.get("evidence", [])) == 4, "AZ expected exactly four pre-existing Live evidence rows")
    for row in payload["live_evidence"]:
        target["evidence"].append(deepcopy(row))
    target["version"] = "0.4"
    target["reference_date"] = "2026-09-06"
    target["population_state"] = "CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN"
    target["scope_note"] = "Evidence supports the bounded reviewed Live store through AZ. Live evidence remains separate from Canonical provenance and Analysis evidence; public observation projection remains closed."
    return target'''
    text = replace_between(text, "def target_live_evidence", "\ndef target_analysis_schema", new_live_evidence)

    start = text.index("def target_analysis_schema")
    end = text.index("\ndef target_reviews", start)
    block = text[start:end]
    guard_start = block.index('    raw_version = current.get("version")')
    target_start = block.index("    target = deepcopy(current)", guard_start)
    replacement = '''    raw_version = current.get("version")
    if raw_version != "0.5":
        require(
            version_at_least(raw_version, "0.6"),
            "AZ Analysis schema requires v0.5 prestate or v0.6+ reviewed descendant",
        )
        return deepcopy(current)
'''
    block = block[:guard_start] + replacement + block[target_start:]
    text = text[:start] + block + text[end:]

    new_reviews = '''def target_reviews(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    row = deepcopy(payload["analysis_review"])
    ids = {item.get("analysis_id") for item in target.get("reviews", [])}
    if row["analysis_id"] in ids:
        return target
    require(len(target.get("reviews", [])) == 20, "AZ expected 20 Analysis reviews prestate")
    target["reviews"].append(row)
    target["version"] = "0.17"
    target["reference_date"] = "2026-09-06"
    return target'''
    text = replace_between(text, "def target_reviews", "\ndef target_analysis_evidence", new_reviews)

    new_analysis_evidence = '''def target_analysis_evidence(current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    target = deepcopy(current)
    payload_ids = {row["evidence_id"] for row in payload["analysis_evidence"]}
    existing = {row.get("evidence_id") for row in target.get("evidence", [])}
    present = payload_ids & existing
    if present == payload_ids:
        return target
    require(not present, "AZ partial Analysis evidence materialisation detected")
    require(len(target.get("evidence", [])) == 91, "AZ expected 91 Analysis evidence rows prestate")
    for row in payload["analysis_evidence"]:
        target["evidence"].append(deepcopy(row))
    target["version"] = "0.17"
    target["reference_date"] = "2026-09-06"
    return target'''
    text = replace_between(text, "def target_analysis_evidence", "\ndef target_status", new_analysis_evidence)

    old_descendant = '''    if ay_title not in current:
        require(
            current.startswith("# CURRENT RECOVERY OVERRIDE — POST-"),
            "AZ PROJECT_STATUS title drift",
        )
        require(
            "- Live Intelligence: **v0.4 / 4 reviewed internal observations / 6 primary-official evidence rows / public observation projection CLOSED**" in current,
            "AZ PROJECT_STATUS descendant lost Live v0.4 checkpoint",
        )
        require(
            "- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**" in current,
            "AZ PROJECT_STATUS descendant lost Analysis v0.17 population",
        )
        require(
            "- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**" in current,
            "AZ PROJECT_STATUS descendant lost first production Live input",
        )
        return current
'''
    new_descendant = '''    if ay_title not in current:
        require(
            current.startswith("# CURRENT RECOVERY OVERRIDE — POST-"),
            "AZ PROJECT_STATUS title drift",
        )
        report = validate_descendant_checkpoint(
            required_markers={
                "AZ PROJECT_STATUS descendant": (
                    current,
                    ["AZ exercises the first **production Live Intelligence → Analysis relationship**"],
                )
            }
        )
        require(
            report.ok,
            "AZ PROJECT_STATUS descendant lost AZ architecture: " + "; ".join(report.errors),
        )
        return current
'''
    if old_descendant not in text:
        raise SystemExit("AZ status descendant block drift")
    text = text.replace(old_descendant, new_descendant, 1)

    old = '    if "## Stage 8 — prospective Live Intelligence → Analysis linkage — AZ FIRST PRODUCTION LINK DONE / PUBLIC CLOSED" in current:\n        return current\n'
    new = '    if "## Stage 8 — prospective Live Intelligence → Analysis linkage — AZ FIRST PRODUCTION LINK DONE / PUBLIC CLOSED" in current or "AZ then pressure-audited and populated exactly one relationship" in current:\n        return current\n'
    if old not in text:
        raise SystemExit("AZ roadmap descendant anchor drift")
    text = text.replace(old, new, 1)

    new_assert_target = '''def assert_target(plan: dict[str, Any], target: dict[str, Any]) -> None:
    post = plan["target_state"]
    live_schema = target["live_schema"]
    live_observations = target["live_observations"]
    live_evidence = target["live_evidence"]
    analysis_schema = target["analysis_schema"]
    reviews = target["reviews"]
    analysis_evidence = target["analysis_evidence"]

    exact_az_checkpoint = (
        live_schema.get("version") == post["live_schema_version"]
        and len(live_observations.get("observations", [])) == post["live_observation_count"]
        and len(live_evidence.get("evidence", [])) == post["live_evidence_count"]
        and analysis_schema.get("version") == post["analysis_schema_version"]
        and len(reviews.get("reviews", [])) == post["analysis_review_count"]
        and len(analysis_evidence.get("evidence", [])) == post["analysis_evidence_count"]
        and production_live_input_count(reviews) == post["production_live_input_count"]
    )
    if exact_az_checkpoint:
        require(live_observations.get("population_state") == post["live_population_state"], "AZ target Live population state mismatch")
        policy = analysis_schema["live_input_policy"]
        require(policy["mode"] == "CONTROLLED_SINGLE_PRODUCTION_LINK", "AZ target bridge mode mismatch")
        require(policy["maximum_production_live_inputs"] == 1, "AZ target max live-input mismatch")
        require(policy["maximum_live_inputs_per_review"] == 1, "AZ target per-review max mismatch")
        require(policy["public_live_input_projection_allowed"] is False, "AZ public bridge projection opened")
        require(live_schema["population_policy"]["public_observation_projection_allowed"] is False, "AZ public Live projection opened")
        require(exact_series_count(reviews) == post["production_exact_timestamp_series_count"], "AZ target exact-series mismatch")
    else:
        report = validate_descendant_checkpoint(
            versions_at_least={
                "AZ target Live schema": (live_schema.get("version"), post["live_schema_version"]),
                "AZ target Analysis schema": (analysis_schema.get("version"), post["analysis_schema_version"]),
                "AZ target reviews": (reviews.get("version"), post["analysis_reviews_version"]),
                "AZ target evidence": (analysis_evidence.get("version"), post["analysis_evidence_version"]),
            },
            counts_at_least={
                "AZ target Live observations": (len(live_observations.get("observations", [])), post["live_observation_count"]),
                "AZ target Live evidence": (len(live_evidence.get("evidence", [])), post["live_evidence_count"]),
                "AZ target Analysis reviews": (len(reviews.get("reviews", [])), post["analysis_review_count"]),
                "AZ target Analysis evidence": (len(analysis_evidence.get("evidence", [])), post["analysis_evidence_count"]),
                "AZ target production Live inputs": (production_live_input_count(reviews), post["production_live_input_count"]),
            },
        )
        require(report.ok, "AZ target descendant failed: " + "; ".join(report.errors))

    policy = analysis_schema["live_input_policy"]
    require(
        policy.get("factual_input_requires_matching_canonical_occurrence") is True,
        "AZ descendant same-anchor gate missing",
    )

    new_live = [
        row
        for row in live_observations["observations"]
        if row.get("observation_id") == plan["selection"]["live_observation_id"]
    ]
    require(len(new_live) == 1, "AZ target Live observation missing/duplicated")
    require(new_live[0].get("observation_type") == "ECONOMIC_DATA_OBSERVATION", "AZ must not relabel July FIES as DATA_REVISION")
    require(new_live[0].get("revision_of_observation_id") is None, "AZ must not invent Live revision ancestry")
    require(
        new_live[0].get("canonical_links")
        == [{"occurrence_id": "WSO-MAC-B-0041", "relationship": "OUTCOME_OF"}],
        "AZ Live canonical link drift",
    )

    review = next(
        row
        for row in reviews["reviews"]
        if row.get("analysis_id") == plan["selection"]["analysis_id"]
    )
    require(review.get("what_moved") == [], "AZ must not manufacture market movement")
    require(review.get("what_surprised", {}).get("status") == "DOWNSIDE", "AZ surprise status drift")
    require(review.get("canonical_release_utc") is None, "AZ must preserve unresolved Canonical release UTC")
    require(
        review.get("live_inputs")
        == [
            {
                "observation_id": plan["selection"]["live_observation_id"],
                "roles": ["FACTUAL_INPUT"],
                "analysis_sections": [
                    "what_happened",
                    "what_surprised",
                    "what_may_be_noise",
                    "alternative_explanations",
                ],
            }
        ],
        "AZ inaugural production Live-input relationship drift",
    )

    if exact_az_checkpoint:
        public = public_live_intelligence_projection(
            live_schema, live_evidence, live_observations, load(CANONICAL_PATH)
        )
        require(
            public["metadata"]["public_observation_count"] == 0,
            "AZ public Live observation projection must remain zero at frozen checkpoint",
        )
        require(public["observations"] == [], "AZ public Live observation rows must remain empty at frozen checkpoint")

    readiness = analysis_population_readiness(analysis_schema, reviews, load(CANONICAL_PATH))
    require(readiness["reviewed_occurrence_count"] >= 21, "AZ reviewed occurrence floor lost")'''
    text = replace_between(text, "def assert_target", "\ndef write_target", new_assert_target)
    path.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    path = Path("tests/test_analysis_revision_contract_ba.py")
    text = path.read_text(encoding="utf-8")
    old = '''        self.assertEqual(production_analysis_revision_count(self.reviews), 0)
        self.assertEqual(len(self.reviews["reviews"]), 21)
        self.assertEqual(len(self.evidence["evidence"]), 95)
        self.assertEqual(production_live_input_count(self.reviews), 1)
        self.assertEqual(apply_ba.exact_series_count(self.reviews), 0)
'''
    new = '''        self.assertEqual(self.plan["target_state"]["analysis_review_count"], 21)
        self.assertEqual(self.plan["target_state"]["analysis_evidence_count"], 95)
        self.assertGreaterEqual(len(self.reviews["reviews"]), 21)
        self.assertGreaterEqual(len(self.evidence["evidence"]), 95)
        self.assertGreaterEqual(production_live_input_count(self.reviews), 1)
'''
    if old not in text:
        raise SystemExit("BA exact-count test anchor drift")
    text = text.replace(old, new, 1)
    old = '''        malformed = descendant.replace(
            "- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**",
            "- production Analysis revisions: **1 / gate OPEN**",
            1,
        )
'''
    new = '''        malformed = descendant.replace(
            "BA adds a **production-closed Analysis revision-lineage contract**",
            "BA historical architecture marker removed",
            1,
        )
'''
    if old not in text:
        raise SystemExit("BA status test anchor drift")
    text = text.replace(old, new, 1)
    old = '        self.assertEqual(len(projection["reviews"]), 21)\n'
    new = '        self.assertEqual(len(projection["reviews"]), len(self.reviews["reviews"]))\n'
    if old not in text:
        raise SystemExit("BA projection count anchor drift")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

    path = Path("tests/test_japan_fies_live_analysis_az.py")
    text = path.read_text(encoding="utf-8")
    old = '''        self.assertEqual(len(self.target["reviews"]["reviews"]), 21)
        self.assertEqual(self.target["analysis_evidence"]["version"], "0.17")
        self.assertEqual(len(self.target["analysis_evidence"]["evidence"]), 95)
        self.assertEqual(production_live_input_count(self.target["reviews"]), 1)
        policy = self.target["analysis_schema"]["live_input_policy"]
        self.assertEqual(policy["maximum_production_live_inputs"], 1)
        self.assertEqual(policy["maximum_live_inputs_per_review"], 1)
        self.assertFalse(policy["public_live_input_projection_allowed"])
        self.assertFalse(
            self.target["live_schema"]["population_policy"]["public_observation_projection_allowed"]
        )
        self.assertEqual(post["analysis_evidence_count"], 95)
'''
    new = '''        self.assertGreaterEqual(len(self.target["reviews"]["reviews"]), 21)
        evidence_version = tuple(
            int(part) for part in self.target["analysis_evidence"]["version"].split(".")
        )
        self.assertGreaterEqual(evidence_version, (0, 17))
        self.assertGreaterEqual(len(self.target["analysis_evidence"]["evidence"]), 95)
        self.assertGreaterEqual(production_live_input_count(self.target["reviews"]), 1)
        self.assertEqual(post["maximum_production_live_inputs"], 1)
        self.assertEqual(post["maximum_live_inputs_per_review"], 1)
        self.assertFalse(post["public_live_input_projection_allowed"])
        self.assertFalse(post["public_live_observation_projection_allowed"])
        self.assertEqual(post["analysis_evidence_count"], 95)
'''
    if old not in text:
        raise SystemExit("AZ bounded-population test anchor drift")
    text = text.replace(old, new, 1)

    old = '''        reviews = deepcopy(self.target["reviews"])
        row = next(
            item for item in reviews["reviews"]
            if item["analysis_id"] == "WSAN-JP-FIES-202607-001"
        )
        row["live_inputs"].append({
'''
    new = '''        schema = deepcopy(self.target["analysis_schema"])
        policy = schema["live_input_policy"]
        policy["mode"] = "CONTROLLED_SINGLE_PRODUCTION_LINK"
        policy["maximum_production_live_inputs"] = 1
        policy["maximum_live_inputs_per_review"] = 1
        policy["public_live_input_projection_allowed"] = False
        source_row = self.analysis_by_id["WSAN-JP-FIES-202607-001"]
        reviews = deepcopy(self.target["reviews"])
        reviews["reviews"] = [deepcopy(source_row)]
        row = reviews["reviews"][0]
        row["live_inputs"].append({
'''
    if old not in text:
        raise SystemExit("AZ second-input test anchor drift")
    text = text.replace(old, new, 1)
    old = '            self.target["analysis_schema"], reviews, self.target["live_observations"]\n'
    new = '            schema, reviews, self.target["live_observations"]\n'
    if old not in text:
        raise SystemExit("AZ second-input validator anchor drift")
    text = text.replace(old, new, 1)

    old = '''        malformed = descendant.replace(
            "- production `live_inputs`: **1 / reviewed maximum 1 / public projection CLOSED**",
            "- production `live_inputs`: **2 / reviewed maximum 2 / public projection OPEN**",
            1,
        )
'''
    new = '''        malformed = descendant.replace(
            "AZ exercises the first **production Live Intelligence → Analysis relationship**",
            "AZ historical relationship marker removed",
            1,
        )
'''
    if old not in text:
        raise SystemExit("AZ status test anchor drift")
    text = text.replace(old, new, 1)

    old = '''        self.assertEqual(readiness["eligible_completed_occurrence_count"], 21)
        self.assertEqual(readiness["reviewed_occurrence_count"], 21)
        self.assertEqual(readiness["reviewed_event_type_diversity"], 18)
'''
    new = '''        self.assertGreaterEqual(readiness["eligible_completed_occurrence_count"], 21)
        self.assertGreaterEqual(readiness["reviewed_occurrence_count"], 21)
        self.assertGreaterEqual(readiness["reviewed_event_type_diversity"], 18)
'''
    if old not in text:
        raise SystemExit("AZ readiness test anchor drift")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_status_and_roadmap() -> None:
    path = Path("PROJECT_STATUS.md")
    text = path.read_text(encoding="utf-8")
    old_header = "# CURRENT RECOVERY OVERRIDE — POST-BA / BB BARMM CANONICAL COVERAGE REPAIR"
    new_header = "# CURRENT RECOVERY OVERRIDE — POST-BB / BC CHECKPOINT DESCENDANT CONTRACT"
    if old_header in text:
        text = text.replace(old_header, new_header, 1)
    elif new_header not in text:
        raise SystemExit("BC status header drift")
    marker = "## Current architecture decision\n\n"
    paragraph = (
        "BC adds a **no-population historical-checkpoint / reviewed-descendant contract** after BB exposed repeated stale ceilings in older tranche tests and helpers. "
        "Before a tranche target exists, exact historical preconditions remain mandatory. After the target is materialised, the old helper validates only tranche-owned identity, relationship and structural invariants plus legitimate version/population floors; unrelated later Source, Change Ledger, monitor, Live or Analysis growth is not treated as drift. "
        "BC opens no production gate and changes no Canonical, Source, Change Ledger, Live or Analysis population.\n\n"
    )
    if paragraph not in text:
        if marker not in text:
            raise SystemExit("BC status architecture marker drift")
        text = text.replace(marker, marker + paragraph, 1)
    old = (
        "After BB, a fresh pressure audit must decide whether the now-anchored BARMM transition warrants downstream Live/Analysis work, whether another Live class creates greater contract pressure, or whether a genuinely evidence-driven first Analysis revision has emerged. No downstream population is pre-authorised by this coverage repair."
    )
    new = (
        "After BC, a fresh pressure audit must decide whether the now-anchored BARMM transition warrants downstream Live/Analysis work, whether another Live class creates greater contract pressure, whether a second Live→Analysis relationship is justified, or whether a genuinely evidence-driven first Analysis revision has emerged. No downstream population is pre-authorised by BC."
    )
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("BC status next-audit marker drift")
    path.write_text(text, encoding="utf-8")

    path = Path("ROADMAP.md")
    text = path.read_text(encoding="utf-8")
    marker = "## Stage 5 — Analysis foundation and controlled sample — DONE / PAUSED FOR AUDIT"
    section = '''### BC — historical checkpoint / reviewed descendant contract — DONE / NO POPULATION

BC formalises the distinction between exact historical transaction prestates and legitimate reviewed descendants. A materialised tranche keeps its frozen historical checkpoint, but later validation is limited to invariants that tranche owns: stable IDs/relationships, structural rules and explicit version/population floors. Unrelated later registry counts, monitor cohorts and temporary population caps are not permanent ceilings.

BA and AZ helpers now remain exact before first materialisation and become read-only/idempotent on reviewed descendants rather than downgrading later dataset versions or populations. BC adds no Canonical, Source, Change Ledger, Live or Analysis rows and opens no production/public gate.

'''
    if section not in text:
        if marker not in text:
            raise SystemExit("BC roadmap marker drift")
        text = text.replace(marker, section + marker, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_ba()
    patch_az()
    patch_tests()
    patch_status_and_roadmap()
    print("BC authoring patch: PASS")


if __name__ == "__main__":
    main()
