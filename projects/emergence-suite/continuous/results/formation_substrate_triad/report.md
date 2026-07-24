# Experiment 45: the formation-substrate triad

## Design

The construction compares assembly, recruitment, and hybrid formation over paired observation streams from the same worlds. Four free sufficient coordinates—affect, policy, `self-world` coupling, and `policy-outcome` coupling—materialize an Experiment 43-compatible organization: a four-element (`self`, `world`, `policy`, `outcome`) bundle, its two explicit couplings, a matched precision vector, and its field profile. Affect and policy coordinates can align with four authored prepared carriers; the coupling coordinates are biographical. Precision and field profiles are fixed across models so this experiment changes formation substrate rather than evidence weighting. Assembly begins from a uniform latent-cause prior and constructs the organization at freeze. Recruitment selects a persistent prepared carrier and binds the remaining burden. Hybrid factors the result into a persistent carrier and learned couplings.

Selective reduction shrinks learned burden parameters toward each model's factorized prior. Assembly can leave coupling-attributable residue, recruitment carrier-attributable residue, and hybrid both. Ablations remove one named component at a time. Interference is the held-out error increase on the first formation after the same persistent carrier is bound to a second formation.

### Register guards

*Organization* means the four-element bundle, its couplings, its precisions, and the field profile. *Carrier* means independently parameterized substrate. *Configural* is used only statistically for within-bundle organization; *relational* is reserved for interpersonal use. These names and the measures were fixed before outcomes.

### Design decisions

- One seed is one world. Conditions and models are paired within seed.
- Affect and policy instantiate the prepared repertoire; the two coupling coordinates generate the `world` and `outcome` bundle contents alongside explicit biographical couplings. Bundle contents are derived organization readouts, not extra free parameters.
- Shuffling preserves the marginal sets of affect and policy priors but repairs them across carriers, breaking their joint preparation.
- The unspecified phrase “measurable margin” was fixed before pilot as an RMSE increase of at least `0.03`, present in at least `16/20` confirmatory worlds for recruitment and hybrid and absent in assembly.
- “Present, separable by ablation” was fixed before pilot as component norm at least `0.15` and ablation loss at least `0.10`.
- Taxonomy is reported descriptively as four-cluster silhouette, cluster sizes, and seed-level nearest-carrier margins; it is not promoted to an unregistered success criterion.

### Capacity-matching audit

All three models have exactly `4` continuous parameters per formation and one uniform `4`-way latent index. With Gaussian prior SD `0.25`, conditional continuous prior entropy is `0.1306` nats; uniform index entropy is `1.3863` nats; labeled joint prior entropy is `1.5169` nats for **each** model. Each receives at most `72` observations with SD `0.55` from the identical replayed stream. Parameter-count equality: `true`; prior-entropy equality: `true`; audit valid: `true`.

Prepared prior means differ but do not change Gaussian entropy. The authored carrier index is counted explicitly rather than treated as free capacity.

## Pilot

Ten worlds (`18101:18110`) were run. Recruitment's sample reduction relative to assembly was 50.0% in prepared worlds, -47.2% in arbitrary worlds, and 4.4% under shuffled preparation. Mean prepared-world interference degradation was assembly `0.0000`, recruitment `0.0734`, and hybrid `0.0734`. Pilot criteria are descriptive because the count criteria are calibrated for 20 worlds.

## Freeze log

No outcome threshold moved after pilot. The shared prior strength, hybrid carrier update, and residue readout point were calibrated on pilot worlds and logged before confirmation. The confirmation seed block remained unopened until the design constants, operational thresholds, vocabulary register, and `magic-numbers.md` were frozen. Full details are in `freeze-log.md`.

## Confirmatory results

Twenty fresh worlds (`18201:18220`) were run after freeze, disjoint from the pilot.

- Formation efficiency: recruitment's sample reduction was 46.3% prepared, -57.6% arbitrary, and 21.5% shuffled.
- Interference worlds at or above the frozen margin: assembly `0/20`, recruitment `13/20`, hybrid `13/20`.
- Prepared-world residue: assembly both/carrier-only/coupling-only/neither = `0/0/17/3`; recruitment = `0/20/0/0`; hybrid = `16/4/0/0`.

### Cluster structure

| Model | Prepared silhouette | Arbitrary silhouette | Shuffled silhouette |
|---|---:|---:|---:|
| assembly | 0.7349 | 0.3230 | 0.7647 |
| recruitment | 0.8367 | 0.5796 | 0.7072 |
| hybrid | 0.8367 | 0.5796 | 0.7072 |

### Verdict against §4.6

1. **FAIL — formation efficiency and shuffled-preparation control.** Prepared advantage must be ≥20%; arbitrary and shuffled advantages must each be ≤5%.
2. **FAIL — shared-carrier interference.** Recruitment and hybrid must each reach the frozen margin in ≥16/20 worlds; assembly must do so in 0/20.
3. **PASS — post-reduction residue.** Hybrid must show both separable components in ≥16/20 worlds and neither pure model may show both.

Overall frozen conjunction: **FAIL**.

## Interpretation

The carriers are authored. This experiment tests distinguishability of the models, not which is true of people. Its result licenses exactly one manuscript sentence: the three formation hypotheses are (or are not) separable in principle by the signatures §10 names.

Licensed manuscript sentence: **The signatures §10 names failed to separate the three formation hypotheses in this construction; the residue dissociation separated hybrid from both pure models, but formation efficiency and interference did not reach their frozen criteria.**

This is a construction result inside an authored model. It establishes no clinical effect, biological mechanism, or ontology of parts.

## Exploratory addendum (post-freeze; non-confirmatory)

This addendum does not alter the frozen criteria, confirmatory values, or overall **FAIL** verdict. It analyzes the existing confirmatory interference values and uses 40 fresh diagnostic worlds (`18301:18340`), disjoint from both frozen blocks.

### Shuffled-preparation failure

The diagnostic held the shuffled worlds and evidence streams fixed while varying only carrier access. Best-fitting selection over the shuffled four-carrier repertoire retained a 22.1% advantage over assembly (mean samples: `7.1250` vs. `9.1500`). Assigning one carrier at random, independently of evidence, changed the advantage to -35.2% (mean `12.3750`). Keeping best-fit selection but shifting both carrier marginals outside the world range changed it to -59.3% (mean `14.5750`).

Best-fit selection accounts for `5.2500` samples relative to fixed-random assignment; its share of the observed shuffled saving is `259.3%`. Marginal coverage accounts for `7.4500` samples relative to the degraded-marginal repertoire.

The selection share exceeds 100% because removing selection did more than erase the advantage: fixed-random recruitment was slower than assembly.

The exploratory comparison supports the proposed diagnosis: selection over a repertoire with covering affect and policy marginals explains the residual shuffled advantage even after joint pairing is broken. The efficiency signature therefore cannot distinguish prepared joint structure from any sufficiently covering repertoire plus selection. This is informative about what §10's efficiency signature can and cannot measure, but it is non-confirmatory.

### Interference failure

Across the 20 frozen confirmatory worlds, interference degradation had min/median/max `-0.0854` / `0.0521` / `0.1467`. Seven worlds missed `0.03`; their values were `-0.0854, -0.0138, -0.0091, 0.0121, 0.0197, 0.0197, 0.0287`. Only `1/7` miss was within `0.01` of the margin, and `3/7` misses were negative.

This was a broad, heterogeneous distribution, not a simple threshold near-miss or a clean bimodal split; the largest gap isolates one negative outlier. No threshold was changed and the frozen `13/20` failure stands.
