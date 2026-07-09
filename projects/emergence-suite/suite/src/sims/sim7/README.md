# Sim 7: One Simulated Life

This module implements T3.3 inside `EmergenceSuite.Sim7`. It is a composition
layer only: Sims 1-6 and shared modules are not modified.

## Composition Map

- Formation: Sim 4's accepted developmental schedule creates neutral layer
  records; Sim 1's Tier-A write-time reflexivity readout is added to those logs.
- Stack and descent: Sim 4's computed access, relational trust banks, and EFE
  contact choice are used directly.
- Dyad and inferred depth: Sim 5's regulated co-presence evidence updates the
  client's depth posterior during therapy.
- Melt: Sim 5's composed Sim 2 BMR root-revision machinery runs during witnessed
  root contact.
- Transfer: Sim 3's root-coupled cue continuum and H2 reversed-root architecture
  provide the post-melt probe and H2-life control.

The only scripted object is the world schedule: childhood adversity, adult cue
encounters, therapy sessions, and after-therapy probe opportunities. Taxonomy is
read out post hoc by the fixed classifier preregistered in
`configs/sim7-criteria.yaml`.

## Outputs

- `summary.json`, `status.json`, `metadata.json`
- `per_seed_metrics.csv`
- `posterior_traces.csv`
- `formation_events.csv`
- `taxonomy_readouts.csv`
- `first_passage_sessions.csv`
- `transfer_probe.csv`
- `criteria-results.json`
- `figures/timeline.svg`

Run:

```sh
~/.juliaup/bin/julia --project=projects/emergence-suite/suite projects/emergence-suite/suite/scripts/run.jl projects/emergence-suite/suite/configs/sim7.yaml
```
