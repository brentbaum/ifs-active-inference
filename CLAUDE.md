# IFS Active Inference Project

## Simulation Parameter Registry

When modifying simulation parameters in `projects/library/src/active_inference/ifs_model_v2.jl` or `ifs_polarization_v2.jl`:
- Update `projects/ifs-paper/simulation-magic-numbers.md` with any changed, added, or removed parameters
- Include justification for the value and sensitivity status
- When a parameter is eliminated, move it to the "Eliminated" section

## Paper Draft

The current draft is `projects/ifs-paper/draft-v8.md`. The paper has three moves:
1. Parts as identity-level precision bundles (self-state is the organizing prior)
2. Self-energy as precision governor (regime: capture vs context-held)
3. At sufficient Self-energy depth, the system can observe its own self-state — relational prediction error reaches the organizing prior

## Roadmap

Session-level roadmap and revision history: `~/.claude/projects/-Users-brentbaum-dev-research-ifs-active-inference/memory/project_revision_roadmap.md`
Next-session pickup: `projects/ifs-paper/next-session.md`

## Simulation Files

- `projects/library/src/active_inference/ifs_model_v2.jl` — three-move single-bundle model
- `projects/library/src/active_inference/ifs_polarization_v2.jl` — two-part polarization model
- `projects/library/scripts/ifs_simulation_v2.jl` — main simulation runner
- `projects/library/scripts/ifs_polarization_simulation_v2.jl` — polarization runner
- `projects/ifs-paper/figures/v2/` — generated figures
- `projects/ifs-paper/simulation-v2-spec.md` — simulation design specification
- `projects/ifs-paper/simulation-magic-numbers.md` — parameter registry (keep evergreen)

## IFS Relationship Quotes

Clinical evidence grounding the relational mechanism: `resources/ifs-relationship-quotes.md`
