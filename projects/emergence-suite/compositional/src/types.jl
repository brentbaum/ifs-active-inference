const CONTRACT_ID = "ifs-ai-experiment-51-contract"
const CONTRACT_VERSION = "1.0.1"

struct BundleDocuments
    configuration::Dict{String,Any}
    world::Dict{String,Any}
    protocol::Dict{String,Any}
    analysis::Dict{String,Any}
end

struct NodeIR
    id::String
    kind::Symbol
    cardinality::Int
    slot::Int
    active::Bool
end

struct EdgeIR
    id::String
    kind::Symbol
    source::String
    target::String
    initial_state::Symbol
end

struct ChannelIR
    id::String
    source::Symbol
    scope::Vector{String}
    likelihood_family::Symbol
    values::Vector{String}
    bounds::Union{Nothing,Tuple{Float64,Float64}}
    enabled::Bool
end

struct PolicyIR
    id::String
    family::Symbol
    actors::Vector{String}
    actions::Vector{String}
    enabled::Bool
end

struct CandidateIR
    id::String
    structure_node::String
    family::Symbol
    active_edges::Set{String}
    inactive_edges::Set{String}
    ordinal::Int
end

struct FactorIR
    id::String
    values::Vector{String}
    initial_distribution_id::String
end

abstract type DistributionIR end

struct FixedDistributionIR <: DistributionIR
    id::String
    scope::Symbol
    value::Float64
end

struct UniformDistributionIR <: DistributionIR
    id::String
    scope::Symbol
    lower::Float64
    upper::Float64
end

struct IntegerUniformDistributionIR <: DistributionIR
    id::String
    scope::Symbol
    lower::Int
    upper::Int
end

struct BetaDistributionIR <: DistributionIR
    id::String
    scope::Symbol
    alpha::Float64
    beta::Float64
end

struct CategoricalDistributionIR <: DistributionIR
    id::String
    values::Vector{String}
    probabilities::Vector{Float64}
end

struct TransitionDistributionIR <: DistributionIR
    id::String
    values::Vector{String}
    matrix::Matrix{Float64}
end

abstract type ProcessIR end

struct IIDProcessIR <: ProcessIR
    id::String
    target::String
    distribution_id::String
    update_interval::Int
end

struct MarkovProcessIR <: ProcessIR
    id::String
    kind::Symbol
    target::String
    transition_id::String
    update_interval::Int
end

struct ChangePointProcessIR <: ProcessIR
    id::String
    target::String
    before_id::String
    after_id::String
    change_time_id::String
    update_interval::Int
end

struct ActionProcessIR <: ProcessIR
    id::String
    target::String
    action::String
    baseline_id::String
    action_id::String
    update_interval::Int
end

struct CoupledProcessIR <: ProcessIR
    id::String
    target::String
    source_factors::Vector{String}
    transition_ids::Vector{String}
    update_interval::Int
end

struct EmissionIR
    id::String
    source_factors::Vector{String}
    channel_id::String
    likelihood_family::Symbol
    conditional_distribution_ids::Vector{String}
    means::Vector{Float64}
    noise_scale_id::Union{Nothing,String}
    reliability_id::String
    masked_scope::Set{String}
end

abstract type OutcomeIR end

struct ActionOutcomeIR <: OutcomeIR
    id::String
    action::String
    source_factors::Vector{String}
    success_probabilities::Vector{Float64}
    exposure_values::Vector{Float64}
end

struct HazardOutcomeIR <: OutcomeIR
    id::String
    source_factors::Vector{String}
    probabilities::Vector{Float64}
    mitigating_actions::Set{String}
end

struct ContingencyIR
    id::String
    action::String
    process_id::String
    enabled::Bool
end

struct CompiledModel
    genome_id::String
    configuration_id::String
    initializer_id::String
    history_generator_id::String
    action_reconciler_id::String
    world_id::String
    family::Symbol
    horizon::Int
    episode_length::Int
    development_horizon::Int
    seed_namespace::String
    development_emission_ids::Vector{String}
    nodes::Dict{String,NodeIR}
    edges::Dict{String,EdgeIR}
    channels::Dict{String,ChannelIR}
    policies::Dict{String,PolicyIR}
    candidates::Dict{String,CandidateIR}
    factors::Dict{String,FactorIR}
    distributions::Dict{String,DistributionIR}
    processes::Dict{String,ProcessIR}
    emissions::Dict{String,EmissionIR}
    outcomes::Dict{String,OutcomeIR}
    contingencies::Dict{String,ContingencyIR}
    genome::Dict{String,Float64}
    action_costs::Dict{String,Float64}
    consumption::Dict{String,String}
end

struct TriggerIR
    kind::Symbol
    field::String
    comparator::Symbol
    value::Any
