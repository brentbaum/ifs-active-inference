# V2.5a format-core stage report

**Format-core disposition:** `ADJUDICATED_MIXED`  
**V2.5a stage verdict:** `OPEN_PENDING_MASTER_SPEC_COMPLETION_PASS`  
**Sealed challenge:** not authored or opened in this arc

The evaluator-authored format core is complete on its committed Epoch-A
blocks. It establishes the presentation operator, exact derived-marginal
candidates, episodic-information accounting, and formed-state composition.
The single V2.5a stage remains open because the reconciliation note requires
the post-R0 master-spec completion pass before a stage-level verdict.

## Gate standing

| Gate | Standing | Result |
|---|---|---|
| Stage 0 | Complete | Exact channel marginals were computable through the frozen API. The range-only pilot froze all three 0.01 criteria before assay execution. |
| 1 | PASS | All 10 semantic proofs passed. Factorization error was `4.44e-16`; increment-identity error `8.88e-16`; the independent CS oracle differed by `4.44e-16`. |
| 2 | PASS | Carrying ΔI/token was `0.062724`, 95% CI `[0.058371, 0.067088]`, versus SESOI `0.01`. Independent maximum absolute ΔI was `1.13e-14`. |
| 3, original | FAIL retained | Three failures were preserved verbatim and adjudicated separately. |
| 3, decomposition repair | PASS | The endpoint-likelihood software defect was repaired narrowly. Identity held 120/120 with maximum error `0.0`; all non-decomposition quantities were byte-identical. |
| 4 | PASS | All three selective lesions passed on 80 worlds each. |
| 5, original | FAIL retained | The verifier omitted the committed V2.4.4 manifest addendum. Every other blocking check and the 129-test suite passed. |
| 5, repaired | PASS under adjudicated mixed disposition | One shared public manifest-chain helper verified V2.4.4 and R0 effective chains. All deterministic scientific and cumulative artifacts were byte-identical; the enlarged suite passed 131/131. |

## Gate-3 adjudicated findings

### Machinery identities established

The format machinery satisfies its exact obligations:

- factorized candidates have ΔI equal to zero to enumeration tolerance;
- cumulative ΔI exactly recombines the joint-minus-derived evidence;
- both accountings satisfy the cumulative constitutions;
- presentation labels and derived candidates remain analysis-only under the
  one-posterior audit;
- Gate-2 association-carrying evidence exceeded the frozen SESOI.

### Dose matching criterion retired

The `m*/n`-monotone-by-dose criterion is
`RETIRED_CONSTRUCT_INVALID`. The dose operator permutes markers only, while
the matching target reads only the root channel. Dose therefore cannot alter
the target or matched sample size under the frozen likelihood. It was not
evaluated in Gates 4–5 and has no replacement within this format-core arc.
The separate ΔI dose-response assay passed.

### Matching-lattice limitation retained

All 120 formed-bank scans reached their targets, but 17 targets lay off the
fixed per-slice KL lattice: no prefix through 8n was within 0.01. This is
retained as the named `MATCHING_LATTICE_LIMITATION`, not relabeled as
information-matched and not repaired by changing the tolerance.

For the 103 within-tolerance worlds, the joint-minus-matched-marginal bridge
contrast was:

`0.063137`, 95% CI `[0.044628, 0.084270]`.

Rounded as preregistered for synthesis: **0.063 [0.045, 0.084]**.

### Decomposition repaired

The original increment trajectory used the fixed 0.85 root likelihood while
its contract-facing endpoint used bank-specific reliability. The authorized
repair changes only that trajectory to the endpoint likelihood. The
original FAIL remains in the record; the repaired execution passed 120/120,
and every non-decomposition field was byte-identical.

## Gate 4

- association severed: maximum absolute ΔI `0.0`; channel-marginal change
  `0.0`;
- root broadcast severed: maximum root-movement difference `0.0`; local ΔI
  survived in 80/80 worlds and changed by at most
  `2.220446049250313e-15`;
- mis-declared matching target: custody audit detected 80/80.

## Gate 5 and shared manifest-chain repair

The complete block `761000:763999` was executed and then reexecuted under the
authorized software repair. Length 32/64/96, cue-count, missingness,
one-at-a-time parameter, cue-root-strength, and presentation-schedule sweeps
all retained their declared semantics. Maximum increment-identity error was
`2.8199664825478976e-14`; maximum factorized absolute ΔI was
`1.354472090042691e-14`.

The public `ref.manifest_chain.verify_manifest_chain` function now supplies
one implementation for future Gate-5 custody:

- V2.4.4: base 86 files, effective 87 files, zero mismatches;
- R0: base 27 files, effective 31 files after the committed escrow amendment
  and shared-helper refactor, zero mismatches.

The repaired execution preserved every recorded non-manifest quantity and
every deterministic raw/cumulative artifact byte-for-byte. Its fresh full
suite passed **131/131** in `431.294` unittest seconds.

## Constants and custody

- `B_max_inherited_formation = 3.801426508560692`;
- `B_max_v24_common_emissions = 6.704414354964107`;
- `B_max_v25a_marginal_accounting = 6.704414354964107` (not distinct).

Consumed Epoch-A blocks:

- pilot `755000:755199`;
- Gate 2 `756000:756399`;
- Gate 3 `757000:759239` as assigned, with intentional gaps untouched;
- Gate 4 `760000:760239`;
- Gate 5 `761000:763999`.

The master-spec completion blocks and C-V25A escrow remain outside this
format-core result. This report does not close V2.5a and does not authorize a
sealed challenge.
