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

## T4.8 Step A pilot (registered before execution)

These constants apply only to `configs/t48-pilot.yaml`. The historical Stage 3
configuration and results are unchanged.

| Constant | Pilot value | Rationale / provenance |
|---|---:|---|
| Pilot seeds | first 10 Stage 3 seeds: `11, 23, 37, 53, 71, 97, 131, 173, 211, 251` | Uses the continuous area's existing fixed-seed ordering and the ticket's 10-seed pilot budget. |
| Clinical/default reference | bundle strength `1.7`, volatility sensitivity `1.3`, beta `1.05`, gamma `1.25` | The first two values are the historical `simulate_hysteresis` regime; the tilt slopes are the registered continuous defaults. This is explicitly a historical hysteresis-reference default, not the `DynamicsParams()` constructor's weaker `1.2 x 1.0` setting. |
| Safety-prior mass | default `0.60`, grid `[0.20, 0.40, 0.60, 0.80, 1.00]` | Matches the discrete robustness default high-state mass. Continuous support is `mass / 3`, so `0.60` exactly reproduces historical `self_support = 0.20`. |
| Beta grid | `[0.35, 0.70, 1.05, 1.40, 1.75]` | Symmetric coarse span around the registered `1.05` slope, from one-third to five-thirds of default. |
| Gamma grid | `[0.40, 0.825, 1.25, 1.675, 2.10]` | Symmetric coarse span around the registered `1.25` slope while remaining positive. |
| Bistable cell | at least one converged Self endpoint and one converged capture endpoint from a `9 x 9` initial-state grid | Uses the historical endpoint classes and a residual gate `<= 0.005`; prevents transient classifications from counting as attractors. |
| Region connectivity | 6-neighbor adjacency in beta x gamma x safety grid | Face connectivity is the conservative standard for a connected 3-D grid region. |
| Continuous null maps | theory `(1-h)^2`; flat `1/3`; reversed `h^2`; non-monotone `4(h-0.5)^2` | Flat is the mean theory-map value under uniform depth; reversed swaps the endpoint ordering; the U-shaped map destroys monotonic ordering while retaining the `[0,1]` range. Null-generated observations are evaluated by the frozen theory-response dynamics, matching the discrete adversarial standard. |
| Autonomous latent drive | initial `0.90`, speed `0.055`, noise SD `0.012`, reflected bounds `[0.08, 0.92]`, 72 observations | Inherited from the discrete T4.7 pilot so the latent path crosses low depth and returns without biography-phase input. Separate RNG streams generate latent motion and observation noise. |
| Latent-to-load gain | `0.95` | Matches the historical continuous freeze-burst external-volatility magnitude at the theory map's low-depth endpoint. |
| State/observation timescale | 3 ODE substeps of `dt=0.14` per latent observation | The continuous state is allowed three fast relaxation steps per slower latent observation; `dt=0.14` reproduces the historical per-step depth/capture relaxation magnitudes (`0.42*dt ~= 0.06`, `1.15*dt ~= 0.16`). |
| Complete pilot signature | Self immediately before first low-depth crossing; capture during the low-depth excursion; capture on at least 4/5 states after latent depth first recovers to `>=0.70` | Directly operationalizes “collapse-and-stay-collapsed”; no recovery assistance or parameter switch is used. |
| Null gate | each null `<=2/10`, with theory reference `>=8/10` | Same honest pilot selectivity rate used in discrete T4.7 Step A. |
| Decoupled gate | `>=8/10` complete signatures | Same pilot fraction as discrete T4.7, now applied to persistent basin capture. |
| Observation-noise grid | SD `[0, 0.012, 0.035, 0.07, 0.14, 0.28]` | Includes the inherited latent noise scale, the historical Gaussian posterior observation SD scale (`sqrt(0.035)`) on both sides, and a severe endpoint. Hysteresis death is the first point below `8/10`. |
