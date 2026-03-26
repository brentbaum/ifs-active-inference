"""
    ifs_polarization_model.jl - IFS Polarization Dynamics Model

Standalone dynamical systems model of two competing IFS part-bundles
showing how Self-energy (E_t) dampens polarization oscillations.

This implements the model described in Appendix B of the IFS-Active Inference paper:
- Part A (approach/attach): Priors favoring connection, disclosure
- Part B (withdraw/protect): Priors favoring distance, safety
- Competitive dynamics with mutual inhibition and fatigue
- Self-energy modulates competition intensity (not baseline drive)

The key design:
Self-energy does NOT suppress parts. Instead, it reduces the intensity
of winner-take-all competition (self-excitation λ and mutual inhibition κ).
This matches the IFS insight: Self doesn't silence parts, it reduces the
intensity with which they fight for control.

Effective competition coefficients:
    κ_eff = κ * (1 - E_t)     -- mutual inhibition decreases with Self-energy
    λ_eff = λ * (1 - E_t)     -- self-excitation decreases with Self-energy

Drive equations:
    drive_A = θ_A * cue_A - κ_eff * a_B + λ_eff * a_A - δ * f_A
    drive_B = θ_B * cue_B - κ_eff * a_A + λ_eff * a_B - δ * f_B

Activation update:
    a_A(t+1) = τ * a_A(t) + (1-τ) * σ(drive_A + noise)
    a_B(t+1) = τ * a_B(t) + (1-τ) * σ(drive_B + noise)

Fatigue update:
    f_A(t+1) = f_A(t) + ρ * a_A(t) - ψ * f_A(t)
    f_B(t+1) = f_B(t) + ρ * a_B(t) - ψ * f_B(t)

This produces the desired phenomenology:
- Low E_t: strong competition → one part captures → fatigue builds → flip → oscillation
- High E_t: weak competition → both parts maintain moderate activation → coexistence
"""

using Random
using Statistics

#==============================================================================#
# Types
#==============================================================================#

"""
Parameters for the polarization model.
"""
struct PolarizationParams
    # Part drives
    θ_A::Float64    # Baseline drive strength for Part A
    cue_A::Float64  # External cue strength for Part A
    θ_B::Float64    # Baseline drive strength for Part B
    cue_B::Float64  # External cue strength for Part B

    # Competition (modulated by Self-energy)
    κ::Float64      # Mutual inhibition coefficient (at E_t = 0)
    λ::Float64      # Self-excitation coefficient (at E_t = 0)

    # Fatigue
    δ::Float64      # Fatigue impact on drive
    ρ::Float64      # Fatigue accumulation rate
    ψ::Float64      # Fatigue decay rate

    # Dynamics
    τ::Float64        # Momentum / inertia (0 = instant response)
    σ_noise::Float64  # Activation noise standard deviation

    # Policy selection
    α_policy::Float64  # Policy precision (inverse temperature)
end

"""
    default_params()

Create default polarization parameters calibrated for dramatic visualization.

The parameters are tuned so that:
- Low E_t (0.1): rapid anti-phase oscillation driven by fatigue cycling
- Medium E_t (0.5): dampened oscillation, mixed policy emerging
- High E_t (0.9): stable coexistence, mixed policy dominant
"""
function default_params()
    PolarizationParams(
        # Part drives -- baseline activation drive
        1.2,    # θ_A: drive strength (slightly above center → sigmoid ~ 0.77 alone)
        1.0,    # cue_A: cue strength
        1.2,    # θ_B: drive strength (symmetric with A)
        1.0,    # cue_B: cue strength

        # Competition
        4.5,    # κ: mutual inhibition (strong winner-take-all at E_t=0)
        3.5,    # λ: self-excitation (reinforces dominance)

        # Fatigue
        2.8,    # δ: fatigue impact (strong enough to force switching)
        0.28,   # ρ: fatigue accumulation rate
        0.14,   # ψ: fatigue decay rate

        # Dynamics
        0.12,   # τ: momentum (lower = faster response)
        0.10,   # σ_noise: stochastic perturbation

        # Policy
        8.0     # α_policy: policy precision
    )
end

"""
State of the system at a single timestep.
"""
struct PolarizationState
    a_A::Float64            # Part A activation [0, 1]
    a_B::Float64            # Part B activation [0, 1]
    f_A::Float64            # Part A fatigue level
    f_B::Float64            # Part B fatigue level
    policy::Symbol          # :approach, :withdraw, or :mixed
    policy_probs::Vector{Float64}  # [p_approach, p_withdraw, p_mixed]
    policy_entropy::Float64 # Entropy of policy distribution
    capture_A::Float64      # Capture index for Part A
    capture_B::Float64      # Capture index for Part B
    simultaneous::Bool      # Both active, neither > 0.7
end

