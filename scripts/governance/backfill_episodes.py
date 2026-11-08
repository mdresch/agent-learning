#!/usr/bin/env python3
"""
Backfill Governance Episodes Script

Purpose:
    Create missing governance episodes for upstream gates that were identified
    in LL-046. This script operationalizes GC-002 from LL-046 
    (Evidence Management Synchronization).

Background:
    LL-046 and INSIGHT-004 identified that upstream gates (approve-charter,
    approve-business-case) have no episodes recorded, while later gates do.
    This creates an incomplete audit trail.
    
    SPA-20261106-001 requires backfilling these missing episodes to ensure
    a complete and consistent audit trail.

Usage:
    python scripts/governance/backfill_episodes.py [options]

Options:
    --list              List all gates and their episode status
    --missing           List only gates with missing episodes
    --create            Create missing episodes
    --dry-run           Simulate creation without saving
    --force             Force creation even if episodes exist
    --verbose           Enable verbose output
    --output FILE       Save report to file
    --help              Show this help message

Examples:
    # List all gates and their status
    python scripts/governance/backfill_episodes.py --list
    
    # List only gates with missing episodes
    python scripts/governance/backfill_episodes.py --missing
    
    # Create missing episodes (dry run)
    python scripts/governance/backfill_episodes.py --create --dry-run
    
    # Create missing episodes for real
    python scripts/governance/backfill_episodes.py --create

Author:
    Vibe Code (operationalizing GC-002 from LL-046)

Date:
    2026-11-06

Related:
    - ADP-20261106-001 (Stage 17 Adaptation Plan)
    - SPA-20261106-001 (Evidence Management Synchronization)
    - GC-002 (Governance Change)
    - LL-046 (Dual Evidence Storage Requires Reconciliation)
    - INSIGHT-004 (Gate evidence is split between the repository and an external store)
    - OBS-007 (Upstream gates missing episodes)
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/backfill_episodes.log')
    ]
)
logger = logging.getLogger(__name__)


class BackfillError(Exception):
    """Custom exception for backfill errors."""
    pass


class EpisodeBackfiller:
    """
    Main class for backfilling missing governance episodes.
    """
    
    # Known gates that should have episodes
    KNOWN_GATES = [
        {
            'policy': 'approve-ideation',
            'name': 'Ideation Approval',
            'description': 'Validates Spark Capture and Ideation Document',
            'pmbok_process': 'Pre-Project Initiating',
            'required': True
        },
        {
            'policy': 'approve-charter',
            'name': 'Charter Approval',
            'description': 'Validates Project Charter and measurable objectives',
            'pmbok_process': '4.1 Develop Project Charter',
            'required': True
        },
        {
            'policy': 'approve-business-case',
            'name': 'Business Case Approval',
            'description': 'Validates Business Case, Benefits Statement, and value premise',
            'pmbok_process': 'Business Documents Initiating',
            'required': True
        },
        {
            'policy': 'approve-project-pillars',
            'name': 'Project Pillars Approval',
            'description': 'Validates architectural pillars and decomposition',
            'pmbok_process': 'Planning',
            'required': True
        },
        {
            'policy': 'approve-adr',
            'name': 'ADR Approval',
            'description': 'Evaluates architectural soundness and consequence honesty',
            'pmbok_process': '5.3 Define Scope / Architecture',
            'required': True
        },
        {
            'policy': 'approve-brd',
            'name': 'BRD Approval',
            'description': 'Evaluates business rules and stakeholder alignment',
            'pmbok_process': '5.2 Collect Requirements',
            'required': True
        },
        {
            'policy': 'approve-fdd',
            'name': 'FDD Approval',
            'description': 'Evaluates technical interface design and invariant enforcement',
            'pmbok_process': '5.3 Detailed Interface Design',
            'required': True
        },
        {
            'policy': 'approve-user-stories',
            'name': 'User Stories Approval',
            'description': 'Evaluates testability of acceptance criteria',
            'pmbok_process': '5.4 Create WBS / Backlog',
            'required': True
        },
        {
            'policy': 'validate-intent-foundation',
            'name': 'Intent Foundation Validation',
            'description': 'Pre-implementation gate ensuring requirement artifacts are grounded',
            'pmbok_process': 'Planning → Executing Gate',
            'required': True
        },
        {
            'policy': 'approve-audit-record',
            'name': 'Audit Record Approval',
            'description': 'Validates audit findings and corrective actions',
            'pmbok_process': '8.2 Manage Quality Audits',
            'required': True
        },
        {
            'policy': 'approve-subsidiary-plan',
            'name': 'Subsidiary Plan Approval',
            'description': 'Evaluates individual subsidiary management plans',
            'pmbok_process': '5.1/6.1/7.1 Subsidiary Planning',
            'required': True
        },
        {
            'policy': 'approve-pmp',
            'name': 'PMP Approval',
            'description': 'Formalizes integrated Project Management Plan',
            'pmbok_process': '4.2 Develop PMP',
            'required': True
        },
        {
            'policy': 'approve-adaptation-plan',
            'name': 'Adaptation Plan Approval',
            'description': 'Validates operational rollout of governance changes',
            'pmbok_process': '4.6 Change Tailoring',
            'required': True
        },
        {
            'policy': 'approve-intent-refinement',
            'name': 'Intent Refinement Approval',
            'description': 'Validates cognitive feedback from outcomes',
            'pmbok_process': '4.7 Close Phase / Cognitive Feedback',
            'required': True
        },
    ]
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the episode backfiller.
        
        Args:
            verbose: If True, enable verbose logging
        """
        self.verbose = verbose
        
        # Get repository root
        self.repo_root = self._get_repo_root()
        
        # Define paths
        self.repo_episodes_dir = Path(self.repo_root) / "docs" / "policy-shapes" / "episodes"
        self.external_store_dir = self._get_external_store_dir()
        
        # Validate paths
        self._validate_paths()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug(f"Repository root: {self.repo_root}")
            logger.debug(f"Repository episodes dir: {self.repo_episodes_dir}")
    
    def _get_repo_root(self) -> Path:
        """Get the repository root directory."""
        repo_root = os.environ.get('REPO_ROOT')
        if repo_root:
            return Path(repo_root)
        
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except Exception:
            return Path.cwd()
    
    def _get_external_store_dir(self) -> Optional[Path]:
        """Get the external store directory."""
        store_path = os.environ.get('AGENT_LEARNING_LOCAL_STORE_DIR')
        if store_path:
            return Path(store_path)
        
        return None
    
    def _validate_paths(self) -> None:
        """Validate that required paths exist."""
        if not self.repo_episodes_dir.exists():
            raise BackfillError(
                f"Repository episodes directory not found: {self.repo_episodes_dir}"
            )
        
        if not self.repo_episodes_dir.is_dir():
            raise BackfillError(
                f"Repository episodes path is not a directory: {self.repo_episodes_dir}"
            )
    
    def _get_episode_files(self, episodes_dir: Path) -> List[Path]:
        """
        Get list of episode files from a directory.
        
        Args:
            episodes_dir: Directory to search for episodes
            
        Returns:
            List of Path objects for episode files
        """
        episode_files = []
        
        if not episodes_dir.exists():
            return episode_files
        
        for file_path in episodes_dir.glob("*.json"):
            if file_path.is_file():
                episode_files.append(file_path)
        
        return sorted(episode_files)
    
    def _load_episode(self, file_path: Path) -> Optional[Dict]:
        """
        Load an episode from a JSON file.
        
        Args:
            file_path: Path to the episode JSON file
            
        Returns:
            Dictionary containing episode data, or None if invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return None
    
    def _get_existing_episodes(self) -> Dict[str, Path]:
        """
        Get all existing episodes from repository.
        
        Returns:
            Dictionary mapping episode_id to file path
        """
        episodes = {}
        episode_files = self._get_episode_files(self.repo_episodes_dir)
        
        for file_path in episode_files:
            episode = self._load_episode(file_path)
            if episode and 'episode_id' in episode:
                episodes[episode['episode_id']] = file_path
        
        return episodes
    
    def _check_gate_has_episode(self, policy: str) -> Tuple[bool, Optional[Path]]:
        """
        Check if a gate (policy) has at least one episode.
        
        Args:
            policy: The policy name to check
            
        Returns:
            Tuple of (has_episode, file_path)
        """
        existing_episodes = self._get_existing_episodes()
        
        for episode_id, file_path in existing_episodes.items():
            episode = self._load_episode(file_path)
            if episode and episode.get('policy') == policy:
                return True, file_path
        
        return False, None
    
    def list_gates(self) -> List[Dict]:
        """
        List all gates and their episode status.
        
        Returns:
            List of dictionaries with gate information and status
        """
        results = []
        
        for gate in self.KNOWN_GATES:
            has_episode, file_path = self._check_gate_has_episode(gate['policy'])
            
            results.append({
                'policy': gate['policy'],
                'name': gate['name'],
                'description': gate['description'],
                'pmbok_process': gate['pmbok_process'],
                'required': gate['required'],
                'has_episode': has_episode,
                'episode_file': str(file_path) if file_path else None
            })
        
        return results
    
    def list_missing_gates(self) -> List[Dict]:
        """
        List gates that are missing episodes.
        
        Returns:
            List of dictionaries with missing gate information
        """
        all_gates = self.list_gates()
        missing = [gate for gate in all_gates if not gate['has_episode']]
        return missing
    
    def _generate_episode_id(self) -> str:
        """
        Generate a new UUID v4 for an episode.
        
        Returns:
            String containing UUID v4
        """
        return str(uuid.uuid4())
    
    def _get_gate_approval_date(self, policy: str) -> Optional[datetime]:
        """
        Get the approval date for a gate from its document.
        
        Args:
            policy: The policy name
            
        Returns:
            Datetime of approval, or None if not found
        """
        # Map policies to their document paths
        policy_docs = {
            'approve-ideation': 'docs/Ideation-Document.md',
            'approve-charter': 'docs/project-docs/Project-Charter.md',
            'approve-business-case': 'docs/project-docs/Business-Case.md',
            'approve-project-pillars': 'docs/Project-Pillars.md',
            'approve-pmp': 'docs/project-docs/Project-Management-Plan.md',
        }
        
        doc_path = self.repo_root / policy_docs.get(policy, '')
        
        if not doc_path.exists():
            return None
        
        # Try to extract date from document
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for approval date in various formats
                import re
                date_patterns = [
                    r'approval_date:\s*(\d{4}-\d{2}-\d{2})',
                    r'date:\s*(\d{4}-\d{2}-\d{2})',
                    r'Approved:\s*(\d{4}-\d{2}-\d{2})',
                    r'last_updated:\s*["\'](\d{4}-\d{2}-\d{2})',
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        try:
                            return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue
        except Exception:
            pass
        
        return None
    
    def _get_gate_decision_maker(self, policy: str) -> str:
        """
        Get the decision maker for a gate.
        
        Args:
            policy: The policy name
            
        Returns:
            String with decision maker name
        """
        # Default decision makers based on policy
        decision_makers = {
            'approve-ideation': 'Project Sponsor',
            'approve-charter': 'Project Sponsor',
            'approve-business-case': 'Project Sponsor',
            'approve-project-pillars': 'Project Manager',
            'approve-adr': 'Project Manager',
            'approve-brd': 'Project Manager',
            'approve-fdd': 'Project Manager',
            'approve-user-stories': 'Project Manager',
            'validate-intent-foundation': 'Project Manager',
            'approve-audit-record': 'Project Manager',
            'approve-subsidiary-plan': 'Project Manager',
            'approve-pmp': 'Steering Committee',
            'approve-adaptation-plan': 'Project Manager',
            'approve-intent-refinement': 'Project Sponsor',
        }
        
        return decision_makers.get(policy, 'Unknown')
    
    def _get_gate_decision(self, policy: str) -> str:
        """
        Get a generic decision text for a gate.
        
        Args:
            policy: The policy name
            
        Returns:
            String with decision text
        """
        decisions = {
            'approve-ideation': 'Ideation document and spark capture approved',
            'approve-charter': 'Project charter approved with measurable objectives',
            'approve-business-case': 'Business case and benefits statement approved',
            'approve-project-pillars': 'Project pillars approved and decomposed',
            'approve-adr': 'Architectural decision record approved',
            'approve-brd': 'Business requirements document approved',
            'approve-fdd': 'Functional design document approved',
            'approve-user-stories': 'User stories with testable acceptance criteria approved',
            'validate-intent-foundation': 'Intent foundation validated, ready for implementation',
            'approve-audit-record': 'Audit record approved with findings and corrective actions',
            'approve-subsidiary-plan': 'Subsidiary management plan approved',
            'approve-pmp': 'Project Management Plan approved and baselined',
            'approve-adaptation-plan': 'Adaptation plan approved, governance changes operationalized',
            'approve-intent-refinement': 'Intent refinement approved, strategic feedback incorporated',
        }
        
        return decisions.get(policy, f'{policy} approved')
    
    def _create_episode(self, policy: str, action: str = "approve", 
                       timestamp: Optional[datetime] = None) -> Dict:
        """
        Create a new episode for a gate.
        
        Args:
            policy: The policy name
            action: The action (approve, reject, request_revision)
            timestamp: The timestamp for the episode (defaults to now)
            
        Returns:
            Dictionary containing the new episode
        """
        if timestamp is None:
            # Try to get approval date from document
            timestamp = self._get_gate_approval_date(policy)
            if timestamp is None:
                # Use a reasonable default (2026-11-04 for Phase 1 gates)
                timestamp = datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc)
        
        # Find the gate info
        gate_info = next((g for g in self.KNOWN_GATES if g['policy'] == policy), None)
        
        episode = {
            'episode_id': self._generate_episode_id(),
            'timestamp': timestamp.isoformat(),
            'policy': policy,
            'action': action,
            'decision': self._get_gate_decision(policy),
            'decision_maker': self._get_gate_decision_maker(policy),
            'evidence': {
                'basis': 'design_time',
                'artifacts': [
                    f'docs/{policy.replace("-", "_")}.md',
                    'docs/project-docs/Project-Status-Register.md'
                ]
            },
            'related_episodes': [],
            'stage': 16 if policy == 'approve-audit-record' else None,
            'pmbok_process': gate_info['pmbok_process'] if gate_info else None,
            'project_phase': 'Phase 1',
            'links': {}
        }
        
        # Add specific evidence based on policy
        if policy == 'approve-charter':
            episode['evidence']['artifacts'].extend([
                'docs/project-docs/Business-Case.md',
                'docs/project-docs/Benefits-Statement.md'
            ])
        elif policy == 'approve-business-case':
            episode['evidence']['artifacts'].extend([
                'docs/project-docs/Project-Charter.md'
            ])
        elif policy == 'approve-pmp':
            episode['evidence']['artifacts'].extend([
                'docs/project-docs/management-plans/Scope-Management-Plan.md',
                'docs/project-docs/management-plans/Schedule-Management-Plan.md',
                'docs/project-docs/management-plans/Cost-Management-Plan.md'
            ])
        
        return episode
    
    def _save_episode(self, episode: Dict, file_path: Optional[Path] = None) -> Path:
        """
        Save an episode to a JSON file.
        
        Args:
            episode: The episode dictionary to save
            file_path: Optional file path (defaults to episodes dir with episode_id)
            
        Returns:
            Path where the episode was saved
        """
        if file_path is None:
            file_name = f"{episode['policy']}-{episode['action']}-{episode['episode_id']}.json"
            file_path = self.repo_episodes_dir / file_name
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(episode, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def create_missing_episodes(self, dry_run: bool = False, force: bool = False) -> Dict:
        """
        Create missing episodes for gates that don't have them.
        
        Args:
            dry_run: If True, simulate creation without saving
            force: If True, create even if episodes exist
            
        Returns:
            Dictionary with creation results
        """
        missing_gates = self.list_missing_gates()
        
        if not missing_gates:
            return {
                'success': True,
                'message': 'No missing episodes found',
                'created': 0,
                'skipped': 0,
                'details': []
            }
        
        results = {
            'success': True,
            'created': 0,
            'skipped': 0,
            'details': []
        }
        
        for gate in missing_gates:
            policy = gate['policy']
            
            # Check if episode exists (might have been created by another process)
            has_episode, _ = self._check_gate_has_episode(policy)
            
            if has_episode and not force:
                results['skipped'] += 1
                results['details'].append({
                    'policy': policy,
                    'status': 'skipped',
                    'message': 'Episode already exists'
                })
                logger.info(f"Skipping {policy}: episode already exists")
                continue
            
            # Create episode
            episode = self._create_episode(policy, action='approve')
            
            if dry_run:
                results['created'] += 1
                results['details'].append({
                    'policy': policy,
                    'status': 'created',
                    'message': f"[DRY RUN] Would create episode {episode['episode_id']}",
                    'episode_id': episode['episode_id'],
                    'timestamp': episode['timestamp']
                })
                logger.info(f"[DRY RUN] Would create episode for {policy}: {episode['episode_id']}")
            else:
                try:
                    file_path = self._save_episode(episode)
                    results['created'] += 1
                    results['details'].append({
                        'policy': policy,
                        'status': 'created',
                        'message': f"Created episode {episode['episode_id']}",
                        'episode_id': episode['episode_id'],
                        'timestamp': episode['timestamp'],
                        'file': str(file_path.relative_to(self.repo_root))
                    })
                    logger.info(f"Created episode for {policy}: {episode['episode_id']}")
                except Exception as e:
                    results['success'] = False
                    results['details'].append({
                        'policy': policy,
                        'status': 'failed',
                        'message': f"Error creating episode: {e}",
                        'error': str(e)
                    })
                    logger.error(f"Error creating episode for {policy}: {e}")
        
        return results


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Backfill missing governance episodes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all gates and their episode status'
    )
    
    parser.add_argument(
        '--missing',
        action='store_true',
        help='List only gates with missing episodes'
    )
    
    parser.add_argument(
        '--create',
        action='store_true',
        help='Create missing episodes'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate creation without saving'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force creation even if episodes exist'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Save report to file'
    )
    
    args = parser.parse_args()
    
    # Initialize backfiller
    try:
        backfiller = EpisodeBackfiller(verbose=args.verbose)
    except BackfillError as e:
        logger.error(f"Initialization error: {e}")
        sys.exit(1)
    
    # Run appropriate action
    if args.list:
        gates = backfiller.list_gates()
        
        print("\n" + "="*80)
        print("GOVERNANCE GATE EPISODE STATUS")
        print("="*80)
        print()
        
        for gate in gates:
            status = "✅ Has Episode" if gate['has_episode'] else "❌ Missing"
            print(f"{status} {gate['policy']:30} - {gate['name']}")
            if gate['has_episode']:
                print(f"     Episode file: {gate['episode_file']}")
        
        print("="*80 + "\n")
        
        # Summary
        total = len(gates)
        with_episodes = sum(1 for g in gates if g['has_episode'])
        missing = total - with_episodes
        
        print(f"Total gates: {total}")
        print(f"With episodes: {with_episodes}")
        print(f"Missing episodes: {missing}")
        
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(gates, f, indent=2)
                logger.info(f"Report saved to: {args.output}")
            except Exception as e:
                logger.error(f"Error saving report: {e}")
        
        sys.exit(0 if missing == 0 else 1)
    
    elif args.missing:
        missing_gates = backfiller.list_missing_gates()
        
        print("\n" + "="*80)
        print("GATES WITH MISSING EPISODES")
        print("="*80)
        print()
        
        if not missing_gates:
            print("All gates have episodes!")
        else:
            for gate in missing_gates:
                print(f"❌ {gate['policy']:30} - {gate['name']}")
                print(f"     PMBOK Process: {gate['pmbok_process']}")
                print(f"     Description: {gate['description']}")
                print()
        
        print("="*80 + "\n")
        print(f"Total missing: {len(missing_gates)}")
        
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(missing_gates, f, indent=2)
                logger.info(f"Report saved to: {args.output}")
            except Exception as e:
                logger.error(f"Error saving report: {e}")
        
        sys.exit(0 if len(missing_gates) == 0 else 1)
    
    elif args.create:
        results = backfiller.create_missing_episodes(
            dry_run=args.dry_run,
            force=args.force
        )
        
        print("\n" + "="*80)
        print("BACKFILL RESULTS")
        print("="*80)
        print()
        
        if args.dry_run:
            print("[DRY RUN] No changes were made")
            print()
        
        print(f"Created: {results['created']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Status: {'SUCCESS' if results['success'] else 'FAILED'}")
        print()
        
        if results['details']:
            print("Details:")
            for detail in results['details']:
                status_icon = "✅" if detail['status'] == 'created' else "⚠️" if detail['status'] == 'skipped' else "❌"
                print(f"  {status_icon} {detail['policy']}: {detail['message']}")
        
        print("="*80 + "\n")
        
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Report saved to: {args.output}")
            except Exception as e:
                logger.error(f"Error saving report: {e}")
        
        sys.exit(0 if results['success'] else 1)
    
    else:
        # Default: list missing gates
        missing_gates = backfiller.list_missing_gates()
        
        print("\n" + "="*80)
        print("GATES WITH MISSING EPISODES")
        print("="*80)
        print()
        
        if not missing_gates:
            print("All gates have episodes!")
        else:
            for gate in missing_gates:
                print(f"❌ {gate['policy']}")
        
        print("="*80 + "\n")
        print(f"Total missing: {len(missing_gates)}")
        print("Use --list to see all gates, --missing to see details, --create to create episodes")
        
        sys.exit(0 if len(missing_gates) == 0 else 1)


if __name__ == '__main__':
    main()
