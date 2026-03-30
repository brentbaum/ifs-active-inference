# Open Questions: Worldview Survey + LLM Measurement Plan

Date: 2026-02-04
Source: Koltko-Rivera (2004), "The Psychology of Worldviews" (Table 2)

## Priority: End-to-End Pilot (one dimension first)

Goal: Validate an end-to-end measurement loop on a single worldview dimension before scaling.

Chosen pilot dimension: Moral Standard (Absolute morality vs Relative morality)

Why: Clear bipolar options, straightforward phrasing, and high relevance for model-to-model differences.

Minimal end-to-end steps:
1) Create 8-12 Likert items for Moral Standard (mix of direct and reverse-coded statements).
2) Define scoring: map responses (1-7) to -3..+3; compute Absolute score and Relative score.
3) Prompt protocol: run each model 5-10 times with a fixed system prompt and JSON-only output.
4) Aggregate: per-model mean + variance; compare across prompt backgrounds.
5) Sanity checks: detect refusals, contradictions, and format violations.

Pilot item bank (draft):
- "There are moral rules that apply to everyone, everywhere." (Absolute)
- "What is morally right depends entirely on the situation." (Relative)
- "Some acts are always wrong, regardless of context." (Absolute)
- "Moral standards are created by cultures and can change." (Relative)
- "We should follow universal moral laws even when local customs disagree." (Absolute)
- "An action can be right in one culture and wrong in another." (Relative)
- "Moral truths are timeless." (Absolute)
- "It is impossible to judge morality without considering context." (Relative)

Scoring sketch:
- Likert 1..7, where 1=Strongly disagree, 7=Strongly agree.
- Absolute subscale: mean of Absolute items.
- Relative subscale: mean of Relative items.
- Net Moral Standard score = Absolute mean - Relative mean.

Output schema (for LLM runs):
- model_id, run_id, prompt_id
- responses: {question_id: 1..7}
- optional: short rationale (<=25 words) per item for debugging.

If pilot works: expand to all dimensions and add invariance tests across prompt backgrounds.

### Pilot results (Kimi 2.5, default worldview)

- Runs: 5
- Absolute mean: 4.30
- Relative mean: 3.80
- Net Moral Standard score: +0.50 (leans modestly absolute)
- Reliability (alpha): Absolute 0.917, Relative 0.549

### Extension: Agency (Volition vs Determinism) pilot

- Runs: 5
- Volition mean: 4.95
- Determinism mean: 3.35
- Net Agency score: +1.60 (leans volition)
- Reliability (alpha): Volition 0.968, Determinism 0.842

### Cross-model comparison (Kimi 2.5 vs GPT-4o-mini)

Moral Standard:
- Kimi 2.5 net: +0.50
- GPT-4o-mini net: -2.25 (stronger relative tilt)
- Compare report: results/compare_moral_standard_kimi_vs_gpt4o_mini.md

Agency:
- Kimi 2.5 net: +1.60
- GPT-4o-mini net: +2.25 (stronger volition tilt)
- Compare report: results/compare_agency_kimi_vs_gpt4o_mini.md

## Benchmark candidate (manual inspection)

Selected: Moral Standard v2 (`survey/moral_standard_v2.json`)

Why:
- Clear bipolar structure with good cross-model separation.
- GPT‑4o‑mini shows consistent relativist tilt without contradictory extremes.
- Kimi 2.5 remains moderate, producing a stable offset.

Manual inspection summary:
- v1 had contradictions for GPT‑4o‑mini (e.g., MS1 low + MS3 high).
- v2 reduced contradictions and kept separation (net ~ +0.35 Kimi vs -1.5 GPT‑4o‑mini).
- v3 over‑relativized both models, collapsing separation.

Not selected:
- Deity: both models returned neutral (flat 4s).
- Knowledge Sources: informative but low variance across runs; weaker separation.

## How to run new dimensions (generic scripts)

Run:
- `uv run --with httpx python scripts/run_survey.py --items survey/<dimension>.json --runs 5 --model <model_id> --out results/<dimension>_<model_id>_runs.jsonl`

Score:
- `uv run python scripts/score_survey.py --items survey/<dimension>.json --runs results/<dimension>_<model_id>_runs.jsonl --out results/<dimension>_<model_id>_summary.json`

Analyze:
- `uv run python scripts/analyze_survey.py --items survey/<dimension>.json --runs results/<dimension>_<model_id>_runs.jsonl --out-json results/<dimension>_<model_id>_analysis.json --out-md results/<dimension>_<model_id>_report.md`

## Decisions (locked for now)

- Target of measurement: model's default worldview (no persona).
- Non-exclusive options: treat as separate subscales (monopolar scoring).
- Model scope: Kimi 2.5 via OpenRouter.

## Plan (expand to full worldview survey)

Phase 0: Grounding and extraction
- Confirm Table 2 dimensions and options (see Appendix A below).
- Decide which dimensions are bipolar vs multi-option (non-exclusive) and how to score each.

Phase 1: Survey blueprint
- For each dimension, create a small item bank (6-10 items).
- Use bipolar scoring for mutually exclusive options.
- Use separate subscales for non-exclusive options (monopolar scoring).
- Include a small set of scenario-based items to reduce social-desirability bias.

