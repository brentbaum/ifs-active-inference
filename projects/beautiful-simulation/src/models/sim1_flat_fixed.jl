function build_sim1_flat_fixed_components(config::Sim1Config; context_override::Union{Nothing, Int} = nothing)
    A_s = make_sticky_matrix(config.n_states, config.state_diag, config.state_offdiag)
    table = sim1_reliability_table(config)
    if isnothing(context_override)
        Bv = zeros(Float64, 4, 4)
        Ba = zeros(Float64, 4, 4)
        for ctx in 1:config.n_contexts
            Bv .+= make_emission(table.r_vision[ctx], table.shift_vision[ctx])
            Ba .+= make_emission(table.r_audio[ctx], table.shift_audio[ctx])
        end
        Bv ./= config.n_contexts
        Ba ./= config.n_contexts
    else
        Bv = make_emission(table.r_vision[context_override], table.shift_vision[context_override])
        Ba = make_emission(table.r_audio[context_override], table.shift_audio[context_override])
    end
    prior = fill(1.0 / config.n_states, config.n_states)
    return (; transition = A_s, Bv, Ba, prior)
end

function sim1_flat_fixed_infer(episode, config::Sim1Config; context_override::Union{Nothing, Int} = nothing)
    parts = build_sim1_flat_fixed_components(config; context_override)
    bundle = joint_hmm_inference_bundle(
        episode.ov,
        episode.oa,
        parts.transition,
        parts.Bv,
        parts.Ba,
        parts.prior
    )

    phi_constant = sim1_reliability_table(config)
    p_v = fill(mean(phi_constant.r_vision), length(episode.ov) - 1)
    p_a = fill(mean(phi_constant.r_audio), length(episode.oa) - 1)

    return (
        world_posteriors = bundle.smoothed_joint_posteriors,
        filtered_world_posteriors = bundle.filtered_joint_posteriors,
        smoothed_world_posteriors = bundle.smoothed_joint_posteriors,
        phi_posteriors = nothing,
        filtered_phi_posteriors = nothing,
        smoothed_phi_posteriors = nothing,
        phi_v_posteriors = nothing,
        filtered_phi_v_posteriors = nothing,
        smoothed_phi_v_posteriors = nothing,
        phi_a_posteriors = nothing,
        filtered_phi_a_posteriors = nothing,
        smoothed_phi_a_posteriors = nothing,
        future_v = p_v,
        future_a = p_a,
        filtered_future_v = p_v,
        filtered_future_a = p_a,
        smoothed_future_v = p_v,
        smoothed_future_a = p_a,
        log_evidence = bundle.log_evidence,
        rxinfer_result = bundle.rxinfer_result
    )
end
