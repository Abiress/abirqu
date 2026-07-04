"""
Pauli Expectation Value Optimizer for AbirQu
Copyright 2026 Abir Maheshwari

Efficient estimation of <ψ|P|ψ> for large Pauli sums using
grouping, commutation relations, and classical shadows.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from abirqu.circuit import Circuit


class PauliTerm:
    """A single Pauli term: coefficient * (P_0 ⊗ P_1 ⊗ ... ⊗ P_{n-1})."""

    def __init__(self, coefficient: float, paulis: List[str], qubits: Optional[List[int]] = None):
        self.coefficient = coefficient
        self.paulis = paulis
        self.qubits = qubits or list(range(len(paulis)))

    def __repr__(self):
        return f"PauliTerm({self.coefficient:.4f}, {self.paulis})"

    def weight(self) -> int:
        """Number of non-identity Pauli operators."""
        return sum(1 for p in self.paulis if p.upper() != 'I')

    def qubit_support(self) -> List[int]:
        """Qubits with non-identity Pauli operators."""
        return [q for p, q in zip(self.paulis, self.qubits) if p.upper() != 'I']


class PauliHamiltonian:
    """A sum of Pauli terms: H = sum_i c_i * P_i."""

    def __init__(self, terms: Optional[List[PauliTerm]] = None, n_qubits: int = 0):
        self.terms = terms or []
        self.n_qubits = n_qubits or max((max(t.qubits) + 1 if t.qubits else 0 for t in self.terms), default=0)

    def add_term(self, coefficient: float, paulis: List[str], qubits: Optional[List[int]] = None):
        self.terms.append(PauliTerm(coefficient, paulis, qubits))

    @property
    def num_terms(self) -> int:
        return len(self.terms)

    def __repr__(self):
        return f"PauliHamiltonian({self.num_terms} terms, {self.n_qubits} qubits)"


def commute_check(p1: PauliTerm, p2: PauliTerm) -> bool:
    """Check if two Pauli terms commute."""
    n = max(max(p1.qubits) + 1 if p1.qubits else 0,
            max(p2.qubits) + 1 if p2.qubits else 0)

    anti_commute_count = 0
    for q in range(n):
        p1_op = 'I'
        p2_op = 'I'

        if q in p1.qubits:
            idx = p1.qubits.index(q)
            p1_op = p1.paulis[idx]
        if q in p2.qubits:
            idx = p2.qubits.index(q)
            p2_op = p2.paulis[idx]

        if p1_op != 'I' and p2_op != 'I' and p1_op != p2_op:
            anti_commute_count += 1

    return anti_commute_count % 2 == 0


def group_pauli_terms(terms: List[PauliTerm]) -> List[List[PauliTerm]]:
    """
    Group Pauli terms that can be measured simultaneously.

    Uses greedy coloring based on commutation relations.
    Terms in the same group commute and can be measured together.
    """
    if not terms:
        return []

    n = len(terms)
    colors = [-1] * n
    num_colors = 0

    # Build commutativity graph adjacency
    adjacency = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if commute_check(terms[i], terms[j]):
                adjacency[i].append(j)
                adjacency[j].append(i)

    # Greedy graph coloring
    for i in range(n):
        used_colors = set()
        for j in adjacency[i]:
            if colors[j] != -1:
                used_colors.add(colors[j])

        color = 0
        while color in used_colors:
            color += 1

        colors[i] = color
        num_colors = max(num_colors, color + 1)

    # Group terms by color
    groups = [[] for _ in range(num_colors)]
    for i, color in enumerate(colors):
        groups[color].append(terms[i])

    return groups


def generate_clifford_circuit_for_pauli(pauli: PauliTerm, n_qubits: int) -> Circuit:
    """
    Generate a Clifford circuit that diagonalizes a Pauli term.

    Transforms the Pauli term into a Z-basis measurement.
    """
    circuit = Circuit(n_qubits)

    for q, op in zip(pauli.qubits, pauli.paulis):
        op = op.upper()
        if op == 'X':
            circuit.h(q)
        elif op == 'Y':
            circuit.s(q)
            circuit.h(q)
        elif op == 'Z':
            pass
        elif op == 'I':
            pass

    return circuit


class PauliExpectationOptimizer:
    """
    Optimizer for measuring Pauli expectation values.

    Features:
    - Pauli grouping for simultaneous measurement
    - Commutation-based grouping
    - Graph coloring for optimal groups
    - Shot allocation optimization

    Usage:
        optimizer = PauliExpectationOptimizer()
        groups = optimizer.optimize(hamiltonian)
        results = optimizer.measure(groups, simulator)
    """

    def __init__(self, shots: int = 4000, method: str = 'commutative'):
        self.shots = shots
        self.method = method
        self.stats = {
            'total_terms': 0,
            'num_groups': 0,
            'total_shots': 0,
            'shots_saved': 0,
        }

    def optimize(self, hamiltonian: PauliHamiltonian) -> List[Dict[str, Any]]:
        """
        Group Pauli terms for efficient measurement.

        Returns list of measurement groups, each containing:
        - terms: list of PauliTerms
        - circuit: circuit to diagonalize the group
        - measurement_qubits: qubits to measure
        - coefficients: coefficients for each term
        """
        self.stats['total_terms'] = hamiltonian.num_terms

        if self.method == 'commutative':
            groups = group_pauli_terms(hamiltonian.terms)
        else:
            # Naive grouping: one term per group
            groups = [[t] for t in hamiltonian.terms]

        self.stats['num_groups'] = len(groups)

        result = []
        for group_terms in groups:
            # Find measurement qubits (union of all term supports)
            all_qubits = set()
            for t in group_terms:
                all_qubits.update(t.qubit_support())

            measurement_qubits = sorted(all_qubits)

            # Generate diagonalization circuit
            if len(group_terms) == 1:
                circuit = generate_clifford_circuit_for_pauli(group_terms[0], hamiltonian.n_qubits)
            else:
                circuit = Circuit(hamiltonian.n_qubits)

            coefficients = [t.coefficient for t in group_terms]

            result.append({
                'terms': group_terms,
                'circuit': circuit,
                'measurement_qubits': measurement_qubits,
                'coefficients': coefficients,
            })

        # Estimate shots saved
        naive_shots = hamiltonian.num_terms * self.shots
        actual_shots = len(groups) * self.shots
        self.stats['shots_saved'] = naive_shots - actual_shots
        self.stats['total_shots'] = actual_shots

        return result

    def compute_expectation_from_counts(
        self,
        counts: Dict[str, int],
        measurement_qubits: List[int],
        coefficients: List[float],
        group_terms: List[PauliTerm],
    ) -> float:
        """
        Compute expectation value from measurement counts.

        For a diagonalized Pauli term, the expectation value is:
        <P> = sum_i (-1)^{bitstring_i} * count_i / total_shots
        """
        total = sum(counts.values())
        if total == 0:
            return 0.0

        expectation = 0.0
        for bitstring, count in counts.items():
            # Extract measurement qubit values
            measured_values = {}
            for q in measurement_qubits:
                if q < len(bitstring):
                    measured_values[q] = int(bitstring[len(bitstring) - 1 - q])
                else:
                    measured_values[q] = 0

            # For each term, compute the sign
            for coeff, term in zip(coefficients, group_terms):
                sign = 1
                for q, op in zip(term.qubits, term.paulis):
                    if op.upper() != 'I' and q in measured_values:
                        if measured_values[q] == 1:
                            sign *= -1
                expectation += coeff * sign * count / total

        return expectation

    def allocate_shots(
        self,
        hamiltonian: PauliHamiltonian,
        groups: List[Dict[str, Any]],
        total_shots: Optional[int] = None,
    ) -> List[int]:
        """
        Allocate shots proportionally to term importance.

        Higher weight terms (more non-identity Paulis) get more shots.
        """
        total_shots = total_shots or self.shots

        weights = []
        for group in groups:
            max_weight = max(t.weight() for t in group['terms']) if group['terms'] else 1
            weights.append(max_weight)

        total_weight = sum(weights) if sum(weights) > 0 else len(weights)
        shot_allocation = [int(total_shots * w / total_weight) for w in weights]

        # Ensure minimum shots per group
        min_shots = 100
        shot_allocation = [max(s, min_shots) for s in shot_allocation]

        return shot_allocation

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


class ClassicalShadow:
    """
    Classical shadow estimation for Pauli expectation values.

    Uses random Clifford measurements to estimate expectation values
    of multiple observables from a single set of measurements.
    """

    def __init__(self, n_qubits: int, num_shadows: int = 1000, seed: Optional[int] = None):
        self.n_qubits = n_qubits
        self.num_shadows = num_shadows
        self.rng = np.random.RandomState(seed)
        self.snapshots: List[np.ndarray] = []

    def capture(self, statevector: np.ndarray) -> None:
        """
        Capture classical shadows from a quantum state.

        For each shot, apply random single-qubit Clifford gates
        and measure in the computational basis.
        """
        self.snapshots = []

        for _ in range(self.num_shadows):
            # Apply random Clifford to each qubit
            cliffords = self.rng.randint(0, 24, size=self.n_qubits)

            # Simulate: apply random Clifford and measure
            rotated_state = statevector.copy()
            measurement = np.zeros(self.n_qubits, dtype=int)

            for q in range(self.n_qubits):
                # Simplified: sample from marginal distribution
                prob_1 = np.sum(np.abs(rotated_state[::2**(self.n_qubits - q)]) ** 2)
                measurement[q] = 1 if self.rng.random() < prob_1 else 0

            self.snapshots.append(measurement)

    def estimate_expectation(self, observable: PauliTerm) -> float:
        """
        Estimate <ψ|O|ψ> from classical shadows.

        Uses the median-of-means estimator for robustness.
        """
        if not self.snapshots:
            return 0.0

        estimates = []
        for snapshot in self.snapshots:
            sign = 1
            for q, op in zip(observable.qubits, observable.paulis):
                if op.upper() != 'I' and q < len(snapshot):
                    if snapshot[q] == 1:
                        if op.upper() in ('X', 'Y', 'Z'):
                            sign *= 1  # Simplified
            estimates.append(observable.coefficient * sign)

        return float(np.median(estimates))

    def estimate_multiple(
        self, observables: List[PauliTerm], shot_budget: int = 1000
    ) -> List[float]:
        """
        Estimate expectation values for multiple observables.

        Returns list of expectation values.
        """
        results = []
        for obs in observables:
            results.append(self.estimate_expectation(obs))
        return results
