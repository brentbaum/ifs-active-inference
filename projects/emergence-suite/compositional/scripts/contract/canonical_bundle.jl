#!/usr/bin/env julia

using SHA

const CONTRACT_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const BUNDLE_FILES = [
    "configuration.toml",
    "world.toml",
    "protocol.toml",
    "analysis.toml",
    "interpretation-lock.md",
]
const BLOCK = 512
const ZERO_BLOCKS = zeros(UInt8, 2 * BLOCK)

function fail(message)
    error("canonical bundle: $message")
end

function ascii_bytes(value::AbstractString)
    all(byte < 0x80 for byte in codeunits(value)) ||
        fail("USTAR path is not ASCII: $value")
    return collect(codeunits(value))
end

function put_bytes!(header::Vector{UInt8}, offset::Int, width::Int,
        value::AbstractString)
    bytes = ascii_bytes(value)
    length(bytes) <= width || fail("header value exceeds width $width: $value")
    copyto!(header, offset, bytes, 1, length(bytes))
    return header
end

function octal_field(value::Integer, width::Int)
    value >= 0 || fail("negative USTAR numeric value")
    digits = string(value; base = 8)
    length(digits) <= width - 1 || fail("USTAR numeric value does not fit")
    return lpad(digits, width - 1, '0') * "\0"
end

function canonical_header(path::AbstractString, size::Integer)
    header = zeros(UInt8, BLOCK)
    put_bytes!(header, 1, 100, path)
    put_bytes!(header, 101, 8, octal_field(0o644, 8))
    put_bytes!(header, 109, 8, octal_field(0, 8))
    put_bytes!(header, 117, 8, octal_field(0, 8))
    put_bytes!(header, 125, 12, octal_field(size, 12))
    put_bytes!(header, 137, 12, octal_field(0, 12))
    header[149:156] .= UInt8(' ')
    header[157] = UInt8('0')
    put_bytes!(header, 258, 6, "ustar\0")
    put_bytes!(header, 264, 2, "00")
    put_bytes!(header, 330, 8, octal_field(0, 8))
    put_bytes!(header, 338, 8, octal_field(0, 8))
    checksum = sum(Int, header)
    put_bytes!(header, 149, 8, lpad(string(checksum; base = 8), 6, '0') * "\0 ")
    return header
end

function preflight_payload(path::AbstractString)
    ispath(path) || fail("missing file: $path")
    islink(path) && fail("symlinks are forbidden: $path")
    isfile(path) || fail("not a regular file: $path")
    payload = read(path)
    length(payload) >= 1 || fail("empty files are forbidden: $path")
    length(payload) <= 262_144 || fail("file exceeds 262,144 bytes: $path")
    length(payload) >= 3 && payload[1:3] == UInt8[0xef, 0xbb, 0xbf] &&
        fail("UTF-8 BOM is forbidden: $path")
    any(==(0x00), payload) && fail("NUL is forbidden: $path")
    any(==(0x0d), payload) && fail("CR line endings are forbidden: $path")
    payload[end] == 0x0a || fail("final LF is required: $path")
    length(payload) > 1 && payload[end - 1] == 0x0a &&
        fail("more than one trailing LF is forbidden: $path")
    isvalid(String, payload) || fail("payload is not valid UTF-8: $path")
    return payload
end

function validate_bundle_directory(directory::AbstractString)
    bundle_id = basename(normpath(directory))
    occursin(r"^51-P-[0-9]{2}$", bundle_id) ||
        fail("bundle directory must match 51-P-NN: $directory")
    names = sort(readdir(directory))
    sort(BUNDLE_FILES) == names ||
        fail("bundle must contain exactly the five normative files")
    payloads = Dict(name => preflight_payload(joinpath(directory, name))
        for name in BUNDLE_FILES)
    return bundle_id, payloads
end

function canonical_bytes(bundle_id::AbstractString,
        payloads::AbstractDict{<:AbstractString,<:AbstractVector{UInt8}})
    archive = UInt8[]
    for name in BUNDLE_FILES
        payload = payloads[name]
        append!(archive, canonical_header("$bundle_id/$name", length(payload)))
        append!(archive, payload)
        padding = mod(-length(payload), BLOCK)
        padding > 0 && append!(archive, zeros(UInt8, padding))
    end
    append!(archive, ZERO_BLOCKS)
    return archive
end

function build_bundle(directory::AbstractString, output::AbstractString)
    bundle_id, payloads = validate_bundle_directory(directory)
    archive = canonical_bytes(bundle_id, payloads)
    length(archive) <= 1_048_576 || fail("archive exceeds 1,048,576 bytes")
    open(output, "w") do io
        write(io, archive)
    end
    return (path = String(output), bytes = length(archive),
        sha256 = bytes2hex(sha256(archive)))
end

function parse_octal(field::AbstractVector{UInt8})
    text = strip(replace(String(copy(field)), '\0' => ' '))
    isempty(text) && return 0
    all(character in '0':'7' for character in text) ||
        fail("invalid USTAR octal field")
    return parse(Int, text; base = 8)
end

function header_string(header::Vector{UInt8}, range)
    bytes = header[range]
    stop = findfirst(==(0x00), bytes)
    stop === nothing || (bytes = bytes[1:stop - 1])
    return String(copy(bytes))
end

