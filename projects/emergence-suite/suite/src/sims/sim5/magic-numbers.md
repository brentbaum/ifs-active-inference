# Sim 5 Magic Numbers

## T4.4 Step A de-aliasing pilot (2026-07-10)

The values in this section and the corrected thresholds in
`configs/sim5-criteria.yaml` were written before executing T4.4 pilot seeds
1001-1010. The old aliased S5.1b/S5.2 criteria remain in that file under
`falsified_originals`. No confirmatory seed may be run during Step A.

| Constant | Pilot value | Provenance / role |
|---|---:|---|
| regulated emission `(P(coherent), P(safe channel))` | `(0.92, 0.90)` | Preregistered high-reliability coherent/safe tuple; interior probabilities preserve counterexamples. |
| fluent-threatened emission | `(0.92, 0.10)` | Preregistered misleading-surface tuple: the same calm/competent surface reliability as regulated, with the same threatened-channel probability as dysregulated. |
| dysregulated emission | `(0.10, 0.10)` | Preregistered incoherent/threatened tuple. The three emission tuples are therefore genuinely distinct. |
| `mapping_settle_probability_by_signal` | `[0.90, 0.60, 0.64, 0.10]` | Preregistered generative contingencies for coherent-safe, coherent-threat, incoherent-safe, incoherent-threat. The relational channel supplies the larger contrast; coherent-threat remains intermediate and can be learned rather than named. |
| `mapping_prior_count` | `1.0` per outcome | Uniform Beta(1,1) row prior for every observed joint therapist signal. |
| `mapping_learning_rate` | `1.0` | One Dirichlet count per observed therapist-signal / own-state-change contingency. |
| `unreliable_mapping_noise` | `0.75` | Preregistered control that mixes each outcome contingency 75% toward chance, leaving a weak learnable residual rather than deleting the channel. |
| `mapping_lesion_trial` | `31` | Mid-session intervention after 30 learning trials. Counts reset to the uniform prior and subsequent mapping writes are blocked. |
| `learned_mapping_tail_trials` | `15` | Last-quarter readout, registered before the pilot so early prior transients do not define the signature. |
| `learned_signature_margin` | `0.15` | Each adjacent learned-probability contrast must be at least 15 percentage points within a seed. |
| `unreliable_degradation_ratio` | `0.60` | Unreliable regulated-to-dysregulated span must be no more than 60% of the paired reliable span. |
| `lesion_degradation_ratio` | `0.50` | Lesioned fluent tail estimate must move at least halfway from its intact value back toward chance. |
| `contact_root_evidence_fraction` | `0.30` | Every realized contact routes 30% of the existing parts-language root-evidence budget regardless of content; parts-language supplies the remaining 70%. This makes regulation-only live without forcing it to equal regulation-plus-witnessing. |
| seed robustness | `8/10` | User-specified Step A success convention for signature, reversal, degradation, and lesion criteria. |

The old constants below describe the superseded pre-T4.4 implementation. They
are retained as provenance, not presented as a valid preregistration for the
de-aliased pilot.

### Post-pilot provenance

The single authorized pilot met S5.signature at exactly 8/10 and the reversed,
unreliable, lesion, and liveness criteria at 10/10. **No constant or threshold
was changed after observing the pilot, and the pilot was not rerun.** This exact
8/10 signature is a fragile pilot margin that must be treated as such before any
future confirmatory step.

## Session and evidence budgets

- `n_session_trials = 60`: inherited from Sim 2's melt-phase budget so root BMR
  has the same number of contact opportunities.
- `contact_start_trial = 6`: keeps an activation-only opening before witnessed
  contact can accumulate.
- `bmr_interval = 5`: inherited from Sim 2's BMR cadence.

## Depth grid and priors

- `depth_grid = [0.0, 0.25, 0.50, 0.75, 1.0]`: inherited from Sim 6a's
  accepted categorical depth filter.
- `low/medium/high_baseline_prior`: preregistered self-practice capacity sweep.
  These are explicit baseline-capacity settings, not condition-specific switches.
- `dyad_baseline_prior`: moderate client prior used for all therapist
  conditions.
- `transition_mix = 0.08`: floor on the level-3 transition back toward the
  client's baseline prior. The realized prior pull is
  `max(transition_mix, expected_depth(baseline_prior)^2)`, so low baseline
  capacity gets only the floor while high/owned capacity becomes a stable prior
  across activation trials.

## Likelihood and precision constants

- `activation_drive = 0.86`: bundle-live activation strength. Realized PE is
  scaled by current capture, so higher depth can reduce subsequent volatility
  evidence without a direct depth write.
- `activation_jitter = 0.04`: deterministic seed/trial variation to avoid
  single-trajectory artifacts.
- `volatility_precision = 1.35`: makes activation evidence strong enough to
  collapse low-baseline self-practice.
- `coreg_precision = 2.35`: makes regulated/dysregulated body evidence strong
  enough to test the same-words/different-bodies contrast.
- `regulated_coreg_by_depth = [0.08, 0.16, 0.36, 0.74, 0.93]`: likelihood of
  observing a regulated other at each depth state; the dysregulated likelihood
  is its complement.

## Sim 2 inherited revision constants

- `pi_part = 4.0`, `lambda_ctx = 0.90`, `beta = 1.00`, `gamma = 1.15`: same
  scale as Sim 6a's accepted effective-precision mapping.
- `relational_count_good = 1.0`, `relational_count_old = 0.08`: inherited from
  Sim 2's accessible root statistics.
- `full_prior_met = 2.0`, `full_prior_alone = 12.0`,
  `reduced_prior_met = 7.0`, `reduced_prior_alone = 7.0`,
  `prior_log_odds = -5.0`, `E0 = 1.0`: inherited from Sim 2's D2 BMR
  comparison.

## Borrowed-then-owned prior learning

- `ownership_prior_concentration = 24.0`: converts the low baseline prior into
  slow Dirichlet counts.
- `ownership_learning_rate = 0.72`: adds mean regulated-session depth occupancy
  to the client's prior counts after each borrowed-depth session.
- `ownership_revision_floor = 8.0`: same revision floor as S5.1's contrast
  margin.
- `ownership_max_sessions = 12`: bounded course length for the preregistered
  ownership search.
