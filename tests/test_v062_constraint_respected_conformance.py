"""Integrity checks for the shared Scholia Rule-7 regression fixtures."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]
_SUITE_PATH = _ROOT / "conformance" / "v0.6.2" / "constraint_respected.json"
_MANIFEST_PATH = _ROOT / "compatibility-manifest.json"
_EXPECTED_CASE_IDS = {
    "v062-constraint-bare-null-article-is-not-a-verb",
    "v062-constraint-forbidden-token-needs-word-boundary",
    "v062-constraint-not-retroactive",
    "v062-constraint-never-explicit-violation",
    "v062-constraint-must-not-explicit-violation",
    "v062-constraint-do-not-explicit-violation",
}


def _suite() -> dict:
    return json.loads(_SUITE_PATH.read_text(encoding="utf-8"))


def test_constraint_suite_identity_and_coverage() -> None:
    suite = _suite()
    assert suite["schema_version"] == "1.0"
    assert suite["spec_version"] == "0.6.2"
    assert suite["validator_version"] == "0.7.1"
    assert suite["rule"] == "constraint_respected"
    cases = suite["cases"]
    assert {case["id"] for case in cases} == _EXPECTED_CASE_IDS
    assert len(cases) == len(_EXPECTED_CASE_IDS)
    assert sum(case["category"] == "positive" for case in cases) == 3
    assert sum(case["category"] == "negative" for case in cases) == 3


def test_constraint_traces_are_well_formed_and_exercise_the_rule() -> None:
    for case in _suite()["cases"]:
        root = ET.fromstring(f'<Scholia>{case["trace"]}</Scholia>')
        assert root.findall(".//Constraint"), case["id"]
        assert root.findall(".//Action"), case["id"]
        expects = case["expects"]
        assert expects["rule"] == "constraint_respected"
        if case["category"] == "positive":
            assert expects == {
                "rule": "constraint_respected",
                "outcome": "pass",
                "error_count": 0,
            }
        else:
            assert expects["outcome"] == "fail"
            assert expects["error_count"] == 1
            assert expects["atom_ids"] == ["A_01"]


def test_compatibility_manifest_registers_constraint_suite() -> None:
    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    suites = {suite["id"]: suite for suite in manifest["conformance_suites"]}
    assert suites["v06_2-constraint-respected"] == {
        "id": "v06_2-constraint-respected",
        "spec_version": "0.6.2",
        "rule": "constraint_respected",
        "path": "conformance/v0.6.2/constraint_respected.json",
        "description": (
            "Three positive and three negative Rule-7 cases covering articles, "
            "token boundaries, trace-order scope, and all three forbidden-phrase forms."
        ),
    }
