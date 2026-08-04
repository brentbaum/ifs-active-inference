# DT-S1-IDGEN code audit

Date: 2026-08-04. Scope: frozen V3.6 scientific source, zero seeds.

## Six audit questions

1. **What random variable is identity?** The therapy-facing identity variable is
   the binary root state `G` (`root_state in (0, 1)`). It is represented by
   `q_root` and exposed in the scientific-state store as latent posterior `G`.
   See `ref/v34.py:127-146`, `ref/v34.py:443-462`, and
   `ref/v34.py:599-604`. V3.1 separately reports an identity-*organization*
   structural readout over `M1_G`, `G_W`, `G_A`, and `G_Y`; it is not a second
   mutable identity state (`ref/v31.py:427-465`).

2. **Is its posterior computed by ordinary likelihood and marginalization?**
   Yes. Root evidence enters the ordinary observation likelihood through
   `root_probability` (`ref/v34.py:288-343`). The scorer enumerates every
   structure and both root states, adds the root prior and likelihood, normalizes
   the joint weights, and marginalizes those weights to obtain `q_root`
   (`ref/v34.py:431-497`).

3. **Does any protocol directly assign or increment it?** No. Protocol
   declarations only determine whether typed root evidence is present and
   whether broadcast is enabled (`ref/v36.py:179-192`). `run_therapy` generates
   a world and calls the unchanged scorer (`ref/v36.py:346-353`). No protocol
   writes `q_root`, `root_movement`, or an identity winner. Generated root tokens
   are sampled through the same public root likelihood used by the scorer
   (`ref/v34.py:671-696`).

4. **Does root-evidence uptake flow through the same graph used outside
   therapy?** Yes. `observation_likelihood` and `_forward_backward` are the sole
   route for both generated recovery worlds and composed therapy worlds
   (`ref/v34.py:302-411`, `ref/v34.py:630-696`). Partner-state-dependent local
   precision sharpens that same root likelihood (`ref/v34.py:282-299`); the
   protocol does not introduce a therapy-only update equation.

5. **Are downstream effects recalculated from that posterior or written
   separately?** Mixed. `root_movement` is a pure calculation from `q_root`
   (`ref/v34.py:577-590`) and V3.6 reads it without mutation
   (`ref/v36.py:381-386`). However, the reported transfer field is separately
   authored as `0.7 * movement` (`ref/v34.py:590`) rather than obtained by
   posterior prediction through a downstream identity-conditioned factor.

6. **Is transfer via shared parent structure or an explicit transfer
   function?** Explicit transfer function. The decisive line is
   `transfer=float(0.7 * movement)` (`ref/v34.py:590`). Two other public
   transfer readouts likewise multiply posterior summaries explicitly:
   `ref/v31.py:468-483` and `ref/v32.py:787-800`. These are pure readouts and do
   not violate the one-posterior rule, but they do not establish shared-parent
   mediation.

## Standing

**Standing 2 — therapy evidence updates identity by ordinary inference, but
transfer is authored.**

The strongest ledger upgrade is not licensed. S1-A and S1-D test the ordinary
identity posterior directly. S1-B and S1-C still run, but their transfer results
are labeled **architecture-conditional** as required by the sealed prediction.

Frozen V3.6 scientific modules were not modified.
