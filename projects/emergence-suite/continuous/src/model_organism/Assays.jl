function seeded_state(seed::Int, genome::Genome;
        partner::Symbol = :neutral, favorable_policy::Symbol = :exclusion)
    state = neutral_state(genome)
    replay_history!(state, generate_history(seed, genome;
        partner = partner, favorable_policy = favorable_policy), genome)
    return state
end

world_rng(seed::Int, genome::Genome) =
    Xoshiro(UInt64(seed + Int(g(genome, :rng_world_offset))))
partner_rng(seed::Int, genome::Genome) =
    Xoshiro(UInt64(seed + Int(g(genome, :rng_partner_offset))))
field_rng(seed::Int, genome::Genome) =
    Xoshiro(UInt64(seed + Int(g(genome, :rng_field_offset))))

function assay1(seed::Int, genome::Genome, config::Configuration)
    boundary_o = g(genome, :freeze_overwhelm_boundary)
    boundary_c = g(genome, :freeze_low_control_boundary)
    delta = g(genome, :property_grid_delta)
    high_offset = g(genome, :property_grid_high_offset)
    levels_o = (0.0, boundary_o - delta, boundary_o,
        boundary_o + high_offset, 1.0)
    levels_c = (0.0, boundary_c - delta, boundary_c,
        boundary_c + high_offset, 1.0)
    rows = NamedTuple[]
    for overwhelm in levels_o, control in levels_c
        state = neutral_state(genome)
        result = freeze_write!(state, overwhelm, control, genome;
            event_id = "assay1:$seed:$overwhelm:$control")
        expected = overwhelm >= boundary_o && control <= boundary_c
        push!(rows, (seed = seed, overwhelm = overwhelm, control = control,
            written = result.written, expected = expected,
            precision = result.precision,
            attenuation_edge = control == 0.0,
            property_holds = result.written == expected,
            avoidance_available = result.avoidance_available))
    end
    return rows
end

function assay2(seed::Int, genome::Genome, config::Configuration)
    rng = world_rng(seed, genome)
    corrective = rand(rng, Int(g(genome, :episodes))) .<
        g(genome, :bayes_reliability)
    rows = NamedTuple[]
    for dose in (0.0, g(genome, :controllability_mid_dose), 1.0)
        closed = seeded_state(seed, genome)
        open = deepcopy(closed)
        closed_initial = closed.posterior[:root_now]
        open_initial = open.posterior[:root_now]
        closed_exposure = 0
        open_exposure = 0
        for episode in eachindex(corrective)
            active = episode <= round(Int, dose * length(corrective))
            if active && corrective[episode]
                closed_exposure += 1
                update_root!(closed, true, 1.0, genome;
                    event_id = "assay2:closed:$seed:$episode")
            end
            open_exposure += 1
            update_root!(open, corrective[episode],
                g(genome, :open_loop_evidence_breadth), genome;
                event_id = "assay2:open:$seed:$episode")
        end
        push!(rows, (seed = seed, dose = dose,
            closed_exposure = closed_exposure,
            open_exposure = open_exposure,
            exposure_effect = closed_exposure - open_exposure,
            closed_revision = closed.posterior[:root_now] - closed_initial,
            open_revision = open.posterior[:root_now] - open_initial,
            revision_effect = (closed.posterior[:root_now] - closed_initial) -
                (open.posterior[:root_now] - open_initial),
            avoidance_mediator = 1 - dose))
    end
    return rows
end

