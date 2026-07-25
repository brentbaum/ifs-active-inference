clamp_probability(value, genome::Genome) =
    clamp(Float64(value), g(genome, :probability_guard),
        1 - g(genome, :probability_guard))

logistic(value::Real) = inv(1 + exp(-Float64(value)))
logit(value::Real, genome::Genome) = begin
    probability = clamp_probability(value, genome)
    log(probability / (1 - probability))
end

function bernoulli_update(prior::Real, observation::Bool,
        reliability::Real, genome::Genome)
    p = clamp_probability(prior, genome)
    r = clamp_probability(reliability, genome)
    likelihood_ratio = observation ? r / (1 - r) : (1 - r) / r
    return logistic(logit(p, genome) + log(likelihood_ratio))
end

function record_update!(state::StrainState, variable::Symbol,
        old_value::Real, new_value::Real, update_function::Symbol,
        event_kind::Symbol, event_id::AbstractString)
    event = ProvenanceEvent(length(state.log) + 1, variable,
        Float64(old_value), Float64(new_value), update_function,
        event_kind, String(event_id))
    state.provenance[variable] = event
    push!(state.log, event)
    return new_value
end

function update_posterior!(state::StrainState, variable::Symbol,
        observation::Bool, reliability::Real, genome::Genome;
        event_kind::Symbol = :development, event_id::AbstractString = "")
    old = state.posterior[variable]
    updated = bernoulli_update(old, observation, reliability, genome)
    rate = g(genome, :history_learning_rate)
    new = clamp_probability((1 - rate) * old + rate * updated, genome)
    state.posterior[variable] = record_update!(state, variable, old, new,
        :update_posterior!, event_kind, event_id)
    return new
end

function update_policy_belief!(state::StrainState, policy::Symbol,
        cost_observation::Real, success::Bool, genome::Genome;
        event_id::AbstractString)
    rate = g(genome, :history_learning_rate)
    old_cost = state.policy_cost[policy]
    new_cost = (1 - rate) * old_cost + rate * clamp(Float64(cost_observation), 0, 1)
    state.policy_cost[policy] = new_cost
    record_update!(state, Symbol(:cost_, policy), old_cost, new_cost,
        :update_policy_belief!, :development, event_id * ":cost")
    old_reliability = state.policy_reliability[policy]
    target = success ? 1.0 : 0.0
    new_reliability = (1 - rate) * old_reliability + rate * target
    state.policy_reliability[policy] = new_reliability
    record_update!(state, Symbol(:reliability_, policy), old_reliability,
        new_reliability, :update_policy_belief!, :development,
        event_id * ":reliability")
    return nothing
end

function generate_history(seed::Int, genome::Genome;
        partner::Symbol = :neutral, favorable_policy::Symbol = :exclusion)
    rng = Xoshiro(UInt64(seed + Int(g(genome, :rng_history_offset))))
    events = NamedTuple[]
    count = Int(g(genome, :training_events))
    partner_probability = partner == :trustworthy ?
        g(genome, :partner_trustworthy_probability) :
        partner == :adverse ? g(genome, :partner_adverse_probability) :
        g(genome, :partner_neutral_probability)
    for episode in 1:count
        policy = POLICY_NAMES[mod1(episode, length(POLICY_NAMES))]
        baseline_cost = policy == favorable_policy ?
            g(genome, :history_favorable_cost) :
            g(genome, :history_unfavorable_cost)
        cost = clamp(baseline_cost + g(genome, :history_cost_sd) *
            randn(rng), 0.0, 1.0)
        success_probability = policy == favorable_policy ?
            g(genome, :history_favorable_success) :
            g(genome, :history_unfavorable_success)
        push!(events, (
            id = "history:$seed:$episode",
            kind = :joint_development,
            partner_positive = rand(rng) < partner_probability,
            competence_positive = rand(rng) < partner_probability,
            tolerated_positive = rand(rng) < partner_probability,
            root_now_positive = rand(rng) <
                g(genome, :history_root_positive_rate),
            policy = policy,
            policy_cost = cost,
            policy_success = rand(rng) < success_probability,
        ))
    end
    return events
