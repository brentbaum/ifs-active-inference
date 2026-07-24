# Experiment 49: dyad-gate coupling and derived descent

## Design

The construction stacks the unmodified Experiment 47 protector over the unmodified Experiment 48 `VulnerableBundle`. A small adapter stores an identity-root log odds beside that bundle because Experiment 48 exposes a relational prior and registration channel but no root posterior. The adapter uses the bundle's committed 2×16 conditional table: each permitted witnessing observation contributes `0.38 × log p(bundle|g=+1)/p(bundle|g=-1)`. Root revision therefore proceeds by Bayesian inference; no repeated-contact assignment or arm-specific root update appears.

The committed Sim 5 dyad module exports only its full runner, so a thin adapter reproduces its load-bearing internal path without modifying it: a stochastic joint therapist signal (surface coherence × relational safety) updates Dirichlet counts over the client's observed settling, the learned signal-to-settling mapping updates the categorical depth posterior, and that posterior yields effective part/context precisions and a normalized relational-field weight. Coupled and decoupled arms receive identical dyad signals and settling outcomes. The field weight controls the rate at which three independently generated protector observations enter `TrustEvidence`; the dyad outcome itself never supplies a trust-evidence sign.

Permission is the protector's risk-model decision under the obsolete future. Its baseline risk reads tolerated outcome, shared competence, and partner policy; inferred shared competence then determines how much of that full risk can be carried without the protector. All three Experiment 47 routes therefore change permission (single-route positive-evidence effects at the structural audit were `0.030337, 0.283766, 0.011258`). Contact is permitted exactly when permission reaches `0.5`. The gate is not stored separately.

Every denied attempt is passed to Experiment 48's committed `register_contact!` with suppression and registration active, strengthening the vulnerable bundle's *alone with this* prior. When permission is granted, suppression ends and a witnessing configuration reaches the identity-root likelihood adapter. Thus the relational prior/registration channel and the four-channel bundle are both live.

### Wiring note: no access by fiat

`run_gate_arm` has no access-rule argument. It learns the Sim 5 field, calls `ingest_evidence!` only through the coupled field edge, computes the protector's risk-model permission, and defines contact as that probability crossing the frozen threshold. Only then does `update_root_from_witnessing!` read one matched bundle observation. The coupled, no-dyad, and decoupled paths contain no branch that grants access from an arm label. The historical authored-access comparator is isolated in `run_authored_calibration`; it bypasses the gate by definition, is reported as a calibration benchmark, and is excluded from every inferential success criterion.

### Register guards

*Configural* refers only to organization within the four-element bundle. *Relational* refers to the interpersonal partner route. Permitted contact with the vulnerable bundle is *witnessing*; protector engagement is *befriending*. *Organization* means the bundle, couplings, precisions, and field profile. *Carrier* means independently parameterized substrate; the learned dyad precision is not renamed a carrier.

### Design decisions

- The spec requires an authored-access baseline while also saying no arm may require authored access. These conflict literally. The comparator is therefore an isolated calibration benchmark, not one of the three inferential gate arms and not evidence for any criterion. Criterion 3 is evaluated over coupled, no-dyad, and decoupled worlds.
- Sim 5's useful mapping, depth, and precision functions are internal and its module exports only `run_sim5_config`. The adapter duplicates only that committed path and constants; this is the genuine interface block allowed by the brief.
- Experiment 48 has no identity-root state or witnessing update. A second thin adapter is necessary for §8.3 and uses its committed conditional table rather than modifying `ExilingEmergence.jl` or inventing an endpoint assignment. Its relational prior and registration channel remain active for denied attempts.
- The risk-model obsolete future was chosen because Experiment 47's post-freeze audit showed that co-protection posterior risk, unlike policy addition, supports the intended differential. The adapter retains the full baseline risk inside the competence-conditioned mixture so no route is causally idle.
- One seed is one matched world. Protector jitter, dyad signals/outcomes, independent protector observations, and the complete witnessing stream are shared across arms. The coupled/decoupled contrast changes only whether field-weighted packets reach `TrustEvidence`.
- One normalized relational-field unit emits one packet on each protector route. Route signs come from an independent matched stream, not from the dyad outcome used to learn the field.
- `0.5` operationalizes permission rising; `0.62` operationalizes revision beginning. Both were declared before the corrected pilot. The ordering predicate requires a strictly earlier episode (`permission < revision`), not a tie.
- Contact is measured separately from descent. A world may contact the bundle yet fail to accumulate enough likelihood evidence for root revision; such a failure is retained.
- The first implementation attempt is retained under `invalidated-attempt-1/`. It was rejected before claiming completion because it mislabeled a safe-rate posterior as the committed dyad precision mechanism. Its exposed seeds and results are excluded. The corrected single moderate calibration uses entirely fresh seeds and contains no rescue sweep.

### Structural audit

