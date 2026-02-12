"""
    model.jl - IFS Spider Phobia Active Inference Model

Model construction for the CBT spider exposure therapy simulation.
Based on the MATLAB implementation from the Scientific Reports paper.
"""

using LinearAlgebra

"""
    ModelParams

Simulation parameters for the IFS active inference model.
"""
Base.@kwdef struct ModelParams
    CABi::Float64 = 0.9      # Cognitive-Affective Belief interaction
    Psafe::Float64 = 0.1     # Prior probability spider is safe
    N::Int = 200             # Number of trials
    T::Int = 4               # Time steps per trial
end

"""
    create_initial_state_priors(params::ModelParams)

Create D (categorical priors) and d (Dirichlet concentration parameters)
for the initial hidden state distribution.

Returns: (D, d) where D is normalized probabilities and d is Dirichlet counts.
"""
function create_initial_state_priors(params::ModelParams)
    # D: Initial state priors (categorical)
    D = Vector{Vector{Float64}}(undef, 3)
    D[1] = [1.0, 0, 0, 0, 0, 0]  # Factor 1: start/stim/approach/interact/avoid/safety+cost
    D[2] = [0.0, 1.0]            # Factor 2: no spider / spider
    D[3] = [0.0, 1.0]            # Factor 3: dangerous / safe

    # d: Explicit Dirichlet beliefs over initial states
    d = deepcopy(D)
    d[2] = [1.0, 1.0]                        # Uncertain about spider presence
    d[3] = [1 - params.Psafe, params.Psafe]  # Prior belief about safety

    # Scale to Dirichlet concentration parameters
    d[1] .*= 128
    d[2] .*= 128
    d[3] .*= 50

    return D, d
end

"""
    create_observation_model(Ns::Vector{Int}, No::Vector{Int}, params::ModelParams)

Create A (observation likelihood) and a (Dirichlet concentration parameters)
matrices for mapping hidden states to observations.

Modalities:
1. Visual (spider/no spider)
2. Arousal (low/high)
3. Affective consequences (neutral/negative/harm)
4. Behavioral state (identity mapping)

Returns: (A, a) where A is normalized and a is Dirichlet counts.
"""
function create_observation_model(Ns::Vector{Int}, No::Vector{Int}, params::ModelParams)
    Ng = length(No)

    # Initialize A matrices: state->observation mappings
    A = Vector{Array{Float64}}(undef, Ng)
    for g in 1:Ng
        A[g] = zeros(No[g], Ns...)  # dims: (No[g], Ns[1], Ns[2], Ns[3])
    end

    # --- A[1]: Visual observations (spider presence) ---
    # No spider present (factor 2 = 1)
    A[1][:, :, 1, 1] .= [1 1 1 1 1 1;   # see nothing
                        0 0 0 0 0 0]    # see spider
    A[1][:, :, 1, 2] .= [1 1 1 1 1 1;
                        0 0 0 0 0 0]
    # Spider present (factor 2 = 2)
    A[1][:, :, 2, 1] .= [1 0 0 0 0 0;   # only see nothing at start
                        0 1 1 1 1 1]    # see spider otherwise
    A[1][:, :, 2, 2] .= [1 0 0 0 0 0;
                        0 1 1 1 1 1]

    # --- A[2]: Arousal observations ---
    # No spider
    A[2][:, :, 1, 1] .= [1 1 1 1 0 1;   # low arousal
                        0 0 0 0 1 0]    # high arousal (at avoid state)
    A[2][:, :, 1, 2] .= [1 1 1 1 0 1;
                        0 0 0 0 1 0]
    # Spider present
    A[2][:, :, 2, 1] .= [1 0 1 1 0 1;   # low arousal
                        0 1 0 0 1 0]    # high arousal at stim or avoid
    A[2][:, :, 2, 2] .= [1 0 1 1 0 1;
                        0 1 0 0 1 0]

    # --- A[3]: Affective consequences ---
    # No spider - all neutral/negative, no harm possible
    A[3][:, :, 1, 1] .= [1 1 1 1 0 0;   # neutral
                        0 0 0 0 1 1;    # negative
                        0 0 0 0 0 0]    # harm (never)
    A[3][:, :, 1, 2] .= [1 1 1 1 0 0;
                        0 0 0 0 1 1;
                        0 0 0 0 0 0]
    # Spider + dangerous - can experience harm at interact
    A[3][:, :, 2, 1] .= [1 1 0 0 0 0;   # neutral
                        0 0 1 0 1 1;    # negative
                        0 0 0 1 0 0]    # harm (at interact state)
    # Spider + safe - no harm possible
    A[3][:, :, 2, 2] .= [1 1 1 1 0 0;
                        0 0 0 0 1 1;
                        0 0 0 0 0 0]

    # --- A[4]: Behavioral observations = identity over factor 1 ---
    for i in 1:2, j in 1:2
        A[4][:, :, i, j] .= Matrix{Float64}(I, 6, 6)
    end

    # --- a: Dirichlet concentration parameters for learning A ---
    a = deepcopy(A)
    a[1] .*= 128  # Fixed visual mapping
    a[2] .*= 128  # Fixed arousal mapping
    a[4] .*= 128  # Fixed behavioral mapping

    # a[3]: Learnable affective consequences
    # Spider + dangerous - uncertain about consequences
    a[3][:, :, 2, 1] .= [1   1   0.1  0.1  0   0;
                        0   0   0.9  0    1   1;
                        0   0   0    0.9  0   0]
    # Spider + safe - beliefs modulated by CABi
    a[3][:, :, 2, 2] .= [1   1   params.CABi      params.CABi      0               0;
                        0   0   (1-params.CABi)  0                1               1;
                        0   0   0                (1-params.CABi)  0               0]
    a[3] .*= 5  # Moderate concentration

    return A, a
