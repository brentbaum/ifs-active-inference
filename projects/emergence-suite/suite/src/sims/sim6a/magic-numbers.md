# Sim 6a Magic Numbers

| Constant | Value | Status | Rationale |
| --- | ---: | --- | --- |
| Depth grid | `[0.0, 0.25, 0.50, 0.75, 1.0]` | preregistered design | Five discrete states satisfy the ticket's 4-6 state request while keeping the D1 finite-difference slope readable. |
| Initial depth prior | `[0.03, 0.05, 0.10, 0.27, 0.55]` | design prior | Starts the biography in a high-depth safety regime without making the posterior degenerate. |
| Safety depth prior | `[0.02, 0.04, 0.09, 0.25, 0.60]` | design prior | Encodes recovery pressure under repeated low-volatility observations. It is used only in the transition prediction, not as an `E_t` assignment. |
| Transition mix | `0.06` | stability setting | Slow categorical filtering memory. Re-verified with zero oscillating seeds; differs from the bounded-relaxation precision update in the Sandved-Smith notes. |
| `pi_part` | `4.0` | D1 scale | Keeps bundle-stream effective precision inside the inherited `[0.5, 8.0]` stability envelope. |
| `lambda_ctx` | `0.90` | D1 scale | Keeps context-stream effective precision inside the inherited `[0.5, 8.0]` stability envelope. |
| `beta` | `1.00` | D1 slope | Finite-difference slope for the depth-to-log bundle-precision map. |
| `gamma` | `1.15` | D1 slope | Finite-difference slope for the depth-to-log context-precision map. |
| Threat cue activation | `1.35` | cue process | Raises the bundle stream on threat cue trials while preserving the same D1 log-precision message form. |
| Safe cue activation | `1.00` | cue process | Neutral cue gain for safety trials. |
| Context threat probability | `0.14` | imported-bundle contrast | Gives threat cues evidence for the imported Sim 1 bundle over the present context. |
| `o_self` reliability | `[0.52, 0.58, 0.68, 0.83, 0.94]` | reflexive likelihood | Low depth is nearly flat; high depth makes self-observation sharp. |
| Transparent sharpness threshold | `0.22` | preregistered readout | Below this, the self-observation posterior is close enough to flat to count as transparent. |
| Opacified sharpness threshold | `0.62` | preregistered readout | Above this, the same active bundle is registered sharply enough to count as opacified. |
| Bundle-active threshold | `0.60` | preregistered readout | Minimum level-1 bundle posterior for transparency/opacity regime counts. |
| Volatility likelihood | See `volatility_likelihood` | mechanistic table | Low-volatility observations favor high depth; burst observations are broad over lower depth states, producing inference-face collapse through Bayesian updating. |
| Arousal bins | `<0.18`, `<0.36`, `<0.56`, `<0.76`, otherwise | preregistered probe scale | Converts realized precision-weighted prediction error into the volatility observation stream. |
| Dose levels | `[0.12, 0.32, 0.52, 0.72, 0.92]` | preregistered probe scale | Five arousal evidence levels, exceeding the ticket's requirement of at least four. |
| Collapse threshold | `0.35` | preregistered criterion | Strongest burst must lower posterior precision by at least 35% of baseline. |
| Recovery threshold | `0.80` | preregistered criterion | Safety recovery must reach at least 80% of baseline within the registered window. |
| Recovery window | `18` trials | preregistered criterion | Covers the safety-recovery phase immediately after dark avoidance. |
| Identifiability threshold | `r >= 0.80` | preregistered criterion | Appendix A.6.2 recovery target. |
| Broken-collinearity curvature | `0.85` | D1 probe | Deliberately violates affine collinearity enough to make the one-scalar approximation error visible. |
| Oscillation threshold | `4` sign alternations over `0.04` | stability probe | Flags repeated second-order depth chatter while ignoring small numerical wiggles. |
| Stage-2 threat belief grid | `[0.05, 0.15, 0.30, 0.45, 0.60, 0.75, 0.90]` | preregistered policy probe | Evaluates policy EFE from low to acute threat belief without reading trial labels, schedule position, or arousal. |
| Acute threat belief | `0.90` | preregistered S2s.1 probe | Fixed belief point for the collapse-selected ranking. It is a belief input to EFE, not a schedule label. |
| Activation threat belief | `0.65` | preregistered S2s.2 probe | Fixed activation point for the witnessing-policy comparison before and after safe evidence. |
| Witnessing evidence grid | `[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36]` | preregistered course | Safe/co-regulated evidence updates only the agent's belief about reflexive-allocation outcome contingencies. |
| Aversive cost | `10.0` | survival preference | Fixed preference cost for aversive outcomes in EFE. |
| Aversive cost sweep | `[8.0, 10.0, 12.0]` | S2s.1 robustness | Three preregistered preference settings for the acute-threat ranking robustness check. |
| Epistemic value weight | `1.9` | policy preference | Weights uncertainty reduction from holding the reflexive/depth evidence channels. |
| Ambiguity weight | `0.25` | policy preference | Keeps channel ambiguity visible in the EFE decomposition while leaving S2s.1 attributable to pragmatic value if supported. |
| Reflexive safety prior | `alpha=1.0`, `beta=9.0` | witnessing prior | Before co-regulated evidence, reflexive allocation is believed unlikely to prevent aversive outcomes under activation. |
| Threat control base/gain | `0.15`, `0.50` | policy outcome model | Converts first-order threat-channel precision into predicted aversive-outcome control by a bounded ratio, not a logistic map. |
| Reflexive control gain | `0.55` | policy outcome model | Converts learned reflexive-safety evidence and self-channel precision into predicted aversive-outcome control. |
| Control saturation | `1.5` | policy outcome model | Bounded-ratio denominator for predicted control, chosen so low evidence favors threat allocation and accumulated safe evidence can flip the policy. |
| Threat-allocation precisions | threat `2.40`, self `0.35`, depth `1.00` | mental action | Boosts first-order threat-channel precision and starves the `o_self` channel while preserving Stage-1 volatility updating. |
| Reflexive-allocation precisions | threat `0.85`, self `1.55`, depth `1.25` | mental action | Holds/boosts `o_self` and depth-evidence precision while reducing first-order threat-channel priority. |
