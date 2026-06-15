#!/usr/bin/env python3
"""Generate ``reference/notation-reference.md`` from ``atoms_index.yaml``.

The YAML index is the source of truth for the per-atom catalog. This
script emits one markdown section per atom (32 sections in v0.6),
preserving the §2 category groupings from the canonical spec.

Usage::

    python scripts/notation_reference_gen.py
    python scripts/notation_reference_gen.py --check reference/notation-reference.md

``--check`` re-renders from YAML and asserts the on-disk file matches.

Introduced for the v0.5 spec-docs reconciliation; updated for v0.6.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_INDEX = Path(__file__).resolve().parents[1] / "reference" / "atoms_index.yaml"
_DEFAULT_OUT = Path(__file__).resolve().parents[1] / "reference" / "notation-reference.md"

CATEGORY_ORDER: tuple[str, ...] = (
    "Reasoning",
    "Evidence",
    "Control",
    "Reference",
    "Social",
    "Meta",
    "Primitives",
)

CATEGORY_BLURB: dict[str, str] = {
    "Reasoning": "Atoms that describe the agent's reasoning posture — what it's thinking, observing, or doing.",
    "Evidence":  "Atoms that carry epistemic claims — hypotheses, evidence, findings, and the closure atom.",
    "Control":   "Atoms that mark control-flow shape — decisions, branches, loops, parallel sub-traces.",
    "Reference": "Atoms that link, store, or surface — long-form back-/forward-links and named-value memory.",
    "Social":    "Atoms that involve another agent — handoff, question, review.",
    "Meta":      "Atoms that carry trace-level metadata — goals, constraints, budgets, costs, confidence.",
    "Primitives": "v0.3.1 schema-reserved hooks — edges, effects, refs, and step-level metadata.",
}


def _slug(kind: str) -> str:
    return kind.lower()


def _format_attr_row(attr: dict[str, Any]) -> str:
    required = "yes" if attr.get("required") else "no"
    notes = attr.get("notes", "").replace("|", "\\|")
    return (
        f"| `{attr['name']}` | {attr['type']} | {required} | {notes} |"
    )


def _format_example(example: str) -> str:
    cleaned = textwrap.dedent(example).strip("\n")
    return f"```xml\n{cleaned}\n```"


def _format_atom(atom: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"### `<{atom['kind']}>` — {atom['semantic']}")
    lines.append("")
    lines.append(f"**Category:** §2 {atom['category']} &nbsp;·&nbsp; "
                 f"**Slug:** `{_slug(atom['kind'])}` &nbsp;·&nbsp; "
                 f"**Body:** {atom['body']}.")
    lines.append("")

    attrs = atom.get("attributes", [])
    if attrs:
        lines.append("| Attribute | Type | Required | Notes |")
        lines.append("|---|---|---|---|")
        for a in attrs:
            lines.append(_format_attr_row(a))
        lines.append("")
    else:
        lines.append("_No attributes._")
        lines.append("")

    example = atom.get("example")
    if example:
        lines.append("**Example:**")
        lines.append("")
        lines.append(_format_example(example))
        lines.append("")

    rules = atom.get("applies_rules", []) or []
    if rules:
        formatted = ", ".join(f"`{r}`" for r in rules)
        lines.append(f"**Validator rules:** {formatted} (see §4 of the canonical spec).")
    else:
        lines.append("**Validator rules:** none specific to this atom (general well-formedness applies).")
    lines.append("")
    return "\n".join(lines)


def render(index: dict[str, Any]) -> str:
    atoms = list(index.get("atoms", []))
    by_cat: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORY_ORDER}
    for atom in atoms:
        cat = atom["category"]
        if cat not in by_cat:
            raise SystemExit(
                f"notation_reference_gen: unknown category {cat!r} for "
                f"atom {atom.get('kind')!r}; add it to CATEGORY_ORDER."
            )
        by_cat[cat].append(atom)

    version = index.get("version")
    lines: list[str] = []
    lines.append(f"# Scholia v{version} — Notation Reference")
    lines.append("")
    lines.append("**Status:** Canonical, derived from "
                 f"`reference/atoms_index.yaml` (v{version}).")
    lines.append("**Spec:** see "
                 f"[`docs/scholia/{index.get('spec')}`](../docs/scholia/{index.get('spec')}) "
                 f"for the full v{version} specification.")
    lines.append("")
    lines.append(
        f"This document lists the {index.get('total_atoms')} atoms in the "
        f"Scholia v{version} closed set with their attributes, body "
        "conventions, examples, and applicable validator rules. One section "
        "per atom; atoms within a category are alphabetical."
    )
    lines.append("")
    lines.append(
        "> **Generated file.** Edit `atoms_index.yaml` and regenerate via "
        "`python scripts/notation_reference_gen.py`. The consistency test "
        "in `tests/test_spec_consistency.py` enforces this on PR."
    )
    lines.append("")

    # Universal base attributes (carried by every atom; not repeated
    # per-kind below). Rendered from the ``base_attributes`` key when
    # present so the v0.6 ``canonical_id`` surfaces once, universally.
    base_attrs = list(index.get("base_attributes", []) or [])
    if base_attrs:
        lines.append("## Base attributes (every atom)")
        lines.append("")
        lines.append(
            "These attributes are inherited by every atom kind below and are "
            "not repeated in the per-kind tables."
        )
        lines.append("")
        lines.append("| Attribute | Type | Required | Notes |")
        lines.append("|---|---|---|---|")
        for a in base_attrs:
            lines.append(_format_attr_row(a))
        lines.append("")

    # Table of contents
    lines.append("## Table of contents")
    lines.append("")
    for cat in CATEGORY_ORDER:
        kinds = by_cat[cat]
        if not kinds:
            continue
        anchored = " · ".join(
            f"[`<{a['kind']}>`](#{_slug(a['kind'])})" for a in kinds
        )
        lines.append(f"- **{cat}** — {anchored}")
    lines.append("")

    # Per-category sections
    for idx, cat in enumerate(CATEGORY_ORDER, start=1):
        kinds = by_cat[cat]
        if not kinds:
            continue
        lines.append(f"## §{idx} {cat}")
        lines.append("")
        lines.append(CATEGORY_BLURB[cat])
        lines.append("")
        for atom in kinds:
            lines.append(_format_atom(atom))

    lines.append("---")
    lines.append("")
    lines.append(
        f"*Generated by `scripts/notation_reference_gen.py` from "
        f"`reference/atoms_index.yaml` (Scholia v{version}). "
        "If you found a drift between this doc and the canonical spec or "
        "the reference implementation, file an issue against `scholialang-spec`.*"
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    description = (__doc__ or "").splitlines()[0]
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--index",
        type=Path,
        default=_DEFAULT_INDEX,
        help="Path to atoms_index.yaml (default: ../reference/atoms_index.yaml).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        help="Path to write generated notation-reference.md (default: ../reference/notation-reference.md).",
    )
    parser.add_argument(
        "--check",
        type=Path,
        default=None,
        help="Re-render and assert the file at this path matches the generated output.",
    )
    args = parser.parse_args(argv)

    if not args.index.exists():
        raise SystemExit(f"atoms_index.yaml not found at {args.index!s}.")
    index = yaml.safe_load(args.index.read_text(encoding="utf-8"))
    rendered = render(index)

    if args.check is not None:
        live = args.check.read_text(encoding="utf-8")
        if live.strip() != rendered.strip():
            print(
                f"notation_reference_gen --check FAILED: live "
                f"{args.check!s} differs from generated. "
                f"Re-run: python scripts/notation_reference_gen.py",
                file=sys.stderr,
            )
            return 1
        print("notation_reference_gen --check OK.")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(f"Wrote notation reference to {args.out!s} "
          f"({len(index.get('atoms', []))} atoms).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
