"""Source snapshot v2 — foo() UNCHANGED but MOVED down (bar() grew above it).

The line span in the trace's `location` (8:10, from v1) is now stale, but the
fingerprint over foo()'s body still matches: the symbol moved, it did not
change. A consumer rebinds `location` to the new span (14:16) and the claim
survives. This is the moved-symbol-rebind case.
"""


def bar(y):
    # bar() grew, pushing foo() down.
    z = y * 2
    return z


def foo(x):
    # foo() body is byte-identical to v1; only its line span changed.
    return x + 1
