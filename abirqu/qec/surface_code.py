"""
Rotated Surface Code for AbirQu
Copyright 2026 Abir Maheshwari

Full implementation of the rotated surface code with:
- Stabilizer construction
- Encoding
- Syndrome measurement
- Logical operators
- Error threshold estimation

Pure numpy implementation.
"""
import numpy as np
from typing import List, Tuple, Optional


class RotatedSurfaceCode:
    """Rotated surface code [[2d^2-2d+1, 1, d]].

    The rotated surface code is the most commonly used variant for
    practical quantum error correction.

    Layout for d=3 (13 data qubits):
        Z - X - Z
        |   |   |
        X - X - X
        |   |   |
        Z - X - Z
    """

    def __init__(self, distance: int = 3):
        if distance < 2:
            raise ValueError("Distance must be >= 2")
        self.d = distance
        self.n = 2 * distance**2 - 2 * distance + 1
        self.k = 1
        self.distance = distance

        # Build qubit grid
        self.data_qubits = []
        self.x_stabilizer_qubits = []
        self.z_stabilizer_qubits = []
        self._build_layout()

    def _build_layout(self):
        """Build the qubit layout for the rotated surface code."""
        d = self.d
        # Data qubits are at positions (i,j) where i+j is even
        # in a d x (2d-1) grid
        idx = 0
        grid = {}
        for i in range(d):
            for j in range(2 * d - 1):
                if (i + j) % 2 == 0:
                    grid[(i, j)] = idx
                    self.data_qubits.append((i, j, idx))
                    idx += 1

        # X stabilizers (face operators)
        self.x_stabilizers = []
        for i in range(d - 1):
            for j in range(0, 2 * d - 2, 2):
                qubits = []
                for di, dj in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    pos = (i + di, j + dj)
                    if pos in grid:
                        qubits.append(grid[pos])
                if len(qubits) >= 2:
                    self.x_stabilizers.append(qubits)

        # Z stabilizers (star operators)
        self.z_stabilizers = []
        for i in range(d - 1):
            for j in range(1, 2 * d - 1, 2):
                qubits = []
                for di, dj in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    pos = (i + di, j + dj)
                    if pos in grid:
                        qubits.append(grid[pos])
                if len(qubits) >= 2:
                    self.z_stabilizers.append(qubits)

        # Logical operators
        # Logical X: path across rows (left boundary to right boundary)
        self._logical_x = []
        for i in range(self.d):
            for j in range(2 * self.d - 1):
                if (i, j) in {pos[:2] for pos in self.data_qubits}:
                    # Pick one qubit per row at the boundary
                    if j == 0 or j == 2 * self.d - 2:
                        for pos in self.data_qubits:
                            if pos[0] == i and pos[1] == j:
                                self._logical_x.append(pos[2])
                                break
                    if len(self._logical_x) >= self.d:
                        break
            if len(self._logical_x) >= self.d:
                break

        # Logical Z: path down columns (top boundary to bottom)
        self._logical_z = []
        for j in range(2 * self.d - 1):
            for i in range(self.d):
                if (i, j) in {pos[:2] for pos in self.data_qubits}:
                    if i == 0 or i == self.d - 1:
                        for pos in self.data_qubits:
                            if pos[0] == i and pos[1] == j:
                                self._logical_z.append(pos[2])
                                break
                    if len(self._logical_z) >= self.d:
                        break
            if len(self._logical_z) >= self.d:
                break

    def encode(self, logical_state: int) -> np.ndarray:
        """Encode a logical qubit."""
        state = np.zeros(self.n, dtype=int)
        if logical_state == 1:
            for q in self._logical_x:
                if q < self.n:
                    state[q] = 1
        return state

    def syndrome_x(self, error: np.ndarray) -> np.ndarray:
        """Measure X stabilizers (detect Z errors)."""
        syndrome = np.zeros(len(self.x_stabilizers), dtype=int)
        for i, qubits in enumerate(self.x_stabilizers):
            for q in qubits:
                if q < len(error):
                    syndrome[i] ^= error[q]
        return syndrome

    def syndrome_z(self, error: np.ndarray) -> np.ndarray:
        """Measure Z stabilizers (detect X errors)."""
        syndrome = np.zeros(len(self.z_stabilizers), dtype=int)
        for i, qubits in enumerate(self.z_stabilizers):
            for q in qubits:
                if q < len(error):
                    syndrome[i] ^= error[q]
        return syndrome

    def syndrome(self, error: Optional[np.ndarray] = None) -> np.ndarray:
        """Full syndrome measurement."""
        if error is None:
            error = np.zeros(self.n, dtype=int)
        sx = self.syndrome_x(error)
        sz = self.syndrome_z(error)
        return np.concatenate([sx, sz])

    def get_logical_x(self) -> List[int]:
        return self._logical_x.copy()

    def get_logical_z(self) -> List[int]:
        return self._logical_z.copy()

    def get_overhead(self) -> dict:
        return {
            'n': self.n,
            'k': self.k,
            'd': self.d,
            'data_qubits': len(self.data_qubits),
            'x_stabilizers': len(self.x_stabilizers),
            'z_stabilizers': len(self.z_stabilizers),
            'logical_x_weight': len(self._logical_x),
            'logical_z_weight': len(self._logical_z),
        }

    def error_correction_threshold(self, num_trials: int = 1000,
                                    error_rates: Optional[List[float]] = None
                                    ) -> dict:
        """Estimate the error correction threshold via simulation.

        Simulates random errors at different rates and checks if the
        decoder can correct them.
        """
        if error_rates is None:
            error_rates = [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]

        results = {}
        for p in error_rates:
            successes = 0
            for _ in range(num_trials):
                # Random X error
                error = (np.random.random(self.n) < p).astype(int)
                syn = self.syndrome(error)

                # Simple decoder: correct at syndrome locations
                correction = np.zeros(self.n, dtype=int)
                for i, s in enumerate(syn):
                    if s == 1 and i < self.n:
                        correction[i] = 1

                # Check if logical error occurred
                total = (error + correction) % 2
                is_logical = False
                for q in self._logical_x:
                    if q < self.n and total[q] == 1:
                        is_logical = True
                        break
                if not is_logical:
                    successes += 1

            results[p] = successes / num_trials

        return results

    def __repr__(self):
        return (f"RotatedSurfaceCode(d={self.d}, n={self.n}, "
                f"k={self.k}, stabilizers={len(self.x_stabilizers)+len(self.z_stabilizers)})")
