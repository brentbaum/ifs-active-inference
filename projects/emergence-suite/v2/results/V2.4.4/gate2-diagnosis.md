# V2.4.4 Gate-2 decomposition diagnosis

Status: **diagnosis only**. No engine, threshold, family, likelihood,
transition, prior, randomization definition, or criterion changed. No
V2.4.4 Gate-3 block was opened. The analysis uses only:

- the consumed Gate-2 CS worlds `790700:790799`; and
- the explicitly requested, consumed V2.4.3 genuine worlds
  `788500:788619`, marked non-criterial.

No new seed block was introduced.

Supporting per-world tables:

- `gate2-diagnosis-cs-crt-per_world.csv`: all 100 primary CS worlds,
  including `T0`, Q50/Q90/Q95/Q99, `p_CRT`, `E_null`, material status,
  `q1`, `BF_2C:1C`, transition parameters, realized path features, outcome
  contrast, and marker informativeness;
- `gate2-diagnosis-information-curves.csv`: the same 100 worlds at total
  lengths 32/64/96, corresponding to frozen pre-held-out prefixes
  24/48/72;
- `gate2-diagnosis-v243-genuine-crt.csv`: the 120 consumed V2.4.3 genuine
  worlds, explicitly descriptive and non-criterial.

Required constants:

- `B_max_inherited_formation = 3.801426508560692`
- `B_max_v24_common_emissions = 6.704414354964107`
- the two-context CS path prior is `pi1 = 0.92741935483871` at the
  24-slice reference prefix; it rises mechanically with path length to
  `0.9766233766233766` at 48 slices and `0.9886075949367091` at 72 slices.

## 1. Power decomposition

The 100 CS worlds separate into:

- 44 selective material worlds;
- 48 material but nonselective worlds; and
- 8 nonmaterial worlds.

### Primary separation

| quantity | selective material, n=44 | material/nonselective, n=48 | nonmaterial, n=8 |
|---|---:|---:|---:|
| mean `T0` | **11.101** | 8.040 | 0.839 |
| mean null `T_b` | 3.402 | **4.532** | 0.083 |
| mean Q95 | 8.800 | **10.389** | 2.445 |
| mean `E_null = T0-Q95` | **+2.301** | **-2.350** | -1.606 |
| mean `p_CRT` | **0.0160** | 0.2008 | 0.4140 |
| mean `q1` | approximately 1.0 | approximately 1.0 | 0.8537 |
| mean realized cue outcome contrast | **0.5419** | 0.4460 | 0.2988 |
| mean marker accuracy | **0.9515** | 0.9347 | 0.9305 |
| mean cue context-mix balance | 0.3254 | **0.3423** | 0.0347 |
| mean minimum-context occupancy | 0.3292 | **0.3452** | 0.0347 |
| mean switches in 72 slices | 12.80 | 13.00 | 2.25 |
| mean dwell | 8.12 | 7.36 | 35.80 |
| maximum dwell | 19.82 | 19.56 | 58.13 |
| generator `p00` | 0.7873 | 0.7938 | 0.8739 |
| generator `p11` | 0.8157 | 0.8007 | 0.8922 |

Material-but-nonselective worlds differ from selective worlds in **both**
directions relevant to power:

1. their observed compound statistic is lower by `3.06` log units; and
2. their Q95 null threshold is higher by `1.59` log units.

The resulting `E_null` separation is `4.65` log units. Roughly two thirds
of that group difference is lower observed evidence, and one third is a
stronger conditional null.

`q1` and the within-CS BF do not usefully distinguish the two material
groups: both are generally saturated near complete two-context occupancy.
The CRT failure occurs at the additional global/selectivity layer.

### Dwell and generator-parameter correlations

Across all 100 CS worlds, Pearson correlation with `p_CRT` was:

| feature | correlation |
|---|---:|
| realized cue outcome contrast | **-0.590** |
| marker accuracy | -0.310 |
| context switches | -0.256 |
| minimum-context occupancy | -0.350 |
| cue context-mix balance | -0.351 |
| mean dwell | +0.458 |
| maximum dwell | +0.424 |
| generator `p00` | +0.130 |
| generator `p11` | +0.188 |
| observed `T0` | **-0.731** |
| null mean | -0.150 |
| Q95 | -0.242 |

The apparent dwell correlations are driven chiefly by the eight
near-single-context, nonmaterial worlds. Restricting to the 92 material
worlds:

- mean-dwell Pearson/Spearman correlations with `p_CRT` are
  `+0.206/-0.027`;
- maximum-dwell correlations are `+0.228/-0.008`;
- switch-count correlations are `-0.114/+0.033`;
- `p00` and `p11` correlations are near zero;
- realized outcome-contrast correlations remain `-0.422/-0.542`;
- marker-accuracy correlations remain `-0.274/-0.251`; and
- `T0` correlations remain `-0.695/-0.630`.

