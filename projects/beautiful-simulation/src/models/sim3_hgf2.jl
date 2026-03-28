@model function sim3_hgf2_model(rho, kappa, omega, z_variance, y_variance, z_prev_mean, z_prev_var, x_prev_mean, x_prev_var, y)
    z_prev ~ Normal(mean = z_prev_mean, var = z_prev_var)
    x_prev ~ Normal(mean = rho * x_prev_mean, var = rho^2 * x_prev_var + 1e-6)
    z_t ~ Normal(mean = z_prev, var = z_variance)
    x_t ~ GCV(x_prev, z_t, kappa, omega)
    y ~ Normal(mean = x_t, var = y_variance)
end

@constraints function sim3_hgf2_constraints()
    q(x_t, z_t, x_prev) = q(x_t, x_prev)q(z_t)
end

@meta function sim3_hgf2_meta()
    GCV(x_prev, x_t, z_t) -> GCVMetadata(GaussHermiteCubature(31))
end

function sim3_hgf2_infer(sequence, config::Sim3Config)
    autoupdates = @autoupdates begin
        z_prev_mean, z_prev_var = mean_var(q(z_t))
        x_prev_mean, x_prev_var = mean_var(q(x_t))
    end

    init = @initialization begin
        q(z_t) = NormalMeanVariance(sequence.params.h_prior_mean, sequence.params.h_prior_var)
        q(x_t) = NormalMeanVariance(sequence.params.x_prior_mean, sequence.params.x_prior_var)
    end

    result = infer(
        model = sim3_hgf2_model(
            rho = config.rho,
            kappa = config.kappa,
            omega = config.omega,
            z_variance = config.v_z,
            y_variance = sequence.params.v_y
        ),
        constraints = sim3_hgf2_constraints(),
        meta = sim3_hgf2_meta(),
        data = (y = sequence.y,),
        autoupdates = autoupdates,
        initialization = init,
        keephistory = length(sequence.y),
        historyvars = (x_t = KeepLast(), z_t = KeepLast()),
        iterations = config.vmp_iters,
        free_energy = true,
        autostart = true
    )

    x_hist = result.history[:x_t]
    z_hist = result.history[:z_t]
    return (
        x_mean = mean.(x_hist),
        x_var = var.(x_hist),
        z_mean = mean.(z_hist),
        z_var = var.(z_hist),
        h_mean = fill(NaN, length(x_hist)),
        h_var = fill(NaN, length(x_hist)),
        free_energy = result.free_energy_history,
        raw = result
    )
end
