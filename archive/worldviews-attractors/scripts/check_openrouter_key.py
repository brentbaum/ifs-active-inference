#!/usr/bin/env python3
"""Quick check that the OpenRouter key works by hitting /models."""
from __future__ import annotations

import os
from pathlib import Path

import httpx


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    load_dotenv(Path(".env"))
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENROUTER_API_KEY in environment or .env")

    headers = {"Authorization": f"Bearer {api_key}"}
    resp = httpx.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=30)
    if resp.status_code != 200:
        raise SystemExit(f"Key check failed: {resp.status_code} {resp.text}")

    data = resp.json()
    models = data.get("data", [])
    print(f"OK: {len(models)} models accessible")


if __name__ == "__main__":
    main()
