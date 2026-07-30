# C-V30 immutable sealed verdict: PASS

The verdict above is the sealed-written result. Pass requires all five criteria.

## Criteria

1. **PASS** — `criterion_1_compile_sample_score`.
2. **PASS** — `criterion_2_exact_probability`.
3. **PASS** — `criterion_3_structure_recovery`.
4. **PASS** — `criterion_4_semantics`.
5. **PASS** — `criterion_5_custody`.

## Verdict classes

- Scientific-apparatus: PASS.
- Semantic: PASS.
- Custody: PASS.

## Cell results

- `cell_1_identity_no_danger`: accuracy 0.998571; ECE 0.000767; oracle error 2.842e-14; local error 1.208e-13.
- `cell_2_danger_plus_action`: accuracy 0.998286; ECE 0.000796; oracle error 4.263e-14; local error 1.279e-13.
- `cell_3_mixed_scope_dynamics`: accuracy 0.999714; ECE 0.000243; oracle error 1.421e-13; local error 4.832e-13.
- `cell_4_two_modes_full`: accuracy 0.999714; ECE 0.000232; oracle error 1.137e-13; local error 3.126e-13.

Raw traces were hashed before criterion aggregation. All 2,000 escrow seeds
were consumed once, ascending and gap-free. Frozen source identity was
31/31.

Post-run verification: V3 tests 13/13 green; frozen V2 tests 180/180 green.
