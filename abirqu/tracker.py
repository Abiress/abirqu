"""
Benchmark tracker for quantum advantage snapshots.
Copyright 2026 Abir Maheshwari
"""

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
    def __init__(self, filepath: str = "benchmark_results/telemetry.json") -> None:
        self._points: List[BenchmarkPoint] = []
        self.filepath = filepath
        self.load()

    def record(self, workload: str, quantum_ms: float, classical_ms: float) -> BenchmarkPoint:
        point = BenchmarkPoint(workload=workload, quantum_ms=quantum_ms, classical_ms=classical_ms)
        self._points.append(point)
        self.save()
        return point

    def save(self) -> None:
        import json
        import os
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        from dataclasses import asdict
        data = [asdict(p) for p in self._points]
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        import json
        import os
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                self._points = [
                    BenchmarkPoint(
                        workload=item["workload"],
                        quantum_ms=item["quantum_ms"],
                        classical_ms=item["classical_ms"]
                    )
                    for item in data
                ]
            except Exception:
                self._points = []

    def simulate_telemetry_updates(self, count: int = 5, base_speedup: float = 10.0) -> List[BenchmarkPoint]:
        """Simulate a trend of increasing speedups to demonstrate telemetry."""
        new_points = []
        for i in range(count):
            workload = f"simulated_workload_{len(self._points) + 1}"
            classical = 1000.0
            speedup = base_speedup + i * 2.5
            quantum = classical / speedup
            point = self.record(workload, quantum, classical)
            new_points.append(point)
        return new_points

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
