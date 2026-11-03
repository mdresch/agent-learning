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
    """
    if representation != "softmax":
        raise NotImplementedError(f"representation {representation!r} is not built yet (Story 19.2)")
    roles, values, spread = _pool_softmax(members)
    return MetaPrior(
        representation=representation,
        roles=roles,
        values=values,
        member_count=len(members),
        role_spread=spread,
        sigma_het=sigma_het,
        kappa_prior=None,
        compiled_from=tuple((member.task_id, member.version) for member in members),
    )


__all__ = ["FamilyMember", "MetaPrior", "compile_meta_prior"]
