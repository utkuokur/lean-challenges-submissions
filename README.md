# lean-challenges-submissions

Submission queue and leaderboard for the
[lean-challenges](https://github.com/utkuokur/lean-challenge) parametrized
problem set.

## How to submit

1. Host your `challenge_NN.lean` (or `challenge_NN_univ.lean`) file
   publicly — a public GitHub repo or a public gist.
2. Open a [**Submit a proof**](../../issues/new?template=submit.yml) issue
   and fill in the form: URL of your file, which problem you're targeting,
   prove or disprove, the parameter `r`, and a nickname.
3. CI fetches your file, builds it against the pinned `lean-toolchain`,
   and on success adds your entry to `site-data/leaderboard.json` and
   closes the issue. On failure it comments with the compiler output.

## Repository layout

```
.github/
  ISSUE_TEMPLATE/
    config.yml          # disable blank issues
    submit.yml          # the GitHub Issue Form users fill in
  workflows/
    submission.yml      # triggered on `submission` label
scripts/
  append_leaderboard.py # appends one entry to site-data/leaderboard.json
site-data/
  leaderboard.json      # public leaderboard; consumed by the React UI
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
