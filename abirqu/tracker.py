"""Benchmark tracker for quantum advantage snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List


@dataclass
class BenchmarkPoint:
    workload: str
    quantum_ms: float
    classical_ms: float

    @property
    def speedup(self) -> float:
        if self.quantum_ms <= 0:
            return 0.0
        return self.classical_ms / self.quantum_ms


class QuantumAdvantageTracker:
    def __init__(self) -> None:
        self._points: List[BenchmarkPoint] = []

    def record(self, workload: str, quantum_ms: float, classical_ms: float) -> BenchmarkPoint:
        point = BenchmarkPoint(workload=workload, quantum_ms=quantum_ms, classical_ms=classical_ms)
        self._points.append(point)
        return point

    def summary(self) -> Dict[str, float]:
        if not self._points:
            return {"count": 0, "mean_speedup": 0.0, "best_speedup": 0.0}
        speeds = [p.speedup for p in self._points]
        return {
            "count": len(self._points),
            "mean_speedup": mean(speeds),
            "best_speedup": max(speeds),
        }

    def by_workload(self) -> Dict[str, float]:
        return {p.workload: p.speedup for p in self._points}
