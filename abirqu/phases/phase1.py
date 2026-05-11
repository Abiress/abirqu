"""Phase 1: Core Engine wiring layer."""

from __future__ import annotations

from typing import Optional

from ..circuit import Circuit, Gate, Measurement
from ..measurement import MeasurementResult, SamplingEngine
from ..noise import NoiseModel
from ..simulator import SimulatorBackend


class CoreEngine:
    """Small facade that binds core circuit and simulation primitives."""

    def new_circuit(self, num_qubits: int, name: str = "") -> Circuit:
        return Circuit(num_qubits=num_qubits, name=name)

    def run(self, circuit: Circuit, shots: int = 1024, noise_model: Optional[NoiseModel] = None):
        backend = SimulatorBackend(num_qubits=circuit.num_qubits)
        return backend.run(circuit, shots=shots, noise_model=noise_model)


__all__ = [
    "CoreEngine",
    "Circuit",
    "Gate",
    "Measurement",
    "SimulatorBackend",
    "NoiseModel",
    "SamplingEngine",
    "MeasurementResult",
]
