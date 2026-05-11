from dataclasses import dataclass
from typing import Any, Dict, List, Sequence


@dataclass
class ProviderProfile:
    name: str
    latency_ms: float
    cost_per_shot: float
    fidelity: float
    online: bool = True


class MultiCloudQuantumRouter:
    """Route workloads across providers using cost/latency/fidelity objectives."""

    def select_provider(self, providers: Sequence[ProviderProfile], objective: str = "balanced") -> ProviderProfile:
        online = [p for p in providers if p.online]
        if not online:
            raise ValueError("No online providers")

        def score(p: ProviderProfile) -> float:
            if objective == "low-latency":
                return -p.latency_ms
            if objective == "low-cost":
                return -p.cost_per_shot
            if objective == "high-fidelity":
                return p.fidelity
            return p.fidelity - 0.001 * p.latency_ms - 0.1 * p.cost_per_shot

        return max(online, key=score)

    def route(self, workload: Dict[str, Any], providers: Sequence[ProviderProfile], objective: str = "balanced") -> Dict[str, Any]:
        best = self.select_provider(providers, objective=objective)
        return {
            "workload_id": workload.get("id"),
            "provider": best.name,
            "objective": objective,
            "estimated_latency_ms": best.latency_ms,
            "estimated_cost": workload.get("shots", 1024) * best.cost_per_shot,
        }


class FederatedResultMerger:
    def merge_counts(self, results: Sequence[Dict[str, Any]]) -> Dict[str, int]:
        merged: Dict[str, int] = {}
        for r in results:
            for bitstring, c in r.get("counts", {}).items():
                merged[bitstring] = merged.get(bitstring, 0) + int(c)
        return merged

    def merge_probabilities(self, results: Sequence[Dict[str, Any]]) -> Dict[str, float]:
        counts = self.merge_counts(results)
        total = sum(counts.values())
        if total == 0:
            return {}
        return {k: v / total for k, v in counts.items()}


class HybridWorkloadPlanner:
    def partition(self, tasks: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        out = {"quantum": [], "classical": []}
        for t in tasks:
            if t.get("quantum_speedup", 1.0) > 1.0:
                out["quantum"].append(dict(t))
            else:
                out["classical"].append(dict(t))
        return out

    def budgeted_plan(self, tasks: Sequence[Dict[str, Any]], budget: float) -> Dict[str, Any]:
        selected = []
        spent = 0.0
        for t in sorted(tasks, key=lambda x: x.get("value", 0.0), reverse=True):
            cost = float(t.get("cost", 0.0))
            if spent + cost <= budget:
                selected.append(t)
                spent += cost
        return {"selected": selected, "spent": spent, "remaining": budget - spent}
