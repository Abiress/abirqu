"""
AbirQu Hardware Panel
Copyright 2026 Abir Maheshwari

Hardware management and selection panel.
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class HardwareBackend:
    """Represents a quantum hardware backend."""
    backend_id: str
    name: str
    backend_type: str  # 'simulator', 'real', 'cloud'
    num_qubits: int
    provider: str
    status: str = 'online'  # 'online', 'offline', 'maintenance'
    max_shots: int = 100000
    gates: List[str] = field(default_factory=list)
    connectivity: str = 'all-to-all'  # 'all-to-all', 'linear', 'grid'
    noise_model: Optional[str] = None
    queue_depth: int = 0
    avg_runtime: float = 0.0
    fidelity: float = 1.0
    error_rate: float = 0.0
    supports_qiskit: bool = False
    supports_cirq: bool = False
    supports_pennylane: bool = False
    supports_abirqu: bool = True

    def to_dict(self) -> Dict:
        return {
            'backend_id': self.backend_id,
            'name': self.name,
            'type': self.backend_type,
            'num_qubits': self.num_qubits,
            'provider': self.provider,
            'status': self.status,
            'max_shots': self.max_shots,
            'gates': self.gates,
            'connectivity': self.connectivity,
            'noise_model': self.noise_model,
            'queue_depth': self.queue_depth,
            'avg_runtime': self.avg_runtime,
            'fidelity': self.fidelity,
            'error_rate': self.error_rate,
            'supports_qiskit': self.supports_qiskit,
            'supports_cirq': self.supports_cirq,
            'supports_pennylane': self.supports_pennylane,
            'supports_abirqu': self.supports_abirqu,
        }


class HardwarePanel:
    """Hardware management panel for selecting and monitoring backends."""

    def __init__(self):
        self.backends: Dict[str, HardwareBackend] = {}
        self.selected_backend: Optional[str] = None
        self._callbacks = []
        self._register_default_backends()

    def _register_default_backends(self):
        default_backends = [
            HardwareBackend(
                backend_id='abirqu_simulator',
                name='AbirQu Statevector Simulator',
                backend_type='simulator',
                num_qubits=30,
                provider='AbirQu',
                gates=['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'T', 'S', 'Sdg', 'Tdg',
                       'Rx', 'Ry', 'Rz', 'SWAP', 'Toffoli', 'Measure'],
                connectivity='all-to-all',
                noise_model=None,
                fidelity=1.0,
                error_rate=0.0,
            ),
            HardwareBackend(
                backend_id='abirqu_density_matrix',
                name='AbirQu Density Matrix Simulator',
                backend_type='simulator',
                num_qubits=20,
                provider='AbirQu',
                gates=['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'T', 'S', 'Rx', 'Ry', 'Rz',
                       'SWAP', 'Toffoli', 'Measure'],
                connectivity='all-to-all',
                noise_model='configurable',
                fidelity=1.0,
                error_rate=0.0,
            ),
            HardwareBackend(
                backend_id='abirqu_mps',
                name='AbirQu MPS Simulator',
                backend_type='simulator',
                num_qubits=50,
                provider='AbirQu',
                gates=['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'T', 'S', 'Rx', 'Ry', 'Rz',
                       'SWAP', 'Measure'],
                connectivity='all-to-all',
                noise_model=None,
                fidelity=1.0,
                error_rate=0.0,
            ),
            HardwareBackend(
                backend_id='abirqu_clifford',
                name='AbirQu Clifford Simulator',
                backend_type='simulator',
                num_qubits=1000,
                provider='AbirQu',
                gates=['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'S', 'Sdg'],
                connectivity='all-to-all',
                noise_model=None,
                fidelity=1.0,
                error_rate=0.0,
            ),
            HardwareBackend(
                backend_id='abirqu_gpu',
                name='AbirQu GPU Simulator',
                backend_type='simulator',
                num_qubits=40,
                provider='AbirQu',
                gates=['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'T', 'S', 'Rx', 'Ry', 'Rz',
                       'SWAP', 'Toffoli', 'Measure'],
                connectivity='all-to-all',
                noise_model=None,
                fidelity=1.0,
                error_rate=0.0,
            ),
        ]
        for b in default_backends:
            self.backends[b.backend_id] = b

    def on(self, event: str, callback):
        self._callbacks.append((event, callback))

    def _emit(self, event: str, data: Any):
        for ev, cb in self._callbacks:
            if ev == event:
                try:
                    cb(data)
                except Exception:
                    pass

    def add_backend(self, backend: HardwareBackend):
        self.backends[backend.backend_id] = backend
        self._emit('backend_added', backend.to_dict())

    def remove_backend(self, backend_id: str):
        if backend_id in self.backends:
            del self.backends[backend_id]
            if self.selected_backend == backend_id:
                self.selected_backend = None
            self._emit('backend_removed', backend_id)

    def select_backend(self, backend_id: str) -> bool:
        if backend_id in self.backends:
            self.selected_backend = backend_id
            self._emit('backend_selected', self.backends[backend_id].to_dict())
            return True
        return False

    def get_selected(self) -> Optional[HardwareBackend]:
        if self.selected_backend:
            return self.backends.get(self.selected_backend)
        return None

    def get_all_backends(self) -> List[HardwareBackend]:
        return list(self.backends.values())

    def get_backends_by_type(self, backend_type: str) -> List[HardwareBackend]:
        return [b for b in self.backends.values() if b.backend_type == backend_type]

    def get_backends_by_provider(self, provider: str) -> List[HardwareBackend]:
        return [b for b in self.backends.values() if b.provider == provider]

    def get_compatible_backends(self, num_qubits: int,
                                required_gates: List[str]) -> List[HardwareBackend]:
        compatible = []
        for b in self.backends.values():
            if b.num_qubits >= num_qubits:
                if all(g in b.gates for g in required_gates):
                    compatible.append(b)
        return compatible

    def get_render_data(self) -> Dict:
        backends = []
        for b in self.backends.values():
            backends.append({
                **b.to_dict(),
                'is_selected': b.backend_id == self.selected_backend,
            })

        providers = {}
        for b in self.backends.values():
            if b.provider not in providers:
                providers[b.provider] = []
            providers[b.provider].append(b.backend_id)

        return {
            'backends': backends,
            'providers': providers,
            'selected': self.selected_backend,
            'total': len(self.backends),
        }

    def get_stats(self) -> Dict:
        types = {}
        providers = {}
        for b in self.backends.values():
            types[b.backend_type] = types.get(b.backend_type, 0) + 1
            providers[b.provider] = providers.get(b.provider, 0) + 1
        return {
            'total': len(self.backends),
            'by_type': types,
            'by_provider': providers,
            'selected': self.selected_backend,
        }

    def __repr__(self):
        return f"HardwarePanel(backends={len(self.backends)}, selected={self.selected_backend})"
