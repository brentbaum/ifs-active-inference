# V3.6 Gate-3 predictive noninferiority decomposition

Status: **DIAGNOSIS ONLY — no classification, repair, criterion, or floor.**

This run consumed the authorized diagnosis block `3665160:3667159` once, ascending and gap-free. All 2000 per-world records and runtime event ledgers were persisted to `gate3-noninferiority-diagnosis-traces.jsonl` and hashed (`646fd20d42b224aa37e7d82e55aa72c7520b3cf60fabe88371ba94e1eb29a9ca`) before aggregation. Gates 4–5, escrow, barred blocks, and scientific modules were not touched.

## Apparatus-first finding

The failed number is not a comparison on common predictive support. It combines V2's T/D/P formation likelihood over `(self value, outcome, localization)` with V3's GROW likelihood over `(mode, root, world, policy proposal, outcome)`. The two sides also use different history lengths and independently generated observations. Exactly **0 of 2000** observation documents were byte-identical. Same seed and a matched broad truth condition did not make the evidence streams equal.

This means the reported `-0.0339 nats/token` cannot yet be interpreted as V3 losing predictive accuracy to V2 on the same data. The localization below describes the software accounting that produced it; it does not replace or revise the committed Gate-3 verdict.

## 1. Support equality

V2 scored channels: `self_value, outcome, localization`. V3 scored channels: `mode, root, world, policy_proposal, outcome`. V2 histories had [18, 30] slices; V3 always had [16] slices. V2's nominal token counts were [54, 90], versus delivered-token counts [48, 85, 90]; V3's nominal and delivered counts were both [80] and [80].

In V2, collapsed-broadcast slices encode localization with the deterministic sentinel `2`. The Gate-3 denominator nevertheless counted that field as a token. V3's GROW cell used broad precision and full availability, so all five scored fields were delivered. The observation hashes, channel names, masks, and token counts therefore establish unequal support, not merely different numerical values.

## 2. Normalization

| Accounting | Mean V3 − V2 |
|---|---:|
| frozen nominal-token statistic | -0.033416471 nats/token |
| raw per-world total | -1.090724964 nats/world |
| delivered-token normalization | -0.002873688 nats/token |
| equal-weight truth-clamped channel-type rates | 0.026996490 |

The sign is not stable across these descriptive normalizations. It remains an unequal-support comparison in every row. The frozen calculation uses `3 × V2 slices` and `5 × V3 slices`; it is not one shared atomic-token denominator.

## 3. Per-channel decomposition

The table uses each model's truth-structure-clamped, exactly recombining likelihood factors. Because the supports differ, the last column is bookkeeping rather than a like-for-like predictive contrast.

| Channel/factor | V2 mean nats/world | V3 mean nats/world | V3 − V2 |
|---|---:|---:|---:|
| mode_signals | -14.876426 | -12.476618 | 2.399808 |
| outcomes | -16.089609 | -6.957245 | 9.132364 |
| partner | 0.000000 | 0.000000 | 0.000000 |
| support | 0.000000 | 0.000000 | 0.000000 |
| contact | 0.000000 | 0.000000 | 0.000000 |
| registration | 0.000000 | 0.000000 | 0.000000 |
| context_cue_emissions | -13.449780 | 0.000000 | 13.449780 |
| root | 0.000000 | -7.578967 | -7.578967 |
| world | 0.000000 | -8.021188 | -8.021188 |
| policy | 0.000000 | -8.074877 | -8.074877 |

Partner, support, contact, and registration are not present in either predictive quantity used by this tournament; each contributes exactly zero to the published deficit. The dominant deficit is not a matched channel. It is the structure/model-averaging term described next. Among the raw likelihood factors, V3 additionally pays about 7.58–8.07 nats/world each for root, world, and policy observations that V2 never scores. The V2-specific object is the compact, normalized joint T/D/P slice likelihood—especially its localization/configural production. Accordingly, no scientifically valid statement such as “V2 wins on partner evidence” or “V3 loses on outcome evidence” follows from this comparison.

## 4. Structure versus parameters

Clamping both scorers to their own generating structure gives a mean parameter-predictive component of **-0.004110644** nats/nominal-token. The residual contribution of structure prior/model averaging is **-0.029305827**. They recombine to **-0.033416471**, with maximum numerical error `1.94e-16`.

V2's model-evidence-minus-truth-likelihood term is **-1.369782 nats/world**; V3's is **-3.767427 nats/world**. Their normalized difference accounts for **87.7%** of the mean nominal-token deficit. Thus the miss is mostly structural/model-averaging under the frozen, unequal-support accounting: the three-state V2 menu concentrates prior/model mass much more cheaply than the 128-program V3 GROW space. “Parameter-predictive” here does not mean bad parameter inference; it includes the cost of scoring different channel families.

## 5. Calibration cross-check

| Model | accuracy | ECE | mean truth probability | normalized posterior entropy |
|---|---:|---:|---:|---:|
| V2 T/D/P | 0.995000 | 0.002937 | 0.991206 | 0.013242 |
| V3 GROW graph | 0.025000 | 0.286314 | 0.065304 | 0.464943 |

The reported 6C profile did **not** measure calibration on this tournament population. Gate 3 copied Gate 2's results from 64-slice, prior-sampled recovery worlds (Gate-2 ECE 0.01183 and exact-program accuracy 0.5696). These diagnosis worlds use a fixed 16-slice formation configuration. On them, exact-program accuracy is 0.025, ECE is 0.286, and normalized posterior entropy is 0.465. So the answer is not simply “well calibrated but honestly diffuse”: the referenced profile missed this population. Some of the apparent failure can reflect observationally equivalent graph programs, but the exact-structure statistic is plainly not calibrated here. This remains distinct from the predictive comparison, which also lacks common support.

## 6. Distribution and subclasses

V2's nominal-token advantage has mean **0.033416471**. Overall quantiles are `{"q00": -0.31413387974119655, "q01": -0.171586822486009, "q05": -0.11655765316431085, "q100": 0.4192149671252704, "q25": -0.04035977892531442, "q50": 0.02287453525726202, "q75": 0.0956330868165304, "q95": 0.22553340966042804, "q99": 0.29989984937660574}`.

| Subclass | n | mean V2 advantage | q05 | median | q95 |
|---|---:|---:|---:|---:|---:|
| stratum=acute_one | 500 | 0.149440 | -0.017940 | 0.148234 | 0.293983 |
| stratum=chronic_multiple | 500 | 0.011239 | -0.100754 | 0.011198 | 0.120768 |
| stratum=chronic_one | 500 | 0.009165 | -0.109901 | 0.009788 | 0.119508 |
| stratum=real_danger_adaptive | 500 | -0.036177 | -0.155125 | -0.037066 | 0.071039 |
| truth_mode_count=1 | 1500 | 0.040809 | -0.123956 | 0.028641 | 0.246971 |
| truth_mode_count=3 | 500 | 0.011239 | -0.100754 | 0.011198 | 0.120768 |
| truth_topology=allied | 666 | 0.034580 | -0.114571 | 0.021574 | 0.229055 |
| truth_topology=independent | 667 | 0.034088 | -0.112889 | 0.025678 | 0.223369 |
| truth_topology=opposed | 667 | 0.031583 | -0.120101 | 0.019494 | 0.221405 |

These strata localize which independently generated evidence schedules drive the number. They are not common-world treatment effects.

## Custody and stopping point

No criterion was evaluated. No scientific source, threshold, floor, Gate-4/5 artifact, escrow, or barred seed was touched. The committed Gate-3 FAIL remains intact and unclassified pending evaluator adjudication.
