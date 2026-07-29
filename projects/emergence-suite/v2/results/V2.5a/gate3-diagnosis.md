# V2.5a Gate-3 decomposition diagnosis

Status: **diagnosis only**. This analysis changes no engine, protocol,
criterion, parameter, or result. It reads the retained Gate-3 traces and
deterministically reconstructs only their already-consumed worlds through the
frozen constructors. No new seed was consumed.

Trace sources:

- `gate-3-matching-per_world.json`, seeds 758000:758299;
- `gate-3-bridge-per_world.json`, seeds 758500:758619;
- the frozen 120-state bank used by those bridge traces.

## 1. Dose-pathway construct

### Analytic result: the matching target is dose-invariant

The frozen association-dose operator changes marker placement only. For dose
\(a\), it maps a slice

\[
o_t=(Y_t,X_t,R_t)
\quad\longmapsto\quad
o_t^{(a)}=(Y_t,X_{\pi_a(t)},R_t),
\]

where the permutation is within cue. Outcomes, roots, cue order, missingness,
and every channel multiset are unchanged.

The declared matching target is

\[
K_n =
D_{\mathrm{KL}}\!\left[
q_n(G)\,\|\,q_0(G)
\right],\qquad
q_n(G)\propto q_0(G)\prod_{t=1}^n p(R_t\mid G).
\]

Neither \(X_t\) nor the marker permutation \(\pi_a\) occurs in this
posterior. Therefore

\[
q_n^{(a)}(G)=q_n(G),\quad K_n^{(a)}=K_n,
\quad\text{and}\quad m^{*}(a)=m^{*}
\]

for a paired world under the frozen likelihood interface. The same result
holds operationally even before this algebra is used: the Gate-3 matching
runner records `association_strength` as a row label but never passes it to
`match_marginal_root_information`; that function regenerates the same root
stream and calls only `root_posterior`.

**Construct finding:** association dose cannot affect the root-channel
matching target or \(m^*/n\) under the frozen interface. The authored
monotone-\(m^*/n\)-by-dose criterion therefore lacks construct validity for
this implementation. Equality would be guaranteed only in a paired-seed
design. The retained assay instead assigned different, unpaired seeds to its
six dose labels, so its observed group differences are sampling differences
in root paths.

### Retained-trace confirmation

Every one of the 300 targets was exactly
`0.6931471805599453 = log(2)` at retained precision. The root-observation CPT
was fixed in every world at reliability 0.85, corresponding to a nonmissing
root-token log likelihood-ratio step of
`log(0.85/0.15) = 1.7346010553881064`. No root-association-strength or
root-precision parameter varied across dose cells.

| Dose label | Worlds | Median \(m^*/n\) | Median \(m^*\) | Mean root-missing slices | Mean terminal absolute root-token imbalance |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 50 | 0.062500 | 6 | 14.40 | 56.16 |
| 0.2 | 50 | 0.062500 | 6 | 14.58 | 56.18 |
| 0.4 | 50 | 0.062500 | 6 | 14.38 | 57.22 |
| 0.6 | 50 | 0.062500 | 6 | 13.76 | 56.32 |
| 0.8 | 50 | 0.052083 | 5 | 14.06 | 57.62 |
| 1.0 | 50 | 0.052083 | 5 | 14.16 | 57.56 |

What \(m^*/n\) actually measures here is the first-passage time of the
realized root-token random walk. At the selected prefix, the absolute
positive-minus-negative root-token imbalance was exactly 4 in all 300
worlds. Missing root slices delay that boundary, while contradictory root
tokens make the walk recede from it:

- matched-slice count quantiles (minimum, Q25, median, Q75, Q90, maximum):
  `4, 4, 6, 8, 11, 20`;
- nonmissing root tokens needed at crossing: minimum 4, median 4, maximum 16;
- opposing token pairs before crossing: median 0, Q90 2, maximum 6;
- correlation of \(m^*\) with missing slices before crossing: `0.7506`;
- correlation of \(m^*\) with opposing pairs before crossing: `0.9336`;
- correlation of \(m^*\) with root switches before crossing: `0.8654`.

Thus the retained variation is due to the realized root path and missingness,
under one fixed precision. It is not variation in association dose, root
association strength, or root precision.

## 2. Matching-tolerance tails in the formed-P bridge

All 120 bridge scans were uncensored. The 17 failures are therefore not
failures to accumulate enough information by the 8n cap. They are failures
of the discrete prefix grid to land within 0.01 nats of the target.

### Population decomposition

