---
status: ready
priority: p1
issue_id: "002"
tags: [experiment-51, active-inference, compositional-engine, preregistration]
dependencies: []
---

# Execute Experiment 51 through the complete staged record

## Problem Statement

Experiment 51 requires a prospective, compositional generative architecture and
a custody-preserving execution sequence. The handoff specification's prose-only
schema section is not executable enough to support a fair hidden challenge, so a
formal public contract must be locked before challenge authoring. The complete
experiment must then preserve its seal, freeze, reveal, and no-repair boundaries.

## Findings

- The specification and kickoff were moved from `~/Downloads` to
  `projects/ifs-paper/`, then amended only to bind private authoring to public
  contract `1.0.1`, its exact commit, and its content manifest.
- Fable identified a blocking schema underdetermination: §6 lacks field names,
  enums, reference rules, trace vocabulary, and an analysis expression grammar.
- The original worktree contains unrelated user changes. Experiment 51 work is
  isolated on `codex/experiment-51`.
- Experiment 50 must remain byte-for-byte unchanged.

## Proposed Solutions

### Option 1: Publish a formal public contract, then seal and execute

**Approach:** Lock versioned JSON Schemas, trace vocabulary, analysis grammar,
canonical archive tooling, and a public dummy bundle before private challenge
authoring. Continue through all mandated Experiment 51 stages.

**Pros:**
- Makes prospective compilation fair and auditable.
- Preserves the intended custody and no-post-reveal-code boundaries.

**Cons:**
- Adds a public apparatus commit not explicitly enumerated in the kickoff.
- Requires a larger implementation and validation record.

**Effort:** Large

**Risk:** Medium

### Option 2: Seal against the prose-only schema

**Approach:** Invent private TOML keys and let the implementation guess.

**Pros:**
- Faster initial seal.

**Cons:**
- Invalid prospective test; semantic inexpressibility would be confounded with
  missing public grammar.

**Effort:** Small

**Risk:** Critical

## Recommended Action

Use Option 1. The author explicitly authorized resolving the public-contract gap
and continuing through Experiment 51, with Fable review.

## Technical Details

**Primary homes:**
- `projects/emergence-suite/compositional/`
- `projects/ifs-paper/`

**Custody constraints:**
- Private challenge archives and seed escrow remain outside the repository.
- Only hashes and byte counts enter the pre-implementation seal commit.
- Challenge archives are revealed only after the frozen engine exists.

## Acceptance Criteria

- [x] Public JSON Schemas, trace vocabulary, analysis grammar, and reference
      rules are versioned and validated.
- [x] Canonical uncompressed USTAR builder/verifier passes a public test vector.
- [x] Fable reviews the public contract and all blocking findings are addressed.
- [ ] At least three private 51-P bundles meet every §12 requirement.
- [ ] H/C/P/L seeds are disjoint and release-block commitments are sealed.
- [ ] Seal commit contains no private challenge or seed plaintext.
- [ ] Generic compiler, engine, runner, evaluator, and provenance trace exist.
- [ ] Semantic edge/mutation, inference, evidence-accounting, composition, and
      generic-runner gates pass or produce an explicit architecture failure.
- [ ] Fable reviews Stage A and blocking findings are resolved or retained.
- [ ] Freeze package and 51-L preregistration predate challenge reveal.
- [ ] 51-H and 51-C run once on escrowed blocks.
- [ ] Revealed 51-P archives hash-match, validate without source changes, and
      scientifically evaluable challenges run once.
- [ ] 51-L lesions and robustness run from the preregistered package.
- [ ] Results synthesis states failures and implementation walls at the affected
      claims without exceeding the specification's licensed language.
- [ ] Experiment 50 tracked files are unchanged.
- [ ] Full test suite and record-integrity checks pass.
- [ ] Final Fable review has no unresolved blocking process or claim-discipline
      findings.

## Work Log

### 2026-07-26 - Authorization and isolation

**By:** Codex (Sol role)

**Actions:**
- Read the complete kickoff and Experiment 51 specification.
- Consulted Fable on placement, custody, and archive/schema ambiguity.
- Moved both public Markdown files unchanged into `projects/ifs-paper/`.
- Created isolated branch/worktree `codex/experiment-51`.
- Received author authorization to publish the missing public contract and
  continue through Experiment 51.

