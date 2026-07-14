"""
NumPy-accelerated quantum simulator for AbirQu.
Simple but correct implementation.
"""
import numpy as np
from typing import Dict

# Gate matrices
_H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
_X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
_Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
_Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
_S = np.array([[1, 0], [0, 1j]], dtype=np.complex128)
_T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=np.complex128)


class NumPySimulator:
    """
    Pure-Python/NumPy state-vector simulator.
    Uses explicit loops for correctness. Performance is O(n * 2^n).
    """
    
    def __init__(self, num_qubits: int):
        self.n = num_qubits
        self.state = np.zeros(2**num_qubits, dtype=np.complex128)
        self.state[0] = 1.0
    
    def _apply_1q(self, gate: np.ndarray, qubit: int):
        """Apply 2x2 gate to single qubit."""
        new_state = np.zeros_like(self.state)
        mask = 1 << qubit
        
        for i in range(2**self.n):
            bit = (i >> qubit) & 1
            other = i ^ mask
            
            if bit == 0:
                # This is a |0⟩ component on this qubit
                new_state[i] = gate[0, 0] * self.state[i] + gate[0, 1] * self.state[other]
                new_state[other] = gate[1, 0] * self.state[i] + gate[1, 1] * self.state[other]
        
        self.state = new_state
    
    def h(self, qubit: int):
        self._apply_1q(_H, qubit)
    
    def x(self, qubit: int):
        self._apply_1q(_X, qubit)
    
    def y(self, qubit: int):
        self._apply_1q(_Y, qubit)
    
    def z(self, qubit: int):
        self._apply_1q(_Z, qubit)
    
    def s(self, qubit: int):
        self._apply_1q(_S, qubit)
    
    def t(self, qubit: int):
        self._apply_1q(_T, qubit)
    
    def rx(self, qubit: int, theta: float):
        c, s = np.cos(theta/2), np.sin(theta/2)
        gate = np.array([[c, -1j*s], [-1j*s, c]], dtype=np.complex128)
        self._apply_1q(gate, qubit)
    
    def ry(self, qubit: int, theta: float):
        c, s = np.cos(theta/2), np.sin(theta/2)
        gate = np.array([[c, -s], [s, c]], dtype=np.complex128)
        self._apply_1q(gate, qubit)
    
    def rz(self, qubit: int, theta: float):
        gate = np.array([[np.exp(-1j*theta/2), 0],
                         [0, np.exp(1j*theta/2)]], dtype=np.complex128)
        self._apply_1q(gate, qubit)
    
    def cnot(self, control: int, target: int):
        """CNOT: if control=1, flip target."""
        new_state = np.zeros_like(self.state)
        control_mask = 1 << control
        target_mask = 1 << target
        
        for i in range(2**self.n):
            if (i & control_mask):
                new_state[i ^ target_mask] = self.state[i]
            else:
                new_state[i] = self.state[i]
        
        self.state = new_state
    
    def cz(self, control: int, target: int):
        """CZ: if both control and target are 1, multiply by -1."""
        for i in range(2**self.n):
            if ((i >> control) & 1) and ((i >> target) & 1):
                self.state[i] *= -1
    
    def toffoli(self, c1: int, c2: int, target: int):
        """Toffoli: if both controls are 1, flip target."""
        new_state = np.zeros_like(self.state)
        c1_mask = 1 << c1
        c2_mask = 1 << c2
        t_mask = 1 << target
        
        for i in range(2**self.n):
            if (i & c1_mask) and (i & c2_mask):
                # Both controls are 1, flip target
                new_state[i ^ t_mask] = self.state[i]
            else:
                new_state[i] = self.state[i]
        
        self.state = new_state
    
    def swap(self, q0: int, q1: int):
        """SWAP: exchange q0 and q1."""
        if q0 == q1:
            return

        new_state = np.zeros_like(self.state)
        m0 = 1 << q0
        m1 = 1 << q1

        for i in range(2**self.n):
            b0 = (i >> q0) & 1
            b1 = (i >> q1) & 1
            if b0 == b1:
                j = i
            else:
                j = i ^ m0 ^ m1
            new_state[j] = self.state[i]

        self.state = new_state
    
    def run_circuit(self, circuit) -> Dict[str, float]:
        """Execute a full Circuit object."""
        for gate in getattr(circuit, 'gates', []):
            name = gate.name.upper()
            qubits = gate.qubits
            params = getattr(gate, 'params', []) or []
            
            if len(qubits) == 1:
                q = qubits[0]
                if name == 'H':
                    self.h(q)
                elif name == 'X':
                    self.x(q)
                elif name == 'Y':
                    self.y(q)
                elif name == 'Z':
                    self.z(q)
                elif name == 'S':
                    self.s(q)
                elif name == 'T':
                    self.t(q)
                elif name == 'RX':
                    self.rx(q, params[0])
                elif name == 'RY':
                    self.ry(q, params[0])
                elif name == 'RZ':
                    self.rz(q, params[0])
            elif len(qubits) == 2:
                c, t = qubits[0], qubits[1]
                if name in ['CNOT', 'CX']:
                    self.cnot(c, t)
                elif name == 'CZ':
                    self.cz(c, t)
                elif name == 'SWAP':
                    self.swap(c, t)
            elif len(qubits) == 3:
                if name == 'TOFFOLI':
                    self.toffoli(qubits[0], qubits[1], qubits[2])
            else:
                # Custom multi-qubit gate: apply matrix directly
                matrix = getattr(gate, 'matrix', None)
                if matrix is not None:
                    self._apply_custom_unitary(matrix, qubits)
        
        probs = np.abs(self.state) ** 2
        return {
            format(i, f'0{self.n}b'): float(p)
            for i, p in enumerate(probs) if p > 1e-15
        }
    
    def get_probabilities(self) -> Dict[str, float]:
        probs = np.abs(self.state) ** 2
        return {
            format(i, f'0{self.n}b'): float(p)
            for i, p in enumerate(probs) if p > 1e-15
        }
    
    def get_state_vector(self) -> np.ndarray:
        return self.state.copy()
    
    def _apply_custom_unitary(self, matrix: np.ndarray, qubits: list):
        """Apply an arbitrary unitary matrix to specified qubits."""
        n_qubits = len(qubits)
        dim = 2 ** n_qubits
        
        if matrix.shape != (dim, dim):
            raise ValueError(f"Unitary matrix shape {matrix.shape} doesn't match {n_qubits} qubits")
        
        # Create the full state vector permutation for these qubits
        # We need to apply the matrix to the subspace defined by these qubits
        new_state = np.zeros_like(self.state)
        
        # Iterate over all basis states
        for i in range(2 ** self.n):
            # Extract the bits for the target qubits
            subspace_idx = 0
            for j, q in enumerate(qubits):
                if (i >> q) & 1:
                    subspace_idx |= (1 << j)
            
            # Apply the unitary to this component
            for k in range(dim):
                if abs(matrix[k, subspace_idx]) > 1e-15:
                    # Compute the output state index
                    output_idx = i
                    # Clear the target qubit bits
                    for j, q in enumerate(qubits):
                        output_idx &= ~(1 << q)
                    # Set the new bits from the matrix output
                    for j, q in enumerate(qubits):
                        if (k >> j) & 1:
                            output_idx |= (1 << q)
                    new_state[output_idx] += matrix[k, subspace_idx] * self.state[i]
        
        self.state = new_state