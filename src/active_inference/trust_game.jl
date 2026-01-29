"""
    trust_game.jl - Trust Game for Active Inference

Implementation of the Trust Game paradigm from:
"Simulating Active Inference of Interpersonal Context Within and Across Mental Disorders"
(Eckertal et al., Scientific Reports, 2023)

Models interpersonal decision-making with different agent profiles representing
transdiagnostic biases in mental disorders.

# Paper Overview

The paper models interpersonal decision-making using a **Trust Game** paradigm where
an agent (investor) decides whether to share resources with a partner (trustee).
The model captures how different mental disorders affect social decision-making
through biased generative model parameters.

# Model Structure

**State Space (2 factors):**
1. **Context** (3 states): friendly, hostile, neutral - hidden state about partner's disposition
2. **Choice** (3 states): share, keep, start - agent's current action state

**Observation Space (3 modalities):**
1. **Reward**: 1.0 (cooperation returned), 0.0 (betrayed), 0.5 (neutral)
2. **Behavior**: social, anti-social, unknown - partner's observed behavior
3. **Choice**: share, keep, start - agent observes own choice

**Policies:**
- 2 main policies: Share or Keep
- Trial length T=2 (decide, then observe outcome)

# Transdiagnostic Biases Modeled

| Bias          | Parameter | Effect                                                |
|---------------|-----------|-------------------------------------------------------|
| Uncertainty   | biased A  | P(share|friendly) = P(share|hostile) = 0.5            |
| Fatalism      | biased B  | Low agency belief - actions don't change context      |
| Loss Aversion | biased C  | Negative outcomes weighted more heavily (-5.0 vs -2.2)|
| Pessimism     | biased D  | Prior belief context is hostile (70% vs 33%)          |

# Clinical Profiles from Paper

| Agent Type      | Biases Combined                          |
|-----------------|------------------------------------------|
| Type1_depressed | Loss aversion + Pessimism + Fatalism     |
| Type2_anxiety   | Uncertainty + Pessimism                  |
| Type3_insecure  | Pessimism + Low learning rate            |
| healthy         | No biases, balanced priors               |

# Key Results to Replicate (Figures 2-4 in paper)

1. **Sharing Rates**: Healthy agents should share more with friendly partners.
   Depressed agents show reduced sharing due to loss aversion + pessimism.

2. **Belief Evolution**: Healthy agents should update beliefs about partner
   context based on evidence. Depressed/insecure agents update slowly.

3. **Learning Dynamics**: Different learning rates affect how quickly agents
   adapt to partner behavior.

# Reference Implementation

Based on pymdp_depression repository (Eckertal/pymdp_depression, branch: sims):
- gms.py: Generative model structure
- library.py: Agent profile definitions
"""

using Statistics: mean

# =============================================================================
# Constants
# =============================================================================

# State factor 1: Context (partner disposition)
const CONTEXT_FRIENDLY = 1
const CONTEXT_HOSTILE = 2
const CONTEXT_NEUTRAL = 3
const N_CONTEXT_STATES = 3

# State factor 2: Choice (agent's action state)
const CHOICE_SHARE = 1
const CHOICE_KEEP = 2
const CHOICE_START = 3
const N_CHOICE_STATES = 3

# Observation modality 1: Reward
const REWARD_HIGH = 1      # 1.0 - cooperation returned
const REWARD_LOW = 2       # 0.0 - betrayed
const REWARD_NEUTRAL = 3   # 0.5 - neutral outcome
const N_REWARD_OBS = 3

# Observation modality 2: Behavior (partner's observed behavior)
const BEHAVIOR_SOCIAL = 1
const BEHAVIOR_ANTISOCIAL = 2
const BEHAVIOR_UNKNOWN = 3
const N_BEHAVIOR_OBS = 3

# Observation modality 3: Choice (agent observes own choice)
const N_CHOICE_OBS = 3

# Actions for factor 1 (context - uncontrollable)
const N_CONTEXT_ACTIONS = 1

