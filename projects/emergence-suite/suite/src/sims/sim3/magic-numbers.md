# Sim 3 Magic Numbers — Phase 4 Step A Pilot

The Phase 4 pilot may tune constants, but every such choice is disclosed here.
"Pilot candidate" means chosen before the first 1001–1010 execution; any value
changed after observing that pilot must be relabeled "pilot-tuned" with the
observed reason. Step B must freeze both code and criteria before fresh seeds.

| Constant | Value | Status / provenance |
|---|---:|---|
| Pilot seeds | 1001–1010 | Protocol-fixed by T4.2 Step A. |
| Association pre-training observations per cue | 48 | Pilot candidate; enough Bernoulli co-occurrences to separate the five world rates while retaining seed-level posterior variation. |
| Association Dirichlet prior | `[1,1]` | Conventional symmetric Laplace prior; not tuned. |
| Root-context world rates | `[0.95, 0.80, 0.65, 0.45, 0.25]` | Pilot candidate; experimenter manipulation replacing supplied causal coupling. These values generate contexts only. |
| Root-poor confound world rate | `0.05` | Pilot candidate; makes A3.2's perceptually near cue genuinely root-poor without setting a zero pathway. |
| Perceptual similarities | `[1.0, 0.35, 0.20, 0.70, 0.45]` | Carried from the prior decorrelated cue design. |
| Root-poor confound perceptual similarity | `0.90` | Carried from the prior A3.2 near-feature confound. |
| Perceptual generalization gain | `0.45` | Pilot candidate; moderate shared threat evidence, chosen to make conventional generalization live without assuming it dominates root-mediated transfer. |
| Training trials | 20 | Carried from v10/v11 Sim 3. |
| Held-out trials | 6 | Pilot candidate; gives each pilot seed multiple frozen-bank predictions without feeding held-out outcomes back into state. |
| High / low depth | `0.85 / 0.15` | Carried from v10/v11 witnessing and exposure conditions. |
| Training parity stop | `0.05` nats/trial | Carried strict stop condition; not relaxed for the pilot. |
| Prior/evidence precision constants | `pi_part=3.6`, `beta_se=1.0`, `lambda_self=0.9`, `gamma_se=1.2` | `pi_part`, `beta_se`, and `gamma_se` carried from v10/v11. `lambda_self` pilot-tuned from `0.7` to `0.9` jointly with the common coupling; see log. |
| Learning rates | `eta_self=7.0`, `eta_threat=1.6` | `eta_threat` carried from v10/v11. `eta_self` pilot-tuned from `1.0`; identical across H1/H2; see log. |
| Cross-level coupling | `2.0` | Pilot-tuned from the carried `1.35`; common to H1 self→threat and H2 threat→self and never cue-specific; see log. |
| Outcome precision | `1.6` | Carried from v10/v11. |
| Policy precision / threat weight | `3.2 / 2.4` | Carried from v10/v11; policy equation identical across architectures. |
| Self policy biases | contact `0.08`, avoid `0.03` | Carried from v10/v11 and active in both architectures. |
| Outcome utilities | `[-2.4, 1.4, -0.15, 0.20]` | Carried contact/avoid harm/neutral utilities. |
| Initial self counts | `[18,2]` for both roots | Carried from v10/v11; root banks initialized identically. |
| Initial threat counts | `[17,3]` for every cue | Carried from v10/v11; cue banks initialized identically. |
| Relational truthfulness | `0.88` | Carried from v10/v11; also generates observed relational messages. |
| Outcome reliabilities | `[0.96,0.08,0.97,0.78]` | Carried from v10/v11. |
| Self / threat first-passage threshold | `0.60` | Carried IOU threshold. |
| Policy first-passage threshold | `0.60` | Carried IOU threshold. |
| Shared micro-step clock | self `+1`, threat `+2`, policy `+3` | Protocol choice, identical for H1/H2; these are actual update steps, not architecture-label offsets. |
| Structural A3.2 cue | `cue_3` | Predeclared from the old design because it combines low feature overlap (`0.20`) with a high root-context world rate (`0.65`). Metrics use its learned association. |
| Criteria thresholds | see `configs/sim3-criteria.yaml` | Pilot candidates selected before the first run from effect-size and 8/10 seed-robustness conventions; changes after pilot must be recorded below. |

## Pilot-tuning log

- First stop-condition attempt with carried `lambda_self=0.7` and coupling
  `1.35` stopped at an H1/H2 training-likelihood gap of `0.1163` nats/trial.
  The parity epsilon remained fixed at `0.05`.
- A shared-parameter grid over `lambda_self ∈ {0.25,0.4,0.55,0.7,0.9,1.1}`
  and coupling `∈ {1.5,2.0,2.5,3.0,3.5,4.0}` selected
  `lambda_self=0.9`, coupling `2.0`: pilot parity gap `0.0159`, held-out
  H1−H2 log-likelihood `+0.0219` nats/trial, and strict H1 cascade rate `1.0`.
  Selection required all three properties; no architecture-specific constant
  was introduced.
- The first completed pilot exposed a saturated untrained-cue policy readout:
  H1−exposure mean contact was `7.47e-8` because the shared root bank ended at
  `P(resourced)=0.452`. A shared `eta_self` sweep over
  `{1,1.5,2,3,4,4.5,5,5.5,6,6.5,7,8}` selected `7.0`, the smallest tested
  value meeting the prewritten `r≥0.70` learned-association correlation while
  retaining the strict cascade in 9/10 seeds. At `7.0`, pilot diagnostics were:
  parity gap `0.0069`, held-out H1−H2 `+0.0289` nats/trial, H1−exposure contact
  `+0.431`, root-controlled association correlation `0.723`, and structural
  cue−perceptual-confound contact `+0.457`.
- The preliminary perceptual behavioral-gain criterion was removed after the
  first pilot because T4.2 specifies a *threat-level, cue-bound* conventional
  pathway. The threat-safe gain remains directly preregistered, together with
  the harder requirement that root-associated `cue_3` exceed the perceptual
  confound in contact. H2 self liveness was corrected from a signed resourced
  shift to an absolute bank shift: reversed conditioning initially moves the
  bank toward helplessness, which is evidence of an active pathway, not a dead
  one.
