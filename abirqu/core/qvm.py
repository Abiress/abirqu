"""
Quantum Virtual Machine - Core simulation engine for AbirQu
Copyright 2026 Abir Maheshwari
"""
import numpy as np
from typing import List, Optional, Dict, Any, Tuple

class QuantumVirtualMachine:
    """Simulates quantum circuits with state vector evolution."""
    
    def __init__(self, num_qubits: int, use_gpu: bool = False):
        self.num_qubits = num_qubits
        self.use_gpu = use_gpu
        self.state = self._initialize_state()
        self.measurements = {}
        
    def _initialize_state(self) -> np.ndarray:
        """Initialize |00...0> state."""
        state = np.zeros(2**self.num_qubits, dtype=complex)
        state[0] = 1.0 + 0j
        return state
        
    def apply_gate(self, gate: Gate, qubits: List[int]):
        """Apply a gate to specified qubits."""
        n = self.num_qubits
        # Build full unitary matrix from gate's matrix
        full_unitary = self._expand_gate(gate.matrix, qubits)
        self.state = full_unitary @ self.state
        
    def _expand_gate(self, gate_matrix: np.ndarray, qubits: List[int]) -> np.ndarray:
        """Expand gate matrix to full system size."""
        n = self.num_qubits
        gate_size = len(qubits)
        
        # Start with identity
        full = np.eye(2**n, dtype=complex)
        
        # Build the permutation matrix for the gate
        if gate_size == 1:
            # Single qubit gate
            q = qubits[0]
            op = gate_matrix
            full = self._single_qubit_op(op, q)
        elif gate_size == 2:
            # Two qubit gate
            q1, q2 = qubits[0], qubits[1]
            op = gate_matrix
            full = self._two_qubit_op(op, q1, q2)
        elif gate_size == 3:
            # Three qubit gate (Toffoli)
            q1, q2, q3 = qubits[0], qubits[1], qubits[2]
            full = self._three_qubit_op(gate_matrix, q1, q2, q3)
            
        return full
        
    def _single_qubit_op(self, op: np.ndarray, qubit: int) -> np.ndarray:
        """Apply single qubit operation."""
        n = self.num_qubits
        result = np.zeros((2**n, 2**n), dtype=complex)
        
        for i in range(2**n):
            # Get the bit at position qubit
            bit = (i >> (n - 1 - qubit)) & 1
            # Apply operator
            for j in range(2):
                new_state = i & ~(1 << (n - 1 - qubit))  # Clear bit
                new_state |= (j << (n - 1 - qubit))  # Set new bit
                result[new_state, i] = op[j, bit]
                
        return result
        
    def _two_qubit_op(self, op: np.ndarray, q1: int, q2: int) -> np.ndarray:
        """Apply two qubit operation."""
        n = self.num_qubits
        result = np.zeros((2**n, 2**n), dtype=complex)
        
        for i in range(2**n):
            bit1 = (i >> (n - 1 - q1)) & 1
            bit2 = (i >> (n - 1 - q2)) & 1
            old_bits = (bit1 << 1) | bit2
            
            for j in range(4):
                new_state = i
                new_bit1 = (j >> 1) & 1
                new_bit2 = j & 1
                new_state = (new_state & ~(1 << (n - 1 - q1))) | (new_bit1 << (n - 1 - q1))
                new_state = (new_state & ~(1 << (n - 1 - q2))) | (new_bit2 << (n - 1 - q2))
                result[new_state, i] = op[j, old_bits]
                
        return result
        
    def _three_qubit_op(self, op: np.ndarray, q1: int, q2: int, q3: int) -> np.ndarray:
        """Apply three qubit operation (Toffoli)."""
        n = self.num_qubits
        result = np.eye(2**n, dtype=complex)
        
        # Toffoli: flip q3 if q1 and q2 are both 1
        for i in range(2**n):
            bit1 = (i >> (n - 1 - q1)) & 1
            bit2 = (i >> (n - 1 - q2)) & 1
            bit3 = (i >> (n - 1 - q3)) & 1
            
            if bit1 == 1 and bit2 == 1:
                # Flip q3
                new_state = i ^ (1 << (n - 1 - q3))
                result[new_state, i] = 1
                result[i, i] = 0
                
        return result
        
    def measure(self, qubit: int) -> int:
        """Measure a qubit, collapsing the state."""
        n = self.num_qubits
        # Calculate probability of |1>
        prob_1 = 0.0
        for i in range(2**n):
            if ((i >> (n - 1 - qubit)) & 1) == 1:
                prob_1 += abs(self.state[i])**2
                
        # Collapse
        if np.random.random() < prob_1:
            result = 1
            # Project to |1> subspace
            for i in range(2**n):
                if ((i >> (n - 1 - qubit)) & 1) == 0:
                    self.state[i] = 0
        else:
            result = 0
            # Project to |0> subspace
            for i in range(2**n):
                if ((i >> (n - 1 - qubit)) & 1) == 1:
                    self.state[i] = 0
                    
        # Renormalize
        norm = np.sqrt(np.sum(np.abs(self.state)**2))
        if norm > 0:
            self.state /= norm
            
        self.measurements[qubit] = result
        return result
        
    def measure_all(self) -> List[int]:
        """Measure all qubits."""
        return [self.measure(q) for q in range(self.num_qubits)]
        
    def get_statevector(self) -> np.ndarray:
        """Return current state vector."""
        return self.state.copy()
        
    def get_probabilities(self) -> Dict[str, float]:
        """Get measurement probabilities for all basis states."""
        n = self.num_qubits
        probs = {}
        for i in range(2**n):
            if abs(self.state[i])**2 > 1e-10:
                basis = format(i, f'0{n}b')
                probs[basis] = abs(self.state[i])**2
        return probs
