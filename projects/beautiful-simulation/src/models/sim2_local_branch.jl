function sim2_local_branch_prior(config::Sim2Config; bias_probe::Bool = false)
    prior = zeros(Float64, 32)
    g_prior = bias_probe ? [config.bias_g_prior, 1.0 - config.bias_g_prior] : [0.5, 0.5]
    phi_prior = bias_probe ? [config.bias_phi_bind_prior, 1.0 - config.bias_phi_bind_prior] : [0.5, 0.5]
    z_prior = [0.5, 0.5]
    for g in 1:2, phi1 in 1:2, phi2 in 1:2, z1 in 1:2, z2 in 1:2
        idx = flatten_state([g, phi1, phi2, z1, z2], [2, 2, 2, 2, 2])
        prior[idx] = g_prior[g] * phi_prior[phi1] * phi_prior[phi2] * z_prior[z1] * z_prior[z2]
    end
    return prior ./ sum(prior)
end

function build_sim2_local_branch_components(config::Sim2Config; bias_probe::Bool = false)
    A_g = make_sticky_matrix(2, config.g_diag, config.g_offdiag)
    A_phi = make_sticky_matrix(2, config.phi_diag, config.phi_offdiag)
    n_joint = 32
    transition = zeros(Float64, n_joint, n_joint)
    B1 = zeros(Float64, 2, n_joint)
    B2 = zeros(Float64, 2, n_joint)

    for g in 1:2, phi1 in 1:2, phi2 in 1:2, z1 in 1:2, z2 in 1:2
        idx = flatten_state([g, phi1, phi2, z1, z2], [2, 2, 2, 2, 2])
        r1 = phi1 == BIND ? config.r_obs_bind : config.r_obs_frag
        r2 = phi2 == BIND ? config.r_obs_bind : config.r_obs_frag
        B1[:, idx] = binary_emission(r1, z1)
        B2[:, idx] = binary_emission(r2, z2)
        for g_next in 1:2, phi1_next in 1:2, phi2_next in 1:2, z1_next in 1:2, z2_next in 1:2
            idx_next = flatten_state([g_next, phi1_next, phi2_next, z1_next, z2_next], [2, 2, 2, 2, 2])
            rho1 = phi1_next == BIND ? config.rho_bind : config.rho_frag
            rho2 = phi2_next == BIND ? config.rho_bind : config.rho_frag
            pz1 = z1_next == g_next ? rho1 : 1.0 - rho1
            pz2 = z2_next == g_next ? rho2 : 1.0 - rho2
            transition[idx_next, idx] = A_g[g_next, g] * A_phi[phi1_next, phi1] * A_phi[phi2_next, phi2] * pz1 * pz2
        end
    end

    prior = sim2_local_branch_prior(config; bias_probe)
    return (; transition, B1, B2, prior)
end

function sim2_local_branch_infer(episode, config::Sim2Config; bias_probe::Bool = false)
    parts = build_sim2_local_branch_components(config; bias_probe)
    bundle = joint_hmm_inference_bundle(episode.o1, episode.o2, parts.transition, parts.B1, parts.B2, parts.prior)
    dims = [2, 2, 2, 2, 2]
    smoothed_g_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 1)
    filtered_g_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 1)
    smoothed_z1_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 4)
    filtered_z1_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 4)
    smoothed_z2_posteriors = marginalize_joint_rows(bundle.smoothed_joint_posteriors, dims, 5)
    filtered_z2_posteriors = marginalize_joint_rows(bundle.filtered_joint_posteriors, dims, 5)
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
