"""Pooling the converged policies of a task family into a meta-prior (ADR-019, FDD-019).

Pure functions over plain values. Standard library only: nothing here reads the store, draws a random
number or touches a file; the command line (Story 19.4 onward) does the reading and writing.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

MIN_FAMILY_SIZE = 4  # the smallest family that is pooled (ADR-019 §4.1)
KAPPA_MAX = 10.0  # the largest prior strength (ADR-019 §4.2)
REPRESENTATIONS = ("softmax", "thompson")


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


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _check_member(member: FamilyMember, representation: str) -> None:
    """Refuse a member that is unqualified, mapped badly or holds the wrong kind of value."""
    task = member.task_id
    if not member.gate_passed:
        raise ValueError(f"member {task!r} has not passed the autonomy gate")

    actions, mapped = set(member.params), set(member.role_map)
    for action_id in sorted(actions - mapped):
        raise ValueError(f"member {task!r}: role_map misses action {action_id!r}")
    for action_id in sorted(mapped - actions):
        raise ValueError(f"member {task!r}: role_map names action {action_id!r}, which has no value in params")
    if len(set(member.role_map.values())) != len(member.role_map):
        raise ValueError(f"member {task!r}: role_map sends two actions to one role, so it is not a bijection")

    for action_id, value in member.params.items():
        if representation == "softmax":
            if not _is_number(value):
                raise ValueError(f"member {task!r}: action {action_id!r} needs a finite logit, got {value!r}")
        elif not (
            isinstance(value, (tuple, list)) and len(value) == 2 and all(_is_number(part) for part in value)
        ):
            raise ValueError(f"member {task!r}: action {action_id!r} needs an (alpha, beta) pair, got {value!r}")


def _check_family(members: Sequence[FamilyMember], representation: str) -> None:
    if len(members) < MIN_FAMILY_SIZE:
        raise ValueError(f"the family has {len(members)} members; at least {MIN_FAMILY_SIZE} are needed")
    seen: set[str] = set()
    for member in members:
        if member.task_id in seen:
            raise ValueError(f"task_id {member.task_id!r} appears more than once in the family")
        seen.add(member.task_id)

    for member in members:
        _check_member(member, representation)

    role_sets = [set(member.role_map.values()) for member in members]
    if any(roles != role_sets[0] for roles in role_sets):
        listing = "; ".join(f"{m.task_id}: {sorted(r)}" for m, r in zip(members, role_sets))
        raise ValueError(f"the members' role sets differ ({listing})")

    if representation == "thompson":
        for member in members:
            for action_id, pair in member.params.items():
                alpha, beta = cast(tuple[float, float], pair)
                if alpha + beta <= 2.0:
                    role = member.role_map[action_id]
                    raise ValueError(
                        f"member {member.task_id!r}, role {role!r}: alpha + beta = {alpha + beta} is not above 2, "
                        "so the member has not converged"
                    )


def _pool_softmax(members: Sequence[FamilyMember]) -> tuple[tuple[str, ...], dict[str, float], dict[str, float]]:
    """Zero-centre each member's logits by role, then take the mean and the K - 1 spread per role."""
    centred: list[dict[str, float]] = []
    for member in members:
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
    sigma_het: float | None = None,
    kappa_prior: float = 10.0,
) -> MetaPrior:
    """Pool ``members`` into a :class:`MetaPrior` (FDD-019 §3 items 1 to 3).

    Softmax logits are zero-centred per member, because softmax ignores a constant added to every logit,
    then averaged per role. ``kappa_prior`` is only for the Beta representation and is ``None`` on a
    softmax prior.

    Beta counts (``"thompson"``) are pooled in their own representation: per role the payoff rate of a
    member is ``(alpha - 1) / (alpha + beta - 2)``, the pooled rate is the sum of the ``alpha - 1`` over
    the sum of the ``alpha + beta - 2``, and the prior is ``(1 + kappa * rate, 1 + kappa * (1 - rate))``.
    The spread is that of the members' payoff rates.

    ``sigma_het`` has no default value (FDD-019 H4): ``None`` means it was left out and is refused.

    Raises:
        ValueError: naming the cause, for fewer than ``MIN_FAMILY_SIZE`` members, a duplicate ``task_id``,
            an unknown ``representation``, a ``sigma_het`` that is missing, not finite or not positive, a
            ``kappa_prior`` outside (0, ``KAPPA_MAX``] for Beta counts, a member that has not passed the
            gate, a ``role_map`` that is not a bijection, role sets that differ, parameters of the wrong
            kind, a Beta member with ``alpha + beta`` of 2 or less, or a largest role spread above
            ``sigma_het``.
    """
    if representation not in REPRESENTATIONS:
        raise ValueError(f"representation must be one of {', '.join(REPRESENTATIONS)}, got {representation!r}")
    if sigma_het is None or not _is_number(sigma_het) or sigma_het <= 0:
        raise ValueError(f"sigma_het must be given as a finite positive number, got {sigma_het!r}")
    if representation == "thompson" and not (_is_number(kappa_prior) and 0 < kappa_prior <= KAPPA_MAX):
        raise ValueError(f"kappa_prior must be above 0 and at most {KAPPA_MAX}, got {kappa_prior!r}")
    _check_family(members, representation)

    values: Mapping[str, float | tuple[float, float]]
    kappa: float | None
    if representation == "softmax":
        roles, values, spread = _pool_softmax(members)
        kappa = None
    else:
        roles, values, spread = _pool_thompson(members, kappa_prior)
        kappa = kappa_prior

    widest = max(roles, key=lambda role: spread[role])
    if spread[widest] > sigma_het:
        raise ValueError(
            f"role {widest!r} has a spread of {spread[widest]:.4f}, above sigma_het {sigma_het}: "
            "the family is too heterogeneous to pool"
        )

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


__all__ = ["KAPPA_MAX", "MIN_FAMILY_SIZE", "FamilyMember", "MetaPrior", "compile_meta_prior"]
