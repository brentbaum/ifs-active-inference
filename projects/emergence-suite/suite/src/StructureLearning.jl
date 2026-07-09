module StructureLearning

export CRPSpawnProposal, propose_crp_spawn

"""
    CRPSpawnProposal(factor, concentration, posterior_predictive, threshold)

Typed seam for latent-cause growth. T1.2 should replace the stub with the CRP
spawn rule while preserving explicit logging of structural precision changes.
"""
struct CRPSpawnProposal{T<:Real}
    factor::Symbol
    concentration::T
    posterior_predictive::T
    threshold::T
end

"""
    propose_crp_spawn(args...; kwargs...)

Stub for dynamic state-space growth. Returns `nothing` until T1.2 defines the
actual CRP proposal contract.
"""
function propose_crp_spawn(args...; kwargs...)
    return nothing
end

end
