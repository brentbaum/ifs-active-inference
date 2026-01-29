"""
    tmaze.jl - Classic T-Maze Benchmark for Active Inference Verification

The T-maze is a standard benchmark for testing epistemic behavior in Active Inference.

Structure:
- Agent starts at center
- Must go to cue location to see which arm has reward
- Then navigate to the rewarded arm

State Factors:
- Factor 1: Location (4 states: center, cue_location, left_arm, right_arm)
- Factor 2: Reward location (2 states: left, right) - hidden, doesn't change

Observations:
- Modality 1: Location (4 outcomes: center, cue, left, right)
- Modality 2: Cue (3 outcomes: null, cue_left, cue_right) - only informative at cue_location
- Modality 3: Reward (2 outcomes: no_reward, reward) - only at correct arm

Actions:
- 4 actions affecting location: stay, go_to_cue, go_left, go_right
"""

using Random

# =============================================================================
# Constants
# =============================================================================

# Location states
const LOC_CENTER = 1
const LOC_CUE = 2
const LOC_LEFT = 3
const LOC_RIGHT = 4

# Reward location states
const REWARD_LEFT = 1
const REWARD_RIGHT = 2

# Cue observations
const CUE_NULL = 1
const CUE_LEFT = 2
const CUE_RIGHT = 3

# Reward observations
const REWARD_NONE = 1
const REWARD_GOT = 2

# Actions
const ACTION_STAY = 1
const ACTION_GO_CUE = 2
const ACTION_GO_LEFT = 3
const ACTION_GO_RIGHT = 4

# =============================================================================
# Build T-Maze Matrices
# =============================================================================

