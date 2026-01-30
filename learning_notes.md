# Learning Notes: Active Inference Fundamentals

> Working through the mechanics of active inference. These are Q&A notes from reviewing the papers.

---

## How does precision connect to reaching outcomes?

**My confusion:** When we talk about "sensory precision" for confirming we reached an outcome — as we get closer to the outcome's state, do we increase weight on signs we might NOT be in that state so they surprise us more?

**Answer:** Not quite. Precision isn't specifically on "signs we're not there." It's **turning up the gain on the whole sensory channel** — which amplifies whatever mismatch exists.

### Concrete example: reaching for a coffee cup

**Setup:** You predict "At time T, I'll feel contact."

**High precision on tactile channel means:** "I'm listening carefully to touch signals right now."

| Actual sensation | Prediction error | With HIGH precision |
|------------------|------------------|---------------------|
| Feel contact at T | Small (expected) | Small update — "yep, got it" |
| NO contact at T | Large (unexpected) | **Large** update — "wait, I missed!" |

With **LOW precision** on that same channel, the "I missed" signal would be muted. Less sensitive to failure.

### The volume knob analogy

- **Low precision** = volume turned down, hard to hear if the signal says "hit" or "miss"
- **High precision** = volume turned up, you'll clearly hear whichever it is

### Why increase precision when approaching a goal?

Because you need to know whether you succeeded. High precision on goal-relevant observations means you're *paying attention* to the signals that would tell you either way. You become more sensitive to **both** confirmation AND disconfirmation.

---

## Core formula (don't forget)

```
weighted update = prediction error × precision
```

Precision modulates the **error signal**, not the outcome probabilities directly. You're tuning the sensitivity of your surprise-detectors.

---
