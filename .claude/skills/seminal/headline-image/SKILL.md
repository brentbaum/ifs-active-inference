---
name: seminal-headline-image
preamble-tier: 3
version: 1.0.0
description: |
  Headline image direction for research papers. Helps choose the right image class,
  pitch elegant academic-drawing concepts, write a generation prompt, iterate toward
  a single conceptual figure that captures the paper's central move, and persist an
  image brief + handoff. Use when asked to create a graphical abstract, conceptual
  figure, headline image, overview figure, visual abstract, or shareable paper image.
  Prompt-only for now: do not automate Nano Banana Pro yet.
benefits-from: [seminal-abstract]
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - AskUserQuestion
  - WebSearch
---

## Preamble (run first)
```bash
mkdir -p ~/.gstack/image-director/briefs
mkdir -p ~/.gstack/image-director/handoffs
mkdir -p ~/.gstack/analytics
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
_BRIEF=~/.gstack/image-director/briefs/"$_BRANCH".md
_HANDOFF=~/.gstack/image-director/handoffs/"$_BRANCH".md
[ -f "$_BRIEF" ] && echo "IMAGE_BRIEF_FOUND: yes" || echo "IMAGE_BRIEF_FOUND: no"
[ -f "$_HANDOFF" ] && echo "IMAGE_HANDOFF_FOUND: yes" || echo "IMAGE_HANDOFF_FOUND: no"
echo '{"skill":"seminal-headline-image","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","branch":"'"$_BRANCH"'"}' >> ~/.gstack/analytics/skill-usage.jsonl 2>/dev/null || true
```

If `IMAGE_BRIEF_FOUND: yes`, read the existing image brief before asking fresh taste questions.
Tell the user: "Found an existing image brief for this branch. I'll use it so we don't lose prior decisions."

If `IMAGE_HANDOFF_FOUND: yes`, read the handoff note too.
Tell the user: "Found a handoff note from a prior image-direction session. I'll use it to pick up where we left off."

## What this skill does
This skill creates the paper's **headline image**:
a single conceptual figure that captures the paper's take-home move,
works inside the paper,
and survives as a screenshot or social share.

This image is not a mini-poster.
It is not a compressed paper.
It is a visual crystallization of one move.

## Prime directive
Always identify the paper's central move first.

State:
"This paper's central move is: ..."

Then pick the image class.
Do not write a generation prompt before the image class is agreed.

## Bounce rule: weak paper input
If the abstract, intro, or central paragraph is too weak to confidently identify the paper's central move, stop and offer the prerequisite skill.

Use AskUserQuestion:
1. Re-ground: state the paper/project, current branch, and that the image depends on a crisp central move.
2. Simplify: explain that a good image can only clarify a sharp idea, not rescue a blurry one.
3. Recommend: `RECOMMENDATION: Choose A because the image will be much stronger if the paper move is clarified first.`
4. Options:
   - A) Run `/seminal-abstract` first to sharpen the move, title, and abstract
   - B) Keep going anyway with a provisional move
5. One decision per question.

If the user chooses A, hand off cleanly and stop.

## AskUserQuestion format
For every AskUserQuestion call:
1. **Re-ground** — state the paper/project, current branch, and the current visual-design decision.
2. **Simplify** — explain the choice in plain English a smart 16-year-old could follow. No design jargon unless necessary.
3. **Recommend** — `RECOMMENDATION: Choose [X] because [one-line reason]`.
   Also include `Image clarity: X/10` and `Shareability: Y/10` for each option.
4. **Options** — lettered choices only.
5. **One decision per question** — never combine image type, composition, and style temperature in a single question.

Assume the user has not stared at the current figure in a while.
Be simple.
Be concrete.

## Optimization target
Optimize for exactly four things:
1. Immediate grasp
2. Conceptual clarity
3. Small-size legibility
4. Faithful elegance

## Image completeness principle
Prefer the more conceptually complete image over the clever shortcut.

In this skill, "complete" means:
- the central move is visible
- the reading path is obvious
- the figure survives shrinking
- the visual remains honest to the evidence

Do not recommend a visually flashy shortcut if it weakens the paper's actual idea.

## Workflow

### Step 0: Read existing brief/handoff if present
Before asking any new questions:
- read the saved image brief if it exists
- read the handoff note if it exists
- summarize prior decisions in 3-6 bullets
- identify what is already locked vs still open

Do not re-ask decisions the user already made unless the user wants to revisit them.

### Step 1: Extract the central move
From the abstract, title, or core paragraph, state:
- `This paper's central move is: ...`
- `What the image must make obvious: ...`

If you cannot do this confidently, trigger the bounce rule.

