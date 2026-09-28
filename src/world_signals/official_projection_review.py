"""Native optional INTERNAL_ONLY Analysis extension; validation, never promotion.

Source-native horizons remain strings (or explicit source-native period objects).
The Step 14D adapter composes hash-checked material in memory, not a population.
"""
from copy import deepcopy
from datetime import date
import math
import re
import json

from .world_state_history import fingerprint

EPISTEMIC_CLASSES = frozenset({
    "PUBLICATION_FACT", "OBSERVED_EVIDENCE", "MODEL_ASSUMPTION",
    "OFFICIAL_PROJECTION", "SENSITIVITY_CASE", "POLICY_CLAIM", "PRIOR_OFFICIAL_PROJECTION",
})
EDGE_CLASSES = frozenset({
    "MODEL_DEFINED", "ASSUMED_MECHANISM", "SENSITIVITY_SUPPORTED",
    "EXTERNAL_EVIDENCE_SUPPORTED", "HYPOTHESISED",
})
AUDIT_AXES = (
    "historical_plausibility", "current_trajectory", "structural_break_risk",
    "implementation_dependency", "circularity_endogeneity", "sensitivity",
    "downside_alternative", "upside_alternative", "signposts", "revision_conditions",
)
REQUIRED_SECTIONS = (
    "projection_framework", "projection_outputs", "model_assumptions",
    "sensitivity_cases", "assumption_audit", "comparison_baseline", "limitations",
)
COMPARABILITY = {"DIRECTLY_COMPARABLE", "QUALIFIED_COMPARISON", "NOT_DIRECTLY_COMPARABLE"}
METHOD_COMPATIBILITY = {"COMPATIBLE", "QUALIFIED", "INCOMPATIBLE", "NOT_ESTABLISHED"}
CORROBORATION = "SAME_ORIGIN_ASSETS_AND_DEPENDENT_OUTPUTS_NOT_INDEPENDENT_CONFIRMATIONS"
ERROR_INTERPRETATION = "MODEL_ERROR_IS_NOT_EVIDENCE_OF_BAD_FAITH"


def _require(condition, message):
    if not condition:
        raise ValueError("OFFICIAL_PROJECTION_REVIEW: " + message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _limits(value):
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)


def _period(value):
    if isinstance(value, str):
        # No fabricated UTC precision: fiscal years and source-native windows survive.
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                date.fromisoformat(value)
            except ValueError:
                return False
        return _text(value) and re.search(r"\d{4}", value) is not None
    if isinstance(value, dict) and set(value) == {"source_native_period"}:
        return _text(value["source_native_period"])
    if isinstance(value, dict) and set(value) == {"start_date", "end_date"}:
        try:
            return date.fromisoformat(value["start_date"]) <= date.fromisoformat(value["end_date"])
        except (ValueError, TypeError):
            return False
    return False


def _no_scores(value):
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            _require(not any(token in normalized.split("_") for token in ("score", "rating", "grade"))
                     and normalized != "overall_verdict", "audit scores/ratings/grades prohibited")
            _no_scores(child)
    elif isinstance(value, list):
        for child in value:
            _no_scores(child)


