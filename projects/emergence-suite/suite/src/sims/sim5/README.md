# Sim 5 - The Dyad

Sim 5 composes the accepted Sim 2 root-revision machinery with Sim 6a-style
categorical inferred depth. The client receives two independent therapist
outputs:

- content: parts-language, neutral/informational, or no content;
- regulation: the other body's observed regulation state, which enters the
  client's level-3 depth update as ordinary likelihood evidence.

The co-regulation channel is not a switch and does not write `E_t`. Activation
generates volatility observations, therapist regulation generates
co-regulation observations, and both multiply into the same categorical depth
posterior update. `E_t` is then read as expected depth and used only in the
effective-precision balance that determines capture and relational evidence
weight.

The money contrast is condition (1) regulated vs. condition (3)
fluent-but-threatened: the content stream is identical, while the regulation
stream differs. The run writes `figures/capture-index.svg` and
`posterior_traces.csv` so this contrast can be inspected directly.

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
- `criteria-results.json`
- `figures/capture-index.svg`
