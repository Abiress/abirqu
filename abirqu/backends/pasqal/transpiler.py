"""
Neutral Atom Transpiler
=======================
Decompose AbirQu circuits to neutral atom native gate set.
"""

from __future__ import annotations

import numpy as np

from ...circuit import Circuit


NEUTRAL_ATOM_NATIVE_GATES = ["Ry", "Rz", "MS", "CZ"]


def transpile_to_neutral_atom_native(circuit: Circuit) -> str:
    """Transpile an AbirQu circuit to neutral atom native gates.

    Neutral atom (Rydberg) native gate set:
    - Ry(θ) — Y-rotation (via global/local addressing)
    - Rz(θ) — Z-rotation (via AC Stark shift)
    - CZ — Controlled-Z (via Rydberg blockade)
    - MS — Molmer-Sorensen (via Rydberg interaction)

    The CZ gate is the native two-qubit gate for neutral atoms,
    implemented via the Rydberg blockade mechanism.
    """
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{circuit.num_qubits}];",
        f"creg c[{circuit.num_qubits}];",
    ]

    for gate in getattr(circuit, "gates", []):
        name = gate.name.upper()
        qubits = list(gate.qubits)
        params = list(gate.params)

        if name == "H":
            # H = Rz(π).Ry(π/2).Rz(0)
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")
            lines.append(f"ry({np.pi / 2}) q[{qubits[0]}];")

        elif name == "X":
            lines.append(f"ry({np.pi}) q[{qubits[0]}];")

        elif name == "Y":
            lines.append(f"ry({np.pi}) q[{qubits[0]}];")

        elif name == "Z":
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")

        elif name == "S":
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")

        elif name == "T":
            lines.append(f"rz({np.pi / 4}) q[{qubits[0]}];")

        elif name == "RX":
            angle = float(params[0])
            lines.append(f"ry({-np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"rz({angle}) q[{qubits[0]}];")
            lines.append(f"ry({np.pi / 2}) q[{qubits[0]}];")

        elif name == "RY":
            angle = float(params[0])
            lines.append(f"ry({angle}) q[{qubits[0]}];")

        elif name == "RZ":
            angle = float(params[0])
            lines.append(f"rz({angle}) q[{qubits[0]}];")

        elif name in ("CNOT", "CX"):
            # CNOT via CZ + Hadamards
            lines.append(f"rz({np.pi}) q[{qubits[1]}];")
            lines.append(f"ry({np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"cz q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"ry({-np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"rz({np.pi}) q[{qubits[1]}];")

        elif name == "CZ":
            lines.append(f"cz q[{qubits[0]}],q[{qubits[1]}];")

        elif name == "SWAP":
            # SWAP = 3 CZs
            lines.append(f"cz q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"ry({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")
            lines.append(f"ry({-np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"cz q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"ry({np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"rz({np.pi}) q[{qubits[1]}];")
            lines.append(f"ry({-np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"cz q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"ry({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")
            lines.append(f"ry({-np.pi / 2}) q[{qubits[0]}];")

    for i in range(circuit.num_qubits):
        lines.append(f"measure q[{i}] -> c[{i}];")

    return "\n".join(lines)
