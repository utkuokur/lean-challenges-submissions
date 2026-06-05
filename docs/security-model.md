# Security model: the lean-challenges submission pipeline

This describes the confidentiality and integrity properties of the
submission pipeline after the private-submission port, what they depend
on, and — importantly — where they are **weaker** than the upstream
`leanprover/lean-eval` pipeline this was adapted from.

## 1. What the pipeline promises

- **Integrity (unchanged from the public pipeline).** A leaderboard
  entry means `lake build` of a signature-shim `Check.lean` succeeded:
  the submitter's `Submission.challenge_N` matched the canonical
  signature (with `Submission.r` substituted for `r`), with no `sorry`,
  no user-declared `axiom`, against the pinned toolchain.
- **Confidentiality (best-effort).** Other contestants cannot see a
  submission's source; the submitter (it is their repo) and the
  maintainers (who hold the audit-archive private keys and can read the
  private audit repo) can. This is the "submitter + maintainers, not
  other contestants" model. It is **not** "nobody but the submitter" —
  server-side verification inherently requires the verifier to read the
  source.

## 2. How confidentiality is achieved

1. **Private source via the `lean-challenge-bot` App.** Submissions are
   always a GitHub repo, cloned with a step-scoped installation token; a
   private repo with the App installed clones, a private repo without it
   is rejected with instructions.
2. **Source is never deliberately published.** The old pipeline committed
   every accepted proof into a public `solutions/` directory and linked
   it from the leaderboard via `source_url`. Both are removed: the
   leaderboard now carries `submission_public` and an **empty
   `source_url` for private submissions**, and no source is committed
   here.
3. **The plaintext source never becomes a downloadable artifact.** Fetch
   and build share **one job**, so the source never crosses a runner
   boundary. Only the age-**encrypted** ciphertext is uploaded as an
   artifact (useless without a recipient key). Do not split these jobs,
   and do not upload the plaintext.
4. **Credential hygiene.** `persist-credentials: false` on both
   checkouts; `.git` stripped from both checkouts and the token-bearing
   user clone before any Lean runs; the bot token is scoped to the single
   `Fetch submission` step's env; the archiver token lives only in the
   separate `archive` job.
5. **Encrypted audit retention.** Every fetched submission's source tar
   is age-encrypted to `.audit/recipients.txt` and pushed to the private
   `lean-challenges-audit` repo. `record` is gated on `archive`, so a
   leaderboard entry always implies a durable encrypted copy. See
   `docs/audit-archive.md`.
6. **Network-isolated build.** The untrusted submission is compiled under
   `bubblewrap --unshare-net`, so the build has no network access. Deps
   (Mathlib cache + the canonical module) are fetched/compiled in a
   separate, earlier step that runs only trusted code with network; the
   untrusted compile then runs offline. This blocks crypto-mining, data
   exfiltration, and using the runner to attack third parties, and stops a
   malicious submission from phoning home with anything it reads on the
   runner. See §3 for what this does and does not cover.

## 3. Residual exposure — read this before relying on confidentiality

**Confidentiality is best-effort, not a guarantee.** Two things to know:

- **Network-isolated, but not a full sandbox.** Lean elaboration can
  execute arbitrary code (custom elaborators, `run_cmd`, `#eval`, build
  scripts), so the build step runs untrusted code. We compile it under
  `bubblewrap --unshare-net`, which removes **network access** — the
  highest-value containment (no mining, no exfiltration, no outbound
  attacks, nothing it reads can be phoned home). This is lighter than
  `leanprover/lean-eval`'s `comparator`/`landrun` sandbox: we do **not**
  lock down the filesystem (`--dev-bind / /` leaves it intact, to minimise
  the chance of breaking the build), so untrusted code can still read
  what's on the runner and use CPU within the job's `timeout-minutes`. It
  cannot, however, send any of that anywhere. The `.git`-strip +
  `persist-credentials:false` + step-scoped bot token mean no long-lived
  credentials are present during the build. Each submission runs on its
  own fresh runner, so cross-submission reads are limited to whatever is
  co-resident in a single run. Tightening to a filesystem sandbox (bind
  only the build dir read-write, rest read-only) is the next hardening
  step if needed.
- **Sandbox engagement is runner-dependent.** Whether bubblewrap can
  initialise a network namespace depends on the CI runner, not on local
  tooling. The workflow falls back to a non-isolated build (with a
  `::warning::`) if it cannot, so it will not hard-fail every
  submission — but confirm on a real CI run that bubblewrap engages and
  that legitimate submissions still compile offline before relying on it.
- **Public Actions logs.** While this submissions repo is **public**, its
  Actions logs are public. The pipeline no longer prints the build log
  into issue comments, but `lake build` diagnostics in the run logs can
  still surface source fragments (e.g. a failing goal echoes the
  theorem statement). For stronger confidentiality, make this repo
  private — at the cost that external contributors can no longer open
  issues unless they are collaborators (the standard open-submission
  trade-off). See `docs/ci-secrets.md` step 5.

## 4. Injection hardening

User-controlled issue fields (nickname, name, URLs) are passed into
workflow scripts via **environment variables**, never via `${{ }}`
expression interpolation into a `run:` block, and are serialized with
`json.dumps`. This prevents a crafted issue body from injecting shell or
Python into the workflow. Constrained fields (`problem_id`, `parameter`,
`module`) are validated by regex in the parse step.

## 5. Soft spots — where to look first

1. **The build step runs untrusted Lean** (§3). It is network-isolated
   (`bubblewrap --unshare-net`) but not filesystem-sandboxed. Tightening
   the filesystem and confirming the sandbox engages on CI is the
   highest-value remaining hardening.
2. **`.audit/recipients.txt` custody.** Adding a recipient grants
   permanent read access to the entire archive; treat additions as
   reviewed PRs. Losing every private key makes the archive
   undecryptable.
3. **Repo visibility vs. open submission** (§3). The confidentiality
   ceiling is set by whether the repo (and thus its Actions logs) is
   public.
4. **Workflow-structure drift.** The confidentiality argument depends on
   the one-job fetch+build shape, the token scoping, and the `.git`
   strip. Review changes to `submission.yml` against §2.

## References

- `docs/audit-archive.md` — the encrypted-archive design and decryption.
- `docs/ci-secrets.md` — the GitHub Apps, the audit repo, and setup.
- Upstream: `leanprover/lean-eval-submissions` `SECURITY.md` and the
  `leanprover/lean-eval` comparator/landrun sandbox model.
