#!/usr/bin/env python3
"""Validate the examples/v06 corpus against the published scholialang v0.6.

Run from anywhere with the published ``scholialang`` v0.6 importable
(``pip install -e <scholialang>``):

    python examples/v06/validate_examples.py

What it does:
  1. Parses + validates every ``examples/v06/*.xml`` trace with the
     published v0.6 validator; asserts ``ok`` (no errors) and reports
     warnings (there should be none).
  2. Demonstrates the genuine cross-session REFER:canonical_id path: it
     loads ``registry_dag_chain.xml``, ``put``s the atoms into a temporary
     DAG registry, and resolves a ``REFER:sha256:<cid>`` from a synthetic
     session-N+1 atom via the 4-path ``resolve_refer`` resolver (registry
     path). It also walks the registry DAG (ancestors / walk_chain).
  3. Renders the 3 CORE prelude modes (hash_only / hash_list / inline)
     over the prior atoms and writes them to ``prelude_<mode>.txt``.

Exit code 0 iff every trace validates clean and the registry resolution
succeeds. Deterministic; no LLM calls.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from scholialang import (
    __version__ as scholialang_version,
    build_canonical_prelude,
    CORE_PRELUDE_MODES,
    parse,
    Registry,
    resolve_refer,
    validate,
)


HERE = Path(__file__).resolve().parent


def _walk(atoms):
    for a in atoms:
        yield a
        yield from _walk(a.children)


def validate_all() -> bool:
    ok_all = True
    for xml_path in sorted(HERE.glob("*.xml")):
        steps = parse(xml_path.read_text(encoding="utf-8"))
        result = validate(steps)
        status = "PASS" if result.ok else "FAIL"
        print(f"[{status}] {xml_path.name}: "
              f"{len(result.errors)} error(s), {len(result.warnings)} warning(s)")
        for e in result.errors:
            print(f"        error  {e.rule}: {e.message}")
        for w in result.warnings:
            print(f"        warn   {w.rule}: {w.message}")
        ok_all = ok_all and result.ok
    return ok_all


def demo_registry_and_prelude() -> bool:
    """Cross-session resolve_refer via registry + render the 3 core modes."""
    steps = parse((HERE / "registry_dag_chain.xml").read_text(encoding="utf-8"))
    prior_atoms = list(_walk([a for st in steps for a in st.atoms]))

    tmp = tempfile.mkdtemp(prefix="scholia-v06-examples-")
    registry = Registry(Path(tmp) / "registry.proofchain.json")
    for atom in prior_atoms:
        registry.put(atom)

    # Pick the Concluding's premise Finding (F_01) as the reuse target.
    f01 = next(a for a in prior_atoms if a.id == "F_01")
    target_cid = f01.canonical_id
    print(f"\nRegistry: {len(registry)} atoms, reuse target F_01 -> {target_cid}")

    # Session N+1: a bare REFER:sha256:<cid> resolves via the registry
    # (resolve_refer path 3) even though the atom is not in this trace.
    resolved = resolve_refer([], target_cid, registry=registry)
    if resolved is None:
        print("FAIL: resolve_refer could not resolve the cross-session cid.")
        return False
    print(f"resolve_refer (registry path) resolved {target_cid} -> "
          f"kind={resolved.get('kind')!r}")

    # Session N+1 emits a NEW Concluding whose body REFERs the prior F_01
    # by canonical_id (REFER:sha256:<cid>) — the registry forms a real
    # premise->conclusion DAG edge from that inline cid target.
    next_session = parse(
        f'<Step id="s2" name="cross-session close">'
        f'<Goal id="G_99" priority="required" criticality="verifier">'
        f'Reuse the prior merge finding.</Goal>'
        f'<Concluding id="C_99" for_goal="G_99" criticality="verifier">'
        f'REFER:{target_cid} IMPLIES the prior merge decision carries forward.'
        f'</Concluding></Step>'
    )
    c99 = next(a for a in _walk([a for st in next_session for a in st.atoms])
               if a.id == "C_99")
    registry.put(c99)

    # DAG: the new Concluding C_99 should have F_01 as a premise (ancestor).
    ancestors = list(registry.ancestors(c99.canonical_id))
    anc_kinds = sorted({r.get("kind") for r in ancestors})
    chain = registry.walk_chain(c99.canonical_id)
    print(f"DAG: C_99 ancestors={anc_kinds}; "
          f"walk_chain nodes={len(chain.nodes)} edges={len(chain.edges)} "
          f"complete={chain.is_complete}")

    # Render the 3 CORE prelude modes over the prior atoms.
    for mode in CORE_PRELUDE_MODES:
        rendered = build_canonical_prelude(prior_atoms, registry=registry, mode=mode)
        out = HERE / f"prelude_{mode}.txt"
        out.write_text(rendered, encoding="utf-8")
        print(f"Wrote {out.name} ({len(rendered)} chars)")

    return resolved is not None and bool(ancestors)


def main() -> int:
    print(f"scholialang {scholialang_version} — examples/v06 validation\n")
    traces_ok = validate_all()
    demo_ok = demo_registry_and_prelude()
    print()
    if traces_ok and demo_ok:
        print("ALL v0.6 examples validate clean; registry + prelude OK.")
        return 0
    print("FAILURE: see output above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
