"""Multi-objective routing and orchestration for AbirQu."""

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple


class MultiObjectiveRouter:
    def route(self, circuit_qubits: int, num_1q_gates: int, num_2q_gates: int, shots: int, weights: Dict[str, float]):
        cands = [
            {"backend": "ibm_eagle", "estimated_fidelity": 0.985, "estimated_cost": 0.002 * shots, "latency_ms": 55},
            {"backend": "google_sycamore", "estimated_fidelity": 0.980, "estimated_cost": 0.0025 * shots, "latency_ms": 35},
            {"backend": "abirqu_sim", "estimated_fidelity": 0.999, "estimated_cost": 0.00005 * shots, "latency_ms": 5},
            {"backend": "ionq_forte", "estimated_fidelity": 0.975, "estimated_cost": 0.003 * shots, "latency_ms": 200},
        ]
        for c in cands:
            c["score"] = (
                weights.get("fidelity", 0.5) * c["estimated_fidelity"]
                - weights.get("cost", 0.25) * (c["estimated_cost"] / max(1, shots))
                - weights.get("latency", 0.25) * (c["latency_ms"] / 1000.0)
            )
        pareto = sorted(cands, key=lambda x: x["score"], reverse=True)
        return {"recommended": pareto[0], "pareto_front": pareto}

    def route_circuit(self, circuit: Any, shots: int, weights: Dict[str, float]):
        """Route a specific Circuit object."""
        circuit_qubits = circuit.num_qubits
        counts = circuit.count_gates()
        num_1q_gates = sum(v for k, v in counts.items() if k not in ("CNOT", "CX", "CZ", "SWAP", "TOFFOLI", "FREDKIN"))
        num_2q_gates = sum(v for k, v in counts.items() if k in ("CNOT", "CX", "CZ", "SWAP"))
        return self.route(circuit_qubits, num_1q_gates, num_2q_gates, shots, weights)

    def route_workload(self, workload: List[Dict[str, Any]], weights: Dict[str, float]) -> List[Dict[str, Any]]:
        """Route a workload of circuits, each with its own shots parameter."""
        results = []
        for item in workload:
            circuit = item["circuit"]
            shots = item.get("shots", 1024)
            res = self.route_circuit(circuit, shots, weights)
            results.append({
                "circuit_name": getattr(circuit, "name", "unknown"),
                "recommended": res["recommended"],
                "pareto_front": res["pareto_front"]
            })
        return results


