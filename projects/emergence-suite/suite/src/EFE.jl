module EFE

export Policy, PolicyScore

"""
    Policy(actions)

Typed placeholder for an action sequence scored by expected free energy.
Concrete policy scoring for T1.1+ should port the v10 EFE terms here.
"""
struct Policy
    actions::Vector{Int}
end

"""
    PolicyScore(policy, utility, ambiguity, information_gain, total)

Audit-friendly decomposition seam for policy scoring. Keeping the terms
separate makes later R2/R3 checks easier because E_t effects should enter only
through effective precision, not through bonus terms.
"""
struct PolicyScore{T<:Real}
    policy::Policy
    utility::T
    ambiguity::T
    information_gain::T
    total::T
end

end
