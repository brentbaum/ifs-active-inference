# V3.4 Gate 5 stop — 32-slice exact-program recovery

## Verdict

`FAIL`

V3.4 stops at Gate 5. No freeze-readiness record or freeze manifest is
produced, and C-V34 escrow `4040000:4043999` remains untouched.

## Blocking result

The 32-slice recovery cell attained exact four-edge program accuracy `0.733`,
below the Gate-2-frozen floor `0.78`.

This failure is localized to simultaneous recovery of the complete four-edge
program at the shorter information length. The same cell passed every other
declared check:

| Metric | Result | Criterion |
|---|---:|---:|
| minimum edge accuracy | 0.845 | >= 0.84 |
| `L_PREC` accuracy | 0.900 | >= 0.84 |
| `L_Y` accuracy | 0.845 | >= 0.84 |
| `PA_RY` accuracy | 0.969 | >= 0.84 |
| `L_TRANSITION` accuracy | 0.975 | >= 0.94 |
| root accuracy | 0.797 | >= 0.74 |
| structure ECE | 0.02019 | <= 0.08 |
| root ECE | 0.01336 | <= 0.08 |
| 95% structure-set coverage | 0.975 | >= 0.93 |
| maximum normalization error | 1.43e-14 | <= 1e-10 |
| maximum independent-oracle error | 5.68e-14 | <= 1e-10 |

The discrepancy between passing edgewise recovery and failing exact-program
recovery is combinatorial: a world counts as an exact-program error when any
one of the four edge decisions is wrong. This report does not adjudicate
whether the 48-slice floor was appropriate for the 32-slice robustness cell;
the criterion was executed as authored and the miss stands.

## Other Gate-5 cells

All other recovery cells passed the full frozen recovery battery:

- 96 slices: exact-program accuracy `0.915`;
- transition stay `0.75`: `0.841`;
- code-length scale `1.5`: `0.832`.

All scientific robustness cells passed:

- candidate-common missingness retained positive root uptake;
- reduced relational-channel information retained the reliable-versus-
  soothing-noncontingent trust distinction;
- altered partner-action prevalence retained positive root uptake;
- broadcast repetition retained exact local identity and positive additional
  root uptake.

All V3.0–V3.3 freeze manifests verified, and all Gate-5 trace ledgers passed
their hashes and record counts.

## Bounds and custody

- `B_max_v34_relational = 3.8066624897703196`
- `B_max_v34_root = 1.9736255489018601`
- Gate-5 block `3412000:3419999` was consumed once and serialized.
- C-V34 escrow was not opened.
