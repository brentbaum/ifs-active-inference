# Experiment 49: dyad-gate coupling and derived descent

## Design

The construction stacks the unmodified Experiment 47 protector over the unmodified Experiment 48 `VulnerableBundle`. A small adapter stores an identity-root log odds beside that bundle because Experiment 48 exposes a relational prior and registration channel but no root posterior. The adapter uses the bundle's committed 2×16 conditional table: each permitted witnessing observation contributes `0.38 × log p(bundle|g=+1)/p(bundle|g=-1)`. Root revision therefore proceeds by Bayesian inference; no repeated-contact assignment or arm-specific root update appears.

A dyad scaffold begins with Beta(`2.0`, `2.0`) precision uncertainty and learns from the same pre-generated co-regulation outcomes in coupled and decoupled arms. Posterior mean precision accumulates; each full precision unit makes one observation available as `TrustEvidence`. An admitted packet updates tolerated outcome, shared competence, and partner policy, so all three Experiment 47 routes remain active. The no-dyad arm has no scaffold; the decoupled arm learns the same scaffold but its packets do not enter the protector.

Permission is the protector's own risk-model decision under the obsolete future, where inferred co-protection determines the risk of protector absence. Contact is permitted exactly when that probability reaches `0.5`. The gate is not stored separately.

### Wiring note: no access by fiat

`run_gate_arm` has no access-rule argument. It constructs an Experiment 47 protector, calls `ingest_evidence!` only through the coupled dyad edge, computes `risk_model_permission(..., future=:obsolete)`, and defines contact as the resulting probability crossing the frozen threshold. Only then does `update_root_from_witnessing!` read one matched bundle observation. The coupled, no-dyad, and decoupled paths contain no branch that grants access from an arm label. The historical authored-access comparator is isolated in `run_authored_calibration`; it bypasses the gate by definition, is reported as a calibration benchmark, and is excluded from every inferential success criterion.

### Register guards

*Configural* refers only to organization within the four-element bundle. *Relational* refers to the interpersonal partner route. Permitted contact with the vulnerable bundle is *witnessing*; protector engagement is *befriending*. *Organization* means the bundle, couplings, precisions, and field profile. *Carrier* means independently parameterized substrate; the learned dyad precision is not renamed a carrier.

### Design decisions

- The spec requires an authored-access baseline while also saying no arm may require authored access. These conflict literally. The comparator is therefore an isolated calibration benchmark, not one of the three inferential gate arms and not evidence for any criterion. Criterion 3 is evaluated over coupled, no-dyad, and decoupled worlds.
- Experiment 48 has no identity-root state or witnessing update. The thin adapter is necessary for §8.3 and uses its committed conditional table rather than modifying `ExilingEmergence.jl` or inventing an endpoint assignment.
- The risk-model obsolete future was chosen because Experiment 47's post-freeze audit showed that co-protection posterior risk, unlike policy addition, supports the intended differential.
- One seed is one matched world. Protector jitter, dyad outcomes, and the complete witnessing stream are shared across arms. The coupled/decoupled contrast changes only whether precision-weighted packets reach `TrustEvidence`.
- A posterior-precision accumulator operationalizes “precision scaffolding feeds the evidence stream” without a fitted evidence-admission cutoff. One full unit emits one packet.
- `0.5` operationalizes permission rising; `0.62` operationalizes revision beginning. Both were declared before the pilot. Within-episode event phase establishes strict ordering even when integer episode labels tie.
- Contact is measured separately from descent. A world may contact the bundle yet fail to accumulate enough likelihood evidence for root revision; such a failure is retained.
- The single moderate calibration was run once. The design contains no rescue sweep or post-pilot strength escalation.

### Structural audit

Seed blocks disjoint = `true`; Experiment 48 bundle reused = `true`; Experiment 47 `TrustEvidence` reused = `true`; all protector evidence routes active = `true`; gate equals permission threshold = `true`; coupled/decoupled dyad marginals matched = `true`; decoupled ingests no evidence = `true`; no-dyad emits no scaffold packets = `true`; closed gate has no root update = `true`; authored comparator isolated = `true`.

