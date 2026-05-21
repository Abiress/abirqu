"""
Quantum Error Correction Codes for AbirQu
Copyright 2026 Abir Maheshwari
"""
import numpy as np
from typing import List, Dict, Optional, Tuple

class SurfaceCode:
    """Surface code implementation for fault-tolerant quantum computing."""
    
    def __init__(self, distance: int = 3):
        self.distance = distance  # Code distance
        self.d = distance
        # For surface code: n = 2*d^2 - 1, k = 1
        self.physical_qubits = 2 * distance**2 - 1
        self.logical_qubits = 1
        
    def encode(self, logical_state: int) -> np.ndarray:
        """Encode a logical qubit into surface code."""
        # Create physical qubits in appropriate state
        # For |0>_L: all data qubits in |0>, measure stabilizers
        # For |1>_L: all data qubits in |1>
        encoded = np.zeros(self.physical_qubits, dtype=int)
        
        if logical_state == 1:
            # Set data qubits to |1>
            # In surface code, data qubits are at odd positions
            for i in range(self.physical_qubits):
                if i % 2 == 0:  # Data qubit
                    encoded[i] = 1
                    
        return encoded
        
    def get_overhead(self) -> int:
        """Return physical qubit overhead."""
        return self.physical_qubits
        
    def syndrome_measurement(self, state: np.ndarray, error: Optional[np.ndarray] = None) -> np.ndarray:
        """Measure syndrome (simplified)."""
        # Simplified: measure stabilizers
        # In real implementation, would measure X and Z stabilizers
        syndrome = np.zeros(self.distance**2, dtype=int)
        
        if error is not None:
            # Detect errors (simplified)
            for i in range(min(len(error), len(syndrome))):
                syndrome[i] = error[i] % 2
                
        return syndrome
        
    def logical_operators(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return logical X and Z operators."""
        # Simplified: logical X flips all data qubits in a row
        logical_x = np.zeros(self.physical_qubits, dtype=int)
        logical_z = np.zeros(self.physical_qubits, dtype=int)
        
        # Set logical operators (simplified)
        for i in range(self.physical_qubits):
            if i % 2 == 0:  # Data qubit
                logical_x[i] = 1
                logical_z[i] = 1
                
        return logical_x, logical_z
        
    def __repr__(self):
        return f"SurfaceCode(d={self.distance}, physical={self.physical_qubits})"

class LDPCCode:
    """LDPC code with reduced overhead (10-100x improvement over surface code)."""
    
    def __init__(self, n: int = 100, k: int = 50, d: int = 10):
        self.n = n  # Code length (physical qubits)
        self.k = k  # Message length (logical qubits)
        self.d = d  # Code distance
        
        # Generate parity-check matrix H (n-k × n)
        self.H = self._generate_parity_matrix()
        # Generator matrix G (k × n)
        self.G = self._generate_generator_matrix()
        
    def _generate_parity_matrix(self) -> np.ndarray:
        """Generate sparse parity-check matrix in systematic form H = [P^T | I_{n-k}]."""
        m = self.n - self.k
        col_weight = min(3, m)
        P = np.zeros((self.k, m), dtype=int)
        
        if self.k == m:
            for w in range(col_weight):
                for attempt in range(100):
                    perm = np.random.permutation(m)
                    if not np.any(P[np.arange(self.k), perm] == 1):
                        P[np.arange(self.k), perm] = 1
                        break
        else:
            # General case: ensure no row or column is empty
            for i in range(self.k):
                col_idxs = np.random.choice(m, col_weight, replace=False)
                P[i, col_idxs] = 1
            # Fix any empty columns in P
            for j in range(m):
                if np.sum(P[:, j]) == 0:
                    r = np.random.randint(self.k)
                    P[r, j] = 1
            
        # H = [P^T | I_m] of shape m x n
        H = np.zeros((m, self.n), dtype=int)
        H[:, :self.k] = P.T
        H[:, self.k:] = np.eye(m, dtype=int)
        
        self._P = P
        return H
        
    def _generate_generator_matrix(self) -> np.ndarray:
        """Generate generator matrix in systematic form G = [I_k | P]."""
        if not hasattr(self, '_P'):
            self.H = self._generate_parity_matrix()
            
        G = np.zeros((self.k, self.n), dtype=int)
        G[:, :self.k] = np.eye(self.k, dtype=int)
        G[:, self.k:] = self._P
        return G
        
    def encode(self, message: List[int]) -> List[int]:
        """Encode message with LDPC."""
        if len(message) != self.k:
            raise ValueError(f"Message length must be {self.k}")
            
        msg = np.array(message, dtype=int)
        codeword = (msg @ self.G) % 2
        return codeword.tolist()
        
    def decode(self, received: List[float]) -> List[int]:
        """Decode received channel values/codeword to recover message."""
        from abirqu.qec.ldpc import LDPCDecoder
        decoder = LDPCDecoder()
        decoder.load_code(self)
        codeword = decoder.decode(received)
        return codeword[:self.k]
        
    def get_rate(self) -> float:
        """Return code rate k/n."""
        return self.k / self.n
        
    def estimate_overhead(self) -> int:
        """Estimate qubit overhead vs surface code."""
        surface_overhead = 2 * self.d**2 - 1
        ldpc_overhead = self.n
        return int(surface_overhead / ldpc_overhead * 100)  # Percentage
        
    def __repr__(self):
        return f"LDPCCode(n={self.n}, k={self.k}, d={self.d}, rate={self.get_rate():.2f})"

class EncodedState:
    """Container for encoded quantum state."""
    
    def __init__(self, code: 'SurfaceCode', state: np.ndarray):
        self.code = code
        self.state = state
        self.syndrome = None
        
    def apply_error(self, error_pattern: np.ndarray):
        """Apply error to encoded state."""
        self.state = (self.state + error_pattern) % 2
        
    def measure_syndrome(self) -> np.ndarray:
        """Measure syndrome."""
        self.syndrome = self.code.syndrome_measurement(self.state)
        return self.syndrome
        
    def __repr__(self):
        return f"EncodedState(code={self.code}, syndrome={self.syndrome})"
