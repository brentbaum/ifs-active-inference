"""Module-parallel unittest wrapper with deterministic reporting."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _run_module(path: Path) -> tuple[str, int, float, str]:
    module = f"tests.{path.stem}"
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", module],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return (
        module,
        completed.returncode,
        time.perf_counter() - started,
        completed.stdout,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workers",
        type=int,
        default=min(8, max(1, os.cpu_count() or 1)),
    )
    args = parser.parse_args()
    modules = sorted((ROOT / "tests").glob("test*.py"))
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(_run_module, modules))
    failures = []
    for module, returncode, elapsed, output in results:
        status = "PASS" if returncode == 0 else "FAIL"
        print(f"{status} {module} {elapsed:.3f}s")
        if returncode:
            failures.append(module)
            print(output.rstrip())
    print(
        f"modules={len(results)} failures={len(failures)} "
        f"elapsed={time.perf_counter()-started:.3f}s"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