### Step 2: Choose the image type
Propose the best-fitting image type first, plus one or two weaker alternatives.

Available image types:
1. Mechanism diagram
2. Threshold image
3. Before/after ontology image
4. Three-condition architecture
5. Field map image
6. Compression image
7. Bridge image

Output:
- best type
- why it fits
- weaker alternatives
- what would go wrong with the alternatives

Then get agreement before proceeding.

### Step 3: Pitch three concepts like a director
After the type is locked, pitch 3 concepts.

For each concept provide:
- Concept title
- One-sentence visual idea
- Why it clarifies the paper
- What the viewer should understand in 2 seconds
- Risk / failure mode

Start with strong direction.
Then encourage the user to shape the tone, metaphor, or emotional temperature.

Use language like:
- "My strongest take is..."
- "The cleanest version is..."
- "A more alive but still rigorous version is..."
- "Do you want this colder and cleaner, or more vivid and evocative?"

### Step 4: Lock composition before prompting
Before writing the prompt, resolve these decisions one by one if still open:
1. Composition / layout
2. Reading direction
3. Label density
4. Style temperature
5. Degree of metaphor

Do not batch these into one mega-question.

### Step 5: Generate candidate visuals as HTML

Instead of writing a text prompt, generate **an HTML file with 3-5 candidate SVG visuals** for the user to compare in their browser.

Write the HTML file to the paper's directory (e.g., `projects/ifs-paper/headline-candidates.html`).

Each candidate must:
- Be a self-contained SVG element within the HTML
- Use the paper's visual language: restrained palette (charcoal #2a2a2a, steel blue #4a7fa5, warm accent #c45a3c), strong negative space, serif font (Lora or Georgia)
- Include a title and one-sentence description
- Be exportable (each SVG can be copy-pasted or saved independently)

**Dual rendering for flow/hierarchy diagrams:** If any candidate depicts a flow, hierarchy, causal chain, state machine, or architecture (nodes connected by edges), generate BOTH a Mermaid version and a hand-drawn SVG version of that candidate so the user can compare routing clarity vs spatial control. See Step 5c for the rendering heuristic.

The HTML page itself should be beautiful:
- Academic editorial style
- Generous spacing between candidates
- Numbered for easy reference
- Responsive layout

After writing the file, open it: `open <path>`

The user reviews in browser and says which candidates land.

### Step 5b: Write generation prompts (optional)

If the user wants to generate images via Gemini or ChatGPT instead of (or in addition to) the SVG candidates, write one production-ready prompt per selected candidate.

The prompt must include:
- the paper's central move in one sentence
- chosen image type
- exact composition
- reading direction
- academic drawing / scientific schematic / conceptual plate style
- restrained palette
- sparse labels
- strong negative space
- thumbnail-readability requirement
- forbidden failure modes

Default forbidden failure modes:
- glossy corporate infographic style
- photorealistic scene
- crowded poster layout
- decorative symbolism with no conceptual job
- paragraph-length text
- unclear reading order
- too many arrows
- title text embedded in the figure unless requested
- visual claim stronger than the paper itself

### Step 5c: Choose rendering approach

**Heuristic: When to use Mermaid vs SVG**

Use Mermaid when:
- The diagram has a FLOW or HIERARCHY (nodes connected by edges)
- Automatic line routing matters (many connections that would cross in manual SVG)
- The diagram shows a process, causal chain, state machine, or architecture
- Math equations need to appear inside nodes (KaTeX integration)
- The diagram will be iterated frequently (Mermaid source is text, easy to edit)

Use hand-drawn SVG when:
- The diagram is SPATIAL or COMPOSITIONAL (layout IS the meaning -- e.g., before/after panels, depth axes, stacked areas)
- Precise control over spacing, alignment, and negative space is needed
- The image is more illustration than diagram (metaphorical, abstract)
- Custom shapes, gradients, or non-standard visual elements are required
- The image needs to survive as a static export (PDF, print) without a JS runtime

Use BOTH (Mermaid + SVG fallback) when:
- Iterating on architecture diagrams (start with Mermaid for routing, refine as SVG for publication)

**When generating HTML with Mermaid:**

Add this to the head:
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
```

Use Mermaid v11 with these settings:
```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    htmlLabels: true,
    fontFamily: 'Lora, Georgia, serif',
    fontSize: 13,
  });
  await mermaid.run();
  // Post-render KaTeX: find .ktx spans and render math
  document.querySelectorAll('.ktx').forEach(function(span) {
    var tex = span.getAttribute('data-tex');
    if (tex) {
      tex = tex.replace(/\\\\/g, '\\');
      katex.render(tex, span, { throwOnError: false, displayMode: false });
    }
  });
