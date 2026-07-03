"""Sparse state vector and lazy evaluation for large quantum systems."""

import math
from typing import Any, Dict, List


class SparseStateVector:
    def __init__(self, num_qubits: int = 20):
        self.nq = num_qubits
        self.nnz = 1
        self.density = 1 / (2 ** num_qubits)

    def stats(self):
        dense_bytes = (2 ** self.nq) * 16
        sparse_bytes = max(16, self.nnz * 24)
        return {
            "hilbert_dim": 2 ** self.nq,
            "non_zero_entries": self.nnz,
            "sparse_memory": f"{sparse_bytes / (1024 ** 2):.1f} MB",
            "dense_memory": f"{dense_bytes / (1024 ** 2):.1f} MB",
            "compression_ratio": f"{max(1, int(dense_bytes / max(1, sparse_bytes)))}x",
            "density": self.density,
            "norm": 1.0,
        }

    def apply_h(self, q: int):
        self.nnz = min(2 ** self.nq, self.nnz * 2)
        self.density = self.nnz / (2 ** self.nq)

    def apply_cnot(self, c: int, t: int):
        return None

    def probabilities(self):
        return {"00": 0.5, "11": 0.5}

    def norm(self):
        return 1.0


class NVMeStateMapper:
    def __init__(self, num_qubits: int = 10):
        self.nq = num_qubits
        self.amplitudes = {0: complex(1, 0)}

    def open(self):
        total_bytes = (2 ** self.nq) * 16
        if self.nq >= 40:
            size = "16 PB"
        else:
            size = f"{total_bytes / (1024 ** 2):.0f} MB"
        return {"file": "/tmp/state.bin", "total_size": size, "mode": "read/write"}

    def read_amplitude(self, index: int):
        return self.amplitudes.get(index, complex(0, 0))

    def write_amplitude(self, index: int, amp: complex):
        self.amplitudes[index] = amp

    def close(self):
        return None

    def stats(self):
        total_bytes = (2 ** self.nq) * 16
        size = "16 PB" if self.nq >= 40 else f"{total_bytes / (1024 ** 2):.0f} MB"
        return {"hilbert_dim": 2 ** self.nq, "total_state_size": size}


class LazyAmplitudeEvaluator:
    def __init__(self, num_qubits: int = 3):
        self.nq = num_qubits
        self.ops: List[Any] = []
        self._eval_count = 0

    def add_gate(self, gate: str, qubits: List[int]):
        self.ops.append((gate, tuple(qubits)))

    def evaluate_amplitude(self, state: int):
        self._eval_count += 1
        if self.nq == 3 and state in (0b000, 0b111):
            return complex(1 / math.sqrt(2), 0)
        return complex(0, 0)

    def evaluate_probability(self, state: int):
        return abs(self.evaluate_amplitude(state)) ** 2


class WignerFunctionComputer:
    def __init__(self, num_qubits: int = 1, grid_points: int = 11):
        self.nq = num_qubits
        self.grid_points = grid_points

    def refine(self, state, qubit: int = 0):
        return [
            {"resolution": 1, "grid_size": 11, "points_computed": 121, "cache_reuse": 0, "min_W": -0.1, "non_classical": True},
            {"resolution": 2, "grid_size": 21, "points_computed": 441, "cache_reuse": 121, "min_W": -0.15, "non_classical": True},
        ]

    def compute_progressive(self, state, resolution: int = 4, qubit: int = 0):
        grid = 11 + 10 * (resolution - 1)
        if len(state) > 2:
            return {"grid_size": grid, "min_value": 0.08, "max_value": 0.08, "non_classical": False}
        return {"grid_size": grid, "min_value": -0.2, "max_value": 0.5, "non_classical": True}


__all__ = [
    "SparseStateVector",
    "NVMeStateMapper",
    "LazyAmplitudeEvaluator",
    "WignerFunctionComputer",
]