"""
Results from a full simulation run.
"""
struct PolarizationResults
    E_t::Float64                        # Self-energy level used
    params::PolarizationParams          # Model parameters
    states::Vector{PolarizationState}   # Per-timestep states
    n_timesteps::Int                    # Number of timesteps

    # Summary statistics
    oscillation_frequency::Float64      # Oscillation frequency of a_A
    switching_rate::Float64             # Rate of policy switches
    time_in_simultaneous::Float64       # Fraction of time in simultaneous representation
    time_to_negotiated::Int             # Timestep of first mixed policy (-1 if never)
    mean_anticorrelation::Float64       # Correlation between a_A and a_B
end

#==============================================================================#
# Core Dynamics
#==============================================================================#

"""
    sigmoid(x)

Standard logistic sigmoid function.
"""
sigmoid(x::Real) = 1.0 / (1.0 + exp(-x))

"""
    select_policy(a_A, a_B, α)

Select policy based on relative part activations.
Returns (policy_symbol, policy_probs).

Policy semantics:
- :approach  -- Part A's preferred action (connection, disclosure)
- :withdraw  -- Part B's preferred action (distance, protection)
- :mixed     -- Negotiated policy (both perspectives held simultaneously)
"""
function select_policy(a_A::Float64, a_B::Float64, α::Float64)
    # Policy utilities
    # Approach: driven by A's relative strength
    u_approach = a_A - 0.5 * a_B

    # Withdraw: driven by B's relative strength
    u_withdraw = a_B - 0.5 * a_A

    # Mixed: requires both parts to be moderately active and balanced.
    # The min(a_A, a_B) term ensures both must be active.
    # The -dominance term penalizes imbalance.
    dominance = abs(a_A - a_B)
    both_active = min(a_A, a_B)
    u_mixed = 2.0 * both_active - 1.5 * dominance - 0.3

    utilities = [u_approach, u_withdraw, u_mixed]

    # Softmax policy selection
    utilities_shifted = utilities .- maximum(utilities)
    exp_u = exp.(α .* utilities_shifted)
    probs = exp_u ./ sum(exp_u)

    # Deterministic selection (argmax)
    selected = argmax(probs)
    policies = [:approach, :withdraw, :mixed]

    return policies[selected], probs
end

"""
    compute_capture_index(a_own, a_other)

Capture index: how much one part dominates the system.
Range [0, 1] where 1 = complete takeover, 0 = no presence.
"""
function compute_capture_index(a_own::Float64, a_other::Float64)
    total = a_own + a_other
    if total < 1e-6
        return 0.0
    end
    (a_own / total) * a_own
end

"""
    policy_entropy(probs)

Shannon entropy of the policy distribution (in bits).
"""
function policy_entropy(probs::Vector{Float64})
    h = 0.0
    for p in probs
        if p > 1e-10
            h -= p * log2(p)
        end
    end
    return h
end

"""
    is_simultaneous(a_A, a_B; threshold=0.3, cap=0.7)

Check if both parts are simultaneously represented without takeover.
Both must be above `threshold` and neither above `cap`.
"""
function is_simultaneous(a_A::Float64, a_B::Float64;
                          threshold::Float64=0.3, cap::Float64=0.7)
    return a_A > threshold && a_B > threshold && a_A < cap && a_B < cap
end

#==============================================================================#
# Simulation
#==============================================================================#

