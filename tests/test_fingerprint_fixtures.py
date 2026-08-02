"""Fingerprint fixture-corpus test — exercises the executable NOTATION layer.

Covers the proposed additive ``fingerprint=`` attribute
(``docs/scholia/FINGERPRINT.md``) at the layer this repo can execute today
(no source access, no 52X-B2 digest):

  a) manifest ↔ files: every fixture / source named in manifest.yaml exists,
     and every fixture file on disk is listed in the manifest.
  b) well-formedness: each trace's fingerprint values match (or, for the
     malformed negative, violate) ``well_formed_regex`` exactly as the
     manifest's ``notation_valid`` flag declares.
  c) fingerprint-requires-location: every atom carrying ``fingerprint=`` also
     carries ``location=`` (spec §3.3).
  d) ignore-if-absent / non-load-bearing: stripping every ``fingerprint=``
     attribute yields a trace that PARSES and VALIDATES CLEAN under the
     PUBLISHED scholialang v0.6 validator — the older-validator-tolerance
     guarantee (spec §4.1). This holds for the negatives too, because their
     only defect lives in the fingerprint layer.

The consumer-layer verdicts (verifies / rebinds / span_mismatch / stale) are
NOT executed here — they need 52X-B2's digest definition and a source tree;
the manifest declares them as intent. See the fixtures README.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "fingerprint"

# ` fingerprint="..."` wire attribute.
_FP_RE = re.compile(r'fingerprint="([^"]*)"')
# A location-bearing element carrying a fingerprint, to assert location present.
_FP_ELEM_RE = re.compile(r"<\w+\b[^>]*\bfingerprint=\"[^\"]*\"[^>]*>")


def _spec_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _scholialang_src() -> Path:
    sibling = _spec_repo_root().parent / "scholialang" / "src"
    if (sibling / "scholialang" / "atoms.py").exists():
        return sibling
    raise FileNotFoundError(f"scholialang.atoms not found at {sibling}")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load((FIXTURES / "manifest.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def scholialang():
    src = _scholialang_src()
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    import importlib

    return importlib.import_module("scholialang")


# ── (a) manifest ↔ files ────────────────────────────────────────────


def test_manifest_and_files_agree(manifest: dict) -> None:
    listed_traces = set()
    for fx in manifest["fixtures"]:
        trace = FIXTURES / fx["trace"]
        assert trace.exists(), f"manifest names missing trace {fx['trace']}"
        listed_traces.add(trace.resolve())
        src = fx.get("source")
        if src:
            assert (FIXTURES / src).exists(), f"missing source {src}"

    on_disk = {p.resolve() for p in FIXTURES.glob("*/*.xml")}
    unlisted = on_disk - listed_traces
    assert not unlisted, f"fixture files not in manifest: {sorted(unlisted)}"


# ── (b) well-formedness matches the manifest's notation_valid flag ──


def test_well_formedness_matches_manifest(manifest: dict) -> None:
    wf = re.compile(manifest["well_formed_regex"])
    for fx in manifest["fixtures"]:
        text = (FIXTURES / fx["trace"]).read_text(encoding="utf-8")
        values = _FP_RE.findall(text)
        all_well_formed = all(wf.match(v) for v in values)
        if fx["notation_valid"]:
            assert all_well_formed, (
                f"{fx['name']}: manifest says notation_valid but a fingerprint "
                f"value is malformed: {values}"
            )
        else:
            assert not all_well_formed, (
                f"{fx['name']}: manifest says NOT notation_valid but every "
                f"fingerprint value is well-formed: {values}"
            )


# ── (c) fingerprint requires location (spec §3.3) ───────────────────


def test_fingerprint_requires_location() -> None:
    for trace in FIXTURES.glob("*/*.xml"):
        for elem in _FP_ELEM_RE.findall(trace.read_text(encoding="utf-8")):
            assert "location=" in elem, (
                f"{trace.name}: atom carries fingerprint but no location: {elem}"
            )


# ── (d) ignore-if-absent: strip fingerprint → validates clean ───────


def test_stripping_fingerprint_validates_clean(manifest: dict, scholialang) -> None:
    parse = scholialang.parse
    validate = scholialang.validate
    for fx in manifest["fixtures"]:
        raw = (FIXTURES / fx["trace"]).read_text(encoding="utf-8")
        stripped = _FP_RE.sub("", raw)
        # sanity: no fingerprint *attribute* survives (prose mentions in
        # comments are fine — the parser ignores comment bodies).
        assert _FP_RE.search(stripped) is None, fx["name"]
        steps = parse(stripped)
        result = validate(steps)
        assert result.ok, (
            f"{fx['name']}: stripped trace should validate clean under the "
            f"published validator, got errors: "
            f"{[(e.rule, e.message) for e in result.errors]}"
        )
