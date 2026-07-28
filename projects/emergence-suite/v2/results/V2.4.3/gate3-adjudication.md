# V2.4.3 gate-3 adjudication (GPT-5.6 Pro round 4, 2026-07-28)

Consultation round 4 (branch pushed through a6e1979; diagnosis: `gate3-diagnosis.md` + four per-world CSVs). Decision metric: whatever most strengthens the paper.

## Standing
- **V2.4.3 remains a gate-3 FAIL exactly as recorded.** Its load-bearing genuine and bridge results remain visible (material redescription 0.708 / 0.675; single-regime material controls exactly zero); the failures were the shuffled control, all five 32-slice BMA criteria, and the CS margin interval.
- The 45–47% raw shuffled material rate is retained as a **reported limitation**.
- All diagnosis blocks remain barred; no barred or previously consumed world may serve as criterion data.
- **V2.4.4 is authorized as the final open-development successor for this model family.** It is not a license to iterate until success.

## Adjudication of the three failures
| Failure | Status | Resolution |
|---|---|---|
| Shuffled material rate | **Criterion-validity failure** | Replace the uncalibrated absolute material ceiling with a conditional-randomization-calibrated *selective redescription* criterion; raw rate kept as limitation |
| BMA regret | **Information-budget failure** | Move the criterial assay to 96 slices on fresh seeds; 32-slice results become a short-history stress test; no family exception, including DR |
| CS matched margin | **Information/power failure** | Evaluate on the same fresh 96-slice CS population with 500 worlds; .01 margin and positive lower-CI requirements unchanged |

Rationale, per the diagnosis: the shuffled generator correctly implements its independence null, but finite permutations often instantiate accidental cue/marker associations that the exact CS posterior correctly recognizes (45–47% of null worlds). The current material readout answers "does this realized stream support a materially occupied two-context representation?" — not "is that support stronger than finite streams with the same cue-wise marginals produce by chance?" BMA regret falls sharply on the 96-slice population as family uncertainty resolves (DR retains a smaller tail). The CS margin has a stable positive mean (+0.0344; every leave-one-out mean ≥ +0.0288) with broad world heterogeneity, not a zero or negative center.

## What V2.4.4 may change
1. How the conditional-product null calibrates evidence for redescription (add compound structural statistic T, deterministic conditional-randomization distributions and p-values, selective-material-redescription criterion);
2. Information budget and sample size of the held-out predictive assay (96 slices, 500/family);
3. Information budget and power of the CS matched-margin assay (same 96-slice population, 375/500 feasibility floor);
plus fresh seed blocks, reports, exact oracles, analysis-only fields, and 32/64/96 information curves.

## What V2.4.4 may not change
Any candidate family; any emission or transition probability; CS transition prior; family prior; parameter prior; common likelihood interface; path-complexity accounting; material thresholds .80 and 4.0; genuine/control thresholds .60 and .10; held-out SESOI .01; complexity tolerance .13; transfer, historical-retention, present-indexing, or G-fixed criteria; formed-bank states or weighting; C-V24 plaintext, hash, seeds, criteria, or interpretation; any barred or previously consumed world as criterion data. The very high two-context CS path prior (pi1 ≈ 0.9274 at 24 pre-held-out slices) must remain unchanged and be reported.

## Stop rule after V2.4.4
- A numeric failure of .60, .10, .01, or the interval criteria **stands**.
- No further sample-size or information-length amendment is permitted.
- Another successor is justified only if C-V24 exposes a genuinely absent representational class or semantic inexpressibility.
- If DR still fails BMA regret on fresh 96-slice data, that is retained as a real limitation ("the BMA remained slightly worse than the known DR generator in a tail of ambiguous drift histories"); there is no DR-specific V2.4.5.

## C-V24 gating
C-V24 stays sealed and unopened; no freeze or reveal while V2.4.4 gate 3 is unresolved. Sequence: V2.4.4 gates 1–5 all pass, or a later explicit external adjudication accepts a remaining result as a limitation and authorizes freeze (not pre-authorized now). Before implementation the evaluator renews the hash-only compatibility attestation (`c-v24-compatibility-attestation.json` in this directory). C-V24's immutable criteria are evaluated exactly as sealed; selective-redescription outputs are an additional scientific class and may not rewrite an old raw-selection challenge verdict. Escrow 830001:830600 remains closed until the frozen V2.4.4 runner validates the revealed plaintext through the public API.

## Revised V2.4 claim (adopted)
> Context-indexed redescription is supported when a materially occupied two-context representation is favored among live temporal alternatives and carries more compound structural evidence than expected under a cue-marginal-preserving conditional-randomization null. In genuine then/now worlds, that representation preserves historical predictions while present-context identity-root revision transfers to untreated cues.

Explicit limitation:
> Finite streams lacking systematic context dependence can nevertheless contain chance cue–marker alignments that rationally support a two-context posterior. Raw structural support is therefore not itself a selectivity test; selectivity is evaluated relative to each stream's conditional randomization distribution.

This distinguishes: (1) family selection; (2) within-family structural use; (3) evidence beyond finite-sample chance structure; (4) therapeutic consequence. The formed-P bridge licenses composition, not a formation-dependent prior: the same redescription and transfer route operates from a previously formed identity organization; the initial formed-state posterior does not enter the redescription-family prior (neutral and formed-bank shuffled failures are the same phenomenon).

## Post-V2.4 ladder (amended)
V2.4.4 → V2.5a (joint episodic vs marginal cue evidence) → V2.5b (full vs reduced structural comparison + do-over) → **V2.6a** (partner process and co-regulation) → **V2.3.4** (counterfactual action attribution) → V2.6b (one protector: trust, policy, access, future-risk counterfactual) → V2.7 (multi-protector, exiling, registration, polarization) → V2.8 (complete therapeutic trajectory). Amendment from round 3: V2.6a now precedes attribution — co-regulation depends on recursive-precision and root-evidence machinery, not safety-behavior causal attribution; attribution is required before V2.6b's protector future-risk claims.

## Permanent suite rules (adopted from V2.4's lessons)
1. Whenever a flexible structural family contains a simpler subcase, define and score the structural-existence proposition inside the family.
2. Whenever a finite null can instantiate the target statistic by chance, calibrate that statistic against a population-matched conditional null rather than demanding an arbitrary raw ceiling.

V2.5b must accordingly distinguish "the reduced family won" from material reduction, as V2.4 distinguishes CS selection from actual, selective two-context use.
