---
name: seminal-abstract
description: |
  Title and abstract workshop for theoretical, conceptual, or field-shaping papers.
  Optimizes for sharpness, inevitability, and memorability — not compression.
  Use when writing or revising a paper title and abstract.
  Runs in review mode (critique existing) or draft mode (write from scratch).
  Invoke with /seminal-abstract or when the user says "workshop the abstract", "title and abstract", "abstract review".
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - AskUserQuestion
---

# Skill: Seminal Abstract

## Special mode: thesis abstract + seminal title

Use this mode when the paper is theoretical, conceptual, synthetic, or trying to make a field-shaping move.
The goal is not to summarize the whole paper.
The goal is to make the paper feel sharp, inevitable, and worth reading.

### What to optimize for
The title and abstract together should make a reader feel:
- there is one real move here
- I understand the stakes quickly
- this paper has a clean architecture
- the contribution is memorable
- the claim is ambitious but cashed out

---

## Title guidance

### Default title standard
Prefer a title that is:
- short
- literal
- searchable
- contribution-bearing
- defensible at the paper's exact evidence level

### Title rules
- Put the contribution, mechanism, or object in the title, not the workflow.
- Prefer real keywords over private jargon.
- Avoid cleverness unless the paper truly has a singular memorable move.
- Avoid colons by default.
- Avoid question marks by default.
- Avoid acronyms unless they are standard in the field.
- Avoid methods-heavy titles unless the method itself is the contribution.
- If the paper introduces a named theory, mechanism, or hypothesis, the title may simply name it — but only if the abstract immediately cashes it out.

### Preferred title modes
1. Mechanism for domain
2. Law or pattern in domain
3. Hypothesis or theory of phenomenon
4. Named framework
5. Rarely: thesis-like slogan title

### Title test
Ask:
- Could an adjacent scholar understand the paper's move from the title alone?
- Does the title contain the keyword a serious reader would actually search?
- Does the title say what the paper changes, not just what it touches?
- Is the title stronger than the evidence? If yes, weaken it.

---

## Abstract guidance

### Target abstract style
Write an abstract that feels like the opening move of an argument, not a compressed table of contents.

It should be:
- short
- proposition-first
- high-signal
- concrete
- slightly horizon-opening
- free of ceremony

### Abstract rules
- First sentence: name the live question, bottleneck, or mistaken assumption.
- Second sentence: state the paper's move in plain language.
- By sentence three or four, the reader should know what is new.
- Use numbered conditions / principles / components only when the paper genuinely has a crisp architecture.
- Include at least one concrete anchor: theorem, benchmark, corpus, dataset, effect size, formal result, or type of analysis.
- End by widening the horizon exactly one notch: what this changes, enables, or reorients.
- Keep the prose energetic, but keep the evidence visible.
- If the abstract opens with a question, answer it immediately in the next sentence.

### What to cut
Delete:
- "X is important"
- "In recent years..."
- "There has been growing interest..."
- mini literature reviews
- vague claims of novelty
- adjective stacks
- hedging piles
- throat-clearing before the move appears

### Preferred abstract shapes
1. Obstacle → move → result → implication
2. Question → answer → mechanism → horizon
3. Assumption → reversal → evidence → consequence
4. One problem → two to four principles → payoff

### Sentence-level style
- Prefer live verbs over abstract nouns.
- Prefer one decisive sentence over two diluted ones.
- Prefer portable nouns: terms a later paper could reuse.
- Define coined terms instantly.
- Make the strongest sentence the one most likely to be remembered.

### Abstract test
Ask:
- Is the first sentence already alive?
- Is the contribution explicit by sentence two?
- Is there one sentence another scholar could cite or repeat?
- Is there at least one concrete anchor?
- Does the ending open a horizon without sounding inflated?
- Could 20% be cut with no loss? If yes, cut it.

---

## Preferred failure diagnosis language
- "The title names the area, but not yet the move."
- "The abstract delays the contribution by two sentences."
- "The prose is promising, but still too ceremonial."
- "The abstract gestures at significance without cashing it out."
- "The title is memorable, but not yet searchable."
- "The ending overreaches the evidence."

---

## Steps

### Step 1: Locate or receive the paper

If the user provides a file path or the paper is in the working directory, read the abstract and title from the file. Otherwise, ask the user to paste the current abstract and title.

Also read:
- The paper's carry-forward sentence or central claim (if known)
- The paper's argumentative spine (if stated)

### Step 2: Review mode — critique the existing title and abstract

Report in exactly this order:
1. **Central move:** What is the paper's one real contribution?
2. **Title verdict:** Does it name the move cleanly? Which title mode does it use?
3. **Abstract speed:** How many sentences before the contribution appears?
4. **Concrete anchor:** What is it? Is it present?
5. **Horizon:** Does the ending enlarge stakes without overselling?
6. **Dead words:** Which words are generic, inflated, or dead?
7. **Rewritten title:** One alternative. Label it and explain the choice.
8. **Rewritten abstract:** One full draft in thesis/seminal mode. Label the shape used (obstacle → move → result → implication, etc.).

### Step 3: Draft mode (if no existing abstract, or if user requests a fresh draft)

Ask the user for:
- The paper's central move in one sentence
- The concrete anchor (simulation result, formal theorem, empirical finding)
- The target audience

Then draft title and abstract directly in thesis/seminal mode. Present two title options and one abstract.

### Step 4: Iterate

After presenting the draft, ask:
- "Does the first sentence land?"
- "Is the concrete anchor visible enough?"
- "Does the ending feel right?"

Offer one targeted revision per round. Do not rewrite the whole abstract unless the user requests it.

---

## Notes
- This skill is for theoretical and synthetic papers. For empirical papers reporting experimental results, the concrete anchor is a finding or effect size; make sure it appears.
- Do not pad. Each sentence must earn its place.
- The rewritten abstract should be a real draft, not a template with blanks.
- When workshopping iteratively, track which version the user prefers and build on it.
