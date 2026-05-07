import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from collections import Counter
import random

class MeasurementResult:
    """Container for measurement results."""
    
    def __init__(self, shots: int, bitstring_counts: Dict[str, int], 
                 qubit_indices: List[int]):
        """
        Initialize measurement result.
        
        Args:
            shots: Number of shots
            bitstring_counts: Dict mapping bitstring to count
            qubit_indices: List of measured qubit indices
        """
        self.shots = shots
        self.counts = bitstring_counts
        self.qubit_indices = qubit_indices
        
    def get_counts(self) -> Dict[str, int]:
        """Get raw counts."""
        return self.counts.copy()
    
    def get_probabilities(self) -> Dict[str, float]:
        """Get empirical probabilities from counts."""
        return {k: v / self.shots for k, v in self.counts.items()}
    
    def most_frequent(self) -> str:
        """Return the most frequently observed bitstring."""
        return max(self.counts, key=self.counts.get)
    
    def expectation_z(self) -> float:
        """
        Estimate expectation value of Z on all measured qubits.
        Assumes computational basis measurement.
        For single qubit: returns <Z> = P(0) - P(1)
        For multiple qubits: returns product of individual expectations (if independent)
        """
        probs = self.get_probabilities()
        exp_val = 0.0
        
        if len(self.qubit_indices) == 1:
            # Single qubit
            p0 = sum(v/shots for k, v in self.counts.items() if k == '0')
            p1 = sum(v/shots for k, v in self.counts.items() if k == '1')
            return p0 - p1
        else:
            # Multiple qubits - compute parity-based expectation
            # <Z1⊗Z2⊗...⊗Zn> = sum over bitstrings of (-1)^(# of 1s) * prob
            exp_val = 0.0
            for bitstring, count in self.counts.items():
                parity = bitstring.count('1')
                sign = 1 if parity % 2 == 0 else -1
                exp_val += sign * (count / self.shots)
            return exp_val
    
    def __repr__(self):
        return f"MeasurementResult(shots={self.shots}, unique_states={len(self.counts)})"

