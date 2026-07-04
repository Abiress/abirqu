"""
AbirQu Cloud Manager
Copyright 2026 Abir Maheshwari

Unified cloud provider management for quantum hardware access.
"""
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CloudProvider(Enum):
    IBM_QUANTUM = "ibm_quantum"
    AWS_BRAKET = "aws_braket"
    AZURE_QUANTUM = "azure_quantum"
    GOOGLE_QUANTUM = "google_quantum"
    IONQ = "ionq"
    RIGETTI = "rigetti"
    QUANTINUUM = "quantinuum"
    PASQAL = "pasqal"
    OQC = "oqc"
    QUERA = "quera"
    ABIRQU_LOCAL = "abirqu_local"


class ProviderStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CREDENTIALS_MISSING = "credentials_missing"


@dataclass
class CloudCredentials:
    """Cloud provider credentials."""
    provider: CloudProvider
    api_key: Optional[str] = None
    token: Optional[str] = None
    project_id: Optional[str] = None
    region: str = 'us-east-1'
    endpoint: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls, provider: CloudProvider) -> 'CloudCredentials':
        env_map = {
            CloudProvider.IBM_QUANTUM: {
                'api_key': ['IBM_QUANTUM_TOKEN', 'QX_TOKEN', 'IBM_QUANTUM_API_KEY'],
            },
            CloudProvider.AWS_BRAKET: {
                'api_key': ['AWS_ACCESS_KEY_ID'],
                'extra': {'secret_key': 'AWS_SECRET_ACCESS_KEY', 'region': 'AWS_DEFAULT_REGION'},
            },
            CloudProvider.AZURE_QUANTUM: {
                'token': ['AZURE_QUANTUM_TOKEN', 'AZURE_TENANT_ID'],
                'extra': {'subscription_id': 'AZURE_SUBSCRIPTION_ID', 'resource_group': 'AZURE_RESOURCE_GROUP'},
            },
            CloudProvider.GOOGLE_QUANTUM: {
                'token': ['GOOGLE_APPLICATION_CREDENTIALS'],
                'project_id': ['GOOGLE_CLOUD_PROJECT'],
            },
            CloudProvider.IONQ: {
                'api_key': ['IONQ_API_KEY'],
                'endpoint': ['IONQ_API_URL'],
            },
            CloudProvider.RIGETTI: {
                'token': ['RIGETTI_API_KEY', 'QCS_API_TOKEN'],
            },
            CloudProvider.QUANTINUUM: {
                'api_key': ['QUANTINUUM_API_KEY'],
            },
            CloudProvider.PASQAL: {
                'api_key': ['PASQAL_API_KEY'],
            },
            CloudProvider.OQC: {
                'api_key': ['OQC_API_KEY'],
            },
            CloudProvider.QUERA: {
                'api_key': ['QUERA_API_KEY'],
            },
        }

        config = env_map.get(provider, {})
        creds = cls(provider=provider)

        for field_name, env_names in config.items():
            if field_name == 'extra':
                for extra_key, env_name in env_names.items():
                    val = os.getenv(env_name)
                    if val:
                        creds.extra[extra_key] = val
            else:
                for env_name in env_names:
                    val = os.getenv(env_name)
                    if val:
                        setattr(creds, field_name, val)
                        break

        if provider == CloudProvider.AWS_BRAKET:
            creds.region = creds.extra.get('region', 'us-east-1')

        return creds

    @property
    def is_complete(self) -> bool:
        if self.provider in (CloudProvider.IBM_QUANTUM, CloudProvider.IONQ,
                             CloudProvider.QUANTINUUM, CloudProvider.PASQAL,
                             CloudProvider.OQC, CloudProvider.QUERA):
            return bool(self.api_key)
        if self.provider == CloudProvider.AWS_BRAKET:
            return bool(self.api_key and creds.extra.get('secret_key'))
        if self.provider == CloudProvider.AZURE_QUANTUM:
            return bool(self.token or self.api_key)
        if self.provider == CloudProvider.GOOGLE_QUANTUM:
            return bool(self.token or self.project_id)
        return bool(self.api_key or self.token)

    def to_dict(self) -> Dict:
        return {
            'provider': self.provider.value,
            'has_api_key': bool(self.api_key),
            'has_token': bool(self.token),
            'project_id': self.project_id,
            'region': self.region,
            'is_complete': self.is_complete if hasattr(self, 'api_key') else False,
        }