**Learnings:**
- A prose-only content policy is insufficient for a sealed executable challenge.
- The formal contract must predate private challenge authoring.

### 2026-07-26 - Public contract closure and second Fable gate

**By:** Codex (Sol role)

**Actions:**
- Added four closed JSON Schemas, cross-file semantic validation, typed trace and
  analysis grammars, world/protocol/RNG semantics, canonical USTAR custody
  tooling, seed-escrow commitment tooling, and the public `51-P-00` test vector.
- Bound the public apparatus to a generated SHA-256/byte-count content manifest.
- Addressed Fable's first two blocking reviews: contingency timing, scalar
  distribution lifetimes, episode boundaries, candidate completeness,
  predicate and decision typing, interval algorithms, event ordering,
  control matching, inactive-node rules, joint-action labels, and
  purpose/order-bound seed commitments.
- Passed 62 schema accepted/rejected pairs, 27 semantic rejection fixtures,
  seed-escrow conformance, semantic dummy validation, and independent Julia and
  Python archive verification.
- Returned the exact manifest-bound contract to Fable for a fresh seal/no-seal
  decision. No private challenge or seed material exists yet.

**Learnings:**
- Event scheduling and resampling algorithms are part of the scientific
  contract, not implementation details.
- A seed-block hash must bind release purpose and order to preserve staged
  custody.

### 2026-07-26 - Public contract approval

**By:** Codex (Sol role), reviewed by Fable

**Actions:**
- Closed the remaining contract ambiguities around action/hazard outcomes,
  causal success-to-transition timing, empty policy support, tick/event row
  domains, stopping rows, developmental replay, paired cross-arm units,
  evidence-budget pairs, inactive structure nodes, and horizon bounds.
- Added exact public math for bootstrap resampling, paired-unit keys,
  Clopper-Pearson intervals, decision boundaries, and elementary RNG
  transforms.
- Passed the authoritative contract command: four JSON Schemas, 64 accepted/
  rejected schema pairs, 40 semantic rejection fixtures, seed-escrow tests,
  analysis-math tests, RNG-transform vectors, the public manifest, canonical
  USTAR reconstruction, and independent archive verification.
- Sealed the superseded `1.0.0` public dummy `51-P-00` at SHA-256
  `5c6fd361536c44b5e30b56404f7ca49ed2fd7682569aabf505429472dcb72d3f`
  and 24,064 bytes; the later correction log records why this version was
  withdrawn before private sealing.
- Received Fable's exact-contract verdict: `APPROVED`.
- Reverified the Experiment 50 tracked-tree digest as
  `64444faf9b2c8ab5e8a2e5ea9cf8e2177b9953a49de318a1852a7bbca3646679`
  with no diff from the branch base.

**Learnings:**
- Row occurrence semantics and cross-arm resampling keys must be public before
  sealed analysis plans can be interpreted fairly.
- A single authoritative validator must invoke every suite named by the
  contract.

### 2026-07-26 - Pre-seal escrow correction

**By:** Codex (Sol role)

**Actions:**
- Detected on first real escrow generation that Julia's `String(raw_bytes)`
  ownership transfer emptied the byte vector later supplied to the public
  commitment formatter.
- Withheld the erroneous empty-file commitment; no private seal or encrypted
  custody object was created.
- Moved all affected unsealed private drafts to macOS Trash and revoked the
  earlier Fable approval.
- Bumped the public contract to `1.0.1`, preserved the exact byte vector with
  `String(copy(raw_bytes))`, and added byte-for-byte SHA-256 and length
  regression assertions.
- Regenerated the `1.0.1` public dummy vector at SHA-256
  `7f1d40d9200430b68ab6138cba260bb1d4bbf76b8836de1f7a7ee7363ff70b2a`
  and 24,064 bytes.
- Restored all accidentally touched transitive `package-lock.json` metadata so
  only the two root-package version fields changed, then passed a clean
  `npm ci` and the full authoritative suite.
- Received Fable's replacement exact-contract verdict: `APPROVED`.

**Learnings:**
- Parser correctness does not establish custody correctness; exact committed
  bytes need an independent regression assertion.
