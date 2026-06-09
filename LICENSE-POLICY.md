# Scholialang License Policy

Scholialang separates the license for the normative specification text from
the license for implementation code.

## Specification Text

The prose specification, reference documentation, migration notes, and
standards-facing language artifacts in this repository are licensed under the
Creative Commons Attribution 4.0 International license (`CC-BY-4.0`), unless a
file states otherwise.

This keeps the standards text freely copyable, quotable, translatable,
redistributable, and adaptable with attribution.

## Implementation Code

Reference implementations, parser and validator packages, MCP/LSP tooling,
host plugins, and other executable code live in sibling repositories such as
`scholialang` and `scholialang-mcp`. Those code-bearing repositories are
licensed separately, generally under dual `MIT OR Apache-2.0` terms.

## Examples and Machine-Readable Artifacts

Examples, fixtures, schemas, generated reference tables, and other
machine-readable artifacts in this repository inherit the repository's
`CC-BY-4.0` license unless a file or directory states a different license.

If an artifact is intended to be copied directly into an implementation, the
preferred future policy is to mark it explicitly as `MIT OR Apache-2.0`.

## Trademarks and Conformance

The licenses above do not grant trademark rights or permission to imply
official certification. Implementations may describe compatibility with
published Scholialang versions, but official conformance claims should follow
the project governance and conformance process once that process is published.
