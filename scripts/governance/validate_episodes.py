#!/usr/bin/env python3
"""
Validate Governance Episodes Script

Purpose:
    Validate governance episodes in both repository and external store to detect
    discrepancies. This script operationalizes GC-002 from LL-046 
    (Evidence Management Synchronization).

Background:
    LL-046 identified that gate evidence was split between two locations:
    1. External store (AGENT_LEARNING_LOCAL_STORE_DIR)
    2. Repository copies (docs/policy-shapes/episodes/)
    
    This created an incomplete audit trail with no reconciliation mechanism.
    SPA-20261106-001 requires automated validation to detect discrepancies.

Usage:
    python scripts/governance/validate_episodes.py [options]

Options:
    --repo-only          Only check repository episodes
    --store-only         Only check external store episodes
    --detailed           Show detailed validation results
    --fix               Attempt to fix discrepancies (sync missing files)
    --verbose           Enable verbose output
    --output FILE       Save report to file
    --help              Show this help message

Examples:
    # Validate both locations
    python scripts/governance/validate_episodes.py
    
    # Validate repository only
    python scripts/governance/validate_episodes.py --repo-only
    
    # Validate with detailed output
    python scripts/governance/validate_episodes.py --detailed
    
    # Validate and save report
    python scripts/governance/validate_episodes.py --output validation-report.json

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
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validate_episodes.log')
    ]
)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class EpisodeValidator:
    """
    Main class for validating governance episodes.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the episode validator.
        
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
            logger.debug(f"External store dir: {self.external_store_dir}")
    
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
        
        common_locations = [
            Path.home() / ".agent_learning_store",
            Path("/opt/agent_learning_store"),
            Path("/var/lib/agent_learning_store"),
        ]
        
        for loc in common_locations:
            if loc.exists():
                logger.info(f"Found external store at: {loc}")
                return loc
        
        logger.warning("AGENT_LEARNING_LOCAL_STORE_DIR not set and no default location found")
        return None
    
    def _validate_paths(self) -> None:
        """Validate that required paths exist."""
        if not self.repo_episodes_dir.exists():
            raise ValidationError(
                f"Repository episodes directory not found: {self.repo_episodes_dir}"
            )
        
        if not self.repo_episodes_dir.is_dir():
            raise ValidationError(
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
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error loading episode from {file_path}: {e}")
            return None
    
    def _validate_episode_schema(self, episode: Dict) -> Tuple[bool, List[str]]:
        """
        Validate an episode has all required fields and valid values.
        
        Args:
            episode: Episode dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ['episode_id', 'timestamp', 'policy', 'action']
        for field in required_fields:
            if field not in episode:
                errors.append(f"Missing required field: {field}")
        
        # Check episode_id format (UUID v4)
        if 'episode_id' in episode:
            episode_id = episode['episode_id']
            if not self._is_valid_uuid(episode_id):
                errors.append(f"Invalid episode_id format: {episode_id}")
        
        # Check timestamp format
        if 'timestamp' in episode:
            timestamp = episode['timestamp']
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                errors.append(f"Invalid timestamp format: {timestamp}")
        
        # Check policy exists
        if 'policy' in episode:
            policy = episode['policy']
            if not policy or not isinstance(policy, str):
                errors.append(f"Invalid policy: {policy}")
        
        # Check action exists
        if 'action' in episode:
            action = episode['action']
            if not action or not isinstance(action, str):
                errors.append(f"Invalid action: {action}")
        
        return (len(errors) == 0, errors)
    
    def _is_valid_uuid(self, uuid_str: str) -> bool:
        """
        Check if a string is a valid UUID v4.
        
        Args:
            uuid_str: String to check
            
        Returns:
            True if valid UUID v4, False otherwise
        """
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)
        return bool(uuid_pattern.match(uuid_str))
    
    def _get_relative_path(self, file_path: Path) -> Path:
        """
        Get the relative path of an episode file.
        
        Args:
            file_path: Absolute path to the episode file
            
        Returns:
            Relative path from the episodes directory
        """
        try:
            return file_path.relative_to(self.repo_episodes_dir)
        except ValueError:
            return file_path.name
    
    def validate_repo_episodes(self) -> Dict:
        """
        Validate all episodes in the repository.
        
        Returns:
            Dictionary with validation results
        """
        episode_files = self._get_episode_files(self.repo_episodes_dir)
        
        results = {
            'location': 'repository',
            'total': len(episode_files),
            'valid': 0,
            'invalid': 0,
            'details': []
        }
        
        for file_path in episode_files:
            episode = self._load_episode(file_path)
            
            if episode is None:
                results['details'].append({
                    'file': str(self._get_relative_path(file_path)),
                    'valid': False,
                    'errors': ['Failed to load episode']
                })
                results['invalid'] += 1
                continue
            
            is_valid, errors = self._validate_episode_schema(episode)
            
            results['details'].append({
                'file': str(self._get_relative_path(file_path)),
                'valid': is_valid,
                'errors': errors,
                'episode_id': episode.get('episode_id'),
                'timestamp': episode.get('timestamp'),
                'policy': episode.get('policy')
            })
            
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1
                logger.warning(f"Invalid episode: {self._get_relative_path(file_path)}")
        
        return results
    
    def validate_store_episodes(self) -> Dict:
        """
        Validate all episodes in the external store.
        
        Returns:
            Dictionary with validation results
        """
        if not self.external_store_dir:
            return {
                'location': 'external_store',
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'error': 'External store not configured',
                'details': []
            }
        
        if not self.external_store_dir.exists():
            return {
                'location': 'external_store',
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'error': 'External store directory does not exist',
                'details': []
            }
        
        episode_files = self._get_episode_files(self.external_store_dir)
        
        results = {
            'location': 'external_store',
            'total': len(episode_files),
            'valid': 0,
            'invalid': 0,
            'details': []
        }
        
        for file_path in episode_files:
            episode = self._load_episode(file_path)
            
            if episode is None:
                results['details'].append({
                    'file': str(self._get_relative_path(file_path)),
                    'valid': False,
                    'errors': ['Failed to load episode']
                })
                results['invalid'] += 1
                continue
            
            is_valid, errors = self._validate_episode_schema(episode)
            
            results['details'].append({
                'file': str(self._get_relative_path(file_path)),
                'valid': is_valid,
                'errors': errors,
                'episode_id': episode.get('episode_id'),
                'timestamp': episode.get('timestamp'),
                'policy': episode.get('policy')
            })
            
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1
                logger.warning(f"Invalid episode in store: {self._get_relative_path(file_path)}")
        
        return results
    
    def compare_locations(self) -> Dict:
        """
        Compare episodes between repository and external store.
        
        Returns:
            Dictionary with comparison results
        """
        if not self.external_store_dir or not self.external_store_dir.exists():
            return {
                'comparison': 'skipped',
                'reason': 'External store not configured or does not exist',
                'repo_only': [],
                'store_only': [],
                'both': [],
                'discrepancies': []
            }
        
        # Get episodes from both locations
        repo_files = self._get_episode_files(self.repo_episodes_dir)
        store_files = self._get_episode_files(self.external_store_dir)
        
        # Extract episode IDs
        repo_episodes = {}
        for file_path in repo_files:
            episode = self._load_episode(file_path)
            if episode and 'episode_id' in episode:
                repo_episodes[episode['episode_id']] = file_path
        
        store_episodes = {}
        for file_path in store_files:
            episode = self._load_episode(file_path)
            if episode and 'episode_id' in episode:
                store_episodes[episode['episode_id']] = file_path
        
        # Find differences
        repo_only_ids = set(repo_episodes.keys()) - set(store_episodes.keys())
        store_only_ids = set(store_episodes.keys()) - set(repo_episodes.keys())
        both_ids = set(repo_episodes.keys()) & set(store_episodes.keys())
        
        # Check for content discrepancies in episodes that exist in both
        discrepancies = []
        for episode_id in both_ids:
            repo_file = repo_episodes[episode_id]
            store_file = store_episodes[episode_id]
            
            repo_episode = self._load_episode(repo_file)
            store_episode = self._load_episode(store_file)
            
            if repo_episode != store_episode:
                discrepancies.append({
                    'episode_id': episode_id,
                    'repo_file': str(self._get_relative_path(repo_file)),
                    'store_file': str(self._get_relative_path(store_file)),
                    'difference': 'Content differs'
                })
        
        return {
            'comparison': 'completed',
            'repo_only': [
                {
                    'episode_id': eid,
                    'file': str(self._get_relative_path(repo_episodes[eid]))
                } for eid in sorted(repo_only_ids)
            ],
            'store_only': [
                {
                    'episode_id': eid,
                    'file': str(self._get_relative_path(store_episodes[eid]))
                } for eid in sorted(store_only_ids)
            ],
            'both': sorted(both_ids),
            'discrepancies': discrepancies
        }
    
    def validate_all(self) -> Dict:
        """
        Validate all episodes in both locations and compare.
        
        Returns:
            Dictionary with complete validation results
        """
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'repository': self.validate_repo_episodes(),
            'external_store': self.validate_store_episodes(),
            'comparison': self.compare_locations()
        }
        
        # Calculate summary
        total_repo = results['repository']['total']
        valid_repo = results['repository']['valid']
        total_store = results['external_store']['total']
        valid_store = results['external_store']['valid']
        
        results['summary'] = {
            'repository': {
                'total': total_repo,
                'valid': valid_repo,
                'invalid': total_repo - valid_repo,
                'valid_percentage': (valid_repo / total_repo * 100) if total_repo > 0 else 0
            },
            'external_store': {
                'total': total_store,
                'valid': valid_store,
                'invalid': total_store - valid_store,
                'valid_percentage': (valid_store / total_store * 100) if total_store > 0 else 0
            },
            'comparison': {
                'repo_only_count': len(results['comparison']['repo_only']),
                'store_only_count': len(results['comparison']['store_only']),
                'both_count': len(results['comparison']['both']),
                'discrepancy_count': len(results['comparison']['discrepancies'])
            }
        }
        
        # Determine overall status
        if results['comparison']['comparison'] == 'skipped':
            results['summary']['overall_status'] = 'PARTIAL'
            results['summary']['overall_message'] = 'External store not available'
        elif (results['comparison']['repo_only_count'] > 0 or 
              results['comparison']['store_only_count'] > 0 or
              results['comparison']['discrepancy_count'] > 0):
            results['summary']['overall_status'] = 'FAILED'
            results['summary']['overall_message'] = 'Discrepancies found'
        elif results['repository']['invalid'] > 0 or results['external_store']['invalid'] > 0:
            results['summary']['overall_status'] = 'FAILED'
            results['summary']['overall_message'] = 'Invalid episodes found'
        else:
            results['summary']['overall_status'] = 'PASSED'
            results['summary']['overall_message'] = 'All episodes valid and synchronized'
        
        return results


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Validate governance episodes in repository and external store',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--repo-only',
        action='store_true',
        help='Only check repository episodes'
    )
    
    parser.add_argument(
        '--store-only',
        action='store_true',
        help='Only check external store episodes'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed validation results'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix discrepancies by syncing missing files'
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
    
    # Initialize validator
    try:
        validator = EpisodeValidator(verbose=args.verbose)
    except ValidationError as e:
        logger.error(f"Initialization error: {e}")
        sys.exit(1)
    
    # Run validation
    if args.repo_only:
        results = {'repository': validator.validate_repo_episodes()}
    elif args.store_only:
        results = {'external_store': validator.validate_store_episodes()}
    else:
        results = validator.validate_all()
    
    # Print results
    if args.detailed:
        print(json.dumps(results, indent=2))
    else:
        # Print summary
        print("\n" + "="*60)
        print("GOVERNANCE EPISODE VALIDATION REPORT")
        print("="*60)
        print(f"Generated: {results.get('timestamp', 'N/A')}")
        print()
        
        if 'summary' in results:
            summary = results['summary']
            
            print("REPOSITORY:")
            print(f"  Total episodes: {summary['repository']['total']}")
            print(f"  Valid: {summary['repository']['valid']}")
            print(f"  Invalid: {summary['repository']['invalid']}")
            print(f"  Valid percentage: {summary['repository']['valid_percentage']:.1f}%")
            print()
            
            print("EXTERNAL STORE:")
            print(f"  Total episodes: {summary['external_store']['total']}")
            print(f"  Valid: {summary['external_store']['valid']}")
            print(f"  Invalid: {summary['external_store']['invalid']}")
            print(f"  Valid percentage: {summary['external_store']['valid_percentage']:.1f}%")
            print()
            
            print("COMPARISON:")
            comp = summary['comparison']
            print(f"  Repository only: {comp['repo_only_count']}")
            print(f"  Store only: {comp['store_only_count']}")
            print(f"  In both: {comp['both_count']}")
            print(f"  Discrepancies: {comp['discrepancy_count']}")
            print()
            
            print(f"OVERALL STATUS: {summary.get('overall_status', 'UNKNOWN')}")
            print(f"MESSAGE: {summary.get('overall_message', 'N/A')}")
            print("="*60 + "\n")
            
            # Print discrepancies if any
            if 'comparison' in results and results['comparison']['comparison'] == 'completed':
                comp = results['comparison']
                
                if comp['repo_only_count'] > 0:
                    print("\nFiles only in REPOSITORY:")
                    for item in comp['repo_only']:
                        print(f"  - {item['file']} ({item['episode_id']})")
                
                if comp['store_only_count'] > 0:
                    print("\nFiles only in EXTERNAL STORE:")
                    for item in comp['store_only']:
                        print(f"  - {item['file']} ({item['episode_id']})")
                
                if comp['discrepancy_count'] > 0:
                    print("\nFiles with DISCREPANCIES:")
                    for item in comp['discrepancies']:
                        print(f"  - {item['episode_id']}: {item['difference']}")
                        print(f"    Repository: {item['repo_file']}")
                        print(f"    Store: {item['store_file']}")
        else:
            print(json.dumps(results, indent=2))
    
    # Save to file if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Report saved to: {args.output}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    # Exit with appropriate code
    if 'summary' in results:
        if results['summary'].get('overall_status') == 'PASSED':
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
