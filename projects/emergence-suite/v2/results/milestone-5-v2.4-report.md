# Milestone 5 — V2.4 context-indexed redescription

V2.4 stopped honestly at Gate 2 and is **not** a freeze candidate.

Gate 1 passed all fourteen semantic and constitutional proofs. The five
families use common normalized observations and replace complete temporal
process bundles. Missing evidence was structure-neutral to
`4.44e-16`; every posterior log-odds increment matched its published log BF;
partition/complexity recombination error was zero; and a separately authored
path summation matched the candidate scorers to `1.56e-17`.

Gate 2 generated 100 worlds from every family. Macro recovery passed at
`0.682`, but the frozen per-family diagonal `>=0.60` failed for global
down-weight (`0.56`), cue-local relearning (`0.49`), and continuous drift
(`0.59`). Their errors were concentrated among those same three smooth/local
families. Context split recovered at `0.80`, change point at `0.97`, and the
false-context-split rates passed in both drift (`0.02`) and change-point
(`0.03`) worlds.

The original Gate-2 report also flagged Brier because it summed classwise
squared errors. Under the inherited suite definition—mean over worlds and
classes—the same fixed predictions score `0.079161`, passing the `0.15`
ceiling. The original `0.395806` result and failure flag remain verbatim with
an explicit erratum. This software-scoring correction does not change the
recovery failure or authorize a rerun.

Gates 3–5 were not run. The V2.3.3 bank bridge was not opened, C-V24 remained
sealed, and no escrow seed was accessed. Scientific verdict: **FAIL**;
semantic integrity: **PASS**; process custody: **PASS**; distributional
stress: **NOT RUN**.
