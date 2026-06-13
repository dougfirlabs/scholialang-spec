"""Spec consistency test — asserts SCHOLIA_v0.6_SPEC.md ↔ scholialang.atoms.

Targets the canonical v0.6 spec (the v0.5 spec is superseded/archived).
The atom catalog is unchanged from v0.5 (32 kinds); v0.6 is additive at
the substrate layer (canonical_id base attribute, registry, prelude).

Four core consistency assertions:

a) Every atom in scholialang.atoms._ATOM_CLASSES appears in
   SCHOLIA_v0.6_SPEC.md §2.
b) The atom count in §2 matches len(_ATOM_CLASSES) (== 32 at v0.6).
c) atom-card-v0.5.md mentions all 32 atoms.
d) No orphaned atom names appear (e.g. 'Decision' singular shouldn't
   appear in the current spec; it's only legal in the legacy/ doc).

Plus three structural assertions:
e) atoms_index.yaml (v0.6) lists exactly 32 atoms matching the impl.
f) atoms_to_spec --check passes (the generated §2 matches what's in
   the spec doc).
g) notation_reference_gen --check passes (the generated notation-
   reference.md matches what's on disk).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


# ── Path discovery ──────────────────────────────────────────────────
#
# This test file lives at
# ``scholialang-spec/tests/test_spec_consistency.py``. Two layouts are
# resolved by the fixtures below: the canonical sibling-repo layout
# (``scholialang-spec/tests/`` with ``scholialang`` a sibling), and a
# nested-checkout fallback where the spec repo sits several directories
# deep inside a larger tree with ``scholialang`` near that tree's root.


def _spec_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _scholialang_src_candidates() -> list[Path]:
    # Sibling-repo layout: scholialang-spec and scholialang live under
    # ``~/projects/`` as siblings.
    sibling = _spec_repo_root().parent / "scholialang" / "src"
    # Staging layout: scholialang lives at the OT repo root.
    candidates = [sibling]
    if len(_spec_repo_root().parents) > 4:
        candidates.append(_spec_repo_root().parents[4] / "scholialang" / "src")
    return candidates


def _scholialang_src() -> Path:
    for candidate in _scholialang_src_candidates():
        if (candidate / "scholialang" / "atoms.py").exists():
            return candidate
    raise FileNotFoundError(
        "scholialang.atoms not found in any of: "
        + ", ".join(str(p) for p in _scholialang_src_candidates())
    )


def _scripts_dir() -> Path:
    return _spec_repo_root() / "scripts"


@pytest.fixture(scope="module")
def atom_classes() -> dict[str, type]:
    src = _scholialang_src()
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    # Standard import via the package path. dataclass module lookup
    # requires the module to be registered in sys.modules under its
    # qualified name. Do NOT reload — if other tests in the same run
    # already imported scholialang.atoms (the validator tests do, via
    # their own conftest), reloading produces a fresh ``Concluding``
    # class object that breaks ``isinstance(atom, OldConcluding)``
    # checks elsewhere in the suite.
    import importlib
    module = importlib.import_module("scholialang.atoms")
    return dict(module._ATOM_CLASSES)


@pytest.fixture(scope="module")
def spec_text() -> str:
    path = _spec_repo_root() / "docs" / "scholia" / "SCHOLIA_v0.6_SPEC.md"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def atom_card_text() -> str:
    path = _spec_repo_root() / "reference" / "atom-card-v0.5.md"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def atoms_index() -> dict:
    path = _spec_repo_root() / "reference" / "atoms_index.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def notation_ref_text() -> str:
    path = _spec_repo_root() / "reference" / "notation-reference.md"
    return path.read_text(encoding="utf-8")


# ── Helpers ─────────────────────────────────────────────────────────

# `<Action>` style — backtick-wrapped tag references inside markdown.
_ATOM_MENTION_RE = re.compile(r"`<([A-Z][A-Za-z]+)>`")


def _atom_mentions(text: str) -> set[str]:
    return set(_ATOM_MENTION_RE.findall(text))


def _section_two(spec_text: str) -> str:
    begin = spec_text.find("<!-- BEGIN_GENERATED:atoms_to_spec -->")
    end = spec_text.find("<!-- END_GENERATED:atoms_to_spec -->")
    assert begin != -1, "spec doc missing BEGIN sentinel for §2"
    assert end != -1, "spec doc missing END sentinel for §2"
    return spec_text[begin:end]


# ── (a) — every impl atom appears in §2 of the spec doc ─────────────


def test_every_atom_in_impl_appears_in_spec_section_two(
    atom_classes: dict[str, type], spec_text: str
) -> None:
    section_two = _section_two(spec_text)
    mentioned = _atom_mentions(section_two)
    expected = set(atom_classes)
    missing = expected - mentioned
    assert not missing, (
        f"§2 of SCHOLIA_v0.6_SPEC.md is missing impl atoms: "
        f"{sorted(missing)}. Regenerate via "
        f"`python scripts/atoms_to_spec.py --out section2.md` and splice."
    )


# ── (b) — atom count in §2 matches impl ─────────────────────────────


def test_section_two_count_matches_impl(
    atom_classes: dict[str, type], spec_text: str
) -> None:
    section_two = _section_two(spec_text)
    mentioned = _atom_mentions(section_two)
    # Section 2 may also mention <Action> / <Concluding> / etc. as
    # cross-references in the prose; what we care about is the count of
    # *unique impl atoms* mentioned vs. the impl size.
    impl_kinds = set(atom_classes)
    found = mentioned & impl_kinds
    assert len(found) == len(impl_kinds) == 32, (
        f"§2 mentions {len(found)} impl atoms but impl has {len(impl_kinds)} "
        "and v0.6 targets exactly 32."
    )


# ── (c) — atom card mentions all 32 atoms ───────────────────────────


def test_atom_card_mentions_all_atoms(
    atom_classes: dict[str, type], atom_card_text: str
) -> None:
    mentioned = _atom_mentions(atom_card_text)
    expected = set(atom_classes)
    missing = expected - mentioned
    assert not missing, (
        f"atom-card-v0.5.md is missing impl atoms: {sorted(missing)}."
    )


# ── (d) — no orphaned atom names in current canonical surfaces ──────


_ORPHANED_NAMES: tuple[str, ...] = (
    "Decision",       # the singular form has never existed
    "Decisions",      # plural also bogus
    "Conclusion",     # the closing atom is Concluding, not Conclusion
)


@pytest.mark.parametrize("orphan", _ORPHANED_NAMES)
def test_no_orphan_in_canonical_surfaces(
    orphan: str,
    spec_text: str,
    atom_card_text: str,
    notation_ref_text: str,
) -> None:
    # Tag-pattern check: orphan as `<Tag>` in any current canonical
    # surface must not appear. The legacy/ directory is excluded — it
    # preserves the v0.4 draft verbatim and may mention these.
    pattern = f"`<{orphan}>`"
    for label, body in (
        ("SCHOLIA_v0.5_SPEC.md", spec_text),
        ("atom-card-v0.5.md", atom_card_text),
        ("notation-reference.md", notation_ref_text),
    ):
        assert pattern not in body, (
            f"orphan tag {pattern} appears in {label} — "
            "current canonical must not name this atom."
        )


# ── (d2) — rule 8 (goal_declared) agrees with the Concluding table ──
#
# v0.6.1 reconciliation: the goal_declared validator rule names a
# ``status`` on the closing ``<Concluding>``; the ``<Concluding>``
# attribute table must therefore declare ``status`` with a matching
# enum. This asserts the two surfaces agree so the v0.6.0 contradiction
# (rule named a status the table omitted) cannot recur.

_CONCLUDING_STATUS_ENUM: tuple[str, ...] = ("met", "unmet", "partially_met")


def _concluding_attrs(atoms_index: dict) -> dict:
    for atom in atoms_index["atoms"]:
        if atom["kind"] == "Concluding":
            return {a["name"]: a for a in atom.get("attributes", [])}
    raise AssertionError("Concluding atom missing from atoms_index.yaml")


def _rule_eight_text(spec_text: str) -> str:
    # Rule 8 is the ``goal_declared`` bullet in §4.1; slice from its
    # marker to the next numbered rule (``9.``).
    begin = spec_text.find("**`goal_declared`**")
    assert begin != -1, "spec doc missing the goal_declared (rule 8) bullet"
    end = spec_text.find("\n9. ", begin)
    assert end != -1, "could not bound rule 8 before rule 9 in the spec"
    return spec_text[begin:end]


def test_concluding_table_declares_status(atoms_index: dict) -> None:
    attrs = _concluding_attrs(atoms_index)
    assert "status" in attrs, (
        "the <Concluding> attribute table must declare `status` "
        "(v0.6.1) so it agrees with goal_declared (rule 8)."
    )
    status_type = attrs["status"]["type"]
    for value in _CONCLUDING_STATUS_ENUM:
        assert value in status_type, (
            f"<Concluding> status enum is missing {value!r}: {status_type!r}"
        )
    assert attrs["status"].get("required") is False, (
        "<Concluding> status must be OPTIONAL (additive/non-breaking)."
    )


def test_rule8_and_concluding_status_agree(
    atoms_index: dict, spec_text: str
) -> None:
    attrs = _concluding_attrs(atoms_index)
    rule8 = _rule_eight_text(spec_text)
    # Rule 8 must reference a status on the closing Concluding.
    assert "status" in rule8 and "Concluding" in rule8, (
        "goal_declared (rule 8) must name `status` on the closing "
        "<Concluding>."
    )
    # Every value in the Concluding attribute-table enum must appear in
    # rule 8 — the rule cannot allow/expect a value the table omits, nor
    # vice versa, for the Concluding enum.
    status_type = attrs["status"]["type"]
    table_values = {v.strip() for v in status_type.split("|")}
    assert table_values == set(_CONCLUDING_STATUS_ENUM), (
        f"<Concluding> status enum drifted: {sorted(table_values)}"
    )
    for value in _CONCLUDING_STATUS_ENUM:
        assert value in rule8, (
            f"rule 8 omits the <Concluding> status value {value!r} that the "
            "attribute table declares — the two surfaces disagree."
        )


# ── (e) — atoms_index.yaml lists exactly 32 atoms matching impl ─────


def test_atoms_index_matches_impl(
    atom_classes: dict[str, type], atoms_index: dict
) -> None:
    yaml_kinds = {a["kind"] for a in atoms_index["atoms"]}
    expected = set(atom_classes)
    assert yaml_kinds == expected, (
        f"atoms_index.yaml drift vs scholialang.atoms: "
        f"missing in YAML: {sorted(expected - yaml_kinds)}, "
        f"extra in YAML: {sorted(yaml_kinds - expected)}."
    )
    assert atoms_index["total_atoms"] == len(expected) == 32, (
        f"atoms_index.total_atoms={atoms_index['total_atoms']} but "
        f"len(_ATOM_CLASSES)={len(expected)}; both must be 32 at v0.6."
    )


# ── (f) — atoms_to_spec --check passes ──────────────────────────────


def test_atoms_to_spec_check_passes() -> None:
    spec_path = _spec_repo_root() / "docs" / "scholia" / "SCHOLIA_v0.6_SPEC.md"
    script = _scripts_dir() / "atoms_to_spec.py"
    result = subprocess.run(
        [sys.executable, str(script),
         "--scholialang-src", str(_scholialang_src()),
         "--check", str(spec_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"atoms_to_spec --check FAILED:\nstdout: {result.stdout!r}\n"
        f"stderr: {result.stderr!r}"
    )


# ── (g) — notation_reference_gen --check passes ─────────────────────


def test_notation_reference_gen_check_passes() -> None:
    ref_path = _spec_repo_root() / "reference" / "notation-reference.md"
    script = _scripts_dir() / "notation_reference_gen.py"
    result = subprocess.run(
        [sys.executable, str(script), "--check", str(ref_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"notation_reference_gen --check FAILED:\nstdout: {result.stdout!r}\n"
        f"stderr: {result.stderr!r}"
    )
