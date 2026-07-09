# Emergence Suite Harness

Julia scaffold for the v11 emergence simulations. Sims 1-4 will port the v10
discrete active-inference core while keeping the `beautiful-simulation` output
contract.

## Run Contract

Each run writes:

- `summary.json`: deterministic metrics and config snapshot; no timestamps.
- `status.json`: implementation pass flag and criteria-level theory label.
- `metadata.json`: seed/config snapshot, git hash, package versions, runtime, timestamp.
- `per_seed_metrics.csv`: one row per seed.
- `posterior_traces.csv`: compact trace rows for the first scaffold plots.
- `figures/`: generated figures.
- `criteria-results.json`: emitted when `criteria.yaml` is present.

Runs are placed under:

```sh
projects/emergence-suite/runs/<experiment>/<timestamp-or-label>/
```

## Criteria Schema

`criteria.yaml` is a mapping with a `criteria` list. Each criterion has:

- `id`
- `description`
- `metric_path`: dot path into `summary.json`
- `comparator`: one of `>=`, `>`, `<=`, `<`, `==`, `!=`
- `threshold`
- `kind`: `success` or `adversarial`
- optional `weak_threshold`
- optional `opposite_threshold`

Label semantics:

- `support`: the metric passes `comparator threshold`.
- `weak_support`: the metric misses the main threshold but passes `weak_threshold` with the same comparator.
- `null`: the metric is missing, non-numeric, or misses both thresholds without reaching the opposite threshold.
- `falsified`: the metric crosses `opposite_threshold` in the opposite direction.

## Commands

Dummy run:

```sh
~/.juliaup/bin/julia --project=projects/emergence-suite/suite projects/emergence-suite/suite/scripts/run.jl projects/emergence-suite/suite/configs/dummy.yaml
```

Tests:

```sh
~/.juliaup/bin/julia --project=projects/emergence-suite/suite -e 'using Pkg; Pkg.test()'
```