| Quantity | 17 outside tolerance | 103 within tolerance |
|---|---:|---:|
| Moderate / strong / very-strong states | 9 / 4 / 4 | 31 / 36 / 36 |
| Initial \(|q_0(G=1)-0.5|\), mean / median | 0.2227 / 0.2533 | 0.1856 / 0.1347 |
| Bank association reliability, mean / median | 0.6454 / 0.6361 | 0.8521 / 0.8789 |
| Target KL, mean / median | 0.8550 / 0.5346 | 1.7883 / 1.0070 |
| Crossing-slice KL jump, mean / median | 0.3976 / 0.3611 | 0.02326 / 0.01890 |
| Absolute error, mean / median | 0.2327 / 0.1772 | 0.00537 / 0.00505 |
| \(m^*\), mean / median | 17.53 / 8 | 11.75 / 7 |

The moderate-stratum failure rate was 9/40 (22.5%); the strong and
very-strong rates were each 4/40 (10%). Initial-root extremity was somewhat
higher in the tail, but the sharper separator was the bank-specific
association reliability. The absolute matching error correlated `0.9217`
with the KL jump at the crossing and `-0.3927` with bank reliability.

All 17 failures had the same apparatus signature:

1. the preceding prefix was more than 0.01 below the target;
2. the next root-bearing slice overshot to more than 0.01 above it;
3. no prefix anywhere through the 256-slice cap was within 0.01 of the
   target.

Consequently these 17 targets were unattainable on the frozen prefix lattice,
not merely missed by the choice of the first crossing.

| Seed | Stratum | \(q_0(G=1)\) | Bank reliability | Target KL | \(m^*\) | KL before | KL at \(m^*\) | Error | Best grid error | Best prefix |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 758504 | very_strong | 0.753350 | 0.636054 | 0.033938 | 29 | 0.000000 | 0.361149 | 0.327211 | 0.033938 | 1 |
| 758511 | strong | 0.531870 | 0.661176 | 0.657767 | 3 | 0.605685 | 0.720494 | 0.062727 | 0.052081 | 2 |
| 758522 | moderate | 0.500000 | 0.636054 | 0.375118 | 8 | 0.270438 | 0.557706 | 0.182588 | 0.104680 | 1 |
| 758535 | very_strong | 0.576726 | 0.643177 | 0.790646 | 5 | 0.676966 | 0.813599 | 0.022953 | 0.022953 | 5 |
| 758537 | moderate | 0.753350 | 0.877457 | 1.120566 | 35 | 1.007602 | 1.297233 | 0.176667 | 0.112964 | 10 |
| 758540 | strong | 0.753350 | 0.636054 | 0.787644 | 11 | 0.361149 | 1.007602 | 0.219959 | 0.219959 | 11 |
| 758554 | very_strong | 0.985719 | 0.742424 | 0.534564 | 29 | 0.067086 | 0.733889 | 0.199325 | 0.199325 | 29 |
| 758561 | moderate | 0.753350 | 0.528751 | 0.158210 | 1 | 0.000000 | 0.361149 | 0.202939 | 0.202939 | 1 |
| 758569 | very_strong | 0.999620 | 0.636054 | 0.416729 | 16 | 0.270336 | 1.624252 | 1.207522 | 0.146393 | 11 |
| 758577 | moderate | 0.913467 | 0.830383 | 2.413778 | 20 | 2.366726 | 2.429779 | 0.016000 | 0.016000 | 20 |
| 758578 | moderate | 0.753350 | 0.528751 | 0.404158 | 2 | 0.361149 | 1.007602 | 0.603445 | 0.043009 | 1 |
| 758579 | strong | 0.576726 | 0.538591 | 0.460129 | 3 | 0.308029 | 0.676966 | 0.216837 | 0.152099 | 2 |
| 758584 | strong | 0.634685 | 0.516427 | 0.304192 | 3 | 0.000000 | 0.332546 | 0.028354 | 0.028354 | 3 |
| 758599 | moderate | 0.985719 | 0.568611 | 3.992072 | 5 | 3.748709 | 4.135813 | 0.143740 | 0.143740 | 5 |
| 758603 | moderate | 0.500000 | 0.528751 | 0.166409 | 18 | 0.000000 | 0.270438 | 0.104029 | 0.104029 | 18 |
| 758608 | moderate | 0.516714 | 0.877983 | 0.626853 | 107 | 0.582605 | 0.690891 | 0.064038 | 0.044248 | 2 |
| 758618 | moderate | 0.798301 | 0.585144 | 1.291440 | 3 | 1.104068 | 1.468682 | 0.177242 | 0.177242 | 3 |

### Why the pilot did not expose the tail

The pilot/carrying matching population began from prior `(0.5, 0.5)` and
computed both the 96-slice target and the prefix scan with the same fixed
0.85 root CPT. In the retained Gate-3 matching population, the long-history
target saturated at `log(2)`, and the first absolute root-token imbalance of
4 produced KL `0.6854553788470493`, exactly `0.007691801712895963` below
the target. This is the pilot's published maximum error.

The formed-bank bridge is different in two coupled ways:

