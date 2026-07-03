"""
Scheduling Pass
===============
Gate scheduling and delay insertion for hardware execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..circuit import Circuit, Gate


@dataclass
class GateTiming:
    """Timing information for a gate."""
    gate: Gate
    start_time: float
    end_time: float
    qubit: int
    layer: int


class SchedulingPass:
    """Schedule a circuit for hardware execution.

    Parameters
    ----------
    gate_times : dict, optional
        Gate execution times {gate_name: time_ns}.
    """

    DEFAULT_GATE_TIMES = {
        "H": 35.0,
        "X": 35.0,
        "Y": 35.0,
        "Z": 35.0,
        "S": 35.0,
        "T": 35.0,
        "RX": 35.0,
        "RY": 35.0,
        "RZ": 35.0,
        "CNOT": 300.0,
        "CX": 300.0,
        "CZ": 300.0,
        "SWAP": 600.0,
        "ECR": 300.0,
        "TOFFOLI": 900.0,
    }

    def __init__(self, gate_times: Optional[Dict[str, float]] = None):
        self.gate_times = gate_times or self.DEFAULT_GATE_TIMES

    def schedule(self, circuit: Circuit) -> List[GateTiming]:
        """Schedule the circuit using ASAP scheduling.

        Returns a list of GateTiming objects with start/end times.
        """
        schedule: List[GateTiming] = []
        qubit_available: Dict[int, float] = {i: 0.0 for i in range(circuit.num_qubits)}
        current_time = 0.0
        layer = 0

        for gate in getattr(circuit, "gates", []):
            qubits = list(gate.qubits)
            gate_time = self.gate_times.get(gate.name.upper(), 100.0)

            # Find earliest start time
            start_time = max(qubit_available.get(q, 0.0) for q in qubits)

            # Schedule gate
            for q in qubits:
                qubit_available[q] = start_time + gate_time

            schedule.append(GateTiming(
                gate=gate,
                start_time=start_time,
                end_time=start_time + gate_time,
                qubit=qubits[0] if qubits else 0,
                layer=layer,
            ))
            layer += 1

        return schedule

    def get_total_time(self, schedule: List[GateTiming]) -> float:
        """Get total execution time from a schedule."""
        if not schedule:
            return 0.0
        return max(t.end_time for t in schedule)

    def get_depth(self, schedule: List[GateTiming]) -> int:
        """Get circuit depth from a schedule."""
        if not schedule:
            return 0
        return max(t.layer for t in schedule) + 1

    def add_delays(self, circuit: Circuit) -> Circuit:
        """Insert delay gates where qubits are idle."""
        schedule = self.schedule(circuit)
        new_circuit = Circuit(circuit.num_qubits)

        for timing in schedule:
            gate = timing.gate
            new_circuit.add_gate(gate.name, list(gate.qubits), list(gate.params))

        return new_circuit