def _validate(extension):
    json.dumps(extension, allow_nan=False)
    _require(isinstance(extension, dict), "extension object required")
    _require(set(REQUIRED_SECTIONS) <= extension.keys(), "required sections missing")
    _require(extension.get("contract_version") == "0.1" and
             extension.get("visibility") == "INTERNAL_ONLY", "internal contract/version required")
    _require(extension.get("corroboration_policy") == CORROBORATION, "no source-count confidence uplift")
    _require(extension.get("error_interpretation") == ERROR_INTERPRETATION, "model miss is not bad faith")
    _require(_limits(extension["limitations"]), "limitations required")
    assets = extension.get("source_manifest", [])
    _require(isinstance(assets, list) and assets, "source manifest required")
    by_asset = {}
    for row in assets:
        aid = row.get("asset_id")
        _require(_text(aid) and aid not in by_asset, "duplicate/missing source identity")
        _require(_text(row.get("url")) and row["url"].startswith("https://") and
                 _text(row.get("source_family")) and row.get("source_class") in EPISTEMIC_CLASSES and
                 re.fullmatch(r"[a-f0-9]{64}", row.get("sha256", "")), "source provenance/hash required")
        by_asset[aid] = row
    _require(extension.get("source_manifest_sha256") == fingerprint(assets), "source manifest mismatch")

    def refs(rows):
        _require(isinstance(rows, list) and rows, "source references required")
        for ref in rows:
            _require(ref.get("asset_id") in by_asset and _text(ref.get("locator")), "unknown source/locator")

    def tagged_fields(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"epistemic_class", "projection_class"}:
                    _require(child in EPISTEMIC_CLASSES | EDGE_CLASSES, "unknown epistemic class")
                elif key == "source_refs":
                    refs(child)
                tagged_fields(child)
        elif isinstance(value, list):
            for child in value:
                tagged_fields(child)

    def index(section, key):
        rows = extension[section]
        _require(isinstance(rows, list), section + " must be an array")
        result = {}
        for row in rows:
            identity = row.get(key)
            _require(_text(identity) and identity not in result, "duplicate/missing " + key)
            result[identity] = row
        return result

    outputs = index("projection_outputs", "projection_id")
    assumptions = index("model_assumptions", "assumption_id")
    sensitivities = index("sensitivity_cases", "sensitivity_id")
    _require(outputs and assumptions, "outputs and assumptions required")
    _require(not outputs.keys() & assumptions.keys() and
             not (outputs.keys() | assumptions.keys()) & sensitivities.keys(), "identities must be distinct")
    framework = extension["projection_framework"]
    refs(framework["source_refs"])
    _require(framework["publication_fact"]["epistemic_class"] == "PUBLICATION_FACT", "publication fact separate")
    _require(_text(framework["publication_fact"]["statement"]), "publication finding required")
    _require(_period(framework["projection_horizon"]), "framework horizon required")
    if "ministerial_framing" in framework:
        framing = framework["ministerial_framing"]
        _require(framing["epistemic_class"] == "POLICY_CLAIM", "policy framing is not factual evidence")
        refs(framing["source_refs"])

    comparison_rows = extension.get("projection_comparison", []) + extension.get("historical_backtest", [])
    comparisons = {}
    for row in comparison_rows:
        cid = row.get("comparison_id")
        _require(_text(cid) and cid not in comparisons, "duplicate/missing comparison_id")
        comparisons[cid] = row
        refs(row["source_refs"])
        _require(row.get("comparability") in COMPARABILITY and _text(row.get("method_basis")) and
                 row.get("method_compatibility") in METHOD_COMPATIBILITY, "comparison method/compatibility required")
        historical = "original_vintage" in row
        _require(_text(row.get("original_vintage" if historical else "prior_vintage")), "prior vintage required")
        _require(_text(row.get("observed_vintage" if historical else "current_vintage")), "comparison vintage required")
        prior_vintage = row["original_vintage" if historical else "prior_vintage"]
        _require(any(by_asset[r["asset_id"]].get("vintage") == prior_vintage and
                     by_asset[r["asset_id"]]["source_class"] == "PRIOR_OFFICIAL_PROJECTION"
                     for r in row["source_refs"]), "prior/original vintage provenance required")
        _require(_period(row.get("reference_period")) if historical else
                 _period(row.get("prior_horizon")) and _period(row.get("current_horizon")), "comparison horizon required")
        field = "error" if historical else "difference"
        calculated = row.get(field)
        if row["comparability"] == "NOT_DIRECTLY_COMPARABLE":
            _require(row.get("difference") is None and row.get("error") is None, "noncomparable calculation prohibited")
        elif calculated is not None:
            _require(row["method_compatibility"] in {"COMPATIBLE", "QUALIFIED"} and
                     (row["comparability"] != "DIRECTLY_COMPARABLE" or row["method_compatibility"] == "COMPATIBLE"),
                     "method compatibility blocks numeric calculation")
            _require(_text(row.get("calculation_basis")), "calculation basis required")
            old = row.get("original_projected_value" if historical else "prior_value")
            new = row.get("observed_value" if historical else "current_value")
            _require(_number(old) and _number(new) and _number(calculated) and _text(row.get("unit")), "numeric comparison/units required")
            _require(calculated == round(new - old, 6), "comparison arithmetic mismatch")
            if not historical:
                _require(row["prior_horizon"] == row["current_horizon"], "incompatible comparison horizons")
            if any(marker in row["unit"].lower() for marker in ("dollar", "$", "aud", "usd", "eur", "gbp", "cad", "jpy", "nzd")):
                basis = row.get("value_basis", {})
                _require(basis.get("prior") and basis.get("prior") == basis.get("current"), "incompatible/unknown price basis")

    for row in outputs.values():
        _require(row.get("epistemic_class") == "OFFICIAL_PROJECTION", "output is not Forecast/Observation/state")
        _require(_text(row.get("metric")) and _text(row.get("unit")) and
                 _period(row.get("projection_horizon")) and _period(row.get("reference_period")), "output metric/units/horizon required")
        value = row.get("value")
        bounded = isinstance(value, dict) and set(value) == {"lower", "upper"} and all(_number(x) for x in value.values()) and value["lower"] <= value["upper"]
        _require(_number(value) or _text(value) or bounded, "numeric/range/qualitative value required")
        _require(row.get("assumption_refs") and set(row["assumption_refs"]) <= assumptions.keys(), "unknown output assumption")
        _require(set(row.get("sensitivity_refs", [])) <= sensitivities.keys() and
                 set(row.get("comparison_refs", [])) <= comparisons.keys(), "unknown output sensitivity/comparison")
        _require(_limits(row.get("limitations")), "output limitations required")
        refs(row["source_refs"])
        _require(all(by_asset[ref["asset_id"]]["source_class"] == "OFFICIAL_PROJECTION" for ref in row["source_refs"]), "technical projection provenance required")
    for row in assumptions.values():
        _require(row.get("epistemic_class") == "MODEL_ASSUMPTION", "assumption epistemic class")
        _require(row.get("basis_kind") in {"EMPIRICAL_EXTRAPOLATION", "MAINTAINED_POLICY_SETTING", "TECHNICAL_CONVENTION", "CONDITIONAL_MODEL_MECHANISM"}, "assumption basis required")
        if row.get("assumption_type") == "FISCAL_POLICY_SETTING":
            _require(row["basis_kind"] == "MAINTAINED_POLICY_SETTING", "policy is not empirical assumption")
        _require(all(_text(row.get(f)) for f in ("assumption_type", "domain", "statement", "unit", "issuer_rationale")) and
                 row.get("value_or_rule") is not None and _period(row.get("reference_period")) and
                 _period(row.get("projection_horizon")), "assumption substance required")
        _require(set(row["output_dependencies"]) == {oid for oid, out in outputs.items() if row["assumption_id"] in out["assumption_refs"]}, "output dependency mismatch")
        _require(set(row.get("sensitivity_refs", [])) <= sensitivities.keys(), "unknown assumption sensitivity")
        refs(row["source_refs"])
    for row in sensitivities.values():
        _require(row.get("epistemic_class") == "SENSITIVITY_CASE", "sensitivity is not Scenario")
        _require(row.get("assumption_refs") and set(row["assumption_refs"]) <= assumptions.keys(), "unknown changed assumptions")
        unit = row.get("unit")
        _require(row.get("shock") and (_text(unit) or isinstance(unit, dict) and unit and all(_text(v) for v in unit.values())) and row.get("results") and
                 _period(row.get("projection_horizon")) and _limits(row.get("limitations")), "sensitivity shock/units/horizon required")
        _require(set(row.get("affected_output_refs", [])) <= outputs.keys(), "unknown affected output")
        _require(not any(key in row for key in ("probability", "scenario_id", "forecast_id")), "probability/Scenario/Forecast requires separate contract")
        refs(row["source_refs"])

    audit = index("assumption_audit", "assumption_id")
    _require(audit.keys() == assumptions.keys(), "each material assumption needs one audit")
    _no_scores(extension["assumption_audit"])
    for row in audit.values():
        _require(set(row) == {"assumption_id", *AUDIT_AXES}, "ten audit axes required")
        for axis in AUDIT_AXES:
            finding = row[axis]
            _require(_text(finding.get("finding")) and _limits(finding.get("limitations")), "axis finding/limitations required")
            if finding["finding"] == "NOT_ESTABLISHED":
                _require(_text(finding.get("explanation")), "unresolved finding explanation required")
            refs(finding["source_refs"])
    baseline = extension["comparison_baseline"]
    _require(baseline.get("epistemic_class") == "PRIOR_OFFICIAL_PROJECTION" and
             _text(baseline.get("vintage")) and _period(baseline.get("horizon")), "prior baseline vintage/horizon required")
    refs(baseline["source_refs"])
    _require(any(by_asset[r["asset_id"]].get("vintage") == baseline["vintage"] and
                 by_asset[r["asset_id"]]["source_class"] == "PRIOR_OFFICIAL_PROJECTION"
                 for r in baseline["source_refs"]), "baseline vintage provenance required")
    edges = extension.get("dependency_map", [])
    seen = set()
    graph = {}
    for row in edges:
        _require(_text(row.get("edge_id")) and row["edge_id"] not in seen, "duplicate/missing edge identity")
        seen.add(row["edge_id"])
        _require(row.get("epistemic_class") in EDGE_CLASSES and row.get("production_relationship") is False, "internal dependency not Relationship")
        _require(row["from_ref"] in outputs.keys() | assumptions.keys() and
                 row["to_ref"] in outputs.keys() | assumptions.keys() and row["from_ref"] != row["to_ref"], "dependency refs/self-cycle invalid")
        _require(_text(row.get("mechanism")) and _limits(row.get("limitations")), "dependency mechanism/limitations required")
        refs(row["source_refs"])
        graph.setdefault(row["from_ref"], []).append(row)
    # Model feedback is legitimate only when explicitly declared and sourced.
    declared_cycles = []
    for cycle in extension.get("feedback_cycles", []):
        refs(cycle["source_refs"])
        nodes = cycle["node_refs"]
        _require(len(nodes) >= 3 and nodes[0] == nodes[-1] and
                 len(set(nodes[:-1])) == len(nodes) - 1, "invalid feedback path")
        _require(all(any(e["to_ref"] == b and e["epistemic_class"] == "MODEL_DEFINED"
                         for e in graph.get(a, [])) for a, b in zip(nodes, nodes[1:])), "feedback path unresolved")
        declared_cycles.append(set(zip(nodes, nodes[1:])))
    def walk(node, path, edge_path):
        for edge in graph.get(node, []):
            target = edge["to_ref"]
            if target in path:
                cycle = edge_path[path.index(target):] + [edge]
                _require(all(e["epistemic_class"] == "MODEL_DEFINED" for e in cycle) and
                         {(e["from_ref"], e["to_ref"]) for e in cycle} in declared_cycles,
                         "undeclared/inappropriate dependency cycle")
            else:
                walk(target, path + [target], edge_path + [edge])
    for node in graph:
        walk(node, [node], [])
    for row in extension.get("observed_evidence", []):
        _require(row.get("epistemic_class") == "OBSERVED_EVIDENCE", "observed evidence separate")
        refs(row["source_refs"])
        _require(all(by_asset[ref["asset_id"]]["source_class"] == "OBSERVED_EVIDENCE" for ref in row["source_refs"]), "projection cannot establish observation")
    tagged_fields(extension)


