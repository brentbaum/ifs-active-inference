# Sealed challenge C-V233-M — evidence-shaping maintenance

**Sealed by evaluator after the phase-1 public artifacts and before any V2.3.3 implementation. Runs on the frozen V2.3.3 stage with zero new engine code, ONLY after C-V233-M-bank passes. All estimands, tolerances, CI machinery, and arm semantics are the frozen analysis plan's; this seal contributes the private world variation and the criterion set.**

**Pre-seal linter record:** every referenced quantity is a frozen public-plan field (L^PT/L^PD, M^PT/M^PD, the 1e-10 mechanistic tolerances, the dose grid c ∈ {0,.25,.5,.75,1}, stratum definitions, paired-within-stratum bootstrap CIs, the yoked-replay construction, verdict classes); reference population = evaluation population for every criterion (all contrasts are paired within this challenge's own worlds — no external baseline quantity of any kind is referenced); no tail-percentile criterion appears anywhere; criteria classified inline; failure interpretations pre-committed.

## Configuration (private variation)
120 paired base worlds from seed block 816001:816900 (first eligible per the frozen rules, stratum-balanced 40/40/40 drawn from the qualified bank), with evaluator-varied cells crossing:
- Initial P strength: the three bank strata.
- Censoring rate: the frozen dose grid, plus cells at c drawn per-seed from {0.35, 0.65} (interpolation cells the open battery never used).
- Safe-evidence reliability: two levels (high; degraded-but-informative).
- Action cost: two levels (the frozen default; elevated).
- Censoring schedule: front-loaded vs distributed (same total c).
- Action labels: permuted in half the worlds (label permutation must change nothing scientific).
- Danger type: external-only vs identity-implicating cells (per the frozen T/D/P discriminator machinery).
- One context shift mid-run in a quarter of the worlds.

## Criteria (classes marked)
1. *(scientific)* Safe full observation erodes P: ΔL^PT and ΔL^PD upper 95% CI < 0 in arm-A-equivalent cells.
2. *(scientific)* Censoring protects: M^PT and M^PD lower 95% CI > 0, in the full population and within each stratum.
3. *(scientific + semantic)* Complete censoring (c = 1) does not strengthen P: max |ΔL^PT|, |ΔL^PD| ≤ 1e-10 in the isolated protocol cells.
4. *(semantic)* Closed-loop vs yoked replay: candidate evidence and posteriors within 1e-10 wherever delivered streams are identical.
5. *(semantic)* No action bonus: avoidance-with-observed-safety, sham, and response-prevention cells with literally identical delivered evidence are numerically identical on structural evidence; label-permuted worlds change nothing scientific.
6. *(scientific)* Dose response: retention monotone in c across the seven dose points (isotonic p ≤ 0.05), with the mechanistic identity primary — final evidence equals the exact sum of delivered per-slice BFs (≤ 1e-10) in every world, including the interpolation and front-loaded/distributed cells (schedule shape must not matter at matched delivered evidence).
7. *(scientific)* D/P danger control: external-only danger cells select D over P (D-selection ≥ 0.80); identity-implicating cells may preserve P; generic adversity does not raise P beyond the frozen null band.
8. *(scientific)* Root/transfer follows delivered evidence: observed cells show more root revision and untreated-cue transfer than matched censored cells (paired CI > 0); the frozen fixed-G control removes transfer while leaving the maintenance contrast intact.
9. *(semantic + custody)* The full cumulative constitution (including the graded-update criterion) passes on the challenge trajectories; frozen-identity hashes verify; seeds within block; ITS ledger complete.

Report by verdict class (scientific / semantic / stress / custody) beneath the single preregistered challenge verdict (pass = all nine). Failure interpretations, pre-committed: a criterion-2 failure at intact criteria 1/3/4 means censoring does not protect in this model class — a genuine C1b negative, retained; a criterion-4 or -5 failure is an architecture failure (an action-route leak); a criterion-6 mechanistic-identity failure means undeclared evidence pathways; a criterion-7 failure revives the D/P conflation and blocks V2.4 pending adjudication.
