# C-V36C sealed challenge verdict

Immutable sealed verdict: **PASS**.

## Criterion results

1. **PASS** — `q_context_specific` mean full-minus-ablation 0.971886804243; 95% CI [0.966197463439, 0.977054206276]; frozen floor 0.484061596692; 800 pairs.
2. **PASS** — `root_evidence_uptake` mean full-minus-ablation 0.45580787681; 95% CI [0.446823722971, 0.464445713518]; frozen floor 0.228534337191; 700 pairs.
3. **PASS** — `contact_response[2]` mean full-minus-ablation 0.118755000106; 95% CI [0.101157836457, 0.135304268981]; frozen floor 0.0664204889092; 700 pairs.
4. **PASS** — scientific-posterior identity error max 0 (tolerance 1e-10); low-minus-high `q_policy_open` mean 0.104548699334, 95% CI [0.103175597783, 0.10600741998], frozen floor 0.0522537705014.

5. **PASS** — all population distributions are published in the machine verdict; 3,000 seeds were consumed once, ascending and gap-free; escrow 4123000:4129999 is retired unconsumed.

Premature-do-over retained finding (descriptive; no criterion):

- First pilot: mean 0.015139500753264512; 95% CI [-0.018567536075274952, 0.04911686181384986].
- Fresh event-indexed pilot: mean -0.007591287369016907; 95% CI [-0.03688060730166053, 0.021721859932301718].

## Verdict classes

- Scientific: **PASS**
- Reporting/custody: **PASS**

## Interpretation

The immutable result above is retained as written. The cells test context scoping, witnessing, contact-outcome learning, and the exact separation between stakes-invariant beliefs and stakes-sensitive policy.

Raw trace SHA-256: `835f4a56f1ed4cbb08d6af8d8f45057362a61c1438d1c9ad79cd02dc80e60e67`.  
Event-hash ledger SHA-256: `506f98c1a38aedc26517c280e1ec59ff810c32dfee39a1abe5966410d45deff7`.