Seed blocks disjoint = `true`; Sim 5 mapping/field adapter active = `true`; Experiment 48 bundle reused = `true`; Experiment 48 registration active = `true`; Experiment 47 `TrustEvidence` reused = `true`; all protector evidence routes causally change permission = `true`; gate equals permission threshold = `true`; coupled/decoupled dyad marginals matched = `true`; decoupled ingests no evidence = `true`; no-dyad emits no scaffold packets = `true`; closed gate has no root update = `true`; authored comparator isolated = `true`.

## Pilot

Ten corrected worlds per arm (`24901:24910`) ran once before freeze.

- **Coupled:** contact `10/10`; descent `10/10`; ordered descent `10/10`; mean initial/final permission `0.034295` / `0.997196`; mean final root `1.000000`; mean dyad field `0.986707`; mean registered rejections `1.500000`; permission rise min/median/max `2`/`2.0`/`4`; revision begin `3`/`3.0`/`7`; lag `1`/`1.0`/`3` episodes.
- **No dyad:** contact `0/10`; descent `0/10`; ordered descent `0/10`; mean initial/final permission `0.034295` / `0.034295`; mean final root `0.060000`; mean dyad field `0.000000`; mean registered rejections `18.000000`; no descent worlds (timing distribution empty).
- **Decoupled:** contact `0/10`; descent `0/10`; ordered descent `0/10`; mean initial/final permission `0.034295` / `0.034295`; mean final root `0.060000`; mean dyad field `0.986707`; mean registered rejections `18.000000`; no descent worlds (timing distribution empty).
- **Authored-access calibration:** contact `10/10`; descent `10/10`; ordered descent `0/10`; mean initial/final permission `0.034295` / `0.034295`; mean final root `1.000000`; mean dyad field `0.000000`; mean registered rejections `0.000000`; permission rise min/median/max `0`/`0.0`/`0`; revision begin `2`/`2.5`/`4`; lag `0`/`0.0`/`0` episodes.

Pilot provisional verdicts: contact separation `PASS`; permission-before-revision `PASS`; no authored access in inferential arms `PASS`.

## Freeze log

The design, moderate calibration, thresholds, event ordering, measures, seed blocks, and register guards were frozen before confirmation. No value changed after the pilot. Full details are in `freeze-log.md`.

## Confirmatory results

Twenty fresh, disjoint corrected worlds per arm (`24951:24970`) ran after freeze.

- **Coupled:** contact `20/20`; descent `20/20`; ordered descent `20/20`; mean initial/final permission `0.032915` / `0.997427`; mean final root `1.000000`; mean dyad field `0.974230`; mean registered rejections `2.150000`; permission rise min/median/max `2`/`2.0`/`6`; revision begin `3`/`4.0`/`8`; lag `1`/`2.0`/`6` episodes.
- **No dyad:** contact `0/20`; descent `0/20`; ordered descent `0/20`; mean initial/final permission `0.032915` / `0.032915`; mean final root `0.060000`; mean dyad field `0.000000`; mean registered rejections `18.000000`; no descent worlds (timing distribution empty).
- **Decoupled:** contact `0/20`; descent `0/20`; ordered descent `0/20`; mean initial/final permission `0.032915` / `0.032915`; mean final root `0.060000`; mean dyad field `0.974230`; mean registered rejections `18.000000`; no descent worlds (timing distribution empty).
- **Authored-access calibration:** contact `20/20`; descent `20/20`; ordered descent `0/20`; mean initial/final permission `0.032915` / `0.032915`; mean final root `1.000000`; mean dyad field `0.000000`; mean registered rejections `0.000000`; permission rise min/median/max `0`/`0.0`/`0`; revision begin `2`/`2.0`/`4`; lag `0`/`0.0`/`0` episodes.

### Verdict against §8.5

1. `PASS` — coupled contact ≥ `16/20`; no-dyad and decoupled contact ≤ `2/20`.
2. `PASS` — protector permission rose before the first root-posterior crossing in every inferential world where descent occurred.
3. `PASS` — no coupled, no-dyad, or decoupled world used authored access; the intentionally authored historical comparator remained isolated.

Overall frozen-criterion verdict: **all three construction criteria passed**.

## Interpretation

The construction reproduces the specified coupling result: the Sim 5-form learned mapping changes the categorical depth posterior and relational precision field; coupling that field into three independent protector evidence routes changes the protector's forecast enough to earn permission, while severing the same learned field does not. Denied attempts strengthen Experiment 48's relational prior through registration; once permission is present, witnessing observations revise the vulnerable-bundle identity root by likelihood accumulation. The measured event order supports the secondary prediction inside this construction.

This is a computational sufficiency result, not a clinical mechanism or effectiveness claim. The construction can be read as a candidate account of how dyadic precision scaffolding could alter a protector's risk forecast. The evidence likelihoods, future semantics, permission threshold, dyad generator, and bundle graph remain authored.

## What failure means

If descent deadlocks even when coupled, the obstruction is deeper than the coupling hypothesis, and §10's Limits gains a sharper statement of what is missing. That is a better outcome than an authored success. No coupled-arm deadlock was rescued by strengthening scaffolding after results were observed.
