@model function sim3_blt_hgf_model(rho, kappa, omega, v_h, v_z, v_y, h_prev_mean, h_prev_var, x_prev_mean, x_prev_var, y)
    h_prev ~ Normal(mean = h_prev_mean, var = h_prev_var)
    x_prev ~ Normal(mean = rho * x_prev_mean, var = rho^2 * x_prev_var + 1e-6)
    h_t ~ Normal(mean = h_prev, var = v_h)
    z_t ~ Normal(mean = h_t, var = v_z)
    x_t ~ GCV(x_prev, z_t, kappa, omega)
    y ~ Normal(mean = x_t, var = v_y)
end

@constraints function sim3_blt_hgf_constraints()
    q(x_t, z_t, h_t, x_prev) = q(x_t, x_prev)q(z_t, h_t)
end

@meta function sim3_blt_hgf_meta()
    GCV(x_prev, x_t, z_t) -> GCVMetadata(GaussHermiteCubature(31))
end

function sim3_blt_hgf_infer(sequence, config::Sim3Config)
    autoupdates = @autoupdates begin
        h_prev_mean, h_prev_var = mean_var(q(h_t))
        x_prev_mean, x_prev_var = mean_var(q(x_t))
    end

    init = @initialization begin
        q(h_t) = NormalMeanVariance(sequence.params.h_prior_mean, sequence.params.h_prior_var)
        q(z_t) = NormalMeanVariance(sequence.params.h_prior_mean, sequence.params.h_prior_var)
        q(x_t) = NormalMeanVariance(sequence.params.x_prior_mean, sequence.params.x_prior_var)
    end

    result = infer(
        model = sim3_blt_hgf_model(
            rho = config.rho,
            kappa = config.kappa,
            omega = config.omega,
            v_h = sequence.params.v_h,
            v_z = config.v_z,
            v_y = sequence.params.v_y
        ),
        constraints = sim3_blt_hgf_constraints(),
        meta = sim3_blt_hgf_meta(),
        data = (y = sequence.y,),
        autoupdates = autoupdates,
        initialization = init,
        keephistory = length(sequence.y),
        historyvars = (x_t = KeepLast(), z_t = KeepLast(), h_t = KeepLast()),
        iterations = config.vmp_iters,
        free_energy = true,
        autostart = true
    )

    x_hist = result.history[:x_t]
    z_hist = result.history[:z_t]
    h_hist = result.history[:h_t]
    return (
        x_mean = mean.(x_hist),
        x_var = var.(x_hist),
        z_mean = mean.(z_hist),
        z_var = var.(z_hist),
        h_mean = mean.(h_hist),
        h_var = var.(h_hist),
        free_energy = result.free_energy_history,
        raw = result
    )
end