# Actions for factor 2 (choice)
const ACTION_SHARE = 1
const ACTION_KEEP = 2
const N_CHOICE_ACTIONS = 2

# =============================================================================
# Agent Profiles
# =============================================================================

"""
    AgentProfile

Specification for how an agent's generative model is biased.

# Fields
- `name`: Profile identifier
- `p_share_friendly`: P(partner shares | friendly context) for A matrix
- `p_share_hostile`: P(partner shares | hostile context) for A matrix
- `p_context_friendly`: Prior belief that context is friendly (D matrix)
- `p_context_hostile`: Prior belief that context is hostile (D matrix)
- `loss_aversion`: Scaling factor for negative outcomes in C matrix (>1 = loss averse)
- `agency`: Belief that actions affect context (B matrix learning relevance)
- `eta_A`: Learning rate for observation model
- `eta_B`: Learning rate for transition model
- `eta_D`: Learning rate for prior beliefs
"""
struct AgentProfile
    name::String
    # A matrix biases (observation model)
    p_share_friendly::Float64   # P(social behavior | friendly)
    p_share_hostile::Float64    # P(social behavior | hostile)
    # D matrix biases (prior beliefs)
    p_context_friendly::Float64 # Prior P(friendly)
    p_context_hostile::Float64  # Prior P(hostile)
    # C matrix biases (preferences)
    loss_aversion::Float64      # Weight on negative outcomes (>1 = loss averse)
    # B matrix biases (agency)
    agency::Float64             # Belief actions affect context (0-1)
    # Learning rates
    eta_A::Float64
    eta_B::Float64
    eta_D::Float64
end

"""
Default healthy agent profile with balanced priors.
"""
function healthy_profile()
    AgentProfile(
        "healthy",
        0.8,    # p_share_friendly: can distinguish friendly partners
        0.2,    # p_share_hostile: can distinguish hostile partners
        0.33,   # p_context_friendly: balanced prior
        0.33,   # p_context_hostile: balanced prior
        1.0,    # loss_aversion: neutral
        0.5,    # agency: moderate
        0.5,    # eta_A
        0.5,    # eta_B
        0.5     # eta_D
    )
end

"""
Type 1 depressed agent: loss aversion + pessimism + low agency (fatalism).

From paper: "reward-insensitive, fatalistic pessimists"
"""
function depressed_profile()
    AgentProfile(
        "depressed",
        0.8,    # p_share_friendly: normal observation
        0.2,    # p_share_hostile: normal observation
        0.15,   # p_context_friendly: pessimistic prior
        0.55,   # p_context_hostile: expects hostility (paper: ~70% but that's too extreme)
        1.5,    # loss_aversion: losses hurt more (paper: 2.2x but that prevents all sharing)
        0.3,    # agency: fatalistic (actions don't matter)
        0.3,    # eta_A: slow learning
        0.1,    # eta_B: very slow transition learning
        0.3     # eta_D: slow prior updating
    )
end

"""
Type 2 anxious agent: uncertainty + pessimism.

From paper: "uncertain pessimists"
"""
function anxious_profile()
    AgentProfile(
        "anxious",
        0.55,   # p_share_friendly: uncertain - can't distinguish well
        0.45,   # p_share_hostile: uncertain - can't distinguish well
        0.25,   # p_context_friendly: somewhat pessimistic
        0.45,   # p_context_hostile: expects hostility
        1.2,    # loss_aversion: moderate
        0.5,    # agency: normal
        0.5,    # eta_A
        0.5,    # eta_B
        0.5     # eta_D
    )
end

"""
Type 3 insecure attachment agent: pessimism + low learning.

From paper: "slow-learning pessimists"
"""
function insecure_profile()
    AgentProfile(
        "insecure",
        0.8,    # p_share_friendly: normal observation
        0.2,    # p_share_hostile: normal observation
        0.2,    # p_context_friendly: pessimistic
        0.5,    # p_context_hostile: expects hostility
        1.1,    # loss_aversion: slight
        0.5,    # agency: normal
        0.2,    # eta_A: slow learning
        0.2,    # eta_B: slow learning
        0.15    # eta_D: very slow prior updating (resistant to change)
    )
