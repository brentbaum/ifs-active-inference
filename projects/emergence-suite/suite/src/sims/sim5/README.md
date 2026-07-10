# Sim 5 - T4.4 Step A de-aliased dyad pilot

Sim 5 composes the accepted Sim 2 root-revision machinery with Sim 6a-style
categorical inferred depth. T4.4 removes the old exact aliases. The three
therapist conditions now emit distinct joint surface/channel distributions:

- regulated: coherent surface, safe relational channel;
- fluent-but-threatened: coherent surface, threatened relational channel;
- dysregulated: incoherent surface, threatened relational channel.

The client receives two therapist outputs:

- content: parts-language, neutral/informational, or no content;
- regulation: the other body's noisy relational channel.

The co-regulation likelihood is learned, not supplied by the condition label.
For each observed joint signal (surface coherence x relational safety), the
client updates Beta/Dirichlet counts over its observed next state change
(`settled` or `activated`). The posterior settling probability supplies a soft
likelihood to the same categorical depth update as volatility evidence. `E_t`
remains a posterior readout used only in effective precision.

Controls apply 75% contingency noise toward chance, reverse the contingencies,
or lesion the learned counts on trial 31. The lesion resets every row to its
uniform prior and blocks subsequent mapping writes; it is an intervention on
the learned mapping rather than a renamed emission condition.

Every realized contact now generates relational root evidence regardless of
content. Parts-language adds a content-specific increment. Regulation-only can
therefore revise the root in principle, and A5.2 is no longer an architectural
zero.

The pilot is hard-restricted to label `pilot`, seeds 1001-1010, and output
`runs/sim5/pilot/`. Confirmatory execution is forbidden in Step A.

Run:

```sh
~/.juliaup/bin/julia --project=projects/emergence-suite/suite projects/emergence-suite/suite/scripts/run.jl projects/emergence-suite/suite/configs/sim5.yaml
```

Outputs follow the suite run contract:

- `summary.json`
- `status.json`
- `metadata.json`
- `per_seed_metrics.csv`
- `posterior_traces.csv`
- `learned_mapping_by_seed.csv`
- `criteria-results.json`
- `figures/capture-index.svg`

## Pilot outcome (seeds 1001-1010 only)

No post-outcome constant was changed and no second pilot was run.

- S5.signature: 8/10 seeds. Mean learned settling probabilities were regulated
  0.843, fluent-but-threatened 0.574, and dysregulated 0.181.
- A5.learned reversed: 10/10 reversed ordering (means 0.169, 0.419, 0.780).
- A5.learned unreliable: 10/10 had a span at most 60% of the reliable paired
  span (means 0.577, 0.519, 0.398).
- S5.2 lesion: 10/10 moved the fluent tail estimate back to the uniform 0.5
  mapping prior.
- A5.2-live: contact-generated root evidence was present in 10/10
  regulation-only seeds. Regulation-only lowered mean capture by 0.273 versus
  content-only but revised the root in 0/10 seeds; regulation plus witnessing
  averaged 19.232 revision. Thus this pilot earns the conservative outcome:
  regulation reduces capture, but the smaller contact-only evidence budget is
  insufficient for root revision. This is an empirical pilot result, not a
  content-gated impossibility.

## T4.4 Step B (orchestrator, 2026-07-10)

Audit passed: emission branches are world-side only; the depth likelihood
consumes learned contingency counts, never condition labels; contact root
evidence (0.30 fraction) flows regardless of content; the S5.2 lesion is a real
trial-31 intervention. Deliberate Step B acts: pilot guard lifted label-aware;
confirmatory preregistered at configs/sim5-confirmatory.yaml (fresh seeds
5001-5020) with counts scaled 10 -> 20 at identical fractions
(configs/sim5-criteria-confirmatory.yaml). Pilot fragility to watch: S5.signature
passed at exactly 8/10, and regulation-only revised 0/10 (live but null) — the
confirmatory reports both honestly whichever way they land.
