from typing import Any, Dict, Iterable, List, Optional


class PhysicalResourceCalculator:
    def estimate(
        self,
        logical_qubits: int,
        logical_gates: int,
        code_distance: int,
        physical_gate_time_ns: float,
        physical_error_rate: float,
    ) -> Dict[str, Any]:
        physical_qubits = logical_qubits * (2 * code_distance - 1) ** 2
        physical_gates = logical_gates * max(1, 4 * code_distance)
        time_seconds = (physical_gates * physical_gate_time_ns) * 1e-9
        return {
            "physical_qubits": int(physical_qubits),
            "physical_gates": int(physical_gates),
            "time_seconds": time_seconds,
            "error_rate": physical_error_rate,
            "breakdown": {
                "data_qubits": int(0.7 * physical_qubits),
                "ancilla_qubits": int(0.3 * physical_qubits),
            },
        }


class ErrorBudgetManager:
    def allocate(self, total_error_budget: float, components: Dict[str, float]) -> Dict[str, float]:
        weight_sum = sum(max(v, 0.0) for v in components.values())
        if weight_sum == 0:
            return {k: 0.0 for k in components}
        return {k: total_error_budget * max(v, 0.0) / weight_sum for k, v in components.items()}

    def what_if_code_distance(self, base_resources: Dict[str, Any], new_distance: int, old_distance: int) -> Dict[str, Any]:
        ratio = float(new_distance) / float(max(old_distance, 1))
        return {
            "qubit_scale": ratio ** 2,
            "gate_scale": ratio,
            "new_physical_qubits": int(base_resources["physical_qubits"] * ratio ** 2),
            "new_physical_gates": int(base_resources["physical_gates"] * ratio),
        }


class HardwareRequirementProfiler:
    def profile(self, required_qubits: int, required_fidelity: float) -> Dict[str, Any]:
        threshold_error_rate = max(1e-6, 1.0 - required_fidelity)
        return {
            "min_qubits": required_qubits,
            "min_fidelity": required_fidelity,
            "threshold_error_rate": threshold_error_rate,
        }

    def compare_backends(self, requirements: Dict[str, Any], backends: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for b in backends:
            ok = b.get("qubits", 0) >= requirements["min_qubits"] and b.get("fidelity", 0.0) >= requirements["min_fidelity"]
            out.append({"backend": b.get("name"), "eligible": ok, "score": b.get("fidelity", 0.0) * min(1.0, b.get("qubits", 0) / float(requirements["min_qubits"]))})
        return sorted(out, key=lambda x: x["score"], reverse=True)


class CostEstimationEngine:
    def __init__(self) -> None:
        self.history: List[Dict[str, Any]] = []

    def estimate(self, backend_name: str, shots: int, price_per_shot: float, overhead: float = 1.0) -> Dict[str, Any]:
        cost = float(shots) * float(price_per_shot) * float(overhead)
        row = {"backend": backend_name, "shots": shots, "estimated_cost": cost}
        self.history.append(row)
        return row

    def compare(self, estimates: Iterable[Dict[str, Any]], budget: Optional[float] = None) -> List[Dict[str, Any]]:
        rows = sorted(list(estimates), key=lambda x: x["estimated_cost"])
        if budget is not None:
            for r in rows:
                r["within_budget"] = r["estimated_cost"] <= budget
        return rows


class FeasibilityAssessmentTool:
    def assess(
        self,
        resource_estimate: Dict[str, Any],
        hardware_profile: Dict[str, Any],
        cost_options: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        feasible_hardware = hardware_profile.get("min_qubits", 0) <= resource_estimate.get("physical_qubits", 0)
        cheapest = min(cost_options, key=lambda x: x["estimated_cost"]) if cost_options else None
        practical = feasible_hardware and (cheapest is not None)
        timeline = "near-term" if practical else "long-term"
        recommendation = "Proceed with pilot" if practical else "Reduce qubits/depth and retry"
        return {
            "practical": practical,
            "timeline": timeline,
            "cheapest_option": cheapest,
            "recommendation": recommendation,
        }
