# BACKGROUND: Headline Image Director

## What this skill is trying to do
This skill treats the paper's headline image as a hybrid of three things:
- a conceptual overview figure
- a graphical abstract
- a shareable screenshot object

Its premise is that the best paper image does not summarize the whole paper.
It crystallizes one move.

## What was borrowed from gstack's excellent skills
Two gstack skills heavily shaped this one:

### From `/office-hours`
- strict AskUserQuestion structure
- one decision per question
- complete-over-shortcut bias
- plain-English explanation before asking for a decision
- explicit completion status protocol

### From `/plan-ceo-review`
- prerequisite-skill offer when the upstream thinking is too weak
- reading persisted branch context before resuming
- using handoff notes to avoid re-asking answered questions
- structured review before moving to the next phase

The image skill adapts those patterns to visual work:
- if the paper move is weak, bounce to `/seminal-paper-writer`
- if prior image briefs/handoffs exist, resume from them
- lock image type before moving into prompt-writing
- persist the brief and handoff so image direction can continue across sessions

## Source-backed figure principles

### 1. A good graphical abstract communicates one key message quickly
Jambor and Bornhäuser's "Ten simple rules for designing graphical abstracts" is the strongest practical source here. It recommends defining the key message for the audience first, then building the image around that message, with clear layout and iterative feedback.

### 2. Publishers treat these images as fast interdisciplinary previews
Elsevier describes a graphical abstract as a concise visual summary for an interdisciplinary audience. Cell describes it as a single-panel image designed to give readers an immediate understanding of the paper's take-home message and encourage browsing.

### 3. Figure design is a scientific communication problem, not a decorative one
Rolandi, Cheng, and Pérez-Kriz argue that figures are often the first part readers inspect and should be designed around purpose, audience, contrast, and readability. This supports choosing image class based on communicative job.

### 4. Academic drawing is a serious explanatory style
Goodsell's work on molecular illustration supports schematic drawing as a legitimate explanatory medium. Simplification, when done well, can reveal structure and mechanism more clearly than literal depiction.

## Why the workflow starts with image type
The figure-design and publisher guidance together imply that figure form should follow communicative function.
A mechanism should not be drawn like a field map.
A conceptual replacement should not be drawn like a threshold figure.
That is why this skill starts by locking the image class before any generation prompt is written.

## Why the taxonomy exists
The skill's taxonomy is a synthesis for this workflow, not a direct publisher taxonomy.

It includes:
- Mechanism diagram
- Threshold image
- Before/after ontology image
- Three-condition architecture
- Field map image
- Compression image
- Bridge image

These categories were built by combining:
- one-message graphical-abstract guidance
- figure-design principles around purpose and readability
- scientific-illustration support for schematic explanatory drawing

## Why validation is capped at four checks
The four checks are operationalizations of the literature:

1. One-move check
2. Thumbnail check
3. Reading-path check
4. Fidelity check

Together they catch the main failure modes:
- too many ideas
- too much small text / clutter
- confusing eye flow
- visual oversell

## Why the friend test matters
The two-question test is a practical extension of the literature's core concerns: fast comprehension and faithful representation.

Questions:
1. "What do you think the paper's main claim is?"
2. "What feels confusing, overstated, or missing?"

The first checks whether the image + abstract pair transmits one clear message.
The second checks whether simplification has become distortion.

## Core sources

### gstack skill patterns
- `office-hours/SKILL.md`
- `plan-ceo-review/SKILL.md`

### figure / graphical abstract sources
- Jambor HK, Bornhäuser M. *Ten simple rules for designing graphical abstracts*. PLOS Computational Biology, 2024.
- Elsevier. *Graphical abstract in Elsevier journals*.
- Cell Press. *Graphical Abstract Guidelines*.
- Rolandi M, Cheng K, Pérez-Kriz S. *A Brief Guide to Designing Effective Figures for the Scientific Paper*.
- Goodsell DS, Jenkinson J. *Molecular Illustration in Research and Education*.

## URLs
- https://raw.githubusercontent.com/garrytan/gstack/main/office-hours/SKILL.md
- https://raw.githubusercontent.com/garrytan/gstack/main/plan-ceo-review/SKILL.md
- https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011789
- https://www.elsevier.com/researcher/author/tools-and-resources/graphical-abstract
- https://www.cell.com/pb/assets/raw/shared/figureguidelines/GA_guide.pdf
- https://faculty.uca.edu/patrickd/chem4112/Effective_figures.pdf
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6186494/

## Source summary
The sources collectively support a workflow where one central message is identified first, the right image class is selected, the figure is designed as an academically styled conceptual plate, and progress is persisted across sessions via briefs and handoffs.