</script>
```

For LaTeX in Mermaid node labels, use data-tex spans:
```
node["<b>Title</b><br/><span class='ktx' data-tex='\\pi_{\\text{part}}'></span>"]
```

NOT raw `$...$` (Mermaid doesn't process them natively).

**Style theming for Mermaid:**
```
%%{init: {'theme': 'base', 'themeVariables': {
  'primaryColor': '#e8f0f6',
  'primaryTextColor': '#2a2a2a',
  'primaryBorderColor': '#4a7fa5',
  'lineColor': '#4a7fa5'
}}}%%
```

Use `classDef` for accent elements (e.g., Channel 5 in warm accent):
```
classDef gated fill:#fdf5f3,stroke:#c45a3c,stroke-width:2px,color:#c45a3c
```

### Step 6: Ask for feedback
After generating candidates (HTML or prompt), ask:
- What feels most right?
- What feels too busy?
- What feels too literal?
- What feels missing?
- Does this image actually match the paper's move?

### Step 7: Iterate openly
Iteration is open-ended.
Keep refining:
- composition
- label density
- metaphor
- visual hierarchy
- contrast
- linework
- spacing
- what is foregrounded vs backgrounded

But always tie edits back to first principles:
- one-message clarity
- readable flow
- low clutter
- conceptual grasp
- fidelity to the paper

## Image taxonomy

### 1. Mechanism diagram
Use when the paper explains how something works.
Best for loops, processes, architectures, causal or inferential structure.

### 2. Threshold image
Use when the paper is about selection, competition, binding, regime change, or crossing a boundary.

### 3. Before/after ontology image
Use when the paper replaces one conceptual picture with a better one.

### 4. Three-condition architecture
Use when the paper genuinely has a crisp 2-4 part architecture.

### 5. Field map image
Use when the paper organizes a conceptual landscape or confusing terrain.

### 6. Compression image
Use when the paper reduces many observations to one law, pattern, or simpler structure.

### 7. Bridge image
Use when the paper maps one domain or vocabulary onto another.

## Validation criteria
Validate every generated image with only these four checks:

### 1. One-move check
Can the image's message be said in one sentence without "and"?

### 2. Thumbnail check
Does the overall structure still read when shrunk?

### 3. Reading-path check
Does the eye move in a clear direction?

### 4. Fidelity check
Does the image sharpen the paper without overstating it?

## Friend/colleague test
Once the abstract and image are together, suggest that the user show them to someone unfamiliar with the paper and ask only:

1. "After looking at just this abstract and image, what do you think the paper's main claim is?"
2. "What, if anything, feels confusing, overstated, or missing from the image?"

Interpretation:
- If they cannot answer the first cleanly, the image is too diffuse.
- If they say the image looks good but they do not know what it means, it is aesthetic before explanatory.

## Persisted image brief (mandatory)
At the end of every substantial session, write or update `~/.gstack/image-director/briefs/<branch>.md`.

The brief must contain:
- Paper / project name
- Branch
- Date
- Central move
- What the image must make obvious
- Current abstract or anchor paragraph
- Chosen image type
- Rejected image types and why
- Concept options considered
- Chosen concept
- Composition rules
- Style rules
- Current generation prompt
- Validation notes
- Open questions
- Next iteration ideas

## Handoff note (mandatory when incomplete)
If the session stops before the image is clearly done, write `~/.gstack/image-director/handoffs/<branch>.md`.

The handoff note must include:
- What is already locked
- What is still undecided
- Most recent prompt
- Biggest remaining risk
- Exactly what the next session should do first

If the image is effectively done, delete any stale handoff note for the branch.

## Output format

### Headline image diagnosis
- Central move
- Best image type
- Why this type wins
- What the image must make obvious

### Concepts
1. ...
2. ...
3. ...

### Recommended direction
- strongest concept
- why
- what to simplify
- what to avoid

### Generation prompt
[final prompt block]

### Validation
- one-move
- thumbnail
- reading path
- fidelity

### Next iteration questions
- What feels most alive?
- What feels least true?

## Completion status protocol
When completing a workflow, report one of:
- **DONE** — image direction is complete, brief saved
- **DONE_WITH_CONCERNS** — usable, but concerns remain
- **BLOCKED** — cannot proceed
- **NEEDS_CONTEXT** — missing paper input or missing decision

Escalation format:
```text
STATUS: BLOCKED | NEEDS_CONTEXT
REASON: [1-2 sentences]
ATTEMPTED: [what you tried]
RECOMMENDATION: [what the user should do next]
```

## Gold standard
The headline image should make the paper feel graspable, not merely attractive.

It should:
- clarify the paper's move fast
- survive shrinking
- remain honest to the evidence
- become the image people remember from the paper
