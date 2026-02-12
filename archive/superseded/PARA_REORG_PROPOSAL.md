# PARA Reorganization Proposal

## The Problem

The root directory currently holds ~20 files serving very different purposes: planning docs, theory drafts, result images, comparison scripts, and Julia package files all sit side by side. Results are scattered across `results/`, `results_safe/`, `results_dangerous/`, and loose PNGs at root. There's no clear separation between "reference material I'm reading" (`papers/`), "reproductions I'm building" (`paper_reproduction/`), and "the theory I'm writing" (`ifs-active-inference-outline-v1.md`, `claims.md`).

---

## How PARA Maps Here

PARA has a tension with this repo because it's simultaneously a **Julia package** (which has conventions: `src/`, `test/`, `Project.toml`) and a **research knowledge base**. The proposal below respects Julia package structure while applying PARA to everything else.

### Projects (active, time-bound, with a clear deliverable)

**The IFS-Active Inference Paper** — your novel contribution. This is the main project. Everything driving toward a publishable paper belongs here.

**Paper reproductions** — each is a sub-project with a clear goal (reproduce results from a specific paper). These are currently well-organized internally but orphaned at the top level.

### Areas (ongoing responsibilities, standards to maintain)

**The Julia library itself** — `src/`, `test/`, `Project.toml`, `Manifest.toml`. This is the engine that powers everything. It's not time-bound; it evolves as you add models.

**Development operations** — `AGENTS.md`, `.github/`, CI config. The infrastructure that keeps the project running.

### Resources (reference material, things you consult)

**Papers you're reading** — the `papers/` directory. Pure reference material.

**Glossaries and notes** — `key_terms.md`, `learning_notes.md`. Reference you come back to.

### Archive (completed or inactive items)

**Old results and comparisons** — the loose PNGs, `results_comparison.png`, `COMPARISON_RESULTS.md`, `compare_implementations.jl`. These documented a completed phase (validating the library).

**Superseded plans** — `PLAN_v2.md` (if the library plan is now stable), `spec.md` (if superseded by the outline).

---

## Proposed Structure

```
ifs-active-inference/
│
│── README.md                          # Keep — package entry point
│── Project.toml                       # Keep — Julia package
│── Manifest.toml                      # Keep — Julia package
│── AGENTS.md                          # Keep — dev operations
│── .github/                           # Keep — CI
│── .gitignore
│
│── src/                               # AREA: the library (unchanged)
│   ├── IFSActiveInference.jl
│   ├── active_inference/
│   │   ├── ActiveInferenceCore.jl
│   │   ├── core.jl
│   │   ├── inference.jl
│   │   ├── efe.jl
│   │   ├── policy.jl
│   │   ├── learning.jl
│   │   ├── agent.jl
│   │   ├── visualization.jl
│   │   │
│   │   │── models/                    # NEW: group domain models together
│   │   │   ├── spider_model.jl
│   │   │   ├── trust_game.jl
│   │   │   ├── concepts_model.jl
│   │   │   └── coherence_therapy_model.jl
│   │   └── tmaze.jl                   # benchmark, not a domain model
│   │
│   ├── model.jl                       # → consider archiving (legacy?)
│   ├── simulation.jl
│   ├── plotting.jl
│   ├── activeinference_impl.jl        # → consider archiving (alt impl?)
│   ├── rxinfer_impl.jl               # → consider archiving if experimental
│   └── rxinfer_native.jl             # → consider archiving if experimental
│
│── test/                              # AREA: tests (unchanged)
│
│── projects/                          # NEW: PARA Projects
│   │
│   ├── ifs-paper/                     # PROJECT: the IFS-Active Inference paper
│   │   ├── outline-v1.md             # was: ifs-active-inference-outline-v1.md
│   │   ├── claims.md                 # was: claims.md (root)
│   │   ├── draft-critique.md         # was: v1-draft-critique.md
│   │   └── figures/                   # paper-specific figures
│   │
│   └── reproductions/                 # PROJECT(S): paper reproductions
│       ├── chamberlin_2022/           # (unchanged internally, well-organized)
│       ├── smith_2021/
│       ├── eckertal_2023/
│       └── pmc7250191/
│
│── resources/                         # NEW: PARA Resources
│   ├── papers/                        # was: papers/ (reference literature)
│   │   ├── ho_2021_compassion/
│   │   ├── koltko_rivera_2004_worldviews/
│   │   ├── limanowski_friston_2018_seeing_the_dark/
│   │   ├── limanowski_blankenburg_2013_minimal_self/
│   │   ├── deane_miller_wilkinson_2020_losing_ourselves/
│   │   ├── laukkonen_friston_chandaria_2025_beautiful_loop/
│   │   └── ActInf_SimPaper_preprint.pdf    # was: root level
│   │
│   ├── glossary.md                    # was: key_terms.md
│   ├── learning_notes.md              # was: learning_notes.md
│   └── docs/                          # was: docs/ (concepts, guides, solutions)
│       ├── concepts/
│       ├── guides/
│       └── solutions/
│
│── archive/                           # NEW: PARA Archive
│   ├── library-validation/            # completed phase
│   │   ├── COMPARISON_RESULTS.md
│   │   ├── compare_implementations.jl
│   │   ├── VERIFICATION.md
│   │   ├── HANDOFF.md
│   │   ├── results_comparison.png
│   │   ├── comparison_safe.png
│   │   └── comparison_dangerous.png
│   │
│   ├── results/                       # simulation outputs (reference)
│   │   ├── baseline/                  # was: results/
│   │   ├── safe/                      # was: results_safe/
│   │   └── dangerous/                 # was: results_dangerous/
│   │
│   ├── superseded/                    # old plans, specs
│   │   ├── PLAN_v2.md
│   │   └── spec.md
│   │
│   └── figures/                       # was: figures/ (generated plots)
│       ├── spider_*.png
│       ├── tmaze_*.png
│       └── trust_game/
│
│── scripts/                           # Keep at root (Julia convention)
│   ├── run.jl                         # was: run.jl (root)
│   ├── pmc7250191_reproduce.jl
│   ├── generate_example_plots.jl
│   ├── sharing_rate_sweep.jl
│   └── paper_figure_comparison.jl
```

