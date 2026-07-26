# Experiment 51 public declarative contract

**Contract ID:** `ifs-ai-experiment-51-contract`
**Contract version:** `1.0.0`
**Status:** public pre-implementation apparatus

This contract resolves the machine-readable details intentionally left implicit
by §6 of the Experiment 51 specification. It is locked before any private 51-P
challenge or seed escrow is authored. It defines syntax and reference semantics;
it does not define organism equations, posterior values, challenge outcomes, or
private thresholds.

## Normative files

- `schemas/configuration.schema.json`
- `schemas/world.schema.json`
- `schemas/protocol.schema.json`
- `schemas/analysis.schema.json`
- `contract/trace-vocabulary.md`
- `contract/analysis-expression-grammar.md`
- `contract/reference-rules.md`
- `contract/world-semantics.md`
- `contract/protocol-semantics.md`
- `contract/rng-streams.md`
- `contract/initialization.md`
- `contract/seed-escrow-convention.md`
- `contract/conformance-matrix.md`
- `contract/package.json`
- `contract/package-lock.json`
- `contract/archive-convention.md`
- `contract/public-contract-manifest.sha256`
- `scripts/contract/validate_contract.sh`
- `scripts/contract/validate_bundle.jl`
- `scripts/contract/canonical_bundle.jl`
- `scripts/contract/independent_verify.py`
- `scripts/contract/test_schema_variants.py`
- `scripts/contract/test_semantic_conformance.jl`
- `scripts/contract/seed_escrow.jl`
- `scripts/contract/test_seed_escrow.jl`
- `scripts/contract/public_contract_manifest.py`
- `scripts/contract/analysis_math.jl`
- `scripts/contract/test_analysis_math.jl`
- `scripts/contract/rng_transforms.jl`
- `scripts/contract/test_rng_transforms.jl`

The JSON Schemas describe the JSON data model produced by Julia's standard TOML
parser. TOML documents remain the normative challenge representation.

## Contract identity

Every TOML file begins with:

```toml
contract_id = "ifs-ai-experiment-51-contract"
contract_version = "1.0.0"
```

The version is exact. Implementations must reject an unknown version rather than
silently interpreting it.

## Public vocabulary

### Node types

`BundleNode`, `ContextNode`, `CueNode`, `LocalPrecisionNode`,
`GlobalPrecisionNode`, `ProtectorNode`, `PartnerNode`, `AccessNode`,
`EpisodeNode`, and `StructureNode`.

### Edge types

`bundle_context`, `cue_root`, `local_monitor`,
`local_to_global_broadcast`, `global_precision_message`,
`protector_joint_policy`, `protector_cross_prediction`,
`partner_regulation`, `partner_trust`, `policy_access`,
`access_bundle`, `episode_scope`, `structure_scope`, `registration`, and
`world_coupling`.

Every edge is directed and has state `active`, `inactive`, or `learnable`.
Scientific semantics belong to the generic engine and must be covered by the
semantic edge and mutation gates. An edge that merely parses is non-conforming.

| Edge type | Allowed source | Allowed target | Public message semantics |
|---|---|---|---|
| `bundle_context` | `ContextNode` | `BundleNode` | context posterior conditions bundle inference |
| `cue_root` | `CueNode` | `BundleNode` | learnable cue-to-root association |
| `local_monitor` | `BundleNode` | `LocalPrecisionNode` | local reliability forecast input |
| `local_to_global_broadcast` | `LocalPrecisionNode` | `GlobalPrecisionNode` | optional local forecast message |
| `global_precision_message` | `GlobalPrecisionNode` | `BundleNode`, `ContextNode`, or `ProtectorNode` | five-channel precision message |
| `protector_joint_policy` | `ProtectorNode` | `AccessNode` | protector factor in the joint policy posterior |
| `protector_cross_prediction` | `ProtectorNode` | `ProtectorNode` | forecast of another protector's policy effect |
| `partner_regulation` | `PartnerNode` | `GlobalPrecisionNode` | regulation observation message |
| `partner_trust` | `PartnerNode` | `ProtectorNode` | trust/co-protection forecast message |
| `policy_access` | `BundleNode` | `AccessNode` | no-protector bundle policy contribution |
| `access_bundle` | `AccessNode` | `BundleNode` | inferred contact/access message |
| `episode_scope` | `EpisodeNode` | `BundleNode`, `CueNode`, or `ContextNode` | joint episodic likelihood scope |
| `structure_scope` | `BundleNode`, `ContextNode`, or `EpisodeNode` | `StructureNode` | observations scored by structural candidates |
| `registration` | `AccessNode` | `BundleNode` | denied/suppressed access registration message |
| `world_coupling` | `BundleNode`, `ContextNode`, or `PartnerNode` | a different node among those types | generic cross-latent coupling |

