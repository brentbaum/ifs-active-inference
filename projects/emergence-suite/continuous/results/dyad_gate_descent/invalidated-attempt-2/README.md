# Invalidated Experiment 49 attempt 2

This directory preserves the second pilot, freeze, and confirmation exactly as
generated on 2026-07-24. Those results are **not Experiment 49 evidence**.

The second implementation correctly separated dyad learning from protector
evidence signs, activated all three trust routes, and used Experiment 48's
registration channel. However, its thin Sim 5 adapter still omitted the
arousal-driven volatility likelihood and used the transition floor `0.08`
directly instead of Sim 5's realized
`max(transition_mix, expected_depth(baseline_prior)^2) = 0.2304`.
Because those differences can alter the depth posterior, relational field, and
packet timing, the confirmation was invalidated before completion was claimed.

Its pilot seeds `24901:24910` and confirmation seeds `24951:24970` are exposed
and excluded from the final experiment.
