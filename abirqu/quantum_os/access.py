"""
Access Control
==============
Role-based access control for quantum resources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class Permission(str, Enum):
    JOB_SUBMIT = "job:submit"
    JOB_READ = "job:read"
    JOB_CANCEL = "job:cancel"
    BACKEND_LIST = "backend:list"
    BACKEND_USE = "backend:use"
    RESERVATION_CREATE = "reservation:create"
    RESERVATION_READ = "reservation:read"
    RESERVATION_CANCEL = "reservation:cancel"
    TENANT_ADMIN = "tenant:admin"
    QUOTA_READ = "quota:read"
    COST_READ = "cost:read"


class Role(str, Enum):
    VIEWER = "viewer"
    USER = "user"
    POWER_USER = "power_user"
    ADMIN = "admin"


ROLE_PERMISSIONS = {
    Role.VIEWER: {Permission.JOB_READ, Permission.BACKEND_LIST, Permission.QUOTA_READ},
    Role.USER: {
        Permission.JOB_SUBMIT, Permission.JOB_READ, Permission.JOB_CANCEL,
        Permission.BACKEND_LIST, Permission.BACKEND_USE,
        Permission.RESERVATION_CREATE, Permission.RESERVATION_READ,
        Permission.QUOTA_READ, Permission.COST_READ,
    },
    Role.POWER_USER: {
        Permission.JOB_SUBMIT, Permission.JOB_READ, Permission.JOB_CANCEL,
        Permission.BACKEND_LIST, Permission.BACKEND_USE,
        Permission.RESERVATION_CREATE, Permission.RESERVATION_READ, Permission.RESERVATION_CANCEL,
        Permission.QUOTA_READ, Permission.COST_READ,
    },
    Role.ADMIN: {p for p in Permission},
}


@dataclass
class ACL:
    """Access control list entry."""
    resource: str  # e.g. "backend:ibm_brisbane", "tenant:abc123"
    permissions: Set[Permission] = field(default_factory=set)
    subject: str = ""  # user or role identifier


class AccessController:
    """Role-based access control for quantum resources.

    Parameters
    ----------
    default_role : Role
        Default role for unauthenticated users.
    """

    def __init__(self, default_role: Role = Role.VIEWER):
        self.default_role = default_role
        self._user_roles: Dict[str, Role] = {}
        self._acls: List[ACL] = []
        self._role_overrides: Dict[str, Set[Permission]] = {}

    def set_user_role(self, user_id: str, role: Role):
        """Set a user's role."""
        self._user_roles[user_id] = role

    def get_user_role(self, user_id: str) -> Role:
        return self._user_roles.get(user_id, self.default_role)

    def get_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user."""
        role = self.get_user_role(user_id)
        perms = set(ROLE_PERMISSIONS.get(role, set()))
        perms.update(self._role_overrides.get(user_id, set()))
        return perms

    def check(self, user_id: str, permission: Permission, resource: str = "*") -> bool:
        """Check if a user has a permission."""
        perms = self.get_permissions(user_id)
        if Permission.TENANT_ADMIN in perms:
            return True
        if permission in perms:
            return True

        # Check ACLs
        for acl in self._acls:
            if acl.subject == user_id and permission in acl.permissions:
                if acl.resource == "*" or acl.resource == resource:
                    return True
            if acl.subject == f"role:{self.get_user_role(user_id).value}":
                if permission in acl.permissions:
                    if acl.resource == "*" or acl.resource == resource:
                        return True

        return False

    def add_acl(self, subject: str, resource: str, permissions: List[Permission]):
        """Add an ACL entry."""
        self._acls.append(ACL(resource=resource, permissions=set(permissions), subject=subject))

    def override_permissions(self, user_id: str, permissions: List[Permission]):
        """Grant additional permissions to a user."""
        self._role_overrides.setdefault(user_id, set()).update(permissions)

    def list_user_permissions(self, user_id: str) -> List[str]:
        """List all permissions for a user."""
        return sorted(p.value for p in self.get_permissions(user_id))
