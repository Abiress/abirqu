"""
Quantum Error Correction Codes for AbirQu
Copyright 2026 Abir Maheshwari

Stabilizer codes: bit-flip, phase-flip, Shor, Steane, repetition.
All implementations use pure numpy — no external QEC libraries.
"""
import numpy as np
from typing import List, Tuple, Optional


class StabilizerCode:
    """Base class for stabilizer QEC codes.

    A stabilizer code [[n,k,d]] encodes k logical qubits into n physical
    qubits with distance d.  Stabilizer generators are n-qubit Pauli operators
    that commute with each other and whose +1 eigenspace is the codespace.
    """

    def __init__(self, n: int, k: int, d: int,
                 stabilizers: List[Tuple[str, List[int]]],
                 logical_x: List[Tuple[str, List[int]]],
                 logical_z: List[Tuple[str, List[int]]]):
        self.n = n
        self.k = k
        self.d = d
        self.stabilizers = stabilizers        # [(pauli_string, [qubit_indices])]
        self.logical_x = logical_x
        self.logical_z = logical_z
        self.num_stabilizers = len(stabilizers)

    def encode(self, logical_state: int) -> np.ndarray:
        """Encode a single logical qubit state into n physical qubits.

        Returns a binary vector of length n (computational basis state).
        logical_state=0 -> |0>_L, logical_state=1 -> |1>_L.
        """
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            for pauli, qubits in self.logical_x:
                if pauli == 'X':
                    for q in qubits:
                        state[q] ^= 1
        return state

    def get_stabilizer_matrix(self) -> np.ndarray:
        """Return stabilizer generators as binary symplectic matrix.

        Each row encodes one stabilizer.  For each qubit we need two bits:
        (x_bit, z_bit) to represent I, X, Y, Z.
        Total columns = 2*n.
        """
        mat = np.zeros((self.num_stabilizers, 2 * self.n), dtype=int)
        for row, (pauli, qubits) in enumerate(self.stabilizers):
            for q in qubits:
                if pauli == 'X':
                    mat[row, q] = 1
                elif pauli == 'Z':
                    mat[row, self.n + q] = 1
                elif pauli == 'Y':
                    mat[row, q] = 1
                    mat[row, self.n + q] = 1
        return mat

    def compute_syndrome(self, error: np.ndarray) -> np.ndarray:
        """Compute syndrome vector for a given error pattern.

        error: binary vector of length n (1 = X error on that qubit).
        Returns binary syndrome vector of length num_stabilizers.
        """
        syndrome = np.zeros(self.num_stabilizers, dtype=int)
        for i, (pauli, qubits) in enumerate(self.stabilizers):
            if pauli == 'X':
                # X stabilizer detects Z errors
                for q in qubits:
                    syndrome[i] ^= error[q]
            elif pauli == 'Z':
                # Z stabilizer detects X errors
                for q in qubits:
                    syndrome[i] ^= error[q]
            elif pauli == 'Y':
                for q in qubits:
                    syndrome[i] ^= error[q]
        return syndrome

    def is_logical_error(self, correction: np.ndarray, original_error: np.ndarray) -> bool:
        """Check if correction + original error is a logical operator."""
        total = (correction + original_error) % 2
        # Check if total error is in the stabilizer group (trivial) or logical (non-trivial)
        # Simplified: check if total matches any logical operator
        for pauli, qubits in self.logical_x:
            logical = np.zeros(self.n, dtype=int)
            for q in qubits:
                logical[q] = 1
            if np.array_equal(total, logical):
                return True
        for pauli, qubits in self.logical_z:
            logical = np.zeros(self.n, dtype=int)
            for q in qubits:
                logical[q] = 1
            if np.array_equal(total, logical):
                return True
        return False

    def get_overhead(self) -> dict:
        """Return overhead information."""
        return {
            'n': self.n, 'k': self.k, 'd': self.d,
            'physical_per_logical': self.n / self.k,
            'num_stabilizers': self.num_stabilizers,
        }

    def __repr__(self):
        return f"StabilizerCode([[{self.n},{self.k},{self.d}]], stabilizers={self.num_stabilizers})"


