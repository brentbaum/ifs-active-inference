# V2.5a Gate 3 — format-core open assays

Outcome: **FAIL**. Blocking failures: `['assay2_median_ratio_monotone', 'assay3_information_matching_within_tolerance', 'assay3_exact_per_slice_decomposition']`.

Dose means `[-0.053326561819605364, -0.027250406847702142, -0.004152812013420743, 0.02425118093583654, 0.049006156179246474, 0.068174070671589]`; slope interval `(0.12352526349801067, 0.1139912237400776, 0.13291585307978382)`.

Matching censoring `(0.0, 0.0, 0.012643429997735661)`; median m*/n `[0.0625, 0.0625, 0.0625, 0.0625, 0.052083333333333336, 0.052083333333333336]`.

The nominal bridge joint-minus-marginal contrast was `(0.06110931706890421, 0.0440254665602233, 0.08099266920399958)` against SESOI `0.01`, but it is not a valid information-matched result: only `103/120` worlds were within the frozen `0.01` KL tolerance (median error `0.005347834072338131`, q95 `0.19950524242254006`, maximum `1.2075223097091734`). Strata were `{'moderate': 40, 'strong': 40, 'very_strong': 40}`.

`B_max_inherited_formation = 3.801426508560692`; `B_max_v24_common_emissions = 6.704414354964107`; `B_max_v25a_marginal_accounting = 6.704414354964107`.
