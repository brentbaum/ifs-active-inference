# Notes

## Ground Truth and Deviation

The reproduction follows Sandved-Smith et al. (2021) at the level of model architecture and qualitative figure dynamics:

- level 1: perceptual state inference over standard/deviant observations;
- level 2: attentional state inference over Focused/Distracted states, with these states setting level-1 likelihood precision;
- level 3: meta-awareness state setting level-2 likelihood precision;
- mental action: policy selection over level-2 transition control, implemented as `maintain` versus `refocus`.

I found the paper DOI, OUP record, and OSF preprint. I did not find an official public GitHub/code repository through web search, GitHub repository search, OSF metadata, or pymdp example listings. The OSF preprint metadata reports no data links. This is therefore a faithful compact reimplementation from the paper text, not a port of official code.

Main deviation: the paper describes active inference graphically and qualitatively but does not provide exact numeric matrices in the article text. This implementation uses explicit categorical Bayes updates and an EFE-style policy score, rather than SPM/pymdp internals.

## Reproduced Dynamics

`paper_figure_6_precision_oddball.png` reproduces the level-1 result: high likelihood precision over `A(1)` causes rapid posterior switching to the deviant state, while low precision delays or damps updating.

`paper_figure_8_attention_capture_return.png` reproduces the focused-attention cycle: a forced distractor shifts the latent attentional state, the agent initially remains confident it is focused, metacognitive evidence accumulates until it infers distraction, and the selected `refocus` mental action returns the state to Focused.

`paper_figure_10_meta_awareness_dwell.png` reproduces the meta-awareness manipulation: high `A(2)` precision produces shorter distracted dwell times than low `A(2)` precision under the same forced distractors.

## Stability Envelope

The stability sweep is written to `outputs/stability_envelope.csv`. A run is labeled stable when all forced-distraction dwell times are 1-8 steps, policy switching is not chatty, and adaptive second-order precision does not oscillate repeatedly.

Observed stable ranges in this implementation:

- Level-2 likelihood precision bounds `[0.3, 6.0]`, `[0.5, 8.0]`, `[0.8, 10.0]`, and `[0.2, 14.0]` were stable when the adaptive precision learning rate was `0.0`, `0.3`, or `0.8`.
- Adaptive second-order precision learning rates `0.0-0.8` were stable across all tested precision bounds and policy horizons. Rates `>= 1.2` produced repeated alternating overshoot in this discrete update when the precision estimate started away from its level-3 target.
- Policy horizons `1`, `3`, `5`, `8`, and `12` were all stable when precision learning was stable. In this implementation, horizon is not the primary oscillation risk; learning-rate overshoot is.
- Practical safe setting for T2.1: keep `A(2)` effective precision in `[0.5, 8.0]`, precision learning rate `<= 0.8` (`<= 0.3` if changing targets online), and mental-policy horizon `<= 5` for interpretability even though longer tested horizons did not destabilize the baseline.

## Where Second-Order Precision Oscillates or Diverges

The implemented adaptive precision update is a bounded first-order update toward the level-3 target:

`gamma_l2[t+1] = clip(gamma_l2[t] + lr * (target - gamma_l2[t]), gamma_min, gamma_max)`.

For `lr > 1` from the tested initialization, the discrete update overshoots the target and alternates sign. With clipping, this does not numerically diverge to infinity, but it produces repeated precision chatter when the precision interval is wide. This is the second-order precision oscillation risk that T0.4 was meant to retire before downstream work.

Unbounded variants of this update would diverge for sufficiently high learning rates; the code keeps bounds explicit so the failure mode is observable as oscillation/chatter rather than a floating-point blow-up.
