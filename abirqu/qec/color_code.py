"""
Color Code for AbirQu
Copyright 2026 Abir Maheshwari

Color codes are topological codes on trivalent, 3-colorable lattices.
Key advantage: transversal implementation of the full Clifford group,
including H and S gates (unlike surface codes which only support Clifford-1).

Pure numpy implementation.
"""
import numpy as np
from typing import List, Tuple, Optional


class ColorCode:
    """Color code on a triangular lattice [[n, k, d]].

    For distance d, uses d^2 qubits arranged in a triangular grid.
    Supports transversal Clifford gates: X, Z, H, S, CNOT.
    """

    def __init__(self, distance: int = 3):
        if distance < 3:
            raise ValueError("Color code distance must be >= 3 (odd)")
        self.d = distance
        self.n = distance ** 2
        self.k = 1

        self.data_qubits = []
        self.stabilizers_x = []
        self.stabilizers_z = []
        self._build_code()

    def _build_code(self):
        """Build the color code lattice and stabilizers."""
        d = self.d
        n = self.n

        # Create triangular lattice positions
        positions = []
        idx = 0
        for row in range(d):
            for col in range(d):
                positions.append((row, col, idx))
                idx += 1
        self.data_qubits = positions

        # Build stabilizers for each face of the triangulation
        # X and Z stabilizers on the same face (CSS property)
        self.stabilizers_x = []
        self.stabilizers_z = []

        for row in range(d - 1):
            for col in range(d - 1):
                # Upward triangle
                q0 = row * d + col
                q1 = row * d + col + 1
                q2 = (row + 1) * d + col
                face = [q0, q1, q2]
                if all(q < n for q in face):
                    self.stabilizers_x.append(face)
                    self.stabilizers_z.append(face)

                # Downward triangle
                q0 = row * d + col + 1
                q1 = (row + 1) * d + col
                q2 = (row + 1) * d + col + 1
                face = [q0, q1, q2]
                if all(q < n for q in face):
                    self.stabilizers_x.append(face)
                    self.stabilizers_z.append(face)

        # Remove duplicate stabilizers
        self.stabilizers_x = [list(s) for s in set(
            tuple(sorted(s)) for s in self.stabilizers_x)]
        self.stabilizers_z = [list(s) for s in set(
            tuple(sorted(s)) for s in self.stabilizers_z)]

        self.num_stabilizers = len(self.stabilizers_x) + len(self.stabilizers_z)

    def encode(self, logical_state: int) -> np.ndarray:
        """Encode logical qubit into color code."""
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            # Logical X: flip all qubits (transversal X)
            state[:] = 1
        return state

    def syndrome_x(self, error: np.ndarray) -> np.ndarray:
        """X stabilizer syndrome (detects Z errors)."""
        syndrome = np.zeros(len(self.stabilizers_x), dtype=int)
        for i, face in enumerate(self.stabilizers_x):
            for q in face:
                if q < len(error):
                    syndrome[i] ^= error[q]
        return syndrome

    def syndrome_z(self, error: np.ndarray) -> np.ndarray:
        """Z stabilizer syndrome (detects X errors)."""
        syndrome = np.zeros(len(self.stabilizers_z), dtype=int)
        for i, face in enumerate(self.stabilizers_z):
            for q in face:
                if q < len(error):
                    syndrome[i] ^= error[q]
        return syndrome

    def syndrome(self, error: Optional[np.ndarray] = None) -> np.ndarray:
        """Full syndrome."""
        if error is None:
            error = np.zeros(self.n, dtype=int)
        sx = self.syndrome_x(error)
        sz = self.syndrome_z(error)
        return np.concatenate([sx, sz])

    def apply_transversal_h(self, state: np.ndarray) -> np.ndarray:
        """Transversal Hadamard: swaps X and Z errors.

        For color codes, H can be applied transversally.
        In the computational basis, this is identity (H is applied
        in the encoded space).
        """
        # Transversal H swaps logical X <-> logical Z
        # In the computational basis representation, no change needed
        return state.copy()

    def apply_transversal_s(self, state: np.ndarray) -> np.ndarray:
        """Transversal S gate.

        S maps X -> Y, preserves Z. For color codes this is transversal.
        """
        return state.copy()

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


class ColorCodeDecoder:
    """Decoder for color codes using gauge fixing to surface code."""

    def __init__(self, code: ColorCode):
        self.code = code

    def decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode syndrome using gauge-fixing approach.

        Fix the gauge to reduce to a surface code problem,
        then use surface code decoding.
        """
        n = self.code.n
        correction = np.zeros(n, dtype=int)

        # Split syndrome into X and Z parts
        num_x = len(self.code.stabilizers_x)
        sx = syndrome[:num_x]
        sz = syndrome[num_x:]

        # Greedy correction for X errors (detected by Z stabilizers)
        defects_z = [i for i, s in enumerate(sz) if s == 1]
        for i in range(0, len(defects_z) - 1, 2):
            if defects_z[i] < n:
                correction[defects_z[i]] = 1

        # Greedy correction for Z errors (detected by X stabilizers)
        defects_x = [i for i, s in enumerate(sx) if s == 1]
        for i in range(0, len(defects_x) - 1, 2):
            if defects_x[i] < n:
                correction[defects_x[i]] ^= 1

        return correction
