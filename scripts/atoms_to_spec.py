#!/usr/bin/env python3
"""Generate §2 (Atom Catalog) of SCHOLIA_v0.6_SPEC.md from scholialang.atoms.

This script is the single source of truth for §2 of the canonical spec.
It walks ``scholialang.atoms._ATOM_CLASSES`` alphabetically, groups by
category, and emits markdown to stdout (or to a file via ``--out``).
Wiring it into CI/spec-consistency means impl↔spec drift cannot recur
silently — if a new atom lands in the impl, regenerating §2 surfaces it.

Usage::

    python scripts/atoms_to_spec.py                  # write to stdout
    python scripts/atoms_to_spec.py --out section2.md
    python scripts/atoms_to_spec.py --check spec.md  # assert §2 is current

PRD: rsi-scholia-v0.5-03-spec-docs-reconciliation, story v05-docs-00.
Updated for v0.6: scholia-v0.6-pub-03-spec-authoring, story pub-03-02.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Path to the scholialang source. Two layouts are accepted:
#
# 1. Sibling-repo layout (post-PRD-03-relocation): scholialang-spec and
#    scholialang are siblings under ``~/projects/``. The script sits at
#    ``scholialang-spec/scripts/atoms_to_spec.py`` and looks for
#    ``../../scholialang/src``.
# 2. Staging layout (this PRD's interim location): the script sits at
#    ``opentalon/docs/papers/scholia-v2/spec-stage/scholialang-spec/scripts/``
#    and the package lives at ``opentalon/scholialang/src``.
#
# The default tries (1) first, then (2), then bails.


def _candidate_src_dirs(script_path: Path) -> list[Path]:
    return [
        script_path.resolve().parents[2] / "scholialang" / "src",
        script_path.resolve().parents[6] / "scholialang" / "src",
    ]


def _default_scholialang_src() -> Path:
    for candidate in _candidate_src_dirs(Path(__file__)):
        if candidate.exists():
            return candidate
    # Return the first candidate; the existence check downstream produces
    # the diagnostic.
    return _candidate_src_dirs(Path(__file__))[0]


def _ensure_scholialang_importable(src_dir: Path) -> None:
    if not src_dir.exists():
        attempted = ", ".join(str(p) for p in _candidate_src_dirs(Path(__file__)))
        raise SystemExit(
            f"scholialang src not found at {src_dir!s}. Pass --scholialang-src "
            f"to point at the package containing 'scholialang/atoms.py'. "
            f"Tried: {attempted}."
        )
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


# ── Category groupings (§3 sub-section names from NOTATION_REFERENCE) ─
#
# These mirror the §3a..§3f groupings in NOTATION_REFERENCE.md plus the
# v0.3.1 primitive hooks (Edge/Effect/Ref/Meta) which sit in the
# "schema-reserved primitives" group.

CATEGORY_FOR_ATOM: dict[str, str] = {
    # 3a — reasoning
    "Thinking": "Reasoning",
    "Observation": "Reasoning",
    "Action": "Reasoning",
    # 3b — evidence
    "Hypothesis": "Evidence",
    "Evidence": "Evidence",
    "Finding": "Evidence",
    "Contradiction": "Evidence",
    "Uncertainty": "Evidence",
    "Retract": "Evidence",
    "Concluding": "Evidence",
    # 3c — control
    "Deciding": "Control",
    "Alternative": "Control",
    "Branch": "Control",
    "Loop": "Control",
    "Parallel": "Control",
    # 3d — reference
    "Storing": "Reference",
    "Print": "Reference",
    "Reference": "Reference",
    "Implication": "Reference",
    # 3e — social
    "Handoff": "Social",
    "Question": "Social",
    "Review": "Social",
    # 3f — meta
    "Constraint": "Meta",
    "Goal": "Meta",
    "Confidence": "Meta",
    "EventRef": "Meta",
    "Budget": "Meta",
    "Cost": "Meta",
    # v0.3.1 schema-reserved primitive hooks
    "Edge": "Primitives",
    "Effect": "Primitives",
    "Ref": "Primitives",
    "Meta": "Primitives",
}

CATEGORY_ORDER: tuple[str, ...] = (
    "Reasoning",
    "Evidence",
    "Control",
    "Reference",
    "Social",
    "Meta",
    "Primitives",
)

# One-line semantic per atom — hand-curated. Docstrings on the dataclass
# are too long for the catalog; this map keeps the single-line shape.
# Drift between this map and the dataclass is caught by the spec
# consistency test (PRD-03 story v05-docs-02).
SEMANTIC_FOR_ATOM: dict[str, str] = {
    "Action": "external state change (must produce a Finding).",
    "Alternative": "explicitly rejected option inside a Deciding.",
    "Branch": "legal transition out of a Deciding.",
    "Budget": "declared spending envelope (tokens / actions / wall_clock_ms).",
    "Concluding": "chain-level epistemic close — resolves a Goal via cited atoms.",
    "Confidence": "qualitative or numeric confidence attached to another atom.",
    "Constraint": "hard rule in effect that subsequent decisions must respect.",
    "Contradiction": "two claims that cannot both be true; forces a Deciding.",
    "Cost": "observed expenditure (tokens / dollars / wall_clock_ms).",
    "Deciding": "action commitment branch point — chooses among alternatives.",
    "Edge": "schema-reserved import / dependency edge on an Observation.",
    "Effect": "schema-reserved side-effect kind (io_write / network / subprocess / mutates_state / pure).",
    "EventRef": "pointer to an externally recorded run event.",
    "Evidence": "observation bearing on a Hypothesis (supports / refutes / neutral).",
    "Finding": "conclusion drawn from evidence; evaluates a Hypothesis.",
    "Goal": "target proposition the agent is pursuing; may declare criticality.",
    "Handoff": "pass work to another agent with a named package.",
    "Hypothesis": "explicit conjecture the agent intends to test.",
    "Implication": "long-form forward-link (equivalent to inline IMPLIES:id).",
    "Loop": "iteration over a collection, binding one per-iteration variable.",
    "Meta": "schema-reserved Step-level metadata (e.g. criticality).",
    "Observation": "external input — command output, file contents, query result.",
    "Parallel": "concurrent independent atoms with no specified ordering.",
    "Print": "one-line human-facing summary surfaced to the reader.",
    "Question": "explicit request for external input.",
    "Ref": "schema-reserved generic reference sub-element with type / target.",
    "Reference": "long-form back-link (equivalent to inline REFER:id).",
    "Retract": "revoke a prior Finding (or downgrade-bypass for criticality).",
    "Review": "audit another agent's atom and produce a Finding.",
    "Storing": "persist a named value to trace-local memory for later REFER.",
    "Thinking": "internal deliberation — not observing, not acting.",
    "Uncertainty": "confidence below 1 attached to a finding, hypothesis, or evidence.",
}


def _load_atom_classes(src_dir: Path) -> dict[str, type]:
    _ensure_scholialang_importable(src_dir)
    from scholialang.atoms import _ATOM_CLASSES  # type: ignore[attr-defined]
    return dict(_ATOM_CLASSES)


def render_section_two(atom_classes: dict[str, type]) -> str:
    """Render the §2 markdown block for SCHOLIA_v0.5_SPEC.md."""
    lines: list[str] = []
    lines.append("## §2 Atom catalog")
    lines.append("")
    lines.append(
        f"The Scholia v0.6 closed set is **{len(atom_classes)} atom kinds**, "
        "grouped into seven categories. Names are PascalCase. Adding an "
        "atom kind is a breaking change and requires a spec version bump. "
        "v0.6 is additive at the substrate layer (see §10): the closed set "
        "is unchanged from v0.5; only the base `Atom` grows a universal "
        "`canonical_id` attribute."
    )
    lines.append("")

    by_category: dict[str, list[str]] = {cat: [] for cat in CATEGORY_ORDER}
    missing_category: list[str] = []
    missing_semantic: list[str] = []
    for kind in sorted(atom_classes):
        cat = CATEGORY_FOR_ATOM.get(kind)
        if cat is None:
            missing_category.append(kind)
            continue
        if kind not in SEMANTIC_FOR_ATOM:
            missing_semantic.append(kind)
            continue
        by_category[cat].append(kind)

    if missing_category:
        raise SystemExit(
            f"atoms_to_spec: no category mapped for {missing_category!r} — "
            "add them to CATEGORY_FOR_ATOM before regenerating."
        )
    if missing_semantic:
        raise SystemExit(
            f"atoms_to_spec: no semantic mapped for {missing_semantic!r} — "
            "add them to SEMANTIC_FOR_ATOM before regenerating."
        )

    for cat in CATEGORY_ORDER:
        kinds = by_category[cat]
        if not kinds:
            continue
        lines.append(f"### §2.{CATEGORY_ORDER.index(cat) + 1} {cat}")
        lines.append("")
        for kind in kinds:
            lines.append(f"- **`<{kind}>`** — {SEMANTIC_FOR_ATOM[kind]}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# Sentinel comments delimit the generated §2 block in the spec doc so
# ``--check`` mode can slice it out without confusing the trailing
# editor note. The spec doc must contain a matching pair.
BEGIN_SENTINEL = "<!-- BEGIN_GENERATED:atoms_to_spec -->"
END_SENTINEL = "<!-- END_GENERATED:atoms_to_spec -->"


def extract_section_two(spec_text: str) -> str:
    begin = spec_text.find(BEGIN_SENTINEL)
    if begin == -1:
        raise ValueError(
            f"Could not locate {BEGIN_SENTINEL!r} in spec text — wrap the "
            "generated §2 block in BEGIN/END sentinel comments."
        )
    body_start = begin + len(BEGIN_SENTINEL)
    end = spec_text.find(END_SENTINEL, body_start)
    if end == -1:
        raise ValueError(
            f"Could not locate {END_SENTINEL!r} after {BEGIN_SENTINEL!r}."
        )
    return spec_text[body_start:end].strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    description = (__doc__ or "").splitlines()[0]
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--scholialang-src",
        type=Path,
        default=_default_scholialang_src(),
        help="Path to the scholialang package's src directory.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write generated §2 markdown to this path instead of stdout.",
    )
    parser.add_argument(
        "--check",
        type=Path,
        default=None,
        help="Path to SCHOLIA_v0.5_SPEC.md — assert §2 matches generated output.",
    )
    args = parser.parse_args(argv)

    atom_classes = _load_atom_classes(args.scholialang_src)
    rendered = render_section_two(atom_classes)

    if args.check is not None:
        spec_text = Path(args.check).read_text(encoding="utf-8")
        live = extract_section_two(spec_text)
        if live.strip() != rendered.strip():
            print(
                "atoms_to_spec --check FAILED: live §2 differs from generated. "
                "Regenerate with: python scripts/atoms_to_spec.py "
                f"--out <fragment-path> and splice into {args.check!s}.",
                file=sys.stderr,
            )
            return 1
        print("atoms_to_spec --check OK.")
        return 0

    if args.out is None:
        sys.stdout.write(rendered)
    else:
        args.out.write_text(rendered, encoding="utf-8")
        print(f"Wrote §2 to {args.out!s} ({len(atom_classes)} atoms).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
