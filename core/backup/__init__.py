"""
NHI Backup Module

Provides backup management with dependency resolution for NHI-CORE.
"""

from .dependency_resolver import DependencyResolver
from .backup_manager import BackupManager

__all__ = ['DependencyResolver', 'BackupManager']
