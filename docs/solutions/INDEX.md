# Solutions Knowledge Base

Reference index for problem/solution documentation across the IFS Active Inference project.

## Index by Category

### logic-errors/

| Title | Severity | Status | Date | Key Tags |
|-------|----------|--------|------|----------|
| [Gradual Discovery Dynamics in Coherence Therapy](logic-errors/chamberlin-2022-gradual-discovery.md) | Medium | Resolved | 2026-01-30 | coherence_therapy, schema_dynamics, temporal_dynamics |

### build-errors/
(none yet)

### test-failures/
(none yet)

### performance-issues/
(none yet)

## Index by Component

### `paper_reproduction/chamberlin_2022`

- [Gradual Discovery Dynamics](logic-errors/chamberlin-2022-gradual-discovery.md) - Modeling Discovery as iterative process with stochastic transitions

### `paper_reproduction/pmc7250191`

- See `paper_reproduction/pmc7250191/learnings.md` for concept learning solutions

## Index by Tag

### Coherence Therapy
- [Gradual Discovery Dynamics](logic-errors/chamberlin-2022-gradual-discovery.md)

### Schema Dynamics
- [Gradual Discovery Dynamics](logic-errors/chamberlin-2022-gradual-discovery.md)

### Temporal Dynamics
- [Gradual Discovery Dynamics](logic-errors/chamberlin-2022-gradual-discovery.md)

### Model Realism
- [Gradual Discovery Dynamics](logic-errors/chamberlin-2022-gradual-discovery.md)

### Stochastic Modeling
- [Gradual Discovery Dynamics](logic-errors/chamberlin-2022-gradual-discovery.md)

## Quick Links

### Recent Solutions
1. **2026-01-30**: Gradual Discovery Dynamics (Chamberlin 2022 CT simulation)

### By Severity
- **Critical**: (none currently documented)
- **High**: (none currently documented)
- **Medium**: [Gradual Discovery Dynamics](logic-errors/chamberlin-2022-gradual-discovery.md)
- **Low**: (none currently documented)

## Guides

Design patterns and best practices extracted from solutions:

- [Prevention Strategies](../guides/PREVENTION_STRATEGIES.md) - Design patterns for gradual state transitions
- [Quick Start Checklist](../guides/QUICK_START_CHECKLIST.md) - Phase-by-phase implementation guide
- [Learnings Index](../guides/LEARNINGS_INDEX.md) - Navigation and meta-reference
- [README](../guides/README_LEARNINGS.txt) - Quick summary and orientation

## How to Add a Solution

Each solution should include:
1. **YAML Frontmatter** - Metadata for searchability
2. **Problem statement** - What was wrong
3. **Root cause** - Why it happened
4. **Solution** - How it was fixed
5. **Validation** - How it was tested
6. **Design decisions** - Tradeoffs made
7. **Impact** - Generalizability and maintenance burden

**File location**: `docs/solutions/[category]/[filename].md`

**Categories**:
- build-errors/
- test-failures/
- runtime-errors/
- performance-issues/
- database-issues/
- security-issues/
- ui-bugs/
- integration-issues/
- logic-errors/

See `docs/solutions/logic-errors/chamberlin-2022-gradual-discovery.md` for template.

## Integration with Paper Reproductions

Solutions are documented separately from detailed paper reproduction notes:
- **solutions/**: Problem/solution metadata for the knowledge base
- **paper_reproduction/[paper]/learnings.md**: Detailed insights specific to that reproduction
- **paper_reproduction/[paper]/model_design.md**: Architecture and design choices
- **paper_reproduction/[paper]/task_spec.md**: Technical specifications
