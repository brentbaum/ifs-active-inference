# Sealed challenge C-V233-M-bank2 — sampling-adequacy requalification

**Sealed by evaluator after the bank2 adjudication, compatibility attestation, and public sampling plan were committed. Runs on the frozen V2.3.3 stage (3e9bad2 + seed-authorization repair) with zero new engine code. One retry only, per the committed stop rule. The two prior bank verdicts stand untouched.**

**Pre-seal linter record:** every referenced quantity is a committed public field (the three bands, first-40 rule, saturation exclusion, 5,504-candidate budget and its rationale, census coordinates, ITS ledger schema, verdict classes); reference population = evaluation population (the fresh block below); no external baseline quantity; criteria classified; failure interpretations pre-committed; the interpretation lock from the public plan applies verbatim.

## Configuration
Candidate seed block **820001:825504** (5,504 seeds), consumed once, ascending, in full — no early stopping. Frozen constructor and eligibility rules; released-block authorization logged in the ledger.

## Criteria
1. *(scientific sampling adequacy)* ≥ 40 eligible states in each of moderate, strong, and very-strong bands; the first 40 per band retained; no posterior assignment or trajectory continuation anywhere.
2. *(semantic integrity)* Exact provenance reconstruction for all 120 retained states; one-posterior audit; constructor source audit confirming no band threshold inside the state constructor and no maintenance result read during qualification.
3. *(process custody)* All 5,504 seeds consumed once in ascending order; gap-free ITS ledger; every candidate state serializes/reloads/rehashes bitwise; no maintenance seed opened; no early stopping.
4. *(distributional census, non-criterial)* The full census per the public sampling plan, including the m0 log-evidence-margin coordinate and the descriptive comparison to the 800-seed block (no pooling for the verdict).

Pass = criteria 1–3. Failure interpretations, pre-committed: a band shortfall at this budget concludes the equal-band design incompatible with the frozen constructor's endpoint geometry (stop rule fires: C-V233-M archived unopened; V2.3.3b designed); integrity/custody failures are architecture failures. On PASS, the evaluator releases the unchanged C-V233-M seeds (816001:816900).