"""
    build_tmaze_matrices()

Build the generative model matrices for the T-maze.

Returns: (A, B, C, D, Ns, No, Na)
- A: Vector of observation likelihood tensors
- B: Vector of transition tensors
- C: Vector of preference matrices (log preferences)
- D: Vector of initial state priors
- Ns: Tuple of state dimensions
- No: Vector of observation dimensions
- Na: Vector of action dimensions
"""
function build_tmaze_matrices(; T::Int=3, reward_preference::Float64=4.0)
    # State dimensions
    Ns = (4, 2)  # (locations, reward_locations)
    Nf = 2

    # Observation dimensions
    No = [4, 3, 2]  # (location_obs, cue_obs, reward_obs)
    Ng = 3

    # Action dimensions (only factor 1 is controllable)
    Na = [4, 1]  # (location_actions, identity for reward_location)

    # -------------------------------------------------------------------------
    # A[1]: Location observation - identity mapping
    # Shape: (4 outcomes, 4 locations, 2 reward_locations)
    # -------------------------------------------------------------------------
    A1 = zeros(Float64, 4, 4, 2)
    for loc in 1:4
        for rew_loc in 1:2
            A1[loc, loc, rew_loc] = 1.0
        end
    end

    # -------------------------------------------------------------------------
    # A[2]: Cue observation
    # Shape: (3 outcomes, 4 locations, 2 reward_locations)
    # - Null everywhere except at cue location
    # - At cue location: reveals reward location
    # -------------------------------------------------------------------------
    A2 = zeros(Float64, 3, 4, 2)
    for loc in 1:4
        for rew_loc in 1:2
            if loc == LOC_CUE
                # At cue location, cue reveals reward location
                if rew_loc == REWARD_LEFT
                    A2[CUE_LEFT, loc, rew_loc] = 1.0
                else
                    A2[CUE_RIGHT, loc, rew_loc] = 1.0
                end
            else
                # Elsewhere, no informative cue
                A2[CUE_NULL, loc, rew_loc] = 1.0
            end
        end
    end

    # -------------------------------------------------------------------------
    # A[3]: Reward observation
    # Shape: (2 outcomes, 4 locations, 2 reward_locations)
    # - No reward at center or cue
    # - Reward at correct arm, no reward at wrong arm
    # -------------------------------------------------------------------------
    A3 = zeros(Float64, 2, 4, 2)
    for loc in 1:4
        for rew_loc in 1:2
            if loc == LOC_LEFT
                if rew_loc == REWARD_LEFT
                    A3[REWARD_GOT, loc, rew_loc] = 1.0
                else
                    A3[REWARD_NONE, loc, rew_loc] = 1.0
                end
            elseif loc == LOC_RIGHT
                if rew_loc == REWARD_RIGHT
                    A3[REWARD_GOT, loc, rew_loc] = 1.0
                else
                    A3[REWARD_NONE, loc, rew_loc] = 1.0
                end
            else
                # Center and cue location: no reward
                A3[REWARD_NONE, loc, rew_loc] = 1.0
            end
        end
    end

    A = [A1, A2, A3]

    # -------------------------------------------------------------------------
    # B[1]: Location transitions (deterministic based on action)
    # Shape: (4 next_states, 4 current_states, 4 actions)
    # -------------------------------------------------------------------------
    B1 = zeros(Float64, 4, 4, 4)

    for s in 1:4
        # Action 1: Stay
        B1[s, s, ACTION_STAY] = 1.0

        # Action 2: Go to cue
        B1[LOC_CUE, s, ACTION_GO_CUE] = 1.0

        # Action 3: Go left
        B1[LOC_LEFT, s, ACTION_GO_LEFT] = 1.0

        # Action 4: Go right
        B1[LOC_RIGHT, s, ACTION_GO_RIGHT] = 1.0
    end

    # -------------------------------------------------------------------------
    # B[2]: Reward location transitions (identity - doesn't change)
    # Shape: (2 next_states, 2 current_states, 1 action)
    # -------------------------------------------------------------------------
    B2 = zeros(Float64, 2, 2, 1)
    B2[1, 1, 1] = 1.0
    B2[2, 2, 1] = 1.0

    B = [B1, B2]

    # -------------------------------------------------------------------------
    # C: Preferences (log preferences over observations)
    # Shape per modality: (No[g], T)
    # -------------------------------------------------------------------------
    # C[1]: No preference over location observations
    C1 = zeros(Float64, 4, T)

    # C[2]: No preference over cue observations
    C2 = zeros(Float64, 3, T)

    # C[3]: Prefer reward ONLY at final timestep
    # This is critical for epistemic behavior - if reward preference is at all timesteps,
    # going to an arm early gives higher expected utility, defeating epistemic exploration
    C3 = zeros(Float64, 2, T)
    C3[REWARD_GOT, T] = reward_preference    # Prefer getting reward at final timestep only
    C3[REWARD_NONE, :] .= 0.0                 # Neutral to no reward

    C = [C1, C2, C3]

    # -------------------------------------------------------------------------
    # D: Initial state priors
    # -------------------------------------------------------------------------
    # D[1]: Start at center
    D1 = zeros(Float64, 4)
    D1[LOC_CENTER] = 1.0

    # D[2]: Uniform over reward location (agent doesn't know)
    D2 = ones(Float64, 2) ./ 2

    D = [D1, D2]

    return (A=A, B=B, C=C, D=D, Ns=Ns, No=No, Na=Na)
end

# =============================================================================
# Build T-Maze Policies
# =============================================================================

