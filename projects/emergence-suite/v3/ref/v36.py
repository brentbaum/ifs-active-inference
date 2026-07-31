"""V3.6 COMPOSE: composition-only whole-therapy readouts.

This module adds no likelihood, latent variable, prior, or update equation.  It
declares a generic protocol schedule, invokes the frozen V3.1--V3.5 public
interfaces, and returns immutable posterior readouts plus explicit code-length
accounting.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from . import audit, v31, v32, v33, v34, v35
from .trace_sink import require_trace_sink


STAGE_VERSION = "V3.6"
DEVELOPMENT_BLOCK = (3_600_000, 3_679_999)
TOLERANCE = 1e-10
PROTOCOLS = (
    "full",
    "regulation_without_root_evidence",
    "cue_only_exposure",
    "mode_bypass",
    "soothing_noncontingent_partner",
    "unreliable_partner",
    "broadcast_off_monitor",
    "premature_do_over",
    "denied_contact_masked",
    "context_scope_disabled",
    "structural_pruning_disabled",
)
THERAPY_EVENTS = (
    "activation",
    "partner_regulation",
    "refusal_opportunity",
    "noncoercive_relational_observation",
    "policy_testing",
    "vulnerable_mode_contact",
    "root_relevant_evidence",
    "contextual_evidence",
    "imaginal_evidence",
    "followup_stress",
)

# The generic dormant-emission rule appears once here.  Active-count cost is
# charged by each structure prior and is not charged again per dormant slot.
GRAMMAR_TEMPLATE_CODE_LENGTH = 58.0


@dataclass(frozen=True)
class ComposeConfig:
    protocol: str = "full"
    mode_count: int = 3
    topology: str = "allied"
    stakes: str = "low"
    support_target: str = "all"
    policy_regime: str = "engagement"
    missingness: float = 0.0
    length: int = 16

    def __post_init__(self) -> None:
        if self.protocol not in PROTOCOLS:
            raise ValueError("unknown V3.6 protocol")
        if self.mode_count not in (1, 2, 3):
            raise ValueError("mode_count must be in {1,2,3}")
        if self.topology not in {"independent", "opposed", "allied"}:
            raise ValueError("unknown topology")
        if self.stakes not in {"low", "high"}:
            raise ValueError("unknown stakes")
        if self.support_target not in {"one", "all"}:
            raise ValueError("unknown support target")
        if self.policy_regime not in {"exclusion", "monitoring", "engagement", "mixed"}:
            raise ValueError("unknown policy regime")
        if not 0.0 <= self.missingness < 1.0:
            raise ValueError("missingness must be in [0,1)")
        if self.length < 8:
            raise ValueError("composition length must be at least eight")


@dataclass(frozen=True)
class CompositionReadout:
    seed: int
    protocol: str
    q_identity_organization: float
    q_external_danger: float
    q_action_efficacy: float
    episodic_information: float
    q_context_specific: float
    q_recurrent_context: float
    historical_retention: float
    q_current_edge_absence: float
    root_revision: float
    q_partner_reliable: float
    local_precision: float
    global_precision: float
    root_evidence_uptake: float
    root_transfer: float
    q_policy_open: float
    q_joint_policy_edge: float
    support_response: tuple[float, float, float]
    contact_response: tuple[float, float, float]
    opposed_D_0_1: float
    opposed_D_1_0: float
    allied_D_0_1: float
    allied_D_1_0: float
    stage_log_evidence: tuple[tuple[str, float], ...]
    inferred_event_order: tuple[tuple[str, int | None], ...]
    L_grammar: float
    L_H: float
    L_theta_given_H: float
    L_protocol: float
    L_total: float


def protocol_declaration(protocol: str) -> tuple[Mapping[str, Any], ...]:
    """Return generic R0-style events; no milestone conclusion is authored."""
    if protocol not in PROTOCOLS:
        raise ValueError("unknown protocol")
    disabled = {
        "regulation_without_root_evidence": {"root_relevant_evidence"},
        "cue_only_exposure": {
            "partner_regulation", "refusal_opportunity", "policy_testing",
            "vulnerable_mode_contact", "imaginal_evidence",
        },
        "mode_bypass": {"refusal_opportunity"},
        "broadcast_off_monitor": {"root_relevant_evidence"},
        "denied_contact_masked": {"vulnerable_mode_contact"},
        "context_scope_disabled": {"contextual_evidence"},
        "structural_pruning_disabled": {"imaginal_evidence"},
    }.get(protocol, set())
    return tuple(
        MappingProxyType({
            "event_index": index,
            "event_type": event,
            "available": event not in disabled,
        })
        for index, event in enumerate(THERAPY_EVENTS)
    )


def _component_declarations(config: ComposeConfig) -> Mapping[str, Any]:
    protocol = config.protocol
    grow = v31.FormationConfig(
        adversity="none" if protocol == "cue_only_exposure" else "repeated",
        control="high" if protocol == "cue_only_exposure" else "low",
        precision="broad",
        danger="safe",
        action="effective",
        availability="full",
        length=config.length,
    )
    temporal = v32.TemporalStructure(
        2,
        ("context_specific", "context_specific"),
        (
            "discrete_recurrent_context",
            "discrete_recurrent_context",
        ),
    )
    reduction = v33.ReductionConfig(
        corrective_evidence=(
            "none" if protocol == "structural_pruning_disabled"
            else "configural"
        ),
        do_over=(
            "premature" if protocol == "premature_do_over"
            else "post_revision"
        ),
        adaptive_edge="none",
        root_revision=True,
        history_length=config.length,
        corrective_length=max(8, config.length),
        return_length=8,
    )
    partner_pattern = {
        "soothing_noncontingent_partner": "soothing_noncontingent",
        "unreliable_partner": "unstable",
    }.get(protocol, "reliable")
    relate = v34.RelateConfig(
        partner_pattern=partner_pattern,
        regulation_present=protocol != "cue_only_exposure",
        root_evidence_present=protocol not in {
            "regulation_without_root_evidence", "cue_only_exposure",
            "broadcast_off_monitor",
        },
        broadcast=protocol != "broadcast_off_monitor",
        length=config.length,
    )
    protect = v35.ProtectConfig(
        befriend=("none" if protocol == "mode_bypass" else "all"),
        partner=("pressure" if protocol == "unreliable_partner" else "remaining"),
        stakes=config.stakes,
        policy_regime=config.policy_regime,
        mode_count=config.mode_count,
        topology=config.topology,
        support_target=config.support_target,
        registration="delivered",
        denied_contact=("masked" if protocol == "denied_contact_masked" else "delivered"),
        length=config.length,
    )
    return MappingProxyType({
        "grow": grow,
        "temporal_structure": temporal,
        "reduction": reduction,
        "relate": relate,
        "protect": protect,
    })


def _event_order(
    grow: v31.FormationPosterior,
    split: v32.TemporalPosterior,
    prune: v33.ReductionPosterior,
    relate: v34.RelatePosterior,
    protect: v35.ProtectPosterior,
) -> tuple[tuple[str, int | None], ...]:
    """Pure post-trace crossing readout; it never enters inference."""
    values = (
        ("organization", 0 if grow.part_probability >= 0.5 else None),
        ("relation", 1 if relate.co_regulated else None),
        ("policy", 2 if protect.readouts["access_probability"] >= 0.25 else None),
        ("root", 3 if abs(relate.root_movement) > TOLERANCE else None),
        ("context", 4 if split.scope_probability("outcome_emission", "context_specific") >= 0.5 else None),
        ("edge_reduction", 5 if prune.burden_edge_mass <= 0.5 else None),
    )
    return tuple(values)


def do_over_schedule_audit(world: v33.ReductionWorld) -> Mapping[str, Any]:
    """Prove do-over timing relative to the world's observed revision event.

    The comparison uses the event recorded in this world, never a fixed slice.
    It is a protocol-custody audit and does not enter scientific inference.
    """
    boundary = v33.root_revision_event(world)
    premature = tuple(
        item.time for item in world.slices
        if item.episode_kind == "imaginal_premature"
    )
    post_revision = tuple(
        item.time for item in world.slices
        if item.episode_kind == "imaginal_post"
    )
    if world.config.do_over == "premature":
        passed = (
            boundary is not None
            and bool(premature)
            and max(premature) < boundary
            and not post_revision
        )
    elif world.config.do_over == "post_revision":
        passed = (
            boundary is not None
            and bool(post_revision)
            and min(post_revision) > boundary
            and not premature
        )
    else:
        passed = not premature and not post_revision
    return MappingProxyType({
        "root_revision_event": boundary,
        "premature_times": premature,
        "post_revision_times": post_revision,
        "event_indexed": bool(passed),
    })


def _code_lengths(
    config: ComposeConfig,
    grow_world: v31.FormationWorld,
    temporal_world: v32.TemporalWorld,
    relate_world: v34.RelateWorld,
    protect_world: v35.ProtectWorld,
) -> tuple[float, float, float, float, float]:
    L_grammar = GRAMMAR_TEMPLATE_CODE_LENGTH
    L_H = -(
        v31.structure_log_prior(grow_world.structure)
        + v32.structure_log_prior(temporal_world.structure)
        + v34.structure_log_prior(relate_world.truth_structure)
        + v35.structure_log_prior(protect_world.truth_structure)
    ) / math.log(2.0)
    # Generic parameter families: temporal emissions, relational state rows,
    # mode-specific support/contact, and cross-mode sign.  The dormant rule is
    # not charged here; it was counted once in L_grammar.
    L_theta = float(
        2 * temporal_world.structure.active_contexts
        + 1
        + 2 * protect_world.truth_structure.active_modes
        + int(protect_world.truth_structure.cross_mode_outcome)
    )
    L_protocol = math.log2(len(PROTOCOLS))
    total = L_grammar + L_H + L_theta + L_protocol
    return L_grammar, L_H, L_theta, L_protocol, total


def run_therapy(
    seed: int,
    config: ComposeConfig = ComposeConfig(),
    *,
    released_block: tuple[int, int] | None = None,
) -> CompositionReadout:
    """Compose frozen stages without adding a scientific update."""
    require_trace_sink("v36.run_therapy", seed=int(seed))
    block = DEVELOPMENT_BLOCK if released_block is None else released_block
    declarations = _component_declarations(config)
    grow_world = v31.generate_world(seed, declarations["grow"], released_block=block)
    grow = v31.score_world(grow_world)
    temporal_world = v32.generate_world(
        seed,
        structure=declarations["temporal_structure"],
        length=config.length,
        cue_count=3,
        missingness=config.missingness,
        evidence_style="witnessing",
        released_block=block,
    )
    temporal_restrictions = (
        {
            "active_contexts": (1,),
            "scope:cue_emission": ("shared_global",),
            "scope:outcome_emission": ("shared_global",),
            "dynamics:cue_emission": ("static",),
            "dynamics:outcome_emission": ("static",),
        }
        if config.protocol == "context_scope_disabled" else None
    )
    split = v32.score_world(temporal_world, restrictions=temporal_restrictions)
    reduction_world = v33.generate_world(
        seed, declarations["reduction"], released_block=block
    )
    schedule_audit = do_over_schedule_audit(reduction_world)
    if not schedule_audit["event_indexed"]:
        raise AssertionError(
            "V3.6 do-over schedule is not indexed to the observed "
            "root-revision event"
        )
    reduction_restrictions = (
        {name: (1,) for name in v33.BURDEN_EDGES}
        if config.protocol == "structural_pruning_disabled" else None
    )
    prune = v33.score_world(
        reduction_world, restrictions=reduction_restrictions
    )
    relate_world = v34.generate_world(
        seed, declarations["relate"], released_block=block
    )
    relate = v34.score_world(relate_world)
    protect_world = v35.generate_world(
        seed, declarations["protect"], released_block=block
    )
    protect = v35.score_world(protect_world)
    q_context = 0.5 * (
        split.scope_probability("cue_emission", "context_specific")
        + split.scope_probability("outcome_emission", "context_specific")
    )
    q_recurrent = 0.5 * (
        split.dynamics_probability("cue_emission", "discrete_recurrent_context")
        + split.dynamics_probability("outcome_emission", "discrete_recurrent_context")
    )
    local = relate.local_precision[-1] if relate.local_precision else v34.BASE_PRECISION
    global_value = relate.global_precision[-1] if relate.global_precision else v34.BASE_PRECISION
    influence = protect.interventional_influence
    opposed = config.topology == "opposed"
    allied = config.topology == "allied"
    L_grammar, L_H, L_theta, L_protocol, L_total = _code_lengths(
        config, grow_world, temporal_world, relate_world, protect_world
    )
    readout = CompositionReadout(
        seed=int(seed),
        protocol=config.protocol,
        q_identity_organization=float(grow.part_probability),
        q_external_danger=float(grow.danger_probability),
        q_action_efficacy=float(grow.efficacy_probability),
        episodic_information=float(grow.delta_i),
        q_context_specific=float(q_context),
        q_recurrent_context=float(q_recurrent),
        historical_retention=float(prune.old_graph_probability),
        q_current_edge_absence=float(1.0 - prune.burden_edge_mass),
        root_revision=float(prune.root_revision),
        q_partner_reliable=float(relate.q_partner[0]),
        local_precision=float(local),
        global_precision=float(global_value),
        root_evidence_uptake=float(abs(relate.root_movement)),
        root_transfer=float(abs(relate.transfer)),
        q_policy_open=float(protect.readouts["access_probability"]),
        q_joint_policy_edge=float(protect.edge_probabilities["JOINT_POLICY_Y"]),
        support_response=tuple(protect.support_response_posterior),
        contact_response=tuple(protect.contact_response_posterior),
        opposed_D_0_1=float(-influence[0][1] if opposed else 0.0),
        opposed_D_1_0=float(-influence[1][0] if opposed else 0.0),
        allied_D_0_1=float(influence[0][1] if allied else 0.0),
        allied_D_1_0=float(influence[1][0] if allied else 0.0),
        stage_log_evidence=(
            ("grow", float(grow.log_evidence)),
            ("split", float(split.log_evidence)),
            ("prune_current", float(prune.current.log_evidence)),
            ("prune_historical", float(prune.historical.log_evidence)),
            ("relate", float(relate.log_evidence)),
            ("protect", float(protect.log_evidence)),
        ),
        inferred_event_order=_event_order(grow, split, prune, relate, protect),
        L_grammar=L_grammar,
        L_H=L_H,
        L_theta_given_H=L_theta,
        L_protocol=L_protocol,
        L_total=L_total,
    )
    violations = audit.audit_state(readout)
    if violations:
        raise AssertionError(f"V3.6 readout purity failure: {violations}")
    return readout


def finite_information_bounds() -> Mapping[str, float]:
    values = {
        "B_max_v31": 3.801426508560692,
        **v34.finite_information_bounds(),
        **v35.finite_information_bounds(),
    }
    return MappingProxyType(values)
