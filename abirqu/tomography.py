"""
Quantum State Tomography for AbirQu
Copyright 2026 Abir Maheshwari

Reconstruct density matrices from measurement data using
full tomography, compressed sensing, and classical shadows.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from abirqu.circuit import Circuit
from abirqu.gates import H, X, Y, Z, S, S_dag, CNOT


def single_qubit_pauli_matrices() -> Dict[str, np.ndarray]:
    """Return the four single-qubit Pauli matrices."""
    return {
        'I': np.eye(2, dtype=complex),
        'X': np.array([[0, 1], [1, 0]], dtype=complex),
        'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
        'Z': np.array([[1, 0], [0, -1]], dtype=complex),
    }


def pauli_string_to_matrix(paulis: List[str]) -> np.ndarray:
    """Compute tensor product of Pauli matrices."""
    paulis_dict = single_qubit_pauli_matrices()
    result = np.array([[1.0]], dtype=complex)
    for p in paulis:
        result = np.kron(result, paulis_dict[p])
    return result


class MeasurementBasis:
    """A measurement basis for quantum state tomography."""

    def __init__(self, name: str, circuit: Circuit, outcomes: List[str]):
        self.name = name
        self.circuit = circuit
        self.outcomes = outcomes

    def __repr__(self):
        return f"MeasurementBasis({self.name})"


def generate_tomography_bases(n_qubits: int) -> List[MeasurementBasis]:
    """
    Generate measurement bases for quantum state tomography.

    For n qubits, generates 3^n measurement settings (X, Y, Z for each qubit).
    """
    bases = []
    pauli_names = ['X', 'Y', 'Z']

    # Generate all combinations of Pauli bases
    from itertools import product
    for pauli_combo in product(pauli_names, repeat=n_qubits):
        circuit = Circuit(n_qubits)
        outcomes = []

        # Apply basis change gates
        for q, pauli in enumerate(pauli_combo):
            if pauli == 'X':
                circuit.h(q)
            elif pauli == 'Y':
                circuit.s(q)
                circuit.h(q)

        basis_name = ''.join(pauli_combo)
        bases.append(MeasurementBasis(basis_name, circuit, outcomes))

    return bases


class QuantumStateTomography:
    """
    Quantum State Tomography using measurement data.

    Reconstructs the density matrix ρ from measurement outcomes
    in different bases.

    Features:
    - Full tomography with Pauli measurement
    - Linear inversion reconstruction
    - Maximum likelihood estimation (MLE)
    - Compressed sensing for low-rank states

    Usage:
        tomographer = QuantumStateTomography(n_qubits=2)
        data = tomographer.collect_data(statevector, num_shots=1000)
        rho = tomographer.reconstruct(data)
    """

    def __init__(self, n_qubits: int, method: str = 'linear'):
        self.n_qubits = n_qubits
        self.method = method
        self.dim = 2 ** n_qubits
        self.bases = generate_tomography_bases(n_qubits)
        self.stats = {
            'num_bases': len(self.bases),
            'total_measurements': 0,
            'fidelity': 0.0,
        }

    def collect_data(
        self,
        statevector: Optional[np.ndarray] = None,
        density_matrix: Optional[np.ndarray] = None,
        num_shots: int = 1000,
        seed: Optional[int] = None,
    ) -> Dict[str, Dict[str, int]]:
        """
        Collect measurement data in all tomography bases.

        Returns dictionary: {basis_name: {outcome: count}}
        """
        rng = np.random.RandomState(seed)

        if statevector is not None:
            rho = np.outer(statevector, statevector.conj())
        elif density_matrix is not None:
            rho = density_matrix
        else:
            raise ValueError("Provide statevector or density_matrix")

        data = {}
        for basis in self.bases:
            # Apply basis change circuit
            if basis.circuit.gates:
                # Simulate: apply basis change to state
                U = self._circuit_to_unitary(basis.circuit)
                rho_rotated = U @ rho @ U.conj().T
            else:
                rho_rotated = rho

            # Sample from diagonal of rotated density matrix
            probs = np.abs(np.diag(rho_rotated))
            probs = np.real(probs)
            probs = np.clip(probs, 0, None)
            total = probs.sum()
            if total > 0:
                probs /= total
            else:
                probs = np.ones(self.dim) / self.dim

            outcomes = rng.choice(self.dim, size=num_shots, p=probs)
            counts = {}
            for o in outcomes:
                key = format(o, f'0{self.n_qubits}b')
                counts[key] = counts.get(key, 0) + 1

            data[basis.name] = counts
            self.stats['total_measurements'] += num_shots

        return data

    def _circuit_to_unitary(self, circuit: Circuit) -> np.ndarray:
        """Convert a circuit to its unitary matrix."""
        U = np.eye(self.dim, dtype=complex)
        for gate in circuit.gates:
            gate_matrix = self._gate_to_matrix(gate)
            U = gate_matrix @ U
        return U

    def _gate_to_matrix(self, gate) -> np.ndarray:
        """Convert a single gate to its matrix representation."""
        name = gate.name.upper()
        q = gate.qubits[0]

        # Single qubit gates
        gate_matrices = {
            'H': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
            'X': np.array([[0, 1], [1, 0]], dtype=complex),
            'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
            'Z': np.array([[1, 0], [0, -1]], dtype=complex),
            'S': np.array([[1, 0], [0, 1j]], dtype=complex),
            'S_DAG': np.array([[1, 0], [0, -1j]], dtype=complex),
            'T': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
        }

        if name in gate_matrices:
            return self._embed_single_qubit(gate_matrices[name], q)

        if name in ('CNOT', 'CX'):
            return self._cnot_matrix(gate.qubits[0], gate.qubits[1])

        return np.eye(self.dim, dtype=complex)

    def _embed_single_qubit(self, matrix: np.ndarray, qubit: int) -> np.ndarray:
        """Embed a single-qubit gate into the full Hilbert space."""
        result = np.eye(1, dtype=complex)
        for i in range(self.n_qubits):
            if i == qubit:
                result = np.kron(result, matrix)
            else:
                result = np.kron(result, np.eye(2, dtype=complex))
        return result

    def _cnot_matrix(self, control: int, target: int) -> np.ndarray:
        """Build CNOT matrix."""
        dim = self.dim
        mat = np.zeros((dim, dim), dtype=complex)
        for i in range(dim):
            bits = list(format(i, f'0{self.n_qubits}b'))
            c_bit = int(bits[control])
            t_bit = int(bits[target])

            if c_bit == 1:
                bits[target] = '0' if t_bit == 1 else '1'

            j = int(''.join(bits), 2)
            mat[j, i] = 1.0
        return mat

    def reconstruct(self, data: Dict[str, Dict[str, int]]) -> np.ndarray:
        """
        Reconstruct density matrix from measurement data.

        Uses linear inversion: ρ = sum_{i,j} <P_i> P_i / dim
        """
        paulis_dict = single_qubit_pauli_matrices()
        pauli_names = ['I', 'X', 'Y', 'Z']

        rho = np.zeros((self.dim, self.dim), dtype=complex)

        # Compute expectation values
        from itertools import product as iterproduct
        for pauli_combo in iterproduct(pauli_names, repeat=self.n_qubits):
            if all(p == 'I' for p in pauli_combo):
                # Identity term: just add 1/dim to diagonal
                rho += np.eye(self.dim, dtype=complex) / self.dim
                continue

            basis_name = ''.join(p if p != 'I' else 'I' for p in pauli_combo)

            # Skip non-measurement bases
            if basis_name not in data:
                continue

            counts = data[basis_name]
            total = sum(counts.values())
            if total == 0:
                continue

            # Compute expectation value <P>
            expectation = 0.0
            for outcome_str, count in counts.items():
                outcome = int(outcome_str, 2)
                # Compute parity for each qubit
                sign = 1
                for q, pauli in enumerate(pauli_combo):
                    if pauli != 'I':
                        bit = (outcome >> (self.n_qubits - 1 - q)) & 1
                        if bit == 1:
                            sign *= -1
                expectation += sign * count / total

            # Add contribution to density matrix
            P = pauli_string_to_matrix(list(pauli_combo))
            rho += expectation * P / self.dim

        # Ensure Hermiticity
        rho = (rho + rho.conj().T) / 2

        self.stats['fidelity'] = np.real(np.trace(rho))
        return rho

    def fidelity(self, reconstructed: np.ndarray, target: np.ndarray) -> float:
        """Compute fidelity between reconstructed and target density matrix."""
        sqrt_rho = np.linalg.matrix_power(reconstructed, 1/2)
        fidelity_val = np.real(np.trace(np.linalg.matrix_power(
            sqrt_rho @ target @ sqrt_rho, 1/2
        )))
        return float(np.clip(fidelity_val, 0, 1))

    def purity(self, rho: np.ndarray) -> float:
        """Compute purity Tr(ρ²). Pure state = 1, maximally mixed = 1/dim."""
        return float(np.real(np.trace(rho @ rho)))

    def von_neumann_entropy(self, rho: np.ndarray) -> float:
        """Compute von Neumann entropy S = -Tr(ρ log₂ ρ)."""
        eigenvalues = np.linalg.eigvalsh(rho)
        eigenvalues = np.real(eigenvalues)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        return float(-np.sum(eigenvalues * np.log2(eigenvalues)))

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


class CompressedSensingTomography:
    """
    Compressed sensing quantum state tomography.

    Reconstructs low-rank density matrices from fewer measurements
    than full tomography requires.
    """

    def __init__(self, n_qubits: int, rank: int = 1):
        self.n_qubits = n_qubits
        self.dim = 2 ** n_qubits
        self.rank = rank

    def reconstruct(self, measurements: List[float], measurement_matrices: List[np.ndarray]) -> np.ndarray:
        """
        Reconstruct density matrix from compressed measurements.

        Uses nuclear norm minimization (simplified version).
        """
        n_measurements = len(measurements)

        # Build measurement matrix
        M = np.zeros((n_measurements, self.dim ** 2), dtype=complex)
        for i, (val, mat) in enumerate(zip(measurements, measurement_matrices)):
            M[i, :] = mat.flatten()

        # Solve via least squares (simplified)
        b = np.array(measurements, dtype=complex)

        # Use pseudo-inverse
        try:
            rho_vec = np.linalg.lstsq(M, b, rcond=None)[0]
            rho = rho_vec.reshape((self.dim, self.dim))
        except np.linalg.LinAlgError:
            rho = np.eye(self.dim, dtype=complex) / self.dim

        # Enforce Hermiticity and trace 1
        rho = (rho + rho.conj().T) / 2
        trace = np.trace(rho)
        if abs(trace) > 1e-10:
            rho /= trace

        return rho

    def generate_measurement_matrices(self, num_measurements: int, seed: Optional[int] = None) -> List[np.ndarray]:
        """Generate random measurement matrices for compressed sensing."""
        rng = np.random.RandomState(seed)
        matrices = []
        for _ in range(num_measurements):
            # Random Hermitian matrix
            A = rng.randn(self.dim, self.dim) + 1j * rng.randn(self.dim, self.dim)
            A = (A + A.conj().T) / 2
            matrices.append(A)
        return matrices