end

"""
    create_transition_model(Ns::Vector{Int})

Create B matrices for state transitions.
Factor 1 is controllable (approach vs avoid actions).
Factors 2 and 3 are fixed (spider presence and dangerousness don't change).

Returns: B::Vector{Array{Float64,3}}
"""
function create_transition_model(Ns::Vector{Int})
    Nf = length(Ns)
    B = Vector{Array{Float64,3}}(undef, Nf)

    # --- B[1]: Factor 1 transitions (controllable) ---
    # States: 1=start, 2=stim, 3=approach, 4=interact, 5=avoid, 6=safety+cost
    B[1] = zeros(6, 6, 2)

    # Action 1: Approach
    B[1][:, :, 1] .= [0 0 0 0 0 0;  # can't return to start
                     1 0 0 0 0 0;  # start -> stim
                     0 1 0 0 0 0;  # stim -> approach
                     0 0 1 1 1 1;  # approach/interact/avoid/safety -> interact
                     0 0 0 0 0 0;
                     0 0 0 0 0 0]

    # Action 2: Avoid
    B[1][:, :, 2] .= [0 0 0 0 0 0;
                     1 0 0 0 0 0;  # start -> stim
                     0 0 0 0 0 0;
                     0 0 0 0 0 0;
                     0 1 0 0 0 0;  # stim -> avoid
                     0 0 1 1 1 1]  # approach/interact/avoid/safety -> safety+cost

    # --- B[2] and B[3]: Identity transitions (no control) ---
    B[2] = reshape(Matrix{Float64}(I, 2, 2), 2, 2, 1)
    B[3] = reshape(Matrix{Float64}(I, 2, 2), 2, 2, 1)

    return B
end

"""
    create_policies(T::Int)

Create policy matrix V specifying action sequences.
Two policies: approach (always action 1) and avoid (always action 2).

Returns: V::Array{Int,3} of shape (T-1, Np, Nf)
"""
function create_policies(T::Int)
    Np = 2   # Number of policies
    Nf = 3   # Number of factors

    V = ones(Int, T - 1, Np, Nf)
    V[:, 1, 1] .= 1  # Policy 1: approach (action 1 on factor 1)
    V[:, 2, 1] .= 2  # Policy 2: avoid (action 2 on factor 1)

    return V
end

"""
    create_preferences(No::Vector{Int}, T::Int)

Create C matrices encoding outcome preferences.
Prefers low arousal and neutral affect, strongly dislikes harm.

Returns: C::Vector{Matrix{Float64}}
"""
function create_preferences(No::Vector{Int}, T::Int)
    Ng = length(No)
    C = [zeros(No[g], T) for g in 1:Ng]

    # C[1]: No preference for visual observations

    # C[2]: Dislike high arousal
    C[2][2, :] .-= 1

    # C[3]: Dislike negative affect, strongly dislike harm
    C[3][2, :] .-= 1   # Negative affect
    C[3][3, :] .-= 12  # Harm (strong aversion)

    return C
end

"""
    create_policy_prior(Np::Int)

Create E (prior over policies) - uniform by default.

Returns: E::Vector{Float64}
"""
function create_policy_prior(Np::Int)
    return ones(Np)
end

"""
    build_model(; params::ModelParams = ModelParams())

Construct the complete IFS Active Inference generative model.

Returns: NamedTuple with all model components.
"""
function build_model(; params::ModelParams = ModelParams())
    # State and observation dimensions
    D, d = create_initial_state_priors(params)
    Ns = length.(D)         # [6, 2, 2]
    No = [2, 2, 3, 6]       # Outcomes per modality
    Ng = length(No)
    Nf = length(D)

    # Model components
    A, a = create_observation_model(Ns, No, params)
    B = create_transition_model(Ns)
    V = create_policies(params.T)
    C = create_preferences(No, params.T)
    E = create_policy_prior(2)

    # Control structure
    controls = [2, 1, 1]  # Number of control states per factor

    return (
        # Dimensions
        Ns = Ns,
        No = No,
        Ng = Ng,
        Nf = Nf,
        T = params.T,
        # Generative model
        A = A,
        B = B,
        C = C,
        D = D,
        E = E,
        V = V,
        # Dirichlet priors (for learning)
        a = a,
        d = d,
        # Parameters
        controls = controls,
        params = params,
    )
end

"""
    softmax_tau(x; tau=1.0, dims=1)

Temperature-scaled softmax along specified dimension.
Equivalent to MATLAB's spm_softmax(x, tau).
"""
function softmax_tau(x::AbstractArray; tau::Real = 1.0, dims::Int = 1)
    xshift = x .- maximum(x; dims = dims)
    ex = exp.(xshift ./ tau)
    return ex ./ sum(ex; dims = dims)
end

"""
    normalize_columns(x)

Normalize array along first dimension (columns sum to 1).
"""
function normalize_columns(x::AbstractArray)
    s = sum(x; dims = 1)
    s[s .== 0] .= 1  # Avoid division by zero
    return x ./ s
end
