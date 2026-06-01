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

1. **Private source via the `lean-challenge-bot` App, not a public URL.**
   Repo submissions are cloned with a step-scoped installation token; a
   private repo with the App installed clones, a private repo without it
   is rejected with instructions. Single-file (gist/raw-URL) submissions
   remain public-only.
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

## 3. Residual exposure — read this before relying on confidentiality

**Confidentiality is best-effort, not a guarantee**, and is weaker here
than upstream for two structural reasons:

- **No sandbox around untrusted Lean.** `leanprover/lean-eval` elaborates
  untrusted submissions inside the `comparator`/`landrun` sandbox. This
  pipeline runs `lake build` on the submission **directly on the
  runner**. Lean elaboration can execute arbitrary code (custom
  elaborators, `run_cmd`, `#eval`, build scripts), so a malicious
  submission can run arbitrary code on the runner during the build. The
  `.git`-strip + `persist-credentials:false` + step-scoped bot token
  reduce what such code can steal (no long-lived credentials are present
  during the build), but a determined attacker who can run code on the
  runner can still read other submissions in flight on that runner, or
  probe the runner environment. Adding a sandbox (as upstream does) is
  the recommended hardening and is **out of scope** for this privacy
  port; treat the current build step as running untrusted code.
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

1. **The build step runs untrusted Lean unsandboxed** (§3). Highest-value
   hardening target.
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
