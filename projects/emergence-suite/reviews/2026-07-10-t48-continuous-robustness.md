# T4.8 Step A — continuous nulls and bifurcation pilot report

## Status

Implemented and ran the preregistered 10-seed pilot only. Overall pilot theory
result: **falsified/mixed**. `Sc.bifurcation` supports; `Sc.nulls` and
`Sc.decoupled` are falsified. No confirmatory seeds, retuning, git commit, or
changes outside `projects/emergence-suite/continuous/` were made. The discrete
Sim 6a area was read only.

Implementation artifacts:

- `configs/t48-pilot.yaml`
- `configs/t48-criteria-pilot.yaml`
- `src/T48Robustness.jl`
- `scripts/run_t48.jl`
- `test/runtests.jl`
- `results/t48_continuous_robustness_pilot/`

The historical Stage 3 runner and result directories were not modified. The
new robustness runner uses the first ten seeds from the continuous seed list:
`11, 23, 37, 53, 71, 97, 131, 173, 211, 251`.

## Preregistered model contract

- Null worlds generate continuous volatility loads with theory, flat,
  reversed, or non-monotone depth mappings. Agent-side response dynamics stay
  frozen to the theory mapping, matching the discrete adversarial standard.
- Latent depth is an independently evolving reflected stochastic trajectory;
  it never reads continuous state, biography phase, or observation noise.
- Complete collapse-and-stay-collapsed requires a Self baseline immediately
  before the first low-depth crossing, capture during the low-depth excursion,
  and capture for at least 4/5 states after latent depth autonomously returns
  to `>=0.70`.
- Bistability requires at least one converged Self endpoint and one converged
  capture endpoint from the same autonomous dynamics and a 9x9 initial-state
  grid. The residual gate is `<=0.005`.
- The bifurcation reference is the historical continuous hysteresis regime:
  bundle strength `1.7`, volatility sensitivity `1.3`, beta `1.05`, gamma
  `1.25`, and safety-prior mass `0.60`. Safety mass maps to continuous
  `self_support = mass/3`, so the default exactly preserves the historical
  `0.20` support term. This is not the weaker `DynamicsParams()` constructor
  setting `1.2 x 1.0`.

## Per-criterion results

### Sc.nulls — FALSIFIED

Complete signature counts:

| Mapping | Signatures | Preregistered interpretation |
|---|---:|---|
| Theory | 0/10 | Fails required reference `>=8/10` |
| Flat | 0/10 | Numerically clean, but not interpretable as specificity without a theory transition |
| Reversed | 0/10 | Same |
| Non-monotone | 0/10 | Same |

The per-mapping driven basin maps further argue against calling the nulls
clean. Averaged over 81 initial-state cells and 10 seeds, post-recovery capture
fractions were theory `0.514`, flat `0.757`, reversed `0.884`, and
non-monotone `0.607`. Cells with both Self and capture endpoints across seeds
were theory `13/81`, flat `1/81`, reversed `3/81`, and non-monotone `8/81`.
Thus the null drives often leave trajectories in capture when initialized near
that basin; what fails is basin crossing from the preregistered Self start.

Per-mapping maps:

- `basin_map_theory.svg`
- `basin_map_flat.svg`
- `basin_map_reversed.svg`
- `basin_map_nonmonotone.svg`

### Sc.bifurcation — SUPPORT

- Grid: `5 beta x 5 gamma x 5 safety = 125` cells.
- Bistable cells: `66/125`, volume fraction `0.528`.
- Connectivity: one 6-neighbor-connected component containing all 66 cells.
- Historical reference default `(beta, gamma, safety) = (1.05, 1.25, 0.60)`:
  inside the component and itself bistable.
- Default-cell basin fractions: Self `0.963`, capture `0.037`, mixed/unconverged
  `0.000`; maximum endpoint residual `0.00119`.

Region shape: a three-slice slab over safety-prior masses `0.20`, `0.40`, and
`0.60`, with `22/25` beta/gamma cells bistable in each slice. The same three
low-slope corner cells are excluded in each slice:
`(0.35, 0.40)`, `(0.70, 0.40)`, and `(0.35, 0.825)`. All other registered
beta/gamma pairs are bistable over safety `0.20–0.60`. There are no bistable
cells at safety masses `0.80` or `1.00`. The component therefore spans the full
registered beta range `0.35–1.75` and gamma range `0.40–2.10`, but terminates
sharply above safety mass `0.60`.

### Sc.decoupled — FALSIFIED

The autonomous theory-mapped latent drive was structurally evaluable in all
10 seeds, but produced capture-basin entry from the Self start in `0/10`.
Every trajectory was Self immediately before the low-depth crossing, and none
became capture before latent recovery. Therefore collapse-and-persistent-
capture is `0/10`, below the `>=8/10` success gate and the `>=6/10` weak gate.

Interpretation: autonomous bistability exists, but the independently generated
latent-depth excursion does not cross the separatrix. The original continuous
hysteresis trace depended on its authored phase-specific assistance; this
pilot does not reproduce collapse-and-stay-collapsed when parameters remain
fixed.

## Noise robustness

Theory-mapping signature counts by observation-noise SD:

| SD | Signatures |
|---:|---:|
| 0.000 | 0/10 |
| 0.012 | 0/10 |
| 0.035 | 0/10 |
| 0.070 | 0/10 |
| 0.140 | 2/10 |
| 0.280 | 4/10 |

By the preregistered rule, hysteresis dies at SD `0.0`: more precisely, it is
already absent without observation noise, so there is no supported robustness
range. Larger noise occasionally kicks trajectories across the basin boundary,
but no swept point reaches `8/10`.

## Validation

- Julia tests: 14/14 passed.
- Run contract emitted all required JSON, CSV, and SVG artifacts.
- `status.json`: implementation passed, pilot only, confirmatory seeds false.
- `git diff --check`: clean.
- Pilot runtime: about 2.0 seconds on Julia 1.12.4.

## Blockers / limitations

No execution blocker remains. Interpretive limitations are:

1. This is a coarse 5x5x5 pilot map, not a boundary-refined confirmatory map.
2. “Safety-prior mass” is an explicit bridge to the continuous model's
   historical `self_support` term (`mass/3`); the original continuous model did
   not name a probability-valued safety mass.
3. The marked reference uses the historical hysteresis probe's `1.7 x 1.3`
   bundle/volatility regime, not the weaker constructor defaults. This choice
   was preregistered and recorded before execution.
4. Per-mapping driven basin maps classify state after the first autonomous
   latent recovery; they are not independent fixed-point diagrams for altered
   agent equations, because adversarial nulls keep the agent theory mapping
   frozen.

Required report outputs are in
`projects/emergence-suite/continuous/results/t48_continuous_robustness_pilot/`.
