# Magic Numbers

Every hand-set constant in the continuous Stage 3 project is listed here.

| Constant | Value | Rationale / debt |
|---|---:|---|
| Seeds | 20 seeds, fixed list | Matches suite convention of reporting seed aggregates rather than single traces. |
| Burst doses | 0.4, 0.8, 1.2, 1.6 | Four registered magnitudes for the dose-response requirement. |
| Parameter grid | 5x5 bundle strength x volatility sensitivity | Minimum grid requested by T2.4; both parameters directly control capture and collapse. |
| Basin starts | 11x11 per grid cell | Dense enough to estimate basin fractions while keeping the standalone run cheap. |
| Basin integration | 900 steps, dt 0.04 | Chosen so endpoint residuals settle below the fixed-point tolerance on smoke runs. |
| Self fixed-point class | depth >= 0.74 and capture <= 0.35 | Readout threshold for the high-depth, no-dominant-bundle regime. |
| Capture class | depth <= 0.50 and capture >= 0.50 | Readout threshold for occlusion/capture regime. |
| beta_bundle | 1.05 | Affine depth-to-bundle log-precision slope; inherited from D1 as a model slope, not fit after outcomes. |
| gamma_evidence | 1.25 | Affine depth-to-evidence log-precision slope; slightly stronger than bundle slope to make high-depth evidence-dominant. |
| capture_volatility_gain | 0.42 | Makes capture raise volatility estimates, the occlusion half of the U2 loop. |
| depth_error_gain | 0.24 | Makes low depth carry an expected self-modeling error cost. |
| self_loop_gain | 0.62 | Makes accurate self-modeling lower volatility enough for the high-depth fixed point. |
| depth_cost | 0.26 | Baseline cost of sustaining depth; offset by low-volatility self-loop. |
| capture target penalty | 0.55 * capture^2 | Makes capture impose a depth-maintenance cost in the expected dynamics, allowing an occlusion basin instead of only a global self attractor. |
| volatility likelihood depth term | 1.00 * (1 - depth)^2 | Observation model used by the depth posterior update: high depth predicts low volatility, so burst evidence can lower the posterior mean by inference. |
| volatility likelihood capture term | 0.25 * capture^2 | Observation model term allowing capture to explain part of volatility evidence without directly writing to depth. |
| innovation_var_gain | 0.055 | Lets unmodeled volatility prediction error widen the depth posterior during bursts. |
| recovery threshold | recovery fraction >= 0.72 for each dose | Registered before run; stricter pass criterion is encoded through compound T2.4.3. |
