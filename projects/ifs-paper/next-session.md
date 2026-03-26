# Next Session: Conversation 5

Conversations 1–4b are done. Draft v8 is current. V2 simulation is working.

---

## What's been done (2026-03-26, massive session)

**Conversations 1-3:** Discriminant validity, section structure, abstract. All done.

**Conversation 4:** Carry-forward sentence locked. Discriminant validity trimmed (Option B). All settled.

**Conversation 4b — Move 3 (relational prediction error):**
- Formalized what happens inside the witnessing window
- Self's present-moment self-state generates relational PE at the identity level
- Two evidence channels: relational (primary) vs informational (secondary)
- Move 3 is Move 2 at sufficient depth — not a separate mechanism
- §8.3 written, consistency pass applied across all 12 sections → draft-v8.md
- draft-v8-academic-paper.tex + PDF generated

**Simulation v2 (three-move, tuned):**
- 3 hidden factors, 5 observation channels, depth-gated witnessed self-state
- All success criteria pass: cascade diagonal, relational depth gap, free-choice probe differentiation, H1 vs H2, ±20% sensitivity
- Five figures in `figures/v2/`

**Polarization simulation:**
- Two-part dog scenario (exile vs social manager)
- Oscillation → compromise → resolution under varying Self-energy
- Three figures

**Infrastructure:** Parameter registry (`simulation-magic-numbers.md`), CLAUDE.md, figure inspiration doc.

**Critique of draft v8:** Full architectural critique saved at `papers/critiques/critique-draft-v8-2026-03-26.md`. Verdict: READY FOR REVISION PASS.

---

## Next Session: Simulation Section Rewrite + Structural Promotion

### Priority 1: Promote §8.3 to top-level section (from critique)

Move 3 (relational prediction error) is the paper's deepest contribution but is buried as §8.3. Promote it to its own top-level section — the structural climax of the theoretical argument. This renumbers everything after it.

### Priority 2: Rewrite §10-11 with v2 simulation results

Full plan at: `papers/critiques/critique-draft-v8-2026-03-26.md` (critique) and the simulation section planning agent output.

**§10 (Simulation Design) — near-complete rewrite:**
- 10.1 Architecture (3 factors, 5 channels, context environmental)
- 10.2 The Witnessed Self-State Channel (inverse-capture gating, floor safeguard, update ordering)
- 10.3 Conditions (Exposure / Informational / Relational Depth + two-phase design)
- 10.4 H1 vs H2 (updated for four-element chain)
- 10.5 Pre-registered Cascade Metrics
- 10.6 Parameter Sensitivity

**§11 (Results) — near-complete rewrite:**
- 11.1 The Cascade Diagonal (Figure: ifs_v2_one_figure.png — THE iconic figure)
- 11.2 The Relational Depth Gap (Figure: ifs_v2_relational_depth_gap.png)
- 11.3 Free-Choice Probe (Figure: ifs_v2_free_choice_probe.png)
- 11.4 H1 vs H2 (Figure: ifs_v2_h1_vs_h2.png)
- 11.5 Self-Energy Sweep (Figure: ifs_v2_self_energy_sweep.png)
- 11.6 Real-Danger Safety Control
- 11.7 Parameter Sensitivity
- 11.8 Formation (keep as-is)
- 11.9 Polarization (updated with v2 results)

### Priority 3: Update §3.1 (Computational Setup)

Update hidden factors (3 not the old set), observation channels (5 not 4), scope discipline to mention derived witness precision.

### Priority 4: Update §12 (Discussion)

- §12.2: Remove/soften the relational PE limitation (it's now addressed)
- §12.4: Note relational channel prediction has simulation support; add EFE refactor as future work
- §12.1: Note sixth explanatory claim now has simulation backing

### Priority 5: Rewrite the conclusion (from critique)

The conclusion enumerates rather than gathers. "This paper does not finish the job. It builds the first floor." undersells what the paper has done. Rewrite as recognition — the floor holds, the mechanism is visible, the cascade is real.

### Priority 6: Introduction sharpening (from critique)

Add one sentence naming the COST of no formalization: "the claim that IFS works differently from exposure remains unfalsifiable" is sharper than "IFS lacks a formal account."

### Priority 7: Name one clinical surprise

The formalism predicts something clinicians don't already know: witnessing without life-updating should suffice for identity-level revision. State this as a finding, not just a future empirical target.

---

## Other pending items

- **EFE refactor:** GPT 5.4 is replacing the bespoke policy scoring with proper EFE. Evaluate when complete — may or may not make the paper stronger.
- **Scope qualification (Open Thread B):** Not all trauma is identity-organized. Find exceptions. Not urgent.
- **Conversation 6 (Diagrams):** The v2 simulation provides data figures. Conceptual diagrams (bundle diagram, mechanism inset) still needed. See figure-inspiration.md.
- **Jargon audit:** Done in this session. Minor items remain (harmonize Table 1/Appendix C).

## Files to read at session start

- `projects/ifs-paper/draft-v8.md` — current draft
- `papers/critiques/critique-draft-v8-2026-03-26.md` — latest critique
- `projects/ifs-paper/simulation-v2-spec.md` — simulation design
- `projects/ifs-paper/simulation-magic-numbers.md` — parameter registry
- `memory/project_revision_roadmap.md` — full roadmap
