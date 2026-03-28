function sim2_blt_global_prior(config::Sim2Config; bias_probe::Bool = false)
    prior = zeros(Float64, 16)
    g_prior = bias_probe ? [config.bias_g_prior, 1.0 - config.bias_g_prior] : [0.5, 0.5]
    phi_prior = bias_probe ? [config.bias_phi_bind_prior, 1.0 - config.bias_phi_bind_prior] : [0.5, 0.5]
    z_prior = [0.5, 0.5]
    for g in 1:2, phi in 1:2, z1 in 1:2, z2 in 1:2
        idx = flatten_state([g, phi, z1, z2], [2, 2, 2, 2])
        prior[idx] = g_prior[g] * phi_prior[phi] * z_prior[z1] * z_prior[z2]
    end
    return prior ./ sum(prior)
end

function build_sim2_blt_global_components(config::Sim2Config; bias_probe::Bool = false)
    A_phi = make_sticky_matrix(2, config.phi_diag, config.phi_offdiag)
    n_joint = 16
    transition = zeros(Float64, n_joint, n_joint)
    B1 = zeros(Float64, 2, n_joint)
    B2 = zeros(Float64, 2, n_joint)

    for g in 1:2, phi in 1:2, z1 in 1:2, z2 in 1:2
        idx = flatten_state([g, phi, z1, z2], [2, 2, 2, 2])
        r_obs = phi == BIND ? config.r_obs_bind : config.r_obs_frag
        B1[:, idx] = binary_emission(r_obs, z1)
        B2[:, idx] = binary_emission(r_obs, z2)
        for g_next in 1:2, phi_next in 1:2, z1_next in 1:2, z2_next in 1:2
            idx_next = flatten_state([g_next, phi_next, z1_next, z2_next], [2, 2, 2, 2])
            g_diag = phi_next == BIND ? config.g_diag_bind : config.g_diag_frag
            A_g = make_sticky_matrix(2, g_diag, 1.0 - g_diag)
            rho = phi_next == BIND ? config.rho_bind : config.rho_frag
            pz1 = z1_next == g_next ? rho : 1.0 - rho
            pz2 = z2_next == g_next ? rho : 1.0 - rho
            transition[idx_next, idx] = A_g[g_next, g] * A_phi[phi_next, phi] * pz1 * pz2
        end
    end

    prior = sim2_blt_global_prior(config; bias_probe)
    return (; transition, B1, B2, prior)
end

function sim2_blt_global_infer(episode, config::Sim2Config; bias_probe::Bool = false)
    parts = build_sim2_blt_global_components(config; bias_probe)
    bundle = joint_hmm_inference_bundle(episode.o1, episode.o2, parts.transition, parts.B1, parts.B2, parts.prior)
    dims = [2, 2, 2, 2]
    smoothed_g_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 1)
    filtered_g_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 1)
    smoothed_phi_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 2)
    filtered_phi_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 2)
    smoothed_z1_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 3)
    filtered_z1_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 3)
    smoothed_z2_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 4)
    filtered_z2_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 4)
    return (
        joint_posteriors = bundle.smoothed_joint_posteriors,
        filtered_joint_posteriors = bundle.filtered_joint_posteriors,
        smoothed_joint_posteriors = bundle.smoothed_joint_posteriors,
        g_posteriors = smoothed_g_posteriors,
        filtered_g_posteriors = filtered_g_posteriors,
        smoothed_g_posteriors = smoothed_g_posteriors,
        phi_posteriors = smoothed_phi_posteriors,
        filtered_phi_posteriors = filtered_phi_posteriors,
        smoothed_phi_posteriors = smoothed_phi_posteriors,
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
