# Sim 1 Magic Numbers — T4.6 Two-Arm Pilot

All outcome-based calibration used PILOT seeds 1001–1010 only. No confirmatory
seed was run. The prior exact-yoking pilot is superseded, but its tuning
provenance remains disclosed because the two-arm pilot inherited its learner
and behavioral classifier.

## Criteria amendment values fixed before the two-arm pilot

| Constant | Value | Provenance |
|---|---:|---|
| `arm_contrast_margin_cells` | 2 | Fixed before execution as A1.5's minimum nontrivial contrast, matching S1.1a's independently required connected-region size. |
| Relief trials: approach / flee / appease / attenuate | 1 / 3 / 2 / 0 | Fixed before execution as world contingencies. Kappa changes success probability only; the relief durations never vary by kappa or arm. |
| Potential hazard probability | `clamp(0.08 + 0.31*omega, 0.06, 0.97)` | Inherited fixed omega coupling. The schedule is identical across kappa in both arms. |
| Evidence precision / aversive severity | 1.0 / 1.0 | Fixed across omega, kappa, and arm. |
| `connected_region_min_cells` | 2 | Inherited requirement; rejects isolated one-cell specks. |

## Pilot-calibrated values inherited from superseded Step A

| Constant | Frozen value | Pilot provenance |
|---|---:|---|
| `learning_rate_arousal_gain` | 60.0 | Superseded exact-yoking pilot compared 26, 40, 60, 80. Gain 60 gave the clearest low-change tail without 80's larger count writes. The corrected mixed-cell rule later killed the connected yoked region. |
| `behavior_frozen_max_change` | 0.15 | Superseded pilot inspected 0.10, 0.12, 0.15, 0.18. It is outcome-selected and retained unchanged for the two-arm falsification attempt. |
| `behavior_revisable_min_change` | 0.25 | Superseded pilot selected a clear >=25 percentage-point prediction/policy movement and preserved a 0.10 unclassified gap above the frozen cutoff. |
| `threat_prediction_threshold` | 0.40 | Superseded pilot compared 0.40, 0.45, 0.50; 0.40 is above the untrained approach threat prior of 1/3. |
| `cell_classification_rate` | 0.50 | Superseded pilot compared 0.40, 0.50, 0.60. A 5/10 frozen and 5/10 revisable tie is mixed and enters neither region. |
| `slow_path_omega` | 1.00 | Superseded pilot tested 0.70–1.10. The two-arm pilot additionally tested 0.40–1.10; 1.00 is below the 1.18 acute cutoff and, with 600 trials, is the shortest tested schedule meeting both 8/10 crossing margins. |
| `slow_path_kappa` | 0.0 | Fixed no-control chronic route; kappa affects action efficacy only. |
| `slow_path_trials` | 600 | Two-arm pilot tested 300, 450, 600, 900, 1200. At omega 1.00, 600 met 8/10 original and shuffled crossing; longer schedules did not improve both margins. |

### Slow-path PE clarification

During this pilot, S1.3 was clarified to measure the PE at the behavioral
crossing event: maximum crossing-trial PE across crossed chronic seeds versus
the acute closed-loop frozen seed-cell minimum. The previous implementation
used the maximum PE anywhere in the full 600–1200-trial chronic history, which
penalized rare surprises unrelated to the crossing event and was not the
criterion's stated comparison. Candidate omega centers 0.40–1.10 never passed
that history-maximum implementation. This clarification is disclosed as
pilot-stage metric selection and must be frozen before confirmatory work.

## Spawn diagnosis — original scale retained

The original posterior-predictive scale did generate below-threshold events,
but no persistent high-arousal failure. Candidate `crp_threshold_base` values
were tested on the full closed-loop grid using seeds 1001–1010:

| Base cutoff | Flagged failures | Spawn events | Max pressure |
|---:|---:|---:|---:|
| 0.085 | 197 | 0 | 0.617702 |
| 0.12 | 927 | 0 | 0.617702 |
| 0.16 | 2,281 | 0 | 0.617702 |
| 0.20 | 2,558 | 0 | 0.617702 |
| 0.24 | 4,283 | 0 | 0.699932 |
| 0.30 | 6,953 | 0 | 0.699932 |
| 0.40 | 28,955 | 0 | 0.699932 |
| 0.50 | 43,028 | 0 | 0.699933 |
| 0.60 | 67,236 | 0 | 0.739301 |
| 0.80 | 160,397 | 0 | 0.780615 |

The spawn-pressure gate is 2.45. Even a cutoff of 0.80—high enough to label
nearly every ordinary binary observation a predictive failure—did not produce
sustained arousal pressure. Rescaling the posterior-predictive cutoff therefore
does not repair spawning. `crp_threshold_base=0.085` is retained, and
formation-by-spawning is reported dead in this binary environment class.

## Other inherited fixed values

| Constant | Value | Basis |
|---|---:|---|
| `crp_concentration` | 0.34 | Existing CRP prior; A1.2 reruns 0.5x, 1x, 1.5x. |
| `spawn_pressure_threshold` / decay | 2.45 / 0.72 | Existing persistent-failure gate and memory. Not altered after the diagnostic showed the posterior cutoff was not the problem. |
| Formation / probe / postformation trials | 72 / 24 / 18 | Existing common budgets. |
| Base learning rate / cue weight / probe rate | 0.16 / 0.55 / 2.0 | Existing Dirichlet write values. |
| Policy softmax temperature | 1.0 | Existing EFE scale. |
| Arousal PE scale / reflexivity slope | 5.2 / 0.88 | Existing maps to arousal and write-time reflexivity. |
| Safe / aversive preference | 1.35 / -2.35 | Existing EFE preferences. |
| Ambiguity / epistemic weights | 0.10 / 0.28 | Existing EFE terms. |
| Attenuation precision / information / cost | 0.34 / 0.18 / 0.80 | Existing covert-policy model. |
| Overt action cost | 0.03 | Common approach/flee/appease cost. |
| Attenuation corner omega / kappa | 2.65 / 0.16 | Existing S1.4 corner. |
| Acute-region omega cutoff | 1.18 | Existing S1.3 acute reference. |
| Omega grid | 0.20–3.00, 15 points | Full phase grid. |
| Kappa grid | 0.00–1.40, 15 points | Full phase grid. |

## Priors and action efficacy

Initial base counts are cue `[14,10]`, affect `[15,7]`, policy `[3,5,4,1]`,
and outcome `[[8,10,9,6]; [4,3,4,6]]`. Spawned priors remain cue `[1,2]`,
affect `[1,1]`, all-one outcome and policy counts. The saturating efficacy
transform is `kappa/(kappa+0.45)`. Given aversive/safe delivered evidence,
action-consequence baselines are 0.90/0.08 aversive; relief weights are
approach 0.10, flee 1.40, appease 0.90, attenuate 0. These efficacy values
change consequence success, never potential hazard dosage or relief duration.
