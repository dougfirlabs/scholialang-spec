"""Spec consistency test — asserts SCHOLIA_v0.6_SPEC.md ↔ scholialang.atoms.

Targets the canonical v0.6 spec (the v0.5 spec is superseded/archived).
The atom catalog is unchanged from v0.5 (32 kinds); v0.6 is additive at
the substrate layer (canonical_id base attribute, registry, prelude).

Four assertions per the spec-authoring hard_constraints[TESTS]:

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
# ``scholialang-spec/tests/test_spec_consistency.py``. In the staging
# layout (this PRD), the path is
# ``opentalon/docs/papers/scholia-v2/spec-stage/scholialang-spec/tests/``.
# In the post-relocation sibling-repo layout, the path is
# ``scholialang-spec/tests/``. The fixtures below resolve both layouts.


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