@dataclass
class ProviderConnection:
    """Connection state for a cloud provider."""
    provider: CloudProvider
    status: ProviderStatus = ProviderStatus.DISCONNECTED
    last_connected: Optional[float] = None
    error_message: Optional[str] = None
    available_backends: List[str] = field(default_factory=list)
    queue_depth: int = 0
    credits_remaining: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'provider': self.provider.value,
            'status': self.status.value,
            'last_connected': self.last_connected,
            'error_message': self.error_message,
            'num_backends': len(self.available_backends),
            'queue_depth': self.queue_depth,
            'credits_remaining': self.credits_remaining,
        }


class CloudManager:
    """Unified cloud provider management."""

    def __init__(self):
        self.credentials: Dict[CloudProvider, CloudCredentials] = {}
        self.connections: Dict[CloudProvider, ProviderConnection] = {}
        self._callbacks = []
        self._auto_discover_credentials()

    def _auto_discover_credentials(self):
        for provider in CloudProvider:
            if provider == CloudProvider.ABIRQU_LOCAL:
                continue
            creds = CloudCredentials.from_env(provider)
            if creds.api_key or creds.token:
                self.credentials[provider] = creds
                self.connections[provider] = ProviderConnection(provider=provider)

    def on(self, event: str, callback):
        self._callbacks.append((event, callback))

    def _emit(self, event: str, data: Any):
        for ev, cb in self._callbacks:
            if ev == event:
                try:
                    cb(data)
                except Exception:
                    pass

    def add_credentials(self, provider: CloudProvider, api_key: str = None,
                        token: str = None, **kwargs):
        creds = CloudCredentials(
            provider=provider, api_key=api_key, token=token,
            extra=kwargs,
        )
        self.credentials[provider] = creds
        self.connections[provider] = ProviderConnection(provider=provider)
        self._emit('credentials_added', {'provider': provider.value})

    def connect(self, provider: CloudProvider) -> bool:
        if provider not in self.credentials:
            self.connections[provider] = ProviderConnection(
                provider=provider, status=ProviderStatus.CREDENTIALS_MISSING,
                error_message='No credentials found',
            )
            return False

        conn = self.connections.get(provider, ProviderConnection(provider=provider))
        conn.status = ProviderStatus.CONNECTED
        conn.last_connected = time.time()
        self.connections[provider] = conn
        self._emit('connected', {'provider': provider.value})
        return True

    def disconnect(self, provider: CloudProvider):
        if provider in self.connections:
            self.connections[provider].status = ProviderStatus.DISCONNECTED
            self._emit('disconnected', {'provider': provider.value})

    def get_status(self, provider: CloudProvider) -> ProviderStatus:
        conn = self.connections.get(provider)
        return conn.status if conn else ProviderStatus.DISCONNECTED

    def get_connected_providers(self) -> List[CloudProvider]:
        return [p for p, c in self.connections.items()
                if c.status == ProviderStatus.CONNECTED]

    def get_provider_info(self, provider: CloudProvider) -> Dict:
        creds = self.credentials.get(provider)
        conn = self.connections.get(provider, ProviderConnection(provider=provider))
        return {
            'provider': provider.value,
            'has_credentials': creds is not None and creds.is_complete,
            'connection': conn.to_dict(),
        }

    def list_all_providers(self) -> List[Dict]:
        result = []
        for provider in CloudProvider:
            result.append(self.get_provider_info(provider))
        return result

    def get_render_data(self) -> Dict:
        providers = []
        for provider in CloudProvider:
            providers.append(self.get_provider_info(provider))
        return {
            'providers': providers,
            'connected': [p.value for p in self.get_connected_providers()],
            'total': len(providers),
        }

    def __repr__(self):
        connected = len(self.get_connected_providers())
        return f"CloudManager(connected={connected}, providers={len(CloudProvider)})"
