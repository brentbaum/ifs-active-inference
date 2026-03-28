function save_plot(path::AbstractString, plt)
    mkpath(dirname(path))
    savefig(plt, path)
    return path
end
