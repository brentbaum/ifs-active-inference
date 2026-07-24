# Magic numbers — Experiment 44b

| Constant | Value | Rationale |
|---|---:|---|
| `pilot seeds` | `174701:174710` | Calibration-only worlds. |
| `confirm seeds` | `174801:174820` | Never-opened confirmation worlds. |
| `calibration 01` | `18, 0.55, 0.90, 0.45, 0.90` | Preregistered sessions, root amplitude/SD, and contact amplitude/SD; failed pilot guard. |
| `calibration 02` | `14, 0.35, 1.00, 0.30, 1.00` | First preregistered calibration passing the pilot guard. |
| `calibration 03` | `12, 0.30, 1.05, 0.25, 1.05` | Preregistered fallback evaluated only during runner debugging after calibration 02 passed; ineligible for selection. |
| `root sessions` | `14` | First pilot calibration with a passing dynamic-range guard. |
| `root amplitude` | `0.35` | Weakens each bundle likelihood ratio without changing its sign. |
| `root observation SD` | `1.0` | Keeps weak arms away from the ceiling. |
| `contact amplitude` | `0.3` | Makes contact informative but not individually decisive. |
| `contact SD` | `1.0` | Matches the calibrated root evidence scale. |
| `evidence scale` | `1.0` | Common likelihood multiplier; never arm-specific. |
| `safe prior mass` | `8.0` | Reduced-model prior favoring a non-catastrophic present ending. |
| `full prior mass` | `1.0` | Uniform full-model ending prior. |
| `reduced prior penalty` | `1.2` | Prevents reduction before sufficient present evidence. |
| `saturation upper` | `0.9` | Pilot-frozen guard for regulation and negative controls. |
| `witnessing band` | `0.65:0.995` | Requires revision to be visible but not pinned. |
| `dynamic range minimum` | `0.2` | Manipulation check, not criterion 3. |
| `baseline reachable rate` | `0.8` | Makes time-to-reduction measurable before testing shortening. |
| `criterion pair tolerance` | `0.12` | Unchanged from 44a freeze. |
| `criterion high-low gap` | `0.3` | Unchanged from 44a freeze. |
| `criterion heldout margin` | `0.05` | Unchanged §3.6 threshold. |
| `criterion do-over shortening` | `0.2` | Unchanged §3.6 threshold. |
| `criterion success rate` | `0.8` | Unchanged 16/20 threshold. |
| `imaginal outcome probabilities` | `0.15 + 0.70*q(g+)` | Posterior predictive probability under the reduced model. |
| `full imaginal probability` | `0.5` | Root-independent full-model prediction. |
| `bundle pattern` | `1.00, 0.82, 0.65, 0.92` | Experiment-43 four-element corrective bundle shape. |
| `contact breadth` | `geometric mean of four field values` | Contact reaches the root only through a broad context-held field. |
| `reversed graph LLR` | `0.0` | Cue-local parents make observation likelihood identical under both roots. |
| `root prior positive` | `0.06` | Inherited unchanged from 44a. |
| `revision begun/crossing` | `0.62 / 0.80` | Inherited unchanged from 44a. |
| `reduction threshold` | `0.35` | Inherited unchanged from 44a. |
| `imaginal packets/weight` | `4 / 0.72` | Inherited unchanged from 44a. |
| `reduced catastrophe prior` | `1.0` | Completes the asymmetric Beta(8,1) reduced prior. |
| `premature session` | `1` | Fixed pre-revision application point. |
| `root RNG offset` | `700000` | Independent 44b root stream. |
| `do-over RNG offset` | `800000` | Independent 44b ending stream. |
| `catastrophe jitter` | `0.03` | Fractional outcome noise shared across do-over arms. |
| `breadth numerical guard` | `1e-12` | Prevents log zero and has no scientific role. |