## Pilot

Ten worlds per arm (`14901:14910`) ran once before freeze.

- **Coupled:** contact `10/10`; descent `10/10`; ordered descent `10/10`; mean initial/final permission `0.100087` / `0.907308`; mean final root `0.983411`; permission rise min/median/max `2`/`2.0`/`2`; revision begin `3`/`3.5`/`5`; lag `1`/`1.5`/`3` episodes.
- **No dyad:** contact `0/10`; descent `0/10`; ordered descent `0/10`; mean initial/final permission `0.100087` / `0.100087`; mean final root `0.060000`; no descent worlds (timing distribution empty).
- **Decoupled:** contact `0/10`; descent `0/10`; ordered descent `0/10`; mean initial/final permission `0.100087` / `0.100087`; mean final root `0.060000`; no descent worlds (timing distribution empty).
- **Authored-access calibration:** contact `10/10`; descent `10/10`; ordered descent `0/10`; mean initial/final permission `0.100087` / `0.100087`; mean final root `1.000000`; permission rise min/median/max `0`/`0.0`/`0`; revision begin `2`/`2.0`/`4`; lag `0`/`0.0`/`0` episodes.

Pilot provisional verdicts: contact separation `PASS`; permission-before-revision `PASS`; no authored access in inferential arms `PASS`.

## Freeze log

The design, moderate calibration, thresholds, event ordering, measures, seed blocks, and register guards were frozen before confirmation. No value changed after the pilot. Full details are in `freeze-log.md`.

## Confirmatory results

Twenty fresh, disjoint worlds per arm (`14951:14970`) ran after freeze.

- **Coupled:** contact `19/20`; descent `17/20`; ordered descent `17/20`; mean initial/final permission `0.101899` / `0.898924`; mean final root `0.874728`; permission rise min/median/max `2`/`2.0`/`9`; revision begin `3`/`4.0`/`12`; lag `1`/`1.0`/`3` episodes.
- **No dyad:** contact `0/20`; descent `0/20`; ordered descent `0/20`; mean initial/final permission `0.101899` / `0.101899`; mean final root `0.060000`; no descent worlds (timing distribution empty).
- **Decoupled:** contact `0/20`; descent `0/20`; ordered descent `0/20`; mean initial/final permission `0.101899` / `0.101899`; mean final root `0.060000`; no descent worlds (timing distribution empty).
- **Authored-access calibration:** contact `20/20`; descent `20/20`; ordered descent `0/20`; mean initial/final permission `0.101899` / `0.101899`; mean final root `1.000000`; permission rise min/median/max `0`/`0.0`/`0`; revision begin `2`/`2.0`/`4`; lag `0`/`0.0`/`0` episodes.

### Verdict against §8.5

1. `PASS` — coupled contact ≥ `16/20`; no-dyad and decoupled contact ≤ `2/20`.
2. `PASS` — protector permission rose before the first root-posterior crossing in every inferential world where descent occurred.
3. `PASS` — no coupled, no-dyad, or decoupled world used authored access; the intentionally authored historical comparator remained isolated.

Overall frozen-criterion verdict: **all three construction criteria passed**.

## Interpretation

The construction reproduces the specified coupling result: under this authored dyad generator, likelihood model, and permission threshold, learned precision scaffolding coupled into the protector's evidence stream changes the protector's forecast enough to earn permission; the same scaffold severed from that stream does not. Once permission is present, witnessing observations revise the vulnerable-bundle identity root by likelihood accumulation. The measured event order supports the secondary prediction inside this construction.

This is a computational sufficiency result, not a clinical mechanism or effectiveness claim. The construction can be read as a candidate account of how dyadic precision scaffolding could alter a protector's risk forecast. The evidence likelihoods, future semantics, permission threshold, dyad generator, and bundle graph remain authored.

## What failure means

If descent deadlocks even when coupled, the obstruction is deeper than the coupling hypothesis, and §10's Limits gains a sharper statement of what is missing. That is a better outcome than an authored success. No coupled-arm deadlock was rescued by strengthening scaffolding after results were observed.