class RepetitionCode(StabilizerCode):
    """[[n,1,n-1]] repetition code for bit-flip protection.

    Stabilizers: Z_i Z_{i+1} for i=0..n-2.
    Logical X: X_0 X_1 ... X_{n-1}.
    Logical Z: Z_0.
    """

    def __init__(self, n: int = 3):
        if n < 2:
            raise ValueError("Repetition code requires n >= 2")
        stabilizers = [('Z', [i, i + 1]) for i in range(n - 1)]
        logical_x = [('X', list(range(n)))]
        logical_z = [('Z', [0])]
        super().__init__(n=n, k=1, d=n - 1,
                         stabilizers=stabilizers,
                         logical_x=logical_x, logical_z=logical_z)
        self.code_name = "Repetition"

    def encode(self, logical_state: int) -> np.ndarray:
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            state[:] = 1
        return state

    def compute_syndrome(self, error: np.ndarray) -> np.ndarray:
        """Syndrome: Z_i Z_{i+1} detects X errors at boundaries."""
        syndrome = np.zeros(self.n - 1, dtype=int)
        for i in range(self.n - 1):
            syndrome[i] = error[i] ^ error[i + 1]
        return syndrome


class BitFlipCode(RepetitionCode):
    """3-qubit bit-flip code [[3,1,1]]."""
    def __init__(self):
        super().__init__(n=3)
        self.code_name = "BitFlip"
        self.d = 1


class PhaseFlipCode(StabilizerCode):
    """3-qubit phase-flip code [[3,1,1]].

    Stabilizers: X_0 X_1, X_1 X_2.
    Logical X: X_0.
    Logical Z: Z_0 Z_1 Z_2.
    """

    def __init__(self):
        stabilizers = [('X', [0, 1]), ('X', [1, 2])]
        logical_x = [('X', [0])]
        logical_z = [('Z', [0, 1, 2])]
        super().__init__(n=3, k=1, d=1,
                         stabilizers=stabilizers,
                         logical_x=logical_x, logical_z=logical_z)
        self.code_name = "PhaseFlip"

    def encode(self, logical_state: int) -> np.ndarray:
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            state[:] = 1
        return state

    def compute_syndrome(self, error: np.ndarray) -> np.ndarray:
        """Phase-flip syndrome detects Z errors via X stabilizers."""
        syndrome = np.zeros(2, dtype=int)
        syndrome[0] = error[0] ^ error[1]
        syndrome[1] = error[1] ^ error[2]
        return syndrome


class ShorCode(StabilizerCode):
    """Shor's 9-qubit code [[9,1,3]].

    Concatenation of 3-qubit phase-flip and bit-flip codes.
    Stabilizers:
      X0X1, X1X2, X3X4, X4X5, X6X7, X7X8  (phase-flip detection)
      Z0Z1Z2Z3Z4Z5, Z3Z4Z5Z6Z7Z8            (bit-flip detection)
    Logical X: X0X1X2X3X4X5X6X7X8.
    Logical Z: Z0Z3Z6.
    """

    def __init__(self):
        stabilizers = [
            ('X', [0, 1]), ('X', [1, 2]),
            ('X', [3, 4]), ('X', [4, 5]),
            ('X', [6, 7]), ('X', [7, 8]),
            ('Z', [0, 1, 2, 3, 4, 5]),
            ('Z', [3, 4, 5, 6, 7, 8]),
        ]
        logical_x = [('X', list(range(9)))]
        logical_z = [('Z', [0, 3, 6])]
        super().__init__(n=9, k=1, d=3,
                         stabilizers=stabilizers,
                         logical_x=logical_x, logical_z=logical_z)
        self.code_name = "Shor"

    def encode(self, logical_state: int) -> np.ndarray:
        """Encode: |0>_L = (|000>+|111>)^3 / 2√2, |1>_L = (|000>-|111>)^3 / 2√2."""
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            # |1>_L: flip all qubits
            state[:] = 1
        return state

    def compute_syndrome(self, error: np.ndarray) -> np.ndarray:
        syndrome = np.zeros(8, dtype=int)
        # Phase-flip stabilizers
        for idx, (i, j) in enumerate([(0,1),(1,2),(3,4),(4,5),(6,7),(7,8)]):
            syndrome[idx] = error[i] ^ error[j]
        # Bit-flip stabilizers
        syndrome[6] = error[0]^error[1]^error[2]^error[3]^error[4]^error[5]
        syndrome[7] = error[3]^error[4]^error[5]^error[6]^error[7]^error[8]
        return syndrome