"""
    build_tmaze_policies(; horizon=2)

Build sensible policies for the T-maze.

Returns a PolicySet with 4 policies:
1. go_to_cue, go_left  (epistemic then exploit left)
2. go_to_cue, go_right (epistemic then exploit right)
3. go_left, stay       (no cue check, go left)
4. go_right, stay      (no cue check, go right)
"""
function build_tmaze_policies(; horizon::Int=2)
    # V[t, policy, factor]
    # Factor 1: location actions
    # Factor 2: identity action (only 1 action available)

    n_policies = 4
    n_factors = 2

    V = zeros(Int, horizon, n_policies, n_factors)

    # Policy 1: go_to_cue, then go_left
    V[1, 1, 1] = ACTION_GO_CUE
    V[2, 1, 1] = ACTION_GO_LEFT
    V[1, 1, 2] = 1  # Identity action for factor 2
    V[2, 1, 2] = 1

    # Policy 2: go_to_cue, then go_right
    V[1, 2, 1] = ACTION_GO_CUE
    V[2, 2, 1] = ACTION_GO_RIGHT
    V[1, 2, 2] = 1
    V[2, 2, 2] = 1

    # Policy 3: go_left, then stay
    V[1, 3, 1] = ACTION_GO_LEFT
    V[2, 3, 1] = ACTION_STAY
    V[1, 3, 2] = 1
    V[2, 3, 2] = 1

    # Policy 4: go_right, then stay
    V[1, 4, 1] = ACTION_GO_RIGHT
    V[2, 4, 1] = ACTION_STAY
    V[1, 4, 2] = 1
    V[2, 4, 2] = 1

    # Uniform policy prior
    E = ones(Float64, n_policies)

    return PolicySet(V, E)
end

# =============================================================================
# T-Maze Environment
# =============================================================================

"""
    TMazeEnvironment <: AIFEnvironment

T-maze environment for Active Inference experiments.

# Fields
- `reward_location::Int`: Which arm has the reward (1=left, 2=right)
- `current_state::Vector{Int}`: Current state [location, reward_location]
"""
mutable struct TMazeEnvironment <: AIFEnvironment
    reward_location::Int
    current_state::Vector{Int}

    function TMazeEnvironment(; reward_location::Int=rand(1:2))
        @assert reward_location in (REWARD_LEFT, REWARD_RIGHT) "reward_location must be 1 (left) or 2 (right)"
        new(reward_location, [LOC_CENTER, reward_location])
    end
end

"""
    observe(env::TMazeEnvironment) -> Vector{Int}

Generate observations based on current state.
"""
function observe(env::TMazeEnvironment)::Vector{Int}
    loc = env.current_state[1]
    rew_loc = env.current_state[2]

    # Modality 1: Location observation (identity)
    obs_loc = loc

    # Modality 2: Cue observation
    if loc == LOC_CUE
        obs_cue = rew_loc == REWARD_LEFT ? CUE_LEFT : CUE_RIGHT
    else
        obs_cue = CUE_NULL
    end

    # Modality 3: Reward observation
    if loc == LOC_LEFT && rew_loc == REWARD_LEFT
        obs_reward = REWARD_GOT
    elseif loc == LOC_RIGHT && rew_loc == REWARD_RIGHT
        obs_reward = REWARD_GOT
    else
        obs_reward = REWARD_NONE
    end

    return [obs_loc, obs_cue, obs_reward]
end

"""
    step!(env::TMazeEnvironment, action::Vector{Int})

Execute action in the environment.
"""
function step!(env::TMazeEnvironment, action::Vector{Int})
    loc_action = action[1]

    # Deterministic transitions
    if loc_action == ACTION_STAY
        # Stay in current location
    elseif loc_action == ACTION_GO_CUE
        env.current_state[1] = LOC_CUE
    elseif loc_action == ACTION_GO_LEFT
        env.current_state[1] = LOC_LEFT
    elseif loc_action == ACTION_GO_RIGHT
        env.current_state[1] = LOC_RIGHT
    end

    # Reward location never changes
    return nothing
end

"""
    get_state(env::TMazeEnvironment) -> Vector{Int}

Get the current hidden state.
"""
function get_state(env::TMazeEnvironment)::Vector{Int}
    return copy(env.current_state)
end

"""
    reset!(env::TMazeEnvironment)

Reset environment to initial state (center location).
"""
function reset!(env::TMazeEnvironment)
    env.current_state[1] = LOC_CENTER
    # Keep same reward location
    return nothing
