import numpy as np
from typing import List, Union, Optional
import itertools

class QuantumVirtualMachine:
    """
    A state-vector based quantum virtual machine.
    Supports up to 30+ qubits on CPU.
    """
    
    def __init__(self, num_qubits: int):
        """
        Initialize the QVM with |0...0> state.
        
        Args:
            num_qubits: Number of qubits in the system
        """
        if num_qubits < 1:
            raise ValueError("Number of qubits must be at least 1")
        if num_qubits > 30:
            # Warning for CPU limitation, but allow for GPU extension later
            print(f"Warning: {num_qubits} qubits may exceed CPU memory limits. Consider using GPU backend.")
        
        self.num_qubits = num_qubits
        self.state = np.zeros(2**num_qubits, dtype=complex)
        self.state[0] = 1.0  # |0...0> state
        
    def apply_gate(self, gate_matrix: np.ndarray, target_qubits: List[int],
                   control_qubits: Optional[List[int]] = None) -> None:
        """
        Apply a quantum gate to the state vector.
        
        Args:
            gate_matrix: Unitary matrix representing the gate (2^k x 2^k for k target qubits)
            target_qubits: List of target qubit indices (0-indexed)
            control_qubits: List of control qubit indices (0-indexed), optional
        """
        # Validate inputs
        k = len(target_qubits)
        expected_shape = (2**k, 2**k)
        if gate_matrix.shape != expected_shape:
            raise ValueError(f"Gate matrix must be shape {expected_shape}, got {gate_matrix.shape}")
        
        # For now, we'll implement without controls for simplicity
        # In a full implementation, we'd handle controls by expanding the gate
        if control_qubits is not None and len(control_qubits) > 0:
            raise NotImplementedError("Controlled gates not yet implemented in basic QVM")
            
        # Apply the gate to the state vector
        self.state = self._apply_gate_to_state(gate_matrix, target_qubits)
        
    def _apply_gate_to_state(self, gate_matrix: np.ndarray, target_qubits: List[int]) -> np.ndarray:
        """
        Internal method to apply gate to state vector.
        Uses tensor product approach.
        """
        # Reshape state vector to tensor of shape (2, 2, ..., 2)
        tensor_shape = (2,) * self.num_qubits
        state_tensor = self.state.reshape(tensor_shape)
        
        # Prepare axes for tensordot
        # We want to contract the gate matrix with the target qubits
        gate_axes = list(range(len(target_qubits)))  # Axes of gate_matrix to contract
        target_axes = [self.num_qubits - 1 - q for q in target_qubits]  # Axes in state_tensor (little-endian)
        
        # Apply gate using tensordot
        new_tensor = np.tensordot(gate_matrix, state_tensor, 
                                  axes=(gate_axes, target_axes))
        
        # The result has shape: (2, ..., 2) with the target qubit dimensions replaced
        # We need to move the new dimensions to the correct positions
        # Actually, tensordot already puts the uncontracted dimensions of gate_matrix first,
        # followed by the uncontracted dimensions of state_tensor.
        # Since we contracted all of gate_matrix, the result has the shape of state_tensor
        # but with the target qubit dimensions replaced by the gate's output dimensions (which are same size).
        # So we just need to reshape back.
        return new_tensor.reshape(-1)
    
    def measure(self, num_shots: int = 1024) -> List[int]:
        """
        Measure the quantum state in the computational basis.
        
        Args:
            num_shots: Number of measurement shots
            
        Returns:
            List of measurement outcomes (each outcome is an integer representing the bitstring)
        """
        probabilities = np.abs(self.state)**2
        # Normalize to handle any numerical errors
        probabilities = probabilities / np.sum(probabilities)
        
        # Sample from the distribution
        outcomes = np.random.choice(
            len(self.state), 
            size=num_shots, 
            p=probabilities
        )
        
        # Convert to list of integers
        return outcomes.tolist()
    
    def get_statevector(self) -> np.ndarray:
        """
        Get the current state vector.
        
        Returns:
            Copy of the state vector
        """
        return self.state.copy()
    
    def get_probabilities(self) -> np.ndarray:
        """
        Get the measurement probabilities for each basis state.
        
        Returns:
            Array of probabilities
        """
        return np.abs(self.state)**2
    
    def reset(self) -> None:
        """Reset the state to |0...0>."""
        self.state = np.zeros(2**self.num_qubits, dtype=complex)
        self.state[0] = 1.0

# Example usage and basic tests
if __name__ == "__main__":
    # Create a 2-qubit QVM
    qvm = QuantumVirtualMachine(2)
    print("Initial state:", qvm.get_statevector())
    
    # Apply X gate to qubit 0
    x_gate = np.array([[0, 1], [1, 0]], dtype=complex)
    qvm.apply_gate(x_gate, [0])
    print("After X on q0:", qvm.get_statevector())
    
    # Apply H gate to qubit 1
    h_gate = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    qvm.apply_gate(h_gate, [1])
    print("After H on q1:", qvm.get_statevector())
    
    # Measure
    measurements = qvm.measure(10)
    print("Measurements:", measurements)