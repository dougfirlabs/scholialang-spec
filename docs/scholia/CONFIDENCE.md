# Scholia v0.4-D — Observation confidence

**Status:** Implemented
**Spec section:** `SCHOLIA_v0.4_SPEC.md` row 8 (Confidence per Observation)
**Schema reservation:** v0.3.1 (`SCHOLIA_v0.3.1_SPEC.md`)
**PRD:** `rsi-scholia-v0.4-confidence-scoring`

---

## What the field is

Every `<Observation>` atom **may** carry a `confidence` attribute — a float in `[0.0, 1.0]` representing the rewriter model's self-assessed certainty in the assertion the atom makes:

```xml
<Observation id="Observation_01" confidence="1.0">
  Exports utc_iso_now returning ISO-8601 UTC.
</Observation>

<Observation id="Observation_02" confidence="0.65">
  Pure: NOT performing any I/O or side effects.
</Observation>
```

The attribute is **optional**. An Observation without `confidence` is semantically equivalent to `confidence="1.0"` — "unstated = confident."

## How the value is derived

The Gemma4 rewriter is prompted, per Observation, to self-assess on this scale:

| Range       | Meaning                                                                                                                  |
| ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| `1.0`       | Directly grounded in source code (literal import, explicit signature, verbatim class name). Restates what the file says. |
| `0.5`–`0.8` | Derived from docstrings, comments, or module-level prose. Summarizes documented intent.                                  |
| `0.2`–`0.5` | Inferred from prose. Generalizes or paraphrases a human-written description.                                             |
| `0.0`–`0.2` | Speculative. Best guess at intent or behavior, not directly supported.                                                   |

The rewriter **does not post-process** confidence values — Gemma's self-assessment flows through verbatim up to the validator's range check. There is no calibration pass, no human-labeled bootstrap, no ensemble averaging.

## Why the field is advisory, not gating

**No part of a host application's downstream pipeline gates on `confidence`.** Specifically:

- The Scholia validator accepts any in-range value. It does **not** reject low-confidence Observations.
- The Adjudicator does **not** downgrade decisions based on Observation confidence.
- The Hospital does **not** skip files based on confidence.
- Downstream consumers may filter (e.g. "show me only Observations with `confidence > 0.8`"), but those filters are tool-level choices, not part of the trace contract.

The advisory posture is deliberate. Model self-assessment is notoriously unreliable: a confident-sounding LLM is not the same as a well-calibrated probability estimator. We surface the signal because the gradient *between* Observations on the same artifact often correlates with grounding (and reviewers find it useful as a triage hint), but we refuse to predicate downstream pipeline decisions on it.

## ⚠️ Calibration limitation

> **Treat `confidence` as an ordinal hint, not a calibrated probability.**

LLM-emitted confidence scores are **not** calibrated probabilities. A `confidence="0.9"` does not mean "the assertion is correct 90% of the time" — it means Gemma's introspection said "more confident than 0.5, less than 1.0" and snapped to a salient number. Across runs and across files, the same logical claim can be tagged with different confidence values. The model has no ground truth against which to anchor the scale.

Concretely:

- **Do** use the field for ordinal filtering: `confidence > 0.8` as a "show me the high-grounding subset" lens.
- **Do** use it to spot outliers within a single artifact: a single `0.3` Observation among five `1.0`s deserves a human glance.
- **Do not** multiply or arithmetically combine `confidence` values as if they were probabilities. They are not.
- **Do not** use confidence in any decision-making pipeline where calibration matters (test-skip logic, automated escalation thresholds, etc.).

If you find yourself wanting to do probabilistic reasoning over Scholia atoms, the right answer is a separate calibrated signal (e.g. cross-validated agreement between multiple rewriter passes), not Gemma's first-pass self-assessment.

## How downstream tools should use it

Recommended patterns:

1. **Ordinal display** — render a small badge next to each Observation in the rendered atlas codeblock: full bar for `≥0.8`, half bar for `0.4–0.79`, empty bar for `<0.4`. Lets a reader scan for grounding gradient without reading the value itself.
2. **Filtered queries** — a CLI / MCP tool that retrieves Observations may accept a `--min-confidence` filter. Default to no filter; surface the option to operators who want the high-grounding subset.
3. **Surfacing for review** — Squeakaroni-style detectors can sample low-confidence Observations and flag them for human triage when they appear on critical-path files. Critical-path is established via `<Meta criticality="...">` (v0.4-C), not confidence — confidence is a secondary signal.

Anti-patterns:

- **Threshold-and-discard** — "throw away all Observations with `confidence < 0.5`" silently loses inferential content. Inferred Observations are still load-bearing for orientation; they're just less directly supported.
- **Aggregate scoring** — averaging confidence over a directory's atoms to produce a "directory quality" metric reads like signal but is dominated by noise in the underlying model assessment.

## Backwards compatibility

- **v0.3 atoms** (no `confidence` attribute) continue to parse and validate unchanged. The attribute is optional in v0.4; absence is allowed indefinitely.
- **v0.3 consumers** reading v0.4 traces see the extra attribute as inert XML — they ignore it and continue functioning.
- **v0.4 consumers** that care about confidence should default missing values to `1.0` to preserve the "unstated = confident" semantic.

The validator enforces the range check at parse time (`scholialang.parser`) **and** at the AST-level rule pass (`RULE_V031_OPTIONAL_FIELDS` in `scholialang.validator`) so traces that arrive via XML and traces that arrive via JSON reconstitution receive the same closed-set check.

## References

- `docs/scholia/SCHOLIA_v0.4_SPEC.md` — full v0.4 specification (row 8 names this enhancement)
- `docs/scholia/SCHOLIA_v0.3.1_SPEC.md` — schema reservation that makes `confidence` an accepted attribute on `<Observation>` from v0.3.1 onward
- `docs/notation/NOTATION_REFERENCE.md` — canonical atom catalog
- `src/example/atlas/prompts/scholia_rewriter.txt` — the rewriter prompt that elicits the self-assessment
- `src/scholialang/validator.py` — `RULE_V031_OPTIONAL_FIELDS` carries the range check
- `tests/unit/scholia/test_validator_v04D.py` — acceptance suite for the boundary, out-of-range, unparseable, and absence cases
- `tests/integration/atlas/test_scholia_rewriter_v04D.py` — rewriter-prompt + end-to-end contract tests
