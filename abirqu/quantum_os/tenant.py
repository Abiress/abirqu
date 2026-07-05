"""
Tenant Manager
==============
Multi-tenant isolation for quantum computing resources.
"""

from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .environment import ResourceQuota, VirtualEnvironment


class TenantTier(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


TIER_QUOTAS = {
    TenantTier.FREE: ResourceQuota(
        max_jobs_per_hour=10,
        max_shots_per_day=10_000,
        max_concurrent_jobs=2,
        allowed_backends=["fast", "local"],
        max_circuit_qubits=20,
        max_circuit_gates=1000,
    ),
    TenantTier.STANDARD: ResourceQuota(
        max_jobs_per_hour=50,
        max_shots_per_day=100_000,
        max_concurrent_jobs=5,
        allowed_backends=["fast", "local", "ibmq_qasm_simulator"],
        max_circuit_qubits=50,
        max_circuit_gates=5000,
    ),
    TenantTier.PREMIUM: ResourceQuota(
        max_jobs_per_hour=200,
        max_shots_per_day=1_000_000,
        max_concurrent_jobs=20,
        allowed_backends=["fast", "local", "ibm_brisbane", "ibm_osaka", "dwave_simulated"],
        max_circuit_qubits=100,
        max_circuit_gates=10000,
    ),
    TenantTier.ENTERPRISE: ResourceQuota(
        max_jobs_per_hour=1000,
        max_shots_per_day=10_000_000,
        max_concurrent_jobs=100,
        allowed_backends=["*"],
        max_circuit_qubits=1000,
        max_circuit_gates=100000,
    ),
}


@dataclass
class Tenant:
    """A tenant in the system."""
    tenant_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    tier: TenantTier = TenantTier.FREE
    quotas: ResourceQuota = field(default_factory=ResourceQuota)
    environments: List[str] = field(default_factory=list)
    api_key: str = field(default_factory=lambda: secrets.token_hex(32))
    created_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> Dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "tier": self.tier.value,
            "environments": self.environments,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


class TenantManager:
    """Manage multi-tenant isolation.

    Parameters
    ----------
    default_tier : TenantTier
        Tier for new tenants.
    """

    def __init__(self, default_tier: TenantTier = TenantTier.FREE):
        self.default_tier = default_tier
        self._tenants: Dict[str, Tenant] = {}
        self._api_keys: Dict[str, str] = {}  # api_key -> tenant_id
        self._init_default()

    def _init_default(self):
        default = Tenant(
            tenant_id="default",
            name="Default",
            tier=TenantTier.ENTERPRISE,
            quotas=TIER_QUOTAS[TenantTier.ENTERPRISE],
        )
        self._tenants["default"] = default
        self._api_keys[default.api_key] = "default"

    def create_tenant(
        self,
        name: str,
        tier: Optional[TenantTier] = None,
        quotas: Optional[ResourceQuota] = None,
        **metadata,
    ) -> Tenant:
        """Create a new tenant."""
        tier = tier or self.default_tier
        tenant = Tenant(
            name=name,
            tier=tier,
            quotas=quotas or TIER_QUOTAS[tier],
            metadata=metadata,
        )
        self._tenants[tenant.tenant_id] = tenant
        self._api_keys[tenant.api_key] = tenant.tenant_id
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def authenticate(self, api_key: str) -> Optional[Tenant]:
        """Authenticate by API key."""
        tid = self._api_keys.get(api_key)
        if tid:
            tenant = self._tenants.get(tid)
            if tenant and tenant.enabled:
                return tenant
        return None

    def update_tier(self, tenant_id: str, tier: TenantTier) -> bool:
        """Update a tenant's tier."""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.tier = tier
            tenant.quotas = TIER_QUOTAS[tier]
            return True
        return False

    def disable_tenant(self, tenant_id: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.enabled = False
            return True
        return False

    def list_tenants(self) -> List[Dict]:
        return [t.to_dict() for t in self._tenants.values()]
