"""
Measurement Engine for AbirQu
Copyright 2026 Abir Maheshwari
"""
import numpy as np
from typing import List, Dict, Optional, Tuple

class Measurement:
    """Quantum measurement operations."""
    
    def __init__(self, qubit: int, cbit: Optional[int] = None):
        self.qubit = qubit
        self.cbit = cbit if cbit is not None else qubit
        
    @staticmethod
    def measure_state(state: np.ndarray, qubit: int) -> Tuple[int, np.ndarray]:
        """Measure a qubit in the computational basis with state collapse."""
        num_qubits = int(np.log2(len(state)))
        block_size = 2**(num_qubits - qubit - 1)
        
        # Calculate probability of |0>
        prob_0 = 0.0
        for i in range(len(state)):
            if ((i >> (num_qubits - 1 - qubit)) & 1) == 0:
                prob_0 += abs(state[i])**2
                
        prob_1 = 1.0 - prob_0
        
        # Perform measurement
        if np.random.random() < prob_0 and prob_0 > 0:
            result = 0
            # Collapse to |0> subspace
            new_state = np.zeros_like(state)
            norm = 0.0
            for i in range(len(state)):
                if ((i >> (num_qubits - 1 - qubit)) & 1) == 0:
                    new_state[i] = state[i]
                    norm += abs(state[i])**2
            if norm > 0:
                new_state /= np.sqrt(norm)
            return result, new_state
        else:
            result = 1
            # Collapse to |1> subspace
            new_state = np.zeros_like(state)
            norm = 0.0
            for i in range(len(state)):
                if ((i >> (num_qubits - 1 - qubit)) & 1) == 1:
                    new_state[i] = state[i]
                    norm += abs(state[i])**2
            if norm > 0 and prob_1 > 0:
                new_state /= np.sqrt(norm)
            return result, new_state
            
    @staticmethod
    def measure_all(state: np.ndarray) -> List[int]:
        """Measure all qubits."""
        num_qubits = int(np.log2(len(state)))
        result = []
        current_state = state.copy()
        
        for q in range(num_qubits):
            bit, current_state = Measurement.measure_state(current_state, q)
            result.append(bit)
            
        return result
        
    @staticmethod
    def measure_observable(state: np.ndarray, observable: np.ndarray, qubit: int) -> float:
        """Measure expectation value of an observable."""
        # Reshape state as column vector
        psi = state.reshape(-1, 1)
        # Calculate <psi|observable|psi>
        expectation = np.conj(psi).T @ observable @ psi
        return np.real(expectation[0, 0])
        
    @staticmethod
    def get_probabilities(state: np.ndarray, qubit: int) -> Dict[int, float]:
        """Get measurement probabilities for a qubit."""
        num_qubits = int(np.log2(len(state)))
        probs = {0: 0.0, 1: 0.0}
        
        for i in range(len(state)):
            bit = (i >> (num_qubits - 1 - qubit)) & 1
            probs[bit] += abs(state[i])**2
            
        return probs
        
    @staticmethod
    def measure_in_basis(state: np.ndarray, basis: np.ndarray, qubit: int) -> Tuple[int, float]:
        """Measure in an arbitrary basis."""
        # Transform state to new basis
        # Simplified: assume basis is |0> or |1> rotated state
        prob_0 = abs(state[0])**2 if len(state) > 0 else 0.5
        
        if np.random.random() < prob_0:
            return 0, prob_0
        else:
            return 1, 1 - prob_0
