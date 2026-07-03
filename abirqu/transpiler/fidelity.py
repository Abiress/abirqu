"""
Fidelity Estimator
==================
Estimate circuit fidelity from noise model and gate counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..circuit import Circuit


@dataclass
class FidelityEstimate:
    """Estimated fidelity metrics for a circuit."""
    overall_fidelity: float
    gate_fidelity: float
    readout_fidelity: float
    depth: int
    num_gates: int
    num_two_qubit_gates: int
    estimated_execution_time_us: float


class FidelityEstimator:
    """Estimate circuit fidelity for a target backend.

    Parameters
    ----------
    gate_error_1q : float
        Single-qubit gate error rate.
    gate_error_2q : float
        Two-qubit gate error rate.
    readout_error : float
        Readout error per qubit.
    gate_time_1q : float
        Single-qubit gate time (ns).
    gate_time_2q : float
        Two-qubit gate time (ns).
    """

    def __init__(
        self,
        gate_error_1q: float = 0.0003,
        gate_error_2q: float = 0.005,
        readout_error: float = 0.01,
        gate_time_1q: float = 35.0,
        gate_time_2q: float = 300.0,
    ):
        self.gate_error_1q = gate_error_1q
        self.gate_error_2q = gate_error_2q
        self.readout_error = readout_error
        self.gate_time_1q = gate_time_1q
        self.gate_time_2q = gate_time_2q

    def estimate(self, circuit: Circuit) -> FidelityEstimate:
        """Estimate fidelity for the given circuit."""
        gates = getattr(circuit, "gates", [])
        num_gates = len(gates)
        num_1q = sum(1 for g in gates if len(g.qubits) == 1)
        num_2q = sum(1 for g in gates if len(g.qubits) > 1)

        # Gate fidelity
        fidelity_1q = (1 - self.gate_error_1q) ** num_1q
        fidelity_2q = (1 - self.gate_error_2q) ** num_2q
        gate_fidelity = fidelity_1q * fidelity_2q

        # Readout fidelity
        readout_fidelity = (1 - self.readout_error) ** circuit.num_qubits

        # Overall fidelity
        overall = gate_fidelity * readout_fidelity

        # Execution time
        exec_time = (num_1q * self.gate_time_1q + num_2q * self.gate_time_2q) / 1000.0

        return FidelityEstimate(
            overall_fidelity=overall,
            gate_fidelity=gate_fidelity,
            readout_fidelity=readout_fidelity,
            depth=num_gates,
            num_gates=num_gates,
            num_two_qubit_gates=num_2q,
            estimated_execution_time_us=exec_time,
        )

    @classmethod
    def for_ibm(cls) -> "FidelityEstimator":
        """Fidelity estimator for IBM Brisbane."""
        return cls(
            gate_error_1q=0.0001,
            gate_error_2q=0.003,
            readout_error=0.005,
            gate_time_1q=35.0,
            gate_time_2q=300.0,
        )

    @classmethod
    def for_spinq(cls) -> "FidelityEstimator":
        """Fidelity estimator for SpinQ trapped-ion."""
        return cls(
            gate_error_1q=0.0005,
            gate_error_2q=0.01,
            readout_error=0.005,
            gate_time_1q=10.0,
            gate_time_2q=200.0,
        )

    @classmethod
    def for_neutral_atom(cls) -> "FidelityEstimator":
        """Fidelity estimator for neutral atom (Pasqal/QuEra)."""
        return cls(
            gate_error_1q=0.001,
            gate_error_2q=0.015,
            readout_error=0.02,
            gate_time_1q=500.0,
            gate_time_2q=1000.0,
        )
