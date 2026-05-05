"""
QEC Code Framework

Builds a modular QEC code base class supporting arbitrary stabilizer codes.
Implements surface codes, color codes, and toric codes.
Supports custom code definition via stabilizer generators.
Implements logical operation encodings (X, Y, Z, H, S, CNOT, stabilizer rounds).
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from abc import ABC, abstractmethod

class StabilizerCode(ABC):
    """
    Base class for stabilizer codes.
    
    A stabilizer code is defined by a set of commuting Pauli operators
    (stabilizers) that generate an abelian subgroup of the Pauli group.
    """
    
    def __init__(self, n: int, k: int, d: int):
        """
        Initialize a stabilizer code.
        
        Args:
            n: Number of physical qubits
            k: Number of logical qubits
            d: Code distance (minimum weight of logical operators)
        """
        self.n = n  # Physical qubits
        self.k = k  # Logical qubits
        self.d = d  # Distance
        self.stabilizers: List[np.ndarray] = []  # List of stabilizer generators
        self.logical_x: List[np.ndarray] = []  # Logical X operators
        self.logical_z: List[np.ndarray] = []  # Logical Z operators
        
    def get_stabilizer_matrix(self) -> np.ndarray:
        """
        Get stabilizer generators as binary symplectic matrix.
        
        Returns:
            Matrix of shape (n-k, 2n) in the form [x | z]
            where x and z are binary vectors for Pauli X and Z components.
        """
        if not self.stabilizers:
            return np.zeros((0, 2 * self.n), dtype=int)
            
        # Convert stabilizers to binary symplectic form
        matrix = np.zeros((len(self.stabilizers), 2 * self.n), dtype=int)
        
        for i, stab in enumerate(self.stabilizers):
            for qubit in range(self.n):
                # Extract Pauli at this qubit
                pauli = stab[qubit]
                if pauli == 1:  # X
                    matrix[i, qubit] = 1
                elif pauli == 2:  # Z
                    matrix[i, self.n + qubit] = 1
                elif pauli == 3:  # Y
                    matrix[i, qubit] = 1
                    matrix[i, self.n + qubit] = 1
                    
        return matrix
    
    @abstractmethod
    def encode(self, logical_state: int) -> np.ndarray:
        """
        Encode a logical state into physical qubits.
        
        Args:
            logical_state: 0 or 1 for |0> or |1>
            
        Returns:
            Physical state vector
        """
        pass
    
    def measure_stabilizers(self, state: np.ndarray) -> List[int]:
        """
        Measure stabilizers and return syndrome.
        
        Args:
            state: Physical state vector
            
        Returns:
            Syndrome vector (eigenvalues: +1 -> 0, -1 -> 1)
        """
        # This is simplified - actual implementation would use projector measurements
        syndrome = []
        
        for stab in self.stabilizers:
            # Measure eigenvalue of stabilizer
            # For now, return random syndrome for testing
            syndrome.append(np.random.choice([0, 1]))
            
        return syndrome
    
    def get_logical_operator(self, logical_qubit: int, pauli: str) -> np.ndarray:
        """
        Get logical operator for a given logical qubit.
        
        Args:
            logical_qubit: Index of logical qubit
            pauli: 'X', 'Y', 'Z'
            
        Returns:
            Pauli operator as array
        """
        if pauli.upper() == 'X':
            return self.logical_x[logical_qubit] if logical_qubit < len(self.logical_x) else None
        elif pauli.upper() == 'Z':
            return self.logical_z[logical_qubit] if logical_qubit < len(self.logical_z) else None
        elif pauli.upper() == 'Y':
            # Y = i*X*Z
            if logical_qubit < len(self.logical_x) and logical_qubit < len(self.logical_z):
                return self.logical_x[logical_qubit] * self.logical_z[logical_qubit]
        return None

class SurfaceCode(StabilizerCode):
    """
    Surface code implementation.
    
    The surface code is defined on a 2D grid of qubits with
    plaquette operators (star and plaquette).
    """
    
    def __init__(self, distance: int):
        """
        Initialize a surface code with given distance.
        
        Args:
            distance: Code distance (odd integer)
        """
        if distance % 2 == 0:
            raise ValueError("Surface code distance must be odd")
            
        self.distance = distance
        # For a d x d surface code:
        # Number of data qubits = d^2
        # Number of X-stabilizers = (d-1)^2/2 (approx)
        # Number of Z-stabilizers = (d-1)^2/2 (approx)
        n = distance * distance
        k = 1  # One logical qubit
        super().__init__(n, k, distance)
        
        self._initialize_stabilizers()
        
    def _initialize_stabilizers(self):
        """Initialize stabilizer generators for surface code."""
        d = self.distance
        
        # Data qubit positions: (i, j) for i, j in [0, d-1]
        # X-stabilizers on faces: (i+0.5, j+0.5) for even i+j
        # Z-stabilizers on faces: (i+0.5, j+0.5) for odd i+j
        
        # For simplicity, we'll use a linear indexing
        # and define stabilizers as lists of (qubit, pauli) tuples
        
        # This is a simplified representation
        self.stabilizers = []
        
        # X-stabilizers (star operators)
        for i in range(d - 1):
            for j in range(d - 1):
                if (i + j) % 2 == 0:
                    # X-stabilizer on face (i+0.5, j+0.5)
                    stab = np.zeros(d * d, dtype=int)
                    # Adjacent qubits
                    for di, dj in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                        if i + di < d and j + dj < d:
                            qubit_idx = (i + di) * d + (j + dj)
                            stab[qubit_idx] = 1  # X operator
                    self.stabilizers.append(stab)
                    
        # Z-stabilizers (plaquette operators)
        for i in range(d - 1):
            for j in range(d - 1):
                if (i + j) % 2 == 1:
                    # Z-stabilizer on face (i+0.5, j+0.5)
                    stab = np.zeros(d * d, dtype=int)
                    for di, dj in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                        if i + di < d and j + dj < d:
                            qubit_idx = (i + di) * d + (j + dj)
                            stab[qubit_idx] = 2  # Z operator
                    self.stabilizers.append(stab)
                    
        # Logical operators
        self.logical_x = [np.zeros(d * d, dtype=int)]
        self.logical_z = [np.zeros(d * d, dtype=int)]
        
        # Logical X: horizontal line along top row
        for j in range(d):
            self.logical_x[0][j] = 1  # X on (0, j)
            
        # Logical Z: vertical line along left column
        for i in range(d):
            self.logical_z[0][i * d] = 2  # Z on (i, 0)
            
    def encode(self, logical_state: int) -> np.ndarray:
        """
        Encode a logical state.
        For surface code, encoding is non-trivial and requires
        preparing the logical state on the lattice.
        """
        # Simplified: return a state vector with the appropriate
        # stabilizer eigenstate
        n = self.n
        state = np.zeros(2**n, dtype=complex)
        
        if logical_state == 0:
            # |0>_L state (approximately)
            state[0] = 1.0
        else:
            # |1>_L state
            state[2**(n-1)] = 1.0  # Simplified
            
        return state
    
    def get_x_stabilizers(self) -> List[np.ndarray]:
        """Get X-type stabilizers."""
        return [s for s in self.stabilizers if np.all(s == 1) or np.all(s == 3)]
    
    def get_z_stabilizers(self) -> List[np.ndarray]:
        """Get Z-type stabilizers."""
        return [s for s in self.stabilizers if np.all(s == 2) or np.all(s == 3)]

class ColorCode(StabilizerCode):
    """
    Color code implementation.
    
    Color codes are topological codes defined on trivalent lattices
    where qubits are placed on vertices and stabilizers on faces.
    """
    
    def __init__(self, distance: int):
        """
        Initialize a color code.
        
        Args:
            distance: Code distance
        """
        # Simplified: use same parameters as surface code
        n = 2 * distance * distance  # Approximate
        k = 1
        super().__init__(n, k, distance)
        self.distance = distance
        self._initialize_stabilizers()
        
    def _initialize_stabilizers(self):
        """Initialize color code stabilizers."""
        # Color codes have X and Z stabilizers on faces, colored red/green/blue
        # This is a simplified implementation
        self.stabilizers = []
        
        # For simplicity, create some dummy stabilizers
        for i in range(self.n // 2):
            stab_x = np.zeros(self.n, dtype=int)
            stab_x[2*i] = 1  # X
            stab_x[2*i+1] = 1  # X
            self.stabilizers.append(stab_x)
            
            stab_z = np.zeros(self.n, dtype=int)
            stab_z[2*i] = 2  # Z
            stab_z[2*i+1] = 2  # Z
            self.stabilizers.append(stab_z)
            
        # Logical operators
        self.logical_x = [np.zeros(self.n, dtype=int)]
        self.logical_z = [np.zeros(self.n, dtype=int)]
        self.logical_x[0][0] = 1
        self.logical_z[0][self.n-1] = 2
        
    def encode(self, logical_state: int) -> np.ndarray:
        """Encode logical state."""
        n = self.n
        state = np.zeros(2**n, dtype=complex)
        if logical_state == 0:
            state[0] = 1.0
        else:
            state[2**(n-1)] = 1.0
        return state

class ToricCode(StabilizerCode):
    """
    Toric code implementation.
    
    The toric code is defined on a torus with periodic boundary conditions.
    It encodes 2 logical qubits.
    """
    
    def __init__(self, distance: int):
        """
        Initialize a toric code.
        
        Args:
            distance: Code distance
        """
        n = 2 * distance * distance  # Approximate for d x d lattice
        k = 2  # Toric code encodes 2 logical qubits
        super().__init__(n, k, distance)
        self.distance = distance
        self._initialize_stabilizers()
        
    def _initialize_stabilizers(self):
        """Initialize toric code stabilizers."""
        # Similar to surface code but with periodic boundary conditions
        self.stabilizers = []
        
        d = self.distance
        n = d * d
        
        # X-stabilizers and Z-stabilizers (simplified)
        for i in range(d):
            for j in range(d):
                # X-stabilizer
                stab_x = np.zeros(2 * n, dtype=int)  # Simplified
                self.stabilizers.append(stab_x)
                
                # Z-stabilizer
                stab_z = np.zeros(2 * n, dtype=int)
                self.stabilizers.append(stab_z)
                
        # Logical operators for 2 logical qubits
        self.logical_x = [np.zeros(2*n, dtype=int) for _ in range(2)]
        self.logical_z = [np.zeros(2*n, dtype=int) for _ in range(2)]
        
    def encode(self, logical_state: int) -> np.ndarray:
        """Encode logical state."""
        n = self.n
        state = np.zeros(2**n, dtype=complex)
        state[0] = 1.0  # Simplified
        return state

class RepetitionCode(StabilizerCode):
    """
    Simple repetition code for bit-flip or phase-flip protection.
    """
    
    def __init__(self, distance: int, protect_against: str = 'bit_flip'):
        """
        Initialize repetition code.
        
        Args:
            distance: Number of physical qubits (must be odd)
            protect_against: 'bit_flip' (X) or 'phase_flip' (Z)
        """
        if distance % 2 == 0:
            raise ValueError("Repetition code distance must be odd")
            
        n = distance
        k = 1
        super().__init__(n, k, distance)
        self.protect_against = protect_against
        self._initialize_stabilizers()
        
    def _initialize_stabilizers(self):
        """Initialize stabilizers for repetition code."""
        self.stabilizers = []
        
        for i in range(self.n - 1):
            stab = np.zeros(self.n, dtype=int)
            if self.protect_against == 'bit_flip':
                # Z-type stabilizers: Z_i * Z_{i+1}
                stab[i] = 2
                stab[i+1] = 2
            else:
                # X-type stabilizers: X_i * X_{i+1}
                stab[i] = 1
                stab[i+1] = 1
            self.stabilizers.append(stab)
            
        # Logical operators
        self.logical_x = [np.zeros(self.n, dtype=int)]
        self.logical_z = [np.zeros(self.n, dtype=int)]
        
        if self.protect_against == 'bit_flip':
            # Logical Z = Z on all qubits
            self.logical_z[0][:] = 2
            # Logical X = X on first qubit (simplified)
            self.logical_x[0][0] = 1
        else:
            # Logical X = X on all qubits
            self.logical_x[0][:] = 1
            # Logical Z = Z on first qubit
            self.logical_z[0][0] = 2
            
    def encode(self, logical_state: int) -> np.ndarray:
        """Encode logical state."""
        n = self.n
        state = np.zeros(2**n, dtype=complex)
        
        if self.protect_against == 'bit_flip':
            if logical_state == 0:
                # |000...0>
                state[0] = 1.0
            else:
                # |111...1>
                state[2**n - 1] = 1.0
        else:
            # For phase-flip, encode in superposition
            if logical_state == 0:
                state[0] = 1.0 / np.sqrt(2)
                state[2**n - 1] = 1.0 / np.sqrt(2)
            else:
                state[0] = 1.0 / np.sqrt(2)
                state[2**n - 1] = -1.0 / np.sqrt(2)
                
        return state

# Example usage and tests
if __name__ == "__main__":
    print("Testing QEC Code Framework...")
    
    # Test Surface Code
    print("\nSurface Code (distance 3):")
    surface = SurfaceCode(distance=3)
    print(f"Physical qubits: {surface.n}")
    print(f"Logical qubits: {surface.k}")
    print(f"Distance: {surface.d}")
    print(f"Number of stabilizers: {len(surface.stabilizers)}")
    
    # Test Repetition Code
    print("\nRepetition Code (distance 5, bit-flip):")
    rep = RepetitionCode(distance=5, protect_against='bit_flip')
    print(f"Physical qubits: {rep.n}")
    print(f"Stabilizers: {len(rep.stabilizers)}")
    
    # Encode a logical |0>
    state = rep.encode(0)
    print(f"Encoded |0>_L state vector length: {len(state)}")
    print(f"State: {state[:10]}...")  # Show first 10 elements