end

function replay_history!(state::StrainState, history, genome::Genome)
    reliability = g(genome, :bayes_reliability)
    for event in history
        update_posterior!(state, :partner_trustworthy,
            event.partner_positive, reliability, genome;
            event_id = event.id * ":partner")
        update_posterior!(state, :partner_adverse,
            !event.partner_positive, reliability, genome;
            event_id = event.id * ":adverse")
        update_posterior!(state, :co_protection,
            event.competence_positive, reliability, genome;
            event_id = event.id * ":competence")
        update_posterior!(state, :outcome_forecast,
            event.tolerated_positive, reliability, genome;
            event_id = event.id * ":outcome")
        update_posterior!(state, :root_now,
            event.root_now_positive, reliability, genome;
            event_id = event.id * ":root")
        update_policy_belief!(state, event.policy, event.policy_cost,
            event.policy_success, genome; event_id = event.id)
    end
    return state
end

function expected_policy_cost(state::StrainState, policy::Symbol,
        genome::Genome)
    return state.policy_cost[policy] +
        (1 - state.policy_reliability[policy]) *
        g(genome, :policy_failure_cost)
end

function select_policy(state::StrainState, genome::Genome)
    costs = [expected_policy_cost(state, policy, genome)
        for policy in POLICY_NAMES]
    return POLICY_NAMES[argmin(costs)]
end

function protector_permission(state::StrainState, stakes::Real,
        genome::Genome; obsolete::Bool = false)
    risk = g(genome, :outcome_risk_weight) *
            (1 - state.posterior[:outcome_forecast]) +
        g(genome, :competence_risk_weight) *
            (1 - state.posterior[:co_protection]) +
        g(genome, :partner_risk_weight) *
            (1 - state.posterior[:partner_trustworthy])
    if obsolete
        competence = state.posterior[:co_protection]
        risk = competence * risk + (1 - competence)
    end
    allow = g(genome, :hope_value) - Float64(stakes) * risk
    refuse = -g(genome, :refusal_cost)
    return logistic((allow - refuse) / g(genome, :permission_temperature))
end

function freeze_write!(state::StrainState, overwhelm::Real, control::Real,
        genome::Genome; event_id::AbstractString)
    high_overwhelm = overwhelm >= g(genome, :freeze_overwhelm_boundary)
    low_control = control <= g(genome, :freeze_low_control_boundary)
    written = high_overwhelm && low_control
    precision = written ? g(genome, :freeze_write_precision) : 0.0
    if written && control <= g(genome, :probability_guard)
        precision *= g(genome, :freeze_no_control_attenuation)
    end
    push!(state.episodic_write, precision)
    return (written = written, precision = precision,
        avoidance_available = g(genome, :avoidance_cost) <
            g(genome, :policy_failure_cost))
end

function update_root!(state::StrainState, positive::Bool, breadth::Real,
        genome::Genome; event_id::AbstractString)
    old = state.posterior[:root_now]
    signed = positive ? 1.0 : -1.0
    new = logistic(logit(old, genome) + signed *
        g(genome, :root_evidence_weight) * Float64(breadth))
    state.posterior[:root_now] = record_update!(state, :root_now, old, new,
        :update_root!, :experiment, event_id)
    return new
end

function update_registration!(state::StrainState, suppressed::Bool,
        registration::Bool, genome::Genome; event_id::AbstractString)
    old = state.posterior[:relational_prior]
    if suppressed && registration
        new = clamp_probability(old + g(genome, :registration_increment) *
            (1 - old), genome)
        state.posterior[:relational_prior] = record_update!(state,
            :relational_prior, old, new, :update_registration!,
            :experiment, event_id)
        return new
    end
    return old
end

