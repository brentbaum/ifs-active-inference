# IFS Active Inference

Computational models of Internal Family Systems therapy through Active Inference. A Julia implementation of active inference for discrete POMDPs, applied to computational psychiatry.

## What's Here

This repo is organized using [PARA](https://fortelabs.com/blog/para/):

### Projects

- **[`projects/library/`](projects/library/)** — The Julia active inference engine. A reusable implementation of active inference algorithms for discrete, partially observable MDPs with Dirichlet-categorical learning.

- **[`projects/ifs-paper/`](projects/ifs-paper/)** — The IFS-Active Inference paper. The novel theoretical contribution: modeling IFS "parts" as precision-modulating meta-priors within a single generative model.

- **[`projects/reproductions/`](projects/reproductions/)** — Paper reproductions that validate the library and build toward the IFS theory:
  - `chamberlin_2022/` — Coherence therapy mechanisms (most documented)
  - `smith_2021/` — Spider phobia exposure therapy
  - `eckertal_2023/` — Trust game social cognition
  - `pmc7250191/` — Concept learning dynamics

### Resources

- **[`resources/papers/`](resources/papers/)** — Reference literature being read
- **[`resources/glossary.md`](resources/glossary.md)** — Key terms and definitions
- **[`resources/docs/`](resources/docs/)** — Concepts, guides, and a searchable solution knowledge base

### Archive

- **[`archive/`](archive/)** — Completed validation artifacts, old simulation results, superseded plans

## Quick Start

```bash
# Activate the Julia package
julia --project=projects/library

# In the REPL:
using Pkg; Pkg.instantiate()
```

```julia
# Load the active inference core
include("projects/library/src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore

# Run Chamberlin 2022 tests (14 total)
results = run_chamberlin_2022_full(n_replications=30)
```

## Running Tests

```bash
julia --project=projects/library projects/library/test/runtests.jl
```

## Theory

The working thesis: **Parts in IFS are not separate sub-agents but precision-modulating meta-priors within a single generative model.** Modularity (isolation of subgraphs) prevents context-dependent learning. IFS therapy works through re-contextualization — progressively reconnecting isolated beliefs to the full model.

See [`projects/ifs-paper/outline-v1.md`](projects/ifs-paper/outline-v1.md) for the full theoretical framework.

## References

- [ActiveInference.jl](https://github.com/ilabcode/ActiveInference.jl) — Julia active inference library
- [pymdp](https://github.com/infer-actively/pymdp) — Python implementation
- Friston et al. "Active Inference and Learning" — Theoretical foundations

## License

MIT
