# Adaptive epistemic-depth experiment log

**Branch:** `codex/epistemic-depth-experiment-tournament`

**Maximum:** 30 experiments

**Rule:** added complexity must create a new discrimination or improve robust
out-of-sample performance. Simplicity wins ties.

## Tranche A — formal fidelity

### Experiment 1 — Existing five-channel construction

Reproduced the committed global precision-field construction as the reference.
It instantiates the five verbal steps of the Beautiful Loop hyper-loop but
supplies realized precision evidence exogenously and has no explicit hierarchy.

**Decision:** retain as a clinical construction check, not as the formal
baseline for literature combinations.

### Experiment 2 — Explicit three-level hierarchy

Added latent states $x^{(1:3)}$, fixed observations at each level, and
layer-specific precision hyperparameters. State inference now runs inside the
same loop as precision inference.

**Result:** implementation and finite-posterior criteria passed across all test
seeds.

### Experiment 3 — Endogenous second-order errors

Replaced scripted realized precision with the expected residual variance of
the inferred lower-level states. The residual evidence updates the posterior
over layer precision, which is rebroadcast into the next state-inference pass.

**Result:** residuals were positive and finite, and the joint free-energy proxy
changed across iterative state/precision updates.

### Experiment 4 — Global versus local meta-inference

Compared a shared global hyper-node against independent local precision loops.
In a coordinated precision shift, evidence from two layers had to predict a
held-out third layer. In a second environment, layer precisions shifted in
different directions and every layer was observed.

**Result:** on the coordinated held-out test, mean error was `0.223` for the
global model versus `1.000` for local loops. On independent shifts, the local
model correctly won: RMSE `0.167` versus `0.344` for the global model.

**Interpretation:** global pooling earns its complexity only when precision
changes share real cross-layer structure. This is more compelling than a claim
that globality is always better. It supplies a falsifiable scope condition:
epistemic depth should help when context predicts coordinated changes across
levels, and should become a liability when those changes are genuinely
independent.

**Decision:** advance the hierarchical global model, while retaining the local
model as a standing adversarial control. Do not add further global machinery
unless it improves a held-out prediction.
