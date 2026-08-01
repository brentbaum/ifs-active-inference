# Population-B context ECE decomposition

This is read-only localization from the retained Population-B traces plus direct finite enumeration. No world seed, qualification seed, or generator was invoked. The reported sequential forecasts come from an independently written finite filter; frozen V2 scoring was used only on one retained history while validating that filter, with zero seed consumption.

## 1. Fixture identity

**Refuted.** The context fixture is not the frozen V2 context module's own prior predictive joint.

On the three-slice enumerable dummy, maximum joint-atom error is `0.078725454545454571` on the module's normalized full three-marker support. This exceeds `1e-10`. A separate descriptor-conditioned binary diagnostic is also non-identical (`0.057668302277815837`), but it is not substituted for the full-support joint proof.

Two productions differ:

1. The fixture starts every context-split path in `then` (`[1,0]`), while the frozen module prior is `[0.5,0.5]`.
2. The fixture samples `now` with the raw `P(now_marker)` and defines `then` as its complement. This moves all `none_marker` mass into `then`. The frozen module has a three-valued marker CPT; its binary bridge forecast conditions the `then/now` probabilities on a non-`none` token.

Correcting both productions in the descriptor-conditioned isolation gives maximum error `0`. This is a diagnosis calculation, not a repair.

## 2. Finite-sample ECE null

The estimator is exactly the qualification estimator: one token and total weight one per world, ten fixed bins by `P(target=1)`. Each null replicate independently draws each retained outcome from its own retained forecast probability.

| Target | Observed ECE | Null mean | q05 | q50 | q95 | q99 | Observed percentile | Beyond q99 |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| identity | 0.015095 | 0.011405 | 0.002773 | 0.010540 | 0.023733 | 0.029749 | 74.85% | no |
| outcome | 0.029141 | 0.021285 | 0.012377 | 0.021117 | 0.030899 | 0.035986 | 91.05% | no |
| context | 0.057465 | 0.022330 | 0.013708 | 0.021981 | 0.031983 | 0.036847 | 100.00% | yes |
| partner | 0.013578 | 0.015851 | 0.006932 | 0.015269 | 0.026630 | 0.031714 | 38.65% | no |
| contact | 0.027364 | 0.016611 | 0.007824 | 0.016045 | 0.027365 | 0.032223 | 95.00% | no |

Each Population-B context world contributes exactly one held-out context token after 48 prefix tokens. The JSON contains the complete 2,000-value null distributions and the per-bin forecast concentration tables for all five targets.

## 3. Context localization

The observed context ECE is beyond the parametric null's 99th percentile, so the discrepancy is localized below.

### Fixed-bin decomposition of the terminal context forecasts

| P(now) bin | Worlds | Mean P(now) | Observed now rate | Signed gap | ECE contribution |
|---|---:|---:|---:|---:|---:|
| [0.0, 0.1) | 90 | 0.082513 | 0.100000 | -0.017487 | 0.000787 |
| [0.1, 0.2) | 385 | 0.164698 | 0.187013 | -0.022315 | 0.004298 |
| [0.2, 0.3) | 422 | 0.245134 | 0.218009 | 0.027125 | 0.005726 |
| [0.3, 0.4) | 151 | 0.338415 | 0.258278 | 0.080137 | 0.006053 |
| [0.4, 0.5) | 77 | 0.447943 | 0.558442 | -0.110499 | 0.004256 |
| [0.5, 0.6) | 155 | 0.559243 | 0.529032 | 0.030211 | 0.002343 |
| [0.6, 0.7) | 200 | 0.657069 | 0.580000 | 0.077069 | 0.007711 |
| [0.7, 0.8) | 239 | 0.746308 | 0.690377 | 0.055931 | 0.006687 |
| [0.8, 0.9) | 138 | 0.845262 | 0.753623 | 0.091639 | 0.006326 |
| [0.9, 1.0) | 142 | 0.926353 | 0.739437 | 0.186917 | 0.013278 |

The largest single contribution is the `[0.9,1.0)` bin: 142 worlds forecast `P(now)=0.9264` on average, but `now` occurred in 0.7394 of them. That bin alone contributes 0.01328 ECE. Most bins above 0.6 also overpredict `now`; the `[0.4,0.5)` bin instead underpredicts it.

### Slice-position decomposition

| Window | Mean P(now) | Observed now rate | Signed gap | Direction | ECE |
|---|---:|---:|---:|---|---:|
| early_0_15 | 0.392635 | 0.338638 | 0.053997 | overpredicts now_marker | 0.071714 |
| middle_16_32 | 0.442969 | 0.406527 | 0.036442 | overpredicts now_marker | 0.059157 |
| late_33_48 | 0.446655 | 0.419460 | 0.027195 | overpredicts now_marker | 0.048169 |
| terminal_48 | 0.452489 | 0.413707 | 0.038782 | overpredicts now_marker | 0.057465 |
| all_0_48 | 0.427737 | 0.388582 | 0.039155 | overpredicts now_marker | 0.057875 |

The independently written sequential filter reproduces every retained terminal context forecast with maximum absolute error `6.66e-16`.

Here a positive signed gap means overprediction of the `now_marker` event; a negative gap means underprediction. It is not an argmax-confidence calibration statistic.

## Custody note retained

The earlier unit-test sink incident remains retained. The command was `python3 -m unittest tests.test_v36_round12 tests.test_v36_bridge`; its in-memory contexts were `test-v36-round12-calibration-state`, `test-v36-r1-public-dummy`, `test-v36-r1-forecast-semantics`, and `test-v36-r1-oracle`. It consumed zero seeds. This diagnosis does not revise that custody record.
