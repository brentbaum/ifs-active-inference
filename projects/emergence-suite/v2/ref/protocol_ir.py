"""V2.G0 protocol compiler and family-parameterized bridge."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .world_ir import (
    CompiledWorld,
    WorldTrace,
    _canonical_hash,
    _plain,
    compile_world,
    sample_world,
)


@dataclass(frozen=True, slots=True)
class CompiledProtocol:
    spec: Mapping[str, Any]
    protocol_spec_hash: str
    actions: tuple[Any, ...]
    observation_channels: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True, slots=True)
class ScientificTrace:
    world_spec_hash: str
    protocol_spec_hash: str
    process_scopes: Mapping[str, tuple[str, ...]]
    truth_trace: Mapping[str, Any]
    observation_trace: tuple[Any, ...]
    interventions: tuple[Any, ...]
    component_rng_keys: tuple[tuple[str, int, str, int | str], ...]
    exact_world_log_probability: float
    output_schema_hash: str
    initial_state: Any
    inference_input: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class SchemaAudit:
    construction_success: bool
    world_spec_hash: str
    protocol_spec_hash: str
    process_scopes: Mapping[str, tuple[str, ...]]
    lengths: Mapping[str, int]
    support_ok: bool
    requested_fields_present: bool
    output_schema_hash: str
    deterministic_hash: str
    scientific_scores_inspected: bool


def compile_protocol(protocol_spec: Mapping[str, Any]) -> CompiledProtocol:
    spec = _plain(protocol_spec)
    if spec.get("stage_version") != "V2.G0":
        raise ValueError("protocol stage_version must be V2.G0")
    actions = tuple(spec.get("actions", ()))
    channels = tuple(
        MappingProxyType(_plain(item))
        for item in spec.get("observation_channels", ())
    )
    names = [str(item.get("name", "")) for item in channels]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise ValueError("observation channel names must be nonempty and unique")
    for channel in channels:
        if not channel.get("source_process"):
            raise ValueError("observation channel requires source_process")
    return CompiledProtocol(
        spec=MappingProxyType(spec),
        protocol_spec_hash=_canonical_hash(spec),
        actions=actions,
        observation_channels=channels,
    )


def _extract(value: Any, path: list[Any]) -> Any:
    result = value
    for key in path:
        result = result[key]
    return result


def _observations(
    world_trace: WorldTrace, protocol: CompiledProtocol
) -> tuple[Any, ...]:
    result = []
    for channel in protocol.observation_channels:
        source = world_trace.truth_trace[str(channel["source_process"])]
        value = _extract(source, list(channel.get("path", ())))
        mask_name = channel.get("masked_by")
        if mask_name is not None:
            mask = world_trace.truth_trace[str(mask_name)]
            if len(mask) != len(value):
                raise ValueError("mask and observation channel lengths differ")
            value = [
                observed if available else None
                for observed, available in zip(value, mask)
            ]
        result.append({"channel": channel["name"], "values": _plain(value)})
    return tuple(result)


def run_protocol(
    initial_state: Any,
    compiled_world: CompiledWorld,
    compiled_protocol: CompiledProtocol,
    seed: int,
) -> ScientificTrace:
    """Run a protocol as interventions against any compiled world family."""
    world = sample_world(compiled_world, seed)
    observations = _observations(world, compiled_protocol)
    schema_hash = _canonical_hash(
        {
            "world_schema_hash": world.output_schema_hash,
            "observation_channels": [
                {"name": item["channel"], "length": len(item["values"])}
                for item in observations
            ],
            "intervention_length": len(compiled_protocol.actions),
        }
    )
    # The inference-facing payload deliberately excludes protocol names, labels,
    # hashes, and construction metadata.
    inference_input = MappingProxyType(
        {
            "observations": observations,
            "interventions": compiled_protocol.actions,
        }
    )
    return ScientificTrace(
        world_spec_hash=world.world_spec_hash,
        protocol_spec_hash=compiled_protocol.protocol_spec_hash,
        process_scopes=world.process_scopes,
        truth_trace=world.truth_trace,
        observation_trace=observations,
        interventions=compiled_protocol.actions,
        component_rng_keys=world.component_rng_keys,
        exact_world_log_probability=world.exact_world_log_probability,
        output_schema_hash=schema_hash,
        initial_state=_plain(initial_state),
        inference_input=inference_input,
    )


def run_bridge(
    initial_state: Any,
    world_spec: Mapping[str, Any] | CompiledWorld,
    protocol_spec: Mapping[str, Any] | CompiledProtocol,
    rng: int,
) -> ScientificTrace:
    """Generic bridge; ``world_spec`` is not restricted to any family."""
    world = (
        world_spec
        if isinstance(world_spec, CompiledWorld)
        else compile_world(world_spec)
    )
    protocol = (
        protocol_spec
        if isinstance(protocol_spec, CompiledProtocol)
        else compile_protocol(protocol_spec)
    )
    return run_protocol(initial_state, world, protocol, int(rng))


def dry_run_schema(
    world_spec: Mapping[str, Any],
    protocol_spec: Mapping[str, Any],
    seed: int,
) -> SchemaAudit:
    """Four-layer pre-seal dry-run without scientific score inspection."""
    world = compile_world(world_spec)
    protocol = compile_protocol(protocol_spec)
    trace = run_protocol({}, world, protocol, seed)
    required = {
        "world_spec_hash",
        "protocol_spec_hash",
        "process_scopes",
        "truth_trace",
        "observation_trace",
        "interventions",
        "component_rng_keys",
        "exact_world_log_probability",
        "output_schema_hash",
    }
    lengths = MappingProxyType(
        {
            "processes": len(trace.truth_trace),
            "observations": len(trace.observation_trace),
            "interventions": len(trace.interventions),
        }
    )
    deterministic_hash = hashlib.sha256(
        json.dumps(
            {
                "world": trace.world_spec_hash,
                "protocol": trace.protocol_spec_hash,
                "schema": trace.output_schema_hash,
                "lengths": dict(lengths),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return SchemaAudit(
        construction_success=True,
        world_spec_hash=trace.world_spec_hash,
        protocol_spec_hash=trace.protocol_spec_hash,
        process_scopes=trace.process_scopes,
        lengths=lengths,
        support_ok=True,
        requested_fields_present=required.issubset(trace.__dataclass_fields__),
        output_schema_hash=trace.output_schema_hash,
        deterministic_hash=deterministic_hash,
        scientific_scores_inspected=False,
    )