def validate_official_projection_review(extension):
    """Return native validation errors, including malformed container types."""
    try:
        _validate(extension)
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        return ("OFFICIAL_PROJECTION_REVIEW: " + str(error),)
    return ()


def step14d_native_extension(package):
    """Lossless read-only assembly; original vocab retained as source_comparability.

    No re-sealing, admission, public projection or new analytical findings.
    Derived IDs and reverse references are structural, not evidence assertions.
    """
    from .official_projection_candidate import validate_package
    validate_package(package)
    inventory = deepcopy(package["projection_inventory"])
    audit = deepcopy(package["assumption_audit"])
    ext = {key: inventory[key] for key in REQUIRED_SECTIONS if key in inventory}
    ext.update(contract_version="0.1", visibility="INTERNAL_ONLY",
               assumption_audit=audit["assumption_audit"],
               source_manifest=deepcopy(package["evidence_manifest"]["assets"]),
               source_manifest_sha256=package["evidence_manifest"]["asset_manifest_sha256"])
    for key in ("projection_comparison", "historical_backtest", "dependency_map", "corroboration_policy", "error_interpretation"):
        ext[key] = audit[key]
    for key in ("observed_evidence", "major_transitions"):
        ext[key] = inventory[key]
    ext["limitations"] += audit["limitations"]
    ext["candidate_lineage"] = {key: part["semantic_fingerprint"] for key, part in package.items()}
    # Step 14D explicitly names a two-edge model feedback loop. Preserve that
    # declaration; never create edges or classify an arbitrary cycle as feedback.
    ext["feedback_cycles"] = []
    for edge in ext["dependency_map"]:
        if "explicit loop" in edge["mechanism"].lower():
            reverse = next((e for e in ext["dependency_map"] if
                            e["from_ref"] == edge["to_ref"] and e["to_ref"] == edge["from_ref"]), None)
            if reverse:
                ext["feedback_cycles"].append({"node_refs": [edge["from_ref"], edge["to_ref"], edge["from_ref"]],
                                               "source_refs": deepcopy(edge["source_refs"]),
                                               "basis": edge["mechanism"]})
    for section in ("projection_comparison", "historical_backtest"):
        for i, row in enumerate(ext[section]):
            row["comparison_id"] = f"{section}-{i + 1}"
            row["source_comparability"] = row["comparability"]
            if row["comparability"] != "NOT_DIRECTLY_COMPARABLE":
                row["comparability"] = "QUALIFIED_COMPARISON"
            row["method_compatibility"] = "NOT_ESTABLISHED" if row["comparability"] == "NOT_DIRECTLY_COMPARABLE" else "QUALIFIED"
            row["calculation_basis"] = row["method_basis"]
    for row in ext["projection_outputs"]:
        row["epistemic_class"] = row.pop("projection_class")
        row["projection_horizon"] = row.pop("horizon")
        row["reference_period"] = row.pop("reference_year")
        row["comparison_refs"] = []  # No row association was reviewed in Step 14D.
    for row in ext["sensitivity_cases"]:
        row["projection_horizon"] = row.pop("horizon")
        row["unit"] = row["shock"].get("unit", row["shock"].get("units", "SOURCE_NATIVE_QUALITATIVE_CASE"))
        row["affected_output_refs"] = [o["projection_id"] for o in ext["projection_outputs"] if row["sensitivity_id"] in o["sensitivity_refs"]]
    for row in ext["model_assumptions"]:
        row["sensitivity_refs"] = [s["sensitivity_id"] for s in ext["sensitivity_cases"] if row["assumption_id"] in s["assumption_refs"]]
    for section in ("projection_outputs", "model_assumptions", "sensitivity_cases"):
        for row in ext[section]:
            for field in ("projection_horizon", "reference_period"):
                if field in row and not _period(row[field]):
                    row[field] = {"source_native_period": row[field]}
    errors = validate_official_projection_review(ext)
    if errors:
        raise ValueError("; ".join(errors))
    return ext
