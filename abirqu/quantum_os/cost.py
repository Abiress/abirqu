"""
Cost Estimator
==============
Estimate QPU time cost before execution.
"""

from __future__ import annotations

from typing import Dict, Optional

from ..circuit import Circuit


# Cost per shot (in credits) for different backends
BACKEND_COSTS = {
    "fast": 0.0,
    "local": 0.0,
    "ibmq_qasm_simulator": 0.0,
    "ibm_brisbane": 0.001,
    "ibm_osaka": 0.001,
    "dwave_simulated": 0.0,
    "Advantage_system6.4": 0.0005,
    "spinq-3": 0.002,
    "spinq-6": 0.002,
    "ionq_simulator": 0.0,
    "ionq_qpu": 0.01,
    "cirq_simulator": 0.0,
    "fresnel": 0.001,
    "aquila": 0.0005,
}


class CostEstimator:
    """Estimate the cost of running a quantum circuit.

    Parameters
    ----------
    default_cost_per_shot : float
        Default cost per shot for unknown backends.
    """

    def __init__(self, default_cost_per_shot: float = 0.001):
        self.default_cost_per_shot = default_cost_per_shot
        self._costs = dict(BACKEND_COSTS)

    def estimate(
        self,
        circuit: Circuit,
        backend_name: str,
        shots: int = 1024,
    ) -> Dict[str, float]:
        """Estimate the cost of running a circuit.

        Returns
        -------
        dict with keys:
            shots         – int
            cost_per_shot – float
            total_cost    – float
            estimated_time_us – float
            backend       – str
        """
        cost_per_shot = self._costs.get(backend_name, self.default_cost_per_shot)
        total_cost = cost_per_shot * shots

        # Estimate execution time
        num_gates = len(getattr(circuit, "gates", []))
        num_2q = sum(1 for g in getattr(circuit, "gates", []) if len(g.qubits) > 1)

        # Rough time estimates
        gate_time_1q = 35.0  # ns
        gate_time_2q = 300.0  # ns
        exec_time_ns = (num_gates - num_2q) * gate_time_1q + num_2q * gate_time_2q
        exec_time_us = exec_time_ns / 1000.0

        return {
            "shots": shots,
            "cost_per_shot": cost_per_shot,
            "total_cost": total_cost,
            "estimated_time_us": exec_time_us,
            "backend": backend_name,
        }

    def set_cost(self, backend_name: str, cost_per_shot: float):
        """Set the cost for a specific backend."""
        self._costs[backend_name] = cost_per_shot

    def get_cost(self, backend_name: str) -> float:
        """Get the cost per shot for a backend."""
        return self._costs.get(backend_name, self.default_cost_per_shot)

    def compare_backends(
        self,
        circuit: Circuit,
        backends: list,
        shots: int = 1024,
    ) -> list:
        """Compare costs across multiple backends."""
        results = []
        for backend in backends:
            est = self.estimate(circuit, backend, shots)
            results.append(est)
        return sorted(results, key=lambda x: x["total_cost"])
