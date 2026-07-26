#!/usr/bin/env python3

"""Independent verifier for Experiment 51 canonical USTAR bytes."""

from __future__ import annotations

import hashlib
import pathlib
import re
import sys

BLOCK = 512
FILES = (
    "configuration.toml",
    "world.toml",
    "protocol.toml",
    "analysis.toml",
    "interpretation-lock.md",
)


def fail(message: str) -> None:
    raise ValueError(f"independent USTAR verifier: {message}")


def field(header: bytes, start: int, width: int) -> bytes:
    return header[start : start + width]


def text_field(header: bytes, start: int, width: int) -> str:
    return field(header, start, width).split(b"\0", 1)[0].decode("ascii")


def octal_field(header: bytes, start: int, width: int) -> int:
    raw = field(header, start, width).replace(b"\0", b" ").strip()
    if not raw:
        return 0
    if not re.fullmatch(rb"[0-7]+", raw):
        fail("invalid octal field")
    return int(raw, 8)


def number(value: int, width: int) -> bytes:
    digits = f"{value:o}".encode("ascii")
    if len(digits) > width - 1:
        fail("numeric field overflow")
    return b"0" * (width - 1 - len(digits)) + digits + b"\0"


def canonical_header(path: str, size: int) -> bytes:
    encoded = path.encode("ascii")
    if len(encoded) > 100:
        fail("path exceeds name field")
    header = bytearray(BLOCK)
    header[0 : len(encoded)] = encoded
    header[100:108] = number(0o644, 8)
    header[108:116] = number(0, 8)
    header[116:124] = number(0, 8)
    header[124:136] = number(size, 12)
    header[136:148] = number(0, 12)
    header[148:156] = b" " * 8
    header[156:157] = b"0"
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    header[329:337] = number(0, 8)
    header[337:345] = number(0, 8)
    checksum = sum(header)
    header[148:156] = f"{checksum:06o}".encode("ascii") + b"\0 "
    return bytes(header)


def preflight(payload: bytes, label: str) -> None:
    if not payload:
        fail(f"empty payload: {label}")
    if payload.startswith(b"\xef\xbb\xbf"):
        fail(f"BOM: {label}")
    if b"\0" in payload or b"\r" in payload:
        fail(f"NUL/CR: {label}")
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        fail(f"noncanonical final LF: {label}")
    try:
        payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        fail(f"invalid UTF-8: {label}: {error}")


def verify(path: pathlib.Path) -> tuple[str, int]:
    archive = path.read_bytes()
    if len(archive) % BLOCK:
        fail("archive is not block aligned")
    cursor = 0
    bundle_id: str | None = None
    rebuilt = bytearray()
    for expected_name in FILES:
        header = archive[cursor : cursor + BLOCK]
        if len(header) != BLOCK:
            fail("truncated header")
        cursor += BLOCK
        full_name = text_field(header, 0, 100)
        parts = full_name.split("/")
        if len(parts) != 2 or not re.fullmatch(r"51-P-[0-9]{2}", parts[0]):
            fail("invalid entry path")
        current_id, name = parts
        bundle_id = bundle_id or current_id
        if current_id != bundle_id or name != expected_name:
            fail("mixed bundle or noncanonical entry order")
        size = octal_field(header, 124, 12)
        payload = archive[cursor : cursor + size]
        if len(payload) != size:
            fail("truncated payload")
        cursor += size
        preflight(payload, full_name)
        expected_header = canonical_header(full_name, size)
        if header != expected_header:
            fail(f"noncanonical header: {full_name}")
        rebuilt.extend(expected_header)
        rebuilt.extend(payload)
        padding = (-size) % BLOCK
        pad = archive[cursor : cursor + padding]
        if pad != b"\0" * padding:
            fail("nonzero payload padding")
        rebuilt.extend(pad)
        cursor += padding
    trailer = archive[cursor:]
    if trailer != b"\0" * (2 * BLOCK):
        fail("archive must end in exactly two zero blocks")
    rebuilt.extend(trailer)
    if bytes(rebuilt) != archive:
        fail("independent rebuild differs")
    return hashlib.sha256(archive).hexdigest(), len(archive)


def main(arguments: list[str]) -> int:
    if len(arguments) not in (1, 2):
        print("usage: independent_verify.py ARCHIVE.tar [TEST_VECTOR]")
        return 2
    digest, size = verify(pathlib.Path(arguments[0]))
    if len(arguments) == 2:
        expected = pathlib.Path(arguments[1]).read_text(encoding="ascii").split()
        if len(expected) != 3:
            fail("invalid test-vector file")
        if digest != expected[0] or size != int(expected[1]):
            fail("golden SHA-256/byte count mismatch")
    print("independent USTAR verification passed")
    print(f"sha256={digest}")
    print(f"bytes={size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
