"""
Noise Model for AbirQu - Real Kraus operator implementations
Copyright 2026 Abir Maheshwari
"""

import numpy as np
from typing import List, Dict, Optional, Tuple


class NoiseModel:
    """Quantum noise model with various error channels."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.error_rates: Dict[str, float] = {}
        self.t1: Optional[float] = None  # Relaxation time (µs)
        self.t2: Optional[float] = None  # Dephasing time (µs)
        self.gate_times: Dict[str, float] = {'single': 0.1, 'two': 0.3}  # µs

    def add_depolarizing_noise(self, gate: str, error_rate: float):
        """Add depolarizing noise channel."""
        self.error_rates[gate] = error_rate

    def add_amplitude_damping(self, t1: float):
        """Add amplitude damping (T1) noise."""
        self.t1 = t1

    def add_phase_damping(self, t2: float):
        """Add phase damping (T2) noise."""
        self.t2 = t2

    def get_depolarizing_kraus(self, error_rate: float) -> List[np.ndarray]:
        """Get Kraus operators for depolarizing channel."""
        p = error_rate
        I = np.eye(2, dtype=complex)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)

        K0 = np.sqrt(1 - 3*p/4) * I
        K1 = np.sqrt(p/4) * X
        K2 = np.sqrt(p/4) * Y
        K3 = np.sqrt(p/4) * Z
        return [K0, K1, K2, K3]

    def get_amplitude_damping_kraus(self, gamma: float) -> List[np.ndarray]:
        """Get Kraus operators for amplitude damping."""
        sqrt_1_minus_gamma = np.sqrt(1 - gamma)
        sqrt_gamma = np.sqrt(gamma)
        K0 = np.array([[1, 0], [0, sqrt_1_minus_gamma]], dtype=complex)
        K1 = np.array([[0, sqrt_gamma], [0, 0]], dtype=complex)
        return [K0, K1]

    def get_phase_damping_kraus(self, gamma: float) -> List[np.ndarray]:
        """Get Kraus operators for phase damping."""
        sqrt_1_minus_gamma = np.sqrt(1 - gamma)
        sqrt_gamma = np.sqrt(gamma)
        K0 = np.array([[1, 0], [0, sqrt_1_minus_gamma]], dtype=complex)
        K1 = np.array([[0, 0], [0, sqrt_gamma]], dtype=complex)
        return [K0, K1]

    def _embed_single_qubit_op(self, op: np.ndarray, qubit: int, state_dim: int) -> np.ndarray:
        """Embed single-qubit operator in full Hilbert space."""
        num_qubits = int(np.log2(state_dim))
        if num_qubits <= 0:
            return op
        ops = []
        for q in range(num_qubits):
            if q == qubit:
                ops.append(op)
            else:
                ops.append(np.eye(2, dtype=complex))
        # Tensor product
        result = ops[0]
        for op in ops[1:]:
            result = np.kron(result, op)
        return result

    def apply_noise(self, state: np.ndarray, gate_name: str = None) -> np.ndarray:
        """Apply depolarizing noise to a quantum state using Kraus operators."""
        if state is None or len(state) == 0:
            return state

        # Apply depolarizing noise if gate specified
        if gate_name and gate_name in self.error_rates:
            p = self.error_rates[gate_name]
            if p > 0:
                # Get Kraus operators for depolarizing channel
                kraus_ops = self.get_depolarizing_kraus(p)

                # For pure state |ψ>, sample which Kraus operator applies
                # Σ_i p_i = 1 where p_i = ||K_i|ψ>||^2
                probabilities = []
                new_states = []

                for K in kraus_ops:
                    # Embed single-qubit Kraus operator in full Hilbert space (qubit 0)
                    K_full = self._embed_single_qubit_op(K, 0, len(state))
                    # Apply: |ψ'> = K|ψ>
                    psi_prime = K_full @ state
                    prob = np.linalg.norm(psi_prime)**2
                    probabilities.append(prob)
                    new_states.append(psi_prime)

                # Normalize probabilities
                total_prob = sum(probabilities)
                if total_prob > 0:
                    probabilities = [p/total_prob for p in probabilities]
                else:
                    probabilities = [1.0/len(kraus_ops)] * len(kraus_ops)

                # Sample which Kraus operator to apply
                idx = np.random.choice(len(kraus_ops), p=probabilities)
                state = new_states[idx]
                # Normalize
                norm = np.linalg.norm(state)
                if norm > 0:
                    state = state / norm

        return state

    def apply_t1_noise(self, state: np.ndarray, time: float) -> np.ndarray:
        """Apply T1 (amplitude damping) noise using proper Kraus channel."""
        if self.t1 is None or self.t1 == 0 or state is None or len(state) == 0:
            return state

        gamma = 1 - np.exp(-time / self.t1)
        if gamma <= 0:
            return state

        # Get Kraus operators for amplitude damping
        kraus_ops = self.get_amplitude_damping_kraus(gamma)

        # For pure state, sample which Kraus operator applies
        probabilities = []
        new_states = []

        for K in kraus_ops:
            # Embed single-qubit Kraus operator in full Hilbert space (qubit 0)
            K_full = self._embed_single_qubit_op(K, 0, len(state))
            # Apply: |ψ'> = K|ψ>
            psi_prime = K_full @ state
            prob = np.linalg.norm(psi_prime)**2
            probabilities.append(prob)
            new_states.append(psi_prime)

        # Normalize probabilities
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p/total_prob for p in probabilities]
        else:
            probabilities = [0.5, 0.5]

        # Sample which Kraus operator to apply
        idx = np.random.choice(len(kraus_ops), p=probabilities)
        state = new_states[idx]
        # Normalize
        norm = np.linalg.norm(state)
        if norm > 0:
            state = state / norm

        return state

    def apply_t2_noise(self, state: np.ndarray, time: float) -> np.ndarray:
        """Apply T2 (phase damping) noise using proper Kraus channel."""
        if self.t2 is None or self.t2 == 0 or state is None or len(state) == 0:
            return state

        gamma = 1 - np.exp(-time / self.t2)
        if gamma <= 0:
            return state

        # Get Kraus operators for phase damping
        kraus_ops = self.get_phase_damping_kraus(gamma)

        # For pure state, sample which Kraus operator applies
        probabilities = []
        new_states = []

        for K in kraus_ops:
            # Embed single-qubit Kraus operator in full Hilbert space (qubit 0)
            K_full = self._embed_single_qubit_op(K, 0, len(state))
            # Apply: |ψ'> = K|ψ>
            psi_prime = K_full @ state
            prob = np.linalg.norm(psi_prime)**2
            probabilities.append(prob)
            new_states.append(psi_prime)

        # Normalize probabilities
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p/total_prob for p in probabilities]
        else:
            probabilities = [0.5, 0.5]

        # Sample which Kraus operator to apply
        idx = np.random.choice(len(kraus_ops), p=probabilities)
        state = new_states[idx]
        # Normalize
        norm = np.linalg.norm(state)
        if norm > 0:
            state = state / norm

        return state

    def get_total_error_rate(self, gate: str) -> float:
        """Get total error rate for a gate."""
        return self.error_rates.get(gate, 0.0)

    def __repr__(self):
        return f"NoiseModel({self.name}, gates={len(self.error_rates)}, T1={self.t1}, T2={self.t2})"
