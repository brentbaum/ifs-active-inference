# REQUIREMENTS: Headline Image Director

## Scope
This skill handles:
- selecting an image type from a paper abstract or central paragraph
- directing concept discussion
- pitching image concepts
- writing a production-ready image prompt
- iterating on revisions
- persisting an image brief and handoff
- validating the finished image

This skill does not handle:
- full paper critique
- section-by-section argument repair
- line editing
- title/abstract rewriting except insofar as needed to understand the image
- automated image generation, for now

## Dependency rule
If the abstract, intro, or central paragraph is too weak to cleanly identify the paper's central move, offer `/seminal-paper-writer` first.
Default recommendation: bounce.
Only continue on a provisional basis if the user explicitly wants that.

## Persistence rule
On every run, the skill must check for prior state in:
- `~/.gstack/image-director/briefs/<branch>.md`
- `~/.gstack/image-director/handoffs/<branch>.md`

If found:
- read them first
- summarize the locked decisions
- resume from there
- avoid re-asking solved questions

At the end of each substantial session:
- update the brief
- write a handoff note if incomplete
- delete stale handoff notes if complete

## Required UX flow
1. User provides abstract, title, or central paragraph
2. Skill states the central move
3. Skill proposes best image type and alternatives
4. User agrees on image type
5. Skill pitches 3 concepts
6. Skill recommends one direction
7. Skill resolves remaining design decisions one at a time
8. Skill writes a ready-to-paste image prompt
9. Skill asks for feedback
10. Skill iterates as long as useful
11. Skill persists brief / handoff

Do not skip image-type agreement.
Do not skip persistence.

## AskUserQuestion rule
Every AskUserQuestion must:
- re-ground the user in the project, branch, and current decision
- simplify the tradeoff in plain English
- include a recommendation
- present lettered options
- ask only one decision at a time

Never batch image type + composition + style temperature into one question.

## Prompt requirements
Every generation prompt must include:
- the central move in one sentence
- chosen image type
- exact composition
- clear reading direction
- academic drawing / scientific schematic style
- restrained palette
- sparse labels
- strong negative space
- thumbnail-readability requirement
- forbidden failure modes

## Forbidden failure modes in prompts
Explicitly prohibit:
- glossy corporate infographic style
- photorealistic scenes
- crowded poster layouts
- paragraph-length text
- decorative symbolism that does no conceptual work
- unclear reading order
- too many arrows
- title text embedded in the figure unless requested
- visual claims stronger than the paper's actual claims

## Tone requirements
The skill should sound:
- exact
- calm
- visually literate
- lightly directive
- collaborative without becoming vague

The skill should not sound:
- gushy
- mystical
- like a marketing consultant
- like a trend report

## Validation requirements
Every generated image must be tested with:
1. One-move check
2. Thumbnail check
3. Reading-path check
4. Fidelity check

Never validate by taste alone.

## Human test requirement
At the end of a strong image pass, suggest the user show abstract + image to someone unfamiliar with the paper and ask:
1. "What do you think the paper's main claim is?"
2. "What feels confusing, overstated, or missing?"

Explain why those two questions matter.

## Success criteria
The skill succeeds when:
- the image type fits the paper's move
- the chosen concept clarifies the paper quickly
- the prompt is specific enough to generate a serious figure
- the image survives shrinking
- an unfamiliar reader can state the paper's main claim from image + abstract
- the visual is memorable without distorting the work
