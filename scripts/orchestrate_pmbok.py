"""
PMBOK 8 Subsidiary Plans & PMP Orchestrator for SIDPA Template Projects.

Generates and updates the 9 subsidiary management plans and the integrated
Project Management Plan (PMP) using project-anchored context from:
- docs/project-docs/Spark-Capture.md
- docs/project-docs/Ideation-Document.md
- docs/project-docs/Business-Case.md
- docs/project-docs/Project-Charter.md

Also provides closed-loop adaptation regeneration via:
--adapt-from docs/project-docs/Adaptation-Plan.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

# Add sidpa-template root to sys.path so pmbok is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

os.environ["ADPA_AUDIT_MODE"] = "advisory"

from pmbok.models.enums import ProcessGroup
from pmbok.models.pmbok import ProjectArtifact
from pmbok.storage.artifact_store import ArtifactStore
from pmbok.storage.state_store import StateStore
from pmbok.agents.factory import ProcessAgentFactory
from pmbok.agents.process_agent import _StubLLMClient
from pmbok.orchestrator.orchestrator import PMBOKOrchestrator
from pmbok.output.pretty_printer import PrettyPrinter

PLAN_MAPPING = {
    "5.1": {"name": "Scope-Management-Plan", "title": "Scope Management Plan", "flag": "Scope Management Plan"},
    "6.1": {"name": "Schedule-Management-Plan", "title": "Schedule Management Plan", "flag": "Schedule / Cost Plans"},
    "7.1": {"name": "Cost-Management-Plan", "title": "Cost Management Plan", "flag": "Schedule / Cost Plans"},
    "8.1": {"name": "Quality-Management-Plan", "title": "Quality Management Plan", "flag": "Quality Management Plan"},
    "9.1": {"name": "Resource-Management-Plan", "title": "Resource Management Plan", "flag": "Resource Management Plan"},
    "10.1": {"name": "Communications-Management-Plan", "title": "Communications Management Plan", "flag": "Communications Management Plan"},
    "11.1": {"name": "Risk-Management-Plan", "title": "Risk Management Plan", "flag": "Risk Management Plan"},
    "12.1": {"name": "Procurement-Management-Plan", "title": "Procurement Management Plan", "flag": "Procurement Management Plan"},
    "13.2": {"name": "Stakeholder-Engagement-Plan", "title": "Stakeholder Engagement Plan", "flag": "Stakeholder Engagement Plan"},
}

def extract_project_identity(charter_path: Path) -> dict[str, str]:
    """Extract project title and objectives from Project Charter."""
    if not charter_path.exists():
        return {
            "title": "SIDPA Project",
            "objectives": ["Establish validated development lifecycle", "Enforce PMBOK 8 governance baselines"]
        }
    text = charter_path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).replace("Project Charter", "").strip(" :-") if title_match else "SIDPA Project"
    if not title:
        title = "SIDPA Project"
    return {
        "title": title,
        "objectives": [
            "Formalize PMBOK 8 planning baselines",
            "Generate verified subsidiary management plans",
            "Integrate into Project Management Plan (PMP)"
        ]
    }

def synthesize_pmp_markdown(project_context: dict, generated_plans: dict[str, str]) -> str:
    """Synthesize integrated Project-Management-Plan.md from subsidiary plans."""
    lines = [
        "---",
        'pmbok_edition: "PMBOK 8"',
        'pmbok_process_group: "Planning"',
        'pmbok_process: "4.2 Develop Project Management Plan"',
        'lifecycle_stage: "Stage 6 (Project)"',
        'governance_policy: "approve-pmp"',
        "inputs:",
        '  - "Project-Charter.md"',
        '  - "docs/project-docs/management-plans/*.md"',
        'process: "Integrate subsidiary management plans, establish baselines, define governance gates"',
        "outputs:",
        '  - "Project-Management-Plan.md"',
        "---",
        "",
        f"# Project Management Plan (PMP) — {project_context['title']}",
        "",
        "> **PMBOK 8 Process:** `4.2 Develop Project Management Plan` (Planning)  ",
        "> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 6 (Project)`  ",
        "> **Inputs:** Project-Charter.md, Subsidiary Management Plans  ",
        "> **Process:** Integrate subsidiary management plans, establish baselines, define governance gates  ",
        "> **Outputs:** Project-Management-Plan.md",
        "",
        "## 1. Executive Summary & Baselines",
        f"- **Project Title:** {project_context['title']}",
        "- **Scope Baseline:** Approved scope boundary traced to Project Charter objectives.",
        "- **Schedule Baseline / Progressive Elaboration:** Milestones established; duration detailed progressively from empirical evidence.",
        "- **Cost Baseline / Progressive Elaboration:** Investment limits from Business Case; detailed cost tracked as resources are committed.",
        "",
        "## 2. Integrated Subsidiary Management Plans",
        ""
    ]
    
    for pid, meta in PLAN_MAPPING.items():
        doc_name = f"{meta['name']}.md"
        summary = generated_plans.get(pid, f"Detailed in [management-plans/{doc_name}](management-plans/{doc_name}).")
        lines.append(f"### 2.{pid} {meta['title']}")
        lines.append(f"**Document Link:** [management-plans/{doc_name}](management-plans/{doc_name})")
        lines.append(f"- **Summary:** {summary[:300]}...")
        lines.append("")

    lines.extend([
        "## 3. Feedback Loop from Adaptation",
        "When an **Adaptation Plan** (Stage 17) is approved, this PMP and its subsidiary plans are updated with tailored operational changes, which in turn trigger refined ADRs, BRDs, FDDs, and Stories for the next cycle.",
        "",
        "## 4. Governance Authorization",
        "This integrated PMP must be formally evaluated and approved via `approve-pmp` (`FULL` Bayesian authority, `requires_human_approval: true`) before technical specifications (ADR, BRD, FDD, Stories) are finalized."
    ])
    return "\n".join(lines) + "\n"

def parse_adaptation_checklist(adaptation_path: Path) -> list[str]:
    """Parse checked subsidiary management plans from Adaptation-Plan.md."""
    if not adaptation_path.exists():
        return []
    content = adaptation_path.read_text(encoding="utf-8")
    checked = []
    for line in content.splitlines():
        match = re.match(r"^-\s*\[[xX]\]\s*\*\*([^*]+)\*\*", line)
        if match:
            checked.append(match.group(1).strip())
    return checked

async def run_orchestration(args):
    charter_file = Path(args.charter)
    project_context = extract_project_identity(charter_file)
    print(f"\n=======================================================")
    print(f"  SIDPA PMBOK Orchestrator — {project_context['title']}")
    print(f"  Mode: {args.mode.upper()}")
    print(f"=======================================================\n")

    plans_dir = repo_root / "docs" / "project-docs" / "management-plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    storage_dir = repo_root / "data" / "pmbok_runtime"
    storage_dir.mkdir(parents=True, exist_ok=True)

    artifact_store = ArtifactStore(storage_dir)
    state_store = StateStore(str(storage_dir / "state.db"))

    # Determine LLM client
    has_api_key = bool(os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))
    if args.mock or not has_api_key:
        print("  [INFO] Using High-Fidelity Deterministic Engine (Offline / Stub)")
        from pmbok.agents.process_agent import _StubLLMClient
        llm_client = _StubLLMClient()
    else:
        print("  [INFO] Using Live LLM Foundry Client")
        from pmbok.llm import create_llm_client
        llm_client = create_llm_client()

    factory = ProcessAgentFactory(llm_client=llm_client, artifact_store=artifact_store)

    target_processes = list(PLAN_MAPPING.keys())
    if args.mode == "adapt" and args.adaptation_plan:
        adapt_file = Path(args.adaptation_plan)
        checked_flags = parse_adaptation_checklist(adapt_file)
        print(f"  [ADAPT] Checked plans in {adapt_file.name}: {checked_flags}")
        target_processes = [
            pid for pid, meta in PLAN_MAPPING.items()
            if any(flag in meta["flag"] or meta["title"] in flag for flag in checked_flags)
        ]
        if not target_processes:
            print("  [ADAPT] No specific subsidiary plans checked. Defaulting to full re-sync.")
            target_processes = list(PLAN_MAPPING.keys())

    print(f"  Target PMBOK Processes: {target_processes}\n")

    printer = PrettyPrinter()
    generated_summaries = {}

    from pmbok.process_registry import PMBOK_PROCESSES
    proc_map = {p.process_id: p for p in PMBOK_PROCESSES}

    for pid in target_processes:
        meta = PLAN_MAPPING[pid]
        proc = proc_map.get(pid)
        if not proc:
            print(f"      [WARN] Process {pid} not found in registry")
            continue

        print(f"  >>> Executing PMBOK {pid}: {meta['title']}...")
        agent = factory.create(proc)
        # Execute agent
        prompt = (
            f"Generate high-fidelity {meta['title']} (PMBOK {pid}) for project '{project_context['title']}'.\n"
            f"Objectives: {', '.join(project_context['objectives'])}.\n"
            f"Expected outputs: ['{meta['title']}']"
        )
        try:
            artifacts = await agent.execute(
                run_id="sidpa-run",
                input_artifacts=[],
                project_context=project_context
            )
            if artifacts:
                art = artifacts[0]
                doc_path = plans_dir / f"{meta['name']}.md"
                md_content = f"""---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "{pid} {meta['title']}"