function verify_header(header::Vector{UInt8}, expected_path::AbstractString,
        expected_size::Integer)
    header_string(header, 1:100) == expected_path ||
        fail("unexpected entry path")
    header_string(header, 101:108) == "0000644" || fail("noncanonical mode")
    parse_octal(header[109:116]) == 0 || fail("nonzero uid")
    parse_octal(header[117:124]) == 0 || fail("nonzero gid")
    parse_octal(header[125:136]) == expected_size || fail("size mismatch")
    parse_octal(header[137:148]) == 0 || fail("nonzero mtime")
    header[157] == UInt8('0') || fail("non-regular typeflag")
    header_string(header, 258:263) == "ustar" || fail("missing USTAR magic")
    header_string(header, 264:265) == "00" || fail("wrong USTAR version")
    isempty(header_string(header, 158:257)) || fail("nonempty linkname")
    isempty(header_string(header, 266:297)) || fail("nonempty uname")
    isempty(header_string(header, 298:329)) || fail("nonempty gname")
    isempty(header_string(header, 346:500)) || fail("nonempty prefix")
    declared = parse_octal(header[149:156])
    check = copy(header)
    check[149:156] .= UInt8(' ')
    declared == sum(Int, check) || fail("header checksum mismatch")
    return true
end

function verify_bundle(path::AbstractString)
    archive = read(path)
    length(archive) <= 1_048_576 || fail("archive exceeds 1,048,576 bytes")
    length(archive) % BLOCK == 0 || fail("archive is not block aligned")
    cursor = 1
    bundle_id = nothing
    payloads = Dict{String,Vector{UInt8}}()
    for expected_name in BUNDLE_FILES
        cursor + BLOCK - 1 <= length(archive) || fail("truncated header")
        header = archive[cursor:cursor + BLOCK - 1]
        cursor += BLOCK
        full_name = header_string(header, 1:100)
        parts = split(full_name, '/')
        length(parts) == 2 || fail("entry must have one directory component")
        current_id, name = parts
        occursin(r"^51-P-[0-9]{2}$", current_id) ||
            fail("invalid challenge directory")
        bundle_id === nothing && (bundle_id = current_id)
        bundle_id == current_id || fail("mixed bundle directories")
        name == expected_name || fail("noncanonical entry order")
        size = parse_octal(header[125:136])
        cursor + size - 1 <= length(archive) || fail("truncated payload")
        payload = archive[cursor:cursor + size - 1]
        verify_header(header, full_name, size)
        preflight_payload_bytes(payload, full_name)
        payloads[name] = payload
        cursor += size
        padding = mod(-size, BLOCK)
        cursor + padding - 1 <= length(archive) || fail("truncated padding")
        padding > 0 && any(!=(0x00), archive[cursor:cursor + padding - 1]) &&
            fail("nonzero payload padding")
        cursor += padding
    end
    remaining = archive[cursor:end]
    remaining == ZERO_BLOCKS || fail("archive must end in exactly two zero blocks")
    rebuilt = canonical_bytes(bundle_id, payloads)
    rebuilt == archive || fail("archive differs from canonical rebuild")
    return (path = String(path), bundle_id = bundle_id, bytes = length(archive),
        sha256 = bytes2hex(sha256(archive)))
end

function preflight_payload_bytes(payload::Vector{UInt8}, label::AbstractString)
    length(payload) >= 1 || fail("empty file: $label")
    length(payload) >= 3 && payload[1:3] == UInt8[0xef, 0xbb, 0xbf] &&
        fail("BOM: $label")
    any(==(0x00), payload) && fail("NUL: $label")
    any(==(0x0d), payload) && fail("CR: $label")
    payload[end] == 0x0a || fail("missing final LF: $label")
    length(payload) > 1 && payload[end - 1] == 0x0a &&
        fail("multiple trailing LF: $label")
    isvalid(String, payload) || fail("invalid UTF-8: $label")
    return true
end

function read_test_vector()
    path = joinpath(CONTRACT_ROOT, "contract", "archive-test-vector.sha256")
    fields = split(strip(read(path, String)))
    length(fields) == 3 || fail("test vector must contain SHA-256, bytes, label")
    return (sha256 = fields[1], bytes = parse(Int, fields[2]), label = fields[3])
end

function self_test()
    dummy = joinpath(CONTRACT_ROOT, "protocols", "public-dummies", "51-P-00")
    expected = read_test_vector()
    mktempdir() do directory
        output = joinpath(directory, "51-P-00.tar")
        built = build_bundle(dummy, output)
        verified = verify_bundle(output)
        built.sha256 == verified.sha256 || fail("build/verify hash mismatch")
        built.bytes == verified.bytes || fail("build/verify byte mismatch")
        built.sha256 == expected.sha256 || fail("test-vector SHA-256 mismatch")
        built.bytes == expected.bytes || fail("test-vector byte-count mismatch")
        println("canonical USTAR self-test passed")
        println("sha256=$(built.sha256)")
        println("bytes=$(built.bytes)")
    end
    return true
end

function usage()
    println("usage:")
    println("  canonical_bundle.jl build BUNDLE_DIRECTORY OUTPUT.tar")
    println("  canonical_bundle.jl verify ARCHIVE.tar")
    println("  canonical_bundle.jl self-test")
end

function main(arguments)
    isempty(arguments) && (usage(); return 2)
    command = arguments[1]
    if command == "build" && length(arguments) == 3
        result = build_bundle(arguments[2], arguments[3])
        println("sha256=$(result.sha256)")
        println("bytes=$(result.bytes)")
        return 0
    elseif command == "verify" && length(arguments) == 2
        result = verify_bundle(arguments[2])
        println("bundle_id=$(result.bundle_id)")
        println("sha256=$(result.sha256)")
        println("bytes=$(result.bytes)")
        return 0
    elseif command == "self-test" && length(arguments) == 1
        self_test()
        return 0
    end
    usage()
    return 2
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main(ARGS))
end
