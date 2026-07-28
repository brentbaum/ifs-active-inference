# Sealed challenge C-V233-M-bank — formed-world bank qualification

**Sealed by evaluator after the phase-1 public artifacts (contract, analysis plan, dummy, parameters) and before any V2.3.3 implementation. Runs on the frozen V2.3.3 stage with zero new engine code. Purpose: verify the frozen bank constructor yields a sufficient formed population WITHOUT posterior assignment, before any maintenance seed opens. If this fails, C-V233-M's seeds remain closed.**

**Pre-seal linter record:** every referenced quantity is a frozen public-plan field (eligibility rules, 40-per-stratum minimum, the three q0(P) strata, first-eligible ordering, ITS ledger schema, provenance audit); reference population = evaluation population (fresh developmental histories from the frozen V2.3.2 generators at the seeds below); units consistent (world counts, posterior ranges); criteria classified below; each failure interpretation stated; evaluable on the public dummy schema.

## Configuration
Candidate seed block 815001:815800, consumed in order by the frozen bank constructor and frozen eligibility rules (first-eligible, no selection beyond the frozen rules, no regeneration).

## Criteria
1. *(scientific precondition)* Within the 800-seed block, each stratum (moderate 0.60–0.75, strong 0.75–0.90, very strong 0.90–0.98 on q0(P)) reaches ≥ 40 eligible worlds. Report the eligibility rate per stratum with 95% intervals and the seed index at which each stratum filled.
2. *(semantic integrity)* No posterior assignment anywhere in bank construction: the provenance audit shows every state variable arriving via the frozen V2.3.2 update equations from neutral priors; the one-posterior audit passes on ten randomly drawn bank states.
3. *(custody)* Every banked state serializes and rehashes identically on reload (bitwise), and the ITS ledger lists all candidate seeds with eligibility decisions and exclusion reasons, no gaps.
4. *(distributional stress, descriptive only — no pass/fail)* Publish the q0(P) distribution across all candidates and the per-stratum fill curves.

Pass = criteria 1–3. Failure interpretations, pre-committed: a stratum shortfall is a formation-yield finding about the frozen constructor (reported per stratum; maintenance stays closed; no regeneration or rule change may rescue it in this cycle); a provenance or custody failure is an architecture failure of the bank procedure.