---

## What Changes (and Why)

### 1. Root cleanup (biggest win)
The root drops from ~20 loose files to just the Julia package essentials (`README.md`, `Project.toml`, `Manifest.toml`, `AGENTS.md`) plus the four PARA directories. Right now the root is doing too many jobs — it's a package, a notebook, a filing cabinet, and an archive all at once.

### 2. `projects/ifs-paper/` — give the main deliverable a home
Your outline, claims, and critique are the heart of this repo's *original contribution*, but they're mixed in with infrastructure files. Grouping them makes it obvious what you're actually building toward.

### 3. `projects/reproductions/` — absorb `paper_reproduction/`
Rename only. The internal structure of each reproduction (PLAN.md, task_spec.md, model_design.md, learnings.md, library_mapping.md) is already great.

### 4. `resources/` — reading material and reference
`papers/` and the glossary are things you *consult*, not things you're *building*. Moving them under `resources/` makes that role explicit. The preprint PDF joins its friends instead of floating at root.

### 5. `archive/` — completed work stays findable but out of the way
The library validation phase (HANDOFF.md, COMPARISON_RESULTS.md, VERIFICATION.md, comparison PNGs) documented important work, but that phase is done. Same for the scattered result directories. Archiving them preserves the history without cluttering active workspace.

### 6. `scripts/` consolidation
`run.jl` and `compare_implementations.jl` move from root into `scripts/` where the other runnable scripts already live.

### 7. `src/active_inference/models/` (optional)
The domain-specific models (spider, trust game, concepts, coherence therapy) could be grouped under a `models/` subdirectory to separate them from the generic engine files. This is a small change but makes the library's architecture clearer: engine vs. applications.

---

## What Stays Put

- **`src/` and `test/`** — Julia package conventions. Don't fight them.
- **`AGENTS.md`** — needs to be at root for AI tooling to find it.
- **`.github/`** — must be at root for GitHub Actions.
- **Internal structure of reproductions** — already well-organized.

---

## Migration Risk

This is a git repo, so renames need care. A few things to watch:

- **Import paths in Julia code**: Moving model files into `models/` would require updating `include()` paths in `ActiveInferenceCore.jl`.
- **AGENTS.md references**: It currently points to file paths that would change. Update after moving.
- **CI workflows**: Check if any scripts reference specific paths.
- **Syncthing** (`.stfolder/`, `.stignore`): These are sync configuration — leave them at root.

If the import path changes feel risky, skip the `src/` internal reorg and just reorganize the documentation/knowledge side. That's where the biggest clarity gains are anyway.

---

## Priority Order

If you want to do this incrementally:

1. **Create `projects/ifs-paper/`** and move the outline, claims, critique → immediate clarity on what matters most
2. **Create `archive/`** and sweep the completed validation artifacts there → declutter root
3. **Rename `paper_reproduction/` → `projects/reproductions/`** and move `papers/` → `resources/papers/` → structural clarity
4. **Consolidate scripts** → minor cleanup
5. **`src/models/` refactor** → only if you're already touching the code
