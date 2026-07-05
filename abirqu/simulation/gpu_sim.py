"""
GPU-Accelerated Quantum Simulator
=================================
CuPy-backed statevector simulation for large circuits.
Falls back to NumPy when CuPy is unavailable.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    cp = None
    CUPY_AVAILABLE = False

import numpy as np

from ..circuit import Circuit, Gate


def gpu_available() -> bool:
    """Check if CuPy GPU is available."""
    if not CUPY_AVAILABLE:
        return False
    try:
        cp.cuda.Device(0).compute_capability()
        return True
    except Exception:
        return False


class GPUSimulator:
    """GPU-accelerated statevector simulator.

    Automatically uses CuPy when available, falls back to NumPy.

    Parameters
    ----------
    n_qubits : int
        Number of qubits.
    use_gpu : bool
        Force GPU usage. If False, uses NumPy.
    """

    def __init__(self, n_qubits: int = 1, use_gpu: Optional[bool] = None):
        self.n_qubits = n_qubits
        self.n_states = 2 ** n_qubits
        self._use_gpu = use_gpu if use_gpu is not None else gpu_available()
        self._xp = cp if self._use_gpu else np
        self._statevector = self._init_state()
        self.name = "gpu_simulator" if self._use_gpu else "numpy_simulator"

    def _init_state(self):
        """Initialize |00...0> state."""
        sv = self._xp.zeros(self.n_states, dtype=complex)
        sv[0] = 1.0
        return sv

    def _get_gate_matrix(self, gate: Gate) -> np.ndarray:
        """Get unitary matrix for a gate."""
        name = gate.name.upper()
        params = gate.params or []

        if name == "H":
            return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        elif name == "X":
            return np.array([[0, 1], [1, 0]], dtype=complex)
        elif name == "Y":
            return np.array([[0, -1j], [1j, 0]], dtype=complex)
        elif name == "Z":
            return np.array([[1, 0], [0, -1]], dtype=complex)
        elif name == "S":
            return np.array([[1, 0], [0, 1j]], dtype=complex)
        elif name == "S_DAG":
            return np.array([[1, 0], [0, -1j]], dtype=complex)
        elif name == "T":
            return np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
        elif name == "T_DAG":
            return np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex)
        elif name == "RX":
            theta = params[0] if params else 0
            return np.array([
                [np.cos(theta / 2), -1j * np.sin(theta / 2)],
                [-1j * np.sin(theta / 2), np.cos(theta / 2)]
            ], dtype=complex)
        elif name == "RY":
            theta = params[0] if params else 0
            return np.array([
                [np.cos(theta / 2), -np.sin(theta / 2)],
                [np.sin(theta / 2), np.cos(theta / 2)]
            ], dtype=complex)
        elif name == "RZ":
            theta = params[0] if params else 0
            return np.array([
                [np.exp(-1j * theta / 2), 0],
                [0, np.exp(1j * theta / 2)]
            ], dtype=complex)
        elif name in ("CNOT", "CX"):
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ], dtype=complex)
        elif name == "CZ":
            return np.diag([1, 1, 1, -1]).astype(complex)
        elif name == "SWAP":
            return np.array([
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ], dtype=complex)
        elif name == "TOFFOLI":
            mat = np.eye(8, dtype=complex)
            # Toffoli swaps |011> (index 3) and |111> (index 7)
            mat[3, 3] = 0
            mat[7, 7] = 0
            mat[3, 7] = 1
            mat[7, 3] = 1
            return mat
        else:
            return np.eye(2, dtype=complex)

    def apply_gate(self, gate: Gate):
        """Apply a gate to the statevector."""
        qubits = gate.qubits
        matrix = self._get_gate_matrix(gate)
        n_qubits_involved = len(qubits)

        if n_qubits_involved == 1:
            self._apply_single_qubit_gate(qubits[0], matrix)
        elif n_qubits_involved == 2:
            self._apply_two_qubit_gate(qubits[0], qubits[1], matrix)
        elif n_qubits_involved == 3:
            self._apply_three_qubit_gate(qubits, matrix)

    def _apply_single_qubit_gate(self, qubit: int, matrix: np.ndarray):
        """Apply single-qubit gate using tensor contraction."""
        xp = self._xp
        m = self._xp.asarray(matrix)
        sv = self._statevector.reshape([2] * self.n_qubits)

        # Contract axis qubit with matrix
        result = xp.tensordot(m, sv, axes=([1], [qubit]))
        # Move result axis to correct position
        result = xp.moveaxis(result, 0, qubit)
        self._statevector = result.reshape(self.n_states)

    def _apply_two_qubit_gate(self, q0: int, q1: int, matrix: np.ndarray):
        """Apply two-qubit gate.

        Works for any qubit positions by contracting the gate
        with the two target qubit indices.
        """
        xp = self._xp
        m = self._xp.asarray(matrix).reshape(2, 2, 2, 2)
        sv = self._statevector.reshape([2] * self.n_qubits)

        # Build output indices: same as input but q0,q1 replaced by new indices
        # Contract m[a,b,c,d] with sv[..., qa, ..., qb, ...]
        # over axes a->qa, b->qb
        in_indices = list(range(self.n_qubits))
        out_indices = list(range(self.n_qubits))

        # Use einsum string approach
        n = self.n_qubits
        letters = [chr(ord('a') + i) for i in range(n)]
        gate_letters = ['G0', 'G1', 'G2', 'G3']

        input_str = "".join(letters)
        gate_str = "".join(gate_letters)
        output_str = input_str

        # Build the einsum equation
        # m[G2, G0, G3, G1] sv[letters] -> result[letters]
        # where G0,q0 and G1,q1 are contracted
        eq = f"{gate_str},{input_str}->{output_str}"
        # But we need to specify which indices contract...
        # Simpler: use explicit index notation

        # Actually, let's use a direct approach
        # Permute q0, q1 to the front
        perm = [q0, q1] + [i for i in range(n) if i != q0 and i != q1]
        inv_perm = [0] * n
        for i, p in enumerate(perm):
            inv_perm[p] = i

        sv_perm = xp.transpose(sv, perm)
        # Now first two indices are q0, q1
        shape_rest = sv_perm.shape[2:]
        sv_2d = sv_perm.reshape(4, -1)

        # Apply gate
        gate_matrix = m.reshape(4, 4)
        result_2d = gate_matrix @ sv_2d

        # Permute back
        result = result_2d.reshape(2, 2, *shape_rest)
        result = xp.transpose(result, inv_perm)
        self._statevector = result.reshape(self.n_states)

        self._statevector = result.reshape(self.n_states)

    def _apply_three_qubit_gate(self, qubits: tuple, matrix: np.ndarray):
        """Apply three-qubit gate (Toffoli, Fredkin) using tensor contraction."""
        q0, q1, q2 = qubits
        n = self.n_qubits
        
        # Build the full 8x8 matrix for the 3-qubit subsystem
        # Then apply it using index manipulation
        new_state = self._xp.zeros_like(self._statevector)
        
        for i in range(2**n):
            # Extract bits for the 3 qubits
            b0 = (i >> q0) & 1
            b1 = (i >> q1) & 1
            b2 = (i >> q2) & 1
            
            # Compute the 3-bit index
            idx3 = b0 + 2*b1 + 4*b2
            
            # Apply the 8x8 matrix to get new 3-bit index
            new_idx3 = 0
            for j in range(8):
                if abs(matrix[j, idx3]) > 1e-10:
                    new_idx3 = j
                    break
            
            # Extract new bits
            new_b0 = new_idx3 & 1
            new_b1 = (new_idx3 >> 1) & 1
            new_b2 = (new_idx3 >> 2) & 1
            
            # Compute new full index
            new_i = i
            # Clear old bits
            new_i &= ~(1 << q0)
            new_i &= ~(1 << q1)
            new_i &= ~(1 << q2)
            # Set new bits
            new_i |= (new_b0 << q0)
            new_i |= (new_b1 << q1)
            new_i |= (new_b2 << q2)
            
            new_state[new_i] += self._statevector[i]
        
        self._statevector = new_state

    def run_circuit(self, circuit: Circuit, shots: int = 1000) -> Dict[str, Any]:
        """Execute a circuit and return measurement results."""
        # Apply all gates
        for gate in circuit.gates:
            self.apply_gate(gate)

        # Compute probabilities
        probs = self._xp.abs(self._statevector) ** 2
        if self._use_gpu:
            probs = cp.asnumpy(probs)

        # Sample
        counts = {}
        indices = np.random.choice(self.n_states, size=shots, p=probs)
        for idx in indices:
            bitstring = format(idx, f"0{self.n_qubits}b")
            counts[bitstring] = counts.get(bitstring, 0) + 1

        return {
            "counts": counts,
            "shots": shots,
            "num_qubits": self.n_qubits,
            "backend": self.name,
            "success": True,
        }

    def get_statevector(self) -> np.ndarray:
        """Get the current statevector."""
        if self._use_gpu:
            return cp.asnumpy(self._statevector)
        return self._statevector.copy()

    def get_probabilities(self) -> Dict[str, float]:
        """Get probabilities for all states."""
        probs = self._xp.abs(self._statevector) ** 2
        if self._use_gpu:
            probs = cp.asnumpy(probs)
        return {
            format(i, f"0{self.n_qubits}b"): float(p)
            for i, p in enumerate(probs) if p > 1e-10
        }
