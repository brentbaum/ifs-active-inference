module BMR

export bmr_delta_f_pooled_evidence,
       bmr_delta_f_prior_swap,
       accessibility_weight,
       dirichlet_log_evidence,
       logbeta,
       reflexive_prior_swap_delta,
       reflexivity_weight

const EPS = 1e-12

function loggamma_lanczos(z::Float64)
    coeffs = (
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    )
    if z < 0.5
        return log(pi) - log(sin(pi * z)) - loggamma_lanczos(1.0 - z)
    end
    z -= 1.0
    x = 0.99999999999980993
    for (i, c) in enumerate(coeffs)
        x += c / (z + i)
    end
    t = z + length(coeffs) - 0.5
    return 0.5 * log(2pi) + (z + 0.5) * log(t) - t + log(x)
end

"""
    logbeta(alpha)

Log multivariate beta function for positive Dirichlet parameters.
"""
function logbeta(alpha)
    vals = Float64.(alpha)
    any(vals .<= 0.0) && error("Dirichlet parameters must be positive")
    return sum(loggamma_lanczos, vals) - loggamma_lanczos(sum(vals))
end

"""
    dirichlet_log_evidence(counts, prior)

Column-wise Dirichlet marginal likelihood contribution.
"""
function dirichlet_log_evidence(counts, prior)
    size(counts) == size(prior) || error("counts and prior must have matching shapes")
    total = 0.0
    for idx in CartesianIndices(size(counts)[2:end])
        c = counts[:, idx]
        p = prior[:, idx]
        total += logbeta(c .+ p) - logbeta(p)
    end
    return total
end

"""
    bmr_delta_f_pooled_evidence(counts)

Corrected pooled-evidence tying reduction from the T0.1 spike review. The
return value is `log p(y | reduced) - log p(y | full)`; positive favors the
reduced tied model.
"""
function bmr_delta_f_pooled_evidence(counts)
    size(counts, 2) < 2 && return 0.0
    a = ones(size(counts, 1))
    total = 0.0
    for rest in CartesianIndices(size(counts)[3:end])
        n1 = counts[:, 1, Tuple(rest)...] .- 1.0
        n2 = counts[:, 2, Tuple(rest)...] .- 1.0
        total += logbeta(a .+ n1 .+ n2) - logbeta(a .+ n1) - logbeta(a .+ n2) + logbeta(a)
    end
    return total
end

"""
    bmr_delta_f_prior_swap(post, full_prior, reduced_prior)

Canonical Friston-2017 prior-swap BMR over Dirichlet posterior counts. The
return value is `log p(y | reduced) - log p(y | full)`; positive favors the
reduced model. This is the T1.3 form and matches `derivations/d2_toy_demo.py`.
"""
function bmr_delta_f_prior_swap(post, full_prior, reduced_prior)
    size(post) == size(full_prior) == size(reduced_prior) || error("post, full_prior, and reduced_prior must have matching shapes")
    total = 0.0
    for idx in CartesianIndices(size(post)[2:end])
        p = post[:, idx]
        f = full_prior[:, idx]
        r = reduced_prior[:, idx]
        reduced_post = p .+ r .- f
        any(reduced_post .<= 0.0) && error("Reduced posterior parameters must stay positive")
        total += logbeta(f) - logbeta(r) + logbeta(reduced_post) - logbeta(p)
    end
    return total
end

"""
    reflexivity_weight(E; E0 = 1.0)

Saturating D2 toy-demo mapping from reflexivity precision to accessible
evidence fraction. At `E <= 0`, no data-driven BMR comparison is available.
"""
function accessibility_weight(E::Real; form::Symbol = :saturating, E0::Real = 1.0, threshold::Real = 0.2, full_access::Real = 0.8)
    value = Float64(E)
    if form == :saturating
        E0 > 0 || error("E0 must be positive")
        value <= 0 && return 0.0
        return value / (value + Float64(E0))
    elseif form == :threshold_linear
        full_access > threshold || error("full_access must exceed threshold")
        return clamp((value - Float64(threshold)) / (Float64(full_access) - Float64(threshold)), 0.0, 1.0)
    end
    error("Unknown accessibility form: $form")
end

function reflexivity_weight(E::Real; E0::Real = 1.0)
    return accessibility_weight(E; form = :saturating, E0 = E0)
end

"""
    reflexive_prior_swap_delta(full_prior, reduced_prior, counts, E; E0 = 1.0)

D2 toy-demo helper: builds `post = full_prior + rho(E) * counts` and evaluates
the canonical prior-swap BMR.
"""
function reflexive_prior_swap_delta(full_prior, reduced_prior, counts, E; E0 = 1.0, form::Symbol = :saturating, threshold::Real = 0.2, full_access::Real = 0.8)
    rho = accessibility_weight(E; form = form, E0 = E0, threshold = threshold, full_access = full_access)
    post = full_prior .+ rho .* counts
    return bmr_delta_f_prior_swap(post, full_prior, reduced_prior)
end

end
