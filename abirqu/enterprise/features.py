"""
Phase 25: Enterprise Features.

Enterprise-grade features: multi-tenant, audit logs, SSO, quotas, billing.
Supports 20+ qubit simulations with full enterprise integration.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class TenantStatus(Enum):
    """Status of a tenant."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class SubscriptionTier(Enum):
    """Subscription tiers."""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"


@dataclass
class Tenant:
    """A multi-tenant tenant."""
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.PENDING
    subscription: SubscriptionTier = SubscriptionTier.FREE
    quotas: Dict[str, int] = field(default_factory=dict)
    users: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'name': self.name,
            'status': self.status.value,
            'subscription': self.subscription.value,
            'quotas': self.quotas,
            'user_count': len(self.users),
            'created_at': self.created_at
        }
    
    def add_user(self, user_id: str):
        """Add a user to tenant."""
        if user_id not in self.users:
            self.users.append(user_id)
    
    def remove_user(self, user_id: str):
        """Remove a user from tenant."""
        if user_id in self.users:
            self.users.remove(user_id)
    
    def check_quota(self, resource: str, requested: int) -> Tuple[bool, int]:
        """
        Check if quota allows resource usage.
        Returns: (allowed, remaining).
        """
        if self.subscription == SubscriptionTier.UNLIMITED:
            return True, 999999
        
        current_usage = self.metadata.get(f"{resource}_usage', 0)
        quota = self.quotas.get(resource, 0)
        
        remaining = quota - current_usage
        allowed = (current_usage + requested) <= quota
        
        return allowed, max(0, remaining)
    
    def update_usage(self, resource: str, delta: int):
        """Update resource usage."""
        key = f"{resource}_usage'
        self.metadata[key] = self.metadata.get(key, 0) + delta


@dataclass
class AuditLogEntry:
    """An audit log entry."""
    entry_id: str
    tenant_id: str
    user_id: str
    action: str
    resource: str
    timestamp: float = field(default_factory=time.time)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entry_id': self.entry_id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'action': self.action,
            'resource': self.resource,
            'timestamp': self.timestamp,
            'ip_address': self.ip_address,
            'metadata': self.metadata
        }


@dataclass
class BillingRecord:
    """A billing record."""
    record_id: str
    tenant_id: str
    amount: float
    currency: str = "USD"
    description: str = ""
    timestamp: float = field(default_factory=time.time)
    paid: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'tenant_id': self.tenant_id,
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
            'timestamp': self.timestamp,
            'paid': self.paid
        }


