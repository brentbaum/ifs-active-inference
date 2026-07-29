# V2.4.4 Gate 3 — adjudicated mixed-verdict continuation

Outcome: **FAIL — honest stop before Gate 4**.

The formal Gate-2 verdict remains **FAIL**. The round-5 adjudication allowed
only the two per-world selective-material-redescription rate failures to
continue. Both occurred:

- genuine then/now: `0.2333 < 0.60`;
- formed-P bridge genuine arm: `0.2833 < 0.60`.

They are recorded as adjudicated non-blocking failures. Gate 3 nevertheless
fails because both separately frozen population-level null-excess criteria
missed:

- genuine mean `E_null = -1.2024`, 95% CI
  `[-1.5786, -0.8294]`; required lower bound `> 0`;
- bridge mean `E_null = -1.0104`, 95% CI
  `[-1.4027, -0.6261]`; required lower bound `> 0`.

These are blocking failures under
`stage-progression-authorization.json`. No Gate-4 seed was opened.

## Exact-family predictive assays

| generating family | mean BMA regret | 95% CI | upper bound <= .01 |
| --- | ---: | ---: | --- |
| global down-weight | 0.00485 | [0.00327, 0.00642] | pass |
| cue-local relearning | 0.00498 | [0.00317, 0.00671] | pass |
| context split | 0.00123 | [-0.00026, 0.00269] | pass |
| continuous drift | 0.00598 | [0.00388, 0.00837] | pass |
| change point | 0.00088 | [0.00065, 0.00113] | pass |

The 96-slice CS population had `499/500` matched worlds. Its mean held-out
margin was `0.10364` nats/token, 95% CI `[0.09310, 0.11443]`; all three
matched-margin criteria passed. The same 2,500 worlds' 32- and 64-slice
information curves are descriptive and retained in `gate-3.json` and the
per-world file.

## Structural controls

| population | raw CS | material | selective | frozen result |
| --- | ---: | ---: | ---: | --- |
| continuous drift | 0.0083 | 0.0083 | 0.0000 | pass |
| change point | 0.0000 | 0.0000 | 0.0000 | pass |
| cue-local relearning | recovery 0.6833 | 0.0250 | 0.0000 | pass |
| genuine shuffled | 0.5333 | 0.3750 | 0.0667 | selective ceiling pass |
| genuine single-regime | 0.3583 | 0.0000 | 0.0000 | pass |
| bridge shuffled | 0.6333 | 0.4917 | 0.0500 | selective ceiling pass |
| bridge single-regime | 0.4750 | 0.0000 | 0.0000 | pass |

Raw shuffled material support is descriptive by the frozen amendment.
Every selective ceiling and every single-regime material ceiling passed.

## Composition and bridge outcomes

| estimand | genuine then/now | formed-P bridge | requirement |
| --- | ---: | ---: | --- |
| raw CS rate | 0.7000 | 0.7667 | >= 0.60, pass |
| material rate | 0.6250 | 0.6500 | >= 0.60, pass |
| selective rate | 0.2333 | 0.2833 | >= 0.60, adjudicated failure |
| mean split log BF | 8.6906 [7.2662, 10.1421] | 10.5535 [9.0376, 12.0760] | lower CI > 0, pass |
| mean `E_null` | -1.2024 [-1.5786, -0.8294] | -1.0104 [-1.4027, -0.6261] | lower CI > 0, **blocking fail** |
| held-out margin | 0.1251 [0.0777, 0.1783] | 0.0817 [0.0466, 0.1195] | mean >= .01 and lower CI > 0, pass |
| root-mediated transfer | 0.3797 [0.3643, 0.3926] | 0.4407 [0.4010, 0.4801] | mean >= .05 and lower CI > 0, pass |
| present indexing | 0.3797 [0.3638, 0.3929] | 0.4407 [0.3998, 0.4808] | mean >= .05 and lower CI > 0, pass |

All 120 neutral worlds were complexity-matched. The bridge had `117/120`
matched worlds, retained exact 40/40/40 stratum balance, and passed bitwise
clone identity. Maximum historical-retention error was `0` neutral and
`1.11e-16` bridge; zero-association and G-fixed effects were exactly zero.

## Custody and distributions

Every original Gate-3 criterion was computed. The per-world JSON files
retain candidate posteriors, path-class quantities, transition/occupancy
posteriors, ELL and complexity fields. The compressed NPZ files retain all
999 conditional-randomization statistics for every audited world.
The cached runner path was checked against the frozen public helpers on
retained public seed `790700` at 32/64/96 slices: every family weight,
family log score, BMA score, regret, held-out score, complexity, matched
margin, and material classification agreed exactly (maximum error `0`).
Misspecification remains descriptive: 240 worlds, mean hindsight-best minus
BMA `0.09614` nats/token, material rate `0.1083`, selective-material rate
`0.0458`, mean `p_CRT = 0.5983`, maximum update-identity error `8.88e-15`,
and maximum decomposition error `4.26e-14`. Full family-posterior
trajectories and candidate decompositions are retained per world.

Required constants are unchanged:

- `B_max_inherited_formation = 3.801426508560692`
- `B_max_v24_common_emissions = 6.704414354964107`
- `pi1 = 0.92741935483871` at 24 pre-held-out slices
