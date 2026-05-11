from typing import Any, Dict, List, Sequence

from .phase19 import MultiCloudQuantumRouter, ProviderProfile


class WorkloadScorer:
    def score(self, provider: Dict[str, Any], workload: Dict[str, Any]) -> float:
        fidelity = float(provider.get("fidelity", 0.9))
        latency = float(provider.get("latency_ms", 100.0))
        cost = float(provider.get("cost_per_shot", 0.001))
        shots = float(workload.get("shots", 1024))
        return fidelity - 0.001 * latency - 0.0001 * shots * cost


class FederatedBenchmarkRunner:
    def run(self, workload: Dict[str, Any], providers: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scorer = WorkloadScorer()
        rows = []
        for p in providers:
            rows.append({"provider": p["name"], "score": scorer.score(p, workload), "workload": workload.get("id")})
        return sorted(rows, key=lambda x: x["score"], reverse=True)


class CostTimeQualityOptimizer:
    def choose(self, candidates: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        best = None
        best_score = -1e9
        for c in candidates:
            quality = float(c.get("quality", 0.0))
            cost = max(float(c.get("cost", 1.0)), 1e-9)
            time = max(float(c.get("time", 1.0)), 1e-9)
            s = quality / (cost * time)
            if s > best_score:
                best_score = s
                best = dict(c)
        return {"best": best, "score": best_score}


class ProductionRouter:
    def route(self, workload: Dict[str, Any], providers: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        profiles = [
            ProviderProfile(
                name=p["name"],
                latency_ms=float(p.get("latency_ms", 100.0)),
                cost_per_shot=float(p.get("cost_per_shot", 0.001)),
                fidelity=float(p.get("fidelity", 0.9)),
                online=bool(p.get("online", True)),
            )
            for p in providers
        ]
        return MultiCloudQuantumRouter().route(workload, profiles)