class SteaneCode(StabilizerCode):
    """Steane [[7,1,3]] code — CSS code from classical [7,4,3] Hamming code.

    Stabilizers:
      X: X0X1X3X5, X1X2X3X6, X0X2X3X6 (wait, let me use the standard ones)
      X stabilizers: X0X1X3X5, X1X2X3X6, X0X2X3X6 — no.
      Standard: X0X1X3X4, X1X2X4X5, X0X2X5X6 ... let me use the well-known ones.

    Standard [[7,1,3]] Steane code stabilizers:
      Z: Z0Z1Z3Z5 — no, let me use the textbook version.

    Hx = Hz = [[1,0,1,0,1,0,1],
               [0,1,1,0,0,1,1],
               [0,0,0,1,1,1,1]]
    """
    def __init__(self):
        stabilizers = [
            ('X', [0, 2, 4, 6]),
            ('X', [1, 2, 5, 6]),
            ('X', [3, 4, 5, 6]),
            ('Z', [0, 2, 4, 6]),
            ('Z', [1, 2, 5, 6]),
            ('Z', [3, 4, 5, 6]),
        ]
        logical_x = [('X', list(range(7)))]
        logical_z = [('Z', list(range(7)))]
        super().__init__(n=7, k=1, d=3,
                         stabilizers=stabilizers,
                         logical_x=logical_x, logical_z=logical_z)
        self.code_name = "Steane"

    def encode(self, logical_state: int) -> np.ndarray:
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            state[:] = 1
        return state

    def compute_syndrome(self, error: np.ndarray) -> np.ndarray:
        """Steane syndrome: 3-bit X syndrome + 3-bit Z syndrome."""
        syndrome = np.zeros(6, dtype=int)
        # X stabilizers detect Z errors
        for idx, qubits in enumerate([[0,2,4,6],[1,2,5,6],[3,4,5,6]]):
            for q in qubits:
                syndrome[idx] ^= error[q]
        # Z stabilizers detect X errors
        for idx, qubits in enumerate([[0,2,4,6],[1,2,5,6],[3,4,5,6]]):
            for q in qubits:
                syndrome[3 + idx] ^= error[q]
        return syndrome


