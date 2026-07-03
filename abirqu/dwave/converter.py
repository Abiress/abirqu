"""
D-Wave Circuit Converter
========================
Convert AbirQu circuits to D-Wave QUBO/Ising models for quantum annealing.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from ..circuit import Circuit
from .qubo import QUBOBuilder


def circuit_to_qubo(circuit: Circuit) -> QUBOBuilder:
    """Convert an AbirQu quantum circuit to a QUBO model.

    This is a simplified converter that maps gate operations to
    binary quadratic biases.  For production use, the circuit should
    be decomposed to the native gate set first.

    Parameters
    ----------
    circuit : Circuit
        The AbirQu circuit to convert.

    Returns
    -------
    QUBOBuilder ready to be solved by D-Wave.
    """
    n = circuit.num_qubits
    builder = QUBOBuilder(num_variables=n)

    # Process gates
    for gate in getattr(circuit, "gates", []):
        name = gate.name.upper()
        qubits = list(gate.qubits)
        params = list(gate.params)

        if name == "X":
            # X gate → flip bias → favor |1⟩
            builder.set_linear(qubits[0], -1.0)

        elif name in ("H",):
            # Hadamard → equal superposition → zero bias
            builder.set_linear(qubits[0], 0.0)

        elif name in ("CNOT", "CX"):
            # CNOT → quadratic coupling
            ctrl, tgt = qubits[0], qubits[1]
            builder.set_linear(ctrl, 0.0)
            builder.set_linear(tgt, 0.0)
            # CNOT creates correlation: ctrl=1 → flip tgt
            builder.set_quadratic(ctrl, tgt, 1.0)

        elif name == "CZ":
            # CZ → quadratic coupling
            builder.set_quadratic(qubits[0], qubits[1], 1.0)

        elif name in ("RX", "RY", "RZ"):
            # Rotation gates → partial bias
            angle = float(params[0]) if params else 0.0
            builder.set_linear(qubits[0], -np.cos(angle / 2))

        elif name == "SWAP":
            # SWAP → bidirectional coupling
            builder.set_quadratic(qubits[0], qubits[1], 1.0)

    return builder


def circuit_to_ising(circuit: Circuit) -> Tuple[Dict[str, float], Dict[Tuple[str, str], float]]:
    """Convert an AbirQu circuit to an Ising model.

    Returns
    -------
    (linear, quadratic) where:
        linear    – Dict[str, float] spin biases
        quadratic – Dict[Tuple[str,str], float] spin couplings
    """
    builder = circuit_to_qubo(circuit)
    return builder.to_ising()


def qubo_to_qasm(qubo: QUBOBuilder, num_qubits: int) -> str:
    """Convert a QUBO model to a simple QASM circuit.

    This creates a circuit that encodes the QUBO as a quantum
    annealing schedule (simplified for gate-based machines).
    """
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{num_qubits}];",
        f"creg c[{num_qubits}];",
    ]

    qubo_dict = qubo.build()

    # Add single-qubit biases as Rz rotations
    for i, bias in qubo_dict["linear"].items():
        if bias != 0:
            lines.append(f"rz({bias}) q[{i}];")

    # Add two-qubit couplings as CNOT gates
    for (i, j), bias in qubo_dict["quadratic"].items():
        if bias != 0:
            lines.append(f"h q[{i}];")
            lines.append(f"h q[{j}];")
            lines.append(f"cx q[{i}],q[{j}];")

    # Measurements
    for i in range(num_qubits):
        lines.append(f"measure q[{i}] -> c[{i}];")

    return "\n".join(lines)
