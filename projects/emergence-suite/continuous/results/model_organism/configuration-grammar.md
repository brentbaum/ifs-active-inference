# Experiment 50-H frozen configuration grammar

Status: **frozen before Phase 0**  
Schema: `model-organism-configuration/v1`  
Freeze scope: all Experiment 50-H, 50-P, and 50-L instantiations

This grammar changes the number and arrangement of part-slots while leaving the canonical equations and `genome.toml` unchanged. Configuration files are TOML records with exactly eight top-level fields: `assay`, `id`, `nodes`, `edges`, `slots`, `initializers`, `interventions`, and `observations`. Except for the assay identifier and integer slot multiplicities, numeric values are invalid. Unknown fields or vocabulary terms are a build failure.

## Node types

| Symbol | Meaning |
|---|---|
| `vulnerable_bundle` | Four-element self/world/policy/outcome organization with couplings, relational prior, contact attempts, registration, and context-split root machinery. |
| `protector` | Permission through expected-cost choice using outcome, co-protection, and latent-partner trust posteriors. |
| `protective_repertoire` | Policies whose cost and reliability beliefs are learned by developmental replay. |
| `precision_field` | Five-channel part/context/interoception/relational/policy precision field. |
| `latent_partner` | One latent disposition process (`trustworthy`, `neutral`, or `adverse`) generating both regulation signals and trust-relevant outcomes. |
| `episodic_memory` | Target of the one-step high-precision freeze write. |
| `part_slot` | Optional self-like slot with local monitoring; recursive broadcast is separately controlled. |
| `cue_meaning` | Cue-bound meaning beneath a shared identity root. |

## Edge types

| Symbol | Source → target and semantics |
|---|---|
| `bundle_coupling` | Within-bundle self–world and policy–outcome coupling. |
| `shared_root_parent` | Root → multiple cue meanings. |
| `reversed_root_child` | Cue meanings → root, used only as assay 4's graph-direction control. |
| `protector_guards_bundle` | Protector permission gates witnessing of one bundle; many protectors may target one bundle. |
| `repertoire_to_permission` | Learned expected costs feed protector policy choice. |
| `partner_to_regulation` | The latent partner generates regulation signals. |
| `partner_to_trust_outcome` | The same latent partner generates trust-relevant outcomes. |
| `field_to_protector` | Relational-field packets enter the ordinary protector update path. |
| `field_broadcast` | Revised five-channel field is recursively broadcast. |
| `local_monitor` | A part-slot reads local forecast errors. |
| `registration_write` | Suppressed contact can update the relational prior when registration is on. |
| `freeze_write` | Overwhelm plus low control writes episodic state for one step. |
| `ordinary_evidence` | Corrective evidence enters the standard Bayesian update path. |

## Slots

The `[slots]` table may contain only these nonnegative integer multiplicities: `vulnerable_bundles`, `protectors`, `protective_repertoires`, `precision_fields`, `latent_partners`, `episodic_memories`, `part_slots`, and `cue_meanings`. Multiple protectors guarding one bundle is represented by `protectors > vulnerable_bundles` plus repeated `protector_guards_bundle`; no polarization-specific node or equation exists. A zero-count slot remains instantiated as an idle canonical mechanism and must pass the bit-for-bit idleness audit.

## Initializers

| Symbol | Rule |
|---|---|
| `neutral_prior` | Set every psychologically meaningful posterior to the genome's neutral prior and log provenance. |
| `developmental_replay` | Generate a seeded history and replay it through canonical update equations. |
| `freeze_history_replay` | Generate overwhelm/control history and replay freeze writes. |
| `partner_history_replay` | Learn partner type, competence, and tolerated outcome from noisy joint interaction history. |
| `policy_history_replay` | Learn protective-policy cost and reliability from developmental outcomes. |

No initializer may contain or accept a posterior value. “Mature,” “frozen,” and “trusting” are histories, never states.

## Interventions

`overwhelm_control_grid`, `closed_action_evidence_loop`, `open_loop_replay`, `corrective_evidence`, `controllability_dose`, `four_field_regimes`, `one_dimensional_comparator`, `witnessing`, `matched_exposure`, `reversed_graph`, `regulation_on`, `regulation_off`, `root_evidence_on`, `root_evidence_off`, `registration_on`, `registration_off`, `registration_ablation`, `context_family_global`, `context_family_cue_local`, `context_family_split`, `context_family_drift`, `context_family_change_point`, `limited_evidence_budget`, `premature_doover`, `postrevision_doover`, `suggestion_only`, `stakes_low`, `stakes_high`, `risk_model_obsolete_future`, `scaffold_coupled`, `scaffold_decoupled`, `positive_evidence_without_scaffold`, `field_narrowing`, `recursive_broadcast_on`, and `recursive_broadcast_off`.

`field_narrowing` reduces context and relational channel availability through the canonical field equation. Registration toggles only the `registration_write` edge. Dyad absence is `latent_partners = 0`; dyad presence uses exactly one latent partner process. Local monitoring without recursive broadcast is `part_slots = 1`, `local_monitor`, and `recursive_broadcast_off`.

## Observation channels

`self`, `world`, `policy`, `outcome`, `context_then_now`, `root_evidence`, `cue_evidence`, `overwhelm`, `control`, `contact_attempt`, `suppression`, `policy_cost`, `policy_success`, `partner_regulation`, `partner_outcome`, `settling`, `field_forecast_error`, `permission`, `registration`, `imaginal_outcome`, and `part_local_error`.

The words *configural* and *relational* are guarded: configural is statistical organization only; relational is interpersonal only. Exile contact is *witnessing* and protector contact is *befriending*. Organization means bundle + couplings + precisions + field profile; carrier means independently parameterized substrate.

## Expressibility audit

The ten frozen configurations are `configurations/assay-01.toml` through `assay-10.toml`. The grammar additionally expresses the public sealed-challenge interfaces without revealing them: multiple protector slots may guard one bundle; evidence may target episodic or cue observations; and a `part_slot` may use `local_monitor` with `recursive_broadcast_off`. No claim is made about whether the withheld protocols will succeed.
