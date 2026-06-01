# CI secrets and setup for private submissions

This is the source-of-truth for the credentials the private-submission
pipeline needs, and the one-time setup to bring it online. Adapted from
`leanprover/lean-eval-submissions`'s `docs/ci-secrets.md`, simplified for
this repo: there is **no recorder App** (this repo has no branch
protection, so the default `GITHUB_TOKEN` can push the leaderboard) and
**no leaderboard-redeploy PAT** (the leaderboard lives in this same repo
and the frontend fetches `site-data/leaderboard.json` directly).

## What you need

| Item | Type | Stored as | Used by |
| --- | --- | --- | --- |
| `lean-challenge-bot` | GitHub App | `LEAN_CHALLENGE_BOT_APP_ID`, `LEAN_CHALLENGE_BOT_PRIVATE_KEY` | `submission.yml` (fetch / clone private repos) |
| `lean-challenge-archiver` | GitHub App | `LEAN_CHALLENGE_ARCHIVER_APP_ID`, `LEAN_CHALLENGE_ARCHIVER_PRIVATE_KEY` | `submission.yml` (archive) |
| `lean-challenges-audit` | private repo | — | holds the age-encrypted source archive |
| an `age` recipient | public key | `.audit/recipients.txt` (committed) | `submission.yml` (encrypt) |

Until **all** of these exist, the pipeline is down: the `encrypt` step
fails on an empty `.audit/recipients.txt`, and `record` is gated on
`archive`, so no leaderboard entry is written without a successful
encrypted archive.

## Setup checklist (one-time)

1. **Create the private audit repo.** A new **private** repo
   `utkuokur/lean-challenges-audit` (empty is fine; the archiver creates
   files via the Contents API). If you pick a different name, update
   `DEFAULT_AUDIT_REPO` in `scripts/archive_submission.py` and the
   `repositories:` input of the `archive` job in `submission.yml`.

2. **Add an audit recipient key.** Either reuse an SSH public key you
   control, or `age-keygen -o ~/.config/lean-challenges-audit.key` and
   take the printed `age1...` public key. Put the **public** key on its
   own line in `.audit/recipients.txt` (replace the SETUP block), and
   keep the private key safe and backed up — losing every recipient
   private key makes the archive permanently undecryptable.

3. **Create the `lean-challenge-bot` App** (clones submission repos,
   including private ones):
   - <https://github.com/settings/apps/new>
   - Name: `lean-challenge-bot`; Webhook → Active: **unchecked**
   - Repository permissions → **Contents: Read** (nothing else)
   - Where can this GitHub App be installed: **Any account** (submitters
     install it on their own repos)
   - Save → note the **App ID**; generate a **private key** (`.pem`).
   - Install it on this repo too (so the workflow has an installation).
   - Set secrets on `utkuokur/lean-challenges-submissions`:
     ```bash
     gh secret set LEAN_CHALLENGE_BOT_APP_ID -R utkuokur/lean-challenges-submissions --body <APP_ID>
     gh secret set LEAN_CHALLENGE_BOT_PRIVATE_KEY -R utkuokur/lean-challenges-submissions < path/to/bot-key.pem
     ```
   - Put the **public install URL** (`https://github.com/apps/lean-challenge-bot`)
     in the README so submitters can install it.

4. **Create the `lean-challenge-archiver` App** (writes the private audit
   repo). This MUST be a separate App from the bot — the bot is
   installed on arbitrary third-party repos and must stay read-only; a
   write-capable App must never be installable on third-party repos:
   - Name: `lean-challenge-archiver`; Webhook: unchecked
   - Repository permissions → **Contents: Read and write**
   - Where can this GitHub App be installed: **Only on this account**
   - Save → note the App ID; generate a private key.
   - Install it **only** on `utkuokur/lean-challenges-audit`.
   - Set secrets:
     ```bash
     gh secret set LEAN_CHALLENGE_ARCHIVER_APP_ID -R utkuokur/lean-challenges-submissions --body <APP_ID>
     gh secret set LEAN_CHALLENGE_ARCHIVER_PRIVATE_KEY -R utkuokur/lean-challenges-submissions < path/to/archiver-key.pem
     ```

5. **(Recommended) Decide on repo visibility.** See `SECURITY.md` §
   "Residual exposure". Source confidentiality is *best-effort* while
   this submissions repo is public, because the Actions logs are public.
   The pipeline no longer publishes source deliberately, but build
   diagnostics can still surface fragments in logs. If you need stronger
   confidentiality, make this repo private (note: external contributors
   then cannot open issues unless they are collaborators — the usual
   open-submission trade-off).

6. **Smoke-test.** File a submission against a small **private** test
   repo with the bot App installed, confirm: the issue is accepted, an
   object appears under `audit/YYYY/MM/...` in `lean-challenges-audit`,
   the leaderboard row has `submission_public: false` and an empty
   `source_url`, and you can decrypt the archived tarball
   (`docs/audit-archive.md` > "Decryption procedure").

## Why a GitHub App and not a PAT for cloning

The default `GITHUB_TOKEN` can only read the repo the workflow runs in,
not arbitrary private contributor repos. A PAT would have to belong to a
human and carry broad access. A GitHub App that contributors install
**themselves** on **their** repo grants exactly `Contents: Read` on that
one repo, with a short-lived installation token minted per run.
