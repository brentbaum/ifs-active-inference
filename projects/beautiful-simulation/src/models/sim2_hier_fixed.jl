function build_sim2_hier_fixed_components(config::Sim2Config)
    A_g = make_sticky_matrix(2, config.g_diag, config.g_offdiag)
    n_joint = 8
    transition = zeros(Float64, n_joint, n_joint)
    B1 = zeros(Float64, 2, n_joint)
    B2 = zeros(Float64, 2, n_joint)
    r_obs = (config.r_obs_bind + config.r_obs_frag) / 2

    for g in 1:2, z1 in 1:2, z2 in 1:2
        idx = flatten_state([g, z1, z2], [2, 2, 2])
        B1[:, idx] = binary_emission(r_obs, z1)
        B2[:, idx] = binary_emission(r_obs, z2)
        for g_next in 1:2, z1_next in 1:2, z2_next in 1:2
            idx_next = flatten_state([g_next, z1_next, z2_next], [2, 2, 2])
            pz1 = z1_next == g_next ? config.rho_fixed : 1.0 - config.rho_fixed
            pz2 = z2_next == g_next ? config.rho_fixed : 1.0 - config.rho_fixed
            transition[idx_next, idx] = A_g[g_next, g] * pz1 * pz2
        end
    end

    prior = fill(1.0 / n_joint, n_joint)
    return (; transition, B1, B2, prior)
end

function sim2_hier_fixed_infer(episode, config::Sim2Config; bias_probe::Bool = false)
    parts = build_sim2_hier_fixed_components(config)
    bundle = joint_hmm_inference_bundle(episode.o1, episode.o2, parts.transition, parts.B1, parts.B2, parts.prior)
    dims = [2, 2, 2]
    smoothed_g_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 1)
    filtered_g_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 1)
    smoothed_z1_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 2)
    filtered_z1_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 2)
    smoothed_z2_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 3)
    filtered_z2_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 3)
    return (
        joint_posteriors = bundle.smoothed_joint_posteriors,
        filtered_joint_posteriors = bundle.filtered_joint_posteriors,
        smoothed_joint_posteriors = bundle.smoothed_joint_posteriors,
        g_posteriors = smoothed_g_posteriors,
        filtered_g_posteriors = filtered_g_posteriors,
        smoothed_g_posteriors = smoothed_g_posteriors,
        phi_posteriors = nothing,
        filtered_phi_posteriors = nothing,
        smoothed_phi_posteriors = nothing,
        z1_posteriors = smoothed_z1_posteriors,
        filtered_z1_posteriors = filtered_z1_posteriors,
        smoothed_z1_posteriors = smoothed_z1_posteriors,
        z2_posteriors = smoothed_z2_posteriors,
        filtered_z2_posteriors = filtered_z2_posteriors,
        smoothed_z2_posteriors = smoothed_z2_posteriors,
        log_evidence = bundle.log_evidence,
        rxinfer_result = bundle.rxinfer_result
    )
end
