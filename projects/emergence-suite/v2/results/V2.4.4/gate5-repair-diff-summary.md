# V2.4.4 Gate-5 cue-shape software repair

Authorization: `gate5-software-repair-authorization.md`, committed at
`e60a0c8`. Classification: pure software error; invalidate and repeat.

## Exact repair scope

Only cue-shape handling changed:

1. `ref/v24.py` now centralizes cue-ID-to-frozen-template mapping in
   `_cue_template_index`. The mapping is the modulo behavior already used by
   the frozen scorer: cue IDs index the three unchanged cue-meaning
   templates.
2. Cue-local generation allocates the unchanged three template-specific
   latent filters and maps supported cue IDs through those filters. It no
   longer requests an undeclared `cue_4` parameter row.
3. Context-split and change-point generation map cue IDs through the same
   unchanged three-entry baseline/corrective likelihood tables instead of
   directly indexing those tables with cue ID 3.
4. The independent enumeration oracle replaces literal `3` cue-template
   shapes with `len(BASELINE)` and uses the same cue-template index helper.
   Its three-cue behavior is unchanged.
5. `tests/test_v24.py` adds a regression test that generates and scores all
   five families at cue counts 2 and 4 using public development seeds.

No likelihood value, prior, transition, candidate family, threshold,
randomization, information budget, seed block, protocol, or frozen
parameter changed.

## Verification before rerun

- The failure reproduced identically twice before repair.
- All five families now generate and score at cue counts 2 and 4.
- The retained seed-790700 identity audit at 32/64/96 slices is bitwise
  identical to pre-repair commit `e60a0c8` for every required quantity.
  Pre/post serialized SHA-256:
  `45a61a9c383f6c1ef0b0e1cbf3a4bd6b3e698558087b1f5da7f3f290c5cfb25e`.
- The full unit suite passed `94/94` tests in `420.603` seconds.
