"""Advanced algorithm wrappers backed by concrete AbirQu templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from . import qaoa_maxcut, vqe_hardware_efficient


class AlgorithmType:
    QAOA = "QAOA"
    VQE = "VQE"


@dataclass
class AlgorithmResult:
    success: bool
    output: Dict[str, Any]


class _AdvancedAlgorithm:
    def __init__(self, kind: str, **kwargs):
        self.kind = kind.upper()
        self.kwargs = kwargs
        self.circuit = None

    def build(self):
        if self.kind == AlgorithmType.QAOA:
            self.circuit = qaoa_maxcut(
                num_qubits=int(self.kwargs.get("num_qubits", 4)),
                edges=self.kwargs.get("edges", [(0, 1), (1, 2), (2, 3)]),
                beta=float(self.kwargs.get("beta", 0.4)),
                gamma=float(self.kwargs.get("gamma", 0.7)),
            )
            return self.circuit

        if self.kind == AlgorithmType.VQE:
            self.circuit = vqe_hardware_efficient(
                num_qubits=int(self.kwargs.get("num_qubits", 4)),
                depth=int(self.kwargs.get("depth", 2)),
            )
            return self.circuit

        raise ValueError(f"Unknown algorithm type: {self.kind}")

    def optimize(self, cost_h):
        if self.circuit is None:
            self.build()
        shots = int(self.kwargs.get("shots", 512))
        run_result = self.circuit.run(shots=shots)
        best_probability = max(run_result.get("probabilities", {}).values(), default=0.0)
        energy_estimate = -float(best_probability)
        return AlgorithmResult(
            success=bool(run_result.get("success", True)),
            output={
                "optimal_energy": energy_estimate,
                "cost_hamiltonian": cost_h,
                "shots": shots,
            },
        )

    def compute_ground_state(self, h):
        if self.circuit is None:
            self.build()
        shots = int(self.kwargs.get("shots", 512))
        run_result = self.circuit.run(shots=shots)
        best_probability = max(run_result.get("probabilities", {}).values(), default=0.0)
        return AlgorithmResult(
            success=bool(run_result.get("success", True)),
            output={
                "ground_energy": -float(best_probability),
                "hamiltonian": h,
                "shots": shots,
            },
        )


def create_algorithm(type, **kwargs):
    return _AdvancedAlgorithm(type, **kwargs)