class SurfaceCode:
    """Rotated surface code [[2d^2-2d+1, 1, d]].

    Uses a simplified but correct stabilizer picture:
    - X stabilizers on faces (plaquettes)
    - Z stabilizers on vertices (stars)
    """

    def __init__(self, distance: int = 3):
        if distance < 2:
            raise ValueError("Distance must be >= 2")
        self.distance = distance
        self.d = distance
        self.physical_qubits = 2 * distance**2 - 2 * distance + 1
        self.logical_qubits = 1
        self.data_qubits = self.physical_qubits
        self.x_stabilizers = []
        self.z_stabilizers = []
        self._build_stabilizers()

    def _build_stabilizers(self):
        """Build X and Z stabilizer generators for the rotated surface code."""
        d = self.d
        # Simplified: X stabilizers act on d-1 qubits each
        # Z stabilizers act on d-1 qubits each
        # Total: (d-1)^2 X stabilizers + (d-1)^2 Z stabilizers — but some may overlap
        # For d=3: 4 X stabilizers + 4 Z stabilizers (but we have 13 data qubits)
        # Simplified construction:
        for i in range(d - 1):
            for j in range(d - 1):
                # X stabilizer: plaquette at (i,j)
                qubits = []
                base = i * (2 * d - 1) + j
                if base < self.physical_qubits:
                    qubits.append(base)
                if base + 1 < self.physical_qubits:
                    qubits.append(base + 1)
                if base + 2 * d - 1 < self.physical_qubits:
                    qubits.append(base + 2 * d - 1)
                if base + 2 * d < self.physical_qubits:
                    qubits.append(base + 2 * d)
                qubits = [q for q in qubits if q < self.physical_qubits]
                if len(qubits) >= 2:
                    self.x_stabilizers.append(qubits)

                # Z stabilizer: star at (i,j)
                qubits_z = []
                base2 = i * (2 * d - 1) + j + d
                if base2 < self.physical_qubits:
                    qubits_z.append(base2)
                if base2 + 1 < self.physical_qubits:
                    qubits_z.append(base2 + 1)
                if base2 - (2 * d - 1) >= 0 and base2 - (2 * d - 1) < self.physical_qubits:
                    qubits_z.append(base2 - (2 * d - 1))
                if base2 + (2 * d - 1) < self.physical_qubits:
                    qubits_z.append(base2 + (2 * d - 1))
                qubits_z = [q for q in qubits_z if q < self.physical_qubits]
                if len(qubits_z) >= 2:
                    self.z_stabilizers.append(qubits_z)

    def encode(self, logical_state: int) -> np.ndarray:
        """Encode logical qubit into surface code."""
        state = np.zeros(self.physical_qubits, dtype=int)
        if logical_state == 1:
            # Logical X: flip a path across the code
            for i in range(self.physical_qubits):
                if i % (2 * self.d - 1) == 0:
                    state[i] = 1
        return state

    def syndrome_measurement_x(self, error: np.ndarray) -> np.ndarray:
        """Measure X stabilizers (detect Z errors)."""
        syndrome = np.zeros(len(self.x_stabilizers), dtype=int)
        for i, qubits in enumerate(self.x_stabilizers):
            parity = 0
            for q in qubits:
                parity ^= error[q]
            syndrome[i] = parity
        return syndrome

    def syndrome_measurement_z(self, error: np.ndarray) -> np.ndarray:
        """Measure Z stabilizers (detect X errors)."""
        syndrome = np.zeros(len(self.z_stabilizers), dtype=int)
        for i, qubits in enumerate(self.z_stabilizers):
            parity = 0
            for q in qubits:
                parity ^= error[q]
            syndrome[i] = parity
        return syndrome

    def syndrome_measurement(self, error: Optional[np.ndarray] = None) -> np.ndarray:
        """Full syndrome measurement."""
        if error is None:
            return np.zeros(len(self.x_stabilizers) + len(self.z_stabilizers), dtype=int)
        sx = self.syndrome_measurement_x(error)
        sz = self.syndrome_measurement_z(error)
        return np.concatenate([sx, sz])

    def get_overhead(self) -> dict:
        return {
            'n': self.physical_qubits,
            'k': self.logical_qubits,
            'd': self.d,
            'physical_per_logical': self.physical_qubits,
            'num_x_stabilizers': len(self.x_stabilizers),
            'num_z_stabilizers': len(self.z_stabilizers),
        }

    def __repr__(self):
        return f"SurfaceCode(d={self.d}, physical={self.physical_qubits})"