end

abstract type EventIR end

struct ObservationEventIR <: EventIR
    id::String
    time::Int
    kind::Symbol
    source::Symbol
    channel_id::String
    emission_id::Union{Nothing,String}
    generator_id::Union{Nothing,String}
    repeat::Int
    interval::Int
    trigger::Union{Nothing,TriggerIR}
end

struct InterventionEventIR <: EventIR
    id::String
    time::Int
    intervention_id::String
    trigger::Union{Nothing,TriggerIR}
end

struct StopEventIR <: EventIR
    id::String
    time::Int
    rule_id::String
    trigger::Union{Nothing,TriggerIR}
end

struct ArmIR
    id::String
    world_id::String
    events::Vector{EventIR}
end

struct InterventionIR
    id::String
    target_kind::Symbol
    target_id::String
    operation::Symbol
end

struct StoppingRuleIR
    id::String
    kind::Symbol
    max_time::Int
    field::Union{Nothing,String}
    comparator::Union{Nothing,Symbol}
    threshold::Union{Nothing,Float64}
    persistence::Int
end

struct PairedComponentIR
    kind::Symbol
    id::String
end

struct PairedStreamIR
    id::String
    arms::Set{String}
    components::Set{Tuple{Symbol,String}}
end

struct EvidenceBudgetIR
    id::String
    arms::Set{String}
    arm_pairs::Vector{Tuple{String,String}}
    metric::Symbol
    scope::Set{String}
    tolerance::Float64
end

struct ControlIR
    id::String
    kind::Symbol
    treatment_arms::Set{String}
    control_arms::Set{String}
    intervention_ids::Set{String}
    budget_ids::Set{String}
    explanation::Union{Nothing,String}
end

struct ProtocolIR
    protocol_id::String
    requested_fields::Vector{String}
    interventions::Dict{String,InterventionIR}
    arms::Vector{ArmIR}
    stopping_rules::Dict{String,StoppingRuleIR}
    paired_streams::Vector{PairedStreamIR}
    budgets::Dict{String,EvidenceBudgetIR}
    controls::Dict{String,ControlIR}
end

struct PredicateIR
    field::String
    comparator::Symbol
    value::Any
end

abstract type ExpressionIR end
struct LiteralExpr <: ExpressionIR
    value::Any
end
struct FieldExpr <: ExpressionIR
    path::String
end
struct WhereExpr <: ExpressionIR
    source::ExpressionIR
    predicates::Vector{PredicateIR}
end
struct UnaryExpr <: ExpressionIR
    op::Symbol
    arg::ExpressionIR
end
struct BinaryExpr <: ExpressionIR
    op::Symbol
    left::ExpressionIR
    right::ExpressionIR
end
struct TemporalExpr <: ExpressionIR
    op::Symbol
    arg::ExpressionIR
    steps::Int
    comparator::Union{Nothing,Symbol}
    threshold::Any
    persistence::Int
    time_path::Union{Nothing,String}
end
struct AggregateExpr <: ExpressionIR
    op::Symbol
    arg::ExpressionIR
    probability::Union{Nothing,Float64}
end
struct ArmDifferenceExpr <: ExpressionIR
    value::ExpressionIR
    treatment::String
    control::String
end
struct DifferenceInDifferencesExpr <: ExpressionIR
    value::ExpressionIR
    treatment_present::String
    treatment_absent::String
    control_present::String
    control_absent::String
end
struct ClassificationExpr <: ExpressionIR
    op::Symbol
    prediction_path::String
    truth_path::String
    strata_path::Union{Nothing,String}
end
struct ArgmaxExpr <: ExpressionIR
    evidence_path::String
    selected_path::String
end
struct EventPrecedesExpr <: ExpressionIR
    left::ExpressionIR
    right::ExpressionIR
end
struct BudgetErrorExpr <: ExpressionIR
    budget_id::String
end
struct SurvivalExpr <: ExpressionIR
    arg::ExpressionIR
    comparator::Symbol
    threshold::Any
end

struct IntervalIR
    method::Symbol
    level::Union{Nothing,Float64}
    resamples::Int
end

struct EstimandIR
    id::String
    status::Symbol
    provenance::Symbol
    expression::ExpressionIR
    aggregation::Symbol
    interval::IntervalIR
    control_ids::Set{String}
end

struct DecisionIR
    id::String
    estimand_id::String
    comparator::Symbol
    threshold::Any
    interval_requirement::Symbol
end

struct AnalysisIR
    analysis_id::String
    unit::Symbol
    tie_handling::Symbol
    non_crossing::Symbol
    missing_cells::Symbol
    non_finite::Symbol
    estimands::Vector{EstimandIR}
    decisions::Vector{DecisionIR}