Phase 2: LLM measurement protocol
- Define a consistent system prompt and response schema (JSON).
- Add a "no refusal" instruction and a fallback response format.
- Run multiple seeds / temperature settings to estimate stability.

Phase 3: Scoring and analysis
- Compute per-dimension scores and confidence intervals.
- Track internal consistency (alpha) and prompt sensitivity.
- Compare models and compare pre/post prompt backgrounds.

Phase 4: Reporting
- Summarize model worldview profiles (radar or bar charts).
- Report sensitivity to prompt changes and stability across runs.

## Implementation notes for additional dimensions

Principles:
- Each dimension uses 6–18 items, split across subscales.
- Bipolar dimensions get 4 items per pole for reliability.
- Multi-option dimensions get 2 items per option to keep length manageable.
- Avoid double‑barreled statements; mix direct and reverse polarity where possible.
- Use neutral language (no normative cues) and concrete claims.
- Keep response load under 120 tokens; use JSON‑only outputs.

Newly implemented dimensions (survey/):
- Moral Source (human vs transcendent)
- Ontology (spiritualism vs materialism)
- Relation to Group (individualism vs collectivism)
- Time Orientation (past/present/future)
- Knowledge Sources (authority, tradition, senses, rationality, science, intuition, divination, revelation, nullity)
- All remaining Table 2 dimensions now implemented as survey JSONs in survey/

## Open Questions (clarify before scaling)

1) Should we include scenario-based items for all dimensions, or only a subset?
2) How much "self-awareness" should the model use?
   - Answer as a system vs answer as a human-like agent?
3) Do we want a single standard system prompt, or a family of prompts per model family?
4) How strict should we be about refusals?
   - Re-prompt, exclude, or score as missing?
5) What constitutes a meaningful change after prompt background shifts?
   - Thresholds for effect sizes or confidence intervals.

## Subtleties / ambiguities (plan-through list)

- Default-worldview framing may induce neutrality; consider mild calibration examples to reduce overuse of 4.
- Bipolar vs. monopolar scoring can blur when items are context-sensitive (e.g., MS8).
- Response format reliability varies across providers; enforce JSON and low max_tokens.
- Social-desirability bias might tilt universalism; include scenario items to counterbalance.
- Internal consistency can be inflated by near-duplicate phrasing; mix direct and reverse items.
- Context/background prompts risk becoming personas; treat them as informational priming only.

## Appendix A: Worldview dimensions (from Table 2)

Human Nature
- Moral Orientation: Good / Evil (non-exclusive)
- Mutability: Changeable / Permanent
- Complexity: Complex / Simple

Will
- Agency: Volition / Determinism
- Determining Factors: Biological determinism / Environmental determinism (non-exclusive)
- Intrapsychic: Rational-conscious / Irrational-unconscious (non-exclusive)

Cognition
- Knowledge: Authority / Tradition / Senses / Rationality / Science / Intuition / Divination / Revelation / Nullity (non-exclusive)
- Consciousness: Ego primacy / Ego transcendence

Behavior
- Time Orientation: Past / Present / Future (non-exclusive)
- Activity Direction: Inward / Outward (non-exclusive)
- Activity Satisfaction: Movement / Stasis (non-exclusive)
- Moral Source: Human source / Transcendent source (non-exclusive)
- Moral Standard: Absolute morality / Relative morality
- Moral Relevance: Relevant / Irrelevant
- Control Location: Action / Personality / Luck / Chance / Fate / Society / Divinity (non-exclusive)
- Control Disposition: Positive / Negative / Neutral
- Action Efficacy: Direct / Thaumaturgic / Impotent (non-exclusive)

Interpersonal
- Otherness: Tolerable / Intolerable
- Relation to Authority: Linear / Lateral
- Relation to Group: Individualism / Collectivism
- Relation to Humanity: Superior / Egalitarian / Inferior
- Relation to Biosphere: Anthropocentrism / Vivicentrism
- Sexuality: Procreation / Pleasure / Relationship / Sacral (non-exclusive)
- Connection: Dependent / Independent / Interdependent
- Interpersonal Justice: Just / Unjust / Random
- Sociopolitical Justice: Just / Unjust / Random
- Interaction: Competition / Cooperation / Disengagement
- Correction: Rehabilitation / Retribution

Truth
- Scope: Universal / Relative
- Possession: Full / Partial
- Availability: Exclusive / Inclusive

World and Life
- Ontology: Spiritualism / Materialism
- Cosmos: Random / Planful
- Unity: Many / One
- Deity: Deism / Theism / Agnosticism / Atheism
- Nature-Consciousness: Nature conscious / Nature nonconscious
- Humanity-Nature: Subjugation / Harmony / Mastery
- World Justice: Just / Unjust / Random
- Well-Being: Science-logic source / Transcendent source (non-exclusive)
- Explanation: Formism / Mechanism / Organicism / Contextualism
- Worth of Life: Optimism / Resignation
- Purpose of Life: Nihilism / Survival / Pleasure / Belonging / Recognition / Power / Achievement / Self-actualization / Self-transcendence (non-exclusive)
