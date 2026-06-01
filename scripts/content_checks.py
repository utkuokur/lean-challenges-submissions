#!/usr/bin/env python3
"""Strip Lean comments and reject `sorry` / user-declared `axiom`.

Usage:
    content_checks.py <path> [<path> ...]

Each path is a `.lean` file or a directory (walked recursively for
`*.lean`). Exits 0 if every file is clean. On the first violation it
prints `ERROR: <message>` to stdout and exits 1; the message is suitable
for posting back to the submitter.

The only axioms permitted in a submission are Lean/Mathlib's foundational
ones (`propext`, `Classical.choice`, `Quot.sound`), which arrive
transitively via imports and are never *declared* in the user's files. A
user-introduced `axiom foo : <sig>` would otherwise let them "prove"
anything by assertion, so we reject any `axiom` declaration here (and the
build-time `Lean.collectAxioms` check in Check.lean is the backstop).
"""

from __future__ import annotations

import pathlib
import re
import sys


# `sorry` as a standalone token (not e.g. `sorryAx`, `my_sorry`). The
# surrounding character classes include newlines, so a `sorry` on its own
# line is caught; absolute file start/end are covered by ^ / $.
SORRY_RE = re.compile(r'(^|[^A-Za-z0-9_])sorry([^A-Za-z0-9_]|$)')
# `axiom foo` / `noncomputable axiom foo` at the start of a logical line.
AXIOM_RE = re.compile(r'^[ \t]*(noncomputable[ \t]+)?axiom[ \t]', re.MULTILINE)
BLOCK_COMMENT_RE = re.compile(r'/-[\s\S]*?-/')   # non-nested; users don't nest
LINE_COMMENT_RE = re.compile(r'--[^\n]*')


def strip_comments(src: str) -> str:
    src = BLOCK_COMMENT_RE.sub('', src)
    src = LINE_COMMENT_RE.sub('', src)
    return src


def iter_lean_files(paths):
    for p in paths:
        pp = pathlib.Path(p)
        if pp.is_dir():
            yield from sorted(pp.rglob('*.lean'))
        elif pp.is_file():
            yield pp


def main(argv):
    files = list(iter_lean_files(argv))
    if not files:
        print("ERROR: no .lean files found to check")
        return 1
    for f in files:
        try:
            src = strip_comments(f.read_text(encoding='utf-8', errors='replace'))
        except OSError as exc:
            print(f"ERROR: could not read {f.name}: {exc}")
            return 1
        if SORRY_RE.search(src):
            print(f"ERROR: `{f.name}` contains `sorry`. All proofs must be complete.")
            return 1
        if AXIOM_RE.search(src):
            print(f"ERROR: `{f.name}` declares an `axiom`. Only Mathlib's "
                  f"foundational axioms (propext, Classical.choice, Quot.sound) "
                  f"are permitted; you cannot introduce new ones.")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
