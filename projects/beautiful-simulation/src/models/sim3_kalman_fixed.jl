@model function sim3_kalman_fixed_model(rho, process_var, y_var, x_prev_mean, x_prev_var, y)
    x_prev ~ Normal(mean = rho * x_prev_mean, var = rho^2 * x_prev_var + 1e-6)
    x_t ~ Normal(mean = x_prev, var = process_var)
    y ~ Normal(mean = x_t, var = y_var)
end

function sim3_kalman_fixed_infer(sequence, config::Sim3Config)
    autoupdates = @autoupdates begin
        x_prev_mean, x_prev_var = mean_var(q(x_t))
    end

    init = @initialization begin
        q(x_t) = NormalMeanVariance(sequence.params.x_prior_mean, sequence.params.x_prior_var)
    end

    result = infer(
        model = sim3_kalman_fixed_model(
            rho = config.rho,
            process_var = config.kalman_process_var,
            y_var = sequence.params.v_y
        ),
        data = (y = sequence.y,),
        autoupdates = autoupdates,
        initialization = init,
        keephistory = length(sequence.y),
        historyvars = (x_t = KeepLast(),),
        iterations = config.vmp_iters,
        free_energy = true,
        autostart = true
    )

    x_hist = result.history[:x_t]
    x_mean = mean.(x_hist)
    x_var = var.(x_hist)
    return (
        x_mean = x_mean,
        x_var = x_var,
        z_mean = fill(NaN, length(x_mean)),
        z_var = fill(NaN, length(x_mean)),
        h_mean = fill(NaN, length(x_mean)),
        h_var = fill(NaN, length(x_mean)),
        free_energy = result.free_energy_history,
        raw = result
    )
end
