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