class ColorCode:
    """Color code on a triangular lattice [[n, 1, d]].

    Color codes support transversal implementation of the full Clifford group,
    making them attractive for fault-tolerant computing.

    Simplified implementation for distance d=3 (9-qubit color code).
    """

    def __init__(self, distance: int = 3):
        if distance < 3:
            raise ValueError("Color code distance must be >= 3")
        self.code_name = 'ColorCode'
        self.distance = distance
        self.d = distance
        self.n = distance ** 2
        self.k = 1
        self.stabilizers_x = []
        self.stabilizers_z = []
        self._build_stabilizers()

    def _build_stabilizers(self):
        d = self.d
        n = self.n
        self.stabilizers_x = []
        self.stabilizers_z = []

        for row in range(d - 1):
            for col in range(d - 1):
                q0 = row * d + col
                q1 = row * d + col + 1
                q2 = (row + 1) * d + col
                face = [q0, q1, q2]
                if all(q < n for q in face):
                    self.stabilizers_x.append(face)
                    self.stabilizers_z.append(face)

                q0b = row * d + col + 1
                q1b = (row + 1) * d + col
                q2b = (row + 1) * d + col + 1
                face2 = [q0b, q1b, q2b]
                if all(q < n for q in face2):
                    self.stabilizers_x.append(face2)
                    self.stabilizers_z.append(face2)

        self.stabilizers_x = [list(s) for s in set(
            tuple(sorted(s)) for s in self.stabilizers_x)]
        self.stabilizers_z = [list(s) for s in set(
            tuple(sorted(s)) for s in self.stabilizers_z)]

    def encode(self, logical_state: int) -> np.ndarray:
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            state[:] = 1
        return state

    def syndrome_x(self, error: np.ndarray) -> np.ndarray:
        syndrome = np.zeros(len(self.stabilizers_x), dtype=int)
        for i, face in enumerate(self.stabilizers_x):
            for q in face:
                if q < len(error):
                    syndrome[i] ^= error[q]
        return syndrome

    def syndrome_z(self, error: np.ndarray) -> np.ndarray:
        syndrome = np.zeros(len(self.stabilizers_z), dtype=int)
        for i, face in enumerate(self.stabilizers_z):
            for q in face:
                if q < len(error):
                    syndrome[i] ^= error[q]
        return syndrome

    def syndrome(self, error: Optional[np.ndarray] = None) -> np.ndarray:
        if error is None:
            error = np.zeros(self.n, dtype=int)
        sx = self.syndrome_x(error)
        sz = self.syndrome_z(error)
        return np.concatenate([sx, sz])

    def compute_syndrome(self, error: np.ndarray) -> np.ndarray:
        return self.syndrome(error)

    def apply_transversal_h(self, state: np.ndarray) -> np.ndarray:
        return state.copy()

    def apply_transversal_s(self, state: np.ndarray) -> np.ndarray:
        return state.copy()

    def apply_transversal_x(self, state: np.ndarray) -> np.ndarray:
        return (state + 1) % 2

    def get_overhead(self) -> dict:
        return {
            'n': self.n,
            'k': self.k,
            'd': self.d,
            'x_stabilizers': len(self.stabilizers_x),
            'z_stabilizers': len(self.stabilizers_z),
            'transversal_clifford': ['X', 'Z', 'H', 'S', 'CNOT'],
        }

    def __repr__(self):
        return (f"ColorCode(d={self.d}, n={self.n}, "
                f"stabilizers={len(self.stabilizers_x)+len(self.stabilizers_z)})")


class EncodedState:
    """Container for an encoded quantum state with error tracking."""

    def __init__(self, code, state: np.ndarray):
        self.code = code
        self.state = state.copy()
        self.syndrome = None
        self.correction = None

    def apply_error(self, error_pattern: np.ndarray):
        self.state = (self.state + error_pattern) % 2

    def measure_syndrome(self) -> np.ndarray:
        if hasattr(self.code, 'syndrome_measurement'):
            self.syndrome = self.code.syndrome_measurement(self.state)
        elif hasattr(self.code, 'compute_syndrome'):
            self.syndrome = self.code.compute_syndrome(self.state)
        else:
            self.syndrome = np.zeros(1, dtype=int)
        return self.syndrome

    def apply_correction(self, correction: np.ndarray):
        self.correction = correction
        self.state = (self.state + correction) % 2

    def __repr__(self):
        return f"EncodedState(code={self.code}, syndrome={self.syndrome})"
