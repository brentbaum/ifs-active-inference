#!/usr/bin/env python3

import json
import pathlib
import sys
import tomllib


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        print("usage: toml_to_json.py INPUT.toml OUTPUT.json")
        return 2
    source, target = map(pathlib.Path, arguments)
    with source.open("rb") as stream:
        payload = tomllib.load(stream)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
