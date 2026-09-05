"""Static producer regressions; no semantic parser/validator is substituted."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SUITE = json.loads((ROOT / "conformance/v0.7/semantic_atoms.json").read_text())
INVENTORY = json.loads((ROOT / "conformance/v0.7/coverage-inventory.json").read_text())
KINDS = {"Map", "Event", "Task"}
FORMATS = {"xml", "json", "yaml", "dict"}
CASE_IDS_SHA256 = "3c985cd15c2f89259ec7499e1f8afd8e5f7fe7923767b3d4958e8e15e046ebf1"
ORIGINAL_IDS_SHA256 = "159fdd88eb7f91941a3de1ae8bce5e501bd2b0ea16641b7cad1cda11e315c7ae"
RUNTIME_IDS_SHA256 = "12660931e9ae110030cb9d207bf148030d0b52d55600130206b7ef1a6ec3ba0e"
EXPECTED_FORMATS = {"xml":{"positive":35,"negative":87},"json":{"positive":1,"negative":27},"yaml":{"positive":0,"negative":25},"dict":{"positive":0,"negative":29}}
EXPECTED_RUNTIME_COUNTS = {"v07-runtime-no-io":15,"v07-runtime-roundtrip-no-caller-mutation":24,"v07-runtime-forced-canonical-collision":3,"v07-runtime-identical-payload-registry":3,"v07-runtime-provenance-registry":2,"v07-runtime-in-memory-map-key-and-object-shapes":16,"v07-runtime-canonical-reference-resolution":96,"v07-runtime-new-field-canonical-identity":22,"v07-runtime-opaque-correlators":5,"v07-runtime-legacy-artifact-probe":6,"v07-runtime-packaging-parity":3}
EXPECTED_PROBE_FAMILIES = ["map-int-bounds","map-int-bool","map-int-overflow","map-int-float","map-int-string","map-special-numbers","map-duplicate-xml","map-duplicate-json","map-duplicate-yaml","map-duplicate-structure","map-nesting","map-key-shapes","map-order-identity","map-value-identity","map-empty-types","map-reference","event-occurrence-distinct","event-source-distinct","event-duplicate-identical","event-duplicate-conflict","event-time-provenance","event-invalid-time","task-goal-not-closed","task-action-not-recorded","task-runtime-enum","task-verdict-evidence","task-opaque-handle","typed-forward-refs","typed-wrong-kind","strict-unknown-fields","strict-children","claimed-id-tamper","roundtrip-identity","roundtrip-no-mutation","forced-canonical-collision","identical-payload-registry","provenance-registry","no-io"]


def _ids_digest(values):
    return hashlib.sha256("\n".join(values).encode()).hexdigest()


def test_complete_case_id_inventory_is_pinned():
    ids = [case["id"] for case in SUITE["cases"]]
    assert len(ids) == len(set(ids)) == 204
    assert ids == INVENTORY["case_ids"]
    assert _ids_digest(ids) == CASE_IDS_SHA256
    original = INVENTORY["original_case_ids"]
    assert len(original) == 106
    assert _ids_digest(original) == ORIGINAL_IDS_SHA256
    assert ids[:106] == original
    assert SUITE["coverage"] == INVENTORY["counts"]
    formats = {}
    for case in SUITE["cases"]:
        formats.setdefault(case["format"], {"positive": 0, "negative": 0})[case["category"]] += 1
    assert formats == INVENTORY["formats"] == EXPECTED_FORMATS


def _xml_missing_references(payload):
    root = ET.fromstring("<Scholia>" + payload + "</Scholia>")
    declared = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}
    references = set()
    for node in root.iter():
        for text in (node.text, node.tail):
            if text:
                references.update(re.findall(
                    r"\b(?:REFER|IMPLIES|NOT):([A-Za-z][A-Za-z0-9_]*)(?![A-Za-z0-9_:])", text
                ))
    return references - declared


POSITIVE_XML = [case for case in SUITE["cases"]
                if case["format"] == "xml" and case["category"] == "positive"]


@pytest.mark.parametrize("case", POSITIVE_XML, ids=lambda case: case["id"])
def test_positive_fixture_lexical_references_are_declared(case):
    for key in ("payload", "payload_b"):
        if key in case:
            assert not _xml_missing_references(case[key]), (case["id"], key)


def test_positive_reference_guard_rejects_missing_declaration():
    bad = '<Step id="S_01"><Evidence id="E_01">REFER:Obs_01</Evidence></Step>'
    assert _xml_missing_references(bad) == {"Obs_01"}
    good = bad.replace('<Evidence', '<Observation id="Obs_01">Recorded.</Observation><Evidence')
    assert not _xml_missing_references(good)


def _fixture_atom(case, kind):
    if case["format"] == "xml":
        root = ET.fromstring("<Scholia>" + case["payload"] + "</Scholia>")
        node = next(node for node in root.iter() if node.tag == kind)
        return {**node.attrib, "children": list(node)}
    data = case["payload"] if case["format"] == "dict" else (
        json.loads(case["payload"]) if case["format"] == "json"
        else yaml.safe_load(case["payload"])
    )
    return next(atom for step in data["steps"] for atom in step["atoms"] if atom["kind"] == kind)


@pytest.mark.parametrize("rule", [
    "semantic_unknown_field", "semantic_children_empty", "canonical_id_well_formed"
])
def test_strict_controls_cover_every_kind_and_format(rule):
    cases = [case for case in SUITE["cases"] if case["expects"].get("rule") == rule]
    pairs = {(kind, case["format"]) for case in cases for kind in case["kinds"]}
    assert pairs == {(kind, fmt) for kind in KINDS for fmt in FORMATS}
    index = yaml.safe_load((ROOT / "reference/v0.7/atoms_index.yaml").read_text())
    allowed = {
        row["kind"]: {a["name"] for a in row["attributes"]} |
        {"kind", "content", "operators", "children", "canonical_id"}
        for row in index["atoms"] if row["kind"] in KINDS
    }
    for case in cases:
        kind = case["kinds"][0]
        atom = _fixture_atom(case, kind)
        if rule == "semantic_unknown_field":
            assert set(atom) - allowed[kind], case["id"]
        elif rule == "semantic_children_empty":
            assert atom["children"], case["id"]
        else:
            assert atom["canonical_id"] in {"sha256:000000000000", "sha256:xyz"}, case["id"]
    if rule == "canonical_id_well_formed":
        for claim in ("sha256:000000000000", "sha256:xyz"):
            claim_pairs = {(c["kinds"][0], c["format"]) for c in cases
                           if _fixture_atom(c, c["kinds"][0])["canonical_id"] == claim}
            assert claim_pairs == {(kind, fmt) for kind in KINDS for fmt in FORMATS}


def test_runtime_obligations_are_exact_pending_consumer_requirements():
    obligations = SUITE["runtime_obligations"]
    ids = [row["id"] for row in obligations]
    assert ids == INVENTORY["runtime_obligation_ids"]
    assert len(ids) == len(set(ids)) == 11
    assert _ids_digest(ids) == RUNTIME_IDS_SHA256
    counts = {}
    for row in obligations:
        assert row["owner_gate"] == "reference-implementation-consumer"
        assert row["status"] == "pending_consumer_execution"
        assert row["required_assertions"] and all(row["required_assertions"])
        assert len(row["required_case_ids"]) == len(set(row["required_case_ids"]))
        assert row["required_case_ids"]
        counts[row["id"]] = len(row["required_case_ids"])
        assert {"node_id", "candidate_sha", "spec_sha", "corpus_sha256", "import_origin",
                "command", "exit_code", "outcome", "evidence_sha256"} <= set(row["receipt_fields"])
        assert not ({"passed", "result", "actual_outcome"} & set(row))
    assert counts == INVENTORY["runtime_obligation_case_counts"] == EXPECTED_RUNTIME_COUNTS
    assert SUITE["positive_assertions"]["execution_status"] == "pending_consumer_execution"
    assert {"canonical_ids_preserved", "typed_entry_values_preserved",
            "opaque_correlators_preserved", "repeated_canonical_json_stable"} <= set(
                SUITE["positive_assertions"]["required"]
            )


def test_all_independent_probe_families_have_concrete_receipt_mapping():
    families = INVENTORY["probe_families"]
    assert [row["id"] for row in families] == EXPECTED_PROBE_FAMILIES
    assert len(families) == 38
    case_ids = set(INVENTORY["case_ids"])
    runtime_ids = set(INVENTORY["runtime_obligation_ids"])
    for row in families:
        assert row["case_ids"] or row["runtime_obligation_ids"], row["id"]
        assert set(row["case_ids"]) <= case_ids
        assert set(row["runtime_obligation_ids"]) <= runtime_ids


def test_duplicate_and_nonfinite_raw_encodings_are_not_predecoded():
    cases = {case["id"]: case for case in SUITE["cases"]}
    duplicate = cases["v07-map-entries-duplicate-keys-yaml-document"]
    assert duplicate["payload"].count("n:") == 2
    for fmt in ("xml", "json"):
        for token in ("nan", "infinity", "negative-infinity"):
            case = cases[f"v07-map-special-number-{token}-{fmt}"]
            assert case["expects"]["phase"] == "parse"
            assert case["expects"]["rule"] == "map_entries_shape"
    for token in ("nan", "infinity", "negative-infinity"):
        case = cases[f"v07-map-special-number-{token}-yaml"]
        assert case["expects"]["phase"] == "validate"
        assert case["expects"]["rule"] == "map_entries_typed"


def test_task_nonclosure_controls_preserve_existing_rule_boundaries():
    cases = {case["id"]: case for case in SUITE["cases"]}
    goal = cases["v07-task-satisfied-does-not-close-required-goal"]
    action = cases["v07-task-satisfied-does-not-record-action-result"]
    for case, rule in ((goal, "goal_declared"), (action, "action_recorded")):
        root = ET.fromstring("<Scholia>" + case["payload"] + "</Scholia>")
        assert root.find(".//Task").attrib["status"] == "satisfied"
        assert root.find(".//Observation") is not None
        assert root.find(".//Finding") is None and root.find(".//Concluding") is None
        assert case["expects"]["rule"] == rule
        assert case["expects"]["phase"] == "validate"
    assert ET.fromstring("<Scholia>" + goal["payload"] + "</Scholia>").find(
        ".//Goal").attrib["priority"] == "required"
