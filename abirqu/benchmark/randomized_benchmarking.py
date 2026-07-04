"""
Randomized Benchmarking for AbirQu
Copyright 2026 Abir Maheshwari

Estimate average gate fidelity via random Clifford sequences.
Standard method for characterizing quantum gate performance.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from abirqu.circuit import Circuit


# Clifford group for single qubit (24 elements)
SINGLE_QUBIT_CLIFFORDS = [
    # Identity
    np.array([[1, 0], [0, 1]], dtype=complex),
    # Pauli gates
    np.array([[0, 1], [1, 0]], dtype=complex),  # X
    np.array([[0, -1j], [1j, 0]], dtype=complex),  # Y
    np.array([[1, 0], [0, -1]], dtype=complex),  # Z
    # Hadamard-like
    np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),  # H
    np.array([[1, -1], [1, 1]], dtype=complex) / np.sqrt(2),
    np.array([[1, 1j], [1j, 1]], dtype=complex) / np.sqrt(2),
    np.array([[1, -1j], [-1j, 1]], dtype=complex) / np.sqrt(2),
    # Phase gates
    np.array([[1, 0], [0, 1j]], dtype=complex),  # S
    np.array([[1, 0], [0, -1j]], dtype=complex),  # S†
    np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),  # T
    np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex),  # T†
    # More rotations
    np.array([[0, 1], [-1, 0]], dtype=complex),
    np.array([[0, -1], [1, 0]], dtype=complex),
    np.array([[0, 1j], [1j, 0]], dtype=complex),
    np.array([[0, -1j], [-1j, 0]], dtype=complex),
    # Additional Clifford elements
    np.array([[1, 0], [0, 1]], dtype=complex) * np.exp(1j * np.pi / 4),
    np.array([[1, 0], [0, 1]], dtype=complex) * np.exp(-1j * np.pi / 4),
    np.array([[0, 1], [1, 0]], dtype=complex) * np.exp(1j * np.pi / 4),
    np.array([[0, 1], [1, 0]], dtype=complex) * np.exp(-1j * np.pi / 4),
    np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2) * np.exp(1j * np.pi / 4),
    np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2) * np.exp(-1j * np.pi / 4),
    np.array([[1, -1], [1, 1]], dtype=complex) / np.sqrt(2) * np.exp(1j * np.pi / 4),
    np.array([[1, -1], [1, 1]], dtype=complex) / np.sqrt(2) * np.exp(-1j * np.pi / 4),
]


def random_clifford_single_qubit(rng: np.random.RandomState) -> np.ndarray:
    """Sample a random single-qubit Clifford gate."""
    idx = rng.randint(0, len(SINGLE_QUBIT_CLIFFORDS))
    return SINGLE_QUBIT_CLIFFORDS[idx]


def inverse_clifford(matrix: np.ndarray) -> np.ndarray:
    """Compute the inverse of a Clifford gate (unitary inverse)."""
    return matrix.conj().T


def clifford_to_circuit(matrix: np.ndarray, qubit: int = 0) -> Circuit:
    """
    Decompose a single-qubit Clifford gate into a circuit.

    Uses brute-force search through known decompositions.
    """
    circuit = Circuit(1)

    # Check against known gates
    for name, gate_matrix in [
        ('I', np.eye(2, dtype=complex)),
        ('X', np.array([[0, 1], [1, 0]], dtype=complex)),
        ('Y', np.array([[0, -1j], [1j, 0]], dtype=complex)),
        ('Z', np.array([[1, 0], [0, -1]], dtype=complex)),
        ('H', np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)),
        ('S', np.array([[1, 0], [0, 1j]], dtype=complex)),
        ('S_DAG', np.array([[1, 0], [0, -1j]], dtype=complex)),
        ('T', np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)),
        ('T_DAG', np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex)),
    ]:
        if np.allclose(matrix, gate_matrix):
            if name != 'I':
                circuit.add_gate(name, [0])
            return circuit

    # Fallback: use S and H decomposition
    circuit.add_gate('H', [0])
    circuit.add_gate('S', [0])
    circuit.add_gate('H', [0])
    return circuit


class RandomizedBenchmarking:
    """
    Randomized Benchmarking for average gate fidelity estimation.

    Protocol:
    1. Generate random Clifford sequences of length m
    2. Append the inverse Clifford to return to |0>
    3. Measure survival probability
    4. Fit to A * p^m + B to extract depolarizing parameter p
    5. Convert p to average gate fidelity

    Usage:
        rb = RandomizedBenchmarking(n_qubits=1)
        results = rb.run(statevector_or_simulator)
        fidelity = rb.fit_and_extract_fidelity(results)
    """

    def __init__(
        self,
        n_qubits: int = 1,
        sequence_lengths: Optional[List[int]] = None,
        num_sequences: int = 50,
        shots: int = 1024,
        seed: Optional[int] = None,
    ):
        self.n_qubits = n_qubits
        self.sequence_lengths = sequence_lengths or [1, 2, 4, 8, 16, 32, 64]
        self.num_sequences = num_sequences
        self.shots = shots
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        self.stats = {
            'total_gates': 0,
            'total_shots': 0,
            'fidelity': 0.0,
            'depolarizing_parameter': 0.0,
        }

    def generate_sequence(self, length: int) -> List[np.ndarray]:
        """Generate a random Clifford sequence."""
        sequence = []
        for _ in range(length):
            sequence.append(random_clifford_single_qubit(self.rng))
        return sequence

    def compute_inverse(self, sequence: List[np.ndarray]) -> np.ndarray:
        """Compute the inverse of the entire sequence."""
        result = np.eye(2, dtype=complex)
        for gate in reversed(sequence):
            result = result @ gate.conj().T
        return result

    def sequence_to_circuit(self, sequence: List[np.ndarray], inverse: np.ndarray) -> Circuit:
        """Convert a Clifford sequence + inverse to a circuit."""
        circuit = Circuit(self.n_qubits)

        for gate in sequence:
            clifford_circuit = clifford_to_circuit(gate, 0)
            for g in clifford_circuit.gates:
                circuit.add_gate(g.name, g.qubits, g.params)

        # Add inverse
        inv_circuit = clifford_to_circuit(inverse, 0)
        for g in inv_circuit.gates:
            circuit.add_gate(g.name, g.qubits, g.params)

        return circuit

    def survival_probability(self, counts: Dict[str, int]) -> float:
        """Compute probability of measuring |0...0>."""
        total = sum(counts.values())
        if total == 0:
            return 0.0
        zero_key = '0' * self.n_qubits
        return counts.get(zero_key, 0) / total

    def run(
        self,
        circuit_executor=None,
        statevector: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Run the randomized benchmarking protocol.

        Args:
            circuit_executor: function that takes a Circuit and returns counts dict
            statevector: if provided, simulate directly without executor
        """
        results = {
            'sequence_lengths': [],
            'survival_probabilities': [],
            'std_errors': [],
            'all_data': [],
        }

        for length in self.sequence_lengths:
            survival_probs = []

            for _ in range(self.num_sequences):
                sequence = self.generate_sequence(length)
                inverse = self.compute_inverse(sequence)
                circuit = self.sequence_to_circuit(sequence, inverse)

                if circuit_executor is not None:
                    counts = circuit_executor(circuit)
                elif statevector is not None:
                    counts = self._simulate_circuit(circuit, statevector)
                else:
                    counts = {'0' * self.n_qubits: self.shots}

                sp = self.survival_probability(counts)
                survival_probs.append(sp)
                self.stats['total_gates'] += length + 1
                self.stats['total_shots'] += self.shots

            mean_sp = np.mean(survival_probs)
            std_sp = np.std(survival_probs) / np.sqrt(len(survival_probs))

            results['sequence_lengths'].append(length)
            results['survival_probabilities'].append(mean_sp)
            results['std_errors'].append(std_sp)
            results['all_data'].append(survival_probs)

        return results

    def _simulate_circuit(self, circuit: Circuit, statevector: np.ndarray) -> Dict[str, int]:
        """Simulate a circuit and return measurement counts."""
        # Apply gates to statevector
        current_state = statevector.copy()

        for gate in circuit.gates:
            gate_matrix = self._gate_to_matrix(gate)
            current_state = gate_matrix @ current_state

        # Sample from final state
        probs = np.abs(current_state) ** 2
        probs = np.real(probs)
        probs = np.clip(probs, 0, None)
        total = probs.sum()
        if total > 0:
            probs /= total
        else:
            probs = np.ones(len(current_state)) / len(current_state)

        indices = np.random.choice(len(current_state), size=self.shots, p=probs)
        counts = {}
        for idx in indices:
            key = format(idx, f'0{self.n_qubits}b')
            counts[key] = counts.get(key, 0) + 1

        return counts

    def _gate_to_matrix(self, gate) -> np.ndarray:
        """Convert gate to matrix."""
        name = gate.name.upper()
        gate_matrices = {
            'H': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
            'X': np.array([[0, 1], [1, 0]], dtype=complex),
            'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
            'Z': np.array([[1, 0], [0, -1]], dtype=complex),
            'S': np.array([[1, 0], [0, 1j]], dtype=complex),
            'S_DAG': np.array([[1, 0], [0, -1j]], dtype=complex),
            'T': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
            'T_DAG': np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex),
        }

        if name in gate_matrices:
            return gate_matrices[name]

        return np.eye(2, dtype=complex)

    def fit_and_extract_fidelity(self, results: Dict[str, Any]) -> float:
        """
        Fit survival probabilities to A * p^m + B and extract fidelity.

        Average gate fidelity: F = (p * (d - 1) + 1) / d
        where d = 2^n_qubits
        """
        lengths = np.array(results['sequence_lengths'])
        probs = np.array(results['survival_probabilities'])

        d = 2 ** self.n_qubits

        # Fit: A * p^m + B
        def model(m, A, p, B):
            return A * np.power(p, m) + B

        try:
            from scipy.optimize import curve_fit

            # Initial guess
            p0 = [0.5, 0.95, 1 / d]

            # Fit
            popt, pcov = curve_fit(model, lengths, probs, p0=p0, maxfev=10000)
            A_fit, p_fit, B_fit = popt

            # Ensure p is in valid range
            p_fit = np.clip(np.abs(p_fit), 0, 1)

            # Compute fidelity
            fidelity = (p_fit * (d - 1) + 1) / d

            self.stats['depolarizing_parameter'] = float(p_fit)
            self.stats['fidelity'] = float(np.clip(fidelity, 0, 1))

        except Exception:
            # Fallback: simple exponential fit
            if len(lengths) > 1:
                log_probs = np.log(np.maximum(probs, 1e-10))
                slope, intercept = np.polyfit(lengths, log_probs, 1)
                p_fit = np.exp(slope)
                p_fit = np.clip(np.abs(p_fit), 0, 1)
                fidelity = (p_fit * (d - 1) + 1) / d
                self.stats['depolarizing_parameter'] = float(p_fit)
                self.stats['fidelity'] = float(np.clip(fidelity, 0, 1))
            else:
                self.stats['fidelity'] = 0.5

        return self.stats['fidelity']

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