end

struct Observation
    event_id::String
    time::Int
    source::Symbol
    channel_id::String
    emission_id::Union{Nothing,String}
    scope::Vector{String}
    masked_scope::Set{String}
    family::Symbol
    value::Union{String,Float64}
    reliability::Float64
    effective_scale::Union{Nothing,Float64}
    log_likelihoods::Dict{String,Float64}
    delivered_log_likelihood::Float64
    marginal_equivalence_error::Float64
    is_imaginal::Bool
    rng_namespace::String
end

Observation(event_id::String, time::Int, source::Symbol, channel_id::String,
    emission_id::Union{Nothing,String}, scope::Vector{String},
    masked_scope::Set{String}, family::Symbol, value::Union{String,Float64},
    reliability::Float64, log_likelihoods::Dict{String,Float64},
    delivered_log_likelihood::Float64, marginal_equivalence_error::Float64,
    is_imaginal::Bool, rng_namespace::String) =
    Observation(event_id, time, source, channel_id, emission_id, scope,
        masked_scope, family, value, reliability, nothing, log_likelihoods,
        delivered_log_likelihood, marginal_equivalence_error, is_imaginal,
        rng_namespace)

mutable struct WorldState
    truth::Dict{String,String}
    contingency_enabled::Dict{String,Bool}
    scalar_cache::Dict{Tuple{String,Int},Float64}
    change_times::Dict{String,Int}
end

mutable struct OrganismState
    factor_beliefs::Dict{String,Vector{Float64}}
    node_beliefs::Dict{String,Vector{Float64}}
    node_values::Dict{String,Dict{String,Float64}}
    edge_enabled::Dict{String,Bool}
    edge_strength::Dict{String,Float64}
    channel_enabled::Dict{String,Bool}
    action_enabled::Dict{String,Bool}
    policy_posterior::Dict{String,Float64}
    policy_gfe::Dict{String,Float64}
    structure_evidence::Dict{String,Float64}
    structure_complexity::Dict{String,Float64}
    likelihood_counts::Dict{String,Vector{Float64}}
    transition_counts::Dict{String,Matrix{Float64}}
    transition_prior::Dict{String,Vector{Float64}}
    policy_counts::Dict{Tuple{String,String},Vector{Float64}}
    access_counts::Dict{String,Vector{Float64}}
    joint_policy_counts::Dict{String,Vector{Float64}}
    joint_access_counts::Dict{String,Vector{Float64}}
    trust_counts::Dict{Tuple{String,String},Vector{Float64}}
    structure_selection::Dict{String,String}
    structure_stability::Dict{String,Int}
    selected_policy_label::Union{Nothing,String}
    selected_action::Union{Nothing,String}
    previous_action::Union{Nothing,String}
    action_success::Union{Nothing,Bool}
    delivered_exposure::Union{Nothing,Float64}
    potential_hazard::Union{Nothing,Bool}
    realized_hazard::Union{Nothing,Bool}
    observation_count::Int
    update_count::Int
end

struct InitializationAuditRow
    seed::UInt64
    arm::String
    tick::Int
    time::Int
    emission_id::String
    rng_namespace::String
    update_provenance::String
    model_candidates::Vector{String}
end

abstract type AbstractTraceRow end

struct EventTraceRow <: AbstractTraceRow
    seed::UInt64
    arm::String
    time::Int
    episode::Int
    row_index::Int
    event_index::Int
    event_id::String
    event_kind::Symbol
    executed::Bool
    fields::Dict{String,Any}
end

struct TickTraceRow <: AbstractTraceRow
    seed::UInt64
    arm::String
    time::Int
    episode::Int
    row_index::Int
    stopped::Bool
    stop_reason::String
    fields::Dict{String,Any}
end

mutable struct TraceTable
    rows::Vector{AbstractTraceRow}
    budgets::Dict{String,EvidenceBudgetIR}
    horizon::Int
    initialization_rows::Vector{InitializationAuditRow}
end
TraceTable() = TraceTable(AbstractTraceRow[], Dict{String,EvidenceBudgetIR}(),
    0, InitializationAuditRow[])
TraceTable(rows::Vector{AbstractTraceRow},
    budgets::Dict{String,EvidenceBudgetIR}, horizon::Int) =
    TraceTable(rows, budgets, horizon, InitializationAuditRow[])

struct EvaluatedEstimand
    id::String
    value::Any
    lower::Union{Nothing,Float64}
    upper::Union{Nothing,Float64}
    expression_ast::String
    source_row_hashes::Vector{String}
end

struct EvaluationResult
    estimands::Dict{String,EvaluatedEstimand}
    decisions::Dict{String,Bool}
end
