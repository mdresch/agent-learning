# Governance Scripts Package
#
# This package contains scripts for governance operations including:
# - sync_episodes.py: Synchronize governance episodes between repository and external store
# - validate_episodes.py: Validate governance episodes in both locations
# - backfill_episodes.py: Backfill missing governance episodes
#
# Created: 2026-11-06
# Version: 1.0.0
# Related: ADP-20261106-001, SPA-20261106-001, GC-002, LL-046

"""
Governance scripts for evidence management and synchronization.

This package operationalizes GC-002 from LL-046 (Evidence Management Synchronization).
It addresses the issue where gate evidence was split between the repository 
and an external store with no reconciliation mechanism.
"""

from . import sync_episodes
from . import validate_episodes
from . import backfill_episodes

__all__ = ['sync_episodes', 'validate_episodes', 'backfill_episodes']
__version__ = "1.0.0"
