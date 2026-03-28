const DEFAULT_SEEDS = [11, 23, 37, 53, 71, 97, 131, 173, 211, 251]

default_rng(seed::Int) = StableRNG(seed)

struct_to_namedtuple(value) = (; (name => getfield(value, name) for name in fieldnames(typeof(value)))...)

function git_commit_hash(root::AbstractString = pwd())
    try
        return readchomp(`git -C $root rev-parse HEAD`)
    catch
        return nothing
    end
end

function package_version(name::AbstractString)
    for dep in values(Pkg.dependencies())
        dep.name == name && return isnothing(dep.version) ? nothing : string(dep.version)
    end
    return nothing
end

function active_project_version()
    project_path = Base.active_project()
    if isnothing(project_path) || !isfile(project_path)
        return nothing
    end

    project = TOML.parsefile(project_path)
    version = get(project, "version", nothing)
    return isnothing(version) ? nothing : string(version)
end

function build_reproducibility_metadata(
    config;
    config_path::Union{Nothing, AbstractString} = nothing,
    runtime_seconds::Union{Nothing, Float64} = nothing,
    repo_root::AbstractString = pwd(),
    extra::Dict{String, Any} = Dict{String, Any}()
)
    metadata = Dict{String, Any}(
        "git_commit_hash" => git_commit_hash(repo_root),
        "julia_version" => string(VERSION),
        "rxinfer_version" => package_version("RxInfer"),
        "plots_version" => package_version("Plots"),
        "package_version" => active_project_version(),
        "config_path" => isnothing(config_path) ? nothing : abspath(config_path),
        "config_snapshot" => struct_to_namedtuple(config),
        "runtime_seconds" => runtime_seconds,
        "generated_at_utc" => Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyy-mm-ddTHH:MM:SSZ")
    )
    merge!(metadata, extra)
    return metadata
end
