# Canonical sealed-bundle archive convention

Version `ustar-51-v1` defines the exact bytes hashed for every 51-P challenge.
Platform `tar` output is not canonical.

## Input

The input is one directory whose basename matches `51-P-[0-9]{2}` and contains
exactly these five regular files in this order:

1. `configuration.toml`
2. `world.toml`
3. `protocol.toml`
4. `analysis.toml`
5. `interpretation-lock.md`

No directory entry is stored in the archive.

Each file must:

- be UTF-8 without BOM;
- contain LF line endings only;
- end in exactly one LF;
- contain no NUL;
- be a regular file, not a symlink;
- contain at most `262,144` bytes.

The builder rejects nonconforming input and never normalizes it.

## Header

Each file is encoded as one POSIX USTAR regular-file record:

- `name`: `<challenge-id>/<filename>`, ASCII
- `mode`: `0000644`
- `uid`: `0000000`
- `gid`: `0000000`
- `size`: eleven-digit octal payload length
- `mtime`: `00000000000`
- checksum: six-digit octal, NUL, space
- `typeflag`: ASCII `0`
- `linkname`: empty
- `magic`: `ustar\0`
- `version`: `00`
- `uname`, `gname`, `prefix`: empty
- device fields: zero
- all unspecified header bytes: zero

Numeric fields end in NUL. During checksum calculation, all eight checksum bytes
are ASCII spaces. Payloads are padded with zero bytes to a 512-byte boundary.

The archive ends with exactly two 512-byte zero blocks and no record padding.
Its total size is at most `1,048,576` bytes.

## Seal

The committed seal records:

- archive convention `ustar-51-v1`;
- SHA-256 of the exact uncompressed `.tar` bytes;
- exact archive byte count;
- encrypted custody-object SHA-256 and byte count, when encryption is used.

Sol retains and later reveals the exact `.tar` bytes. Regeneration is not the
primary custody path.

## Test vector

`protocols/public-dummies/51-P-00/` is the non-secret test vector.
`contract/archive-test-vector.sha256` records the expected archive hash and byte
count. `scripts/contract/canonical_bundle.jl self-test` builds with the Julia
builder and checks the golden vector. `scripts/contract/independent_verify.py`
separately parses and reconstructs every header in Python and checks the same
golden SHA-256/byte count. The authoritative validator requires both.
