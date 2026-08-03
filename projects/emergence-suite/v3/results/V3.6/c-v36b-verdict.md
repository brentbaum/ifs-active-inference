# C-V36B sealed challenge verdict

Immutable sealed verdict: **PASS**.

## Criterion results

1. **PASS** — `q_partner_reliable` mean full-minus-ablation 0.753586424642; 95% CI [0.731508758732, 0.774515301014]; frozen floor 0.370549355302; 700 pairs.
2. **PASS** — `q_partner_reliable` mean full-minus-ablation 0.995446734001; 95% CI [0.994603114944, 0.996232060116]; frozen floor 0.497078097576; 700 pairs.
3. **PASS** — `q_policy_open` mean full-minus-ablation 0.0688216250476; 95% CI [0.0670305857515, 0.0705014002396]; frozen floor 0.0341294783274; 600 pairs.

4. **PASS** — opposed and allied fingerprints were evaluated separately:

   - `opposed_D_0_1`: mean 0.0105828081561; 95% CI [0.00885856809887, 0.0122509432196].
   - `opposed_D_1_0`: mean 0.0104817397822; 95% CI [0.00872268487485, 0.0121457494739].
   - `allied_D_0_1`: mean 0.0188766300417; 95% CI [0.0172387118748, 0.0204481149016].
   - `allied_D_1_0`: mean 0.018864197878; 95% CI [0.0172003677559, 0.0204742255839].

5. **PASS** — 3,000 unique seeds were consumed once, ascending and gap-free; raw rows and event-ledger hashes were fsynced before aggregation. Escrow 4113000:4119999 is retired unconsumed.

## Verdict classes

- Scientific: **PASS**
- Custody: **PASS**

## Interpretation

The immutable result above is retained as written. The cells separately test partner reliability, noncontingent soothing, protection-respecting policy access, and the opposed/allied interventional topology fingerprints.

Raw trace SHA-256: `85ad4271f3e1f299ebae08103b5ac14c652568f07cdfc0d598829cf1db4d1ded`.  
Event-hash ledger SHA-256: `3252159a291aaef785534a5d61d629290e4dff79598c296f5f74fec7b4cda86c`.
