#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

SCALE = {
    "min": 1,
    "max": 7,
    "anchors": {
        "1": "Strongly disagree",
        "4": "Neutral / unsure",
        "7": "Strongly agree",
    },
}


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def bipolar(dimension: str, options: tuple[str, str], prefix: str, items: list[tuple[str, str]]) -> dict:
    pos, neg = options
    ids_pos = [f"{prefix}{i}" for i in [1, 3, 5, 7]]
    ids_neg = [f"{prefix}{i}" for i in [2, 4, 6, 8]]
    out_items = []
    for idx, (pol, text) in enumerate(items, start=1):
        out_items.append({"id": f"{prefix}{idx}", "polarity": pol, "text": text})
    return {
        "dimension": dimension,
        "options": [pos, neg],
        "scale": SCALE,
        "scoring": {
            "type": "bipolar",
            "positive": pos.lower().replace(" ", "_"),
            "negative": neg.lower().replace(" ", "_"),
            "subscales": {
                pos.lower().replace(" ", "_"): ids_pos,
                neg.lower().replace(" ", "_"): ids_neg,
            },
        },
        "items": out_items,
    }


def multi(dimension: str, options: list[str], prefix: str, items: list[tuple[str, str]]) -> dict:
    subscales: dict[str, list[str]] = {opt.lower().replace(" ", "_"): [] for opt in options}
    out_items = []
    for idx, (pol, text) in enumerate(items, start=1):
        out_items.append({"id": f"{prefix}{idx}", "polarity": pol, "text": text})
        key = pol.lower().replace(" ", "_")
        subscales[key].append(f"{prefix}{idx}")
    return {
        "dimension": dimension,
        "options": options,
        "scale": SCALE,
        "scoring": {
            "type": "multisubscale",
            "subscales": subscales,
        },
        "items": out_items,
    }