Thus long-dwell structure explains loss of *material* support in the
eight extreme worlds, but it does not explain the 44-versus-48 selective
split among material worlds. The stronger predictors there are realized
context contrast and marker informativeness.

Cue count is fixed at three in all 100 worlds, so it has no variance and no
estimable correlation.

## 2. Why the conditional null is strong in genuine worlds

Every genuine CS world mixes then- and now-context observations inside each
cue's preserved outcome and marker multisets. Independent permutation
destroys their observed pairing, but it repeatedly draws new pairings from
multisets already containing:

- high and low outcome modes produced by the two context-specific cue
  tables; and
- then- and now-informative markers produced by those same contexts.

When cue-wise context mixing is balanced, many of the 999 permutations can
reconstruct an apparently coherent alignment by chance. This is visible in
the material/nonselective group:

- context-mix balance is slightly higher (`0.342` versus `0.325`);
- mean randomized `T_b` is higher (`4.532` versus `3.402`);
- Q95 is higher (`10.389` versus `8.800`).

But a strong null is only part of the failure. Selective worlds also have
larger realized cue contrast (`0.542` versus `0.446`) and higher marker
accuracy (`0.952` versus `0.935`), raising observed `T0` to `11.10`.
Material/nonselective worlds have weaker observed alignment (`T0=8.04`)
at the same time that their mixed marginals support a stronger null.

Therefore the 0.44 rate is not solely “null replicates are always high” and
not solely “genuine `T0` is low.” It is the conjunction:

- **lower `T0` in failing material worlds is the larger contribution**;
- **higher conditional-null Q95 is a substantial secondary contribution**.

The per-world table publishes the full requested null quantiles, allowing
either component to be audited without reconstructing the randomizations.

## 3. Descriptive information scaling

The same 100 worlds were evaluated at nested total lengths 32/64/96, with
pre-held-out prefixes 24/48/72.

| total / pre length | material rate | selective rate | mean `p_CRT` | mean `T0` | mean null `T_b` | mean `E_null` |
|---|---:|---:|---:|---:|---:|---:|
| 32 / 24 | 0.61 | **0.20** | 0.265 | 2.430 | 0.929 | -1.119 |
| 64 / 48 | 0.85 | **0.35** | 0.203 | 5.435 | 2.251 | -1.008 |
| 96 / 72 | 0.92 | **0.44** | 0.137 | 8.810 | 3.679 | -0.244 |

Selectivity power rises monotonically with information length, while the
mean p-value falls. Observed evidence grows faster than the conditional
null, and mean null excess moves toward zero. Nevertheless, at the final
authorized 96-slice budget, the gain reaches only `0.44`, not the frozen
`0.60`.

This is descriptive scaling on the same worlds, not a new criterion or a
license to extrapolate another length.

## 4. Comparison with consumed V2.4.3 genuine worlds

The 120 V2.4.3 genuine then/now worlds (`788500:788619`) were rerun only as
an explicitly consumed, non-criterial comparison population. They use the
32-slice design and therefore a 24-slice pre-held-out prefix.

| population | material rate | selective rate | mean `p_CRT` | mean `T0` | mean null `T_b` | mean `E_null` |
|---|---:|---:|---:|---:|---:|---:|
| Gate-2 CS generator, 32/24 | 0.61 | 0.20 | 0.265 | 2.430 | 0.929 | -1.119 |
| consumed V2.4.3 genuine, 32/24 | **0.708** | **0.30** | 0.276 | 3.015 | 1.174 | -1.359 |
| Gate-2 CS generator, 96/72 | 0.92 | 0.44 | 0.137 | 8.810 | 3.679 | -0.244 |

At the same 24-slice prefix, the V2.4.3 composition generator yields a
higher selective rate (`0.30` versus `0.20`) and stronger observed
statistic, despite a slightly higher null mean. Generator design therefore
matters.

However, the comparison population also reaches only 0.30. The result is
not exclusively a Gate-2-generator pathology: the CRT has limited power at
the shared short prefix under both genuine designs. The longer Gate-2
history improves power to 0.44 but does not reach 0.60.

## Diagnostic conclusion

The single Gate-2 failure decomposes as follows:

1. Material structural recovery is strong (`0.92`), and nuisance selective
   rates are exactly zero.
2. Among material worlds, dwell parameters do not separate selective from
   nonselective cases.
3. Selective worlds have stronger realized cue contrast and marker
   informativeness, producing higher `T0`.
4. Nonselective material worlds also have slightly more context-mixed
   cue-wise marginals, allowing their conditional randomizations to attain
   higher `T_b` and Q95.
5. Power improves from `0.20` to `0.35` to `0.44` with nested information
   length, but the final frozen criterion remains failed.
6. The consumed V2.4.3 comparison shows both a generator effect and a
   broader short-history CRT-power limitation.

No repair, threshold change, or successor is proposed. External
adjudication follows.
