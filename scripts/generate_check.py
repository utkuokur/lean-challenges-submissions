#!/usr/bin/env python3
"""Generate Challenges/Check.lean for a given problem_id.

The Check.lean file asserts that `Submission.challenge_N` has the exact
canonical type from `Challenges/challenge_NN.lean` (with the canonical
parameter `r` substituted by `Submission.r` for non-universal problems).
If the user's theorem has the wrong signature, `lake build Challenges.Check`
fails with a type error.

This closes the `theorem challenge_N : True := trivial` bypass.

Usage:
    python3 generate_check.py --problem challenge_1 --output Challenges/Check.lean
"""
from __future__ import annotations

import argparse
import sys


# Per-problem check templates. Each maps from problem_id (as it appears in
# the issue dropdown / GitHub issue) to a complete Lean file. The check
#
#   1. imports `Challenges.challenge_NN` to bring helper definitions
#      (Minor, hadwigerNumber, IsGFRepresentable, etc.) into scope, and
#   2. imports `Challenges.Submission` to access the user's proof, and
#   3. writes an `example` whose type is the canonical theorem signature
#      with `r` substituted by `Submission.r`, body `Submission.challenge_N`.
#
# If `Submission.challenge_N` has the wrong type, the application fails to
# typecheck and `lake build Challenges.Check` exits non-zero.

