# Scholia criticality manifest — authoring guide

`.scholia/criticality.yaml` (at repo root) is an operator-curated
manifest that classifies source files by risk level. The Scholia
rewriter reads this manifest to emit `<Meta criticality="..."/>` on
the `<Step>` atom for each file it processes.

The manifest is the **only** input to risk classification — the
rewriter never guesses. Files outside the manifest's globs get no
`<Meta>` element, which is semantically equivalent to `incidental`.

## File format

YAML mapping of criticality level to a list of repo-relative globs:

```yaml
# .scholia/criticality.yaml
kernel:
  - src/scholialang/validator.py
  - src/example/kb/store.py
  - src/example/atlas/scholia_rewriter.py

verifier:
  - src/scholialang/parser.py
  - src/scholialang/atoms.py
  - src/example/adjudicator/**/*.py

ledger:
  - src/example/kb/events.py
  - src/example/rsi/events.py

bridge:
  - src/example/auth/**/*.py
  - src/example/drivers/**/*.py
```

Top-level keys MUST be one of the five closed-set levels (below).
Values MUST be lists of strings; glob patterns use `**` for recursive
matches (fnmatch-style with double-star expansion).

## Closed-set levels

The set is `{kernel, verifier, ledger, bridge, incidental}`. Adding a
new level requires a Scholia spec version bump (next would be v0.5).

### `kernel`

The core code whose correctness the rest of the system depends on.
Casual edits regress the system; changes require careful review and
typically a paired test landing in the same commit.

**Use for:** validator entry points, ledger writers, the bridge
between trust domains, the rewriter that produces audit-trail content.

**Example fits in a host application:**
* `src/scholialang/validator.py` — the Scholia validator is
  the proof surface; bugs here let invalid traces through.
* `src/example/kb/store.py` — the KB store is the durable record of
  what the system has learned; corruption is unrecoverable.
* `src/example/atlas/scholia_rewriter.py` — produces the structured
  artifacts that downstream agents rely on.

### `verifier`

Code that proves the correctness of other code. Edits here change
the semantics of "what passes" — a buggy verifier may accept invalid
input or reject valid input, and downstream agents will trust either
result.

**Use for:** validators, parsers, schema enforcers, adjudicators,
type checkers, anything whose output is "yes/no" or "list of
violations."

**Example fits in a host application:**
* `src/scholialang/parser.py` — the closed-set rejection on
  the wire-form input path lives here.
* `src/example/adjudicator/**/*.py` — the adjudicator that decides
  PRD pass/fail.

### `ledger`

Append-only persistence layers. Edits affect the audit trail and may
make historical records unreproducible.

**Use for:** event streams, KB posts, run journals, any append-only
storage. The rule of thumb: if `git blame` on this file matters in a
post-incident review, it's probably ledger.

**Example fits in a host application:**
* `src/example/kb/events.py` — the KB events stream.
* `src/example/rsi/events.py` — the RSI events stream.

### `bridge`

Code that crosses a trust boundary. Bugs here can leak data across
boundaries, accept untrusted input as trusted, or send trusted output
to untrusted destinations.

**Use for:** auth gateways, external API adapters, encryption/decryption
boundaries, external proof-graph conversions, anything that translates
between two trust domains.

**Example fits in a host application:**
* `src/example/auth/**/*.py` — anything touching session cookies
  or tokens.
* `src/example/drivers/**/*.py` — adapters that send prompts to
  external model providers.

### `incidental`

The default. Everything not load-bearing — debug scripts, one-off
reports, exploratory notebooks, test helpers, documentation tooling,
demo fixtures.

**Use for:** anything where a regression won't propagate. Most files
in most projects are incidental. **Do not list incidental files in
the manifest** — leave them out. Absence is the default.

The one reason to explicitly list a file as `incidental` is to
**downgrade** an inferred-critical file (e.g. a script that lives
under `src/` but is genuinely throwaway). The rewriter respects the
explicit classification.

## Authoring guidance

### Most projects need only two levels

A typical project starts with **kernel** (the 5–20 files whose bugs
are existential) and treats everything else as **incidental** (no
manifest entry). The other three levels — verifier, ledger, bridge —
are domain-specific:

* You need **verifier** if you have code that proves correctness of
  other code. Most product code doesn't.
* You need **ledger** if you have append-only persistence whose
  audit trail matters. Most product code uses ordinary databases
  where the audit trail is implicit in migrations.
* You need **bridge** if you have trust-domain crossings beyond the
  generic "user input is untrusted." Auth code is the prototype.

If you're not sure, leave it out. Adding a file later is cheap;
removing a classification later requires justification.

### Globs vs explicit paths

Both are supported. Prefer **explicit paths for kernel** (you want
the manifest to be auditable — anyone reading it should be able to
say "these specific files are kernel"). Prefer **globs for bridge
and verifier** when the boundary is structural (`src/example/auth/**/*.py`
is clearer than listing 12 auth files).

Globs are evaluated lazily — the rewriter resolves them on each
file lookup, so adding a new file under `src/example/auth/` picks
up the bridge classification automatically.

### Conflict resolution

If a file matches multiple entries (e.g. listed as both `kernel` and
`verifier`), the manifest reader raises an error. **Each file gets
exactly one criticality**. Pick the higher of the two (kernel >
verifier > ledger > bridge > incidental).

### When to update

Update the manifest when:

* A new load-bearing file lands (add it to the appropriate level).
* A file's role changes (e.g. an experimental file graduates to
  kernel).
* A spec version bump introduces a new criticality level (rare).

The manifest is checked into git alongside the code it classifies.
Reviews of changes to `.scholia/criticality.yaml` should be treated
with the same weight as reviews of the underlying code — re-classifying
a file from `incidental` to `kernel` has the same effect on agent
routing as adding `# kernel-critical` to every Scholia atom touching
the file.

## Sample manifest

```yaml
# .scholia/criticality.yaml — a host application's manifest (illustrative).
#
# Kernel: bug here regresses the system end-to-end.
# Verifier: bug here changes what passes/fails.
# Ledger: bug here corrupts the audit trail.
# Bridge: bug here crosses a trust boundary.

kernel:
  - src/scholialang/validator.py
  - src/scholialang/atoms.py
  - src/example/atlas/scholia_rewriter.py
  - src/example/kb/store.py
  - src/example/safety/__init__.py

verifier:
  - src/scholialang/parser.py
  - src/example/adjudicator/**/*.py
  - src/example/atlas/validate.py

ledger:
  - src/example/kb/events.py
  - src/example/rsi/events.py
  - src/example/runlog/**/*.py

bridge:
  - src/example/auth/**/*.py
  - src/example/drivers/**/*.py
  - src/example/bridges/**/*.py
```

## References

* [`FILE_METADATA.md`](FILE_METADATA.md) — the v0.4-C file-level
  metadata program, including how criticality, side effects, and
  test ownership flow into emitted atoms.
* [`SCHOLIA_v0.3.1_SPEC.md`](SCHOLIA_v0.3.1_SPEC.md) — the schema
  reservations that make `<Meta criticality="..."/>` a valid Step
  child.
