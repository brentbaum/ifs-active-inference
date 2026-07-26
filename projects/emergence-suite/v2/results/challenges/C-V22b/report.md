# C-V22b Gate 6 report

Verdict: **PASS**

The runner checked all 50 frozen
V2.2.1 files against commit `347482f` with zero
mismatches. It used seeds `806117` through
`806176`, paired across both treatment arms and across
the three nested history-length doses.

## Preregistered tests

1. **Graded transfer — PASS.** Mean
   within-world Spearman correlation was `0.999`
   (95% interval `0.998` to
   `1.000`), against the `.60` threshold;
   the strong > weak > zero ordering held in
   `60/60` worlds
   (95% Wilson interval `0.940` to
   `1.000`).
2. **Floor with dose-response — PASS.**
   Mean absolute G revision after zero-cue treatment was
   `0.005150` at short,
   `0.000419` at medium, and
   `0.000044` at long history.
   The paired short-minus-medium and medium-minus-long effects were
   `0.004730` and
   `0.000375`. Long-history
   floor compliance was `60/60`
   (95% Wilson interval `0.940` to
   `1.000`).
3. **Mediation — PASS.** The explicit
   root-cut transfer was `0`.
   There were `173` arm-tier instances in the root
   null band; maximum untreated transfer among them was
   `0.006937`.
4. **Segment gating — PASS.** The
   broad-minus-narrowed attribution effect was
   `0.172327` (95% interval
   `0.158840` to
   `0.185814`). Mean cue-level
   revisions were `0.420000` broad
   and `0.429442` narrowed.

The primary 60-world slice for tests 1, 3, and 4 is the preregistered medium
history. Each of those same 60 paired base worlds also uses nested short and
long prefixes for test 2; this is required to interpret the sealed
`48/60 of LONG-tier worlds` threshold without consuming extra seeds. Segment
identity and the unannounced boundary were not inference inputs.

## Failure localization

- No preregistered failure was triggered.

No frozen engine, stage, contract, parameter, result, tolerance, or manifest
file was modified.
