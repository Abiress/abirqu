"""
AbirQu Plugin: Google Sycamore Noise Model
Provides realistic noise parameters from Google's Sycamore processor.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


PLUGIN_NAME = "google_noise"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "Realistic noise model based on Google Sycamore quantum processor"


@dataclass
class SycamoreGateError:
    gate: str
    error_rate: float
    gate_time_ns: float


# Google Sycamore calibrated gate error rates (publicly reported values)
SYCAMORE_GATE_ERRORS: List[SycamoreGateError] = [
    SycamoreGateError("H",     error_rate=0.0015, gate_time_ns=25.0),
    SycamoreGateError("X",     error_rate=0.0012, gate_time_ns=20.0),
    SycamoreGateError("Y",     error_rate=0.0012, gate_time_ns=20.0),
    SycamoreGateError("Z",     error_rate=0.0001, gate_time_ns=5.0),
    SycamoreGateError("SX",    error_rate=0.0012, gate_time_ns=20.0),
    SycamoreGateError("CNOT",  error_rate=0.0062, gate_time_ns=32.0),
    SycamoreGateError("CZ",    error_rate=0.0062, gate_time_ns=32.0),
    SycamoreGateError("FSIM",  error_rate=0.0060, gate_time_ns=32.0),
    SycamoreGateError("RESET", error_rate=0.0050, gate_time_ns=500.0),
]


class GoogleSycamoreNoiseModel:
    """
    Noise model calibrated to Google Sycamore 53-qubit processor.

    Parameters based on publicly available data from the Google Quantum AI team.
    Includes T1/T2 decoherence, gate errors, and readout errors.
    """

    def __init__(self, qubit_count: int = 53):
        self.qubit_count = qubit_count
        # Sycamore typical coherence times
        self.T1_us = 15.0         # microseconds (T1 relaxation)
        self.T2_us = 10.0         # microseconds (T2 dephasing)
        self.readout_error = 0.038  # 3.8% readout error (reported)
        self._gate_errors = {g.gate: g for g in SYCAMORE_GATE_ERRORS}

    def get_gate_error(self, gate_name: str) -> float:
        entry = self._gate_errors.get(gate_name.upper())
        return entry.error_rate if entry else 0.002

    def get_gate_time_ns(self, gate_name: str) -> float:
        entry = self._gate_errors.get(gate_name.upper())
        return entry.gate_time_ns if entry else 25.0

    def decoherence_factor(self, gate_time_ns: float) -> float:
        """Compute amplitude damping factor from T1 decoherence."""
        t_us = gate_time_ns / 1000.0
        import math
        return math.exp(-t_us / self.T1_us)

    def apply_to_circuit(self, circuit_gates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply Sycamore noise model to a list of circuit gates.
        Returns noise characterization per gate.
        """
        total_error = 0.0
        gate_log = []
        for op in circuit_gates:
            name = op.get("gate", "H")
            err = self.get_gate_error(name)
            t_ns = self.get_gate_time_ns(name)
            dec = self.decoherence_factor(t_ns)
            total_error += err
            gate_log.append({
                "gate": name,
                "qubits": op.get("qubits", []),
                "error_rate": err,
                "gate_time_ns": t_ns,
                "decoherence_factor": round(dec, 6),
            })

        avg_fid = max(0.0, 1.0 - total_error / max(1, len(circuit_gates)))
        return {
            "backend": "Google Sycamore",
            "qubits": self.qubit_count,
            "T1_us": self.T1_us,
            "T2_us": self.T2_us,
            "readout_error": self.readout_error,
            "gates_analyzed": len(circuit_gates),
            "average_gate_fidelity": round(avg_fid, 6),
            "gate_log": gate_log,
        }

    def benchmark_report(self) -> Dict[str, Any]:
        return {
            "processor": "Google Sycamore",
            "qubit_count": self.qubit_count,
            "topology": "2D grid with nearest-neighbor connectivity",
            "gate_set": ["H", "X", "Y", "Z", "SX", "CZ", "FSIM", "RESET"],
            "1q_gate_fidelity": 0.9985,
            "2q_gate_fidelity": 0.9938,
            "readout_fidelity": round(1 - self.readout_error, 4),
            "T1_us": self.T1_us,
            "T2_us": self.T2_us,
        }


def on_circuit_run(data: Any) -> Dict[str, Any]:
    """Hook: intercept circuit run and inject Sycamore noise."""
    model = GoogleSycamoreNoiseModel()
    gates = data.get("gates", []) if isinstance(data, dict) else []
    return model.apply_to_circuit(gates)


def get_noise_model(qubit_count: int = 53) -> GoogleSycamoreNoiseModel:
    """Factory function - returns a configured Sycamore noise model."""
    return GoogleSycamoreNoiseModel(qubit_count=qubit_count)
