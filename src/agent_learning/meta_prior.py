"""Pooling the converged policies of a task family into a meta-prior (ADR-019, FDD-019).

Pure functions over plain values. Standard library only: nothing here reads the store, draws a random
number or touches a file; the command line (Story 19.4 onward) does the reading and writing.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True)
class FamilyMember:
    """One converged member of a task family (FDD-019 §2.1).

    ``params`` holds a logit per action id (softmax) or an ``(alpha, beta)`` pair per action id
    (Thompson). ``role_map`` sends each action id to the role it plays in the family.
    """

    task_id: str
    version: int
    role_map: Mapping[str, str]
    params: Mapping[str, float | tuple[float, float]]
    gate_passed: bool


@dataclass(frozen=True)
class MetaPrior:
    """The pooled starting values of a family, per role (FDD-019 §2.1)."""

    representation: str
    roles: tuple[str, ...]
    values: Mapping[str, float | tuple[float, float]]
    member_count: int
    role_spread: Mapping[str, float]
    sigma_het: float
    kappa_prior: float | None
    compiled_from: tuple[tuple[str, int], ...]


def _pool_softmax(members: Sequence[FamilyMember]) -> tuple[tuple[str, ...], dict[str, float], dict[str, float]]:
    """Zero-centre each member's logits by role, then take the mean and the K - 1 spread per role."""
    centred: list[dict[str, float]] = []
    for member in members:
        # a pair among softmax parameters is refused by Story 19.3; here the logit is a float by construction
        by_role = {member.role_map[action_id]: cast(float, logit) for action_id, logit in member.params.items()}
        offset = sum(by_role.values()) / len(by_role)
        centred.append({role: logit - offset for role, logit in by_role.items()})

    roles = tuple(sorted(centred[0]))
    count = len(centred)
    values = {role: sum(row[role] for row in centred) / count for role in roles}
    spread = {
        role: math.sqrt(sum((row[role] - values[role]) ** 2 for row in centred) / (count - 1)) for role in roles
    }
    return roles, values, spread


def _pool_thompson(
    members: Sequence[FamilyMember], kappa_prior: float
) -> tuple[tuple[str, ...], dict[str, tuple[float, float]], dict[str, float]]:
    """Pool Beta counts through payoff rates: a pooled rate per role, then a prior of strength kappa."""
    # a float among Beta parameters is refused by Story 19.3; here each value is a pair by construction
    by_role = [
        {member.role_map[action_id]: cast(tuple[float, float], pair) for action_id, pair in member.params.items()}
        for member in members
    ]
    roles = tuple(sorted(by_role[0]))
    count = len(by_role)
    values: dict[str, tuple[float, float]] = {}
    spread: dict[str, float] = {}
    for role in roles:
        pairs = [row[role] for row in by_role]
        rates = [(alpha - 1.0) / (alpha + beta - 2.0) for alpha, beta in pairs]
        pooled = sum(alpha - 1.0 for alpha, _ in pairs) / sum(alpha + beta - 2.0 for alpha, beta in pairs)
        values[role] = (1.0 + kappa_prior * pooled, 1.0 + kappa_prior * (1.0 - pooled))
        mean_rate = sum(rates) / count
        spread[role] = math.sqrt(sum((rate - mean_rate) ** 2 for rate in rates) / (count - 1))
    return roles, values, spread


def compile_meta_prior(
    members: Sequence[FamilyMember],
    *,
    representation: str,
    sigma_het: float,
    kappa_prior: float = 10.0,
) -> MetaPrior:
    """Pool ``members`` into a :class:`MetaPrior` (FDD-019 §3 item 2).

    Softmax logits are zero-centred per member, because softmax ignores a constant added to every logit,
    then averaged per role. ``kappa_prior`` is only for the Beta representation and is ``None`` on a
    softmax prior.

    Beta counts (``"thompson"``) are pooled in their own representation (FDD-019 §3 item 3): per role the
    payoff rate of a member is ``(alpha - 1) / (alpha + beta - 2)``, the pooled rate is the sum of the
    ``alpha - 1`` over the sum of the ``alpha + beta - 2``, and the prior is
    ``(1 + kappa * rate, 1 + kappa * (1 - rate))``. The spread is that of the members' payoff rates.
    """
    values: Mapping[str, float | tuple[float, float]]
    kappa: float | None
    if representation == "softmax":
        roles, values, spread = _pool_softmax(members)
        kappa = None
    elif representation == "thompson":
        roles, values, spread = _pool_thompson(members, kappa_prior)
        kappa = kappa_prior
    else:
        raise NotImplementedError(f"representation {representation!r} is not built yet")
    return MetaPrior(
        representation=representation,
        roles=roles,
        values=values,
        member_count=len(members),
        role_spread=spread,
        sigma_het=sigma_het,
        kappa_prior=kappa,
        compiled_from=tuple((member.task_id, member.version) for member in members),
    )


__all__ = ["FamilyMember", "MetaPrior", "compile_meta_prior"]
