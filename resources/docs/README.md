# Documentation

This directory contains reference documentation for the IFS Active Inference research project.

## Structure

```
docs/
├── README.md                    # This file
└── solutions/                   # Problem/solution knowledge base
    ├── INDEX.md                # Index and discovery guide
    └── *.md                    # Individual solution documents
```

## Solutions Directory

The `solutions/` subdirectory maintains a searchable knowledge base of problems encountered and their solutions. Each entry includes:

- **Metadata**: Problem type, severity, status, component
- **Problem analysis**: Symptoms, root cause, impact
- **Solution**: Implementation approach and design decisions
- **Validation**: Test results and metrics
- **Tags**: For cross-reference and discovery

### Why Separate Solutions?

Solutions are kept separate from detailed paper reproduction notes because:

1. **Searchability**: YAML frontmatter enables structured queries
2. **Reusability**: Insights apply across multiple papers
3. **Maintenance**: Centralized reference for recurring issues
4. **Integration**: Links between related problems and patterns

### Browsing Solutions

Start with `solutions/INDEX.md` to find solutions by:
- **Problem type**: What kind of issue (model behavior, architecture, etc.)
- **Component**: Which module or paper reproduction
- **Tags**: Cross-cutting concerns (stochastic modeling, temporal dynamics, etc.)
- **Severity**: Critical/high/medium/low priority

## Integration Points

- **Paper Reproductions**: Each reproduction in `paper_reproduction/[paper]/` has detailed notes
  - `learnings.md`: Insights specific to that paper
  - `model_design.md`: Architecture and design choices
  - Solutions extract generic patterns from these notes

- **Test Suites**: Solutions reference test coverage and validation approach

## Adding New Solutions

When documenting a new solution:

1. Check `solutions/INDEX.md` for existing related solutions
2. Create a new file: `solutions/[descriptive-name].md`
3. Use YAML frontmatter from existing solutions as template
4. Include metadata fields: `problem_type`, `severity`, `status`, `component`, `tags`
5. Update `solutions/INDEX.md` with new entry

Example template:
```yaml
---
title: "Your Solution Title"
problem_type: "category"
severity: "medium"
status: "resolved"
date_resolved: "YYYY-MM-DD"
component:
  module: "module_name"
  files: []
symptoms: []
tags: []
---
```

## Current Solutions

### Chamberlin 2022 (Coherence Therapy)

**[Gradual Discovery Dynamics](solutions/chamberlin-2022-gradual-discovery.md)**
- Modeling Discovery as iterative process with stochastic accessibility
- Status: Resolved (2026-01-30)
- All 14 tests pass (7 original + 7 discovery)

## Future Documentation

Planned additions:
- [ ] Pattern library: Recurring issues across papers
- [ ] Error guide: Common implementation pitfalls
- [ ] Design patterns: Reusable architectural approaches
- [ ] Validation strategies: Testing approaches for active inference models