function update_precision_field!(state::StrainState,
        errors::Dict{Symbol,Float64}, broadcast::Bool, genome::Genome;
        narrowing::Bool = false)
    rate = g(genome, :field_learning_rate)
    sharing = broadcast ? g(genome, :field_broadcast_mix) : 0.0
    mean_error = mean(values(errors))
    for channel in FIELD_CHANNELS
        local_error = get(errors, channel, mean_error)
        forecast_error = (1 - sharing) * local_error + sharing * mean_error
        target = exp(-forecast_error)
        state.field[channel] = (1 - rate) * state.field[channel] + rate * target
    end
    if narrowing
        strength = g(genome, :field_narrowing_strength)
        for channel in (:context, :relational)
            state.field[channel] *= 1 - strength
        end
    end
    return copy(state.field)
end

function context_model_scores(observations::Vector{Float64}, genome::Genome)
    isempty(observations) && error("context scorer requires observations")
    n = length(observations)
    midpoint = max(1, fld(n, 2))
    global_fit = sum(abs2, observations .- mean(observations))
    cue_local_fit = sum(abs, diff(observations))
    then_mean = mean(view(observations, 1:midpoint))
    now_mean = mean(view(observations, midpoint + 1:n))
    split_fit = sum(abs2, view(observations, 1:midpoint) .- then_mean) +
        sum(abs2, view(observations, midpoint + 1:n) .- now_mean) +
        g(genome, :context_complexity_penalty)
    x = collect(1:n)
    slope = sum((x .- mean(x)) .* (observations .- mean(observations))) /
        max(sum(abs2, x .- mean(x)), eps())
    drift_fit = sum(abs2, observations .-
        (mean(observations) .+ slope .* (x .- mean(x))))
    jumps = abs.(diff(observations))
    change_fit = sum(abs2, observations .- mean(observations)) -
        (isempty(jumps) ? 0.0 : maximum(jumps)^2) +
        g(genome, :context_complexity_penalty)
    return Dict(:global_downweight => global_fit,
        :cue_local => cue_local_fit, :context_split => split_fit,
        :continuous_drift => drift_fit, :change_point => change_fit)
end

function update_dyad!(state::StrainState, signal::Int, settled::Bool,
        genome::Genome)
    outcome = settled ? 1 : 2
    state.dyad_mapping[signal, outcome] += g(genome, :dyad_learning_rate)
    learned_settle = state.dyad_mapping[signal, 1] /
        sum(view(state.dyad_mapping, signal, :))
    depth_grid = collect(range(0.0, 1.0; length = length(state.dyad_depth)))
    predicted = (1 - g(genome, :context_transition_mix)) .* state.dyad_depth .+
        g(genome, :context_transition_mix) / length(state.dyad_depth)
    floor_probability = g(genome, :dyad_regulated_floor)
    span = g(genome, :dyad_regulated_span)
    likelihood = @. learned_settle * (floor_probability + span * depth_grid) +
        (1 - learned_settle) *
            ((1 - floor_probability) - span * depth_grid)
    posterior = predicted .* likelihood .^ g(genome, :field_relational_precision)
    state.dyad_depth .= posterior ./ sum(posterior)
    expected_depth = sum(depth_grid .* state.dyad_depth)
    part = exp(log(g(genome, :field_part_precision)) - expected_depth)
    context = exp(log(g(genome, :field_context_precision)) + expected_depth)
    field_weight = context / (part + context)
    state.dyad_accumulator += field_weight
    packets = floor(Int, state.dyad_accumulator /
        g(genome, :dyad_packet_mass))
    state.dyad_accumulator -= packets * g(genome, :dyad_packet_mass)
    return (field_weight = field_weight, packets = packets,
        learned_settle = learned_settle, expected_depth = expected_depth)
end

imaginal_evidence(root_probability::Real, genome::Genome) =
    g(genome, :imaginal_floor) +
    g(genome, :imaginal_span) * Float64(root_probability)
