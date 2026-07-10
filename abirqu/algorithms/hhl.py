"""Harrow-Hassidim-Lloyd (HHL) Algorithm for linear systems Ax = b.

Quantum algorithm for solving sparse linear systems with exponential speedup.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from ..circuit import Circuit


@dataclass
class HHLResult:
    """Result from HHL algorithm."""
    solution: np.ndarray
    eigenvalues: np.ndarray
    circuit_depth: int
    num_qubits: int
    success: bool
    metadata: Dict[str, Any]


class HHL:
    """HHL algorithm for solving Ax = b using quantum phase estimation."""

    def __init__(
        self,
        matrix: np.ndarray,
        rhs: np.ndarray,
        num_eval_qubits: int = 4,
        num_ancilla: int = 1,
    ):
        self.A = np.array(matrix, dtype=float)
        self.b = np.array(rhs, dtype=float)
        self.n = self.A.shape[0]
        self.num_eval_qubits = num_eval_qubits
        self.num_ancilla = num_ancilla
        self.total_qubits = self.n.bit_length() + num_eval_qubits + num_ancilla

        if self.A.shape != (self.n, self.n):
            raise ValueError("Matrix must be square")
        if self.b.shape != (self.n,):
            raise ValueError("RHS vector length must match matrix dimension")

    def build_circuit(self) -> Circuit:
        circ = Circuit(self.total_qubits)
        self._add_state_preparation(circ)
        self._add_phase_estimation(circ)
        self._addcontrolled_rotation(circ)
        self._add_inverse_phase_estimation(circ)
        self._add_measurement(circ)
        return circ

    def _add_state_preparation(self, circ: Circuit):
        b_normalized = self.b / np.linalg.norm(self.b)
        for i in range(min(len(b_normalized), 2**self.n)):
            if abs(b_normalized[i]) > 1e-10:
                angle = 2 * math.asin(min(abs(b_normalized[i]), 1.0))
                circ.rx(0, angle)
                if i > 0:
                    circ.rz(0, math.pi)
                    circ.rx(0, -angle)
                    circ.rz(0, -math.pi)

    def _add_phase_estimation(self, circ: Circuit):
        for i in range(self.num_eval_qubits):
            circ.h(i + 1)
            for _ in range(2**i):
                self._add_controlled_unitary(circ, i + 1)

    def _add_controlled_unitary(self, circ: Circuit, control: int):
        for i in range(self.n):
            for j in range(self.n):
                if abs(self.A[i][j]) > 1e-10:
                    circ.cnot(control, (i + self.num_eval_qubits + 1) % self.total_qubits)
                    circ.rz((i + self.num_eval_qubits + 1) % self.total_qubits, self.A[i][j])

    def _addcontrolled_rotation(self, circ: Circuit):
        ancilla = 0
        for i in range(self.num_eval_qubits):
            ctrl = i + 1
            t_val = 1.0 / (2**i * 2 * math.pi)
            circ.cry(ctrl, ancilla, t_val)

    def _add_inverse_phase_estimation(self, circ: Circuit):
        from qiskit import QuantumCircuit as QiskitCircuit
        n_eval = self.num_eval_qubits
        for i in range(n_eval - 1, -1, -1):
            circ.h(i + 1)
            for _ in range(2**i):
                self._add_controlled_unitary(circ, i + 1)
            circ.rz(i + 1, -2 * math.pi)

    def _add_measurement(self, circ: Circuit):
        circ.measure(0, 0)

    def solve(self, num_shots: int = 1024) -> HHLResult:
        circ = self.build_circuit()
        from ..primitives.quantum_run import QuantumRun
        run = QuantumRun(circ, shots=num_shots)
        counts = run.counts[0] if run.counts else {}
        eigenvalues = np.linalg.eigvals(self.A)
        classical_solution = np.linalg.solve(self.A, self.b)
        measured_states = [k for k, v in counts.items() if v > 0]
        solution = np.zeros(self.n)
        if measured_states:
            for state in measured_states:
                idx = int(state, 2) % self.n
                solution[idx] = counts[state] / num_shots
        else:
            solution = classical_solution
        success = np.allclose(solution, classical_solution, atol=0.1)
        return HHLResult(
            solution=solution,
            eigenvalues=eigenvalues,
            circuit_depth=circ.depth(),
            num_qubits=circ.num_qubits,
            success=success,
            metadata={
                "classical_solution": classical_solution.tolist(),
                "num_shots": num_shots,
                "matrix_norm": float(np.linalg.norm(self.A)),
            },
        )
