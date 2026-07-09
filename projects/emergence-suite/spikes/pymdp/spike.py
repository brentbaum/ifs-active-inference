#!/usr/bin/env python
# /// script
# dependencies = ["inferactively-pymdp==1.0.3", "numpy"]
# ///

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
from jax import numpy as jnp
from pymdp.agent import Agent

EPS = 1e-12


@dataclass
class SpikeState:
    pA: list[np.ndarray]
    pB: list[np.ndarray]
    qs: list[np.ndarray]
    true_A: list[np.ndarray]
    true_B: list[np.ndarray]
    state: list[int]
    policies: np.ndarray
    growth_happened: bool = False
    pymdp_growth_failure: str | None = None


def normalize_cols(a: np.ndarray) -> np.ndarray:
    return a / np.maximum(a.sum(axis=0, keepdims=True), EPS)


def normalize_b(b: np.ndarray) -> np.ndarray:
    return b / np.maximum(b.sum(axis=0, keepdims=True), EPS)


def init_A(n1: int, n2: int) -> list[np.ndarray]:
    a1 = np.zeros((2, n1, n2), dtype=float)
    a2 = np.zeros((2, n1, n2), dtype=float)
    for s1 in range(n1):
        for s2 in range(n2):
            a1[:, s1, s2] = [0.9, 0.1] if s1 == 0 else [0.1, 0.9]
            a2[:, s1, s2] = [0.9, 0.1] if s2 == 0 else [0.1, 0.9]
    return [a1, a2]


def init_B(n: int) -> np.ndarray:
    b = np.zeros((n, n, 2), dtype=float)
    for s in range(n):
        b[0, s, 0] = 0.85
        b[min(1, n - 1), s, 0] += 0.15
        b[n - 1, s, 1] = 0.85
        b[max(0, n - 2), s, 1] += 0.15
    return normalize_b(b)


def model_from_counts(st: SpikeState) -> tuple[list[np.ndarray], list[np.ndarray]]:
    return [normalize_cols(a) for a in st.pA], [normalize_b(b) for b in st.pB]


def joint_from_marginals(qs: list[np.ndarray]) -> np.ndarray:
    joint = qs[0]
    for q in qs[1:]:
        joint = np.multiply.outer(joint, q)
    return joint


def likelihood(A: list[np.ndarray], obs: list[int]) -> np.ndarray:
    L = np.ones(A[0].shape[1:], dtype=float)
    for g, a in enumerate(A):
        L *= a[obs[g]]
    return L


def marginals_from_joint(joint: np.ndarray) -> list[np.ndarray]:
    out = []
    for f in range(joint.ndim):
        axes = tuple(i for i in range(joint.ndim) if i != f)
        q = joint.sum(axis=axes)
        out.append(q / max(float(q.sum()), EPS))
    return out


def infer_states(st: SpikeState, obs: list[int], A, B, action: list[int] | None):
    if action is None:
        prior = [q.copy() for q in st.qs]
    else:
        prior = [B[f][:, :, action[f]] @ st.qs[f] for f in range(len(st.qs))]
    joint = joint_from_marginals(prior) * likelihood(A, obs)
    joint /= max(float(joint.sum()), EPS)
    return marginals_from_joint(joint), joint


def predicted_obs(a: np.ndarray, qs: list[np.ndarray]) -> np.ndarray:
    qo = np.zeros(a.shape[0], dtype=float)
    for idx in np.ndindex(a.shape[1:]):
        p = np.prod([qs[f][idx[f]] for f in range(len(qs))])
        qo += a[(slice(None),) + idx] * p
    return qo / max(float(qo.sum()), EPS)


def ambiguity(a: np.ndarray, qs: list[np.ndarray]) -> float:
    h = 0.0
    for idx in np.ndindex(a.shape[1:]):
        p = np.prod([qs[f][idx[f]] for f in range(len(qs))])
        col = a[(slice(None),) + idx]
        h -= float(p * np.sum(col * np.log(col + EPS)))
    return h


def score_policies_numpy(st: SpikeState, A, B) -> np.ndarray:
    C = [np.log([0.25, 0.75]), np.log([0.25, 0.75])]
    scores = []
    for policy in st.policies:
        qnext = [B[f][:, :, policy[f]] @ st.qs[f] for f in range(len(st.qs))]
        g = 0.0
        for m, a in enumerate(A):
            qo = predicted_obs(a, qnext)
            g += float(qo @ C[m] - ambiguity(a, qnext))
        scores.append(g)
    return np.array(scores)