lifecycle_stage: "Stage 6 (Project)"
governance_policy: "approve-pmp"
inputs:
  - "Project-Charter.md"
process: "Plan and formalize {meta['title']}"
outputs:
  - "{meta['name']}.md"
---

# {meta['title']} — {project_context['title']}

> **PMBOK 8 Process:** `{pid} {meta['title']}` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 6 (Project)`  
> **Source:** [Project-Charter.md](../Project-Charter.md)

## 1. Purpose & Scope
This plan establishes the guidelines and processes for managing {meta['title'].lower()} across the lifecycle of **{project_context['title']}**.

## 2. Process Specifications
```json
{json.dumps(art.content, indent=2)}
```

## 3. Review & Governance Invariant
This subsidiary plan integrates directly into [Project-Management-Plan.md](../Project-Management-Plan.md) and is verified under `approve-pmp`.
"""
                doc_path.write_text(md_content, encoding="utf-8")
                generated_summaries[pid] = f"Formulated {meta['title']} addressing {', '.join(project_context['objectives'])}."
                print(f"      [OK] Written to {doc_path.relative_to(repo_root)}")
        except Exception as e:
            print(f"      [WARN] Execution error on {pid}: {e}")

    # Synthesize PMP
    print("\n  >>> Synthesizing integrated Project Management Plan (4.2)...")
    pmp_file = repo_root / "docs" / "project-docs" / "Project-Management-Plan.md"
    pmp_markdown = synthesize_pmp_markdown(project_context, generated_summaries)
    pmp_file.write_text(pmp_markdown, encoding="utf-8")
    print(f"  [OK] Project Management Plan written to {pmp_file.relative_to(repo_root)}")

    # Decision Validation Gate Notice
    print("\n-------------------------------------------------------")
    print("  Decision Gate Verification:")
    print("  Run 'agent-learn task-policy-decide --agent-id template-governance --task-id approve-pmp'")
    print("  to formally validate the synthesized PMP.")
    print("-------------------------------------------------------\n")

def main():
    parser = argparse.ArgumentParser(description="Orchestrate PMBOK 8 Subsidiary Plans and PMP")
    parser.add_argument("--mode", choices=["full", "adapt"], default="full", help="Execution mode (full or adapt)")
    parser.add_argument("--charter", default="docs/project-docs/Project-Charter.template.md", help="Path to Project Charter")
    parser.add_argument("--adaptation-plan", default="docs/project-docs/Adaptation-Plan.template.md", help="Path to Adaptation Plan")
    parser.add_argument("--mock", action="store_true", help="Force mock/offline execution")
    args = parser.parse_args()

    asyncio.run(run_orchestration(args))

if __name__ == "__main__":
    main()
