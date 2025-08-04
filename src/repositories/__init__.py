"""
Repositories package
"""
from .base_repository import BaseRepository
from .vulnerability_repository import VulnerabilityRepository

__all__ = [
    'BaseRepository',
    'VulnerabilityRepository'
]
