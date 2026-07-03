"""
SpinQ Calibration
=================
Load and manage calibration data for SpinQ trapped-ion processors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SpinQCalibration:
    """Calibration data for a SpinQ trapped-ion processor.

    Attributes
    ----------
    device_name : str
        Name of the processor (e.g. 'SpinQ-3').
    num_qubits : int
        Number of qubits.
    qubit_frequencies : dict
        Transition frequencies per qubit (MHz).
    gate_fidelities : dict
        Gate fidelity measurements.
    T1 : dict
        T1 relaxation times per qubit (seconds).
    T2 : dict
        T2 dephasing times per qubit (seconds).
    ms_time : float
        Molmer-Sorensen gate time (microseconds).
    single_qubit_gate_time : float
        Single-qubit gate time (microseconds).
    readout_fidelity : dict
        Readout fidelity per qubit.
    """
    device_name: str = "SpinQ-3"
    num_qubits: int = 3
    qubit_frequencies: Dict[int, float] = field(default_factory=dict)
    gate_fidelities: Dict[str, float] = field(default_factory=dict)
    T1: Dict[int, float] = field(default_factory=dict)
    T2: Dict[int, float] = field(default_factory=dict)
    ms_time: float = 200.0
    single_qubit_gate_time: float = 10.0
    readout_fidelity: Dict[int, float] = field(default_factory=dict)

    @classmethod
    def default_3q(cls) -> "SpinQCalibration":
        """Default calibration for SpinQ-3."""
        import numpy as np
        return cls(
            device_name="SpinQ-3",
            num_qubits=3,
            qubit_frequencies={0: 500.0, 1: 502.0, 2: 504.0},
            gate_fidelities={
                "Rz": 0.9995,
                "Rx": 0.9993,
                "MS": 0.992,
            },
            T1={i: 10.0 + np.random.uniform(-0.5, 0.5) for i in range(3)},
            T2={i: 1.0 + np.random.uniform(-0.05, 0.05) for i in range(3)},
            ms_time=200.0,
            single_qubit_gate_time=10.0,
            readout_fidelity={i: 0.995 + np.random.uniform(0, 0.004) for i in range(3)},
        )

    @classmethod
    def default_6q(cls) -> "SpinQCalibration":
        """Default calibration for SpinQ-6."""
        import numpy as np
        return cls(
            device_name="SpinQ-6",
            num_qubits=6,
            qubit_frequencies={i: 500.0 + i * 2.0 for i in range(6)},
            gate_fidelities={
                "Rz": 0.9994,
                "Rx": 0.9992,
                "MS": 0.990,
            },
            T1={i: 10.0 + np.random.uniform(-0.5, 0.5) for i in range(6)},
            T2={i: 1.0 + np.random.uniform(-0.05, 0.05) for i in range(6)},
            ms_time=200.0,
            single_qubit_gate_time=10.0,
            readout_fidelity={i: 0.994 + np.random.uniform(0, 0.005) for i in range(6)},
        )

    def estimate_circuit_fidelity(self, num_single_qubit: int, num_ms: int) -> float:
        """Estimate circuit fidelity from gate counts."""
        fidelity_1q = self.gate_fidelities.get("Rx", 0.999)
        fidelity_ms = self.gate_fidelities.get("MS", 0.99)
        readout = sum(self.readout_fidelity.values()) / self.num_qubits
        return (fidelity_1q ** num_single_qubit) * (fidelity_ms ** num_ms) * readout

    def estimate_circuit_time(self, num_single_qubit: int, num_ms: int) -> float:
        """Estimate total circuit execution time (microseconds)."""
        return (num_single_qubit * self.single_qubit_gate_time +
                num_ms * self.ms_time)

    def to_dict(self) -> Dict[str, Any]:
        """Export calibration as a dictionary."""
        return {
            "device_name": self.device_name,
            "num_qubits": self.num_qubits,
            "qubit_frequencies": self.qubit_frequencies,
            "gate_fidelities": self.gate_fidelities,
            "T1": self.T1,
            "T2": self.T2,
            "ms_time": self.ms_time,
            "single_qubit_gate_time": self.single_qubit_gate_time,
            "readout_fidelity": self.readout_fidelity,
        }
