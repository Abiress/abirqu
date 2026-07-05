import numpy as np
from typing import List, Union, Tuple, Dict, Any
import itertools

# Standard quantum gates as unitary matrices
I = np.array([[1, 0], [0, 1]], dtype=complex)  # Identity
X = np.array([[0, 1], [1, 0]], dtype=complex)  # Pauli-X (NOT)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)  # Pauli-Y
Z = np.array([[1, 0], [0, -1]], dtype=complex)  # Pauli-Z

H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)  # Hadamard

S = np.array([[1, 0], [0, 1j]], dtype=complex)  # Phase gate (S)
S_dag = np.array([[1, 0], [0, -1j]], dtype=complex)  # S dagger

T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)  # T gate (pi/8)
T_dag = np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex)  # T dagger

# RX, RY, RZ rotation gates
def rx(theta: float) -> np.ndarray:
    """Rotation around X axis."""
    return np.array([
        [np.cos(theta/2), -1j*np.sin(theta/2)],
        [-1j*np.sin(theta/2), np.cos(theta/2)]
    ], dtype=complex)

def ry(theta: float) -> np.ndarray:
    """Rotation around Y axis."""
    return np.array([
        [np.cos(theta/2), -np.sin(theta/2)],
        [np.sin(theta/2), np.cos(theta/2)]
    ], dtype=complex)

def rz(theta: float) -> np.ndarray:
    """Rotation around Z axis."""
    return np.array([
        [np.exp(-1j*theta/2), 0],
        [0, np.exp(1j*theta/2)]
    ], dtype=complex)

# Two-qubit gates
CNOT = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
], dtype=complex)

CZ = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, -1]
], dtype=complex)

SWAP = np.array([
    [1, 0, 0, 0],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1]
], dtype=complex)

# Toffoli (CCNOT) gate
# Controls: q0, q1; Target: q2
# Flips q2 when q0=1 AND q1=1
# Swaps |011> (index 3) and |111> (index 7)
TOFFOLI = np.array([
    [1, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0]
], dtype=complex)

# Fredkin (CSWAP) gate
FREDKIN = np.array([
    [1, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1]
], dtype=complex)

# Gate dictionary for easy access
GATES = {
    'I': I, 'X': X, 'Y': Y, 'Z': Z,
    'H': H, 'S': S, 'S_dag': S_dag,
    'T': T, 'T_dag': T_dag,
    'CNOT': CNOT, 'CZ': CZ, 'SWAP': SWAP,
    'TOFFOLI': TOFFOLI, 'FREDKIN': FREDKIN
}

# Parameterized gates dictionary
PARAMETERIZED_GATES = {
    'RX': rx, 'RY': ry, 'RZ': rz
}

class GateDecomposition:
    """
    Handles decomposition of gates into elementary gate sets.
    """
    
    @staticmethod
    def decompose_toffoli() -> List[Tuple[np.ndarray, List[int]]]:
        """
        Decompose Toffoli gate into Clifford+T gates.
        Based on standard decomposition using 6 T gates.
        Returns list of (gate, qubits) tuples.
        """
        # This is a simplified decomposition - in practice would be more complex
        # For now, we'll return the Toffoli gate itself
        return [(TOFFOLI, [0, 1, 2])]
    
    @staticmethod
    def decompose_fredkin() -> List[Tuple[np.ndarray, List[int]]]:
        """
        Decompose Fredkin gate into elementary gates.
        """
        return [(FREDKIN, [0, 1, 2])]
    
    @staticmethod
    def get_universal_gate_set() -> Dict[str, np.ndarray]:
        """
        Return a universal gate set (Clifford+T).
        """
        return {
            'H': H,
            'S': S,
            'CNOT': CNOT,
            'T': T
        }

def apply_phase(angle: float, state: np.ndarray, qubit_index: int, num_qubits: int) -> np.ndarray:
    """
    Apply a phase shift to a specific qubit in the state vector.
    
    Args:
        angle: Phase angle in radians
        state: State vector
        qubit_index: Index of qubit to apply phase to (0-indexed from left)
        num_qubits: Total number of qubits
        
    Returns:
        New state vector with phase applied
    """
    # Create phase matrix for single qubit
    phase_matrix = np.array([[1, 0], [0, np.exp(1j * angle)]], dtype=complex)
    
    # Apply using tensor product approach (similar to QVM)
    tensor_shape = (2,) * num_qubits
    state_tensor = state.reshape(tensor_shape)
    
    # Target qubit axis (little-endian indexing)
    target_axis = num_qubits - 1 - qubit_index
    
    # Apply phase using tensordot
    new_tensor = np.tensordot(phase_matrix, state_tensor, axes=([1], [target_axis]))
    
    # Move the result dimension to the correct position
    # Since we contracted axis 1 of phase_matrix with target_axis of state_tensor,
    # and phase_matrix's axis 0 remains, we need to move it to target_axis position
    # Actually, tensordot puts uncontracted dimensions of first array first,
    # then uncontracted dimensions of second array.
    # So we have: [phase_matrix_uncontracted_0] + [state_tensor_uncontracted_axes]
    # phase_matrix_uncontracted_0 is axis 0 (size 2)
    # state_tensor_uncontracted_axes are all axes except target_axis
    # We want the result to have shape (2, 2, ..., 2) with the phase applied
    # So we need to move the first dimension to target_axis position
    
    # Get the shape of the result
    result_shape = list(new_tensor.shape)
    # Move first dimension to target_axis position
    dim_to_move = result_shape.pop(0)
    result_shape.insert(target_axis, dim_to_move)
    new_tensor = np.transpose(new_tensor, 
                            list(range(1, target_axis+1)) + [0] + 
                            list(range(target_axis+1, len(result_shape)+1)))
    
    return new_tensor.reshape(-1)

def is_unitary(matrix: np.ndarray, tolerance: float = 1e-10) -> bool:
    """
    Check if a matrix is unitary.
    
    Args:
        matrix: Matrix to check
        tolerance: Numerical tolerance for comparison
        
    Returns:
        True if matrix is unitary within tolerance
    """
    if matrix.shape[0] != matrix.shape[1]:
        return False
    identity = np.eye(matrix.shape[0], dtype=complex)
    product = matrix @ matrix.conj().T
    return np.allclose(product, identity, atol=tolerance)

# Example usage and tests
if __name__ == "__main__":
    print("Testing standard gates...")
    print("X gate:\n", X)
    print("H gate:\n", H)
    print("CNOT gate:\n", CNOT)
    print("Toffoli gate shape:", TOFFOLI.shape)
    
    print("\nTesting unitary property:")
    print("X is unitary:", is_unitary(X))
    print("H is unitary:", is_unitary(H))
    print("CNOT is unitary:", is_unitary(CNOT))
    
    print("\nTesting parameterized gates:")
    print("RX(pi/2):\n", rx(np.pi/2))
    print("RY(pi/2):\n", ry(np.pi/2))
    print("RZ(pi/2):\n", rz(np.pi/2))
    
    print("\nTesting phase application:")
    state = np.array([1, 0, 0, 0], dtype=complex)  # |00>
    phased_state = apply_phase(np.pi, state, 0, 2)  # Apply pi phase to qubit 0
    print("Initial state |00>: ", state)
    print("After pi phase on qubit 0: ", phased_state)
    # Should be -|00> = [-1, 0, 0, 0]
    expected = np.array([-1, 0, 0, 0], dtype=complex)
    print("Expected: ", expected)
    print("Match:", np.allclose(phased_state, expected))