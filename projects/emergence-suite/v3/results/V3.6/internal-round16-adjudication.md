# V3.6-R1 Round-16 adjudication (INTERNAL)

**Authority.** This round was adjudicated by the evaluator (Fable) acting in
the advisor role, under Brent's explicit instruction of 2026-08-03: "can you
try and debug / iterate a couple rounds without the advisor? play the part of
the advisor please." It is recorded with the same binding force as external
rounds for execution purposes, but is labeled INTERNAL in the ledger and
remains open to retroactive external review. The round-16 question set is the
one composed for GPT-5.6 Pro (scratchpad `round16-ascii.txt`, 4,698 chars);
the questions are answered exactly as posed.

## Ruling 16.1 — real_danger_adaptive intended structural signature; repair

The stratum's scientific intent (round-12 ruling 2.4) is *continuing real
external danger met by adaptive, effective protection*. Its distinguishing
content is carried entirely by the generator's observable-channel parameters,
which are already correct: persistent `danger = 1` at every slice,
`root_state = 0` (the protected system is not itself dysregulated), and
protection efficacy `0.80` (vs 0.50 elsewhere). None of that involves the
cross-mode outcome channel.

The intended structural signature is therefore: **one active mode, no
cross-mode edge, `cross_sign = 0`**. The hard-coded `-1` was a labeling
error — an attempt to mark "danger-opposed" on a channel that does not exist
in a one-mode program. Under the frozen support rule
(`signs = (-1, 1) if structure.cross_mode_outcome else (0,)`, identical in
v35, v35_calibration, v36_bridge, and v36_round12), sign is a property OF the
cross-mode edge; absent the edge, 0 is the only coherent value.

Authorized repair (minimal, generator-only, one line in
`ref/v36_round12.py::_external_structure`):

```python
return structure, (1 if active > 1 else 0)
```

i.e., delete the `real_danger_adaptive` special case. Constraints inherited
from round 15: differential audit must show this exact one-line change and
nothing else; all frozen scientific-module hashes (v31–v35, bridge, oracles)
bitwise unchanged; scorer untouched (the defect is constructor-side only, so
this is GENERATOR_ONLY class, same as round 15).

## Ruling 16.2 — permanent pre-block generator-coherence proof

Confirmed as permanent. Before ANY block that uses a stratified external (or
native) generator opens: for every stratum, construct the emitted
`(structure, cross_sign, partner-channel type)` tuple by direct call to the
constructor functions (zero scientific seeds; use the declared stratum set),
and prove by enumeration that the tuple lies inside BOTH adapters' native
supports with finite, nonzero prior mass. Any miss is FAIL_UNEXECUTABLE
before the block opens. This joins the fixture-identity proofs, lesion
pre-run proofs, and triangulation battery as standing preconditions. It would
have caught this stop (and, by inspection of the four strata, nothing else
currently pending: acute_one and chronic_one emit (1-mode, 0), chronic_multiple
emits (3-mode, +1), all in support).

## Ruling 16.3 — seeds, custody, per-stratum serial first worlds

- Block `3724000:3725999` is burned (suffix ambiguity); the 1,500-world
  prefix (sha `4ea857b9…`) is retained as evidence only, never scored.
- Fresh **final** Population-C block: `3726000:3727999` (2,000 seeds, exact
  cardinality preflight retained). One-shot boundary as for A-R1: a blocking
  failure on a correctly constructed population stands as a scientific
  result; only a further constructor-semantics defect (a coherence-proof
  class miss) returns to adjudication.
- The first-cell-serial rule is **extended**: the first world of EACH stratum
  runs serially, in-process, and is serialized and fsynced before parallel
  dispatch opens for that stratum's remainder. This applies to Population C,
  the tournament, and any future stratified block. Rationale: all three
  constructor-class failures to date surfaced at a first world of some cell
  or stratum; serializing those boundaries caps collateral loss at one
  stratum's remainder rather than the block.

## Ruling 16.4 — tournament population coverage

Confirmed. The tournament's 6,000-world population uses the same four
stratum constructors through the same `generate_external_world` path (the
`count in (2000, 6000)` guard covers both). The 16.1 repair plus the 16.2
coherence proof cover it with no further change. The tournament block
`3684000:3689999` remains reserved and untouched; it opens only after
Population C passes.

## Ruling 16.5 — resumption order

Confirmed unchanged, serial per round 14: Population C (fresh block) →
tournament → gate 4 (`3709000:3713999`) → gate 5 (`3635000:3659999`) →
compatibility attestations → V3.6 freeze → evaluator reveals C-V36A/B/C →
final v3 profile → T-V3-DO1. Paper and HTML propagation remain deferred by
Brent's standing instruction.
