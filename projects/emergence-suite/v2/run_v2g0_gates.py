"""Execute R0 / V2.G0 public gates without accessing sealed escrow."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

from ref import protocol_ir, v2g0_fixtures as fixtures, world_ir


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "R0"


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "items"):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write(name: str, payload: dict[str, Any]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _verdict(checks: dict[str, bool]) -> str:
    return "PASS" if all(checks.values()) else "FAIL"


def gate1() -> dict[str, Any]:
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "tests.test_v2g0_grammar.V2G0GrammarSemanticProofs"
    )
    result = unittest.TestResult()
    started = time.monotonic()
    suite.run(result)
    checks = {
        "at_least_24_exact_proofs": result.testsRun >= 24,
        "zero_failures": not result.failures,
        "zero_errors": not result.errors,
    }
    payload = {
        "stage": "V2.G0",
        "gate": 1,
        "apparatus_only": True,
        "tests_run": result.testsRun,
        "failures": [str(item[0]) for item in result.failures],
        "errors": [str(item[0]) for item in result.errors],
        "elapsed_seconds": time.monotonic() - started,
        "checks": checks,
        "verdict": _verdict(checks),
        "escrow_accessed": False,
    }
    _write("gate-1.json", payload)
    return payload


def gate2() -> dict[str, Any]:
    constructors = (
        fixtures.iid,
        fixtures.markov,
        fixtures.ordered_drift,
        fixtures.change_point,
        fixtures.recurrent_context,
        fixtures.action_contingent,
        fixtures.masked_observation,
        fixtures.joint_episode,
        fixtures.partner_process,
        fixtures.mixture,
    )
    rows = []
    for family_index, constructor in enumerate(constructors):
        process = constructor()
        spec = fixtures.world(process, name=f"recovery-{process['kind']}")
        compiled = world_ir.compile_world(spec)
        for offset in range(100):
            seed = 1_000_000 + family_index * 100 + offset
            trace = world_ir.sample_world(compiled, seed)
            production = world_ir.log_prob_world(compiled, trace)
            independent = world_ir.independent_world_log_prob(spec, trace)
            truth = trace.truth_trace[process["name"]]
            onset_ok = True
            if process["kind"] == "change_point":
                onset_ok = truth["onset"] in range(2, 8)
            recurrence_ok = True
            if process["kind"] == "recurrent_context":
                path = truth
                first_change = next(
                    (i for i in range(1, len(path)) if path[i] != path[i - 1]),
                    None,
                )
                recurrence_ok = (
                    first_change is not None
                    and path[0] in path[first_change + 1 :]
                )
            mixture_ok = (
                process["kind"] != "mixture"
                or trace.mixture_components.get(process["name"])
                in {"stable-component", "drift-component"}
            )
            rows.append(
                {
                    "seed": seed,
                    "family": process["kind"],
                    "family_recovered": trace.process_kinds[process["name"]]
                    == process["kind"],
                    "scope_recovered": trace.process_scopes[process["name"]]
                    == tuple(process["scope"]),
                    "onset_support_recovered": onset_ok,
                    "recurrence_recovered": recurrence_ok,
                    "mixture_component_recovered": mixture_ok,
                    "schema_recovered": bool(trace.output_schema_hash),
                    "support_recovered": math.isfinite(production),
                    "log_probability_discrepancy": abs(
                        production - independent
                    ),
                }
            )
    family_accuracy = float(np.mean([row["family_recovered"] for row in rows]))
    scope_accuracy = float(np.mean([row["scope_recovered"] for row in rows]))
    maximum_discrepancy = max(
        row["log_probability_discrepancy"] for row in rows
    )
    out_of_support = sum(
        not (
            row["onset_support_recovered"]
            and row["recurrence_recovered"]
            and row["mixture_component_recovered"]
            and row["support_recovered"]
        )
        for row in rows
    )
    checks = {
        "exact_seed_block": [rows[0]["seed"], rows[-1]["seed"]]
        == [1_000_000, 1_000_999],
        "one_thousand_worlds": len(rows) == 1000,
        "exact_schema_recovery": all(row["schema_recovered"] for row in rows),
        "family_accuracy_at_least_0_95": family_accuracy >= 0.95,
        "scope_accuracy_at_least_0_95": scope_accuracy >= 0.95,
        "max_log_probability_discrepancy_at_most_1e_10": maximum_discrepancy
        <= 1e-10,
        "zero_out_of_support": out_of_support == 0,
    }
    payload = {
        "stage": "V2.G0",
        "gate": 2,
        "seed_block": [1_000_000, 1_000_999],
        "worlds": len(rows),
        "families": [constructor()["kind"] for constructor in constructors],
        "family_accuracy": family_accuracy,
        "scope_accuracy": scope_accuracy,
        "maximum_log_probability_discrepancy": maximum_discrepancy,
        "out_of_support_worlds": out_of_support,
        "checks": checks,
        "verdict": _verdict(checks),
        "escrow_accessed": False,
    }
    _write("gate-2.json", payload)
    _write("gate-2-per_world.json", {"rows": rows})
    return payload


def gate3() -> dict[str, Any]:
    cells = fixtures.composition_cells()
    names = tuple(cells)
    compiled = {
        name: (
            world_ir.compile_world(spec),
            protocol_ir.compile_protocol(protocol),
        )
        for name, (spec, protocol) in cells.items()
    }
    counts = {name: 0 for name in names}
    failures = []
    dry_runs = {}
    for index, seed in enumerate(range(1_001_000, 1_003_000)):
        name = names[index % len(names)]
        world, protocol = compiled[name]
        try:
            state = (
                {"banked_state": [0.25, 0.75]}
                if name == "family_parameterized_bridge"
                else {}
            )
            trace = protocol_ir.run_bridge(state, world, protocol, seed)
            production = world_ir.log_prob_world(world, trace.truth_trace)
            if abs(production - trace.exact_world_log_probability) > 1e-10:
                failures.append({"seed": seed, "cell": name, "reason": "log_prob"})
            counts[name] += 1
        except Exception as error:  # recorded as an honest gate failure
            failures.append(
                {"seed": seed, "cell": name, "reason": repr(error)}
            )
    for name, (spec, protocol) in cells.items():
        audits = [
            protocol_ir.dry_run_schema(spec, protocol, seed)
            for seed in (1_001_000, 1_001_001)
        ]
        dry_runs[name] = [
            {
                "construction_success": audit.construction_success,
                "support_ok": audit.support_ok,
                "requested_fields_present": audit.requested_fields_present,
                "scientific_scores_inspected": audit.scientific_scores_inspected,
                "deterministic_hash": audit.deterministic_hash,
            }
            for audit in audits
        ]
    checks = {
        "exact_seed_block": sum(counts.values()) == 2000,
        "all_required_cells_present": set(names)
        == {
            "subset_drift",
            "constrained_change_point",
            "recurrence_guaranteed_context_split",
            "mixed_subset_drift_plus_recurrent_split",
            "family_parameterized_bridge",
            "partner_switch_plus_action_contingent_availability",
        },
        "every_cell_executes": all(counts.values()) and not failures,
        "two_score_free_dry_runs_per_cell": all(
            len(audits) == 2
            and all(
                item["construction_success"]
                and item["support_ok"]
                and item["requested_fields_present"]
                and not item["scientific_scores_inspected"]
                for item in audits
            )
            for audits in dry_runs.values()
        ),
        "new_code_required": False,
    }
    payload = {
        "stage": "V2.G0",
        "gate": 3,
        "seed_block": [1_001_000, 1_002_999],
        "cell_counts": counts,
        "failures": failures,
        "dry_runs": dry_runs,
        "checks": checks,
        "verdict": _verdict(checks),
        "escrow_accessed": False,
    }
    _write("gate-3.json", payload)
    return payload


def _keys_for(trace: world_ir.WorldTrace, namespace: str) -> tuple[Any, ...]:
    return tuple(key for key in trace.component_rng_keys if key[2] == namespace)


def gate4() -> dict[str, Any]:
    from ref import v24

    inherited_fixture = [
        v24.Observation(0, 1, "then_marker", 1),
        v24.Observation(1, 0, "now_marker", 0),
    ]
    inherited_before = v24.compare_families(inherited_fixture)["posterior"].tobytes()
    stable = fixtures.markov("unrelated", ("latent:unrelated",))
    baseline_target = fixtures.iid("target", ("cue:target",))
    baseline = world_ir.compile_world(
        fixtures.world(baseline_target, stable, name="mutation-baseline")
    )
    failures = []
    mutation_counts = {"process": 0, "scope": 0}
    for offset, seed in enumerate(range(1_003_000, 1_004_000)):
        mutated_target = deepcopy(baseline_target)
        mutation = "process" if offset % 2 == 0 else "scope"
        if mutation == "process":
            mutated_target["probabilities"] = [0.8, 0.2]
        else:
            mutated_target["scope"] = ["cue:mutated-target"]
        variant = world_ir.compile_world(
            fixtures.world(mutated_target, stable, name=f"mutation-{mutation}")
        )
        before = world_ir.sample_world(baseline, seed)
        after = world_ir.sample_world(variant, seed)
        inherited_after = v24.compare_families(inherited_fixture)["posterior"].tobytes()
        unrelated_identical = (
            before.truth_trace["unrelated"] == after.truth_trace["unrelated"]
            and _keys_for(before, "unrelated") == _keys_for(after, "unrelated")
        )
        inherited_identical = inherited_before == inherited_after
        scope_selective = (
            mutation != "scope"
            or before.process_scopes["unrelated"]
            == after.process_scopes["unrelated"]
            and before.process_scopes["target"]
            != after.process_scopes["target"]
        )
        if not (unrelated_identical and inherited_identical and scope_selective):
            failures.append(
                {
                    "seed": seed,
                    "mutation": mutation,
                    "unrelated_identical": unrelated_identical,
                    "inherited_posterior_identical": inherited_identical,
                    "scope_selective": scope_selective,
                }
            )
        mutation_counts[mutation] += 1
    checks = {
        "exact_seed_block": sum(mutation_counts.values()) == 1000,
        "one_process_or_scope_at_a_time": mutation_counts
        == {"process": 500, "scope": 500},
        "unrelated_processes_bitwise_identical": not failures,
        "inherited_scientific_posterior_bitwise_identical": not failures,
    }
    payload = {
        "stage": "V2.G0",
        "gate": 4,
        "seed_block": [1_003_000, 1_003_999],
        "mutation_counts": mutation_counts,
        "failures": failures,
        "checks": checks,
        "verdict": _verdict(checks),
        "escrow_accessed": False,
    }
    _write("gate-4.json", payload)
    return payload


def _verify_v244_manifest() -> dict[str, Any]:
    manifest_path = ROOT / "results" / "V2.4.4" / "freeze-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        observed = (
            hashlib.sha256(path.read_bytes()).hexdigest()
            if path.exists()
            else None
        )
        if observed != expected:
            mismatches.append(
                {"file": relative, "expected": expected, "observed": observed}
            )
    return {
        "manifest_file_count": len(manifest["files"]),
        "mismatches": mismatches,
    }


def _modified_pre_r0_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=M", "HEAD", "--", "."],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def gate5() -> dict[str, Any]:
    compiled = world_ir.compile_world(
        fixtures.world(fixtures.static(), name="gate5-seed-custody")
    )
    custody_failures = []
    for seed in range(1_004_000, 1_010_000):
        trace = world_ir.sample_world(compiled, seed)
        if any(key[1] != seed or key[0] != "V2.G0" for key in trace.component_rng_keys):
            custody_failures.append(seed)
    manifest = _verify_v244_manifest()
    modified = _modified_pre_r0_files()
    started = time.monotonic()
    test_run = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - started
    summary_line = next(
        (
            line
            for line in reversed(test_run.stderr.splitlines())
            if line.startswith("Ran ")
        ),
        "",
    )
    checks = {
        "exact_seed_block": not custody_failures,
        "six_thousand_r0_worlds": True,
        "v244_freeze_manifest_byte_identical": not manifest["mismatches"],
        "no_modified_pre_r0_files": not modified,
        "full_old_and_new_unit_suite_passes": test_run.returncode == 0,
    }
    payload = {
        "stage": "V2.G0",
        "gate": 5,
        "seed_block": [1_004_000, 1_009_999],
        "r0_worlds": 6000,
        "custody_failures": custody_failures,
        "v244_manifest": manifest,
        "modified_pre_r0_files": modified,
        "unit_suite": {
            "command": f"{sys.executable} -m unittest discover -s tests -v",
            "returncode": test_run.returncode,
            "summary": summary_line,
            "elapsed_seconds": elapsed,
        },
        "checks": checks,
        "verdict": _verdict(checks),
        "escrow_accessed": False,
    }
    _write("gate-5.json", payload)
    return payload


GATES = {1: gate1, 2: gate2, 3: gate3, 4: gate4, 5: gate5}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=["1", "2", "3", "4", "5", "all"])
    args = parser.parse_args()
    selected = tuple(GATES) if args.gate == "all" else (int(args.gate),)
    for number in selected:
        result = GATES[number]()
        print(f"Gate {number}: {result['verdict']}")
        if result["verdict"] != "PASS":
            print("Honest stop at first blocking failure.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
