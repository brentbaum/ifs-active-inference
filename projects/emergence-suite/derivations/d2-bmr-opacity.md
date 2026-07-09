# D2: Bayesian model reduction requires opacified representation

## Setup

Let `c` denote the coupling parameters that bind a bundle's root state to the
rest of its learned role. The full model `M_F` keeps the coupling. The reduced
model `M_R` prunes that coupling while retaining the competence banks.

For a Dirichlet component,

```text
p_F(c) = Dir(c; b_F)
p_R(c) = Dir(c; b_R)
q_E(c) = Dir(c; a_E)
```

Bayesian model reduction compares the reduced and full models using the
posterior under the full model:

```text
delta_F_R-F(E) = log int q_E(c) p_R(c) / p_F(c) dc
```

For Dirichlet parameters this is

```text
delta_F_R-F(E)
  = log B(b_F) - log B(b_R)
    + log B(a_E + b_R - b_F) - log B(a_E)
```

where `B(alpha) = prod_i Gamma(alpha_i) / Gamma(sum_i alpha_i)`. Positive
`delta_F_R-F` favors pruning, before adding any model prior odds.

The question is what `q_E(c)` is when reflexivity is collapsed. The paper's
mechanism says that `E_t` is the precision of the reflexive observation channel
`o_self`. High `E_t` means the active bundle is represented as "this bundle, here,
as a hypothesis". Collapsed `E_t` means the bundle functions transparently as
the current reality model rather than appearing as an object inside the model.

## Two readings

### Reading (i): architectural substrate

BMR is a comparison over a represented component. It requires an addressable
posterior such as

```text
q(c | H_B, o_self, o_ext)
```

where `H_B` is the hypothesis that this active configuration is the bundle being
evaluated. If the architecture has no precise reflexive representation of
`H_B`, then the agent has no internal variable whose coupling can be reduced.
An external analyst may still point at a learned count table and compute a
number, but the agent cannot compute or act on that number as a reduction of
"this bundle".

This supports the strong sentence:

```text
Transparent prior: no represented component, so no agent-internal BMR target.
Opacified prior: represented component, so BMR has a substrate.
```

In this reading, "only an opacified prior can revise" is an architectural
theorem about the location of the posterior. The theorem is not that the raw
counts disappear. It is that, under transparency, the counts are not bound to a
self-model hypothesis that the agent can reduce.

### Reading (ii): inferential degeneration

The stronger inferential reading says that `delta_F` itself degenerates as
`E_t -> 0`. This does not follow from vanilla BMR alone.

Obstruction: if `a` is a raw learned Dirichlet count table already present in
the full model, then

```text
delta_F_R-F = log B(b_F) - log B(b_R)
              + log B(a + b_R - b_F) - log B(a)
```

contains no `E_t` term. Current reflexive precision changes effective precision
and representation, but it does not automatically erase structural counts. This
matters because the global conventions distinguish structural precision from
fast effective precision. Therefore, a T1.3 implementation that runs BMR over
externally addressed raw counts would be imposing a melt gate if it additionally
blocked pruning at low `E_t`.

The inferential reading is derivable only with one additional modeling premise:
the posterior used by agent-internal BMR is the reflexively accessible posterior.
That is,

```text
a_E = b_F + rho(E_t) n
```

where `n` are the sufficient statistics for the coupling as a self-indexed
component, and `rho(E_t)` is an increasing accessibility or effective sample-size
function with

```text
rho(0) = 0
lim_E->infty rho(E) = 1
```

A convenient saturating form is

```text
rho(E) = E / (E + E_0)
```

The exact saturating function is not essential. The essential constraint is
that collapsed reflexivity supplies zero self-indexed evidence for the component
as a reducible hypothesis.

## Derived graded form

With `a_E = b_F + rho(E) n`, the BMR score becomes

```text
delta_F_R-F(E)
  = log B(b_F) - log B(b_R)
    + log B(b_R + rho(E) n) - log B(b_F + rho(E) n)
```

At collapsed reflexivity,

```text
delta_F_R-F(0)
  = log B(b_F) - log B(b_R) + log B(b_R) - log B(b_F)
  = 0
```

So the comparison carries no data-driven information about whether to prune.
Only model prior odds remain.

The slope with respect to accessible evidence is

```text
d delta_F / d rho
  = sum_i n_i [
      psi(b_R_i + rho n_i) - psi(sum_j b_R_j + rho N)
      - psi(b_F_i + rho n_i) + psi(sum_j b_F_j + rho N)
    ]
```

where `N = sum_i n_i` and `psi` is the digamma function. This is the difference
between the reduced and full priors' expected log likelihood for the accessible
coupling statistics. If the witnessed evidence is better predicted by the
reduced prior than by the full coupling prior, the slope is positive over the
relevant range and `delta_F_R-F(E)` increases with reflexivity. If the burdened
coupling still predicts the data better, the slope is negative and pruning loses.

This gives the threshold form:

```text
Prune when delta_F_R-F(E_t) + log[p(M_R) / p(M_F)] > 0.
```

Equivalently, for a required margin `kappa`,

```text
E_t >= E_star,
where E_star = min E such that delta_F_R-F(E) >= kappa.
```

If `rho(E) = E / (E + E_0)`, then `E_star = E_0 rho_star / (1 - rho_star)`,
where `rho_star` is the corresponding accessible-evidence threshold.

## Interpretation

This derivation supports reading (i) unconditionally, given the spec's
definition of transparency: collapsed `o_self` precision means no precise
posterior over "this bundle as hypothesis", so agent-internal BMR lacks its
substrate.

It supports reading (ii) conditionally. The degeneration
`delta_F_R-F(0) = 0` follows if, and only if, the posterior used by BMR is the
self-indexed/reflexively accessible posterior. It does not follow for an
observer-run BMR calculation over raw structural counts.

## Consequence for Sim 2

T1.3 has two coherent implementation choices:

1. Agent-internal BMR: compute BMR over `a_E = b_F + rho(E_t) n_self`, where
   `n_self` are the counts bound to the opacified bundle representation. Then the
   melt gate is derived. Low `E_t` gives an uninformative comparison; high `E_t`
   gives the BMR score enough substrate to pass the prune threshold when the
   witnessed evidence supports reduction.

2. External BMR over raw counts: compute BMR over the learned Dirichlet counts
   regardless of `E_t`. Then any additional "do not prune unless witnessed" rule
   is imposed and should be logged as an IOU/magic-number gate in T1.3.

Recommended status for the suite: D2 lands for the architectural claim and for a
graded inferential implementation that uses reflexively accessible counts. It
does not prove that every possible raw-count BMR implementation must degenerate
under transparency.