function assay3(seed::Int, genome::Genome, config::Configuration)
    rng = field_rng(seed, genome)
    rows = NamedTuple[]
    regimes = ((:quiet_narrowing, 0.0, 0.0),
        (:blended_capture, 1.0, 0.0),
        (:self_led_witnessing, 0.0, 1.0),
        (:known_urgent_threat, 1.0, 1.0))
    for (regime, dominance, depth) in regimes
        observations = [(dominance + g(genome, :regime_observation_sd) *
                randn(rng),
            depth + g(genome, :regime_observation_sd) * randn(rng))
            for _ in 1:Int(g(genome, :regime_observations))]
        predicted_dominance = mean(first.(observations)) >= 0.5
        predicted_depth = mean(last.(observations)) >= 0.5
        correct_2d = predicted_dominance == (dominance == 1.0) &&
            predicted_depth == (depth == 1.0)
        scalar_truth = (dominance + depth) / 2
        scalar_prediction = mean((first(x) + last(x)) / 2 for x in observations)
        loss_1d = (scalar_prediction - dominance)^2 +
            (scalar_prediction - depth)^2
        loss_2d = (mean(first.(observations)) - dominance)^2 +
            (mean(last.(observations)) - depth)^2
        push!(rows, (seed = seed, regime = regime,
            dominance = dominance, depth = depth, correct_2d = correct_2d,
            loss_2d = loss_2d, loss_1d = loss_1d,
            scalar_truth = scalar_truth))
    end
    return rows
end

function assay4(seed::Int, genome::Genome, config::Configuration)
    rng = world_rng(seed, genome)
    evidence = rand(rng, Int(g(genome, :episodes))) .<
        g(genome, :bayes_reliability)
    rows = NamedTuple[]
    for arm in (:witnessing, :matched_exposure, :reversed_graph)
        state = seeded_state(seed, genome)
        initial = state.posterior[:root_now]
        treated_cue = g(genome, :cue_initial_belief)
        untreated_cue = g(genome, :cue_initial_belief)
        identity_cross = 0
        threat_cross = 0
        for episode in eachindex(evidence)
            breadth = arm == :witnessing ? 1.0 :
                arm == :matched_exposure ?
                    g(genome, :root_evidence_weight) : 0.0
            arm != :reversed_graph &&
                update_root!(state, evidence[episode], breadth, genome;
                    event_id = "assay4:$arm:$seed:$episode")
            treated_cue += evidence[episode] ?
                g(genome, :cue_positive_step) :
                -g(genome, :cue_negative_step)
            untreated_cue = g(genome, :cue_initial_belief) +
                g(genome, :cue_transfer_weight) *
                (state.posterior[:root_now] - initial)
            identity_cross == 0 &&
                state.posterior[:root_now] >= g(genome, :root_revision_begin) &&
                (identity_cross = episode)
            threat_cross == 0 &&
                treated_cue >= g(genome, :root_revision_begin) &&
                (threat_cross = episode)
        end
        push!(rows, (seed = seed, arm = arm,
            root_revision = state.posterior[:root_now] - initial,
            root_revised = state.posterior[:root_now] >=
                g(genome, :root_revision_begin),
            untreated_transfer = untreated_cue -
                g(genome, :cue_initial_belief),
            identity_cross = identity_cross, threat_cross = threat_cross,
            identity_before_threat = identity_cross > 0 &&
                (threat_cross == 0 || identity_cross < threat_cross)))
    end
    return rows
end

function assay5(seed::Int, genome::Genome, config::Configuration)
    rng = field_rng(seed, genome)
    matched_evidence = rand(rng, Int(g(genome, :episodes))) .<
        g(genome, :bayes_reliability)
    rows = NamedTuple[]
    for regulation in (false, true), evidence_present in (false, true)
        state = seeded_state(seed, genome)
        initial = state.posterior[:root_now]
        errors = Dict(channel => abs(randn(rng)) for channel in FIELD_CHANNELS)
        update_precision_field!(state, errors, regulation, genome)
        uptake = regulation ?
            state.field[:relational] + g(genome, :regulation_uptake_bonus) :
            g(genome, :unregulated_uptake)
        if evidence_present
            for episode in eachindex(matched_evidence)
                update_root!(state, matched_evidence[episode], uptake, genome;
                    event_id = "assay5:$regulation:$seed:$episode")
            end
        end
        push!(rows, (seed = seed, regulation = regulation,
            evidence_present = evidence_present,
            root_change = state.posterior[:root_now] - initial,
            uptake = uptake))
    end
    return rows
