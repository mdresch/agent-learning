"""Contract tests for Epic 19, Story 19.1 (Pooling Logits).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.1.
ADR-019 §4.1 and §4.2; BRD-019; FDD-019 §2.1, §3 item 2 and H3, H4.

The members are built here and are synthetic: no family of converged low-authority policies exists in
the recorded store (FDD-019 §8). The numbers are arithmetic checks, not evidence.

Interpretation I1: this story builds the softmax branch only. Refusing a bad family (size, gate,
role maps, ``sigma_het`` values, unknown representation) is Story 19.3, and the Beta branch is
Story 19.2, so the fixtures here are valid by construction and ``compile_meta_prior`` is not asked to
refuse anything. A representation other than ``"softmax"`` or ``"thompson"`` is refused (Story 19.3).

Interpretation I2: ``MetaPrior.values`` and ``role_spread`` are plain ``dict`` objects keyed by role;
``roles`` and ``compiled_from`` are tuples (FDD-019 §2.1).

Interpretation I3: ``sigma_het`` is stored on the record as given; whether the spread respects it is
Story 19.3. The fixtures pass 0.25, above every spread of the base family.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from agent_learning.meta_prior import FamilyMember, MetaPrior, compile_meta_prior

ROLES = ("approve", "reject", "revise")
BASE_LOGITS = [
    [1.2, -0.3, 0.1],
    [1.0, -0.1, 0.3],
    [1.4, -0.5, 0.0],
    [1.1, -0.2, 0.2],
]
SIGMA = 0.25
MODULE = Path(__file__).resolve().parent.parent / "src" / "agent_learning" / "meta_prior.py"


def _member(index: int, logits: list[float], *, prefix: str = "") -> FamilyMember:
    """A member whose action ids are ``<prefix><role>`` and whose role map is the identity on roles."""
    actions = [f"{prefix}{role}" for role in ROLES]
    return FamilyMember(
        task_id=f"task-{index}",
        version=index + 1,
        role_map=dict(zip(actions, ROLES)),
        params=dict(zip(actions, logits)),
        gate_passed=True,
    )


def _base_family(prefix: str = "") -> list[FamilyMember]:
    return [_member(i, logits, prefix=prefix) for i, logits in enumerate(BASE_LOGITS)]


def _compile(members: list[FamilyMember]) -> MetaPrior:
    return compile_meta_prior(members, representation="softmax", sigma_het=SIGMA)


def _expected_from_formulas(logits: list[list[float]]) -> tuple[list[float], list[float]]:
    """FDD-019 §3 item 2, written out again: zero-centre, mean per role, spread with K - 1."""
    centred = [[x - sum(row) / len(row) for x in row] for row in logits]
    k = len(centred)
    mu = [sum(row[r] for row in centred) / k for r in range(len(ROLES))]
    spread = [math.sqrt(sum((row[r] - mu[r]) ** 2 for row in centred) / (k - 1)) for r in range(len(ROLES))]
    return mu, spread


def test_ac0_the_base_family_gives_the_hand_computed_mean_and_spread() -> None:
    prior = _compile(_base_family())

    assert [prior.values[role] for role in ROLES] == pytest.approx([0.825, -0.625, -0.200], abs=1e-9)
    assert [prior.role_spread[role] for role in ROLES] == pytest.approx([0.2132, 0.1287, 0.0861], abs=1e-4)

    mu, spread = _expected_from_formulas(BASE_LOGITS)
    assert [prior.values[role] for role in ROLES] == pytest.approx(mu, abs=1e-12)
    assert [prior.role_spread[role] for role in ROLES] == pytest.approx(spread, abs=1e-12)


def test_ac1_the_prior_is_zero_centred() -> None:
    prior = _compile(_base_family())
    assert sum(prior.values.values()) == pytest.approx(0.0, abs=1e-12)

    # four identical members pool to exactly their own centred logits, which sum to zero and have no spread
    row = BASE_LOGITS[0]
    identical = _compile([_member(i, row) for i in range(4)])
    centred = [x - sum(row) / len(row) for x in row]
    assert [identical.values[role] for role in ROLES] == pytest.approx(centred, abs=1e-12)
    assert sum(centred) == pytest.approx(0.0, abs=1e-12)
    assert [identical.role_spread[role] for role in ROLES] == pytest.approx([0.0, 0.0, 0.0], abs=1e-12)


def test_ac2_adding_a_constant_to_one_member_changes_nothing() -> None:
    base = _compile(_base_family())
    shifted_logits = [list(row) for row in BASE_LOGITS]
    shifted_logits[0] = [x + 5.0 for x in shifted_logits[0]]
    shifted = _compile([_member(i, row) for i, row in enumerate(shifted_logits)])

    for role in ROLES:
        assert shifted.values[role] == pytest.approx(base.values[role], abs=1e-12)
        assert shifted.role_spread[role] == pytest.approx(base.role_spread[role], abs=1e-12)


def test_ac2_a_different_constant_for_each_member_changes_nothing() -> None:
    base = _compile(_base_family())
    offsets = [5.0, -3.25, 100.0, 0.5]
    shifted = _compile(
        [_member(i, [x + offsets[i] for x in row]) for i, row in enumerate(BASE_LOGITS)]
    )
    for role in ROLES:
        assert shifted.values[role] == pytest.approx(base.values[role], abs=1e-12)
        assert shifted.role_spread[role] == pytest.approx(base.role_spread[role], abs=1e-12)


def test_ac3_action_ids_do_not_matter_only_roles() -> None:
    base = _compile(_base_family())
    renamed = _compile(_base_family(prefix="act_"))
    assert renamed.values == pytest.approx(base.values, abs=1e-12)
    assert renamed.role_spread == pytest.approx(base.role_spread, abs=1e-12)


def test_ac3_different_ids_and_order_of_actions_within_a_member() -> None:
    reordered = []
    for i, row in enumerate(BASE_LOGITS):
        ids = ["x1", "x2", "x3"]
        roles = ["revise", "approve", "reject"]  # a different order from ROLES
        logit_by_role = dict(zip(ROLES, row))
        reordered.append(
            FamilyMember(
                task_id=f"task-{i}",
                version=i + 1,
                role_map=dict(zip(ids, roles)),
                params={action: logit_by_role[role] for action, role in zip(ids, roles)},
                gate_passed=True,
            )
        )
    base = _compile(_base_family())
    pooled = _compile(reordered)
    assert pooled.values == pytest.approx(base.values, abs=1e-12)
    assert pooled.role_spread == pytest.approx(base.role_spread, abs=1e-12)


def test_ac3_the_order_of_members_changes_nothing_in_the_values() -> None:
    base = _compile(_base_family())
    reversed_prior = _compile(list(reversed(_base_family())))
    for role in ROLES:
        assert reversed_prior.values[role] == pytest.approx(base.values[role], abs=1e-12)
        assert reversed_prior.role_spread[role] == pytest.approx(base.role_spread[role], abs=1e-12)


def test_ac4_the_record() -> None:
    prior = _compile(_base_family())
    assert prior.representation == "softmax"
    assert prior.member_count == 4
    assert prior.kappa_prior is None
    assert prior.sigma_het == SIGMA
    assert prior.roles == ("approve", "reject", "revise")
    assert prior.compiled_from == (("task-0", 1), ("task-1", 2), ("task-2", 3), ("task-3", 4))


def test_ac4_roles_are_sorted_whatever_the_input_order() -> None:
    scrambled = []
    for i, row in enumerate(BASE_LOGITS):
        order = ["revise", "approve", "reject"]
        by_role = dict(zip(ROLES, row))
        scrambled.append(
            FamilyMember(
                task_id=f"task-{i}",
                version=i + 1,
                role_map={role: role for role in order},
                params={role: by_role[role] for role in order},
                gate_passed=True,
            )
        )
    assert _compile(scrambled).roles == ("approve", "reject", "revise")


def test_ac4_compiled_from_follows_the_input_order() -> None:
    members = list(reversed(_base_family()))
    assert _compile(members).compiled_from == (("task-3", 4), ("task-2", 3), ("task-1", 2), ("task-0", 1))


def test_ac4_the_inputs_are_not_changed() -> None:
    members = _base_family()
    before = [(m.task_id, m.version, dict(m.role_map), dict(m.params), m.gate_passed) for m in members]
    _compile(members)
    assert [(m.task_id, m.version, dict(m.role_map), dict(m.params), m.gate_passed) for m in members] == before


def test_i1_a_representation_that_is_not_built_is_not_silently_pooled() -> None:
    with pytest.raises(ValueError, match="representation"):
        compile_meta_prior(_base_family(), representation="something-else", sigma_het=SIGMA)


def test_ac5_meta_prior_is_pure() -> None:
    assert MODULE.is_file(), f"missing {MODULE}"
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(("." * node.level) + (node.module or ""))
    roots = {name.lstrip(".").split(".")[0] for name in imported}
    assert not [name for name in imported if "storage" in name], imported
    assert not roots & {"random", "numpy", "os", "pathlib", "io", "shutil", "tempfile", "json"}, imported

    called = {
        node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "open" not in called


def test_the_types_and_the_function_are_exported_from_the_package_root() -> None:
    import agent_learning_ext as agent_learning

    assert agent_learning.FamilyMember is FamilyMember
    assert agent_learning.MetaPrior is MetaPrior
    assert agent_learning.compile_meta_prior is compile_meta_prior
    for name in ("FamilyMember", "MetaPrior", "compile_meta_prior"):
        assert name in agent_learning.__all__