class AuditLogger:
    """Enterprise audit logging."""
    
    def __init__(self):
        self.logs: List[AuditLogEntry] = []
        self.handlers: List[Callable] = []
        self.log_counter = 0
    
    def log(self, tenant_id: str, user_id: str,
             action: str, resource: str,
             ip_address: Optional[str] = None,
             metadata: Optional[Dict[str, Any]] = None) -> AuditLogEntry:
        """Log an audit event."""
        self.log_counter += 1
        entry = AuditLogEntry(
            entry_id=f"log_{self.log_counter}",
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        self.logs.append(entry)
        
        # Call handlers.
        for handler in self.handlers:
            try:
                handler(entry)
            except Exception:
                pass
        
        return entry
    
    def query(self, tenant_id: Optional[str] = None,
                user_id: Optional[str] = None,
                action: Optional[str] = None,
                start_time: Optional[float] = None,
                end_time: Optional[float] = None) -> List[AuditLogEntry]:
        """Query audit logs."""
        results = []
        
        for entry in self.logs:
            if tenant_id and entry.tenant_id != tenant_id:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if action and entry.action != action:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            results.append(entry)
        
        return results
    
    def register_handler(self, handler: Callable):
        """Register an audit log handler."""
        self.handlers.append(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        if not self.logs:
            return {'total_entries': 0}
        
        by_tenant = {}
        by_action = {}
        
        for entry in self.logs:
            by_tenant[entry.tenant_id] = by_tenant.get(entry.tenant_id, 0) + 1
            by_action[entry.action] = by_action.get(entry.action, 0) + 1
        
        return {
            'total_entries': len(self.logs),
            'by_tenant': by_tenant,
            'by_action': by_action,
            'time_range': {
                'start': min(e.timestamp for e in self.logs),
                'end': max(e.timestamp for e in self.logs)
            }
        }


class BillingManager:
    """Enterprise billing management."""
    
    def __init__(self):
        self.records: List[BillingRecord] = []
        self.rate_card: Dict[str, float] = {
            'qubit_hour': 0.10,  # $0.10 per qubit-hour.
            'storage_GB': 0.05,  # $0.05 per GB.
            'api_call': 0.001  # $0.001 per API call.
        }
        self.record_counter = 0
    
    def create_charge(self, tenant_id: str,
                       amount: float,
                       description: str = "") -> BillingRecord:
        """Create a billing record."""
        self.record_counter += 1
        record = BillingRecord(
            record_id=f"bill_{self.record_counter}",
            tenant_id=tenant_id,
            amount=amount,
            description=description
        )
        
        self.records.append(record)
        return record
    
    def calculate_usage_charge(self, tenant_id: str,
                                num_qubits: int,
                                hours: float) -> BillingRecord:
        """Calculate charge for qubit usage."""
        rate = self.rate_card['qubit_hour']
        amount = num_qubits * hours * rate
        
        return self.create_charge(
            tenant_id=tenant_id,
            amount=amount,
            description=f"{num_qubits} qubits for {hours} hours"
        )
    
    def get_tenant_bill(self, tenant_id: str,
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None) -> Dict[str, Any]:
        """Get billing summary for a tenant."""
        total = 0.0
        records = []
        
        for record in self.records:
            if record.tenant_id != tenant_id:
                continue
            if start_time and record.timestamp < start_time:
                continue
            if end_time and record.timestamp > end_time:
                continue
            
            total += record.amount
            records.append(record.to_dict())
        
        return {
            'tenant_id': tenant_id,
            'total_amount': total,
            'record_count': len(records),
            'records': records
        }
    
    def mark_paid(self, record_id: str) -> bool:
        """Mark a billing record as paid."""
        for record in self.records:
            if record.record_id == record_id:
                record.paid = True
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get billing statistics."""
        total_revenue = sum(r.amount for r in self.records if r.paid)
        outstanding = sum(r.amount for r in self.records if not r.paid)
        
        return {
            'total_records': len(self.records),
            'total_revenue': total_revenue,
            'outstanding': outstanding,
            'paid_count': sum(1 for r in self.records if r.paid),
            'unpaid_count': sum(1 for r in self.records if not r.paid)
        }


class SSOManager:
    """Single Sign-On management."""
    
    def __init__(self):
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def register_provider(self, name: str,
                          config: Dict[str, Any]) -> bool:
        """Register an SSO provider (SAML, OIDC, etc.)."""
        self.providers[name] = {
            'config': config,
            'registered_at': time.time()
        }
        return True
    
    def authenticate(self, provider: str,
                       credentials: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Authenticate via SSO provider.
        Returns: (success, user_id).
        """
        if provider not in self.providers:
            return False, "Provider not registered"
        
        # Simplified: simulate authentication.
        if credentials.get('token') or credentials.get('assertion'):
            user_id = credentials.get('user_id', 'unknown')
            
            # Create session.
            session_id = f"session_{int(time.time())}"
            self.sessions[session_id] = {
                'user_id': user_id,
                'provider': provider,
                'created_at': time.time()
            }
            
            return True, session_id
        else:
            return False, "Invalid credentials"
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """Validate an SSO session."""
        if session_id not in self.sessions:
            return False, None
        
        session = self.sessions[session_id]
        
        # Check if expired (24 hours).
        if time.time() - session['created_at'] > 86400:
            del self.sessions[session_id]
            return False, None
        
        return True, session['user_id']
    
    def logout(self, session_id: str) -> bool:
        """Logout SSO session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


class EnterpriseManager:
    """Main enterprise feature manager."""
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.audit_logger = AuditLogger()
        self.billing = BillingManager()
        self.sso = SSOManager()
        self.tenant_counter = 0
    
    def create_tenant(self, name: str,
                       subscription: SubscriptionTier = SubscriptionTier.FREE) -> Tenant:
        """Create a new tenant."""
        self.tenant_counter += 1
        tenant_id = f"tenant_{self.tenant_counter}"
        
        # Set default quotas based on subscription.
        quotas = self._get_default_quotas(subscription)
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            subscription=subscription,
            quotas=quotas
        )
        
        self.tenants[tenant_id] = tenant
        
        # Audit log.
        self.audit_logger.log(
            tenant_id=tenant_id,
            user_id="system",
            action="tenant_created",
            resource="tenant",
            metadata={'name': name, 'subscription': subscription.value}
        )
        
        return tenant
    
    def _get_default_quotas(self, subscription: SubscriptionTier) -> Dict[str, int]:
        """Get default quotas for subscription tier."""
        if subscription == SubscriptionTier.FREE:
            return {
                'qubits': 5,
                'circuits_per_day': 10,
                'storage_GB': 1
            }
        elif subscription == SubscriptionTier.BASIC:
            return {
                'qubits': 10,
                'circuits_per_day': 100,
                'storage_GB': 10
            }
        elif subscription == SubscriptionTier.PROFESSIONAL:
            return {
                'qubits': 20,
                'circuits_per_day': 1000,
                'storage_GB': 100
            }
        elif subscription == SubscriptionTier.ENTERPRISE:
            return {
                'qubits': 50,
                'circuits_per_day': 10000,
                'storage_GB': 1000
            }
        else:  # UNLIMITED.
            return {
                'qubits': 999999,
                'circuits_per_day': 999999,
                'storage_GB': 999999
            }
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)
    
    def update_subscription(self, tenant_id: str,
                              subscription: SubscriptionTier) -> bool:
        """Update tenant subscription."""
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        old_sub = tenant.subscription
        tenant.subscription = subscription
        tenant.quotas = self._get_default_quotas(subscription)
        
        # Audit log.
        self.audit_logger.log(
            tenant_id=tenant_id,
            user_id="system",
            action="subscription_changed",
            resource="tenant",
            metadata={'old': old_sub.value, 'new': subscription.value}
        )
        
        return True
    
    def check_resource_access(self, tenant_id: str,
                              resource: str,
                              requested: int = 1) -> Tuple[bool, str]:
        """
        Check if tenant can access resource.
        Returns: (allowed, reason).
        """
        if tenant_id not in self.tenants:
            return False, "Tenant not found"
        
        tenant = self.tenants[tenant_id]
        
        # Check status.
        if tenant.status != TenantStatus.ACTIVE:
            return False, f"Tenant is {tenant.status.value}"
        
        # Check quota.
        allowed, remaining = tenant.check_quota(resource, requested)
        if not allowed:
            return False, f"Quota exceeded. Remaining: {remaining}"
        
        return True, "Allowed"
    
    def record_usage(self, tenant_id: str,
                      resource: str,
                      amount: int = 1) -> bool:
        """Record resource usage."""
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        tenant.update_usage(resource, amount)
        
        # Create billing record.
        if resource == 'qubits':
            self.billing.calculate_usage_charge(tenant_id, amount, 1.0)  # 1 hour.
        
        return True
    
    def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """Suspend a tenant."""
        if tenant_id not in self.tenants:
            return False
        
        self.tenants[tenant_id].status = TenantStatus.SUSPENDED
        
        self.audit_logger.log(
            tenant_id=tenant_id,
            user_id="system",
            action="tenant_suspended",
            resource="tenant",
            metadata={'reason': reason}
        )
        
        return True
    
    def list_tenants(self, status: Optional[TenantStatus] = None) -> List[Dict[str, Any]]:
        """List tenants with optional filtering."""
        results = []
        for tenant in self.tenants.values():
            if status and tenant.status != status:
                continue
            results.append(tenant.to_dict())
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get enterprise statistics."""
        tenant_stats = {
            'total': len(self.tenants),
            'by_status': {},
            'by_subscription': {}
        }
        
        for tenant in self.tenants.values():
            status = tenant.status.value
            tenant_stats['by_status'][status] = \
                tenant_stats['by_status'].get(status, 0) + 1
            
            sub = tenant.subscription.value
            tenant_stats['by_subscription'][sub] = \
                tenant_stats['by_subscription'].get(sub, 0) + 1
        
        # Merge with other stats.
        audit_stats = self.audit_logger.get_stats()
        billing_stats = self.billing.get_stats()
        
        return {
            'tenants': tenant_stats,
            'audit': audit_stats,
            'billing': billing_stats,
            'sso_providers': len(self.sso.providers)
        }
