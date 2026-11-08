#!/usr/bin/env python3
"""
Synchronize Governance Episodes Script

Purpose:
    Synchronize governance episodes from the repository (authoritative source) 
    to the external store. This script operationalizes GC-002 from LL-046 
    (Evidence Management Synchronization).

Background:
    LL-046 identified that gate evidence was split between two locations:
    1. External store (AGENT_LEARNING_LOCAL_STORE_DIR)
    2. Repository copies (docs/policy-shapes/episodes/)
    
    This created an incomplete audit trail with no reconciliation mechanism.
    SPA-20261106-001 designated the repository as the authoritative source
    and requires automated synchronization to the external store.

Usage:
    python scripts/governance/sync_episodes.py [options]

Options:
    --dry-run           Simulate sync without making changes
    --force             Force sync even if files exist in destination
    --verbose           Enable verbose output
    --from DATE        Sync episodes from this date (YYYY-MM-DD)
    --to DATE          Sync episodes to this date (YYYY-MM-DD)
    --specific ID       Sync specific episode by ID
    --validate          Validate episodes before syncing
    --help             Show this help message

Examples:
    # Dry run sync
    python scripts/governance/sync_episodes.py --dry-run
    
    # Force sync all episodes
    python scripts/governance/sync_episodes.py --force
    
    # Sync episodes from specific date
    python scripts/governance/sync_episodes.py --from 2026-11-01
    
    # Sync specific episode
    python scripts/governance/sync_episodes.py --specific a1b2c3d4-e5f6-7890-abcd-ef1234567890

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
import shutil
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
        logging.FileHandler('logs/sync_episodes.log')
    ]
)
logger = logging.getLogger(__name__)


class SyncEpisodesError(Exception):
    """Custom exception for sync errors."""
    pass


class EpisodeSync:
    """
    Main class for synchronizing governance episodes.
    """
    
    def __init__(self, dry_run: bool = False, force: bool = False, verbose: bool = False):
        """
        Initialize the episode sync.
        
        Args:
            dry_run: If True, simulate sync without making changes
            force: If True, force sync even if files exist in destination
            verbose: If True, enable verbose logging
        """
        self.dry_run = dry_run
        self.force = force
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
        # Try to get from environment variable
        repo_root = os.environ.get('REPO_ROOT')
        if repo_root:
            return Path(repo_root)
        
        # Try to get from git
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not get repo root from git: {e}")
        
        # Fall back to current directory
        return Path.cwd()
    
    def _get_external_store_dir(self) -> Optional[Path]:
        """Get the external store directory."""
        store_path = os.environ.get('AGENT_LEARNING_LOCAL_STORE_DIR')
        if store_path:
            return Path(store_path)
        
        # Try common locations
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
            raise SyncEpisodesError(
                f"Repository episodes directory not found: {self.repo_episodes_dir}"
            )
        
        if not self.repo_episodes_dir.is_dir():
            raise SyncEpisodesError(
                f"Repository episodes path is not a directory: {self.repo_episodes_dir}"
            )
        
        # External store is optional (may not exist yet)
        if self.external_store_dir:
            if not self.external_store_dir.exists():
                logger.info(f"External store directory does not exist, will be created: {self.external_store_dir}")
    
    def _get_episode_files(self, episodes_dir: Path, date_from: Optional[datetime] = None, 
                           date_to: Optional[datetime] = None) -> List[Path]:
        """
        Get list of episode files from a directory.
        
        Args:
            episodes_dir: Directory to search for episodes
            date_from: Only include files modified after this date
            date_to: Only include files modified before this date
            
        Returns:
            List of Path objects for episode files
        """
        episode_files = []
        
        if not episodes_dir.exists():
            return episode_files
        
        for file_path in episodes_dir.glob("*.json"):
            if not file_path.is_file():
                continue
            
            # Check date filters
            if date_from or date_to:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if date_from and mtime < date_from:
                    continue
                if date_to and mtime > date_to:
                    continue
            
            episode_files.append(file_path)
        
        return sorted(episode_files)
    
    def _load_episode(self, file_path: Path) -> Dict:
        """
        Load an episode from a JSON file.
        
        Args:
            file_path: Path to the episode JSON file
            
        Returns:
            Dictionary containing episode data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in episode file {file_path}: {e}")
            raise SyncEpisodesError(f"Invalid JSON in {file_path}")
        except Exception as e:
            logger.error(f"Error loading episode from {file_path}: {e}")
            raise SyncEpisodesError(f"Error loading {file_path}")
    
    def _validate_episode(self, episode: Dict) -> bool:
        """
        Validate an episode has required fields.
        
        Args:
            episode: Episode dictionary to validate
            
        Returns:
            True if episode is valid, False otherwise
        """
        required_fields = ['episode_id', 'timestamp', 'policy', 'action']
        
        for field in required_fields:
            if field not in episode:
                logger.warning(f"Episode missing required field: {field}")
                return False
        
        return True
    
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
            # If file is not under repo_episodes_dir, use just the filename
            return file_path.name
    
    def _sync_episode(self, episode_file: Path) -> Tuple[bool, str]:
        """
        Sync a single episode file to the external store.
        
        Args:
            episode_file: Path to the episode file to sync
            
        Returns:
            Tuple of (success, message)
        """
        if not self.external_store_dir:
            return False, "External store directory not configured"
        
        # Get relative path
        rel_path = self._get_relative_path(episode_file)
        
        # Create destination path
        dest_path = self.external_store_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists and we're not forcing
        if dest_path.exists() and not self.force:
            # Compare files
            if self._files_equal(episode_file, dest_path):
                logger.debug(f"File already synced: {rel_path}")
                return True, f"Already synced: {rel_path}"
            else:
                logger.warning(f"File differs but force not set: {rel_path}")
                return False, f"File differs, use --force to overwrite: {rel_path}"
        
        # Load and validate episode
        episode = self._load_episode(episode_file)
        if not self._validate_episode(episode):
            return False, f"Invalid episode: {rel_path}"
        
        # Sync the file
        if self.dry_run:
            logger.info(f"[DRY RUN] Would sync: {rel_path}")
            return True, f"[DRY RUN] Would sync: {rel_path}"
        else:
            try:
                shutil.copy2(episode_file, dest_path)
                logger.info(f"Synced: {rel_path}")
                return True, f"Synced: {rel_path}"
            except Exception as e:
                logger.error(f"Error syncing {rel_path}: {e}")
                return False, f"Error syncing {rel_path}: {e}"
    
    def _files_equal(self, file1: Path, file2: Path) -> bool:
        """
        Compare two files for equality.
        
        Args:
            file1: First file path
            file2: Second file path
            
        Returns:
            True if files are identical, False otherwise
        """
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                return f1.read() == f2.read()
        except Exception:
            return False
    
    def sync_all(self, date_from: Optional[datetime] = None, 
                 date_to: Optional[datetime] = None) -> Dict:
        """
        Sync all episodes from repository to external store.
        
        Args:
            date_from: Only sync episodes from this date
            date_to: Only sync episodes to this date
            
        Returns:
            Dictionary with sync results
        """
        if not self.external_store_dir:
            return {
                'success': False,
                'error': 'External store directory not configured',
                'synced': 0,
                'failed': 0,
                'skipped': 0
            }
        
        # Get episode files
        episode_files = self._get_episode_files(self.repo_episodes_dir, date_from, date_to)
        
        if not episode_files:
            logger.info("No episodes found to sync")
            return {
                'success': True,
                'message': 'No episodes found',
                'synced': 0,
                'failed': 0,
                'skipped': 0
            }
        
        logger.info(f"Found {len(episode_files)} episodes to sync")
        
        # Sync each episode
        results = {
            'success': True,
            'synced': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for episode_file in episode_files:
            success, message = self._sync_episode(episode_file)
            
            if success:
                results['synced'] += 1
            else:
                if "Already synced" in message or "differs" in message:
                    results['skipped'] += 1
                else:
                    results['failed'] += 1
                    results['success'] = False
            
            results['details'].append({
                'file': str(self._get_relative_path(episode_file)),
                'success': success,
                'message': message
            })
            
            if self.verbose:
                logger.info(message)
        
        # Summary
        logger.info(f"Sync complete: {results['synced']} synced, "
                   f"{results['failed']} failed, {results['skipped']} skipped")
        
        return results
    
    def sync_specific(self, episode_id: str) -> Dict:
        """
        Sync a specific episode by ID.
        
        Args:
            episode_id: The episode ID to sync
            
        Returns:
            Dictionary with sync result
        """
        # Find episode file with matching ID
        episode_files = self._get_episode_files(self.repo_episodes_dir)
        target_file = None
        
        for file_path in episode_files:
            try:
                episode = self._load_episode(file_path)
                if episode.get('episode_id') == episode_id:
                    target_file = file_path
                    break
            except Exception:
                continue
        
        if not target_file:
            return {
                'success': False,
                'error': f"Episode {episode_id} not found in repository",
                'file': None
            }
        
        success, message = self._sync_episode(target_file)
        
        return {
            'success': success,
            'message': message,
            'file': str(self._get_relative_path(target_file)),
            'episode_id': episode_id
        }


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string into a datetime object."""
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        return None


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Synchronize governance episodes from repository to external store',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate sync without making changes'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force sync even if files exist in destination'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--from',
        type=str,
        metavar='DATE',
        help='Sync episodes from this date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--to',
        type=str,
        metavar='DATE',
        help='Sync episodes to this date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--specific',
        type=str,
        metavar='ID',
        help='Sync specific episode by ID'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate episodes before syncing'
    )
    
    args = parser.parse_args()
    
    # Parse dates
    date_from = parse_date(args.from) if args.from else None
    date_to = parse_date(args.to) if args.to else None
    
    # Initialize sync
    try:
        sync = EpisodeSync(
            dry_run=args.dry_run,
            force=args.force,
            verbose=args.verbose
        )
    except SyncEpisodesError as e:
        logger.error(f"Initialization error: {e}")
        sys.exit(1)
    
    # Run sync
    if args.specific:
        # Sync specific episode
        result = sync.sync_specific(args.specific)
        
        if result['success']:
            logger.info(f"Successfully synced episode {args.specific}")
            sys.exit(0)
        else:
            logger.error(f"Failed to sync episode {args.specific}: {result.get('error', result.get('message', 'Unknown error'))}")
            sys.exit(1)
    else:
        # Sync all episodes
        result = sync.sync_all(date_from, date_to)
        
        if result['success']:
            logger.info("Sync completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Sync completed with errors: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == '__main__':
    main()
