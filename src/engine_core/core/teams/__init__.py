"""
Teams Module - Team Coordination System

This module contains the team coordination and hierarchy management.
"""

from .team_builder import (
    TeamBuilder, BuiltTeam, TeamExecutionContext, TeamTask, TeamMember,
    TeamCoordinationStrategy, TeamMemberRole, TeamExecutionMode, TeamState,
    CoordinationStrategy, HierarchicalStrategy, CollaborativeStrategy,
    ParallelStrategy, TeamExecutionEngine
)

__all__ = [
    "TeamBuilder",
    "BuiltTeam",
    "TeamExecutionContext",
    "TeamTask",
    "TeamMember",
    "TeamCoordinationStrategy",
    "TeamMemberRole",
    "TeamExecutionMode",
    "TeamState",
    "CoordinationStrategy",
    "HierarchicalStrategy",
    "CollaborativeStrategy",
    "ParallelStrategy",
    "TeamExecutionEngine",
]