class SamplingEngine:
    """
    Engine for shot-based sampling and expectation value estimation.
    Supports mid-circuit measurement and classical feedback.
    """
    
    def __init__(self, num_qubits: int):
        """
        Initialize sampling engine.
        
        Args:
            num_qubits: Number of qubits in the system
        """
        self.num_qubits = num_qubits
        self.classical_bits: Dict[int, int] = {}  # cbit index -> value (0 or 1)
        
    def sample(self, state_vector: np.ndarray, 
               measured_qubits: List[int],
               shots: int = 1024,
               collapse: bool = False) -> MeasurementResult:
        """
        Perform shot-based sampling of the quantum state.
        
        Args:
            state_vector: Current quantum state vector
            measured_qubits: List of qubits to measure
            shots: Number of measurement shots
            collapse: If True, collapse state after each shot (for mid-circuit measurements)
            
        Returns:
            MeasurementResult object
        """
        if collapse:
            # Mid-circuit measurement: collapse state after each shot
            return self._sample_with_collapse(state_vector, measured_qubits, shots)
        else:
            # Standard measurement without collapse
            return self._sample_no_collapse(state_vector, measured_qubits, shots)
    
    def _sample_no_collapse(self, state_vector: np.ndarray, 
                           measured_qubits: List[int], 
                           shots: int) -> MeasurementResult:
        """Sample without collapsing the state."""
        # Compute probabilities for each possible outcome of measured qubits
        # We need to sum over unmeasured qubits
        
        num_qubits = int(np.log2(len(state_vector)))
        measured_qubits_sorted = sorted(measured_qubits)
        
        # Create mapping from measured qubit indices to bit positions
        qubit_to_pos = {q: i for i, q in enumerate(measured_qubits_sorted)}
        
        # Compute probability for each possible bitstring of measured qubits
        prob_dict = {}
        
        for idx in range(len(state_vector)):
            # Determine the bit values of measured qubits for this basis state
            bitstring_parts = []
            for q in measured_qubits_sorted:
                # Extract bit value for qubit q (little-endian: qubit 0 is LSB)
                bit = (idx >> (num_qubits - 1 - q)) & 1
                bitstring_parts.append(str(bit))
            bitstring = ''.join(bitstring_parts)
            
            prob = np.abs(state_vector[idx])**2
            prob_dict[bitstring] = prob_dict.get(bitstring, 0) + prob
            
        # Normalize to handle numerical errors
        total = sum(prob_dict.values())
        prob_dict = {k: v/total for k, v in prob_dict.items()}
        
        # Sample from the distribution
        bitstrings = list(prob_dict.keys())
        probs = list(prob_dict.values())
        
        samples = np.random.choice(bitstrings, size=shots, p=probs)
        counts = Counter(samples)
        
        return MeasurementResult(shots, dict(counts), measured_qubits_sorted)
    
    def _sample_with_collapse(self, state_vector: np.ndarray,
                             measured_qubits: List[int],
                             shots: int) -> MeasurementResult:
        """Sample with state collapse (for mid-circuit measurements)."""
        # This is more complex - each shot collapses the state
        # For simplicity, we'll implement a basic version
        
        num_qubits = self.num_qubits
        measured_qubits_sorted = sorted(measured_qubits)
        
        all_counts = Counter()
        
        for _ in range(shots):
            # Copy state for this shot
            current_state = state_vector.copy()
            
            # Measure qubits one by one
            outcome_bits = []
            for q in measured_qubits_sorted:
                # Compute probability of measuring 0 or 1 for qubit q
                p0, p1 = self._qubit_probability(current_state, q, num_qubits)
                
                # Collapse to outcome
                if np.random.random() < p1:
                    # Measure 1
                    current_state = self._collapse_qubit(current_state, q, 1, num_qubits)
                    outcome_bits.append('1')
                else:
                    # Measure 0
                    current_state = self._collapse_qubit(current_state, q, 0, num_qubits)
                    outcome_bits.append('0')
                    
            bitstring = ''.join(outcome_bits)
            all_counts[bitstring] += 1
            
        return MeasurementResult(shots, dict(all_counts), measured_qubits_sorted)
    
    def _qubit_probability(self, state: np.ndarray, qubit: int, 
                          num_qubits: int) -> Tuple[float, float]:
        """Compute probability of measuring 0 or 1 for a specific qubit."""
        p0 = 0.0
        p1 = 0.0
        
        mask = 1 << (num_qubits - 1 - qubit)
        
        for i in range(len(state)):
            prob = np.abs(state[i])**2
            if i & mask:
                p1 += prob
            else:
                p0 += prob
                
        return p0, p1
    
    def _collapse_qubit(self, state: np.ndarray, qubit: int, 
                       outcome: int, num_qubits: int) -> np.ndarray:
        """Collapse state after measuring qubit to outcome (0 or 1)."""
        mask = 1 << (num_qubits - 1 - qubit)
        new_state = np.zeros_like(state)
        
        total_prob = 0.0
        for i in range(len(state)):
            bit = (i & mask) >> (num_qubits - 1 - qubit)
            if bit == outcome:
                new_state[i] = state[i]
                total_prob += np.abs(state[i])**2
                
        # Normalize
        if total_prob > 0:
            new_state = new_state / np.sqrt(total_prob)
            
        return new_state
    
    def estimate_expectation(self, state_vector: np.ndarray,
                            observable: np.ndarray,
                            shots: int = 10000) -> float:
        """
        Estimate expectation value <ψ|H|ψ> without full tomography.
        
        Args:
            state_vector: Quantum state
            observable: Hermitian matrix representing observable
            shots: Number of shots for estimation
            
        Returns:
            Estimated expectation value
        """
        # For efficiency, we can use the fact that <ψ|H|ψ> = sum_i λ_i p_i
        # where λ_i are eigenvalues and p_i are measurement probabilities in eigenbasis
        
        # Diagonalize the observable
        eigenvalues, eigenvectors = np.linalg.eigh(observable)
        
        # Transform state to eigenbasis
        state_eigen = eigenvectors.conj().T @ state_vector
        
        # Probabilities in eigenbasis
        probs = np.abs(state_eigen)**2
        
        # Sample from distribution
        eigen_indices = np.random.choice(len(eigenvalues), size=shots, p=probs)
        
        # Estimate expectation
        expectation = np.mean(eigenvalues[eigen_indices])
        
        return float(expectation)
    
    def set_classical_bit(self, cbit: int, value: int) -> None:
        """Set a classical bit value (for classical feedback)."""
        self.classical_bits[cbit] = value
        
    def get_classical_bit(self, cbit: int) -> Optional[int]:
        """Get a classical bit value."""
        return self.classical_bits.get(cbit)

# Example usage and tests
if __name__ == "__main__":
    print("Testing Measurement and Sampling Engine...")
    
    # Create a Bell state: (|00> + |11>)/sqrt(2)
    num_qubits = 2
    state = np.zeros(2**num_qubits, dtype=complex)
    state[0] = 1/np.sqrt(2)  # |00>
    state[3] = 1/np.sqrt(2)  # |11>
    
    print("Bell state created.")
    print(f"State vector: {state}")
    
    # Create sampling engine
    engine = SamplingEngine(num_qubits)
    
    # Sample measurements
    result = engine.sample(state, [0, 1], shots=1024)
    print(f"\nMeasurement result: {result}")
    print(f"Counts: {result.get_counts()}")
    print(f"Probabilities: {result.get_probabilities()}")
    print(f"Expectation <Z⊗Z>: {result.expectation_z():.3f}")
    print(f"Most frequent: {result.most_frequent()}")
    
    # Test expectation value estimation
    # Pauli Z observable for single qubit
    z_op = np.array([[1, 0], [0, -1]], dtype=complex)
    z_full = np.kron(z_op, np.eye(2))  # Z on qubit 0
    
    expectation = engine.estimate_expectation(state, z_full, shots=5000)
    print(f"\nExpectation <I⊗Z> (should be 0 for Bell state): {expectation:.3f}")
    
    # Test mid-circuit measurement (collapse)
    print("\nTesting mid-circuit measurement with collapse...")
    result_collapse = engine.sample(state, [0], shots=100, collapse=True)
    print(f"Counts after collapse: {result_collapse.get_counts()}")