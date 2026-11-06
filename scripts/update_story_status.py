#!/usr/bin/env python3
"""
Update Story Status Script

Purpose:
    Automate story status updates in implementation-log.md to eliminate drift
    between epic files and implementation-log.md. This script operationalizes
    GC-004 from LL-045 (Single Source of Truth for Story Status).

Background:
    LL-045 identified that story status is held in two places:
    1. Epic file (Status line)
    2. implementation-log.md
    
    These are edited by hand at different steps, causing drift.
    The solution is to maintain status in implementation-log.md as the canonical
    source and derive all other representations from it.

Usage:
    python scripts/update_story_status.py [options] <story_id> <new_status>

Options:
    --epic EPIC          Update status in epic file (derived from implementation-log)
    --log                Update status in implementation-log.md (canonical source)
    --both               Update both (log first, then epic)
    --dry-run            Simulate update without making changes
    --verbose            Enable verbose output
    --validate           Validate all story statuses for drift
    --fix-drift          Automatically fix all drift by syncing from log to epics
    --help               Show this help message

Examples:
    # Update story 20.1 to "Implemented" in implementation-log
    python scripts/update_story_status.py --log 20.1 Implemented
    
    # Update story 20.1 to "Implemented" in both log and epic
    python scripts/update_story_status.py --both 20.1 Implemented
    
    # Validate all story statuses
    python scripts/update_story_status.py --validate
    
    # Fix all drift
    python scripts/update_story_status.py --fix-drift

Author:
    Vibe Code (operationalizing GC-004 from LL-045)

Date:
    2026-11-06

Related:
    - ADP-20261106-001 (Stage 17 Adaptation Plan)
    - GC-004 (Governance Change)
    - LL-045 (Single Source of Truth for Story Status)
    - INSIGHT-002 (Story status is held in two places that are updated at different steps)
    - OBS-003 (Story status drift - 15 stories)
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/update_story_status.log')
    ]
)
logger = logging.getLogger(__name__)


class StoryStatusError(Exception):
    """Custom exception for story status errors."""
    pass


class StoryStatusUpdater:
    """
    Main class for updating story status.
    """
    
    # Valid status values
    VALID_STATUSES = ['Draft', 'Ready', 'In Progress', 'Implemented', 'Blocked', 'Superseded']
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the story status updater.
        
        Args:
            verbose: If True, enable verbose logging
        """
        self.verbose = verbose
        
        # Get repository root
        self.repo_root = self._get_repo_root()
        
        # Define paths
        self.implementation_log_path = self.repo_root / "implementation-log.md"
        self.epics_dir = self.repo_root / "docs" / "user-stories"
        
        # Validate paths
        self._validate_paths()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug(f"Repository root: {self.repo_root}")
            logger.debug(f"Implementation log: {self.implementation_log_path}")
            logger.debug(f"Epics dir: {self.epics_dir}")
    
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
    
    def _validate_paths(self) -> None:
        """Validate that required paths exist."""
        if not self.implementation_log_path.exists():
            raise StoryStatusError(
                f"Implementation log not found: {self.implementation_log_path}"
            )
        
        if not self.epics_dir.exists():
            logger.warning(f"Epics directory not found: {self.epics_dir}")
    
    def _parse_implementation_log(self) -> List[Dict]:
        """
        Parse implementation-log.md to extract story entries.
        
        Returns:
            List of dictionaries with story information
        """
        stories = []
        
        with open(self.implementation_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by story entries (assuming format: | Story ID | Status | ... |)
        # This is a simplified parser - adjust based on actual format
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('---'):
                continue
            
            # Try to parse story entry
            if '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    story_id = parts[0]
                    status = parts[1]
                    
                    # Extract epic from story ID (e.g., 20.1 -> Epic 20)
                    epic_num = None
                    if '.' in story_id:
                        try:
                            epic_num = story_id.split('.')[0]
                        except Exception:
                            pass
                    
                    stories.append({
                        'story_id': story_id,
                        'status': status,
                        'epic': epic_num,
                        'source': 'implementation-log'
                    })
        
        return stories
    
    def _find_epic_file(self, epic_num: str) -> Optional[Path]:
        """
        Find the epic file for a given epic number.
        
        Args:
            epic_num: The epic number (e.g., "20")
            
        Returns:
            Path to the epic file, or None if not found
        """
        # Try common patterns
        patterns = [
            f"epic-{epic_num}.md",
            f"Epic-{epic_num}.md",
            f"epic{epic_num}.md",
            f"Epic{epic_num}.md",
        ]
        
        for pattern in patterns:
            epic_file = self.epics_dir / pattern
            if epic_file.exists():
                return epic_file
        
        return None
    
    def _parse_epic_file(self, epic_file: Path) -> List[Dict]:
        """
        Parse an epic file to extract story entries.
        
        Args:
            epic_file: Path to the epic file
            
        Returns:
            List of dictionaries with story information
        """
        stories = []
        
        with open(epic_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse stories from epic file
        # This is a simplified parser - adjust based on actual format
        lines = content.split('\n')
        
        current_story = None
        for line in lines:
            line = line.strip()
            
            # Check for story header (e.g., ### Story 20.1: ...)
            if line.startswith('### Story') or line.startswith('#### Story'):
                # Extract story ID
                match = re.search(r'Story\s+(\d+\.\d+)', line)
                if match:
                    story_id = match.group(1)
                    current_story = {
                        'story_id': story_id,
                        'epic': epic_file.stem.replace('epic-', '').replace('Epic-', '').replace('epic', '').replace('Epic', ''),
                        'source': str(epic_file.relative_to(self.repo_root))
                    }
                    stories.append(current_story)
            
            # Check for status line
            elif current_story and line.startswith('Status:'):
                status = line.split(':', 1)[1].strip()
                current_story['status'] = status
        
        return stories
    
    def _get_all_stories(self) -> Dict[str, List[Dict]]:
        """
        Get all stories from both implementation-log and epic files.
        
        Returns:
            Dictionary mapping story_id to list of entries (from different sources)
        """
        stories = {}
        
        # Get stories from implementation-log
        log_stories = self._parse_implementation_log()
        for story in log_stories:
            story_id = story['story_id']
            if story_id not in stories:
                stories[story_id] = []
            stories[story_id].append(story)
        
        # Get stories from epic files
        if self.epics_dir.exists():
            for epic_file in self.epics_dir.glob("epic-*.md"):
                epic_stories = self._parse_epic_file(epic_file)
                for story in epic_stories:
                    story_id = story['story_id']
                    if story_id not in stories:
                        stories[story_id] = []
                    stories[story_id].append(story)
        
        return stories
    
    def validate_statuses(self) -> Dict:
        """
        Validate all story statuses for drift between sources.
        
        Returns:
            Dictionary with validation results
        """
        all_stories = self._get_all_stories()
        
        results = {
            'total_stories': len(all_stories),
            'no_drift': 0,
            'with_drift': 0,
            'details': [],
            'drift_count': 0
        }
        
        for story_id, entries in all_stories.items():
            # Get all statuses for this story
            statuses = {entry['source']: entry.get('status') for entry in entries if 'status' in entry}
            
            if not statuses:
                # No status found for this story
                results['details'].append({
                    'story_id': story_id,
                    'status': 'no_status',
                    'sources': [entry['source'] for entry in entries],
                    'message': 'No status found in any source'
                })
                results['with_drift'] += 1
                results['drift_count'] += 1
                continue
            
            # Check if all statuses are the same
            unique_statuses = set(statuses.values())
            
            if len(unique_statuses) == 1:
                # No drift
                results['no_drift'] += 1
                results['details'].append({
                    'story_id': story_id,
                    'status': list(unique_statuses)[0],
                    'sources': list(statuses.keys()),
                    'message': 'No drift'
                })
            else:
                # Drift detected
                results['with_drift'] += 1
                results['drift_count'] += 1
                results['details'].append({
                    'story_id': story_id,
                    'statuses': statuses,
                    'sources': list(statuses.keys()),
                    'message': 'Drift detected'
                })
                logger.warning(f"Drift detected for {story_id}: {statuses}")
        
        # Calculate percentages
        if results['total_stories'] > 0:
            results['no_drift_percentage'] = (results['no_drift'] / results['total_stories']) * 100
            results['with_drift_percentage'] = (results['with_drift'] / results['total_stories']) * 100
        else:
            results['no_drift_percentage'] = 0
            results['with_drift_percentage'] = 0
        
        # Determine overall status
        if results['drift_count'] == 0:
            results['overall_status'] = 'PASSED'
            results['overall_message'] = 'No drift detected'
        else:
            results['overall_status'] = 'FAILED'
            results['overall_message'] = f"{results['drift_count']} stories with drift"
        
        return results
    
    def update_in_implementation_log(self, story_id: str, new_status: str, dry_run: bool = False) -> Dict:
        """
        Update story status in implementation-log.md.
        
        Args:
            story_id: The story ID to update
            new_status: The new status
            dry_run: If True, simulate update without saving
            
        Returns:
            Dictionary with update result
        """
        # Validate status
        if new_status not in self.VALID_STATUSES:
            return {
                'success': False,
                'error': f"Invalid status: {new_status}. Valid statuses: {', '.join(self.VALID_STATUSES)}"
            }
        
        # Read implementation-log
        with open(self.implementation_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and update the story entry
        lines = content.split('\n')
        updated_lines = []
        found = False
        
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2 and parts[0] == story_id:
                    # Found the story, update status
                    parts[1] = new_status
                    updated_line = ' | '.join(parts)
                    # Preserve leading/trailing whitespace
                    if line.startswith(' '):
                        updated_line = ' ' + updated_line
                    updated_lines.append(updated_line)
                    found = True
                    continue
            updated_lines.append(line)
        
        if not found:
            return {
                'success': False,
                'error': f"Story {story_id} not found in implementation-log.md"
            }
        
        # Join lines back
        updated_content = '\n'.join(updated_lines)
        
        if dry_run:
            return {
                'success': True,
                'message': f"[DRY RUN] Would update {story_id} to {new_status} in implementation-log.md"
            }
        else:
            # Write updated content
            with open(self.implementation_log_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return {
                'success': True,
                'message': f"Updated {story_id} to {new_status} in implementation-log.md"
            }
    
    def update_in_epic(self, story_id: str, new_status: str, dry_run: bool = False) -> Dict:
        """
        Update story status in its epic file.
        
        Args:
            story_id: The story ID to update
            new_status: The new status
            dry_run: If True, simulate update without saving
            
        Returns:
            Dictionary with update result
        """
        # Validate status
        if new_status not in self.VALID_STATUSES:
            return {
                'success': False,
                'error': f"Invalid status: {new_status}. Valid statuses: {', '.join(self.VALID_STATUSES)}"
            }
        
        # Extract epic number from story ID
        if '.' not in story_id:
            return {
                'success': False,
                'error': f"Invalid story ID format: {story_id}. Expected format: <epic>.<story>"
            }
        
        epic_num = story_id.split('.')[0]
        
        # Find epic file
        epic_file = self._find_epic_file(epic_num)
        if not epic_file:
            return {
                'success': False,
                'error': f"Epic file for {epic_num} not found"
            }
        
        # Read epic file
        with open(epic_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and update the story status
        lines = content.split('\n')
        updated_lines = []
        in_story = False
        story_found = False
        
        for line in lines:
            # Check for story header
            if line.startswith('### Story') or line.startswith('#### Story'):
                match = re.search(r'Story\s+(\d+\.\d+)', line)
                if match and match.group(1) == story_id:
                    in_story = True
                    story_found = True
                else:
                    in_story = False
            
            # Check for status line
            elif in_story and line.startswith('Status:'):
                updated_line = f"Status: {new_status}"
                # Preserve indentation
                indent = len(line) - len(line.lstrip())
                updated_line = ' ' * indent + updated_line
                updated_lines.append(updated_line)
                in_story = False
                continue
            
            updated_lines.append(line)
        
        if not story_found:
            return {
                'success': False,
                'error': f"Story {story_id} not found in {epic_file}"
            }
        
        # Join lines back
        updated_content = '\n'.join(updated_lines)
        
        if dry_run:
            return {
                'success': True,
                'message': f"[DRY RUN] Would update {story_id} to {new_status} in {epic_file}"
            }
        else:
            # Write updated content
            with open(epic_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return {
                'success': True,
                'message': f"Updated {story_id} to {new_status} in {epic_file}"
            }
    
    def update_status(self, story_id: str, new_status: str, 
                      update_log: bool = False, update_epic: bool = False,
                      dry_run: bool = False) -> Dict:
        """
        Update story status in specified locations.
        
        Args:
            story_id: The story ID to update
            new_status: The new status
            update_log: If True, update in implementation-log.md
            update_epic: If True, update in epic file
            dry_run: If True, simulate update without saving
            
        Returns:
            Dictionary with update results
        """
        results = {
            'story_id': story_id,
            'new_status': new_status,
            'updates': [],
            'success': True
        }
        
        # Update in implementation-log (canonical source)
        if update_log:
            result = self.update_in_implementation_log(story_id, new_status, dry_run)
            results['updates'].append({
                'location': 'implementation-log',
                'success': result['success'],
                'message': result.get('message', result.get('error', 'Unknown'))
            })
            results['success'] = results['success'] and result['success']
        
        # Update in epic (derived from canonical source)
        if update_epic:
            result = self.update_in_epic(story_id, new_status, dry_run)
            results['updates'].append({
                'location': 'epic',
                'success': result['success'],
                'message': result.get('message', result.get('error', 'Unknown'))
            })
            results['success'] = results['success'] and result['success']
        
        # If neither location specified, default to implementation-log
        if not update_log and not update_epic:
            result = self.update_in_implementation_log(story_id, new_status, dry_run)
            results['updates'].append({
                'location': 'implementation-log',
                'success': result['success'],
                'message': result.get('message', result.get('error', 'Unknown'))
            })
            results['success'] = result['success']
        
        return results
    
    def fix_drift(self, dry_run: bool = False) -> Dict:
        """
        Automatically fix all drift by syncing status from implementation-log to epics.
        
        Args:
            dry_run: If True, simulate fixes without saving
            
        Returns:
            Dictionary with fix results
        """
        # Get all stories
        all_stories = self._get_all_stories()
        
        results = {
            'total_stories': len(all_stories),
            'fixed': 0,
            'skipped': 0,
            'failed': 0,
            'details': [],
            'success': True
        }
        
        for story_id, entries in all_stories.items():
            # Find implementation-log entry (canonical source)
            log_entry = next((e for e in entries if e['source'] == 'implementation-log'), None)
            
            if not log_entry or 'status' not in log_entry:
                results['skipped'] += 1
                results['details'].append({
                    'story_id': story_id,
                    'status': 'skipped',
                    'message': 'No status in implementation-log (canonical source)'
                })
                continue
            
            # Get canonical status
            canonical_status = log_entry['status']
            
            # Find epic entries that have different status
            epic_entries = [e for e in entries if e['source'] != 'implementation-log' and 'status' in e]
            
            for epic_entry in epic_entries:
                if epic_entry['status'] != canonical_status:
                    # Need to fix this
                    epic_file = epic_entry['source']
                    
                    if dry_run:
                        results['fixed'] += 1
                        results['details'].append({
                            'story_id': story_id,
                            'status': 'fixed',
                            'message': f"[DRY RUN] Would sync {story_id} from {epic_entry['status']} to {canonical_status} in {epic_file}",
                            'from': epic_entry['status'],
                            'to': canonical_status,
                            'file': epic_file
                        })
                        logger.info(f"[DRY RUN] Would sync {story_id} from {epic_entry['status']} to {canonical_status} in {epic_file}")
                    else:
                        try:
                            # Update the epic file
                            result = self.update_in_epic(story_id, canonical_status, dry_run=False)
                            
                            if result['success']:
                                results['fixed'] += 1
                                results['details'].append({
                                    'story_id': story_id,
                                    'status': 'fixed',
                                    'message': result['message'],
                                    'from': epic_entry['status'],
                                    'to': canonical_status,
                                    'file': epic_file
                                })
                                logger.info(f"Fixed {story_id}: {epic_entry['status']} -> {canonical_status} in {epic_file}")
                            else:
                                results['failed'] += 1
                                results['success'] = False
                                results['details'].append({
                                    'story_id': story_id,
                                    'status': 'failed',
                                    'message': result.get('error', 'Unknown error'),
                                    'from': epic_entry['status'],
                                    'to': canonical_status,
                                    'file': epic_file
                                })
                                logger.error(f"Failed to fix {story_id} in {epic_file}: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            results['failed'] += 1
                            results['success'] = False
                            results['details'].append({
                                'story_id': story_id,
                                'status': 'failed',
                                'message': str(e),
                                'from': epic_entry['status'],
                                'to': canonical_status,
                                'file': epic_file
                            })
                            logger.error(f"Error fixing {story_id} in {epic_file}: {e}")
        
        return results


# Import os for path operations
import os


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Update story status to eliminate drift',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'story_id',
        nargs='?',
        type=str,
        help='Story ID to update (e.g., 20.1)'
    )
    
    parser.add_argument(
        'new_status',
        nargs='?',
        type=str,
        help='New status for the story'
    )
    
    parser.add_argument(
        '--epic',
        action='store_true',
        help='Update status in epic file (derived from implementation-log)'
    )
    
    parser.add_argument(
        '--log',
        action='store_true',
        help='Update status in implementation-log.md (canonical source)'
    )
    
    parser.add_argument(
        '--both',
        action='store_true',
        help='Update status in both log and epic'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate update without making changes'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate all story statuses for drift'
    )
    
    parser.add_argument(
        '--fix-drift',
        action='store_true',
        help='Automatically fix all drift by syncing from log to epics'
    )
    
    args = parser.parse_args()
    
    # Initialize updater
    try:
        updater = StoryStatusUpdater(verbose=args.verbose)
    except StoryStatusError as e:
        logger.error(f"Initialization error: {e}")
        sys.exit(1)
    
    # Validate mode
    if args.validate:
        results = updater.validate_statuses()
        
        print("\n" + "="*80)
        print("STORY STATUS VALIDATION REPORT")
        print("="*80)
        print()
        
        print(f"Total stories: {results['total_stories']}")
        print(f"No drift: {results['no_drift']} ({results['no_drift_percentage']:.1f}%)")
        print(f"With drift: {results['with_drift']} ({results['with_drift_percentage']:.1f}%)")
        print(f"Drift count: {results['drift_count']}")
        print()
        print(f"Overall status: {results['overall_status']}")
        print(f"Message: {results['overall_message']}")
        print()
        
        if results['drift_count'] > 0:
            print("Stories with drift:")
            for detail in results['details']:
                if detail['message'] == 'Drift detected':
                    print(f"  ❌ {detail['story_id']}: {detail['statuses']}")
        
        print("="*80 + "\n")
        
        sys.exit(0 if results['overall_status'] == 'PASSED' else 1)
    
    # Fix drift mode
    elif args.fix_drift:
        results = updater.fix_drift(dry_run=args.dry_run)
        
        print("\n" + "="*80)
        print("DRIFT FIX REPORT")
        print("="*80)
        print()
        
        if args.dry_run:
            print("[DRY RUN] No changes were made")
            print()
        
        print(f"Total stories: {results['total_stories']}")
        print(f"Fixed: {results['fixed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Failed: {results['failed']}")
        print(f"Status: {'SUCCESS' if results['success'] else 'FAILED'}")
        print()
        
        if results['details']:
            print("Details:")
            for detail in results['details']:
                status_icon = "✅" if detail['status'] == 'fixed' else "⚠️" if detail['status'] == 'skipped' else "❌"
                print(f"  {status_icon} {detail['story_id']}: {detail['message']}")
        
        print("="*80 + "\n")
        
        sys.exit(0 if results['success'] else 1)
    
    # Update mode
    elif args.story_id and args.new_status:
        # Determine update locations
        update_log = args.log or args.both
        update_epic = args.epic or args.both
        
        if not update_log and not update_epic:
            # Default to canonical source (implementation-log)
            update_log = True
        
        results = updater.update_status(
            args.story_id,
            args.new_status,
            update_log=update_log,
            update_epic=update_epic,
            dry_run=args.dry_run
        )
        
        print("\n" + "="*80)
        print("STORY STATUS UPDATE REPORT")
        print("="*80)
        print()
        
        if args.dry_run:
            print("[DRY RUN] No changes were made")
            print()
        
        print(f"Story: {results['story_id']}")
        print(f"New status: {results['new_status']}")
        print(f"Status: {'SUCCESS' if results['success'] else 'FAILED'}")
        print()
        
        if results['updates']:
            print("Updates:")
            for update in results['updates']:
                status_icon = "✅" if update['success'] else "❌"
                print(f"  {status_icon} {update['location']}: {update['message']}")
        
        print("="*80 + "\n")
        
        sys.exit(0 if results['success'] else 1)
    
    else:
        # No arguments or invalid arguments
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
