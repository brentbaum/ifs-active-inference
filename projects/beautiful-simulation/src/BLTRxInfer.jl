module BLTRxInfer

using CSV
using DataFrames
using Dates
using Distributions
using JSON3
using LinearAlgebra
using Plots
using Pkg
using Random
using RxInfer
using StableRNGs
using Statistics
using TOML
using YAML

include("utils/indexing.jl")
include("utils/metrics.jl")
include("utils/io.jl")
include("utils/plotting.jl")
include("utils/reproducibility.jl")

include("envs/sensor_fusion.jl")
include("envs/ambiguous_binding.jl")
include("envs/phase_diagram.jl")

include("models/sim1_common.jl")
include("models/sim1_flat_fixed.jl")
include("models/sim1_local_precision.jl")
include("models/sim1_blt_global.jl")
include("models/sim2_hier_fixed.jl")
include("models/sim2_local_branch.jl")
include("models/sim2_blt_global.jl")
include("models/sim3_kalman_fixed.jl")
include("models/sim3_hgf2.jl")
include("models/sim3_blt_hgf.jl")

include("runners/run_sim1.jl")
include("runners/run_sim2.jl")
include("runners/run_sim3.jl")

export DEFAULT_SEEDS,
       one_hot,
       flatten_state,
       unflatten_state,
       joint_index_s_phi,
       inverse_joint_index_s_phi,
       joint_index_s_phi_phi,
       inverse_joint_index_s_phi_phi,
       marginalize_joint,
       marginalize_joint_rows,
       safe_mean,
       expected_calibration_error,
       state_accuracy,
       negative_log_likelihood,
       matrix_is_column_stochastic,
       rmse,
       coverage_90,
       micro_switch_rate,
       mean_dwell,
        ensure_dir,
        write_json,
        write_rows_csv,
       save_plot,
       default_rng,
       Sim1Config,
       BG,
       VG,
       AG,
       BP,
       default_sim1_config,
       load_sim1_config,
       make_sticky_matrix,
       make_emission,
       sim1_reliability_table,
       generate_sim1_episode,
       generate_sim1_dataset,
       build_sim1_flat_fixed_components,
       build_sim1_local_precision_components,
       build_sim1_blt_global_components,
       infer_joint_hmm_rxinfer,
       forward_filter_joint_hmm,
       sim1_flat_fixed_infer,
       sim1_local_precision_infer,
       sim1_blt_global_infer,
       run_sim1,
       Sim2Config,
       BIND,
       FRAG,
       default_sim2_config,
       load_sim2_config,
       generate_sim2_dataset,
       build_sim2_hier_fixed_components,
       build_sim2_local_branch_components,
       build_sim2_blt_global_components,
       sim2_hier_fixed_infer,
       sim2_local_branch_infer,
       sim2_blt_global_infer,
       run_sim2,
       Sim3Config,
       default_sim3_config,
       load_sim3_config,
       generate_sim3_sequence,
       sim3_kalman_fixed_infer,
       sim3_hgf2_infer,
       sim3_blt_hgf_infer,
       run_sim3

end
