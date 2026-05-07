"""Simulator Backend for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
from typing import Dict, Any, List, Optional
from .circuit import Circuit

try:
    from .abirqu_core import Simulator as RustSimulator
    HAS_RUST_CORE = True
except ImportError:
    HAS_RUST_CORE = False

__all__ = ['SimulatorBackend', 'RustSimulator', '_serialize_circuit']

# Gate type constants (must match src/simulator.rs)
_GATE_MAP = {
    'H': 0, 'X': 1, 'Y': 2, 'Z': 3, 'S': 4, 'T': 5,
    'CNOT': 6, 'CX': 6, 'CZ': 7,
    'RX': 8, 'RY': 9, 'RZ': 10, 'SWAP': 11,
}


def _serialize_circuit(circuit: Circuit) -> list:
    """Convert a Circuit into the batch format: list of (gate_type, qubits, param)."""
    batch = []
    for gate in getattr(circuit, 'gates', []):
        gate_type = _GATE_MAP.get(gate.name.upper(), -1)
        if gate_type < 0:
            continue
        batch.append((gate_type, list(gate.qubits), float(gate.params[0]) if gate.params else 0.0))
    return batch


class SimulatorBackend:
    """Local quantum circuit simulation backend."""

    def __init__(self, use_gpu: bool = False, num_qubits: int = 1):
        self.name = "Simulator"
        self.use_gpu = use_gpu
        self.num_qubits = num_qubits
        self.rust_sim = None
        self.results = {}

    def run(self, circuit: Circuit, shots: int = 1024,
            noise_model=None) -> Dict[str, Any]:
        """Run circuit on local simulator."""
        n = circuit.num_qubits

        if HAS_RUST_CORE and not self.use_gpu:
            # Batch execution in Rust
            self.rust_sim = RustSimulator(n)
            self.rust_sim.run_circuit(_serialize_circuit(circuit))

            if shots == 0:
                # Statevector-only mode: skip ALL post-processing
                return {'success': True, 'backend': self.name, 'shots': 0,
                        'counts': {}, 'probabilities': None}

            # Get probabilities as raw bytes → numpy (avoids 2^n PyFloat boxing)
            # Get probabilities efficiently
            raw = self.rust_sim.get_probabilities_bytes()
            if isinstance(raw, (bytes, bytearray)):
                probs = np.frombuffer(raw, dtype=np.float64).copy()
            else:
                # pyo3 Vec<u8> may come as list — fall back to get_probabilities
                probs = np.array(self.rust_sim.get_probabilities(), dtype=np.float64)

            # Apply noise if provided
            if noise_model is not None:
                probs = noise_model.apply_to_probs_array(probs, n)

            # Normalize
            total = probs.sum()
            if total > 0:
                probs /= total

            # Sample shots directly from numpy array (NOT from dict)
            indices = np.random.choice(len(probs), size=shots, p=probs)
            unique_idx, raw_counts = np.unique(indices, return_counts=True)

            # Format ONLY the observed states (not all 2^n)
            counts = {format(int(u), f'0{n}b'): int(c) for u, c in zip(unique_idx, raw_counts)}

            # Map to classical bits if measurements exist
            if circuit.measurements:
                counts = self._map_to_classical(counts, circuit.measurements, n)

            return {
                'success': True,
                'backend': self.name,
                'shots': shots,
                'counts': counts,
            }
        else:
            # Fallback to Python QVM
            from .qvm import QuantumVirtualMachine
            qvm = QuantumVirtualMachine(n, use_gpu=self.use_gpu)
            for gate in getattr(circuit, 'gates', []):
                qvm.apply_gate(gate.matrix, gate.qubits)
            probs = qvm.get_probabilities()
            counts = self._sample_from_dict(probs, shots)
            return {'success': True, 'backend': self.name,
                    'shots': shots, 'counts': counts}

    def _sample_from_dict(self, probs, shots):
        """Fallback sampling from probability dict."""
        states = list(probs.keys())
        p = np.array(list(probs.values()), dtype=np.float64)
        p /= p.sum()
        idx = np.random.choice(len(states), size=shots, p=p)
        unique, counts = np.unique(idx, return_counts=True)
        return {states[u]: int(c) for u, c in zip(unique, counts)}

    def _map_to_classical(self, quantum_results, measurements, n):
        """Map quantum measurement results to classical register."""
        classical = {}
        creg_size = max((m.cbit if hasattr(m, 'cbit') else m['cbit']
                         for m in measurements), default=0) + 1
        for q_state, count in quantum_results.items():
            c_bits = ['0'] * creg_size
            for m in measurements:
                q = m.qubit if hasattr(m, 'qubit') else m['qubit']
                c = m.cbit if hasattr(m, 'cbit') else m['cbit']
                if q < len(q_state):
                    c_bits[c] = q_state[q]
            c_state = ''.join(c_bits)
            classical[c_state] = classical.get(c_state, 0) + count
        return classical

    def run_batch(self, circuits: List[Circuit], shots: int = 1024) -> List[Dict]:
        return [self.run(c, shots) for c in circuits]

    def get_available_qubits(self) -> int:
        return 32

    def estimate_runtime(self, circuit: Circuit) -> float:
        return 2**circuit.num_qubits * 1e-6