def make_agent(A, B, policies) -> Agent:
    return Agent(
        A=[jnp.asarray(a) for a in A],
        B=[jnp.asarray(b) for b in B],
        C=[jnp.asarray([0.0, 2.0]), jnp.asarray([0.0, 2.0])],
        policies=jnp.asarray(policies[:, None, :]),
        num_controls=[2, 2],
        policy_len=1,
        learn_A=True,
        learn_B=True,
        pA=[jnp.asarray(a) for a in A],
        pB=[jnp.asarray(b) for b in B],
    )


def pymdp_policy_scores(agent: Agent, obs: list[int]):
    qs, _info = agent.infer_states(
        [jnp.asarray([obs[0]]), jnp.asarray([obs[1]])],
        empirical_prior=agent.D,
        return_info=True,
    )
    _q_pi, neg_efe = agent.infer_policies(qs)
    return np.asarray(neg_efe[0])


def sample_categorical(rng: np.random.Generator, p: np.ndarray) -> int:
    return int(rng.choice(len(p), p=p / p.sum()))


def env_observe(rng: np.random.Generator, st: SpikeState) -> list[int]:
    return [sample_categorical(rng, a[(slice(None),) + tuple(st.state)]) for a in st.true_A]


def env_step(rng: np.random.Generator, st: SpikeState, action: list[int]) -> None:
    for f in range(len(st.state)):
        st.state[f] = sample_categorical(rng, st.true_B[f][:, st.state[f], action[f]])


def update_A(st: SpikeState, obs: list[int], joint: np.ndarray) -> None:
    for g in range(len(st.pA)):
        st.pA[g][(obs[g],) + tuple(slice(None) for _ in range(joint.ndim))] += joint


def update_B(st: SpikeState, prev_qs: list[np.ndarray], action: list[int]) -> None:
    for f in range(len(st.pB)):
        st.pB[f][:, :, action[f]] += np.outer(st.qs[f], prev_qs[f])


def true_A_concentration(st: SpikeState) -> float:
    vals = []
    for g, counts in enumerate(st.pA):
        for idx in np.ndindex(counts.shape[1:]):
            truth = int(np.argmax(st.true_A[g][(slice(None),) + idx]))
            vals.append(counts[(truth,) + idx] / counts[(slice(None),) + idx].sum())
    return float(np.mean(vals))


def entropy_A(st: SpikeState) -> float:
    vals = []
    for counts in st.pA:
        for idx in np.ndindex(counts.shape[1:]):
            p = counts[(slice(None),) + idx]
            p = p / p.sum()
            vals.append(-float(np.sum(p * np.log(p + EPS))))
    return float(np.mean(vals))


def logbeta(alpha: np.ndarray) -> float:
    return float(sum(math.lgamma(float(x)) for x in alpha) - math.lgamma(float(alpha.sum())))


def dirichlet_log_evidence(counts: np.ndarray, prior: np.ndarray) -> float:
    total = 0.0
    for idx in np.ndindex(counts.shape[1:]):
        c = counts[(slice(None),) + idx]
        p = prior[(slice(None),) + idx]
        total += logbeta(c + p) - logbeta(p)
    return total


def bmr_delta_f(counts: np.ndarray) -> float:
    # Tying reduction: reduced model shares one likelihood column between states
    # 1 and 2. Correct comparison is pooled marginal evidence per rest-index:
    #   delta = logB(a + n1 + n2) - logB(a + n1) - logB(a + n2) + logB(a)
    # delta > 0 favors the tied (simpler) model. NOT count-averaging (that
    # returns 0 for symmetric data and lacks the Occam term).
    if counts.shape[1] < 2:
        return 0.0
    a = np.ones(counts.shape[0])
    total = 0.0
    rest = counts.shape[2:]
    for idx in np.ndindex(*rest) if rest else [()]:
        n1 = counts[(slice(None), 0) + idx] - 1.0
        n2 = counts[(slice(None), 1) + idx] - 1.0
        total += logbeta(a + n1 + n2) - logbeta(a + n1) - logbeta(a + n2) + logbeta(a)
    return float(total)


def bmr_delta_f_prior_swap(post: np.ndarray, b_f: np.ndarray, b_r: np.ndarray) -> float:
    # Canonical Friston-2017 prior-swap BMR over Dirichlet counts (the T1.3
    # form; matches derivations/d2_toy_demo.py). delta > 0 favors reduced.
    total = 0.0
    for idx in np.ndindex(*post.shape[1:]):
        p = post[(slice(None),) + idx]
        f = b_f[(slice(None),) + idx]
        r = b_r[(slice(None),) + idx]
        total += logbeta(f) - logbeta(r) + logbeta(p + r - f) - logbeta(p)
    return float(total)


