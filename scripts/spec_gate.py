#!/usr/bin/env python3
"""Pre-Flight Specification & Contract Readiness Gate (Epic 14 Bayesian Ingestion).

Audits story acceptance criteria before implementation or RED contract generation.
Evaluates specification completeness (None-guards, boundary behaviors, empty collections,
non-finite domains), testability (determinism, floating point tolerances, exception types),
upstream fork purity (Invariant 6), and architectural boundaries (Invariant 4 stdlib purity,
storage decoupling).

Applies Epic 14 critique deltas, evaluates robust Bayesian utility via DecisionResolver,
generates contract interpretations (I1, I2, ...), and passively records the decision as an
auditable Episode in the LearningStore.

Usage:
    uv run python scripts/spec_gate.py <story_id>
    uv run python scripts/spec_gate.py <story_id> --json
    uv run python scripts/spec_gate.py <story_id> --no-persist
    uv run python scripts/spec_gate.py <story_id> --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_learning.decision import (
    Action,
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    EvidencePoint,
    PolicySnapshot,
)
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Episode

from agent_learning_ext.critique_evidence import (
    AppliedCritique,
    CritiqueDelta,
    apply_critique,
    to_episode_metadata,
)


# ==============================================================================
# Domain Models & Story Parsing
# ==============================================================================

@dataclass(frozen=True)
class AcceptanceCriterionSpec:
    """A single parsed acceptance criterion from a story specification."""

    index: int
    label: str
    prose: str


@dataclass
class StorySpec:
    """Structured representation of a user story specification."""

    epic_num: int
    story_id: str  # e.g. "18.4"
    title: str
    status: str
    role: str
    want: str
    so_that: str
    acceptance_criteria: list[AcceptanceCriterionSpec] = field(default_factory=list)
    epic_context: str = ""
    file_path: Path | None = None


@dataclass(frozen=True)
class Interpretation:
    """An explicit implementation interpretation recommended for contract docstrings."""

    id: str  # e.g. "I1", "I2"
    title: str
    category: str
    text: str
    governing_ac: str | None = None


def normalize_story_id(raw_id: str) -> tuple[int, str]:
    """Parse raw story ID into (epic_num, formatted_story_id).
    
    Examples:
        '18.4' -> (18, '18.4')
        '18-4' -> (18, '18.4')
        'story-18.4' -> (18, '18.4')
        'epic-18-story-4' -> (18, '18.4')
    """
    clean = raw_id.strip().lower()
    
    # Pattern: epic-18-story-4 or epic-18-story-18.4
    m_epic_story = re.match(r"^epic-(\d+)-story-(\d+(?:\.\d+)?)$", clean)
    if m_epic_story:
        epic_n = int(m_epic_story.group(1))
        story_part = m_epic_story.group(2)
        if "." in story_part:
            return epic_n, story_part
        return epic_n, f"{epic_n}.{story_part}"

    # Pattern: story-18.4 or story-18-4
    m_story = re.match(r"^story-(\d+)[.-](\d+)$", clean)
    if m_story:
        epic_n = int(m_story.group(1))
        return epic_n, f"{epic_n}.{m_story.group(2)}"

    # Pattern: 18.4 or 18-4
    m_dot = re.match(r"^(\d+)[.-](\d+)$", clean)
    if m_dot:
        epic_n = int(m_dot.group(1))
        return epic_n, f"{epic_n}.{m_dot.group(2)}"

    raise ValueError(
        f"Invalid story identifier format: {raw_id!r}. "
        "Expected format 'X.Y', 'story-X.Y', or 'epic-X-story-Y' (e.g., '18.4')."
    )


def find_epic_file(epic_num: int, repo_root: Path = ROOT) -> Path:
    """Locate the markdown file for a given epic number in docs/user-stories/."""
    stories_dir = repo_root / "docs" / "user-stories"
    if not stories_dir.is_dir():
        raise FileNotFoundError(f"User stories directory not found at {stories_dir}")

    matches = list(stories_dir.glob(f"epic-{epic_num}-*.md"))
    if not matches:
        raise FileNotFoundError(f"No user story file found for Epic {epic_num} in {stories_dir}")
    if len(matches) > 1:
        # Sort by shortest name or exact match
        matches.sort(key=lambda p: len(p.name))
    return matches[0]


def parse_story(story_id: str, repo_root: Path = ROOT) -> StorySpec:
    """Parse a story and its acceptance criteria from its epic markdown file."""
    epic_num, norm_story_id = normalize_story_id(story_id)
    epic_file = find_epic_file(epic_num, repo_root=repo_root)
    content = epic_file.read_text(encoding="utf-8")

    # Split into epic context and story sections
    story_header_pattern = re.compile(
        r"^##\s*Story\s*(\d+\.\d+)\s*(?:[—–:-]|\s)\s*(.+)$",
        re.MULTILINE,
    )
    matches = list(story_header_pattern.finditer(content))
    if not matches:
        raise ValueError(f"No stories found in {epic_file.name}")

    # Capture epic preamble (text before first story)
    first_story_start = matches[0].start()
    epic_context = content[:first_story_start].strip()

    # Find the requested story
    target_match_idx = -1
    for idx, m in enumerate(matches):
        if m.group(1) == norm_story_id:
            target_match_idx = idx
            break

    if target_match_idx == -1:
        available = [m.group(1) for m in matches]
        raise ValueError(f"Story {norm_story_id} not found in {epic_file.name}. Available stories: {available}")

    target_match = matches[target_match_idx]
    story_title = target_match.group(2).strip()
    story_start = target_match.end()

    # Section ends at next '## ' heading or end of file
    if target_match_idx + 1 < len(matches):
        story_end = matches[target_match_idx + 1].start()
    else:
        # Check if there is another H2 section like '## Not a story'
        next_h2 = re.search(r"^##\s+", content[story_start:], re.MULTILINE)
        if next_h2:
            story_end = story_start + next_h2.start()
        else:
            story_end = len(content)

    story_body = content[story_start:story_end].strip()

    # Extract Status
    status_match = re.search(r"\*\*Status:\*\*\s*(.+)$", story_body, re.MULTILINE)
    status = status_match.group(1).strip() if status_match else "Unknown"

    # Extract As / I want / so that
    role, want, so_that = "", "", ""
    story_sentence_match = re.search(
        r"\*\*As\*\*\s+(.+?),\s+\*\*I want\*\*\s+(.+?),\s+\*\*so that\*\*\s+(.+?)(?:\.|\n|$)",
        story_body,
        re.IGNORECASE | re.DOTALL,
    )
    if story_sentence_match:
        role = story_sentence_match.group(1).strip()
        want = story_sentence_match.group(2).strip()
        so_that = story_sentence_match.group(3).strip()

    # Extract Acceptance Criteria
    # Supports '- **$AC_0$ (Label):** prose' and '- $AC_0$: prose'
    ac_bullet_pattern = re.compile(
        r"^\s*-\s*(?:\*\*)?\$AC_(\d+)\$(?:\s*\(([^)]+)\))?(?:\*\*)?:\s*(.*)$"
    )

    criteria: list[AcceptanceCriterionSpec] = []
    current_ac: dict[str, Any] | None = None

    for line in story_body.splitlines():
        ac_m = ac_bullet_pattern.match(line)
        if ac_m:
            if current_ac is not None:
                criteria.append(
                    AcceptanceCriterionSpec(
                        index=current_ac["index"],
                        label=current_ac["label"],
                        prose=" ".join(current_ac["prose_lines"]).strip(),
                    )
                )
            ac_idx = int(ac_m.group(1))
            ac_label = (ac_m.group(2) or "").strip()
            initial_prose = ac_m.group(3).strip()
            current_ac = {
                "index": ac_idx,
                "label": ac_label,
                "prose_lines": [initial_prose] if initial_prose else [],
            }
        elif current_ac is not None:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("---", "#")):
                # End of criteria block
                criteria.append(
                    AcceptanceCriterionSpec(
                        index=current_ac["index"],
                        label=current_ac["label"],
                        prose=" ".join(current_ac["prose_lines"]).strip(),
                    )
                )
                current_ac = None
            elif stripped.startswith("-"):
                # Non-AC bullet or end of AC block
                criteria.append(
                    AcceptanceCriterionSpec(
                        index=current_ac["index"],
                        label=current_ac["label"],
                        prose=" ".join(current_ac["prose_lines"]).strip(),
                    )
                )
                current_ac = None
            else:
                current_ac["prose_lines"].append(stripped)

    if current_ac is not None:
        criteria.append(
            AcceptanceCriterionSpec(
                index=current_ac["index"],
                label=current_ac["label"],
                prose=" ".join(current_ac["prose_lines"]).strip(),
            )
        )

    if not criteria:
        raise ValueError(f"No acceptance criteria found for Story {norm_story_id} in {epic_file.name}")

    return StorySpec(
        epic_num=epic_num,
        story_id=norm_story_id,
        title=story_title,
        status=status,
        role=role,
        want=want,
        so_that=so_that,
        acceptance_criteria=criteria,
        epic_context=epic_context,
        file_path=epic_file,
    )


# ==============================================================================
# Adversarial Pre-Flight Audit Engine
# ==============================================================================

# IMP-024: math.isclose / allclose with an absolute tolerance keep a default relative tolerance (1e-9 / 1e-5) that can
# silently relax a tight contract. pytest.approx(abs=...) does not, so it is not flagged.
_ISCLOSE = re.compile(r"\b(?:isclose|allclose)\b", re.IGNORECASE)
_ABS_TOL = re.compile(r"\b(?:abs_tol|atol)\b")
_TIGHT = re.compile(r"\b1e-(\d+)\b")
_ZERO_REL = re.compile(r"\b(?:rel_tol|rtol)\s*=\s*0(?:\.0+)?(?![\d.])")
_STRICT = re.compile(r"pytest\.approx\([^)]*\babs\s*=|absolute difference|\babs\(", re.IGNORECASE)

# IMP-021: a classical discrete primitive (Wilson interval over integer successes) widened to a continuous domain.
_DISCRETE = re.compile(r"\bwilson\b|\bbinomial\b|\bclopper\b|\bagresti\b", re.IGNORECASE)
_WIDENED = re.compile(r"\bfloats?\b.*\bsuccesses\b|\bsuccesses\b.*\bfloats?\b|\bin steps of 0\.[0-9]+|\bcumulative reward\b|\bfractional\b|\bnon-integer\b|\breal-valued\b|mapped (?:from \[-1, 1\] )?to \[0, 1\]", re.IGNORECASE)
_CLAMP = re.compile(r"\bclamp(?:ed|s)?\b|\b(?:within|in|to) \[0, ?1\]|max\(0|min\(1", re.IGNORECASE)
_INTEGER_LIMIT = re.compile(r"\binteger\b.*\b(?:equal|equals|agree|agrees|match|matches|identical|reduces)\b|\b(?:equal|equals|agree|agrees|match|matches|identical|reduces)\b.*\binteger\b", re.IGNORECASE)


def audit_story_spec(spec: StorySpec) -> tuple[list[CritiqueDelta], list[Interpretation], list[str]]:
    """Run adversarial pre-flight checks across 4 governance criteria.
    
    Returns:
        (critique_deltas, recommended_interpretations, audit_log_messages)
    """
    deltas: list[CritiqueDelta] = []
    interpretations: list[Interpretation] = []
    log: list[str] = []

    interp_counter = 1

    def add_interp(title: str, category: str, text: str, governing_ac: str | None = None) -> None:
        nonlocal interp_counter
        interp = Interpretation(
            id=f"I{interp_counter}",
            title=title,
            category=category,
            text=text,
            governing_ac=governing_ac,
        )
        interpretations.append(interp)
        interp_counter += 1

    all_ac_prose = " ".join(ac.prose for ac in spec.acceptance_criteria)
    combined_text = f"{spec.epic_context}\n{spec.want}\n{spec.so_that}\n{all_ac_prose}"

    # --------------------------------------------------------------------------
    # 1. UPSTREAM FORK PURITY (Invariant 6)
    # --------------------------------------------------------------------------
    upstream_matches = re.findall(
        r"\b(?:src/)?agent_learning/(?!ext\b)[a-zA-Z0-9_/.]+",
        combined_text,
    )
    # Filter out safe references like 'src/agent_learning/storage' when describing what not to import
    direct_upstream_targets = [
        m for m in upstream_matches if not any(k in m for k in ("storage", "decision", "types"))
    ]

    if direct_upstream_targets:
        target_path = direct_upstream_targets[0]
        subpath = re.sub(r"^(?:src/)?agent_learning/", "", target_path)
        ext_target = f"src/agent_learning_ext/{subpath}"
        finding_id = "SPEC-FORK-COLLISION"
        deltas.append(
            CritiqueDelta(
                criterion_id="upstream_fork_purity",
                support_delta=-0.25,
                rationale=(
                    f"Specification mentions upstream path '{target_path}'. "
                    "Custom code must reside in 'src/agent_learning_ext/' "
                    "to preserve Invariant 6 (Upstream Fork Purity)."
                ),
                finding_id=finding_id,
                basis="rubric",
                rubric_delta=-0.25,
            )
        )
        add_interp(
            title="Upstream Fork Purity (Invariant 6)",
            category="Upstream Fork Purity",
            text=(
                f"Specification references upstream path '{target_path}'. "
                "Per Invariant 6, all custom classes, learners, and helpers must be created under "
                f"'{ext_target}', "
                "leaving the upstream 'src/agent_learning/' tree completely pristine."
            ),
        )
        log.append(f"[WARN] Invariant 6: Upstream collision risk on {target_path}; mapped to {ext_target}.")
    else:
        deltas.append(
            CritiqueDelta(
                criterion_id="upstream_fork_purity",
                support_delta=0.10,
                rationale="Upstream namespace boundaries and fork isolation verified pristine.",
                finding_id="SPEC-FORK-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Invariant 6: Upstream fork purity verified.")

    # --------------------------------------------------------------------------
    # 2. ARCHITECTURAL BOUNDARIES & PURITY (Invariant 4 & Storage Decoupling)
    # --------------------------------------------------------------------------
    # Storage decoupling check
    has_storage_decoupling = (
        "imports nothing from" in combined_text.lower()
        and "storage" in combined_text.lower()
    ) or "json.dumps" in combined_text or "survives json" in combined_text

    mentions_state_or_snapshot = any(
        k in combined_text.lower() for k in ("snapshot", "policy", "metadata", "episode")
    )

    if has_storage_decoupling:
        deltas.append(
            CritiqueDelta(
                criterion_id="architectural_boundaries",
                support_delta=0.10,
                rationale="Storage subsystem decoupling and clean JSON round-trip explicitly specified in AC.",
                finding_id="SPEC-ARCH-STORAGE-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Architectural: Storage subsystem decoupling and serialization round-trip verified.")
    elif mentions_state_or_snapshot:
        deltas.append(
            CritiqueDelta(
                criterion_id="architectural_boundaries",
                support_delta=-0.15,
                rationale="State or policy modifications specified without explicit storage decoupling or JSON round-trip contract.",
                finding_id="SPEC-ARCH-STORAGE-GAP",
                basis="rubric",
                rubric_delta=-0.15,
            )
        )
        add_interp(
            title="Storage Decoupling & Serialization Round-Trip",
            category="Architectural Boundaries",
            text=(
                "All policy snapshots and episode metadata modifications must survive standard "
                "json.dumps() and json.loads() round-tripping without custom decoders, and the learner "
                "module must not import anything from agent_learning.storage."
            ),
        )
        log.append("[WARN] Architectural: Policy/state modification without explicit JSON round-trip contract.")

    # Immutability and input preservation check
    has_immutability = any(
        k in combined_text.lower()
        for k in ("deep copy", "deep copies", "untouched", "idempotent", "no mutation")
    )
    if has_immutability:
        deltas.append(
            CritiqueDelta(
                criterion_id="architectural_boundaries",
                support_delta=0.10,
                rationale="Input preservation, idempotence, or immutability contract explicitly specified in AC.",
                finding_id="SPEC-ARCH-IMMUTABLE-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Architectural: Immutability and input preservation verified.")

    # --------------------------------------------------------------------------
    # 3. SPECIFICATION COMPLETENESS
    # --------------------------------------------------------------------------
    # Check A: None-Safety & Defensive Guardrails
    mentions_dict_fields = any(
        k in combined_text.lower()
        for k in ("metadata", "extra", "options", "params", "kwargs")
    )
    has_explicit_none_check = any(
        k in combined_text.lower()
        for k in ("is none", "none raises", "defaults when none", "if none", "or {}")
    )

    if mentions_dict_fields and not has_explicit_none_check:
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=-0.15,
                rationale="Dictionary or optional parameter referenced without explicit None-safety contract in AC.",
                finding_id="SPEC-COMPL-NONE-GUARD",
                basis="rubric",
                rubric_delta=-0.15,
            )
        )
        add_interp(
            title="Defensive None-Safety for Dictionaries",
            category="Specification Completeness",
            text=(
                "When reading or updating dictionary attributes (such as policy.metadata or extra), "
                "implementations must defensively guard against None values (e.g., using "
                "getattr(policy, 'metadata', {}) or {}) to avoid AttributeError when metadata is None."
            ),
        )
        log.append("[WARN] Completeness: Dictionary/metadata referenced without explicit None-safety contract.")
    elif has_explicit_none_check:
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=0.10,
                rationale="Defensive None-handling and missing parameter contracts verified in AC.",
                finding_id="SPEC-COMPL-NONE-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Completeness: None-safety and missing argument contracts verified.")

    # Check B: Empty Collection / Base Case Handling
    mentions_collections = any(
        k in combined_text.lower()
        for k in ("episodes", "pairs", "deltas", "actions", "inputs", "batch")
    )
    has_empty_case = any(
        k in combined_text.lower()
        for k in (
            "no pair",
            "zero pair",
            "empty",
            "no episodes",
            "episodes_used is 0",
            "episodes_used equal to 0",
            "0 pairs",
        )
    )

    if mentions_collections and has_empty_case:
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=0.10,
                rationale="Empty collection and zero-item base case contract explicitly specified in AC.",
                finding_id="SPEC-COMPL-EMPTY-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Completeness: Empty collection and base case contracts verified.")
    elif mentions_collections and not has_empty_case:
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=-0.15,
                rationale="Collection processing specified without explicit contract for zero items or empty collection.",
                finding_id="SPEC-COMPL-EMPTY-GAP",
                basis="rubric",
                rubric_delta=-0.15,
            )
        )
        add_interp(
            title="Empty Collection Base Case",
            category="Specification Completeness",
            text=(
                "When passed an empty collection or when no items produce valid pairs/deltas, "
                "the function/learner must return a clean, unmutated state with episodes_used=0 without raising."
            ),
        )
        log.append("[WARN] Completeness: Collection processing without explicit empty collection contract.")

    # Check C: Boundary Behavior & Validation
    has_boundaries = any(
        k in combined_text.lower()
        for k in ("below", "above", "clamp", "max_logit", "<", "<=", ">", ">=", "[-", "[0")
    )
    if has_boundaries:
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=0.10,
                rationale="Numerical boundary and threshold behavior explicitly contracted in AC.",
                finding_id="SPEC-COMPL-BOUNDS-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Completeness: Numerical boundary and clamping behavior verified.")

    # Check D: Domain Validation & Non-Finite Numbers
    mentions_math_or_floats = any(
        k in combined_text.lower()
        for k in ("logit", "logits", "loss", "gradient", "theta", "float", "lambda", "lr", "rate")
    )
    has_non_finite_check = "non-finite" in combined_text.lower() or "nan" in combined_text.lower()

    if mentions_math_or_floats and has_non_finite_check:
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=0.10,
                rationale="Non-finite numerical rejection (NaN / Inf) explicitly specified in AC.",
                finding_id="SPEC-COMPL-NONFINITE-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Completeness: Non-finite numerical domain validation verified.")
    elif mentions_math_or_floats and not has_non_finite_check:
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=-0.08,
                rationale="Continuous numerical arguments accepted without explicit non-finite (NaN / Inf) rejection contract.",
                finding_id="SPEC-COMPL-NONFINITE-GAP",
                basis="rubric",
                rubric_delta=-0.08,
            )
        )
        add_interp(
            title="Non-Finite Float Rejection",
            category="Specification Completeness",
            text=(
                "All floating point configuration and logit arguments must be validated using "
                "math.isfinite() and raise ValueError if NaN, Inf, or -Inf is encountered."
            ),
        )
        log.append("[WARN] Completeness: Floating-point processing without explicit non-finite rejection contract.")

    # Check E (IMP-021): a discrete primitive widened to a continuous domain without its clamp and integer limit
    widened = [
        ac for ac in spec.acceptance_criteria if _DISCRETE.search(ac.prose) and _WIDENED.search(ac.prose)
    ]
    if widened and not (_CLAMP.search(combined_text) and _INTEGER_LIMIT.search(combined_text)):
        labels = ", ".join(ac.label for ac in widened)
        deltas.append(
            CritiqueDelta(
                criterion_id="specification_completeness",
                support_delta=-0.05,
                rationale=f"A discrete primitive is widened to a continuous domain ({labels}) without a stated clamp and integer limit.",
                finding_id="SPEC-COMPL-DOMAIN-WIDENING",
                basis="rubric",
                rubric_delta=-0.05,
            )
        )
        add_interp(
            title="Continuous-Domain Widening",
            category="Specification Completeness",
            text=(
                "State how the widened result is clamped (for a proportion bound, to [0, 1]), why it stays inside that "
                "range for every float input, and that it equals the classical value at integer counts."
            ),
            governing_ac=widened[0].label,
        )
        log.append(f"[WARN] Completeness: [domain-widening] {labels}: discrete primitive on a continuous domain.")

    # --------------------------------------------------------------------------
    # 4. TESTABILITY
    # --------------------------------------------------------------------------
    # Check A: Floating point tolerances
    has_float_assertions = any(
        k in combined_text.lower() for k in ("equal", "equals", "within", "loss", "logits")
    )
    has_explicit_tolerance = (
        "within 1e-" in combined_text.lower()
        or "within 1e" in combined_text.lower()
        or "tolerance" in combined_text.lower()
    )

    if has_explicit_tolerance:
        deltas.append(
            CritiqueDelta(
                criterion_id="testability",
                support_delta=0.10,
                rationale="Numerical equality assertions specify explicit precision tolerances (e.g. 1e-12).",
                finding_id="SPEC-TEST-TOLERANCE-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Testability: Explicit floating point tolerances verified.")
    elif has_float_assertions and mentions_math_or_floats:
        deltas.append(
            CritiqueDelta(
                criterion_id="testability",
                support_delta=-0.15,
                rationale="Continuous numerical comparison specified without explicit floating point tolerance.",
                finding_id="SPEC-TEST-TOLERANCE-GAP",
                basis="rubric",
                rubric_delta=-0.15,
            )
        )
        add_interp(
            title="Numerical Precision Tolerances",
            category="Testability",
            text=(
                "Contract tests comparing floating-point outcomes must use pytest.approx or "
                "math.isclose with explicit absolute/relative tolerance (e.g. 1e-9 or 1e-12) "
                "rather than exact equality."
            ),
        )
        log.append("[WARN] Testability: Floating-point assertions without explicit tolerances.")

    # Check A2 (IMP-024): an absolute tolerance on isclose / allclose with the default relative tolerance still in force
    tight = any(int(n) >= 9 for n in _TIGHT.findall(combined_text))
    if (
        _ISCLOSE.search(combined_text)
        and (_ABS_TOL.search(combined_text) or tight)
        and not _ZERO_REL.search(combined_text)
        and not _STRICT.search(combined_text)
    ):
        deltas.append(
            CritiqueDelta(
                criterion_id="testability",
                support_delta=-0.05,
                rationale="isclose / allclose with an absolute tolerance keeps a default relative tolerance that can relax a tight contract.",
                finding_id="SPEC-TEST-REL-TOL-GAP",
                basis="rubric",
                rubric_delta=-0.05,
            )
        )
        add_interp(
            title="Zero Relative Tolerance",
            category="Testability",
            text=(
                "Pass rel_tol=0.0 (or rtol=0) with abs_tol (atol): the default relative tolerance (1e-9 for math.isclose, "
                "1e-5 for numpy.allclose) silently relaxes a 1e-12 contract. pytest.approx(abs=...) or an absolute "
                "difference check is equally strict."
            ),
        )
        log.append("[WARN] Testability: isclose / allclose absolute tolerance without rel_tol=0.0.")

    # Check B: Specific Exception Classes
    negative_path_count = sum(
        1 for ac in spec.acceptance_criteria if "raises" in ac.prose.lower()
    )
    explicit_exception_count = sum(
        1
        for ac in spec.acceptance_criteria
        if any(exc in ac.prose for exc in ("ValueError", "TypeError", "KeyError", "RuntimeError"))
    )

    if negative_path_count > 0 and explicit_exception_count == negative_path_count:
        deltas.append(
            CritiqueDelta(
                criterion_id="testability",
                support_delta=0.10,
                rationale="All negative error paths name explicit exception classes (TypeError, ValueError).",
                finding_id="SPEC-TEST-EXCEPTIONS-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Testability: All negative test paths specify exact exception classes.")
    elif negative_path_count > explicit_exception_count:
        deltas.append(
            CritiqueDelta(
                criterion_id="testability",
                support_delta=-0.15,
                rationale="Error paths specified without naming exact exception classes.",
                finding_id="SPEC-TEST-GENERIC-ERROR",
                basis="rubric",
                rubric_delta=-0.15,
            )
        )
        add_interp(
            title="Specific Exception Class Requirements",
            category="Testability",
            text=(
                "All negative test assertions must name specific built-in exception types "
                "(typically TypeError for invalid types and ValueError for invalid values/domains)."
            ),
        )
        log.append("[WARN] Testability: Negative paths with unspecified exception classes.")

    # Check C: Determinism
    has_determinism = any(
        k in combined_text.lower()
        for k in ("deterministic", "fresh process", "repeated calls", "no random module", "seed")
    )
    if has_determinism:
        deltas.append(
            CritiqueDelta(
                criterion_id="testability",
                support_delta=0.10,
                rationale="Deterministic execution and seed reproducibility explicitly contracted in AC.",
                finding_id="SPEC-TEST-DETERMINISM-CONFIRMED",
                basis="rubric",
                rubric_delta=0.10,
            )
        )
        log.append("[OK] Testability: Deterministic execution and reproducibility verified.")

    return deltas, interpretations, log


# ==============================================================================
# Decision Frame & Bayesian Evaluation
# ==============================================================================

def build_spec_decision_frame(story_id: str) -> DecisionFrame:
    """Construct the standardized Pre-Flight Specification DecisionFrame."""
    criteria = (
        DecisionCriterion(id="specification_completeness", weight=0.35, minimum_sources=1),
        DecisionCriterion(id="testability", weight=0.25, minimum_sources=1),
        DecisionCriterion(id="upstream_fork_purity", weight=0.20, minimum_sources=1),
        DecisionCriterion(id="architectural_boundaries", weight=0.20, minimum_sources=1),
    )

    opt_proceed = DecisionOption(
        action=Action(
            id="proceed_to_implementation",
            description=f"Proceed to RED contract generation and implementation for Story {story_id}",
        ),
        evidence=(
            EvidencePoint("specification_completeness", "spec_analysis", 0.80, 0.75),
            EvidencePoint("testability", "spec_analysis", 0.85, 0.80),
            EvidencePoint("upstream_fork_purity", "fork_purity_guard", 0.90, 0.85),
            EvidencePoint("architectural_boundaries", "arch_review", 0.85, 0.80),
        ),
    )

    opt_amend = DecisionOption(
        action=Action(
            id="clarify_spec_and_amend",
            description=f"Halt and require specification clarification or amendments for Story {story_id}",
        ),
        evidence=(
            EvidencePoint("specification_completeness", "baseline_spec", 0.65, 0.65),
            EvidencePoint("testability", "baseline_spec", 0.65, 0.65),
            EvidencePoint("upstream_fork_purity", "baseline_spec", 0.70, 0.70),
            EvidencePoint("architectural_boundaries", "baseline_spec", 0.70, 0.70),
        ),
    )

    return DecisionFrame(
        task=f"story-{story_id}-spec-gate",
        options=(opt_proceed, opt_amend),
        criteria=criteria,
    )


def make_spec_snapshot(frame: DecisionFrame) -> PolicySnapshot:
    """Create initial uninformative policy snapshot for decision resolution."""
    actions = [opt.action for opt in frame.options]
    return PolicySnapshot(
        id=f"policy-{frame.task}",
        agent_id="agent-learning-governance",
        task_id=frame.task,
        version=1,
        actions=actions,
        logits={act.id: 0.0 for act in actions},
        metadata={"decision_authority": DecisionAuthority.FULL.value},
    )


# ==============================================================================
# Passive LearningStore Episode Persistence
# ==============================================================================

def save_spec_gate_episode(
    spec: StorySpec,
    passed: bool,
    reason: str,
    margin: float,
    interpretations: list[Interpretation],
    applied: AppliedCritique | None = None,
    store_dir: Path | str | None = None,
) -> str | None:
    """Passively record the specification gate decision as an auditable Episode."""
    target_dir = Path(store_dir) if store_dir else ROOT / "data" / "agent-learning" / "store"
    try:
        store = LocalFileStore(root_dir=target_dir)
        ep_uuid = uuid.uuid4().hex[:8]
        clean_id = spec.story_id.replace(".", "_")
        episode_id = f"spec-{clean_id}-{ep_uuid}"

        adjustments = to_episode_metadata(applied).get("critique_adjustments", []) if applied else []

        meta: dict[str, Any] = {
            "story_id": spec.story_id,
            "epic_num": spec.epic_num,
            "title": spec.title,
            "status": spec.status,
            "ac_count": len(spec.acceptance_criteria),
            "margin": round(margin, 4),
            "feedback_status": "accepted" if passed else "rejected",
            "interpretations": [asdict(i) for i in interpretations],
            "critique_adjustments": adjustments,
        }
        if not passed:
            meta["correct_action_id"] = "clarify_spec_and_amend"
            meta["rejection_reason"] = reason

        episode = Episode(
            id=episode_id,
            agent_id="agent-learning-governance",
            task_id=f"story-{spec.story_id}-spec-gate",
            task_name=f"Story {spec.story_id} Specification Readiness Gate",
            policy_id=f"policy-story-{spec.story_id}-spec-gate",
            policy_version=1,
            action_id="proceed_to_implementation",
            intent_summary=f"Pre-flight Bayesian specification evaluation of Story {spec.story_id}",
            user_input=f"Story {spec.story_id}: {spec.title}",
            assistant_output=reason,
            metadata=meta,
        )

        store.store_episode(episode)
        return episode_id
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Passive spec episode storage skipped: {exc}", file=sys.stderr)
        return None


# ==============================================================================
# Evaluation Orchestration
# ==============================================================================

def evaluate_story_spec(
    story_id: str,
    repo_root: Path = ROOT,
    store_dir: Path | str | None = None,
    persist_episode: bool = True,
    min_margin: float = 0.05,
    strict: bool = False,
) -> tuple[bool, str, dict[str, Any]]:
    """Evaluate story specification against adversarial rules and Bayesian decision frame."""
    spec = parse_story(story_id=story_id, repo_root=repo_root)

    # 1. Run adversarial pre-flight audit
    deltas, interpretations, log = audit_story_spec(spec)

    # 2. Construct and apply to DecisionFrame
    frame = build_spec_decision_frame(spec.story_id)
    applied = apply_critique(frame, option_id="proceed_to_implementation", deltas=deltas)

    # 3. Resolve Bayesian utilities
    resolver = DecisionResolver()
    snapshot = make_spec_snapshot(applied.frame)
    result = resolver.resolve(snapshot, applied.frame)

    proceed_assess = next(a for a in result.assessments if a.action.id == "proceed_to_implementation")
    amend_assess = next(a for a in result.assessments if a.action.id == "clarify_spec_and_amend")
    u_proceed = proceed_assess.robust_utility
    u_halt = amend_assess.robust_utility
    margin = u_proceed - u_halt
    scores = {
        "proceed_to_implementation": u_proceed,
        "clarify_spec_and_amend": u_halt,
    }

    # Strict mode check: halt if any negative delta exists
    has_negative_deltas = any(d.support_delta < 0 for d in deltas)

    if strict and has_negative_deltas:
        passed = False
        reason = "Strict Mode Halt: Specification has unresolved warnings or gaps that require amendment."
    elif (
        result.status.value == "resolved"
        and result.selected_action is not None
        and result.selected_action.id == "proceed_to_implementation"
        and margin >= min_margin
    ):
        passed = True
        reason = (
            f"Pre-Flight Specification Gate Passed. Robust margin +{margin:.4f} >= +{min_margin:.2f}. "
            f"Specification is ready for RED contract creation. {result.reason or ''}".strip()
        )
    else:
        passed = False
        reason = (
            f"Pre-Flight Specification Gate Halted. Robust margin {margin:+.4f} below required +{min_margin:.2f}. "
            f"Amend specification or clarify ambiguous criteria before writing contracts. {result.reason or ''}".strip()
        )

    # 4. Passive Episode persistence
    ep_id = None
    if persist_episode:
        ep_id = save_spec_gate_episode(
            spec=spec,
            passed=passed,
            reason=reason,
            margin=margin,
            interpretations=interpretations,
            applied=applied,
            store_dir=store_dir,
        )

    payload = {
        "story_id": spec.story_id,
        "epic_num": spec.epic_num,
        "title": spec.title,
        "status": spec.status,
        "passed": passed,
        "margin": round(margin, 4),
        "scores": {k: round(v, 4) for k, v in scores.items()},
        "ac_count": len(spec.acceptance_criteria),
        "findings_count": len(deltas),
        "audit_log": log,
        "interpretations": [asdict(i) for i in interpretations],
        "episode_id": ep_id,
    }

    return passed, reason, payload


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def ensure_utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so the emoji verdict lines print on a cp1252 console.

    Without it, Windows consoles raised UnicodeEncodeError on the verdict line after the
    verdict was computed (seen with pr_gate.py on PR #146). Streams without `reconfigure`
    (captured or replaced ones) are left alone.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Pre-Flight Specification & Contract Readiness Gatekeeper (Epic 14 Bayesian Ingestion)"
    )
    parser.add_argument("story_id", help="Story identifier to evaluate (e.g., '18.4', 'story-18.4')")
    parser.add_argument("--json", action="store_true", help="Output full evaluation results as JSON")
    parser.add_argument("--no-persist", action="store_true", help="Do not write the episode to LearningStore")
    parser.add_argument("--strict", action="store_true", help="Halt on any negative finding regardless of margin")
    parser.add_argument("--min-margin", type=float, default=0.05, help="Minimum robust utility margin (default 0.05)")
    parser.add_argument("--store-dir", type=str, default=None, help="Custom LearningStore directory path")

    args = parser.parse_args(argv)

    try:
        passed, _reason, payload = evaluate_story_spec(
            story_id=args.story_id,
            repo_root=ROOT,
            store_dir=args.store_dir,
            persist_episode=not args.no_persist,
            min_margin=args.min_margin,
            strict=args.strict,
        )
    except Exception as err:  # noqa: BLE001
        if args.json:
            print(json.dumps({"error": str(err), "passed": False}, indent=2))
        else:
            print(f"Error: {err}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0 if passed else 1

    # Pretty Human-Readable Terminal Layout
    print("=" * 80)
    print(f"PRE-FLIGHT SPECIFICATION READINESS GATE: Story {payload['story_id']} — {payload['title']}")
    print("=" * 80)
    print(f"Status in Epic {payload['epic_num']}: {payload['status']}")
    print(f"Acceptance Criteria Analyzed: {payload['ac_count']}")
    print("-" * 80)

    print("ADVERSARIAL SPECIFICATION FINDINGS:")
    for item in payload["audit_log"]:
        print(f"  {item}")

    print("-" * 80)
    print("RECOMMENDED CONTRACT INTERPRETATIONS (Record in RED test docstrings & PR):")
    if payload["interpretations"]:
        for interp in payload["interpretations"]:
            print(f"  [{interp['id']}] {interp['title']}:")
            print(f"       \"{interp['text']}\"")
    else:
        print("  (None required; specification is fully unambiguous)")

    print("-" * 80)
    print("BAYESIAN DECISION RESOLUTION:")
    print(f"  Proceed to Implementation Utility: {payload['scores'].get('proceed_to_implementation', 0.0):.4f}")
    print(f"  Clarify Spec & Amend Utility:     {payload['scores'].get('clarify_spec_and_amend', 0.0):.4f}")
    print(f"  Robust Utility Margin:            {payload['margin']:+.4f} (Threshold: >={args.min_margin:+.2f})")
    if payload.get("episode_id"):
        print(f"  Governance Episode Persisted:     {payload['episode_id']}")

    print("=" * 80)
    if passed:
        print("VERDICT: PASSED / SPEC READY FOR CONTRACTS")
    else:
        print("VERDICT: HALTED / SPEC AMENDMENT REQUIRED")
    print("=" * 80)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