end

"""
    reset!(env::TMazeEnvironment, reward_location::Int)

Reset environment with a new reward location.
"""
function reset!(env::TMazeEnvironment, reward_location::Int)
    @assert reward_location in (REWARD_LEFT, REWARD_RIGHT)
    env.reward_location = reward_location
    env.current_state = [LOC_CENTER, reward_location]
    return nothing
end

# =============================================================================
# Build T-Maze Model
# =============================================================================

"""
    build_tmaze_model(; T=3, reward_preference=4.0)

Build a complete AIFModel for the T-maze task.

# Arguments
- `T::Int`: Trial length (default 3 timesteps: start, after first action, after second action)
- `reward_preference::Float64`: Log preference for reward (default 4.0)

# Returns
An AIFModel configured for the T-maze task.
"""
function build_tmaze_model(; T::Int=3, reward_preference::Float64=4.0)
    # Build matrices
    matrices = build_tmaze_matrices(T=T, reward_preference=reward_preference)

    # Build policies
    policies = build_tmaze_policies(horizon=T-1)

    # Create model
    return AIFModel(
        matrices.A,
        matrices.B,
        matrices.C,
        matrices.D;
        policies=policies,
        trial_length=T
    )
end

# =============================================================================
# T-Maze Test Runner
# =============================================================================

"""
    TMazeResult

Result of a single T-maze trial.
"""
struct TMazeResult
    checked_cue::Bool       # Did agent visit cue location first?
    got_reward::Bool        # Did agent get the reward?
    correct_choice::Bool    # Did agent go to correct arm (eventually)?
    first_action::Int       # First action taken
    policy_probs::Vector{Float64}  # Policy probabilities after first inference
end

"""
    run_tmaze_test(; n_trials=100, settings=nothing, verbose=false)

Run T-maze benchmark tests to verify Active Inference behavior.

With state_info_gain enabled, the agent should exhibit epistemic behavior:
checking the cue first before choosing an arm.

# Arguments
- `n_trials::Int`: Number of trials to run (default 100)
- `settings::Union{Nothing, AIFSettings}`: Custom settings (default uses state info gain)
- `verbose::Bool`: Print per-trial details (default false)

# Returns
A NamedTuple containing:
- `results`: Vector of TMazeResult for each trial
- `cue_check_rate`: Fraction of trials where agent checked cue first
- `reward_rate`: Fraction of trials where agent got reward
- `correct_rate`: Fraction of trials with correct arm choice
- `epistemic_behavior`: Whether cue_check_rate > 0.8 (expected with state info gain)
"""
function run_tmaze_test(;
    n_trials::Int=100,
    settings::Union{Nothing, AIFSettings}=nothing,
    verbose::Bool=false
)
    # Default settings with state info gain enabled
    if isnothing(settings)
        settings = AIFSettings(
            gamma=16.0,
            alpha=16.0,
            use_ambiguity=true,
            use_utility=true,
            use_states_info_gain=true
        )
    end

    # Build model
    model = build_tmaze_model()

    results = TMazeResult[]

    for trial in 1:n_trials
        # Randomize reward location each trial
        reward_loc = rand(1:2)
        env = TMazeEnvironment(reward_location=reward_loc)

        # Create fresh agent each trial
        agent = init_agent(model)

        # Run trial
        trial_result = run_trial!(agent, model, env, settings)

        # Analyze results
        first_action = trial_result.actions[1][1]
        checked_cue = first_action == ACTION_GO_CUE

        # Check final state for reward
        final_obs = trial_result.observations[end]
        got_reward = final_obs[3] == REWARD_GOT

        # Check if agent eventually went to correct arm
        final_loc = trial_result.states[end][1]
        correct_choice = (final_loc == LOC_LEFT && reward_loc == REWARD_LEFT) ||
                        (final_loc == LOC_RIGHT && reward_loc == REWARD_RIGHT)

        # Get policy probabilities from first timestep
        policy_probs = trial_result.qpi[1] isa Vector ? trial_result.qpi[1] : zeros(4)

        result = TMazeResult(
            checked_cue,
            got_reward,
            correct_choice,
            first_action,
            policy_probs
        )
        push!(results, result)

        if verbose
            action_names = ["stay", "go_cue", "go_left", "go_right"]
            reward_str = reward_loc == REWARD_LEFT ? "left" : "right"
            @info "Trial $trial: reward=$reward_str, first_action=$(action_names[first_action]), " *
                  "checked_cue=$checked_cue, got_reward=$got_reward"
        end
    end

    # Compute statistics
    cue_check_rate = sum(r.checked_cue for r in results) / n_trials
    reward_rate = sum(r.got_reward for r in results) / n_trials
    correct_rate = sum(r.correct_choice for r in results) / n_trials

    # With state info gain, agent should strongly prefer checking cue
    epistemic_behavior = cue_check_rate > 0.8

    return (
        results = results,
        cue_check_rate = cue_check_rate,
        reward_rate = reward_rate,
        correct_rate = correct_rate,
        epistemic_behavior = epistemic_behavior,
        settings = settings
    )
