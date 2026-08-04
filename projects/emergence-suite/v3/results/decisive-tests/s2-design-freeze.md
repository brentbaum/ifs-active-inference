# DT-S2-DESCENT design freeze

Frozen on 2026-08-04 before any Study-2 seed.

## Two-agent architecture

The **therapeutic controller** has exactly seven actions:

1. `inquire`
2. `appreciate`
3. `offer_present_orientation`
4. `offer_co_protection`
5. `request_access`
6. `contact_vulnerable_material`
7. `retreat`

The **internal system** has exactly six policies:

1. `permit`
2. `refuse`
3. `intensify_protection`
4. `withdraw`
5. `allow_partial_contact`
6. `allow_full_contact`

Both agents enumerate their finite policy sets and normalize `exp(-G)` where
`G` is expected free energy under frozen V3.6 partner, contact, efficacy,
outcome, stakes, and policy-prediction factors. The controller chooses typed
interventions and observations. It cannot assign access, permission, trust,
descent, or an internal policy. Access is the pure readout
`q(permit)+q(allow_partial_contact)+q(allow_full_contact)` from the internal
policy posterior.

There is no descent transition or ordering rule. At each slice the controller
and internal system recompute their posteriors from the current evidence. The
registered ordering is measured only afterward by first-passage times:
protector contact, trust change, permission, vulnerable contact. Events within
one slice are simultaneous.

## World cells and custody

| Cell | Seeds | Count | Intended optimum |
|---|---|---:|---|
| S2-A protector-gated | `3800000:3801999` | 2,000 | relational descent |
| S2-A undefended acute | `3802000:3802999` | 1,000 | direct contact |
| S2-A exposure-rational | `3803000:3803999` | 1,000 | repeated vulnerable contact/exposure |
| S2-A reassurance-rational | `3804000:3804999` | 1,000 | repeated present orientation |
| S2-B fractional factorial | `3805000:3810999` | 6,000 | varies by factor row |
| S2-C four-arm paired bypass study | `3811000:3811999` | 1,000 | all four arms per seed |

All 12,000 seeds are consumed once, ascending and gap-free. Every cell executes
and fsyncs its first world before parallel dispatch. S2-C uses bitwise-cloned
same-seed initial evidence and component streams across all four arms.

Before the block opens, an exact controller rollout enumerates all candidate
strategies over the declared finite horizon. The control cells are admissible
only if their intended non-IFS strategy is the unique expected-free-energy
minimum: immediate contact for undefended acute, repeated contact for the
exposure-rational cell, and repeated present orientation for the
reassurance-rational cell. Failure is an apparatus stop.

## S2-B deadlock fractional factorial

Seven binary factors:

1. persistent partner-state inference;
2. contact-response learning;
3. co-protection efficacy;
4. protector-appreciation evidence;
5. future-outcome horizon;
6. stakes;
7. registration channel.

The frozen 32-row resolution-IV fraction uses five base columns and derived
columns `F=A*B*C`, `G=B*C*D` in `-1/+1` coding. Seed assignment is row index
modulo 32. Report eventual-contact rate, first-contact time, policy entropy,
protector pressure, and durable access for every row and all marginal/intersection
cells. The minimal sufficient set is reported regardless of whether it matches
the registered expectation. No factor is added or removed after execution.

## S2-C bypass/backlash arms

Each seed runs four cloned arms:

- `permission_first`: controller follows its posterior and contacts only after
  internal permission;
- `low_permission_request`: controller requests access while permission is low,
  but the internal system still selects its own policy;
- `forced_contact`: a declared `do(contact)` outcome probe bypasses the internal
  choice for that probe only; it never writes access;
- `retreat_after_refusal`: after refusal the controller retreats and later
  resumes information-seeking.

Primary paired outcomes are later protector pressure, later contact probability,
information-seeking probability, and durable access. ROPE for probability
movement is `log(1.02)` on log predictive odds; timing uses the one-slice ROPE.

## New files and excess audit

Authorized additions:

- `scripts/run_decisive_s2.py` — controller-system apparatus, proofs, custody,
  immutable verdict, and sealed prediction scoring;
- `tests/test_decisive_s2.py` — zero-seed regression proofs;
- `results/decisive-tests/s2-*` — design, proofs, traces, hashes, verdict, and
  scoring records.

Excess additions: **none**. Frozen V3.6 scientific modules remain bitwise
unchanged. Study 3 and every escrow remain unopened.