At most one edge may have the same `(type, from, to)` triple. Multiplicity is
represented by distinct typed nodes, never an edge count or weight.

### Likelihood families

`categorical`, `bernoulli`, `ordinal`, and `gaussian_bounded`.

### Policy families and actions

Policy families are `contact`, `avoidance`, `inquiry`, `support`,
`suppression`, and `observe`. Public action symbols are `approach`, `withdraw`,
`inspect`, `request_support`, `offer_support`, `suppress`, `permit`,
`wait`, and `observe`.

### World families and processes

World families are `hazard_loop`, `context_process`, `partner_process`,
`developmental_composition`, and `generic_discrete`.

Processes are `iid`, `markov`, `change_point`, `drift`, `action_contingent`,
and `coupled_latent`. Parameter distributions are `fixed`, `uniform`, `beta`,
`integer_uniform`, `categorical`, and `transition_matrix`. Exact typed
parameters and dimension rules are normative in
`contract/world-semantics.md`.

## Public bounds

- Node cardinality: `2`, `3`, `4`, or `5`.
- Nodes per configuration: `1...64`.
- Edges per configuration: `0...256`.
- Protector nodes: `0...8`; the engine must support at least three.
- Horizon: `1...4096`.
- Schedule time: `0 <= time < horizon <= 4096` (the schema's loose scalar cap
  is narrowed by semantic validation).
- Probability parameters: `[0, 1]`.
- Finite scalar parameters and analysis literals: `[-10^6, 10^6]`.
- Evidence-budget tolerance fraction: `[0, 0.10]`.
- Crossing persistence: `1...128`.
- Structure candidates: exactly the declared cardinality for every active
  `StructureNode`, zero for inactive structure nodes, and `1...32` candidates
  total when any active structure node exists; otherwise zero.

Aggregate feasibility bounds:

- product of active node cardinalities: at most `1,000,000`;
- joint protector policy combinations: at most `4096`;
- parent configurations per coupled process or emission: at most `625`;
- expanded scheduled events per arm: at most `4096`;
- `(maximum horizon tick rows × arms + expanded event rows) × requested trace fields`:
  at most `1,000,000` cells per seed before wildcard expansion;
- total analysis AST nodes: at most `256`;
- bootstrap resamples: at most `5000`;
- each bundle file: at most `262,144` bytes;
- canonical archive: at most `1,048,576` bytes.

## Configuration purity

`configuration.toml` may declare graph structure, observation channels, policy
availability, and history/initializer IDs only. It may not contain posterior
values, thresholds, likelihood numbers, outcomes, or scientific function names.
All configuration keys are closed by schema; unused accepted keys are a compiler
failure.

The only action resolver is `plurality-safety-priority-v1`, normatively defined
in `contract/protocol-semantics.md`.

## World discipline

World distributions and contingencies may contain bounded numbers because they
generate observations and outcomes, never agent conclusions. Latent truth is
written only to evaluator-only trace paths. A world parameter must belong to a
schema-bounded typed distribution object and cannot be read by the agent.

## Protocol discipline

Protocols schedule typed observations, interventions, probes, and stopping
checks. An intervention can toggle an edge, observation source, policy action,
or declared world contingency. It cannot assign a state or metric. Trace-based
triggers use external/proxy fields unless explicitly labeled
`latent_intervention`.

No protocol trigger may read `world.*`. `external_proxy` triggers may read only
`run.time`, `action.*`, and `observation.*`; `latent_intervention` triggers may
read only scalar or Boolean `state.*` and `policy.*` paths.

Expansion, collision ordering, observe/probe/imaginal behavior, intervention
persistence, and stop-check timing are normative in
`contract/protocol-semantics.md`.

## Analysis discipline

Analyses use the structured expression grammar in
`contract/analysis-expression-grammar.md`. The evaluator receives a sealed trace
and an analysis plan; no evaluator plug-in or source-language snippet is
permitted.

## Validation order

1. Preflight UTF-8/LF/final-newline rules.
2. Parse TOML.
3. Validate the closed public schemas.
4. Resolve all cross-file IDs and trace-field patterns.
5. Enforce semantic prohibitions not expressible in JSON Schema.
6. Canonically archive the exact five files.
7. Verify the archive by independent parse-and-rebuild comparison.

`validate_contract.sh` is authoritative and must complete every layer. Running
only the semantic Julia validator or only JSON Schema is insufficient.

The public bundle `protocols/public-dummies/51-P-00/` is the contract test
vector. It is not a scientific challenge and uses no escrowed seed.
