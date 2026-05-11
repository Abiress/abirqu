import random
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, List, Sequence


class AlgorithmSearchSpaceExplorer:
    def evolve(self, population: Sequence[Dict[str, Any]], fitness_key: str = "fitness", generations: int = 3) -> Dict[str, Any]:
        pop = [dict(p) for p in population]
        for _ in range(generations):
            pop = sorted(pop, key=lambda x: x.get(fitness_key, 0.0), reverse=True)
            top = pop[: max(1, len(pop) // 2)]
            children = []
            for p in top:
                c = dict(p)
                c[fitness_key] = c.get(fitness_key, 0.0) + random.uniform(-0.05, 0.1)
                children.append(c)
            pop = top + children
        best = max(pop, key=lambda x: x.get(fitness_key, 0.0))
        return {"best": best, "population": pop}

    def novelty(self, candidate_signature: str, archive: Sequence[str]) -> float:
        if not archive:
            return 1.0
        d = [sum(1 for a, b in zip(candidate_signature, s) if a != b) for s in archive]
        return float(min(d)) / max(1.0, float(len(candidate_signature)))


class QuantumComplexityAnalyzer:
    def classify(self, qubits: int, depth: int, is_verification: bool = False) -> str:
        if is_verification:
            return "QMA"
        if qubits <= 30 and depth <= 1000:
            return "BQP"
        return "QIP"

    def scaling(self, samples: Sequence[Dict[str, float]]) -> Dict[str, float]:
        if len(samples) < 2:
            return {"slope": 0.0}
        xs = [s["n"] for s in samples]
        ys = [s["cost"] for s in samples]
        slope = (ys[-1] - ys[0]) / max(1e-9, xs[-1] - xs[0])
        return {"slope": slope}

    def lower_bound(self, qubits: int) -> float:
        return float(max(1, qubits))


class QuantumAdvantageValidator:
    def validate(self, quantum_times: Sequence[float], classical_times: Sequence[float]) -> Dict[str, Any]:
        q = mean(quantum_times)
        c = mean(classical_times)
        speedup = c / max(q, 1e-9)
        return {"speedup": speedup, "advantage": speedup > 1.0, "quantum_mean": q, "classical_mean": c}

    def hypothesis_test(self, quantum_times: Sequence[float], classical_times: Sequence[float]) -> Dict[str, Any]:
        q = mean(quantum_times)
        c = mean(classical_times)
        delta = c - q
        return {"effect": delta, "statistically_significant": abs(delta) > 0.05 * max(c, 1e-9)}


class LiteratureAwareCircuitSuggestion:
    def __init__(self) -> None:
        self.kb = [
            {"name": "Grover", "tags": {"search", "oracle"}, "citation": "Grover (1996)"},
            {"name": "QAOA", "tags": {"optimization", "maxcut"}, "citation": "Farhi et al. (2014)"},
            {"name": "VQE", "tags": {"chemistry", "ground-state"}, "citation": "Peruzzo et al. (2014)"},
        ]

    def suggest(self, query_tags: Sequence[str]) -> List[Dict[str, Any]]:
        q = set(query_tags)
        out = []
        for item in self.kb:
            overlap = len(q.intersection(item["tags"]))
            if overlap > 0:
                row = dict(item)
                row["score"] = overlap / float(len(item["tags"]))
                out.append(row)
        return sorted(out, key=lambda x: x["score"], reverse=True)


class QuantumAlgorithmBenchmarkingSuite:
    def __init__(self) -> None:
        self.rows: List[Dict[str, Any]] = []

    def record(self, algorithm: str, backend: str, qv: float, clops: float) -> Dict[str, Any]:
        row = {"algorithm": algorithm, "backend": backend, "quantum_volume": qv, "clops": clops}
        self.rows.append(row)
        return row

    def leaderboard(self, metric: str = "clops") -> List[Dict[str, Any]]:
        return sorted(self.rows, key=lambda x: x.get(metric, 0.0), reverse=True)

    def history(self) -> Dict[str, Any]:
        return {"count": len(self.rows), "rows": list(self.rows)}
