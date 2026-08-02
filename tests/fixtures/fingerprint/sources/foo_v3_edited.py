"""Source snapshot v3 — foo() BODY EDITED (the fingerprinted content is gone).

Neither the span at `location` nor anywhere else in the file matches the
fingerprint any more: the symbol's content changed. Re-verification returns
`stale` — the trace's claim about foo() must not be trusted verbatim.
"""


def foo(x):
    # foo() body changed: the claim's fingerprint no longer matches.
    return (x + 1) * 3


def bar(y):
    return y * 2