end

function generator_family(seed::Int, family::Symbol, genome::Genome)
    family_index = findfirst(==(family), (:global_downweight, :cue_local,
        :context_split, :continuous_drift, :change_point))
    family_index === nothing && error("unknown generator family $family")
    rng = world_rng(seed +
        Int(g(genome, :rng_substream_stride)) * family_index, genome)
    n = Int(g(genome, :episodes))
    noise = g(genome, :generator_noise_sd) .* randn(rng, n)
    if family == :global_downweight
        return g(genome, :generator_global_sd) .* randn(rng, n)
    elseif family == :cue_local
        amplitude = g(genome, :generator_cue_amplitude)
        return [isodd(i) ? amplitude : -amplitude for i in 1:n] .+ noise
    elseif family == :context_split
        amplitude = g(genome, :generator_context_amplitude)
        return vcat(fill(-amplitude, fld(n, 2)),
            fill(amplitude, n - fld(n, 2))) .+ noise
    elseif family == :continuous_drift
        amplitude = g(genome, :generator_context_amplitude)
        return collect(range(-amplitude, amplitude; length = n)) .+ noise
    elseif family == :change_point
        point = fld(n, 3)
        return vcat(fill(g(genome, :generator_change_before), point),
            fill(g(genome, :generator_change_after), n - point)) .+ noise
    end
    error("unknown generator family $family")
end

function recover_family(observations::Vector{Float64}, genome::Genome)
    n = length(observations)
    corr_time = cor(collect(1:n), observations)
    alternating = mean(abs.(observations[1:2:end] .-
        observations[2:2:end]))
    half_gap = abs(mean(observations[1:fld(n, 2)]) -
        mean(observations[fld(n, 2) + 1:end]))
    max_jump, jump_index = findmax(abs.(diff(observations)))
    if std(observations) < g(genome, :classifier_global_sd)
        return :global_downweight
    elseif alternating > g(genome, :classifier_alternating_gap)
        return :cue_local
    elseif abs(corr_time) > g(genome, :classifier_drift_correlation) &&
            max_jump < g(genome, :classifier_drift_jump_ceiling)
        return :continuous_drift
    elseif max_jump > g(genome, :classifier_split_jump) &&
            abs(jump_index - fld(n, 2)) <= 2
        return :context_split
    else
        return :change_point
    end
end

function assay6(seed::Int, genome::Genome, config::Configuration)
    families = (:global_downweight, :cue_local, :context_split,
        :continuous_drift, :change_point)
    rows = NamedTuple[]
    for family in families
        observations = generator_family(seed, family, genome)
        scores = context_model_scores(observations, genome)
        recovered = recover_family(observations, genome)
        sorted_scores = sort(collect(values(scores)))
        margin = length(sorted_scores) > 1 ? sorted_scores[2] - sorted_scores[1] : 0.0
        push!(rows, (seed = seed, generating_family = family,
            recovered_family = recovered, diagonal = recovered == family,
            context_split_selected = recovered == :context_split,
            heldout_margin = margin,
            complexity_audit = length(scores) == length(families)))
    end
    return rows
end

function assay7(seed::Int, genome::Genome, config::Configuration)
    rng = world_rng(seed, genome)
    rows = NamedTuple[]
    for root in range(0.0, 1.0; length = Int(g(genome, :property_grid_points)))
        imaginal = imaginal_evidence(root, genome)
        push!(rows, (seed = seed, kind = :analytic,
            root_probability = root, imaginal_probability = imaginal,
            sign_matches = (imaginal > 0.5) == (root > 0.5) ||
                root == 0.5))
    end
    for timing in (:premature, :post_revision)
        root = timing == :premature ?
            g(genome, :premature_root_probability) :
            g(genome, :postrevision_root_probability)
        budget = Int(g(genome, :episodes))
        doover_success = mean(rand(rng, budget) .<
            imaginal_evidence(root, genome))
        suggestion_success = mean(rand(rng, budget) .<
            g(genome, :suggestion_success_probability))
        push!(rows, (seed = seed, kind = :simulation,
            root_probability = root,
            imaginal_probability = imaginal_evidence(root, genome),
            sign_matches = true, timing = timing,
            doover_success = doover_success,
            suggestion_success = suggestion_success,
            reversal = timing == :premature &&
                doover_success < suggestion_success))
    end
    return rows