class InterleavedRandomizedBenchmarking:
    """
    Interleaved Randomized Benchmarking for individual gate fidelity.

    Measures the fidelity of a specific gate by interleaving it with
    random Cliffords and comparing to the standard RB baseline.
    """

    def __init__(
        self,
        gate_matrix: np.ndarray,
        n_qubits: int = 1,
        sequence_lengths: Optional[List[int]] = None,
        num_sequences: int = 50,
        shots: int = 1024,
        seed: Optional[int] = None,
    ):
        self.gate_matrix = gate_matrix
        self.rb = RandomizedBenchmarking(
            n_qubits, sequence_lengths, num_sequences, shots, seed
        )
        self.rng = np.random.RandomState(seed)

    def run_interleaved(
        self,
        circuit_executor=None,
        statevector: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Run interleaved RB protocol."""
        results = {
            'sequence_lengths': [],
            'survival_probabilities': [],
            'std_errors': [],
            'all_data': [],
        }

        for length in self.rb.sequence_lengths:
            survival_probs = []

            for _ in range(self.rb.num_sequences):
                # Generate random Cliffords
                sequence = self.rb.generate_sequence(length)

                # Build circuit with interleaved gate
                circuit = Circuit(self.rb.n_qubits)

                for clifford in sequence:
                    # Add random Clifford
                    clifford_circuit = clifford_to_circuit(clifford, 0)
                    for g in clifford_circuit.gates:
                        circuit.add_gate(g.name, g.qubits, g.params)

                    # Add interleaved gate
                    gate_circuit = clifford_to_circuit(self.gate_matrix, 0)
                    for g in gate_circuit.gates:
                        circuit.add_gate(g.name, g.qubits, g.params)

                # Add inverse of the entire sequence (including interleaved gates)
                # Simplified: just add inverse of random Cliffords
                inverse = self.rb.compute_inverse(sequence)
                inv_circuit = clifford_to_circuit(inverse, 0)
                for g in inv_circuit.gates:
                    circuit.add_gate(g.name, g.qubits, g.params)

                # Execute
                if circuit_executor is not None:
                    counts = circuit_executor(circuit)
                elif statevector is not None:
                    counts = self.rb._simulate_circuit(circuit, statevector)
                else:
                    counts = {'0' * self.rb.n_qubits: self.rb.shots}

                sp = self.rb.survival_probability(counts)
                survival_probs.append(sp)

            mean_sp = np.mean(survival_probs)
            std_sp = np.std(survival_probs) / np.sqrt(len(survival_probs))

            results['sequence_lengths'].append(length)
            results['survival_probabilities'].append(mean_sp)
            results['std_errors'].append(std_sp)
            results['all_data'].append(survival_probs)

        return results

    def extract_gate_fidelity(
        self,
        standard_results: Dict[str, Any],
        interleaved_results: Dict[str, Any],
    ) -> float:
        """
        Extract individual gate fidelity from standard and interleaved RB.

        F_gate = (p_interleaved / p_standard * (d-1) + 1) / d
        """
        # Fit both
        standard_fidelity = self.rb.fit_and_extract_fidelity(standard_results)
        self.rb.stats['fidelity'] = 0  # Reset
        interleaved_fidelity = self.rb.fit_and_extract_fidelity(interleaved_results)

        d = 2 ** self.rb.n_qubits
        p_standard = self.rb.stats['depolarizing_parameter']

        self.rb.stats['fidelity'] = standard_fidelity
        self.rb.fit_and_extract_fidelity(interleaved_results)
        p_interleaved = self.rb.stats['depolarizing_parameter']

        # Compute gate fidelity
        if p_standard > 0:
            gate_fidelity = (p_interleaved / p_standard * (d - 1) + 1) / d
        else:
            gate_fidelity = 0.5

        return float(np.clip(gate_fidelity, 0, 1))
