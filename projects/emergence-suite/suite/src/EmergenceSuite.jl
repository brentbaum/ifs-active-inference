module EmergenceSuite

include("IO.jl")
include("Config.jl")
include("Reproducibility.jl")
include("DiscreteCore.jl")
include("EFE.jl")
include("StructureLearning.jl")
include("BMR.jl")
include("Criteria.jl")
include("DummyExperiment.jl")
include("sims/sim1/Sim1.jl")
include("sims/sim2/Sim2.jl")
include("sims/sim3/Sim3.jl")
include("sims/sim4/Sim4.jl")
include("sims/sim5/Sim5.jl")
include("sims/sim6a/Sim6a.jl")
include("sims/sim6b/Sim6b.jl")
include("Runner.jl")

using .Config: ExperimentConfig, load_config, config_snapshot
using .Criteria: Criterion, evaluate_criteria, write_criteria_results
using .Runner: run_config

export ExperimentConfig,
       Criterion,
       config_snapshot,
       evaluate_criteria,
       load_config,
       run_config,
       write_criteria_results

end