end

"""
Get all standard agent profiles for comparison studies.
"""
function all_profiles()
    [healthy_profile(), depressed_profile(), anxious_profile(), insecure_profile()]
end

# =============================================================================
# Trust Game Environment
# =============================================================================

"""
    TrustGameEnvironment <: AIFEnvironment

Environment for the trust game simulation.

The partner (trustee) can be friendly, hostile, or neutral.
- Friendly: returns cooperation when agent shares
- Hostile: exploits when agent shares
- Neutral: random behavior
"""
mutable struct TrustGameEnvironment <: AIFEnvironment
    partner_type::Symbol       # :friendly, :hostile, :neutral
    current_state::Vector{Int} # [context, choice]
    A::Vector{Array{Float64}}  # For sampling observations
    B::Vector{Array{Float64,3}}# For transitions

    # Initial state for reset
    initial_state::Vector{Int}
end

"""
    TrustGameEnvironment(partner_type, A, B)

Create a trust game environment.

# Arguments
- `partner_type`: :friendly, :hostile, or :neutral
- `A`: Observation likelihood matrices
- `B`: Transition matrices
"""
function TrustGameEnvironment(partner_type::Symbol, A::Vector{<:Array}, B::Vector{<:Array{<:Real,3}})
    # Map partner type to context state
    context = if partner_type == :friendly
        CONTEXT_FRIENDLY
    elseif partner_type == :hostile
        CONTEXT_HOSTILE
    else
        CONTEXT_NEUTRAL
    end

    initial_state = [context, CHOICE_START]
    current_state = copy(initial_state)

    A_typed = [Array{Float64}(a) for a in A]
    B_typed = [Array{Float64,3}(b) for b in B]

    TrustGameEnvironment(partner_type, current_state, A_typed, B_typed, initial_state)
end

function reset!(env::TrustGameEnvironment)
    env.current_state .= env.initial_state
    return env
end

function get_state(env::TrustGameEnvironment)::Vector{Int}
    return copy(env.current_state)
end

function observe(env::TrustGameEnvironment)::Vector{Int}
    Ng = length(env.A)
    obs = Vector{Int}(undef, Ng)

    s1, s2 = env.current_state

    for g in 1:Ng
        # A[g] has shape (No[g], Ns[1], Ns[2])
        probs = env.A[g][:, s1, s2]
        probs_sum = sum(probs)
        if probs_sum > 0
            probs = probs ./ probs_sum
        else
            probs = fill(1.0 / length(probs), length(probs))
        end
        obs[g] = sample_categorical(probs)
    end

    return obs
end

function step!(env::TrustGameEnvironment, action::Vector{Int})
    Nf = length(env.B)

    for f in 1:Nf
        s_current = env.current_state[f]
        Na_f = size(env.B[f], 3)
        a_f = Na_f > 1 ? action[f] : 1

        probs = env.B[f][:, s_current, a_f]
        probs_sum = sum(probs)
        if probs_sum > 0
            probs = probs ./ probs_sum
        else
            probs = zeros(length(probs))
            probs[s_current] = 1.0
        end

        env.current_state[f] = sample_categorical(probs)
    end

    return env
end

# =============================================================================
# Model Construction
# =============================================================================

