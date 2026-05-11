"""
AbirQu Plugin: IBM Falcon/Eagle Noise Model
Provides realistic noise parameters from IBM Quantum processors.
"""
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


PLUGIN_NAME = "ibm_noise"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "Realistic noise model based on IBM Quantum Eagle/Falcon processors"


@dataclass
class IBMGateError:
    gate: str
    error_rate: float
    gate_time_ns: float


# IBM Eagle (127-qubit) reported gate error rates
EAGLE_GATE_ERRORS: List[IBMGateError] = [
    IBMGateError("H",     error_rate=0.0002, gate_time_ns=35.6),
    IBMGateError("X",     error_rate=0.0002, gate_time_ns=35.6),
    IBMGateError("SX",    error_rate=0.0002, gate_time_ns=35.6),
    IBMGateError("RZ",    error_rate=0.0000, gate_time_ns=0.0),    # Virtual gate
    IBMGateError("CNOT",  error_rate=0.0072, gate_time_ns=519.1),
    IBMGateError("CX",    error_rate=0.0072, gate_time_ns=519.1),
    IBMGateError("ECR",   error_rate=0.0065, gate_time_ns=480.0),
    IBMGateError("RESET", error_rate=0.0030, gate_time_ns=1200.0),
    IBMGateError("MEASURE",error_rate=0.0152, gate_time_ns=4000.0),
]

# IBM Falcon (27-qubit) reported gate error rates
FALCON_GATE_ERRORS: List[IBMGateError] = [
    IBMGateError("H",     error_rate=0.0003, gate_time_ns=35.6),
    IBMGateError("X",     error_rate=0.0003, gate_time_ns=35.6),
    IBMGateError("SX",    error_rate=0.0003, gate_time_ns=35.6),
    IBMGateError("RZ",    error_rate=0.0000, gate_time_ns=0.0),
    IBMGateError("CNOT",  error_rate=0.0082, gate_time_ns=363.0),
    IBMGateError("CX",    error_rate=0.0082, gate_time_ns=363.0),
    IBMGateError("RESET", error_rate=0.0040, gate_time_ns=1200.0),
    IBMGateError("MEASURE",error_rate=0.0182, gate_time_ns=4000.0),
]


class IBMQuantumNoiseModel:
    """
    Noise model calibrated to IBM Quantum Eagle (127-qubit) or Falcon (27-qubit).

    Models:
    - Depolarizing error per gate
    - T1/T2 decoherence during gate time
    - Readout (measurement) errors
    - Thermal relaxation
    """

    def __init__(self, processor: str = "eagle"):
        self.processor = processor.lower()
        if self.processor == "eagle":
            errors = EAGLE_GATE_ERRORS
            self.qubit_count = 127
            self.T1_us = 200.0
            self.T2_us = 180.0
            self.readout_error = 0.0152
        else:  # falcon
            errors = FALCON_GATE_ERRORS
            self.qubit_count = 27
            self.T1_us = 120.0
            self.T2_us = 100.0
            self.readout_error = 0.0182

        self._gate_errors = {g.gate: g for g in errors}

    def get_gate_error(self, gate_name: str) -> float:
        entry = self._gate_errors.get(gate_name.upper())
        return entry.error_rate if entry else 0.0003

    def get_gate_time_ns(self, gate_name: str) -> float:
        entry = self._gate_errors.get(gate_name.upper())
        return entry.gate_time_ns if entry else 35.6

    def thermal_relaxation_factor(self, gate_time_ns: float) -> Dict[str, float]:
        """Compute T1/T2 relaxation during a gate."""
        t_us = gate_time_ns / 1000.0
        amp_damp = math.exp(-t_us / self.T1_us)
        phase_damp = math.exp(-t_us / self.T2_us)
        return {"T1_factor": amp_damp, "T2_factor": phase_damp}

    def apply_to_circuit(self, circuit_gates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply IBM noise model to a circuit and return characterization."""
        total_error = 0.0
        gate_log = []
        for op in circuit_gates:
            name = op.get("gate", "H")
            err = self.get_gate_error(name)
            t_ns = self.get_gate_time_ns(name)
            relax = self.thermal_relaxation_factor(t_ns)
            total_error += err
            gate_log.append({
                "gate": name,
                "qubits": op.get("qubits", []),
                "error_rate": err,
                "gate_time_ns": t_ns,
                "T1_factor": round(relax["T1_factor"], 6),
                "T2_factor": round(relax["T2_factor"], 6),
            })

        avg_fid = max(0.0, 1.0 - total_error / max(1, len(circuit_gates)))
        return {
            "backend": f"IBM {self.processor.capitalize()}",
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
            "processor": f"IBM {self.processor.capitalize()}",
            "qubit_count": self.qubit_count,
            "topology": "Heavy-hex lattice" if self.processor == "eagle" else "Heavy-hex 27q",
            "gate_set": ["H", "X", "SX", "RZ", "CNOT", "ECR", "RESET", "MEASURE"],
            "1q_gate_fidelity": round(1 - 0.0002, 4),
            "2q_gate_fidelity": round(1 - 0.0072, 4),
            "readout_fidelity": round(1 - self.readout_error, 4),
            "T1_us": self.T1_us,
            "T2_us": self.T2_us,
        }


def on_circuit_run(data: Any) -> Dict[str, Any]:
    """Hook: intercept circuit run and inject IBM Eagle noise."""
    model = IBMQuantumNoiseModel(processor="eagle")
    gates = data.get("gates", []) if isinstance(data, dict) else []
    return model.apply_to_circuit(gates)


def get_noise_model(processor: str = "eagle") -> IBMQuantumNoiseModel:
    """Factory function - returns a configured IBM noise model."""
    return IBMQuantumNoiseModel(processor=processor)