- its target is generated from an arbitrary banked root prior and the bank's
  association reliability through the context-indexed composition updater;
- its matching scan starts from that prior but uses the fixed 0.85
  root-observation CPT.

The resulting target generally is not a point on the scan's integer
root-token lattice. Low bank reliability produced especially coarse
crossings relative to its smaller target changes. The 0.01 tolerance is thus
attainable for 103/120 banked worlds but structurally unattainable on the
frozen scan grid for the other 17. Under the literal criterion they remain
matching failures; apparatus-first, they are granularity/target-lattice
failures rather than censoring or insufficient-information failures.

## 3. Per-slice decomposition identity

### The identity for unequal stream lengths

Let \(J_t\) be signed joint root movement after \(t\) joint slices, with
joint length \(n\), and let \(M_s\) be signed marginal root movement after
\(s\) marginal slices, with matched length \(m^*\). Set \(J_0=M_0=0\).
For \(L=\max(n,m^*)\), hold each completed trajectory constant:

\[
\bar J_\ell=J_{\min(\ell,n)},\qquad
\bar M_\ell=M_{\min(\ell,m^*)}.
\]

Define the published pathway increment as

\[
\delta_\ell =
(\bar J_\ell-\bar J_{\ell-1})
-
(\bar M_\ell-\bar M_{\ell-1}).
\]

Then telescoping gives

\[
\sum_{\ell=1}^{L}\delta_\ell
=J_n-M_{m^*}.
\]

Different stream lengths do not invalidate the identity. They require the
constant-tail convention above (equivalently, sum each stream's increments
over its own length and subtract). The frozen implementation uses precisely
this padding convention when constructing
`per_slice_difference_increments`.

### What failed

The increment list and the published terminal contrast did not use the same
joint endpoint:

- the contract-facing `joint_root_movement` comes from
  `_composition_world` and `_context_indexed_root_posterior`, whose root
  likelihood uses each bank state's `association_reliability`;
- the joint trajectory used to construct the increments calls
  `v25a.root_posterior`, whose likelihood is the fixed V2.4 root CPT with
  reliability 0.85.

If the latter trajectory is denoted \(\widehat J_t\), the identity that the
stored increments actually satisfy is

\[
\sum_\ell\delta_\ell
=\widehat J_n-M_{m^*},
\]

whereas the reported contrast is

\[
J_n^{\mathrm{bank}}-M_{m^*}.
\]

Across all 120 retained bridge worlds, the corrected identity
`sum(increments) == fixed-0.85 joint-trajectory endpoint -
marginal endpoint` held with maximum absolute error `0.0`, hence within
`1e-10`. The discrepancy from the published contrast equaled
\(\widehat J_n-J_n^{\mathrm{bank}}\) exactly in every world (maximum
residual `0.0`). Sixty-four worlds exceeded `1e-10`; the maximum endpoint
mismatch was `0.2470998783239713`.

Therefore the authored telescoping identity was not mathematically wrong for
matched contrasts, including unequal-length contrasts. The failure is an
implementation inconsistency in the diagnostic trajectory: it uses a
different root likelihood from the endpoint whose decomposition it claims
to publish.

### Worked example: seed 758569

For seed 758569, \(n=32\) and \(m^*=16\):

| Quantity | Value |
|---|---:|
| Initial \(q_0(G=1)\) | 0.999619741489662 |
| Bank association reliability | 0.6360544217687074 |
| Contract-facing bank-reliability joint movement \(J_n^{bank}\) | 0.024884543297402972 |
| Fixed-0.85 trajectory endpoint \(\widehat J_n\) | 0.27198442162137426 |
| Marginal endpoint \(M_{m^*}\) | 0.06446128650007188 |
| Published terminal contrast \(J_n^{bank}-M_{m^*}\) | -0.03957674320266891 |
| Stored increment sum \(\widehat J_n-M_{m^*}\) | 0.20752313512130238 |
| Endpoint-likelihood mismatch \(\widehat J_n-J_n^{bank}\) | 0.2470998783239713 |

The entire published decomposition error is thus accounted for by the
0.85-versus-0.636054 likelihood mismatch. It is not caused by \(n\ne m^*\)
and no residual bookkeeping discrepancy remains after comparing like with
like.

## Diagnostic conclusions

1. **Dose pathway:** refuted as authored. Association dose is outside the
   root matching pathway, so the monotone-dose matching criterion cannot
   measure its named construct.
2. **Tolerance tails:** 17 literal tolerance failures, all caused by
   off-lattice target crossings in the formed-bank population; none was
   censored and none had an attainable within-tolerance prefix through 8n.
3. **Decomposition:** the unequal-length telescoping identity is valid. The
   retained failure localizes to two different root likelihoods being used
   for the trajectory endpoint and the reported endpoint.

This document makes no repair or criterion-change recommendation; those
classifications are left for external adjudication.
