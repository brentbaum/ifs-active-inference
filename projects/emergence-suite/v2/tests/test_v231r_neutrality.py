import itertools
import unittest

import numpy as np

from ref import v23, v231
from ref.factor import Factor
from ref.inference import ExactEngine


def fresh_conditional_evidence(model, observations):
    """Cartesian oracle independent of the engine's elimination path."""
    latent = [
        name
        for name in model.variables
        if name not in observations and name != "H"
    ]
    masses = np.zeros(2)
    for structure in (0, 1):
        for values in itertools.product((0, 1), repeat=len(latent)):
            assignment = dict(zip(latent, values))
            assignment.update(observations)
            assignment["H"] = structure
            mass = 1.0
            for factor in model.factors:
                index = tuple(
                    assignment[name] for name in factor.variables
                )
                mass *= float(factor.values[index])
            masses[structure] += mass
    structure_prior = next(
        factor for factor in model.factors if factor.variables == ("H",)
    ).values
    return masses / structure_prior


def engine_conditional_evidence(model, observations):
    posterior, evidence = ExactEngine().infer(model, ("H",), observations)
    structure_prior = next(
        factor for factor in model.factors if factor.variables == ("H",)
    ).values
    return posterior * evidence / structure_prior


def neutral_priors():
    return {
        "H": np.array([0.2, 0.8]),
        "G": v23.ROOT_PRIOR.copy(),
        "C": np.array([0.5, 0.5]),
        "R": v23.BROADCAST_PRIOR.copy(),
        "W": v23.WORLD_PRIOR.copy(),
    }


def compiled_model(*, action_intervention):
    priors = v231.predicted_priors(neutral_priors())
    return v231.formation_model(
        structure_prior=priors["H"],
        root_prior=priors["G"],
        control_prior=priors["C"],
        broadcast_prior=priors["R"],
        previous_world=priors["W"],
        consequence_alpha=np.tile(v23.POLICY_PRIOR, (2, 1)),
        overwhelm=0,
        real_danger=False,
        action_intervention=action_intervention,
    )


class NeutralityRepairTests(unittest.TestCase):
    def assert_neutral(self, model, observations):
        engine = engine_conditional_evidence(model, observations)
        fresh = fresh_conditional_evidence(model, observations)
        self.assertLess(np.max(np.abs(engine - fresh)), 1e-10)
        self.assertAlmostEqual(float(engine[1] / engine[0]), 1.0, places=12)

    def test_masked_slice_bf_is_one_for_both_interventions(self):
        model = compiled_model(action_intervention=True)
        self.assert_neutral(model, {"A": 0})
        self.assert_neutral(model, {"A": 1})

    def test_masked_slice_bf_is_one_for_generated_action(self):
        self.assert_neutral(
            compiled_model(action_intervention=False),
            {},
        )

    def test_equally_predicted_outcome_contributes_unit_bf(self):
        model = compiled_model(action_intervention=True)
        model.factors = [
            (
                Factor(
                    ("Y", "O"),
                    np.full((2, 2), 0.5),
                    "conditional_categorical",
                )
                if factor.variables == ("Y", "O")
                else factor
            )
            for factor in model.factors
        ]
        masked = fresh_conditional_evidence(model, {"A": 0})
        observed = fresh_conditional_evidence(model, {"A": 0, "O": 0})
        contribution = (observed[1] / masked[1]) / (
            observed[0] / masked[0]
        )
        self.assertAlmostEqual(float(contribution), 1.0, places=12)

    def test_repeated_masked_slices_follow_only_declared_transition(self):
        priors = neutral_priors()
        alpha = np.tile(v23.POLICY_PRIOR, (2, 1))
        for _ in range(60):
            predicted = v231.predicted_priors(priors)
            state = v231.infer_slice(
                priors=priors,
                consequence_alpha=alpha,
                overwhelm=0,
                real_danger=False,
                observations={"A": 0},
                action_intervention=True,
            )
            self.assertAlmostEqual(
                float(state.posterior_store["H"][1]),
                float(predicted["H"][1]),
                places=12,
            )
            priors = {
                name: state.posterior_store[name].copy()
                for name in ("H", "G", "C", "R", "W")
            }


if __name__ == "__main__":
    unittest.main()