end

"""
    run_tmaze_comparison(; n_trials=100, verbose=false)

Compare T-maze behavior with and without state information gain.

This demonstrates the effect of epistemic value on decision-making.

# Returns
A NamedTuple with results for both conditions:
- `with_info_gain`: Results with use_states_info_gain=true
- `without_info_gain`: Results with use_states_info_gain=false
"""
function run_tmaze_comparison(; n_trials::Int=100, verbose::Bool=false)
    println("=" ^ 60)
    println("T-Maze Active Inference Benchmark")
    println("=" ^ 60)

    # Settings WITH state info gain (epistemic)
    settings_epistemic = AIFSettings(
        gamma=16.0,
        alpha=16.0,
        use_ambiguity=true,
        use_utility=true,
        use_states_info_gain=true
    )

    # Settings WITHOUT state info gain (pragmatic only)
    settings_pragmatic = AIFSettings(
        gamma=16.0,
        alpha=16.0,
        use_ambiguity=true,
        use_utility=true,
        use_states_info_gain=false
    )

    println("\nRunning with state information gain (epistemic)...")
    result_epistemic = run_tmaze_test(
        n_trials=n_trials,
        settings=settings_epistemic,
        verbose=verbose
    )

    println("\nRunning without state information gain (pragmatic only)...")
    result_pragmatic = run_tmaze_test(
        n_trials=n_trials,
        settings=settings_pragmatic,
        verbose=verbose
    )

    # Print summary
    println("\n" * "=" ^ 60)
    println("Results Summary")
    println("=" ^ 60)

    println("\nWith State Info Gain (Epistemic):")
    println("  Cue check rate:  $(round(result_epistemic.cue_check_rate * 100, digits=1))%")
    println("  Reward rate:     $(round(result_epistemic.reward_rate * 100, digits=1))%")
    println("  Correct choice:  $(round(result_epistemic.correct_rate * 100, digits=1))%")

    println("\nWithout State Info Gain (Pragmatic):")
    println("  Cue check rate:  $(round(result_pragmatic.cue_check_rate * 100, digits=1))%")
    println("  Reward rate:     $(round(result_pragmatic.reward_rate * 100, digits=1))%")
    println("  Correct choice:  $(round(result_pragmatic.correct_rate * 100, digits=1))%")

    println("\n" * "-" ^ 60)
    if result_epistemic.epistemic_behavior
        println("SUCCESS: Agent exhibits epistemic behavior with info gain enabled")
    else
        println("WARNING: Agent does not exhibit expected epistemic behavior")
    end
    println("-" ^ 60)

    return (
        with_info_gain = result_epistemic,
        without_info_gain = result_pragmatic
    )
end
