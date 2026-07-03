"""
Sampler — convenience wrapper around QuantumRun for sampling only.

This is NOT a copy of Qiskit's Sampler.  It's a thin wrapper that
returns a QuasiDistribution with extra AbirQu-native features like
effective shot count, entropy, and state purity.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import numpy as np
from ..circuit import Circuit
from .quantum_run import QuantumRun, SamplerResult


class QuasiDistribution:
    """Probability distribution with AbirQu-native metadata."""

    def __init__(self, counts: Dict[str, int], shots: int):
        total = sum(counts.values()) if counts else 1
        self._probs = {k: v / total for k, v in counts.items()}
        self._counts = dict(counts)
        self._shots = shots

    @property
    def data(self) -> Dict[str, float]:
        return dict(self._probs)

    @property
    def counts(self) -> Dict[str, int]:
        return dict(self._counts)

    @property
    def shots(self) -> int:
        return self._shots

    @property
    def effective_shots(self) -> int:
        p = np.array(list(self._probs.values()))
        return int(1.0 / np.sum(p ** 2)) if len(p) > 0 else 0

    @property
    def entropy(self) -> float:
        p = np.array(list(self._probs.values()))
        p = p[p > 0]
        return float(-np.sum(p * np.log2(p)))

    @property
    def purity(self) -> float:
        p = np.array(list(self._probs.values()))
        return float(np.sum(p ** 2))

    def top_k(self, k: int = 5) -> List[Tuple[str, float]]:
        return sorted(self._probs.items(), key=lambda x: x[1], reverse=True)[:k]

    def __getitem__(self, key: str) -> float:
        return self._probs.get(key, 0.0)

    def __len__(self) -> int:
        return len(self._probs)

    def __repr__(self) -> str:
        items = sorted(self._probs.items(), key=lambda x: x[1], reverse=True)[:3]
        preview = ", ".join(f"'{k}': {v:.3f}" for k, v in items)
        return f"QuasiDistribution({{{preview}, ...}}, shots={self._shots})"


class Sampler:
    """
    Sample from quantum circuits — returns QuasiDistribution.

    Usage:
        sampler = Sampler()
        dist = sampler.run(bell_circuit, shots=4096)
        dist.data           # {'00': 0.5, '11': 0.5}
        dist.effective_shots # number of statistically independent shots
        dist.entropy         # Shannon entropy in bits
    """

    def __init__(self, backend: Any = None, seed: Optional[int] = None):
        self._backend = backend
        self._seed = seed

    def run(self, circuits: Union[Circuit, List[Circuit]],
            shots: int = 1024) -> Union[QuasiDistribution, List[QuasiDistribution]]:
        qr = QuantumRun(circuits=circuits, shots=shots,
                        backend=self._backend, seed=self._seed)
        results = qr._results
        dists = [QuasiDistribution(r.counts, shots) for r in results]
        return dists[0] if len(dists) == 1 else dists
