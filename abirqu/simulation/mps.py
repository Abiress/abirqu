"""
Matrix Product State (MPS) Simulator
=====================================
Approximate quantum simulation using tensor trains.

MPS simulation is efficient for circuits with limited entanglement,
scaling as O(n * χ^2 * d) where χ is the bond dimension and d is
the local dimension.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from ..circuit import Circuit, Gate


def estimate_bond_dimension(num_qubits: int, entanglement_level: float = 0.5) -> int:
    """Heuristic MPS bond dimension estimator."""
    return max(2, int((2 ** (num_qubits / 4)) * max(0.1, entanglement_level)))


class MPSTensor:
    """A single tensor in the MPS."""

    def __init__(self, data: np.ndarray):
        self.data = data  # shape: (bond_left, phys, bond_right)

    @property
    def shape(self):
        return self.data.shape

    def contract_with_gate(self, gate: np.ndarray, qubit: int) -> 'MPSTensor':
        """Contract this tensor with a gate on the physical index."""
        # gate shape: (phys_out, phys_in)
        result = np.einsum("ijk,lj->ilk", self.data, gate)
        return MPSTensor(result)


class MatrixProductState:
    """Matrix Product State representation of a quantum state.

    Parameters
    ----------
    n_qubits : int
        Number of qubits.
    max_bond : int
        Maximum bond dimension.
    cutoff : float
        Singular value cutoff for truncation.
    """

    def __init__(
        self,
        n_qubits: int,
        max_bond: int = 32,
        cutoff: float = 1e-10,
    ):
        self.n_qubits = n_qubits
        self.max_bond = max_bond
        self.cutoff = cutoff
        self.tensors: List[np.ndarray] = []
        self._init_product_state()

    def _init_product_state(self):
        """Initialize to |00...0> product state."""
        # Each qubit is a separate tensor: shape (1, 2, 1)
        for _ in range(self.n_qubits):
            t = np.zeros((1, 2, 1), dtype=complex)
            t[0, 0, 0] = 1.0  # |0>
            self.tensors.append(t)

    def apply_single_qubit_gate(self, gate: np.ndarray, qubit: int):
        """Apply a single-qubit gate to a site.

        gate: shape (2, 2) unitary matrix.
        """
        t = self.tensors[qubit]
        # Contract gate with physical index
        # t shape: (bond_l, 2, bond_r)
        # gate shape: (2, 2)
        new_t = np.einsum("ijk,lj->ilk", t, gate)
        self.tensors[qubit] = new_t

    def apply_two_qubit_gate(self, gate: np.ndarray, q0: int, q1: int):
        """Apply a two-qubit gate using SVD decomposition.

        gate: shape (4, 4) unitary matrix reshaped to (2,2,2,2).
        """
        if abs(q0 - q1) != 1:
            # For non-adjacent qubits, apply SWAP chain
            if q0 < q1:
                for i in range(q0, q1):
                    self._apply_swap(i, i + 1)
                self.apply_two_qubit_gate(gate, q1 - 1, q1)
                for i in range(q0, q1 - 1):
                    self._apply_swap(i, i + 1)
            return

        # Ensure q0 < q1
        if q0 > q1:
            q0, q1 = q1, q0

        # Merge tensors at q0 and q1
        t0 = self.tensors[q0]   # (bl, 2, bm)
        t1 = self.tensors[q1]   # (bm, 2, br)

        # Contract to form 4-index tensor
        merged = np.einsum("ijk,klm->ijlm", t0, t1)
        # merged shape: (bl, 2, 2, br)

        bl, _, _, br = merged.shape

        # Apply gate: contract gate with physical indices
        g4_t = gate.reshape(2, 2, 2, 2)
        result = np.einsum("ijkl,aklb->aijb", g4_t, merged)
        # result shape: (bl, 2, 2, br)

        # SVD to split back
        result_2d = result.reshape(bl * 2, 2 * br)
        U, S, Vh = np.linalg.svd(result_2d, full_matrices=False)

        # Truncate
        chi = min(self.max_bond, len(S))
        while chi > 1 and S[chi - 1] < self.cutoff:
            chi -= 1

        U = U[:, :chi]
        S = S[:chi]
        Vh = Vh[:chi, :]

        # Normalize
        norm = np.sqrt(np.sum(S ** 2))
        if norm > 1e-12:
            S /= norm

        # Reshape back to tensors
        self.tensors[q0] = U.reshape(bl, 2, chi)
        self.tensors[q1] = (S[:, None] * Vh).reshape(chi, 2, br)

    def _apply_swap(self, q0: int, q1: int):
        """Apply SWAP between adjacent qubits."""
        t0 = self.tensors[q0]
        t1 = self.tensors[q1]

        bl, d, bm = t0.shape
        bm2, d2, br = t1.shape

        # Contract, swap physical indices, split
        merged = np.einsum("ijk,klm->ijlm", t0, t1)
        # merged: (bl, 2, 2, br) with indices (l, p0, p1, r)
        # Swap: (l, p1, p0, r)
        swapped = merged.transpose(0, 2, 1, 3)

        # SVD split
        result_2d = swapped.reshape(bl * 2, 2 * br)
        U, S, Vh = np.linalg.svd(result_2d, full_matrices=False)
        chi = min(self.max_bond, len(S))

        U = U[:, :chi]
        S = S[:chi]
        Vh = Vh[:chi, :]
        norm = np.sqrt(np.sum(S ** 2))
        if norm > 1e-12:
            S /= norm

        self.tensors[q0] = U.reshape(bl, 2, chi)
        self.tensors[q1] = (S[:, None] * Vh).reshape(chi, 2, br)

    def apply_cnot(self, control: int, target: int):
        """Apply CNOT gate."""
        # |0><0| ⊗ I + |1><1| ⊗ X
        gate = np.eye(4, dtype=complex)
        gate[2, 2] = 0
        gate[3, 3] = 0
        gate[2, 3] = 1
        gate[3, 2] = 1
        self.apply_two_qubit_gate(gate, control, target)

    def apply_h(self, qubit: int):
        """Apply Hadamard gate."""
        h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        self.apply_single_qubit_gate(h, qubit)

    def apply_rx(self, qubit: int, theta: float):
        """Apply Rx gate."""
        c, s = np.cos(theta / 2), np.sin(theta / 2)
        gate = np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)
        self.apply_single_qubit_gate(gate, qubit)

    def apply_ry(self, qubit: int, theta: float):
        """Apply Ry gate."""
        c, s = np.cos(theta / 2), np.sin(theta / 2)
        gate = np.array([[c, -s], [s, c]], dtype=complex)
        self.apply_single_qubit_gate(gate, qubit)

    def apply_rz(self, qubit: int, theta: float):
        """Apply Rz gate."""
        e0, e1 = np.exp(-1j * theta / 2), np.exp(1j * theta / 2)
        gate = np.array([[e0, 0], [0, e1]], dtype=complex)
        self.apply_single_qubit_gate(gate, qubit)

    def get_bond_dimensions(self) -> List[int]:
        """Get bond dimensions between sites."""
        dims = []
        for i in range(len(self.tensors) - 1):
            dims.append(self.tensors[i].shape[2])  # right bond
        return dims

    def get_max_bond(self) -> int:
        """Get maximum bond dimension."""
        dims = self.get_bond_dimensions()
        return max(dims) if dims else 1

    def fidelity_with(self, other: 'MatrixProductState') -> float:
        """Compute fidelity |<ψ|φ>|^2 with another MPS."""
        # Overlap via left-to-right contraction
        overlap = np.array([[1.0]], dtype=complex)

        for t1, t2 in zip(self.tensors, other.tensors):
            # Contract: overlap * t1† * t2
            # t1: (bl, 2, br), t2: (bl, 2, br)
            temp = np.einsum("ij,ikl->jkl", overlap, t1.conj())
            overlap = np.einsum("jkl,jkm->lm", temp, t2)

        return float(abs(overlap[0, 0]) ** 2)


class MPSSimulator:
    """MPS-based quantum circuit simulator.

    Parameters
    ----------
    n_qubits : int
        Number of qubits.
    max_bond : int
        Maximum bond dimension (controls accuracy vs speed).
    cutoff : float
        Truncation threshold for small singular values.
    """

    def __init__(
        self,
        n_qubits: int = 1,
        max_bond: int = 32,
        cutoff: float = 1e-10,
    ):
        self.n_qubits = n_qubits
        self.max_bond = max_bond
        self.cutoff = cutoff
        self.mps = MatrixProductState(n_qubits, max_bond, cutoff)
        self.name = "mps_simulator"

    def run_circuit(self, circuit: Circuit, shots: int = 1000) -> Dict[str, Any]:
        """Execute a circuit using MPS simulation."""
        for gate in circuit.gates:
            self._apply_gate(gate)

        counts = self._sample(shots)

        return {
            "counts": counts,
            "shots": shots,
            "num_qubits": self.n_qubits,
            "backend": self.name,
            "success": True,
            "max_bond": self.mps.get_max_bond(),
            "bond_dimensions": self.mps.get_bond_dimensions(),
        }

    def _apply_gate(self, gate: Gate):
        """Apply a gate to the MPS."""
        name = gate.name.upper()
        qubits = gate.qubits
        params = gate.params or []

        if name == "H":
            self.mps.apply_h(qubits[0])
        elif name == "X":
            gate_m = np.array([[0, 1], [1, 0]], dtype=complex)
            self.mps.apply_single_qubit_gate(gate_m, qubits[0])
        elif name == "Y":
            gate_m = np.array([[0, -1j], [1j, 0]], dtype=complex)
            self.mps.apply_single_qubit_gate(gate_m, qubits[0])
        elif name == "Z":
            gate_m = np.array([[1, 0], [0, -1]], dtype=complex)
            self.mps.apply_single_qubit_gate(gate_m, qubits[0])
        elif name == "S":
            gate_m = np.array([[1, 0], [0, 1j]], dtype=complex)
            self.mps.apply_single_qubit_gate(gate_m, qubits[0])
        elif name == "S_DAG":
            gate_m = np.array([[1, 0], [0, -1j]], dtype=complex)
            self.mps.apply_single_qubit_gate(gate_m, qubits[0])
        elif name == "T":
            gate_m = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
            self.mps.apply_single_qubit_gate(gate_m, qubits[0])
        elif name == "RX":
            self.mps.apply_rx(qubits[0], params[0] if params else 0)
        elif name == "RY":
            self.mps.apply_ry(qubits[0], params[0] if params else 0)
        elif name == "RZ":
            self.mps.apply_rz(qubits[0], params[0] if params else 0)
        elif name in ("CNOT", "CX"):
            self.mps.apply_cnot(qubits[0], qubits[1])
        elif name == "CZ":
            # CZ = H(target) CNOT H(target)
            self.mps.apply_h(qubits[1])
            self.mps.apply_cnot(qubits[0], qubits[1])
            self.mps.apply_h(qubits[1])
        elif name == "SWAP":
            self.mps._apply_swap(qubits[0], qubits[1])

    def _sample(self, shots: int) -> Dict[str, int]:
        """Sample from the MPS.

        For small systems (n <= 20), computes full statevector.
        For larger systems, uses sequential sampling.
        """
        if self.n_qubits <= 20:
            # Full statevector approach (exact, simple)
            sv = self.get_statevector()
            probs = np.abs(sv) ** 2
            probs = probs / probs.sum()
            indices = np.random.choice(len(sv), size=shots, p=probs)
            counts = {}
            for idx in indices:
                bs = format(idx, f"0{self.n_qubits}b")
                counts[bs] = counts.get(bs, 0) + 1
            return counts

        # Sequential sampling for large systems
        counts = {}
        for _ in range(shots):
            mps_copy = MatrixProductState(self.n_qubits, self.max_bond, self.cutoff)
            mps_copy.tensors = [t.copy() for t in self.mps.tensors]

            bits = []
            for q in range(self.n_qubits):
                t = mps_copy.tensors[q]
                bl, d, br = t.shape

                # Left environment L: (bl, bl)
                L = np.ones((1, 1), dtype=complex)
                for i in range(q):
                    Ti = mps_copy.tensors[i]
                    L_new = np.einsum("ab,apc,bpd->cd", L, Ti, Ti.conj())
                    L = L_new

                # Right environment R: (br, br)
                R = np.ones((1, 1), dtype=complex)
                for i in range(self.n_qubits - 1, q, -1):
                    Ti = mps_copy.tensors[i]
                    R_new = np.einsum("apc,bpd,cd->ab", Ti, Ti.conj(), R)
                    R = R_new

                # P(k) = Σ_{a,b,c,d} L[a,b] t[a,k,c] conj(t[b,k,d]) R[c,d]
                vals = []
                for k in range(2):
                    tk = t[:, k, :]  # (bl, br)
                    # Step 1: L.T @ tk -> (bl, br)
                    # Step 2: tk.conj() @ R -> (bl, br)
                    # Step 3: elementwise multiply and sum
                    term1 = L.T @ tk
                    term2 = tk.conj() @ R
                    val = np.sum(term1 * term2)
                    vals.append(float(abs(val)))

                p0, p1 = vals
                total = p0 + p1
                if total > 1e-12:
                    p0 /= total
                    p1 /= total
                else:
                    p0, p1 = 0.5, 0.5

                bit = 0 if np.random.random() > p1 else 1
                bits.append(bit)

                collapsed = t[:, bit:bit+1, :].copy()
                norm = np.sqrt(np.sum(np.abs(collapsed) ** 2))
                if norm > 1e-12:
                    collapsed /= norm
                mps_copy.tensors[q] = collapsed

            bitstring = "".join(str(b) for b in reversed(bits))
            counts[bitstring] = counts.get(bitstring, 0) + 1

        return counts

    def get_statevector(self) -> np.ndarray:
        """Convert MPS to full statevector (expensive for large n)."""
        if self.n_qubits > 20:
            raise ValueError("Statevector conversion too expensive for >20 qubits")

        # Contract all tensors left to right
        sv = np.ones((1,), dtype=complex)
        for t in self.mps.tensors:
            # t shape: (bond_l, 2, bond_r), sv shape: (..., bond_l)
            sv = np.tensordot(sv, t, axes=([-1], [0]))
            # sv shape: (..., 2, bond_r)

        # Remove trailing bond dimensions (should be 1)
        while sv.ndim > 1 and sv.shape[-1] == 1:
            sv = sv[..., 0]

        return sv.reshape(-1)

    def get_bond_info(self) -> Dict[str, Any]:
        """Get bond dimension information."""
        return {
            "max_bond": self.mps.get_max_bond(),
            "bond_dimensions": self.mps.get_bond_dimensions(),
            "max_allowed": self.max_bond,
        }