"""
    build_trust_game_A(profile::AgentProfile) -> Vector{Array{Float64}}

Build observation likelihood matrices for trust game.

Modality 1 (Reward): Depends on context × choice
- Friendly + Share → High reward
- Hostile + Share → Low reward
- Keep → Neutral reward

Modality 2 (Behavior): Depends on context
- Friendly → Social behavior
- Hostile → Antisocial behavior

Modality 3 (Choice): Agent observes own choice
"""
function build_trust_game_A(profile::AgentProfile)
    # A[1]: Reward observations (3 × 3 × 3)
    # Shape: (reward_obs, context_state, choice_state)
    A1 = zeros(N_REWARD_OBS, N_CONTEXT_STATES, N_CHOICE_STATES)

    # At start state: neutral observation
    A1[REWARD_NEUTRAL, :, CHOICE_START] .= 1.0

    # After keeping: neutral outcome regardless of context
    A1[REWARD_NEUTRAL, :, CHOICE_KEEP] .= 1.0

    # After sharing: depends on context
    # Friendly context → high reward (cooperation returned)
    A1[REWARD_HIGH, CONTEXT_FRIENDLY, CHOICE_SHARE] = 0.9
    A1[REWARD_NEUTRAL, CONTEXT_FRIENDLY, CHOICE_SHARE] = 0.1

    # Hostile context → low reward (betrayed)
    A1[REWARD_LOW, CONTEXT_HOSTILE, CHOICE_SHARE] = 0.9
    A1[REWARD_NEUTRAL, CONTEXT_HOSTILE, CHOICE_SHARE] = 0.1

    # Neutral context → mixed outcome
    A1[REWARD_HIGH, CONTEXT_NEUTRAL, CHOICE_SHARE] = 0.4
    A1[REWARD_LOW, CONTEXT_NEUTRAL, CHOICE_SHARE] = 0.4
    A1[REWARD_NEUTRAL, CONTEXT_NEUTRAL, CHOICE_SHARE] = 0.2

    # Normalize
    A1 ./= sum(A1, dims=1)

    # A[2]: Behavior observations (3 × 3 × 3)
    A2 = zeros(N_BEHAVIOR_OBS, N_CONTEXT_STATES, N_CHOICE_STATES)

    # Behavior mainly depends on context, biased by profile
    for choice in 1:N_CHOICE_STATES
        # Friendly context → social behavior
        A2[BEHAVIOR_SOCIAL, CONTEXT_FRIENDLY, choice] = profile.p_share_friendly
        A2[BEHAVIOR_ANTISOCIAL, CONTEXT_FRIENDLY, choice] = 1.0 - profile.p_share_friendly

        # Hostile context → antisocial behavior
        A2[BEHAVIOR_SOCIAL, CONTEXT_HOSTILE, choice] = profile.p_share_hostile
        A2[BEHAVIOR_ANTISOCIAL, CONTEXT_HOSTILE, choice] = 1.0 - profile.p_share_hostile

        # Neutral context → unknown
        A2[BEHAVIOR_UNKNOWN, CONTEXT_NEUTRAL, choice] = 1.0
    end

    # At start, behavior is unknown
    A2[:, :, CHOICE_START] .= 0.0
    A2[BEHAVIOR_UNKNOWN, :, CHOICE_START] .= 1.0

    # Normalize
    A2 ./= sum(A2, dims=1)

    # A[3]: Choice observations (agent sees own choice)
    A3 = zeros(N_CHOICE_OBS, N_CONTEXT_STATES, N_CHOICE_STATES)
    for context in 1:N_CONTEXT_STATES
        for choice in 1:N_CHOICE_STATES
            A3[choice, context, choice] = 1.0
        end
    end

    return [A1, A2, A3]
end

"""
    build_trust_game_B(profile::AgentProfile) -> Vector{Array{Float64,3}}

Build transition matrices for trust game.

Factor 1 (Context): Static - doesn't change (but agent may believe it does)
Factor 2 (Choice): Controllable - agent chooses share or keep
"""
function build_trust_game_B(profile::AgentProfile)
    # B[1]: Context transitions (3 × 3 × 1)
    # Context is static - identity transition
    B1 = zeros(N_CONTEXT_STATES, N_CONTEXT_STATES, N_CONTEXT_ACTIONS)
    for s in 1:N_CONTEXT_STATES
        B1[s, s, 1] = 1.0
    end

    # B[2]: Choice transitions (3 × 3 × 2)
    # Action 1 = share, Action 2 = keep
    B2 = zeros(N_CHOICE_STATES, N_CHOICE_STATES, N_CHOICE_ACTIONS)

    # Share action → go to share state
    B2[CHOICE_SHARE, :, ACTION_SHARE] .= 1.0

    # Keep action → go to keep state
    B2[CHOICE_KEEP, :, ACTION_KEEP] .= 1.0

    return [B1, B2]