class CircuitKnitter:
    def find_optimal_cuts(self, num_qubits: int, two_qubit_gates: Sequence[Tuple[int, int]], max_fragment_qubits: int):
        a = list(range(0, num_qubits // 2))
        b = list(range(num_qubits // 2, num_qubits))
        cut = [(u, v) for u, v in two_qubit_gates if (u in a and v in b) or (u in b and v in a)]
        overhead = 2 ** len(cut)
        return {
            "partition_a": a,
            "partition_b": b,
            "fragment_sizes": [len(a), len(b)],
            "cut_edges": cut,
            "num_cuts": len(cut),
            "overhead_human": f"{overhead}x",
        }

    def execute_knitted(self, cuts: Dict[str, Any], shots: int):
        ncuts = cuts["num_cuts"]
        eff = shots * (2 ** ncuts)
        frags = [
            {"fragment_id": 0, "qubits": len(cuts["partition_a"]), "shots": eff // 2},
            {"fragment_id": 1, "qubits": len(cuts["partition_b"]), "shots": eff // 2},
        ]
        return {
            "fragments_executed": 2,
            "total_effective_shots": eff,
            "overhead_factor": 2 ** ncuts,
            "fragments": frags,
        }


class BackendGlobalMap:
    def __init__(self):
        self.backends: Dict[str, Dict[str, Any]] = {}

    def register_backend(self, name: str, provider: str, qubits: int, region: str, latency_ms: float):
        self.backends[name] = {
            "name": name,
            "provider": provider,
            "qubits": qubits,
            "region": region,
            "latency_ms": latency_ms,
            "load_percent": 0.0,
            "queue_depth": 0,
            "status": "HEALTHY",
        }

    def heartbeat(self, name: str, load_percent: float, queue_depth: int, latency_ms: float):
        b = self.backends[name]
        b["load_percent"] = load_percent
        b["queue_depth"] = queue_depth
        b["latency_ms"] = latency_ms
        b["status"] = "DEGRADED" if load_percent > 90 or queue_depth > 10 else "HEALTHY"

    def get_map(self):
        rows = []
        for b in self.backends.values():
            rows.append({
                "name": b["name"], "provider": b["provider"], "region": b["region"], "qubits": b["qubits"],
                "load": f"{b['load_percent']:.0f}%", "queue": b["queue_depth"], "status": b["status"],
            })
        healthy = sum(1 for b in self.backends.values() if b["status"] == "HEALTHY")
        degraded = len(self.backends) - healthy
        return {"total_backends": len(self.backends), "healthy": healthy, "degraded": degraded, "backends": rows}

    def get_best_available(self, min_qubits: int):
        cands = [b for b in self.backends.values() if b["qubits"] >= min_qubits]
        return sorted(cands, key=lambda x: (x["status"] != "HEALTHY", x["load_percent"], x["latency_ms"]))[0]


class CostTracker:
    def __init__(self, budget_limit: float, currency: str = "USD"):
        self.budget_limit = budget_limit
        self.currency = currency
        self.total_spent = 0.0
        self.spend_by_backend: Dict[str, float] = {}
        self.preempted: List[Dict[str, Any]] = []

    def record_cost(self, job_id: str, backend: str, shots: int, cost_per_shot: float):
        c = shots * cost_per_shot
        self.total_spent += c
        self.spend_by_backend[backend] = self.spend_by_backend.get(backend, 0.0) + c

    def check_budget(self, proposed_cost: float):
        if self.total_spent + proposed_cost > self.budget_limit:
            return {"approved": False, "action": "REJECT", "reason": "Budget exceeded"}
        if self.total_spent + proposed_cost > 0.9 * self.budget_limit:
            return {"approved": True, "action": "WARN"}
        return {"approved": True, "action": "APPROVE"}

    def preempt_job(self, job_id: str, reason: str):
        evt = {"job_id": job_id, "reason": reason}
        self.preempted.append(evt)
        return evt

    def get_summary(self):
        rem = self.budget_limit - self.total_spent
        return {
            "total_spent": round(self.total_spent, 6),
            "budget_limit": self.budget_limit,
            "budget_remaining": round(rem, 6),
            "utilization": self.total_spent / max(self.budget_limit, 1e-9),
            "preempted_jobs": len(self.preempted),
            "spend_by_backend": dict(self.spend_by_backend),
        }


class OrchestrationPipeline:
    def __init__(self, budget: float):
        self.router = MultiObjectiveRouter()
        self.global_map = BackendGlobalMap()
        self.cost = CostTracker(budget_limit=budget)
        self.global_map.register_backend("abirqu_sim", "AbirQu", 64, "global", latency_ms=5)

    def submit_job(self, job_id: str, circuit_qubits: int, num_1q_gates: int, num_2q_gates: int, shots: int):
        plan = self.router.route(circuit_qubits, num_1q_gates, num_2q_gates, shots, {"fidelity": 0.6, "cost": 0.2, "latency": 0.2})
        b = plan["recommended"]
        check = self.cost.check_budget(b["estimated_cost"])
        if not check["approved"]:
            self.cost.preempt_job(job_id, check["reason"])
            return {"job_id": job_id, "status": "REJECTED", "reason": check["reason"]}
        self.cost.record_cost(job_id, b["backend"], shots, b["estimated_cost"] / max(1, shots))
        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "backend": b["backend"],
            "cost": b["estimated_cost"],
            "budget_remaining": self.cost.get_summary()["budget_remaining"],
        }


__all__ = [
    "MultiObjectiveRouter",
    "CircuitKnitter",
    "BackendGlobalMap",
    "CostTracker",
    "OrchestrationPipeline",
]
