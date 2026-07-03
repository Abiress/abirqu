"""
QuEra Transpiler
================
Decompose AbirQu circuits to QuEra Aquila analog Hamiltonian format.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np

from ...circuit import Circuit


def transpile_to_analog_hamiltonian(
    circuit: Circuit,
    atom_spacing: float = 8.0,
) -> Dict[str, Any]:
    """Convert an AbirQu circuit to an analog Hamiltonian program.

    QuEra Aquila operates on the analog Hamiltonian model:
    H = Ω/2 Σ_i σ_x^i - Δ Σ_i n_i + V Σ_{i<j} n_i n_j / |r_i - r_j|^6

    This converter maps gate operations to pulse sequences.

    Parameters
    ----------
    circuit : Circuit
        The AbirQu circuit to convert.
    atom_spacing : float
        Spacing between atoms in micrometers.

    Returns
    -------
    dict with 'setup' and 'hamiltonian' keys.
    """
    n = circuit.num_qubits

    # Place atoms in a linear chain
    sites = [{"x": float(i * atom_spacing), "y": 0.0} for i in range(n)]
    filling = [1] * n

    # Build pulse sequence from circuit gates
    pulses = []
    for gate in getattr(circuit, "gates", []):
        name = gate.name.upper()
        qubits = list(gate.qubits)
        params = list(gate.params)

        if name in ("H", "X", "Y"):
            # Single-qubit rotation → global pulse
            pulses.append({
                "type": "global",
                "amplitude": 1.0,
                "detuning": 0.0,
                "phase": 0.0,
                "duration": 1.0,
                "qubits": qubits,
            })
        elif name in ("CNOT", "CX", "CZ"):
            # Two-qubit gate → local pulse with Rydberg interaction
            pulses.append({
                "type": "local",
                "amplitude": 0.5,
                "detuning": 100.0,
                "phase": 0.0,
                "duration": 2.0,
                "qubits": qubits,
            })
        elif name in ("RX", "RY", "RZ"):
            angle = float(params[0])
            pulses.append({
                "type": "global",
                "amplitude": float(np.abs(np.sin(angle / 2))),
                "detuning": float(np.cos(angle / 2)),
                "phase": 0.0,
                "duration": 1.0,
                "qubits": qubits,
            })

    return {
        "setup": {
            "atomArray": {
                "sites": sites,
                "filling": filling,
            }
        },
        "hamiltonian": {
            "pulses": pulses,
            "global_detuning": 0.0,
            "max_amplitude": 2 * np.pi,
            "time": float(len(pulses) * 1.0),
        },
    }


def analog_hamiltonian_to_qasm(program: Dict[str, Any], num_qubits: int) -> str:
    """Convert an analog Hamiltonian program to a simplified QASM representation.

    This is a best-effort conversion for visualization purposes.
    """
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{num_qubits}];",
        f"creg c[{num_qubits}];",
    ]

    pulses = program.get("hamiltonian", {}).get("pulses", [])
    for pulse in pulses:
        qubits = pulse.get("qubits", [])
        ptype = pulse.get("type", "global")
        amp = pulse.get("amplitude", 0)

        if ptype == "global" and len(qubits) == 1:
            if amp > 0.5:
                lines.append(f"rx({amp * np.pi}) q[{qubits[0]}];")
            else:
                lines.append(f"rz({amp * np.pi}) q[{qubits[0]}];")
        elif ptype == "local" and len(qubits) == 2:
            lines.append(f"cz q[{qubits[0]}],q[{qubits[1]}];")

    for i in range(num_qubits):
        lines.append(f"measure q[{i}] -> c[{i}];")

    return "\n".join(lines)
