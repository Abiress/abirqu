"""
Quantum Gate Abstractions for AbirQu
Copyright 2026 Abir Maheshwari
"""
import numpy as np
from typing import List, Callable, Optional

class Gate:
    """Base class for all quantum gates."""
    
    def __init__(self, name: str, matrix: np.ndarray, qubits: List[int]):
        self.name = name
        self.matrix = matrix.astype(complex)
        self.qubits = qubits
        
    def __repr__(self):
        return f"Gate({self.name}, qubits={self.qubits})"
        
    def _replace(self, **kwargs):
        """Return a new Gate with updated attributes."""
        name = kwargs.get('name', self.name)
        matrix = kwargs.get('matrix', self.matrix)
        qubits = kwargs.get('qubits', self.qubits)
        return Gate(name, matrix, qubits)
        
    def to_matrix(self) -> np.ndarray:
        """Return the gate matrix."""
        return self.matrix.copy()

# Single-qubit gates
X = Gate("X", np.array([[0,1],[1,0]], dtype=complex), [0])
Y = Gate("Y", np.array([[0,-1j],[1j,0]], dtype=complex), [0])
Z = Gate("Z", np.array([[1,0],[0,-1]], dtype=complex), [0])
H = Gate("H", np.array([[1,1],[1,-1]], dtype=complex) / np.sqrt(2), [0])
S = Gate("S", np.array([[1,0],[0,1j]], dtype=complex), [0])
T = Gate("T", np.array([[1,0],[0,np.exp(1j*np.pi/4)]], dtype=complex), [0])
I = Gate("I", np.eye(2, dtype=complex), [0])

# Parametric single-qubit rotations
def rx(theta: float) -> Gate:
    """Rotation around X axis."""
    matrix = np.array([
        [np.cos(theta/2), -1j*np.sin(theta/2)],
        [-1j*np.sin(theta/2), np.cos(theta/2)]
    ], dtype=complex)
    return Gate(f"RX({theta:.3f})", matrix, [0])

def ry(theta: float) -> Gate:
    """Rotation around Y axis."""
    matrix = np.array([
        [np.cos(theta/2), -np.sin(theta/2)],
        [np.sin(theta/2), np.cos(theta/2)]
    ], dtype=complex)
    return Gate(f"RY({theta:.3f})", matrix, [0])

def rz(theta: float) -> Gate:
    """Rotation around Z axis."""
    matrix = np.array([
        [np.exp(-1j*theta/2), 0],
        [0, np.exp(1j*theta/2)]
    ], dtype=complex)
    return Gate(f"RZ({theta:.3f})", matrix, [0])

def phase(phi: float) -> Gate:
    """Phase gate."""
    matrix = np.array([[1,0],[0,np.exp(1j*phi)]], dtype=complex)
    return Gate(f"PHASE({phi:.3f})", matrix, [0])

# Two-qubit gates
def CNOT(control: int = 0, target: int = 1) -> Gate:
    """Controlled-NOT gate."""
    matrix = np.array([
        [1,0,0,0],
        [0,1,0,0],
        [0,0,0,1],
        [0,0,1,0]
    ], dtype=complex)
    return Gate("CNOT", matrix, [control, target])

def CZ(control: int = 0, target: int = 1) -> Gate:
    """Controlled-Z gate."""
    matrix = np.diag([1,1,1,-1]).astype(complex)
    return Gate("CZ", matrix, [control, target])

def SWAP(q1: int = 0, q2: int = 1) -> Gate:
    """SWAP gate."""
    matrix = np.array([
        [1,0,0,0],
        [0,0,1,0],
        [0,1,0,0],
        [0,0,0,1]
    ], dtype=complex)
    return Gate("SWAP", matrix, [q1, q2])

def CRX(control: int, target: int, theta: float) -> Gate:
    """Controlled-RX gate."""
    matrix = np.array([
        [1,0,0,0],
        [0,1,0,0],
        [0,0,np.cos(theta/2), -1j*np.sin(theta/2)],
        [0,0,-1j*np.sin(theta/2), np.cos(theta/2)]
    ], dtype=complex)
    return Gate(f"CRX({theta:.3f})", matrix, [control, target])

# Three-qubit gates
def TOFFOLI(c1: int = 0, c2: int = 1, target: int = 2) -> Gate:
    """Toffoli (CCNOT) gate."""
    matrix = np.eye(8, dtype=complex)
    matrix[6,6] = 0
    matrix[7,7] = 0
    matrix[6,7] = 1
    matrix[7,6] = 1
    return Gate("TOFFOLI", matrix, [c1, c2, target])

def FREDKIN(c1: int, t1: int, t2: int) -> Gate:
    """Fredkin (CSWAP) gate."""
    matrix = np.eye(8, dtype=complex)
    # Swap |110> and |101>
    matrix[6,6] = 0; matrix[6,5] = 1
    matrix[5,5] = 0; matrix[5,6] = 1
    return Gate("FREDKIN", matrix, [c1, t1, t2])
