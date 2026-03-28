function build_sim1_blt_global_components(config::Sim1Config)
    A_s = make_sticky_matrix(config.n_states, config.state_diag, config.state_offdiag)
    A_phi = make_sticky_matrix(config.n_contexts, config.context_diag, config.context_offdiag)
    table = sim1_reliability_table(config)
    Bv_ctx = [make_emission(table.r_vision[i], table.shift_vision[i]) for i in 1:config.n_contexts]
    Ba_ctx = [make_emission(table.r_audio[i], table.shift_audio[i]) for i in 1:config.n_contexts]

    n_joint = config.n_states * config.n_contexts
    transition = zeros(Float64, n_joint, n_joint)
    Bv = zeros(Float64, 4, n_joint)
    Ba = zeros(Float64, 4, n_joint)

    for s in 1:config.n_states, phi in 1:config.n_contexts
        idx = joint_index_s_phi(s, phi; n_s = config.n_states, n_phi = config.n_contexts)
        Bv[:, idx] = Bv_ctx[phi][:, s]
        Ba[:, idx] = Ba_ctx[phi][:, s]
        for s_next in 1:config.n_states, phi_next in 1:config.n_contexts
            idx_next = joint_index_s_phi(s_next, phi_next; n_s = config.n_states, n_phi = config.n_contexts)
            transition[idx_next, idx] = A_s[s_next, s] * A_phi[phi_next, phi]
        end
    end

    prior = fill(1.0 / n_joint, n_joint)
    return (; transition, Bv, Ba, prior)
end

function sim1_blt_global_infer(episode, config::Sim1Config)
    parts = build_sim1_blt_global_components(config)
    bundle = joint_hmm_inference_bundle(
        episode.ov,
        episode.oa,
        parts.transition,
        parts.Bv,
        parts.Ba,
        parts.prior
    )

    dims = [config.n_states, config.n_contexts]
    smoothed_world_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 1)
    smoothed_phi_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 2)
    filtered_world_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 1)
    filtered_phi_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 2)

    table = sim1_reliability_table(config)
    filtered_future_v = [
        sum(filtered_phi_posteriors[t, phi] * table.r_vision[phi] for phi in 1:config.n_contexts)
        for t in 1:(size(filtered_phi_posteriors, 1) - 1)
    ]
    filtered_future_a = [
        sum(filtered_phi_posteriors[t, phi] * table.r_audio[phi] for phi in 1:config.n_contexts)
        for t in 1:(size(filtered_phi_posteriors, 1) - 1)
    ]
    smoothed_future_v = [
        sum(smoothed_phi_posteriors[t, phi] * table.r_vision[phi] for phi in 1:config.n_contexts)
        for t in 1:(size(smoothed_phi_posteriors, 1) - 1)
    ]
    smoothed_future_a = [
        sum(smoothed_phi_posteriors[t, phi] * table.r_audio[phi] for phi in 1:config.n_contexts)
        for t in 1:(size(smoothed_phi_posteriors, 1) - 1)
    ]

    return (
        world_posteriors = smoothed_world_posteriors,
        filtered_world_posteriors = filtered_world_posteriors,
        smoothed_world_posteriors = smoothed_world_posteriors,
        phi_posteriors = smoothed_phi_posteriors,
        filtered_phi_posteriors = filtered_phi_posteriors,
        smoothed_phi_posteriors = smoothed_phi_posteriors,
        phi_v_posteriors = nothing,
        filtered_phi_v_posteriors = nothing,
        smoothed_phi_v_posteriors = nothing,
        phi_a_posteriors = nothing,
        filtered_phi_a_posteriors = nothing,
        smoothed_phi_a_posteriors = nothing,
        future_v = smoothed_future_v,
        future_a = smoothed_future_a,
        filtered_future_v = filtered_future_v,
        filtered_future_a = filtered_future_a,
        smoothed_future_v = smoothed_future_v,
        smoothed_future_a = smoothed_future_a,
        log_evidence = bundle.log_evidence,
        rxinfer_result = bundle.rxinfer_result
    )
end
