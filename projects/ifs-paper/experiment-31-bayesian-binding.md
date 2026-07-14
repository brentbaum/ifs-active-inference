# Experiment 31 — precision-weighted Bayesian binding

**Date:** 2026-07-14

## Question

Can one global cause bind several locally competing explanations when evidence
is individually ambiguous, and can the precision field prevent a salient but
unreliable channel from capturing the reality model?

## Construction

The model exactly enumerates one binary global cause and three binary local
causes. Each local cause generates one Gaussian channel. A coherence prior
links local causes to the global cause, while the predicted precision field
controls both the sensory likelihood and how strongly each channel is required
to bind. The ablation infers each channel separately and takes a majority vote.

Three trial types test clear coherent evidence, individually ambiguous but
jointly coherent evidence, and a salient distractor opposed by distributed
evidence in the other channels. A precision-inversion control makes the
distractor appear reliable and the corrective channels unreliable.

## Iteration record

1. The initial fixed-coherence model produced only a `0.013` overall advantage
   and rejected the distractor in `69.7%` of trials.
2. Raising coherence increased posterior confidence but not correctness.
3. The distractor benchmark was repaired so correct evidence was distributed
   across individually uncertain channels; this established the ambiguous
   coherence effect but still rejected the distractor only `68.1%` of the time.
4. The successful model made the binding prior precision-sensitive. A
   low-precision channel can remain locally discrepant rather than forcing its
   content into the global cause.

The fourth change is the substantive result: precision controls not only the
gain of local evidence but its participation in global coherence.

## Results

| Measure | Bound model | Local / inverted control |
|---|---:|---:|
| Overall cause accuracy | 0.888 | 0.822 local |
| Ambiguous coherent accuracy | 0.863 | 0.830 local |
| Ambiguous confidence | 0.631 | 0.472 local |
| Salient-distractor accuracy | 0.814 | 0.288 inverted |

The bound model beat local decisions overall in 20/20 seeds and on ambiguous
trials in 19/20. Calibrated precision beat inverted precision in 20/20.

## Boundary

The cause space is binary, coherence is an authored prior, and the model binds
three channels rather than discovering a representational hierarchy. It is a
minimal demonstration of precision-weighted competition for a global
posterior, not a full reality model or evidence of phenomenal binding.