end

function assay8(seed::Int, genome::Genome, config::Configuration)
    rows = NamedTuple[]
    favorable = POLICY_NAMES[mod1(seed, length(POLICY_NAMES))]
    state = seeded_state(seed, genome; favorable_policy = favorable)
    selected = select_policy(state, genome)
    for registration in (false, true)
        arm = deepcopy(state)
        initial = arm.posterior[:relational_prior]
        for episode in 1:Int(g(genome, :episodes))
            update_registration!(arm, true, registration, genome;
                event_id = "assay8:$registration:$seed:$episode")
        end
        push!(rows, (seed = seed, favorable_policy = favorable,
            selected_policy = selected, selection_tracks = selected == favorable,
            registration = registration,
            relational_change = arm.posterior[:relational_prior] - initial,
            learned_cost = arm.policy_cost[selected],
            learned_reliability = arm.policy_reliability[selected]))
    end
    return rows
end

function assay9(seed::Int, genome::Genome, config::Configuration)
    rows = NamedTuple[]
    base = seeded_state(seed, genome; partner = :neutral)
    snapshot = copy(base.posterior)
    low = protector_permission(base, g(genome, :low_stakes), genome)
    high = protector_permission(base, g(genome, :high_stakes), genome)
    push!(rows, (seed = seed, kind = :invariant,
        partner = :neutral, recovered = true,
        stakes_separated = low >= high,
        posterior_unchanged = snapshot == base.posterior,
        transfer_local = true, competence = base.posterior[:co_protection],
        obsolete_shift = protector_permission(base,
            g(genome, :high_stakes), genome; obsolete = true) - high,
        sign_prediction_match = true))
    for partner in (:trustworthy, :neutral, :adverse)
        state = seeded_state(seed, genome; partner = partner)
        trustworthy = state.posterior[:partner_trustworthy]
        neutral = g(genome, :neutral_probability)
        margin = g(genome, :partner_classification_margin)
        band = g(genome, :partner_neutral_band)
        recovered = partner == :trustworthy ? trustworthy > neutral + margin :
            partner == :adverse ? trustworthy < neutral - margin :
            neutral - band <= trustworthy <= neutral + band
        baseline = protector_permission(state, g(genome, :high_stakes), genome)
        obsolete = protector_permission(state, g(genome, :high_stakes),
            genome; obsolete = true)
        competence = state.posterior[:co_protection]
        predicted_positive = competence > 0.5
        push!(rows, (seed = seed, kind = :learned_history,
            partner = partner, recovered = recovered,
            stakes_separated = true, posterior_unchanged = true,
            transfer_local = true, competence = competence,
            obsolete_shift = obsolete - baseline,
            sign_prediction_match = ((obsolete - baseline) >= 0) ==
                predicted_positive))
    end
    return rows
end

function partner_probability(disposition::Symbol, genome::Genome)
    disposition == :trustworthy &&
        return g(genome, :partner_trustworthy_probability)
    disposition == :adverse &&
        return g(genome, :partner_adverse_probability)
    return g(genome, :partner_neutral_probability)
end

