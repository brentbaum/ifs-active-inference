# Experiment 32 — epistemic agency by expected free energy

**Date:** 2026-07-14

## Question

Can an agent use learned precision beliefs to choose where to sample, detect
that its preferred channel has become unreliable, and redirect epistemic action
without being told which channel changed?

## Construction

Each episode has one hidden binary cause and three possible evidence channels.
The agent maintains Beta beliefs about channel reliability. A policy minimizes
expected posterior entropy plus sampling cost, with a small epistemic bonus for
learning uncertain reliability parameters. Sequential samples update one bound
posterior over the cause.

After one hundred episodes, channel one changes from most to least useful while
channel three becomes most useful. The switch is hidden. Second-order surprise
about observed reliability reduces confidence in the old precision profile,
allowing exploratory policies to become competitive. Controls select a random
channel or retain a fixed channel-one preference.

## Iteration record

The first run was invalid as a comparison: uninformative reliability priors
made sampling and stopping equal, so random and fixed controls took no samples,
while the parameter-epistemic bonus forced the EFE agent to sample almost every
channel. The criteria were not evaluated downward.

The successful revision required one initial observation from every strategy
and reduced the parameter-learning bonus from `0.30` to `0.08`. A sensitivity
sweep showed that lower sampling costs could induce multi-channel sampling only
by making the EFE agent less efficient than random. The retained construction
therefore tests precision-guided selection primarily as choosing the best
channel, while the binding operation itself remains established separately in
experiment 31.

A final review removed an incorrect shortcut that treated a below-chance
channel as reliable without inverting its cue. After that correction, the
160-episode construction became seed-sensitive. Extending the two unannounced
regimes to 100 episodes each restored stable learning without changing any
criterion or inference rule.

## Results

| Measure | EFE | Random | Fixed |
|---|---:|---:|---:|
| Accuracy after switch | 0.822 | 0.749 | 0.558 |
| Mean samples per episode | 1.000 | 1.128 | 1.000 |

Late post-switch EFE accuracy reached `0.887`, up from `0.692` during the first
twenty switched episodes. Its first action shifted from channel one in `0.750`
of pre-switch episodes to channel three in `0.937` of late episodes. Late
estimated reliability was `0.817` for channel three and `0.508` for channel
one. The EFE agent beat fixed sampling in 20/20 seeds and random sampling in
16/20, while using no more samples than random in 20/20.

## Boundary

The policy chooses among three authored sensors, receives the true cause after
each episode for reliability learning, and usually takes one observation. It
demonstrates adaptive allocation of epistemic sampling, not planning over long
policies or the emergence of agency from the full Beautiful Loop architecture.