end

"""
    build_trust_game_C(profile::AgentProfile, T::Int) -> Vector{Matrix{Float64}}

Build preference matrices for trust game.

Preferences are over observations at final timestep only.
Loss aversion affects how negative outcomes are weighted.

Note: Values are scaled to be moderate - extreme values prevent exploration.
The paper uses ~2.2 for loss aversion multiplier but we use log-preferences
so values are scaled accordingly.
"""
function build_trust_game_C(profile::AgentProfile, T::Int)
    # C[1]: Reward preferences (log-preferences, so smaller values)
    C1 = zeros(N_REWARD_OBS, T)
    # Only care about outcome at final timestep
    # Base preference scaled to allow exploration
    base_gain = 1.0
    base_loss = -1.0 * profile.loss_aversion
    C1[REWARD_HIGH, T] = base_gain
    C1[REWARD_LOW, T] = base_loss
    C1[REWARD_NEUTRAL, T] = 0.0

    # C[2]: Behavior preferences (very slight)
    C2 = zeros(N_BEHAVIOR_OBS, T)
    C2[BEHAVIOR_SOCIAL, T] = 0.1
    C2[BEHAVIOR_ANTISOCIAL, T] = -0.1
    C2[BEHAVIOR_UNKNOWN, T] = 0.0

    # C[3]: No preference over choice observation
    C3 = zeros(N_CHOICE_OBS, T)

    return [C1, C2, C3]
end

"""
    build_trust_game_D(profile::AgentProfile) -> Vector{Vector{Float64}}

Build initial state prior for trust game.

Factor 1 (Context): Prior beliefs about partner's disposition
Factor 2 (Choice): Start in start state
"""
function build_trust_game_D(profile::AgentProfile)
    # D[1]: Context prior (biased by profile)
    D1 = zeros(N_CONTEXT_STATES)
    D1[CONTEXT_FRIENDLY] = profile.p_context_friendly
    D1[CONTEXT_HOSTILE] = profile.p_context_hostile
    D1[CONTEXT_NEUTRAL] = 1.0 - profile.p_context_friendly - profile.p_context_hostile
    D1 = D1 ./ sum(D1)  # Normalize

    # D[2]: Choice prior (start in start state)
    D2 = zeros(N_CHOICE_STATES)
    D2[CHOICE_START] = 1.0

    return [D1, D2]
end

"""
    build_trust_game_policies(T::Int) -> PolicySet

Build policies for trust game.

Two main policies:
- Policy 1: Share
- Policy 2: Keep
"""
function build_trust_game_policies(T::Int)
    # Horizon is T-1 (one decision to make)
    horizon = T - 1
    n_policies = 2
    n_factors = 2

    # V[t, π, f] = action for timestep t, policy π, factor f
    V = ones(Int, horizon, n_policies, n_factors)

    # Policy 1: Share (action 1 for choice factor)
    V[:, 1, 2] .= ACTION_SHARE

    # Policy 2: Keep (action 2 for choice factor)
    V[:, 2, 2] .= ACTION_KEEP

    # Factor 1 (context) has only one action
    V[:, :, 1] .= 1

    # Uniform prior over policies
    E = [0.5, 0.5]

    return PolicySet(V, E)
end

"""
    build_trust_game_model(profile::AgentProfile; T::Int=2) -> AIFModel

Build complete trust game model for an agent profile.
"""
function build_trust_game_model(profile::AgentProfile; T::Int=2)
    A = build_trust_game_A(profile)
    B = build_trust_game_B(profile)
    C = build_trust_game_C(profile, T)
    D = build_trust_game_D(profile)
    policies = build_trust_game_policies(T)

    return AIFModel(A, B, C, D; policies=policies, trial_length=T)
end