"""
    run_polarization(E_t; params, n_timesteps, seed)

Run the polarization simulation for a given Self-energy level.

Self-energy modulates competition intensity, not baseline drive:
    κ_eff = κ * (1 - E_t)
    λ_eff = λ * (1 - E_t)

This means:
- At E_t = 0: full competition → aggressive winner-take-all → oscillation via fatigue
- At E_t = 1: zero competition → parts don't interfere → both at sigmoid(θ*cue) ≈ 0.5
- At E_t = 0.5: moderate competition → damped oscillation with some coexistence
"""
function run_polarization(
    E_t::Float64;
    params::PolarizationParams=default_params(),
    n_timesteps::Int=80,
    seed::Int=42
)
    Random.seed!(seed)

    states = PolarizationState[]

    # Initial conditions: slight asymmetry to break symmetry
    a_A = 0.55
    a_B = 0.45

    # Fatigue state
    f_A = 0.0
    f_B = 0.0

    # Effective competition coefficients (Self-energy modulates competition)
    κ_eff = params.κ * (1.0 - E_t)
    λ_eff = params.λ * (1.0 - E_t)

    for t in 1:n_timesteps
        # --- Select policy based on current activations ---
        policy, probs = select_policy(a_A, a_B, params.α_policy)
        h = policy_entropy(probs)

        # --- Compute dependent measures ---
        cap_A = compute_capture_index(a_A, a_B)
        cap_B = compute_capture_index(a_B, a_A)
        simul = is_simultaneous(a_A, a_B)

        # Store state
        push!(states, PolarizationState(a_A, a_B, f_A, f_B, policy, copy(probs),
                                         h, cap_A, cap_B, simul))

        # --- Compute next activations ---
        # Drive = baseline + self-excitation - mutual inhibition - fatigue
        # Self-energy reduces competition (κ_eff, λ_eff) but not baseline drive
        drive_A = params.θ_A * params.cue_A + λ_eff * a_A - κ_eff * a_B - params.δ * f_A
        drive_B = params.θ_B * params.cue_B + λ_eff * a_B - κ_eff * a_A - params.δ * f_B

        # Stochastic noise
        noise_A = params.σ_noise * randn()
        noise_B = params.σ_noise * randn()

        a_A_next = sigmoid(drive_A + noise_A)
        a_B_next = sigmoid(drive_B + noise_B)

        # Momentum: smooth transitions
        a_A = params.τ * a_A + (1.0 - params.τ) * a_A_next
        a_B = params.τ * a_B + (1.0 - params.τ) * a_B_next
        a_A = clamp(a_A, 0.0, 1.0)
        a_B = clamp(a_B, 0.0, 1.0)

        # Update fatigue
        f_A = f_A + params.ρ * a_A - params.ψ * f_A
        f_B = f_B + params.ρ * a_B - params.ψ * f_B
        f_A = max(f_A, 0.0)
        f_B = max(f_B, 0.0)
    end

    # --- Compute summary statistics ---
    activations_A = [s.a_A for s in states]
    activations_B = [s.a_B for s in states]
    policies = [s.policy for s in states]

    # Oscillation frequency: count zero-crossings of (a_A - mean(a_A))
    mean_A = mean(activations_A)
    centered_A = activations_A .- mean_A
    zero_crossings = 0
    for i in 2:n_timesteps
        if centered_A[i] * centered_A[i-1] < 0
            zero_crossings += 1
        end
    end
    osc_freq = zero_crossings / (2.0 * n_timesteps)

    # Switching rate: fraction of timesteps where policy changes
    switches = 0
    for i in 2:n_timesteps
        if policies[i] != policies[i-1]
            switches += 1
        end
    end
    switch_rate = switches / (n_timesteps - 1)

    # Time in simultaneous representation
    simul_count = count(s -> s.simultaneous, states)
    time_simul = simul_count / n_timesteps

    # Time to first negotiated (mixed) policy
    time_to_neg = -1
    for (i, s) in enumerate(states)
        if s.policy == :mixed
            time_to_neg = i
            break
        end
    end

    # Correlation between a_A and a_B
    if length(activations_A) > 1
        mean_B = mean(activations_B)
        centered_B = activations_B .- mean_B
        var_A = sum(centered_A .^ 2)
        var_B = sum(centered_B .^ 2)
        if var_A > 1e-10 && var_B > 1e-10
            corr = sum(centered_A .* centered_B) / sqrt(var_A * var_B)
        else
            corr = 0.0
        end
    else
        corr = 0.0
    end

    return PolarizationResults(
        E_t, params, states, n_timesteps,
        osc_freq, switch_rate, time_simul, time_to_neg, corr
    )
end

"""
    run_all_conditions(; params, n_timesteps, seed)

Run polarization simulation for low, medium, and high Self-energy.
"""
function run_all_conditions(;
    params::PolarizationParams=default_params(),
    n_timesteps::Int=80,
    seed::Int=42
)
    conditions = Dict{Symbol, PolarizationResults}()
    conditions[:low] = run_polarization(0.1; params=params, n_timesteps=n_timesteps, seed=seed)
    conditions[:medium] = run_polarization(0.5; params=params, n_timesteps=n_timesteps, seed=seed)
    conditions[:high] = run_polarization(0.9; params=params, n_timesteps=n_timesteps, seed=seed)
    return conditions
end

"""
    print_summary(results::PolarizationResults)

Print summary statistics for a simulation run.
"""
function print_summary(results::PolarizationResults)
    println("  Self-energy E_t = $(results.E_t)")
    println("  Oscillation frequency: $(round(results.oscillation_frequency, digits=4))")
    println("  Switching rate: $(round(results.switching_rate, digits=4))")
    println("  Time in simultaneous repr: $(round(results.time_in_simultaneous * 100, digits=1))%")
    println("  Time to first mixed policy: $(results.time_to_negotiated == -1 ? "never" : string(results.time_to_negotiated))")
    println("  A-B correlation: $(round(results.mean_anticorrelation, digits=4))")

    policies = [s.policy for s in results.states]
    n = length(policies)
    n_approach = count(p -> p == :approach, policies)
    n_withdraw = count(p -> p == :withdraw, policies)
    n_mixed = count(p -> p == :mixed, policies)
    println("  Policy breakdown: approach=$(round(100*n_approach/n, digits=1))% withdraw=$(round(100*n_withdraw/n, digits=1))% mixed=$(round(100*n_mixed/n, digits=1))%")
end

"""
    print_all_summaries(conditions::Dict{Symbol, PolarizationResults})

Print summary statistics for all conditions.
"""
function print_all_summaries(conditions::Dict{Symbol, PolarizationResults})
    println("=" ^ 65)
    println("IFS Polarization Simulation - Summary Statistics")
    println("=" ^ 65)

    for (label, name) in [(:low, "Low Self-Energy (E=0.1)"),
                           (:medium, "Medium Self-Energy (E=0.5)"),
                           (:high, "High Self-Energy (E=0.9)")]
        println("\n--- $name ---")
        print_summary(conditions[label])
    end

    println("\n" * "=" ^ 65)
end
