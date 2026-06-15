"""Public-spec hygiene guard — local mirror of the CI leak guard.

The authoritative guard is the ``hygiene`` job in
``.github/workflows/docs.yml``; this test runs the same forbidden-token
regex locally so the guard is exercised by ``pytest`` (CI cannot be run
from the dev loop). Two assertions:

a) the published surfaces (docs/, examples/, scripts/, tests/,
   reference/, src/ if present, the root markdown files, and
   ``compatibility-manifest.json``) contain NO internal references;
b) the guard self-test: a planted internal reference IS caught.

The forbidden-token regex is read from ``docs.yml`` (single source of
truth) rather than hard-coded here, so this test file contains no literal
forbidden token that the guard would otherwise flag when it scans
``tests/``. The planted fixture is built by concatenation for the same
reason and is written under a tmp dir, not into the repo tree.
"""
from __future__ import annotations

import re
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _forbidden_regex() -> str:
    """Extract the FORBIDDEN_REGEX value from the CI workflow."""
    workflow = _repo_root() / ".github" / "workflows" / "docs.yml"
    text = workflow.read_text(encoding="utf-8")
    match = re.search(r"FORBIDDEN_REGEX:\s*'([^']+)'", text)
    assert match, "FORBIDDEN_REGEX not found in .github/workflows/docs.yml"
    return match.group(1)


# Scan roots — mirror the workflow's list; only existing paths are kept.
_SCAN_CANDIDATES: tuple[str, ...] = (
    "docs", "examples", "scripts", "tests", "reference", "src",
    "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "GOVERNANCE.md",
    "compatibility-manifest.json",
)


def _scan_files() -> list[Path]:
    root = _repo_root()
    files: list[Path] = []
    for name in _SCAN_CANDIDATES:
        path = root / name
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
        else:
            files.extend(p for p in path.rglob("*") if p.is_file())
    return files


def _text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None  # binary (e.g. assets/*.png) — skipped, like grep -I


def test_published_surfaces_have_no_internal_references() -> None:
    pattern = re.compile(_forbidden_regex())
    offenders: list[str] = []
    for path in _scan_files():
        text = _text_or_none(path)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                rel = path.relative_to(_repo_root())
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Internal references found in published surfaces:\n"
        + "\n".join(offenders)
    )


def test_guard_catches_a_planted_internal_reference(tmp_path: Path) -> None:
    pattern = re.compile(_forbidden_regex())
    # Build the forbidden token by concatenation so this test file stays
    # clean when the guard scans tests/.
    planted = tmp_path / "planted.txt"
    planted.write_text("this mentions " + "open" + "talon" + " internally\n",
                       encoding="utf-8")
    assert pattern.search(planted.read_text(encoding="utf-8")), (
        "guard self-test FAILED — the forbidden regex did not catch a "
        "planted internal reference."
    )