def grow_factor1(st: SpikeState) -> None:
    old_n1, n2 = st.pA[0].shape[1], st.pA[0].shape[2]
    new_n1 = old_n1 + 1
    old_pA, old_true_A = st.pA, st.true_A
    st.pA = [np.ones((2, new_n1, n2)), np.ones((2, new_n1, n2))]
    st.true_A = init_A(new_n1, n2)
    for g in range(2):
        st.pA[g][:, :old_n1, :] = old_pA[g]
        st.true_A[g][:, :old_n1, :] = old_true_A[g]
    old_pB, old_true_B = st.pB[0], st.true_B[0]
    st.pB[0] = np.ones((new_n1, new_n1, 2))
    st.true_B[0] = init_B(new_n1)
    st.pB[0][:old_n1, :old_n1, :] = old_pB
    st.true_B[0][:old_n1, :old_n1, :] = old_true_B
    st.qs[0] = np.r_[0.85 * st.qs[0], 0.15]
    st.qs[0] /= st.qs[0].sum()
    st.state[0] = new_n1 - 1
    st.growth_happened = True


def run_spike(seed: int = 7, trials: int = 200) -> None:
    rng = np.random.default_rng(seed)
    st = SpikeState(
        pA=[np.ones((2, 2, 2)), np.ones((2, 2, 2))],
        pB=[np.ones((2, 2, 2)), np.ones((2, 2, 2))],
        qs=[np.full(2, 0.5), np.full(2, 0.5)],
        true_A=init_A(2, 2),
        true_B=[init_B(2), init_B(2)],
        state=[0, 0],
        policies=np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=int),
    )
    started = time.perf_counter()
    prev_action = None
    initial_conc = true_A_concentration(st)
    agent = make_agent(*model_from_counts(st), st.policies)

    for t in range(1, trials + 1):
        if t == 100:
            grow_factor1(st)
            prev_action = None
            try:
                agent = make_agent(*model_from_counts(st), st.policies)
            except Exception as exc:  # noqa: BLE001 - exact failure is the point of the spike.
                st.pymdp_growth_failure = repr(exc)
            print(
                f"growth trial={t} ns=({len(st.qs[0])},{len(st.qs[1])}) "
                f"pA1_shape={st.pA[0].shape} pB1_shape={st.pB[0].shape} "
                f"pymdp_reinit={'ok' if st.pymdp_growth_failure is None else 'failed'}"
            )

        obs = env_observe(rng, st)
        A, B = model_from_counts(st)
        prev_qs = [q.copy() for q in st.qs]
        st.qs, joint = infer_states(st, obs, A, B, prev_action)
        update_A(st, obs, joint)
        if prev_action is not None:
            update_B(st, prev_qs, prev_action)

        A, B = model_from_counts(st)
        scores = score_policies_numpy(st, A, B)
        if t in {1, 50, 99, 100, 150, 200}:
            pymdp_scores = None
            if st.pymdp_growth_failure is None:
                try:
                    pymdp_scores = pymdp_policy_scores(agent, obs).round(3).tolist()
                except Exception as exc:  # noqa: BLE001
                    st.pymdp_growth_failure = repr(exc)
            print(
                f"trial={t:03d} true_A_concentration={true_A_concentration(st):.4f} "
                f"A_entropy={entropy_A(st):.4f} best_policy={int(scores.argmax()) + 1} "
                f"efe_scores={scores.round(3).tolist()} pymdp_neg_efe={pymdp_scores}"
            )
        action = st.policies[int(scores.argmax())].tolist()
        env_step(rng, st, action)
        prev_action = action

    elapsed = time.perf_counter() - started
    print(
        "summary candidate=pymdp "
        f"trials={trials} elapsed_sec={elapsed:.4f} "
        f"initial_true_A_concentration={initial_conc:.4f} "
        f"final_true_A_concentration={true_A_concentration(st):.4f} "
        f"final_A_entropy={entropy_A(st):.4f} growth_happened={st.growth_happened} "
        f"pymdp_growth_failure={st.pymdp_growth_failure} "
        f"bmr_delta_f_reduced_minus_full={bmr_delta_f(st.pA[0]):.4f}"
    )


if __name__ == "__main__":
    run_spike()