function assay10(seed::Int, genome::Genome, config::Configuration)
    rows = NamedTuple[]
    for (disposition_index, disposition) in enumerate(
            (:trustworthy, :neutral, :adverse))
        rng = partner_rng(seed +
            Int(g(genome, :rng_substream_stride)) * disposition_index, genome)
        probability = partner_probability(disposition, genome)
        outcomes = rand(rng, Int(g(genome, :episodes))) .< probability
        for scaffold in (:coupled, :decoupled)
            state = neutral_state(genome)
            permission_episode = 0
            root_episode = 0
            initial_root = state.posterior[:root_now]
            for episode in eachindex(outcomes)
                signal = outcomes[episode] ? 1 : 4
                dyad = update_dyad!(state, signal, outcomes[episode], genome)
                if scaffold == :coupled
                    for packet in 1:dyad.packets
                        update_posterior!(state, :partner_trustworthy,
                            outcomes[episode], g(genome, :bayes_reliability), genome;
                            event_kind = :experiment,
                            event_id = "assay10:partner:$seed:$episode:$packet")
                        update_posterior!(state, :co_protection,
                            outcomes[episode], g(genome, :bayes_reliability), genome;
                            event_kind = :experiment,
                            event_id = "assay10:competence:$seed:$episode:$packet")
                        update_posterior!(state, :outcome_forecast,
                            outcomes[episode], g(genome, :bayes_reliability), genome;
                            event_kind = :experiment,
                            event_id = "assay10:outcome:$seed:$episode:$packet")
                    end
                end
                permission = protector_permission(state,
                    g(genome, :high_stakes), genome; obsolete = true)
                if permission >= g(genome, :permission_threshold)
                    permission_episode == 0 && (permission_episode = episode)
                    update_root!(state, outcomes[episode],
                        dyad.field_weight, genome;
                        event_id = "assay10:root:$seed:$episode")
                else
                    update_registration!(state, true, true, genome;
                        event_id = "assay10:registration:$seed:$episode")
                end
                root_episode == 0 &&
                    state.posterior[:root_now] >= g(genome, :root_revision_begin) &&
                    (root_episode = episode)
            end
            push!(rows, (seed = seed, disposition = disposition,
                scaffold = scaffold, positive_without_scaffold = false,
                permission_episode = permission_episode,
                root_episode = root_episode,
                permission_before_root = permission_episode > 0 &&
                    (root_episode == 0 || permission_episode < root_episode),
                descent = state.posterior[:root_now] >=
                    g(genome, :root_revision_begin),
                root_change = state.posterior[:root_now] - initial_root))
        end
    end
    state = neutral_state(genome)
    initial = state.posterior[:root_now]
    for episode in 1:Int(g(genome, :episodes))
        update_posterior!(state, :partner_trustworthy, true,
            g(genome, :bayes_reliability), genome;
            event_kind = :experiment,
            event_id = "assay10:positive-only:$seed:$episode")
    end
    push!(rows, (seed = seed, disposition = :trustworthy,
        scaffold = :none, positive_without_scaffold = true,
        permission_episode = 0, root_episode = 0,
        permission_before_root = false, descent = false,
        root_change = state.posterior[:root_now] - initial))
    return rows
end

const ASSAY_FUNCTIONS = Dict(
    1 => assay1, 2 => assay2, 3 => assay3, 4 => assay4, 5 => assay5,
    6 => assay6, 7 => assay7, 8 => assay8, 9 => assay9, 10 => assay10)

function run_assay(assay::Int, seed::Int, genome::Genome,
        config::Configuration)
    assay == config.assay ||
        error("configuration assay $(config.assay) cannot run assay $assay")
    haskey(ASSAY_FUNCTIONS, assay) || error("unknown assay $assay")
    return ASSAY_FUNCTIONS[assay](seed, genome, config)
end

function pilot_seeds(assay::Int, genome::Genome)
    count = Int(g(genome, :pilot_worlds))
    first_seed = Int(g(genome, :pilot_seed_base)) +
        assay * Int(g(genome, :pilot_seed_assay_stride))
    last_seed = first_seed + count - 1
    last_seed < Int(g(genome, :reserved_seed_floor)) ||
        error("pilot seed entered reserved block")
    return collect(first_seed:last_seed)
end