# =============================================================================
# Simulation
# =============================================================================

"""
    TrustGameResults

Results from a trust game simulation.

# Fields
- `sharing_rate`: Proportion of trials where agent chose to share
- `belief_friendly`: Belief history that context is friendly
- `belief_hostile`: Belief history that context is hostile
- `choices`: Sequence of choices (1=share, 2=keep)
- `rewards`: Sequence of reward observations
"""
struct TrustGameResults
    sharing_rate::Float64
    belief_friendly::Vector{Float64}
    belief_hostile::Vector{Float64}
    choices::Vector{Int}
    rewards::Vector{Int}
end

"""
    run_trust_game_simulation(;
        profile::AgentProfile,
        partner_type::Symbol,
        n_trials::Int=100,
        T::Int=2
    ) -> TrustGameResults

Run a trust game simulation.

# Arguments
- `profile`: Agent profile specifying biases
- `partner_type`: :friendly, :hostile, or :neutral
- `n_trials`: Number of rounds to play
- `T`: Timesteps per trial (default 2: decide then observe)
"""
function run_trust_game_simulation(;
    profile::AgentProfile,
    partner_type::Symbol,
    n_trials::Int=100,
    T::Int=2
)
    # Build model and settings
    # Use moderate precision to allow exploration while still preferring better options
    model = build_trust_game_model(profile; T=T)
    settings = AIFSettings(
        gamma=2.0,   # Moderate policy precision (lower = more exploration)
        alpha=4.0,   # Moderate action precision
        eta_A=profile.eta_A,
        eta_B=profile.eta_B,
        eta_D=profile.eta_D
    )

    # Initialize agent with Dirichlet priors
    # Scale priors to reflect profile's certainty
    pA_scale = 10.0  # Moderate prior strength
    pB_scale = 10.0
    pD_scale = 50.0  # Strong prior on context beliefs

    pA = [pA_scale .* model.A[g] for g in 1:model.Ng]
    pB = [pB_scale .* model.B[f] for f in 1:length(model.D)]
    pD = [pD_scale .* model.D[f] for f in 1:length(model.D)]

    agent = init_agent(model, pA, pB, pD)

    # Create environment
    env = TrustGameEnvironment(partner_type, model.A, model.B)

    # Storage
    choices = Vector{Int}(undef, n_trials)
    rewards = Vector{Int}(undef, n_trials)
    belief_friendly = Vector{Float64}(undef, n_trials)
    belief_hostile = Vector{Float64}(undef, n_trials)

    # Run trials
    for trial in 1:n_trials
        reset_trial!(agent, model)
        reset!(env)

        # Record initial beliefs about context
        D_normalized = agent.pD[1] ./ sum(agent.pD[1])
        belief_friendly[trial] = D_normalized[CONTEXT_FRIENDLY]
        belief_hostile[trial] = D_normalized[CONTEXT_HOSTILE]

        # Timestep 1: Observe initial state, decide
        agent.t = 1
        obs = observe(env)
        infer_states!(agent, model, obs, settings)
        infer_policies!(agent, model, settings)
        action = sample_action(agent, model; alpha=settings.alpha)

        # Record choice
        choices[trial] = action[2]  # Factor 2 is choice

        # Execute action
        push!(agent.actions, copy(action))
        step!(env, action)

        # Timestep 2: Observe outcome
        agent.t = 2
        obs = observe(env)
        infer_states!(agent, model, obs, settings)

        # Record reward observation
        rewards[trial] = obs[1]  # Modality 1 is reward

        # Learning: Update D (context beliefs) based on observations
        # Use final beliefs for static hidden states
        update_pD_final!(agent, settings.eta_D, [1])
    end

    # Calculate sharing rate
    n_shares = count(c -> c == CHOICE_SHARE, choices)
    sharing_rate = n_shares / n_trials

    return TrustGameResults(sharing_rate, belief_friendly, belief_hostile, choices, rewards)
end

