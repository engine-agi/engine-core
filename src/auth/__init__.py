"""
Authentication and Authorization Module.

This module provides authentication and authorization services for the Engine Framework,
including user management, token validation, and access control.
"""

from .auth_service import get_current_user

__all__ = ["get_current_user"]