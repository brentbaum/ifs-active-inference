# Literature-derived epistemic-depth tournament

**Date:** 2026-07-13

**Branch:** `codex/epistemic-depth-experiment-tournament`

**Experiments:** 28 of a maximum 30

## Result in one sentence

The experiment program favors a small two-operation theory: a global precision
hyper-model makes the active inference process broadly accessible, and
contextual representational redescription makes an old model conditional on
the world in which it was learned; none of the tested combinations earned its
extra complexity.

## Protocol

Experiments 1–4 repaired formal weaknesses in the initial five-channel
construction. Experiments 5–24 translated twenty papers into one minimal
operator apiece. Every operator used the same seven arms, twenty seeds, twelve
sessions, three strengths, scaffold-removal schedule, and score. Experiments
25–28 combined the top three singles. A combination had to beat the best
single by `0.020`; otherwise the program stopped and retained the simpler
model.

This is an architectural tournament, not a comparative trial of therapies or
an empirical evaluation of the cited papers. Each operator is a hand-built,
minimal interpretation. The score reveals what that interpretation does in
this toy model; it cannot establish that the paper's mechanism exists in
people.

## Formal-fidelity tranche

The explicit three-level Gaussian model closes three gaps in the original
construction: latent hierarchical states are inferred inside the loop,
second-order precision errors come from expected residuals rather than a
scripted target, and a shared global hyper-node is compared with matched local
precision learners.

| Environment | Global model | Local model | Winner |
|---|---:|---:|---|
| Coordinated shift, third layer held out | error 0.223 | error 1.000 | Global |
| Independent layer shifts, all observed | RMSE 0.344 | RMSE 0.167 | Local |

The result is a scope condition rather than a universal advantage. Global
epistemic depth is useful when changes in precision share structure across
levels and evidence at one level predicts another. When changes are genuinely
independent, pooling is bias and local loops should win.

## Ranked single mechanisms

| Rank | Experiment | Minimal operator | Source | Score |
|---:|---:|---|---|---:|
| 1 | 7 | Context redescription | Chamberlin (2023) | 0.866 |
| 2 | 20 | Flexible self/other boundary | Sandved-Smith et al. (2026) | 0.842 |
| 3 | 14 | Patient testing | Li et al. (2025) | 0.841 |
| 4 | 8 | Spare representational capacity | Smith et al. (2020) | 0.835 |
| 5 | 9 | Regulatory authority | Palejova (2026) | 0.830 |
| 6 | 11 | Dyadic synchrony | McParlin et al. (2022) | 0.829 |
| 7 | 16 | Social self-evidencing | Albarracin et al. (2024) | 0.823 |
| 8 | 10 | Second-order social evidence | Harris (2025) | 0.821 |
| 9 | 5 | Global covariance baseline | Laukkonen et al. (2025) | 0.815 |
| 10 | 21 | Compassionate scope | Ho et al. (2021) | 0.814 |

The remaining ten variants and every metric are recorded in
`ranked_experiments.csv`. Rankings within a few hundredths should not be read
as stable scientific differences: the most useful distinction is qualitative.
Context redescription adds a kind of change the precision field does not.

## Why redescription is the interesting result

The Beautiful Loop mechanism answers an access question: can the system infer
and broadcast how confidence is allocated across its hierarchy while an old
identity model is active? It does not, by itself, specify what new structure
is learned through that access.

Chamberlin's proposal supplies a parsimonious answer. The old schema is not
merely weakened or erased. It is re-represented at a higher level and embedded
in context: the protective inference was coherent in the earlier world, but
need not control the present one. That makes the key update closer to structure
learning than to subtracting precision from a part. It also fits the paper's
existing insistence that accurate threat can remain precise.

This should not become another force in the equations. It is a candidate
learning operation made possible by an open global field:

$$
\text{global recursive access} \longrightarrow
\text{context-indexed redescription} \longrightarrow
\text{selective revision}.
$$

The first arrow is an enabling relation, not a guarantee. A system can have
depth without revising anything if no disambiguating evidence is sampled.

## Recombination result

| Experiment | Combination | Score | Gain over best single |
|---:|---|---:|---:|
| 25 | Redescription + flexible boundary | 0.859 | -0.0068 |
| 26 | Redescription + patient testing | 0.868 | +0.0016 |
| 27 | Flexible boundary + patient testing | 0.830 | -0.0358 |
| 28 | All three | 0.846 | -0.0203 |

No gain approached the `0.020` retention threshold. Experiment 26 is the raw
top score, but experiment 7 is the selected model. The program stopped at 28
rather than spending experiments 29–30 on unearned complexity.

## Recommended theory changes

1. Keep epistemic depth narrowly defined as recursive global precision
   inference. Do not make it the cause of every therapeutic consequence.
2. State explicitly that depth enables access, whereas durable revision may
   require context-indexed representational redescription or another form of
   structure learning.
3. Add the globality scope condition: global pooling is adaptive only to the
   extent that precision changes are actually coordinated across levels.
4. Keep local precision learning as an adversarial control and predict that it
   will outperform global pooling for independent changes.
5. Treat flexible boundaries, patient testing, authority, synchrony, and
   compassion as separable extensions to test, not as ingredients of Self.

## What a skeptical reader can still object to

- The clinical five-channel model remains an analogue, not Table 1 of
  Beautiful Loop Theory.
- The hierarchical upgrade uses a small linear Gaussian model and a
  free-energy proxy, not a biological or full variational implementation.
- The literature operators and scoring weights are authored. The tournament
  selects among explicit constructions; it does not discover mechanisms from
  data.
- Context redescription was rewarded for specificity and transfer it was built
  to produce. Its value is conceptual discrimination, not numerical victory.
- There is still no unified simulation in which the hierarchical hyper-loop
  endogenously discovers a part, redescribes it, and reduces its structure.

Those objections define the next honest experiment. A future model should
infer a context variable and allow the old root to split into past-valid and
present-valid hypotheses. Redescription should be retained only if that model
predicts held-out context-sensitive behavior better than either globally
lowering the old belief's precision or locally relearning each cue.

## Artifacts

- Full ranking: `projects/emergence-suite/continuous/results/literature_tournament/ranked_experiments.csv`
- Summary: `projects/emergence-suite/continuous/results/literature_tournament/summary.json`
- Formal comparison: `projects/emergence-suite/continuous/results/hierarchical_epistemic_depth/summary.json`
- Fidelity audit: `projects/ifs-paper/beautiful-loop-fidelity-audit.md`
- Implementation: `projects/emergence-suite/continuous/src/LiteratureTournament.jl`