CHECKS: dict[str, str] = {
    # ─── Parametrized challenges ──────────────────────────────────────
    "challenge_1": r"""
import Challenges.challenge_01
import Challenges.Submission

open SimpleGraph

example {V : Type*} [Fintype V] (G : SimpleGraph V) :
    hadwigerNumber G ≤ Submission.r → G.Colorable (Submission.r + 1) :=
  Submission.challenge_1 G
""",
    "challenge_2": r"""
import Challenges.challenge_02
import Challenges.Submission

open Function Matroid

example {α : Type*} (p m : ℕ) [Fact p.Prime] (hr : Submission.r = p ^ m) :
    ∃ L : Set (Matroid α), CompleteExcludedMinorList (IsGFRepresentable p m) L :=
  Submission.challenge_2 p m hr
""",
    "challenge_3": r"""
import Challenges.challenge_03
import Challenges.Submission

open Filter

example :
    ∃ d₁ d₂ : ℝ, |d₁ - d₂| ≤ (4 - √2) * (0.9 : ℝ)^Submission.r ∧
      ∀ᶠ t in atTop, d₁ ^ t ≤ ramseyNumber t ∧ ramseyNumber t ≤ d₂ ^ t :=
  Submission.challenge_3
""",
    "challenge_4": r"""
import Challenges.challenge_04
import Challenges.Submission

open SimpleGraph

example {V : Type*} [Fintype V] :
    ∀ (G : SimpleGraph V), SidorenkoFor (halfGraph Submission.r) G :=
  Submission.challenge_4
""",
    "challenge_5": r"""
import Challenges.challenge_05
import Challenges.Submission

open SimpleGraph

example : ErdosHajnalConjectureFor (pathGraph Submission.r) :=
  Submission.challenge_5
""",
    "challenge_6": r"""
import Challenges.challenge_06
import Challenges.Submission

open SimpleGraph

example :
    IsBQO (fun (G H : SimpleGraph (Fin Submission.r)) => IsMinor H G) :=
  Submission.challenge_6
""",
    "challenge_7": r"""
import Challenges.challenge_07
import Challenges.Submission

open Function Matroid

example {α : Type*} (hr : Submission.r > 0) :
    ∃ n₀ : ℕ, ∀ n ≥ n₀, ∀ {M : Matroid α} {B : Fin n → Set α},
      IsFamilyOfDisjointBases M B →
      ∀ (ε : ℝ), ε > 0 →
        let m := Nat.ceil ((1 - 1 / (Submission.r : ℝ) - ε) * (n : ℝ))
        ∃ C : Fin m → Set α,
          IsFamilyOfDisjointBases M C ∧
          ∀ (i : Fin n) (j : Fin m), (B i ∩ C j).ncard = 1 :=
  Submission.challenge_7 hr
""",
    "challenge_8": r"""
import Challenges.challenge_08
import Challenges.Submission

example : Hypergraph.RyserConjectureFor.{u} Submission.r :=
  Submission.challenge_8
""",
    "challenge_9": r"""
import Challenges.challenge_09
import Challenges.Submission

example : Challenge09.Hypergraph.RyserConjectureFor.{u} Submission.r :=
  Submission.challenge_9
""",
    "challenge_10": r"""
import Challenges.challenge_10
import Challenges.Submission

example {U : Type u} [DecidableEq U] (hr : 2 < Submission.r)
    {F : Finset (Finset U)}
    (h_union_closed : Challenge10.IsUnionClosed F)
    (h_nontrivial : Challenge10.Nondegenerate F) :
    ∃ x, Challenge10.InGround F x ∧
      Challenge10.density F x ≥ (1 / 2 : Rat) - 1 / (Submission.r : Rat) :=
  Submission.challenge_10 hr h_union_closed h_nontrivial
""",

    # ─── Universal challenges (∀r built into the theorem) ──────────────
    "challenge_1_univ": r"""
import Challenges.challenge_01_univ
import Challenges.Submission

open SimpleGraph

example {V : Type*} [Fintype V] (G : SimpleGraph V) :
    ∀ r, hadwigerNumber G ≤ r → G.Colorable (r + 1) :=
  Submission.challenge_1 G
""",
    "challenge_2_univ": r"""
import Challenges.challenge_02_univ
import Challenges.Submission

open Function Matroid

example {α : Type*} (r p m : ℕ) [Fact p.Prime] (hr : r = p ^ m) :
    ∃ L : Set (Matroid α), CompleteExcludedMinorList (IsGFRepresentable p m) L :=
  Submission.challenge_2 r p m hr
""",
    "challenge_3_univ": r"""
import Challenges.challenge_03_univ
import Challenges.Submission

open Filter

example :
    ∀ r : ℕ, ∃ d₁ d₂ : ℝ, |d₁ - d₂| ≤ (4 - √2) * (0.9 : ℝ)^r ∧
      ∀ᶠ t in atTop, d₁ ^ t ≤ ramseyNumber t ∧ ramseyNumber t ≤ d₂ ^ t :=
  Submission.challenge_3
""",
    "challenge_4_univ": r"""
import Challenges.challenge_04_univ
import Challenges.Submission

open SimpleGraph

example {V : Type*} [Fintype V] :
    ∀ r, ∀ (G : SimpleGraph V), SidorenkoFor (halfGraph r) G :=
  Submission.challenge_4
""",
    "challenge_5_univ": r"""
import Challenges.challenge_05_univ
import Challenges.Submission

open SimpleGraph

example : ∀ r : ℕ, ErdosHajnalConjectureFor (pathGraph r) :=
  Submission.challenge_5
""",
    "challenge_6_univ": r"""
import Challenges.challenge_06_univ
import Challenges.Submission

open SimpleGraph

example :
    ∀ r, IsBQO (fun (G H : SimpleGraph (Fin r)) => IsMinor H G) :=
  Submission.challenge_6
""",
    "challenge_7_univ": r"""
import Challenges.challenge_07_univ
import Challenges.Submission

open Function Matroid

example {α : Type*} :
    ∀ (n : ℕ), ∀ {M : Matroid α} (_ : M.eRank = (n : ℕ∞)) {B : Fin n → Set α},
      IsFamilyOfDisjointBases M B →
      ∃ C : Fin n → Set α, IsFamilyOfDisjointBases M C ∧
        ∀ (i j : Fin n), (B i ∩ C j).ncard = 1 :=
  Submission.challenge_7
""",
    "challenge_8_univ": r"""
import Challenges.challenge_08_univ
import Challenges.Submission

example : Challenge08.RyserHypergraphConjecture.{u} :=
  Submission.challenge_8
""",
    "challenge_9_univ": r"""
import Challenges.challenge_09_univ
import Challenges.Submission

example {U : Type} [Fintype U] [DecidableEq U] :
    ∀ (r : Nat) (_ : 2 < r) {F : Finset (Finset U)}
      (_ : Challenge09.IsUnionClosed F) (_ : Challenge09.Nondegenerate F),
      ∃ x, Challenge09.InGround F x ∧
        Challenge09.density F x ≥ (1 / 2 : Rat) - 1 / (r : Rat) :=
  Submission.challenge_9
""",
    "challenge_10_univ": r"""
import Challenges.challenge_10_univ
import Challenges.Submission

example :
    ∀ {V : Type} [Fintype V] [DecidableEq V] (G : SimpleGraph V),
      ∃ P : Challenge10.Partition V, Challenge10.IsUnfriendly G P :=
  Submission.challenge_10
""",

    # ─── Universal challenges, disprove direction ─────────────────────
    # The submitter exhibits a counterexample to the universal claim.
    "challenge_1_univ_disprove": r"""
import Challenges.challenge_01_univ_disprove
import Challenges.Submission

open SimpleGraph

example :
    ¬ ∀ {V : Type*} [Fintype V] (G : SimpleGraph V),
      ∀ r, hadwigerNumber G ≤ r → G.Colorable (r + 1) :=
  Submission.challenge_1
""",
    "challenge_2_univ_disprove": r"""
import Challenges.challenge_02_univ_disprove
import Challenges.Submission

open Function Matroid

example :
    ¬ ∀ {α : Type*} (r p m : ℕ) [Fact p.Prime], r = p ^ m →
      ∃ L : Set (Matroid α),
        CompleteExcludedMinorList (IsGFRepresentable p m) L :=
  Submission.challenge_2
""",
    "challenge_3_univ_disprove": r"""
import Challenges.challenge_03_univ_disprove
import Challenges.Submission

open Filter

example :
    ¬ ∀ r : ℕ, ∃ d₁ d₂ : ℝ, |d₁ - d₂| ≤ (4 - √2) * (0.9 : ℝ)^r ∧
      ∀ᶠ t in atTop, d₁ ^ t ≤ ramseyNumber t ∧ ramseyNumber t ≤ d₂ ^ t :=
  Submission.challenge_3
""",
    "challenge_4_univ_disprove": r"""
import Challenges.challenge_04_univ_disprove
import Challenges.Submission

open SimpleGraph

example :
    ¬ ∀ {V : Type*} [Fintype V], ∀ r, ∀ (G : SimpleGraph V),
      SidorenkoFor (halfGraph r) G :=
  Submission.challenge_4
""",
    "challenge_5_univ_disprove": r"""
import Challenges.challenge_05_univ_disprove
import Challenges.Submission

open SimpleGraph

example : ¬ ∀ r : ℕ, ErdosHajnalConjectureFor (pathGraph r) :=
  Submission.challenge_5
""",
    "challenge_6_univ_disprove": r"""
import Challenges.challenge_06_univ_disprove
import Challenges.Submission

open SimpleGraph

example :
    ¬ ∀ r, IsBQO (fun (G H : SimpleGraph (Fin r)) => IsMinor H G) :=
  Submission.challenge_6
""",
    "challenge_7_univ_disprove": r"""
import Challenges.challenge_07_univ_disprove
import Challenges.Submission

open Function Matroid

example {α : Type} [Fintype α] :
    ¬ ∀ (n : ℕ), ∀ {M : Matroid α} (_ : M.eRank = (n : ℕ∞))
      {B : Fin n → Set α},
      IsFamilyOfDisjointBases M B →
      ∃ C : Fin n → Set α, IsFamilyOfDisjointBases M C ∧
        ∀ (i j : Fin n), (B i ∩ C j).ncard = 1 :=
  Submission.challenge_7
""",
    "challenge_8_univ_disprove": r"""
import Challenges.challenge_08_univ_disprove
import Challenges.Submission

example : ¬ Challenge08.RyserHypergraphConjecture.{u} :=
  Submission.challenge_8
""",
    "challenge_9_univ_disprove": r"""
import Challenges.challenge_09_univ_disprove
import Challenges.Submission

example :
    ¬ ∀ {U : Type} [Fintype U] [DecidableEq U]
      (r : Nat) (_ : 2 < r) {F : Finset (Finset U)}
      (_ : Challenge09.IsUnionClosed F) (_ : Challenge09.Nondegenerate F),
      ∃ x, Challenge09.InGround F x ∧
        Challenge09.density F x ≥ (1 / 2 : Rat) - 1 / (r : Rat) :=
  Submission.challenge_9
""",
    "challenge_10_univ_disprove": r"""
import Challenges.challenge_10_univ_disprove
import Challenges.Submission

example :
    ¬ ∀ {V : Type} [Fintype V] [DecidableEq V] (G : SimpleGraph V),
      ∃ P : Challenge10.Partition V, Challenge10.IsUnfriendly G P :=
  Submission.challenge_10
""",
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--problem", required=True,
                   help="problem id, e.g. challenge_1 or challenge_3_univ")
    p.add_argument("--output", required=True,
                   help="path to write Check.lean")
    args = p.parse_args()

    template = CHECKS.get(args.problem)
    if template is None:
        sys.exit(f"Unknown problem id: {args.problem!r}. "
                 f"Known: {', '.join(sorted(CHECKS))}")

    body = template.lstrip("\n")
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Wrote signature check for {args.problem} to {args.output} "
          f"({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
