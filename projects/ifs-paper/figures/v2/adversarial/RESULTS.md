# Adversarial Results

- Generated: 2026-03-27 15:32
- Replications per test: 60
- Figure directory: `projects/ifs-paper/figures/v2/adversarial/`

## Test 1: Mechanism vs alpha exponent
- What was tested: the onset ramp with `alpha_witness=1` versus the registered `alpha_witness=3`.
- What happened: baseline onset = 0.640 ± 0.014 E_t; linear onset = 0.618 ± 0.011 E_t. Max jump shifted from 0.178 to 0.167; peak changed from 1.269 to 1.49.
- What it means: The step-change persists almost unchanged under alpha=1; the exponent mainly rescales the late amplitude rather than creating the threshold.

## Test 2: Threshold robustness
- What was tested: ±20% perturbations of `lambda_witness_max`, `lambda_witness_floor`, `beta_se`, and `gamma_se` under the onset ramp.
- Baseline onset: 0.639 ± 0.014 E_t (range 0.624-0.652).
- `lambda_witness_max` × 0.8: onset = 0.635 ± 0.014 E_t (range 0.624-0.652).
- `lambda_witness_max` × 1.2: onset = 0.646 ± 0.011 E_t (range 0.624-0.652).
- `lambda_witness_floor` × 0.8: onset = 0.543 ± 0.007 E_t (range 0.541-0.569).
- `lambda_witness_floor` × 1.2: onset = 0.694 ± 0.014 E_t (range 0.679-0.707).
- `beta_se` × 0.8: onset = 0.645 ± 0.012 E_t (range 0.624-0.652).
- `beta_se` × 1.2: onset = 0.631 ± 0.012 E_t (range 0.624-0.652).
- `gamma_se` × 0.8: onset = 0.734 ± 0.000 E_t (range 0.734-0.734).
- `gamma_se` × 1.2: onset = 0.540 ± 0.006 E_t (range 0.514-0.541).
- What it means: The threshold is not tightly robust: it stays in a mid-range band, but `lambda_witness_floor` and `gamma_se` move the onset by roughly 0.1-0.2 E_t.

## Test 3: Simpler model without Channel 5
- What was tested: `lambda_witness_max=0`, which permanently disables Channel 5 while leaving the rest of the onset ramp unchanged.
- Channel 1: onset = 0.459, peak = 0.02, max jump = 0.002, late/early ratio = 1.803.
- Channel 2: onset = 0.100, peak = 0.086, max jump = 0.01, late/early ratio = 1.044.
- Channel 3: onset = 0.100, peak = 0.061, max jump = 0.003, late/early ratio = 1.887.
- Channel 4: onset = 0.183, peak = 0.043, max jump = 0.003, late/early ratio = 2.035.
- Channel 5: onset = none, peak = 0.0, max jump = 0.0, late/early ratio = 0.0.
- What it means: No other channel reproduces Channel 5's late-onset profile once Channel 5 is removed, so the original figure is not just a generic gated-epistemic effect elsewhere in the model.

## Test 4: Fake Channel 5 content
- What was tested: Channel 5 kept the same inverse-capture gate but its content was replaced with a binary threat-meaning observation instead of witnessed self-state.
- What happened: original Channel 5 onset = 0.639 ± 0.014 E_t; fake Channel 5 onset = 0.663 ± 0.035 E_t.
- Cascade rate: original = 0.0, fake = 0.0.
- First-passage means: original self/threat/outcome/policy = 5.73 / 3.72 / 6.13 / 31.0; fake = 5.72 / 3.93 / 6.32 / 31.0.
- What it means: The gate-step persists and the onset-order metrics barely change. In this implementation, replacing Channel 5 content with threat information does not kill the downstream dynamics, so the figure does not isolate self-state content.

## Test 5: Constant E_t comparison
- What was tested: constant `E_t=0.85` for 30 forced steps.
- What happened: Channel 5 peaked at step 14 with mean epistemic value 0.97; the final five-step tail mean was 0.963.
- What it means: Channel 5 epistemic value stays elevated for much of the constant-E_t run, so the emergence figure is not just a narrow transient.

## Test 6: Revision-speed proxy
- What was tested: `Δ P(capable/present)` per timestep under the onset ramp as a non-EFE proxy for self-state learning.
- What happened: revision-speed onset = 0.100, compared with Channel 5 epistemic onset = 0.64; peak revision speed = 0.116.
- What it means: Revision speed does not align closely with the epistemic threshold, so the EFE view is doing conceptual work the raw revision trace does not.

## Final Verdict
- What the epistemic emergence figure does prove: within this model, there is a real late-opening window where inverse capture plus context precision unlock a burst of self-state-directed information gain, and that window is not trivially reproduced by simply watching the other existing channels.
- What it does not prove by itself: that witnessing is a mathematically unique phase transition independent of parameterization, that the threshold is tightly robust, or that Channel 5's content is uniquely responsible for the downstream dynamics. In these adversarial tests, the threshold moved materially under `lambda_witness_floor` and `gamma_se`, a fake gated threat channel still produced a similar late epistemic jump, and the constant-`E_t` run did not collapse to a brief spike.
