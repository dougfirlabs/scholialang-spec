"""Source snapshot v1 — the tree the fixtures' fingerprints were authored against.

Illustrative only: the fingerprint hex values in the traces are placeholders
(the real digest is computed by 52X-B2's single definition, issue #524). A
consumer wired to that definition recomputes over the span named by `location`.
"""


def foo(x):
    # foo() lives at lines 8:10 in this snapshot.
    return x + 1


def bar(y):
    return y * 2
