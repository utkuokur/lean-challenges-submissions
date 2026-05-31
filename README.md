# lean-challenges-submissions

Submission queue and leaderboard for the
[lean-challenges](https://github.com/utkuokur/lean-challenge) parametrized
problem set.

## How to submit

There are two submission forms, picked from the chooser screen by what
you're settling:

- **[Submit a proof for a specific r](../../issues/new?template=submit-specific.yml)** —
  you've shown the theorem holds at one concrete value of `r`. You
  pick the problem and the value of `r`.
- **[Submit a proof of the universal conjecture](../../issues/new?template=submit-universal.yml)** —
  you've settled the ∀r form, either by proving it or by exhibiting a
  counterexample. You pick the problem and whether you're proving or
  disproving.

Each form lets you submit one of two ways. Fill in **exactly one** of:

- **Submission URL** — single `.lean` file at a public raw URL (a gist
  or a `raw.githubusercontent.com/...` link). CI strips comments,
  rejects bare `sorry` / `axiom` declarations, wraps the file in
  `namespace Submission`, and builds.
- **Repository URL** — multi-file submission hosted in a public GitHub
  repo. Your repo must contain:

  ```
  Submission/
    Main.lean        # defines `r` and `theorem challenge_N` inside `namespace Submission`
    <Helper>.lean    # optional; imported as `import Submission.<Helper>`
  ```

  CI shallow-clones the repo at the given ref, runs the same content
  checks over every file under `Submission/`, splices the directory
  into the canonical checkout as a sibling Lake lib of `Challenges`,
  and builds.

Both paths generate a per-problem `Challenges/Check.lean` that
(1) pins `Submission.challenge_N` to the canonical signature
(substituting `Submission.r` for `r`), and (2) asserts via
`Lean.collectAxioms` that the proof only depends on Lean's three
foundational axioms (`propext`, `Classical.choice`, `Quot.sound`). If
either check fails, the issue is closed with the compiler output. On
success, an entry is appended to `site-data/leaderboard.json`.

Once any submission has settled a given (problem, r) pair, later
submissions for the same pair are rejected — both directions are
mathematically closed at that point. (Two submissions for the same `r`
arriving within minutes of each other can both land; we credit ties.)

AI-assisted, human, or hybrid proofs are all fine — we don't ask how
the proof was produced.

## Repository layout

```
.github/
  ISSUE_TEMPLATE/
    config.yml             # disable blank issues
    submit-specific.yml    # specific-r submission form
    submit-universal.yml   # universal (∀r) submission form
  workflows/
    submission.yml         # triggered on submission issue events
scripts/
  append_leaderboard.py    # appends one entry to site-data/leaderboard.json
  generate_check.py        # per-problem signature + axiom shim
site-data/
  leaderboard.json         # public leaderboard; consumed by the React UI
```

## Schema of `site-data/leaderboard.json`

```jsonc
{
  "entries": [
    {
      "rank": 1,
      "nickname": "lean_enjoyer",
      "name": "",                // optional, may be ""
      "problem": "challenge_1",  // or "challenge_1_univ" etc
      "claim": "prove",          // or "disprove"
      "parameter": "5",          // or "universal" for ∀r challenges
      "date": "2026-05-30T12:34:56Z",
      "issue": 42,
      "source_url": "https://raw.githubusercontent.com/.../challenge_01.lean"
    }
  ]
}
```

The React frontend at
[utkuokur/lean-challenge/automated_compile](https://github.com/utkuokur/lean-challenge/tree/universal-challenges/automated_compile)
fetches this file directly via
`raw.githubusercontent.com/.../site-data/leaderboard.json` and renders
the table.

## Required secrets

The default `GITHUB_TOKEN` is sufficient. No PAT, no GitHub App
installation is required. The workflow needs:

- `contents: write` — to commit updates to `site-data/leaderboard.json`
- `issues: write` — to comment on and close the submission issue

Both are declared in `submission.yml` and granted to the default token.