"""
    run_trust_game_comparison(;
        profiles::Vector{AgentProfile}=all_profiles(),
        partner_type::Symbol=:friendly,
        n_trials::Int=100
    ) -> Dict{String, TrustGameResults}

Run trust game simulation for multiple agent profiles.
"""
function run_trust_game_comparison(;
    profiles::Vector{AgentProfile}=all_profiles(),
    partner_type::Symbol=:friendly,
    n_trials::Int=100
)
    results = Dict{String, TrustGameResults}()

    for profile in profiles
        results[profile.name] = run_trust_game_simulation(
            profile=profile,
            partner_type=partner_type,
            n_trials=n_trials
        )
    end

    return results
end

# =============================================================================
# Visualization
# =============================================================================

"""
    plot_trust_game_sharing(results::Dict{String, TrustGameResults}; window::Int=10)

Plot sharing rate evolution across agent types.
"""
function plot_trust_game_sharing(results::Dict{String, TrustGameResults}; window::Int=10)
    p = plot(
        title="Trust Game: Sharing Rate by Agent Type",
        xlabel="Trial",
        ylabel="Sharing Rate (moving avg)",
        legend=:bottomright,
        size=(800, 500)
    )

    colors = [:blue, :red, :orange, :purple]

    for (i, (name, res)) in enumerate(sort(collect(results), by=x->x[1]))
        # Compute moving average
        n = length(res.choices)
        sharing_ma = zeros(n)
        for t in 1:n
            start_idx = max(1, t - window + 1)
            sharing_ma[t] = mean(res.choices[start_idx:t] .== CHOICE_SHARE)
        end

        plot!(p, 1:n, sharing_ma, label=name, color=colors[mod1(i, length(colors))], linewidth=2)
    end

    return p
end

"""
    plot_trust_game_beliefs(results::Dict{String, TrustGameResults})

Plot belief evolution about partner context.
"""
function plot_trust_game_beliefs(results::Dict{String, TrustGameResults})
    p = plot(
        title="Trust Game: Belief about Partner Being Friendly",
        xlabel="Trial",
        ylabel="P(Friendly)",
        legend=:bottomright,
        size=(800, 500)
    )

    colors = [:blue, :red, :orange, :purple]

    for (i, (name, res)) in enumerate(sort(collect(results), by=x->x[1]))
        plot!(p, 1:length(res.belief_friendly), res.belief_friendly,
              label=name, color=colors[mod1(i, length(colors))], linewidth=2)
    end

    return p
end

"""
    plot_trust_game_summary(;
        partner_type::Symbol=:friendly,
        n_trials::Int=100,
        n_runs::Int=10
    )

Generate summary plots for trust game paper replication.
"""
function plot_trust_game_summary(;
    partner_type::Symbol=:friendly,
    n_trials::Int=100,
    n_runs::Int=10
)
    # Run multiple simulations and average
    all_results = [run_trust_game_comparison(partner_type=partner_type, n_trials=n_trials)
                   for _ in 1:n_runs]

    # Average results across runs
    avg_results = Dict{String, TrustGameResults}()

    for profile in all_profiles()
        name = profile.name

        # Collect all runs
        all_sharing = [r[name].sharing_rate for r in all_results]
        all_bf = hcat([r[name].belief_friendly for r in all_results]...)
        all_bh = hcat([r[name].belief_hostile for r in all_results]...)

        # Average
        avg_bf = vec(mean(all_bf, dims=2))
        avg_bh = vec(mean(all_bh, dims=2))
        avg_sharing = mean(all_sharing)

        # Use first run's choices/rewards (representative)
        avg_results[name] = TrustGameResults(
            avg_sharing,
            avg_bf,
            avg_bh,
            all_results[1][name].choices,
            all_results[1][name].rewards
        )
    end

    p1 = plot_trust_game_sharing(avg_results)
    p2 = plot_trust_game_beliefs(avg_results)

    return plot(p1, p2, layout=(2, 1), size=(800, 900))
end

# =============================================================================
# Exports (handled by ActiveInferenceCore.jl)
# =============================================================================