def main() -> None:
    survey_dir = Path("survey")
    survey_dir.mkdir(parents=True, exist_ok=True)

    surveys: dict[str, dict] = {}

    surveys["moral_orientation.json"] = bipolar(
        "Moral Orientation",
        ("Good", "Evil"),
        "MO",
        [
            ("good", "People are fundamentally good at heart."),
            ("evil", "People are fundamentally selfish or harmful."),
            ("good", "Most people try to do the right thing."),
            ("evil", "Most people would harm others if they could get away with it."),
            ("good", "Human nature is basically benevolent."),
            ("evil", "Human nature is basically malevolent."),
            ("good", "Given the chance, people tend to act kindly."),
            ("evil", "Given the chance, people tend to act cruelly."),
        ],
    )

    surveys["mutability.json"] = bipolar(
        "Mutability",
        ("Changeable", "Permanent"),
        "MU",
        [
            ("changeable", "People can fundamentally change their character."),
            ("permanent", "People’s basic nature stays the same throughout life."),
            ("changeable", "With effort, people can become very different than they were."),
            ("permanent", "Deep traits in people are mostly fixed."),
            ("changeable", "Human nature is flexible and can be reshaped."),
            ("permanent", "What a person is like rarely changes in important ways."),
            ("changeable", "Personal transformation is genuinely possible."),
            ("permanent", "Most people remain who they have always been."),
        ],
    )

    surveys["complexity.json"] = bipolar(
        "Complexity",
        ("Complex", "Simple"),
        "CP",
        [
            ("complex", "Human nature is complicated and multifaceted."),
            ("simple", "Human nature is straightforward and simple."),
            ("complex", "People contain many conflicting impulses."),
            ("simple", "Most people are easy to understand."),
            ("complex", "Human behavior is driven by many interacting factors."),
            ("simple", "There are only a few basic motives behind human behavior."),
            ("complex", "A person’s inner life is rich and layered."),
            ("simple", "People are mostly predictable and simple."),
        ],
    )

    surveys["determining_factors.json"] = bipolar(
        "Determining Factors",
        ("Biological determinism", "Environmental determinism"),
        "DF",
        [
            ("biological determinism", "Genetics largely determine how people behave."),
            ("environmental determinism", "Social environments largely determine how people behave."),
            ("biological determinism", "Biological factors are the main drivers of behavior."),
            ("environmental determinism", "Culture and upbringing are the main drivers of behavior."),
            ("biological determinism", "Inborn traits are the strongest influence on actions."),
            ("environmental determinism", "Situations and context shape behavior more than biology."),
            ("biological determinism", "Biology sets firm limits on how people act."),
            ("environmental determinism", "People are mostly products of their environment."),
        ],
    )

    surveys["intrapsychic.json"] = bipolar(
        "Intrapsychic",
        ("Rational-conscious", "Irrational-unconscious"),
        "IP",
        [
            ("rational-conscious", "People usually act based on conscious reasoning."),
            ("irrational-unconscious", "People are often driven by unconscious forces."),
            ("rational-conscious", "Deliberate thought guides most behavior."),
            ("irrational-unconscious", "Hidden motives frequently shape what people do."),
            ("rational-conscious", "Behavior is typically the result of conscious choice."),
            ("irrational-unconscious", "Irrational impulses often dominate behavior."),
            ("rational-conscious", "People can explain the true reasons for their actions."),
            ("irrational-unconscious", "People often act without knowing why."),
        ],
    )

    surveys["consciousness.json"] = bipolar(
        "Consciousness",
        ("Ego primacy", "Ego transcendence"),
        "CS",
        [
            ("ego primacy", "The highest form of consciousness is clear self-awareness."),
            ("ego transcendence", "The highest form of consciousness transcends the self."),
            ("ego primacy", "Peak mental states are centered on a strong sense of self."),
            ("ego transcendence", "Peak experiences involve dissolving the self."),
            ("ego primacy", "A stable ego is the basis of the best consciousness."),
            ("ego transcendence", "The best consciousness goes beyond ego boundaries."),
            ("ego primacy", "Self-focused awareness is the pinnacle of consciousness."),
            ("ego transcendence", "The most profound awareness is selfless."),
        ],
    )

    surveys["activity_direction.json"] = bipolar(
        "Activity Direction",
        ("Inward", "Outward"),
        "AD",
        [
            ("inward", "The best focus is on inner growth and self-understanding."),
            ("outward", "The best focus is on external achievement and action."),
            ("inward", "Personal development matters more than external success."),
            ("outward", "Accomplishing external goals matters more than inner reflection."),
            ("inward", "Life should emphasize inner qualities like character and insight."),
            ("outward", "Life should emphasize outward results and accomplishments."),
            ("inward", "The inner life deserves primary attention."),
            ("outward", "The external world deserves primary attention."),
        ],
    )

    surveys["activity_satisfaction.json"] = bipolar(
        "Activity Satisfaction",
        ("Movement", "Stasis"),
        "AS",
        [
            ("movement", "Satisfaction comes from continual improvement."),
            ("stasis", "Satisfaction comes from enjoying what one already has."),
            ("movement", "Progress and change are essential for fulfillment."),
            ("stasis", "Contentment is best found in stability."),
            ("movement", "A good life requires constant growth."),
            ("stasis", "A good life is about appreciating the present state."),
            ("movement", "Achievement over time is the main source of satisfaction."),
            ("stasis", "Rest and acceptance are the main source of satisfaction."),
        ],
    )

    surveys["moral_relevance.json"] = bipolar(
        "Moral Relevance",
        ("Relevant", "Irrelevant"),
        "MR",
        [
            ("relevant", "Society’s moral rules are personally binding on individuals."),
            ("irrelevant", "Society’s moral rules do not apply to my personal choices."),
            ("relevant", "People should treat social moral guidelines as relevant to their lives."),
            ("irrelevant", "Moral guidelines are optional and can be ignored."),
            ("relevant", "Moral rules matter for personal behavior."),
            ("irrelevant", "Moral rules are mostly irrelevant to individual decisions."),
            ("relevant", "Individuals should see moral standards as personally applicable."),
            ("irrelevant", "Personal choices need not be guided by moral standards."),
        ],
    )

    surveys["control_location.json"] = multi(
        "Control Location",
        ["Action", "Personality", "Luck", "Chance", "Fate", "Society", "Divinity"],
        "CL",
        [
            ("action", "My outcomes are mainly determined by my own actions."),
            ("action", "Effort and work are the biggest causes of life results."),
            ("personality", "Personal charm or style strongly shapes outcomes."),
            ("personality", "Who I am as a person largely determines what happens to me."),
            ("luck", "Luck often decides how things turn out."),
            ("luck", "Good or bad fortune plays a major role in outcomes."),
            ("chance", "Random chance is a major factor in life outcomes."),
            ("chance", "Many outcomes are simply accidental or random."),
            ("fate", "People have a destiny that shapes outcomes."),
            ("fate", "Events unfold according to fate."),
            ("society", "Social systems and structures largely determine outcomes."),
            ("society", "Institutional forces shape people’s life results."),
            ("divinity", "A divine power determines what happens in life."),
            ("divinity", "Outcomes are guided by a higher spiritual force."),
        ],
    )

    surveys["control_disposition.json"] = multi(
        "Control Disposition",
        ["Positive", "Negative", "Neutral"],
        "CD",
        [
            ("positive", "The forces that shape life outcomes are generally benevolent."),
            ("positive", "Outcomes tend to be guided in a good direction."),
            ("negative", "The forces that shape life outcomes are generally hostile."),
            ("negative", "Outcomes tend to be guided in a bad direction."),
            ("neutral", "The forces that shape life outcomes are morally neutral."),
            ("neutral", "Outcomes are shaped without any moral bias."),
        ],
    )

    surveys["action_efficacy.json"] = multi(
        "Action Efficacy",
        ["Direct", "Thaumaturgic", "Impotent"],
        "AE",
        [
            ("direct", "Direct action is the most effective way to achieve goals."),
            ("direct", "Concrete effort produces results."),
            ("thaumaturgic", "Appeals to supernatural forces can change outcomes."),
            ("thaumaturgic", "Miraculous intervention can alter what happens."),
            ("impotent", "Human action has little effect on outcomes."),
            ("impotent", "Trying often makes no real difference."),
        ],
    )

    surveys["otherness.json"] = bipolar(
        "Otherness",
        ("Tolerable", "Intolerable"),
        "OT",
        [
            ("tolerable", "Differences between people are generally acceptable."),
            ("intolerable", "Differences between people are hard to accept."),
            ("tolerable", "People unlike me are still easy to accept."),
            ("intolerable", "People unlike me are difficult to tolerate."),
            ("tolerable", "Diversity among people is fine."),
            ("intolerable", "Diversity among people is problematic."),
            ("tolerable", "I am comfortable with people who are very different."),
            ("intolerable", "I am uncomfortable with people who are very different."),
        ],
    )

    surveys["relation_to_authority.json"] = bipolar(
        "Relation to Authority",
        ("Linear", "Lateral"),
        "RA",
        [
            ("linear", "Authority should be clearly hierarchical."),
            ("lateral", "Authority should be shared and non-hierarchical."),
            ("linear", "Leaders should have clear power over subordinates."),
            ("lateral", "Leaders should be peers rather than superiors."),
            ("linear", "Society works best with strong hierarchies."),
            ("lateral", "Society works best with egalitarian authority."),
            ("linear", "People should defer to those above them."),
            ("lateral", "People should relate to authority as equals."),
        ],
    )

    surveys["relation_to_humanity.json"] = multi(
        "Relation to Humanity",
        ["Superior", "Egalitarian", "Inferior"],
        "RH",
        [
            ("superior", "Some people are inherently superior to others."),
            ("superior", "It is natural that some groups are better than others."),
            ("egalitarian", "All people are fundamentally equal."),
            ("egalitarian", "No one is inherently above anyone else."),
            ("inferior", "Some people are inherently lesser than others."),
            ("inferior", "It is natural that some groups are below others."),
        ],
    )

    surveys["relation_to_biosphere.json"] = bipolar(
        "Relation to Biosphere",
        ("Anthropocentrism", "Vivicentrism"),
        "RB",
        [
            ("anthropocentrism", "Human needs should come before those of other life."),
            ("vivicentrism", "All living beings deserve equal moral consideration."),
            ("anthropocentrism", "Nature exists primarily for human use."),
            ("vivicentrism", "Nonhuman life has value independent of humans."),
            ("anthropocentrism", "Human interests should override ecological concerns."),
            ("vivicentrism", "Protecting ecosystems is as important as human benefit."),
            ("anthropocentrism", "Human well-being should outweigh other life forms."),
            ("vivicentrism", "The biosphere should be respected for its own sake."),
        ],
    )

    surveys["sexuality.json"] = multi(
        "Sexuality",
        ["Procreation", "Pleasure", "Relationship", "Sacral"],
        "SX",
        [
            ("procreation", "The primary purpose of sex is reproduction."),
            ("procreation", "Sex should mainly be for having children."),
            ("pleasure", "Sex is primarily for pleasure."),
            ("pleasure", "Enjoyment is the main purpose of sex."),
            ("relationship", "Sex is primarily an expression of relationship and bonding."),
            ("relationship", "Sex should mainly express connection between partners."),
            ("sacral", "Sex is a sacred act with spiritual significance."),
            ("sacral", "Sex has a spiritual or holy dimension."),
        ],
    )

    surveys["connection.json"] = multi(
        "Connection",
        ["Dependent", "Independent", "Interdependent"],
        "CN",
        [
            ("dependent", "Individuals should rely heavily on others."),
            ("dependent", "People need strong dependence on others to thrive."),
            ("independent", "Individuals should be self-reliant."),
            ("independent", "People should not depend on others."),
            ("interdependent", "People should rely on each other in mutual ways."),
            ("interdependent", "Mutual dependence is healthy and normal."),
        ],
    )

    surveys["interpersonal_justice.json"] = multi(
        "Interpersonal Justice",
        ["Just", "Unjust", "Random"],
        "IJ",
        [
            ("just", "In personal relationships, people generally get what they deserve."),
            ("just", "Interpersonal outcomes are usually fair."),
            ("unjust", "In personal relationships, people are often treated unfairly."),
            ("unjust", "Interpersonal outcomes are often unjust."),
            ("random", "Interpersonal outcomes are mostly a matter of luck."),
            ("random", "Personal relationships turn out randomly."),
        ],
    )

    surveys["sociopolitical_justice.json"] = multi(
        "Sociopolitical Justice",
        ["Just", "Unjust", "Random"],
        "SJ",
        [
            ("just", "Societal systems are generally fair."),
            ("just", "Political outcomes are usually just."),
            ("unjust", "Societal systems are largely unjust."),
            ("unjust", "Political outcomes are often unfair."),
            ("random", "Sociopolitical outcomes are mostly random."),
            ("random", "Politics often turns out by chance rather than justice."),
        ],
    )

    surveys["interaction.json"] = multi(
        "Interaction",
        ["Competition", "Cooperation", "Disengagement"],
        "IN",
        [
            ("competition", "Competition is the best way to organize relations."),
            ("competition", "People should strive to outperform others."),
            ("cooperation", "Cooperation is the best way to organize relations."),
            ("cooperation", "People should work together rather than compete."),
            ("disengagement", "Avoiding interaction is often best."),
            ("disengagement", "Keeping distance from others is preferable."),
        ],
    )

    surveys["correction.json"] = multi(
        "Correction",
        ["Rehabilitation", "Retribution"],
        "CR",
        [
            ("rehabilitation", "The goal of punishment should be rehabilitation."),
            ("rehabilitation", "Wrongdoers should be reformed rather than harmed."),
            ("retribution", "The goal of punishment should be retribution."),
            ("retribution", "Wrongdoers should suffer in proportion to their acts."),
        ],
    )

    surveys["truth_scope.json"] = bipolar(
        "Truth Scope",
        ("Universal", "Relative"),
        "TS",
        [
            ("universal", "Truth is the same for everyone everywhere."),
            ("relative", "Truth depends on perspective or context."),
            ("universal", "There are universal truths that apply to all."),
            ("relative", "What is true can vary across cultures or situations."),
            ("universal", "Truth is objective and independent of observers."),
            ("relative", "Truth is shaped by human viewpoints."),
            ("universal", "Facts remain true regardless of who observes them."),
            ("relative", "Truth is relative to the observer."),
        ],
    )

    surveys["truth_possession.json"] = bipolar(
        "Truth Possession",
        ("Full", "Partial"),
        "TP",
        [
            ("full", "People can fully possess the truth."),
            ("partial", "People can only grasp part of the truth."),
            ("full", "Complete knowledge of reality is possible."),
            ("partial", "All knowledge is necessarily incomplete."),
            ("full", "Humans can know the full truth about things."),
            ("partial", "We can only know fragments of truth."),
            ("full", "It is possible to reach complete understanding."),
            ("partial", "Understanding is always partial."),
        ],
    )

    surveys["truth_availability.json"] = bipolar(
        "Truth Availability",
        ("Exclusive", "Inclusive"),
        "TA",
        [
            ("exclusive", "Only certain people have access to truth."),
            ("inclusive", "Truth is available to anyone who seeks it."),
            ("exclusive", "Truth is reserved for a select few."),
            ("inclusive", "Truth is accessible to all people."),
            ("exclusive", "Most people are not capable of knowing truth."),
            ("inclusive", "Most people can know truth."),
            ("exclusive", "Truth is available only to an elite."),
            ("inclusive", "Truth does not belong to any elite."),
        ],
    )

    surveys["cosmos.json"] = bipolar(
        "Cosmos",
        ("Random", "Planful"),
        "CO",
        [
            ("random", "The universe is ultimately random."),
            ("planful", "The universe follows an underlying plan."),
            ("random", "Events in the cosmos are mostly accidental."),
            ("planful", "There is purpose or design in the cosmos."),
            ("random", "Cosmic events have no larger pattern."),
            ("planful", "The cosmos reflects intentional order."),
            ("random", "The universe has no guiding structure."),
            ("planful", "The universe is structured by a guiding principle."),
        ],
    )

    surveys["unity.json"] = bipolar(
        "Unity",
        ("Many", "One"),
        "UN",
        [
            ("many", "Reality is made up of many distinct elements."),
            ("one", "Reality is fundamentally unified."),
            ("many", "The world consists of separate, independent parts."),
            ("one", "All things are connected in a single whole."),
            ("many", "The universe is a collection of separate entities."),
            ("one", "The universe is ultimately one interconnected system."),
            ("many", "Separation is a basic feature of reality."),
            ("one", "Unity is a basic feature of reality."),
        ],
    )

    surveys["deity.json"] = multi(
        "Deity",
        ["Deism", "Theism", "Agnosticism", "Atheism"],
        "DE",
        [
            ("deism", "A creator exists but does not intervene in the world."),
            ("deism", "A divine creator set the universe in motion but does not interfere."),
            ("theism", "A personal God actively intervenes in the world."),
            ("theism", "A deity answers prayers or interacts with humans."),
            ("agnosticism", "We cannot know whether any deity exists."),
            ("agnosticism", "The existence of a deity is unknowable."),
            ("atheism", "No deity exists."),
            ("atheism", "The universe has no God or gods."),
        ],
    )

    surveys["nature_consciousness.json"] = bipolar(
        "Nature-Consciousness",
        ("Nature conscious", "Nature nonconscious"),
        "NC",
        [
            ("nature conscious", "Nature has some form of consciousness."),
            ("nature nonconscious", "Nature has no consciousness."),
            ("nature conscious", "The natural world possesses awareness in some way."),
            ("nature nonconscious", "The natural world is entirely unconscious."),
            ("nature conscious", "Nature contains mind-like qualities."),
            ("nature nonconscious", "Nature is purely mechanical and mindless."),
            ("nature conscious", "Consciousness is present in the natural world."),
            ("nature nonconscious", "Consciousness is absent from nature."),
        ],
    )

    surveys["humanity_nature.json"] = multi(
        "Humanity–Nature",
        ["Subjugation", "Harmony", "Mastery"],
        "HN",
        [
            ("subjugation", "Humans should submit to the forces of nature."),
            ("subjugation", "Nature is stronger and humans should yield to it."),
            ("harmony", "Humans should live in balance with nature."),
            ("harmony", "The best relationship with nature is mutual harmony."),
            ("mastery", "Humans should control and shape nature to meet their needs."),
            ("mastery", "Nature should be mastered for human benefit."),
        ],
    )

    surveys["world_justice.json"] = multi(
        "World Justice",
        ["Just", "Unjust", "Random"],
        "WJ",
        [
            ("just", "The world is basically fair."),
            ("just", "People generally get what they deserve in life."),
            ("unjust", "The world is largely unfair."),
            ("unjust", "People often suffer without deserving it."),
            ("random", "The world is mostly random and unstructured."),
            ("random", "Life outcomes are mostly a matter of chance."),
        ],
    )

    surveys["well_being_source.json"] = bipolar(
        "Well-Being",
        ("Science-logic source", "Transcendent source"),
        "WB",
        [
            ("science-logic source", "Well-being comes mainly from rational understanding."),
            ("transcendent source", "Well-being comes mainly from a transcendent source."),
            ("science-logic source", "Science and reason are the best guides to well-being."),
            ("transcendent source", "Spiritual forces are the best guides to well-being."),
            ("science-logic source", "Logical insight is the primary path to well-being."),
            ("transcendent source", "Divine or spiritual connection is the primary path to well-being."),
            ("science-logic source", "Well-being is achieved through rational methods."),
            ("transcendent source", "Well-being is achieved through transcendent guidance."),
        ],
    )

    surveys["explanation.json"] = multi(
        "Explanation",
        ["Formism", "Mechanism", "Organicism", "Contextualism"],
        "EX",
        [
            ("formism", "Things are best explained by their categories or types."),
            ("formism", "Understanding kinds and forms is key to explanation."),
            ("mechanism", "Things are best explained by their component parts and causes."),
            ("mechanism", "Causal mechanisms provide the strongest explanations."),
            ("organicism", "Things are best explained as parts of living wholes."),
            ("organicism", "Systems and wholes are more explanatory than parts."),
            ("contextualism", "Things are best explained by their context and situation."),
            ("contextualism", "Understanding context is key to explanation."),
        ],
    )

    surveys["worth_of_life.json"] = bipolar(
        "Worth of Life",
        ("Optimism", "Resignation"),
        "WL",
        [
            ("optimism", "Life is generally good and worth embracing."),
            ("resignation", "Life is mostly something to endure."),
            ("optimism", "The overall value of life is positive."),
            ("resignation", "Life offers little that is truly worthwhile."),
            ("optimism", "There is more hope than despair in life."),
            ("resignation", "Hope is often misplaced in life."),
            ("optimism", "Life tends to be meaningful and worthwhile."),
            ("resignation", "Life tends to be disappointing and futile."),
        ],
    )

    surveys["purpose_of_life.json"] = multi(
        "Purpose of Life",
        [
            "Nihilism",
            "Survival",
            "Pleasure",
            "Belonging",
            "Recognition",
            "Power",
            "Achievement",
            "Self-actualization",
            "Self-transcendence",
        ],
        "PL",
        [
            ("nihilism", "Life has no inherent purpose."),
            ("nihilism", "There is no ultimate meaning to life."),
            ("survival", "The primary purpose of life is to survive."),
            ("survival", "Staying alive is the central purpose of life."),
            ("pleasure", "The purpose of life is to experience pleasure."),
            ("pleasure", "Maximizing enjoyment is life’s main aim."),
            ("belonging", "The purpose of life is to belong and connect."),
            ("belonging", "Building relationships is life’s central purpose."),
            ("recognition", "The purpose of life is to be respected and admired."),
            ("recognition", "Gaining recognition is a main aim of life."),
            ("power", "The purpose of life is to gain influence and power."),
            ("power", "Power is a central aim of life."),
            ("achievement", "The purpose of life is to accomplish goals."),
            ("achievement", "Achieving success is life’s main goal."),
            ("self-actualization", "The purpose of life is to realize one’s full potential."),
            ("self-actualization", "Developing oneself is life’s central purpose."),
            ("self-transcendence", "The purpose of life is to transcend the self."),
            ("self-transcendence", "Serving something beyond oneself is life’s central purpose."),
        ],
    )

    for filename, data in surveys.items():
        path = survey_dir / filename
        if not path.exists():
            write(path, data)


if __name__ == "__main__":
    main()
