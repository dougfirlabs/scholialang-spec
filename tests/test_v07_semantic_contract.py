"""Producer-side integrity tests for the PROPOSED v0.7 semantic contract.

Like ``tests/test_v062_action_recorded_conformance.py``, this module
does **not** import a validator or any implementation package: the spec
lands before downstream ports, and implementation repositories execute
the same JSON expectations. What is validated here is the *description
of expected outcomes* — index/schema/fixture integrity, index-driven
generation determinism, positive/negative coverage inventory, and
byte-exact preservation of the historical 32-kind surfaces — not
pretend execution of the semantic validator.

Covered nodes (fixed names, part of the producer contract):

1. test_current_catalog_is_legacy_union_three
2. test_current_fields_and_requiredness_are_explicit
3. test_semantic_case_ids_and_coverage_are_exact
4. test_parse_and_validate_expectations_are_distinct
5. test_legacy_corpus_and_canonical_goldens_are_unchanged
6. test_index_generation_requires_no_core_import
7. test_generated_current_reference_matches_index
8. test_unknown_or_duplicate_catalog_entries_fail
9. test_mismatched_generated_text_fails
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _scripts_dir() -> Path:
    return _repo_root() / "scripts"


NEW_KINDS: frozenset[str] = frozenset({"Map", "Event", "Task"})
NEW_KIND_PREFIX: dict[str, str] = {
    "Map": "Map_", "Event": "Event_", "Task": "Task_",
}


@pytest.fixture(scope="module")
def legacy_index() -> dict:
    path = _repo_root() / "reference" / "atoms_index.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current_index() -> dict:
    path = _repo_root() / "reference" / "v0.7" / "atoms_index.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def suite() -> dict:
    path = _repo_root() / "conformance" / "v0.7" / "semantic_atoms.json"
    return json.loads(path.read_text(encoding="utf-8"))


# ── (1) current catalog = legacy ∪ {Map, Event, Task} ────────────────


def test_current_catalog_is_legacy_union_three(
    legacy_index: dict, current_index: dict
) -> None:
    legacy_kinds = {a["kind"] for a in legacy_index["atoms"]}
    current_kinds = {a["kind"] for a in current_index["atoms"]}
    assert legacy_kinds == current_kinds - NEW_KINDS, (
        "the current catalog must be exactly the legacy catalog plus the "
        f"three proposed kinds; unexpected delta: "
        f"{sorted((current_kinds - NEW_KINDS) ^ legacy_kinds)}"
    )
    assert NEW_KINDS <= current_kinds
    assert len(legacy_kinds) == legacy_index["total_atoms"] == 32
    assert len(current_kinds) == current_index["total_atoms"] == 35
    assert current_index["legacy_atoms"] == 32
    assert set(current_index["new_atoms"]) == NEW_KINDS
    # The two version axes stay distinct and stay candidates.
    assert current_index["grammar_version"] == "0.7.0"
    assert current_index["package_version"] == "0.7.3"
    assert current_index["status"] == "proposed"
    # No duplicate kinds anywhere.
    kinds_list = [a["kind"] for a in current_index["atoms"]]
    assert len(kinds_list) == len(set(kinds_list))


# ── (2) explicit fields and requiredness ─────────────────────────────


def test_current_fields_and_requiredness_are_explicit(
    legacy_index: dict, current_index: dict, suite: dict
) -> None:
    known_rules = set(suite["rule_codes"])
    for atom in current_index["atoms"]:
        kind = atom["kind"]
        names = []
        for attr in atom.get("attributes", []):
            assert isinstance(attr["name"], str) and attr["name"], (
                f"{kind}: attribute name must be a nonempty string — the "
                f"legacy index's unquoted `on` (YAML boolean) bug must not "
                f"recur: {attr!r}"
            )
            assert isinstance(attr.get("required"), bool), (
                f"{kind}.{attr['name']}: requiredness must be an explicit "
                "boolean."
            )
            names.append(attr["name"])
        assert len(names) == len(set(names)), f"{kind}: duplicate attributes"

    # The three documentation parity repairs are present and recorded.
    by_kind = {a["kind"]: a for a in current_index["atoms"]}
    obs_attrs = {a["name"] for a in by_kind["Observation"]["attributes"]}
    assert "fingerprint" in obs_attrs
    for kind in ("Uncertainty", "Confidence"):
        attrs = {a["name"] for a in by_kind[kind]["attributes"]}
        assert "on" in attrs, f"{kind}: string attribute 'on' missing"
        assert True not in attrs, f"{kind}: boolean-True attr name leaked"
    corrections = {
        (c["kind"], c["attribute"])
        for c in current_index["legacy_field_corrections"]
    }
    assert corrections == {
        ("Observation", "fingerprint"),
        ("Uncertainty", "on"),
        ("Confidence", "on"),
    }

    # New kinds: required id with kind-matching prefix, rejected children,
    # explicit body requirement, and per-attribute reference policy.
    for kind in sorted(NEW_KINDS):
        atom = by_kind[kind]
        policy = atom["id_policy"]
        assert policy["required"] is True
        assert policy["prefix"] == NEW_KIND_PREFIX[kind]
        assert policy["suffix_charset"] == "[A-Za-z0-9_]+"
        assert atom["children"] == "rejected"
        assert isinstance(atom["body_required"], bool)
        attrs = {a["name"]: a for a in atom["attributes"]}
        assert attrs["id"]["required"] is True, (
            f"{kind}: the per-kind override must make id required."
        )
        for name, attr in attrs.items():
            if attr.get("type") == "local-ref":
                assert attr.get("ref_kinds"), (
                    f"{kind}.{name}: local-ref attributes must declare "
                    "their permitted target kinds."
                )
            if attr.get("opaque"):
                assert attr.get("type") == "string"
        rules = set(atom["applies_rules"])
        unknown = rules - known_rules
        assert not unknown, (
            f"{kind}: applies_rules not declared by the conformance "
            f"suite's rule_codes: {sorted(unknown)}"
        )

    # Legacy entries keep their legacy requiredness (base id stays
    # optional for all 32; the base_attributes table still says so).
    base = {a["name"]: a for a in current_index["base_attributes"]}
    assert base["id"]["required"] is False
    assert base["canonical_id"]["required"] is False
    legacy_by_kind = {a["kind"]: a for a in legacy_index["atoms"]}
    for kind, legacy_atom in legacy_by_kind.items():
        current_attrs = {
            a["name"]: a.get("required")
            for a in by_kind[kind].get("attributes", [])
        }
        for attr in legacy_atom.get("attributes", []):
            name = attr["name"]
            if not isinstance(name, str):
                continue  # the legacy boolean-`on` rows, corrected above
            assert current_attrs.get(name) == attr.get("required"), (
                f"{kind}.{name}: legacy requiredness changed in the "
                "current projection."
            )


# ── (3) exact case IDs and coverage inventory ────────────────────────

# Pinned inventory: the suite may grow by an explicit pin update, but
# discovering fewer fixtures must never shrink the required tests
# silently (consumer gates parametrize from these numbers).
EXPECTED_TOTAL = 106
EXPECTED_POSITIVE = 35
EXPECTED_NEGATIVE = 71
EXPECTED_FAMILIES = {
    "catalog": {"positive": 3, "negative": 7},
    "map_types": {"positive": 9, "negative": 19},
    "event_identity": {"positive": 6, "negative": 9},
    "task_declaration": {"positive": 6, "negative": 6},
    "relation_legality": {"positive": 6, "negative": 19},
    "local_ids": {"positive": 1, "negative": 6},
    "canonical_ids": {"positive": 3, "negative": 2},
    "serialization": {"positive": 1, "negative": 3},
}

# Load-bearing single cases whose absence would silently drop a
# contract row from the fixture matrix.
REQUIRED_CASE_IDS = (
    "v07-catalog-all-three-new-kinds-with-legacy",
    "v07-catalog-event-and-eventref-coexist",
    "v07-catalog-new-kind-under-legacy-profile",
    "v07-catalog-unknown-kind",
    "v07-map-empty-atom-ref",
    "v07-map-populated-integer-bounds",
    "v07-map-bool-as-integer",
    "v07-map-integer-out-of-range",
    "v07-map-entries-duplicate-keys-embedded-json",
    "v07-map-entries-encoded-string-in-json",
    "v07-map-self-ref",
    "v07-event-same-prose-different-occurrence-ids",
    "v07-event-duplicate-occurrence-pair",
    "v07-event-naive-timestamp",
    "v07-task-satisfied-with-evidence",
    "v07-task-runtime-status-substituted",
    "v07-task-satisfied-without-evidence",
    "v07-task-evidence-wrong-kind",
    "v07-relations-forward-references",
    "v07-relations-opaque-refs-stay-opaque",
    "v07-ids-duplicate-new-legacy",
    "v07-canonical-map-insertion-order-not-identity",
    "v07-canonical-event-timestamp-excluded",
    "v07-canonical-claimed-mismatch",
    "v07-serialization-roundtrip-all-new-kinds",
    "v07-serialization-children-on-new-kind",
)

_FORMATS = {"xml", "json", "yaml", "dict"}


def test_semantic_case_ids_and_coverage_are_exact(suite: dict) -> None:
    cases = suite["cases"]
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case ids"
    missing = set(REQUIRED_CASE_IDS) - set(ids)
    assert not missing, f"required cases missing: {sorted(missing)}"

    coverage = suite["coverage"]
    positives = [c for c in cases if c["category"] == "positive"]
    negatives = [c for c in cases if c["category"] == "negative"]
    assert len(cases) == coverage["total_cases"] == EXPECTED_TOTAL
    assert len(positives) == coverage["positive"] == EXPECTED_POSITIVE
    assert len(negatives) == coverage["negative"] == EXPECTED_NEGATIVE

    recount: dict[str, dict[str, int]] = {}
    for c in cases:
        fam = recount.setdefault(c["family"], {"positive": 0, "negative": 0})
        fam[c["category"]] += 1
    assert recount == coverage["families"] == EXPECTED_FAMILIES

    for c in cases:
        assert c["format"] in _FORMATS, c["id"]
        if c["format"] == "dict":
            assert isinstance(c["payload"], dict), c["id"]
        else:
            assert isinstance(c["payload"], str), c["id"]
        assert set(c["kinds"]) <= NEW_KINDS, c["id"]
        assert c["category"] in ("positive", "negative"), c["id"]
        assert c["description"].strip(), c["id"]
        if "identity" in c:
            identity = c["identity"]
            assert identity["relation"] in ("equal", "distinct"), c["id"]
            assert ("atoms" in identity) != ("cross_trace_atom" in identity), (
                f"{c['id']}: identity names either same-trace atoms or one "
                "cross-trace atom, not both"
            )
        if "payload_b" in c:
            assert c["identity"].get("cross_trace_atom"), c["id"]


# ── (4) parse-vs-validate expectations stay distinct ─────────────────


def test_parse_and_validate_expectations_are_distinct(suite: dict) -> None:
    rule_codes = suite["rule_codes"]
    phases_seen = set()
    for c in suite["cases"]:
        expects = c["expects"]
        if c["category"] == "positive":
            assert expects["outcome"] == "pass", c["id"]
            assert "phase" not in expects and "rule" not in expects, (
                f"{c['id']}: positive cases declare no failure phase/rule"
            )
            assert expects["roundtrip"] is True, c["id"]
            assert expects["canonical_json_stable"] is True, c["id"]
            continue
        assert expects["outcome"] == "fail", c["id"]
        phase = expects["phase"]
        assert phase in ("parse", "validate"), c["id"]
        phases_seen.add(phase)
        rule = expects["rule"]
        assert rule in rule_codes, f"{c['id']}: undeclared rule {rule!r}"
        assert rule_codes[rule]["phase"] == phase, (
            f"{c['id']}: case phase {phase!r} contradicts the declared "
            f"phase of rule {rule!r} — a parse failure must never be "
            "translated into a generic successful negative validate case."
        )
        mentions = expects["diagnostic_must_mention"]
        assert mentions and all(
            isinstance(m, str) and m for m in mentions
        ), c["id"]
    assert phases_seen == {"parse", "validate"}, (
        "the suite must exercise both failure phases explicitly"
    )
    # No rule may claim both phases (the two dispatch paths stay distinct).
    for rule, meta in rule_codes.items():
        assert meta["phase"] in ("parse", "validate"), rule


# ── (5) historical surfaces preserved byte-identically ───────────────

# SHA-256 pins of the frozen legacy surfaces. These bytes predate the
# v0.7 proposal and MUST NOT change under it; bumping a pin requires an
# explicit, reviewed decision.
_LEGACY_SHA256: dict[str, str] = {
    "reference/atoms_index.yaml":
        "757781b220836a93359596d9ed66bbaa9239937ed8bcd8d28392cc9b58e7a69e",
    "reference/notation-reference.md":
        "ae3c08f950046a06f1865365a96528371b050375e3ef906dc855c5793d3e078f",
    "reference/atom-card-v0.5.md":
        "09f9b38a667c0112ac5f668862423e534b0e10ca6e614a3f00733f203c89aa99",
    "docs/scholia/SCHOLIA_v0.6_SPEC.md":
        "7495b231c6c05e570a42d9f49bfb4c2223fe922656c58093591ef6077f5c64f8",
    "conformance/v0.6.2/action_recorded.json":
        "61b5fb9db03c9f3999028d32b614129f28925b26d566d4a165d1a9ca061620b5",
    "conformance/v0.6.2/constraint_respected.json":
        "57fc2683f8822467f4ef7eb6e1524c874468347a17590a6bb357a2fb3587ed54",
    "tests/fixtures/fingerprint/manifest.yaml":
        "387c72583e5fc9906d4b85b875722e3482f4280adab05d981d541bdb476400eb",
}


def test_legacy_corpus_and_canonical_goldens_are_unchanged() -> None:
    root = _repo_root()
    for rel, expected in _LEGACY_SHA256.items():
        digest = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        assert digest == expected, (
            f"{rel} changed under the v0.7 proposal — historical surfaces "
            "must stay byte-identical."
        )
    manifest = json.loads(
        (root / "compatibility-manifest.json").read_text(encoding="utf-8")
    )
    goldens = manifest["golden_records"]
    assert [g["id"] for g in goldens] == [
        "v06-canonical-id-basic",
        "v06-goal-close-via-finding-status",
        "v06_1-concluding-status-met",
    ], "golden records reordered/removed — the manifest is append-only"
    assert all(g["frozen"] for g in goldens[:2])
    suites = {s["id"]: s for s in manifest["conformance_suites"]}
    for legacy_id in ("v06_2-action-recorded", "v06_2-constraint-respected"):
        assert legacy_id in suites
    # Required legacy corpus sizes (13 action / 6 constraint / 6
    # fingerprint) stay exact.
    action = json.loads(
        (root / "conformance/v0.6.2/action_recorded.json").read_text()
    )
    constraint = json.loads(
        (root / "conformance/v0.6.2/constraint_respected.json").read_text()
    )
    assert len(action["cases"]) == 13
    assert len(constraint["cases"]) == 6
    fingerprint_dir = root / "tests" / "fixtures" / "fingerprint"
    fixtures = sorted(
        p.relative_to(fingerprint_dir).as_posix()
        for p in fingerprint_dir.glob("*/*.xml")
    )
    assert len(fixtures) == 6, fixtures


# ── (6) index-driven generation needs no implementation ──────────────


def _poisoned_env(tmp_path: Path) -> dict[str, str]:
    """Environment where importing ``scholialang`` fails loudly."""
    poison = tmp_path / "poison" / "scholialang"
    poison.mkdir(parents=True)
    (poison / "__init__.py").write_text(
        "raise ImportError('index-driven generation must not import the "
        "implementation')\n",
        encoding="utf-8",
    )
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(poison.parent)
    return env


def test_index_generation_requires_no_core_import(tmp_path: Path) -> None:
    env = _poisoned_env(tmp_path)
    index = _repo_root() / "reference" / "v0.7" / "atoms_index.yaml"
    out = tmp_path / "section2.md"
    result = subprocess.run(
        [sys.executable, str(_scripts_dir() / "atoms_to_spec.py"),
         "--index", str(index), "--out", str(out)],
        capture_output=True, text=True, env=env, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "35 atom kinds" in out.read_text(encoding="utf-8")

    ref_out = tmp_path / "notation-reference.md"
    result = subprocess.run(
        [sys.executable, str(_scripts_dir() / "notation_reference_gen.py"),
         "--index", str(index), "--out", str(ref_out)],
        capture_output=True, text=True, env=env, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "35 atoms" in ref_out.read_text(encoding="utf-8")


def test_conflicting_generator_source_options_fail(tmp_path: Path) -> None:
    index = _repo_root() / "reference" / "v0.7" / "atoms_index.yaml"
    result = subprocess.run(
        [sys.executable, str(_scripts_dir() / "atoms_to_spec.py"),
         "--index", str(index), "--scholialang-src", str(tmp_path)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "mutually exclusive" in result.stderr


# ── (7) generated current references match the index ─────────────────


def test_generated_current_reference_matches_index() -> None:
    index = _repo_root() / "reference" / "v0.7" / "atoms_index.yaml"
    spec = _repo_root() / "docs" / "scholia" / "SCHOLIA_v0.7_SPEC.md"
    ref = _repo_root() / "reference" / "v0.7" / "notation-reference.md"
    for script, args in (
        ("atoms_to_spec.py", ["--index", str(index), "--check", str(spec)]),
        ("notation_reference_gen.py",
         ["--index", str(index), "--check", str(ref)]),
    ):
        result = subprocess.run(
            [sys.executable, str(_scripts_dir() / script), *args],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, (
            f"{script} --check failed:\nstdout: {result.stdout!r}\n"
            f"stderr: {result.stderr!r}"
        )


# ── (8) bad catalogs are hard failures ───────────────────────────────


def _run_index_mode(index_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_scripts_dir() / "atoms_to_spec.py"),
         "--index", str(index_path)],
        capture_output=True, text=True, check=False,
    )


def test_unknown_or_duplicate_catalog_entries_fail(tmp_path: Path) -> None:
    good = yaml.safe_load(
        (_repo_root() / "reference" / "v0.7" / "atoms_index.yaml")
        .read_text(encoding="utf-8")
    )

    unknown_cat = json.loads(json.dumps(good))
    unknown_cat["atoms"][0]["category"] = "Vibes"
    duplicate = json.loads(json.dumps(good))
    duplicate["atoms"].append(dict(duplicate["atoms"][0]))
    duplicate["total_atoms"] = len(duplicate["atoms"])
    wrong_count = json.loads(json.dumps(good))
    wrong_count["total_atoms"] = 99
    malformed = {"atoms": "not-a-list", "total_atoms": 1}
    missing_semantic = json.loads(json.dumps(good))
    del missing_semantic["atoms"][0]["semantic"]

    scenarios = {
        "unknown-category": (unknown_cat, "unknown category"),
        "duplicate-kind": (duplicate, "duplicate kind"),
        "wrong-count": (wrong_count, "total_atoms"),
        "malformed-schema": (malformed, "atoms"),
        "missing-semantic": (missing_semantic, "semantic"),
    }
    for name, (payload, needle) in scenarios.items():
        bad = tmp_path / f"{name}.yaml"
        bad.write_text(yaml.safe_dump(payload), encoding="utf-8")
        result = _run_index_mode(bad)
        assert result.returncode != 0, f"{name}: bad catalog was accepted"
        assert needle in result.stderr, (
            f"{name}: diagnostic {result.stderr!r} lacks {needle!r}"
        )


# ── (9) generated-text drift is a hard failure ───────────────────────


def test_mismatched_generated_text_fails(tmp_path: Path) -> None:
    index = _repo_root() / "reference" / "v0.7" / "atoms_index.yaml"

    spec_text = (
        _repo_root() / "docs" / "scholia" / "SCHOLIA_v0.7_SPEC.md"
    ).read_text(encoding="utf-8")
    tampered_spec = tmp_path / "tampered_spec.md"
    assert "## §2 Atom catalog" in spec_text
    tampered_spec.write_text(
        spec_text.replace("## §2 Atom catalog", "## §2 Atom catalogue", 1),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(_scripts_dir() / "atoms_to_spec.py"),
         "--index", str(index), "--check", str(tampered_spec)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0, "tampered §2 passed --check"

    ref_text = (
        _repo_root() / "reference" / "v0.7" / "notation-reference.md"
    ).read_text(encoding="utf-8")
    tampered_ref = tmp_path / "tampered_ref.md"
    tampered_ref.write_text(
        ref_text.replace("### `<Task>`", "### `<Job>`", 1),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(_scripts_dir() / "notation_reference_gen.py"),
         "--index", str(index), "--check", str(tampered_ref)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0, "tampered notation reference passed --check"
