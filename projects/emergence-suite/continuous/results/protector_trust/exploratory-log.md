# Experiment 47 exploratory (d) log

- Status: post-freeze, non-confirmatory.
- Frozen summary SHA-256 before this block: `4e9e0f923d4bc411e38a845d1b83519bad9bf07b665ae4b4cb13baf41685c7c2`.
- Fresh seeds: `14801:14840` (40 worlds), disjoint from pilot `14701:14710` and confirmation `14751:14770`.
- Co-protection evidence budget: `4` Bernoulli demonstrations per world.
- True competence generation: one `Uniform(0,1)` draw per seed; demonstrations sampled from that probability.
- Inference likelihood: existing `competence_success_likelihood`; prior: existing `prior_competence`.
- Existing stakes, risk weights, refusal cost, decision temperature, and hope value were reused.
- New obsolescence penalty: **none**. The risk-model path does not read `obsolescence_penalty`.
- Positive/negative obsolete shifts: `26` / `14`.
- Analytic competence crossover: `0.2618`.
