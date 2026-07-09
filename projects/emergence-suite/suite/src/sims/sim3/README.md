# Sim 3 Redesign Notes

This module implements T1.1, Sim 3: the generalization gradient.

## H2 Architecture

H1 keeps the original root direction: relational evidence updates the shared self-state bank, and cue-local threat inference conditions on that self-state through `self_to_threat_coupling * cue.root_coupling`.

H2 is the reversed-root control. Threat is the root: the treated cue's threat meaning is learned from cue/outcome evidence directly, and policy reads threat meaning without reading self-state. The self-state bank still learns in H2. Relational evidence is always on and truthful, and H2 additionally updates self-state downstream from inferred threat through `h2_threat_to_self_coupling`. Because neither threat inference nor policy conditions on self-state in H2, self-state revision is inert for transfer by architecture rather than by a disabled learning flag.

## Cue Design

Each cue has two independent attributes:

| cue | perceptual_similarity | root_coupling | root_id | role |
|---|---:|---:|---:|---|
| `cue_1` | 1.00 | 1.00 | 1 | trained cue |
| `cue_2` | 0.35 | 0.80 | 1 | root-sharing continuum |
| `cue_3` | 0.20 | 0.60 | 1 | structural A3.2 contrast |
| `cue_4` | 0.70 | 0.40 | 1 | decorrelation cue |
| `cue_5` | 0.45 | 0.20 | 1 | root-sharing continuum |
| `structural_confound` | 0.90 | 0.00 | 2 | perceptually near, root-distant A3.2 confound |

There is no separate perceptual stimulus-generalization channel in this run. Perceptual similarity is logged and used for the A3.2 design contrast, but it does not drive threat transfer. Exposure generalization is therefore expected to be cue-bound unless directly learned through the trained cue's local threat bank.

## Criteria Amendments

Thresholds in `configs/sim3-criteria.yaml` are unchanged.

- `S3.transfer.h1_witnessing_gradient`: the metric still reports `metrics.transfer.h1_witnessing_monotone_gradient`, but the continuum is now sorted over `root_coupling`, not perceptual similarity. Reason: T1.1's transfer claim concerns structural similarity through the root.
- `S3.transfer.exposure_flat` and `S3.transfer.h2_flat`: continuum slopes are now computed against `root_coupling`, not perceptual similarity. Reason: the flatness controls should test absence of structural transfer, not absence of feature-overlap effects.
- `A3.2.structural_confound`: the contrast now compares the perceptually distant, root-sharing structural cue (`cue_3`, perceptual similarity 0.20, root coupling 0.60) against the perceptually near, root-distant confound. Reason: the previous metric used the lowest-similarity continuum endpoint and conflated perceptual and root distance.
