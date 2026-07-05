"""
RBAC
====
Role-based access control for the Quantum OS.

This is an *enhanced* RBAC layer that extends the existing ``access.py``
controller with a richer role hierarchy (SUPER_ADMIN, DEVELOPER) and a
fine-grained permission model aligned with audit-trail actions.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set


class Role(str, Enum):
    VIEWER = "viewer"
    RUNNER = "runner"
    DEVELOPER = "developer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Permission(str, Enum):
    READ_CIRCUIT = "circuit:read"
    RUN_CIRCUIT = "circuit:run"
    CREATE_CIRCUIT = "circuit:create"
    DELETE_CIRCUIT = "circuit:delete"
    MANAGE_USERS = "users:manage"
    VIEW_JOBS = "jobs:view"
    MANAGE_BACKENDS = "backends:manage"
    VIEW_AUDIT = "audit:view"


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.READ_CIRCUIT,
        Permission.VIEW_JOBS,
    },
    Role.RUNNER: {
        Permission.READ_CIRCUIT,
        Permission.RUN_CIRCUIT,
        Permission.VIEW_JOBS,
    },
    Role.DEVELOPER: {
        Permission.READ_CIRCUIT,
        Permission.RUN_CIRCUIT,
        Permission.CREATE_CIRCUIT,
        Permission.DELETE_CIRCUIT,
        Permission.VIEW_JOBS,
    },
    Role.ADMIN: {
        Permission.READ_CIRCUIT,
        Permission.RUN_CIRCUIT,
        Permission.CREATE_CIRCUIT,
        Permission.DELETE_CIRCUIT,
        Permission.MANAGE_USERS,
        Permission.VIEW_JOBS,
        Permission.MANAGE_BACKENDS,
        Permission.VIEW_AUDIT,
    },
    Role.SUPER_ADMIN: {p for p in Permission},
}


class RBACController:
    """Role-based access control for the Quantum OS.

    Parameters
    ----------
    default_role : Role
        Role assigned to users that have not been explicitly granted one.
    """

    def __init__(self, default_role: Role = Role.VIEWER):
        self.default_role = default_role
        self._user_roles: Dict[str, Role] = {}

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Return *True* if *user_id* holds *permission*."""
        return permission in self.get_user_permissions(user_id)

    def get_user_role(self, user_id: str) -> Role:
        return self._user_roles.get(user_id, self.default_role)

    def get_user_permissions(self, user_id: str) -> List[Permission]:
        role = self.get_user_role(user_id)
        return sorted(ROLE_PERMISSIONS.get(role, set()), key=lambda p: p.value)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def assign_role(self, user_id: str, role: Role) -> None:
        """Assign *role* to *user_id*."""
        self._user_roles[user_id] = role

    def revoke_role(self, user_id: str) -> None:
        """Revert *user_id* to the default role."""
        self._user_roles.pop(user_id, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def list_roles(self) -> List[Role]:
        return list(Role)

    def list_permissions_for_role(self, role: Role) -> List[Permission]:
        return sorted(ROLE_PERMISSIONS.get(role, set()), key=lambda p: p.value)
