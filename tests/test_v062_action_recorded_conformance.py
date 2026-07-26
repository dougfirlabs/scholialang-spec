"""Integrity checks for the shared Scholia v0.6.2 Rule-4 fixtures.

These tests intentionally do not import a validator implementation. The
spec lands before downstream ports; implementation repositories consume
the same JSON and assert the semantic expectations there.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]
_SUITE_PATH = _ROOT / "conformance" / "v0.6.2" / "action_recorded.json"
_MANIFEST_PATH = _ROOT / "compatibility-manifest.json"
_EXPECTED_CASE_IDS = {
    "v062-action-recorded-nested-finding",
    "v062-action-recorded-nested-concluding",
    "v062-action-recorded-immediate-sibling-finding",
    "v062-action-recorded-immediate-sibling-concluding",
    "v062-action-recorded-direct-cross-step-finding",
    "v062-action-recorded-indirect-observation-chain",
    "v062-action-recorded-indirect-evidence-chain",
    "v062-action-recorded-goal-closing-concluding",
    "v062-action-recorded-records-result-edge",
    "v062-action-recorded-unrelated-later-finding",
    "v062-action-recorded-order-only-later-finding",
    "v062-action-recorded-next-step-order-only-finding",
    "v062-action-recorded-unclosed-action",
}


def _suite() -> dict:
    return json.loads(_SUITE_PATH.read_text(encoding="utf-8"))


def _trace_root(trace: str) -> ET.Element:
    return ET.fromstring(f"<Scholia>{trace}</Scholia>")


def test_v062_action_recorded_suite_identity_and_coverage() -> None:
    suite = _suite()
    assert suite["schema_version"] == "1.0"
    assert suite["spec_version"] == "0.6.2"
    assert suite["validator_version"] == "0.6.2"
    assert suite["rule"] == "action_recorded"

    cases = suite["cases"]
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids)), "conformance case ids must be unique"
    assert set(ids) == _EXPECTED_CASE_IDS
    assert {case["category"] for case in cases} == {"positive", "negative"}
    assert sum(case["category"] == "positive" for case in cases) == 9
    assert sum(case["category"] == "negative" for case in cases) == 4


def test_v062_action_recorded_traces_are_well_formed_fragments() -> None:
    for case in _suite()["cases"]:
        root = _trace_root(case["trace"])
        steps = root.findall("Step")
        assert steps, f"{case['id']} must contain at least one Step"
        actions = root.findall(".//Action")
        assert actions, f"{case['id']} must exercise at least one Action"

        declared_ids = {
            element.attrib["id"]
            for element in root.iter()
            if element.attrib.get("id")
        }
        assert len(declared_ids) == len(
            [
                element.attrib["id"]
                for element in root.iter()
                if element.attrib.get("id")
            ]
        ), f"{case['id']} contains duplicate ids"

        for edge in case["graph_edges"]:
            assert set(edge) == {"source_id", "target_id", "relation"}
            assert edge["source_id"] in declared_ids
            assert edge["target_id"] in declared_ids
            assert edge["relation"] == "records_result"


def test_v062_action_recorded_expectations_are_rule_local_and_consistent() -> None:
    for case in _suite()["cases"]:
        expects = case["expects"]
        assert expects["rule"] == "action_recorded"
        if case["category"] == "positive":
            assert expects["outcome"] == "pass"
            assert expects["error_count"] == 0
            assert "atom_ids" not in expects
        else:
            assert expects["outcome"] == "fail"
            assert expects["error_count"] == 1
            assert expects["atom_ids"] == ["Act_01"]


def test_records_result_is_the_only_case_with_a_graph_edge() -> None:
    cases = {case["id"]: case for case in _suite()["cases"]}
    graph_case = cases["v062-action-recorded-records-result-edge"]
    assert graph_case["graph_edges"] == [
        {
            "source_id": "F_01",
            "target_id": "Act_01",
            "relation": "records_result",
        }
    ]
    for case_id, case in cases.items():
        if case_id != graph_case["id"]:
            assert case["graph_edges"] == []


def test_compatibility_manifest_registers_the_v062_suite() -> None:
    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    suites = {
        suite["id"]: suite for suite in manifest["conformance_suites"]
    }
    assert suites["v06_2-action-recorded"] == {
        "id": "v06_2-action-recorded",
        "spec_version": "0.6.2",
        "rule": "action_recorded",
        "path": "conformance/v0.6.2/action_recorded.json",
        "description": (
            "Nine positive and four negative Rule-4 cases covering nested "
            "and immediate results, direct and indirect cross-step results, "
            "goal-closing Concluding, records_result graph edges, and strict "
            "provenance failures."
        ),
    }
    assert _ROOT.joinpath(
        suites["v06_2-action-recorded"]["path"]
    ).resolve() == _SUITE_PATH.resolve()
