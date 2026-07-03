"""
SpinQ Transpiler
================
Decompose AbirQu circuits to SpinQ native trapped-ion gate set.
"""

from __future__ import annotations

import numpy as np

from ...circuit import Circuit


SPINQ_NATIVE_GATES = ["Rz", "Rx", "MS"]


def transpile_to_spinq_native(circuit: Circuit) -> str:
    """Transpile an AbirQu circuit to SpinQ native gates and return QASM.

    SpinQ trapped-ion native gate set:
    - Rz(θ) — Z-rotation
    - Rx(θ) — X-rotation
    - MS(i,j) — Molmer-Sorensen entangling gate
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
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")
            lines.append(f"rx({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")

        elif name == "X":
            lines.append(f"rx({np.pi}) q[{qubits[0]}];")

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
            lines.append(f"rx({angle}) q[{qubits[0]}];")

        elif name == "RY":
            angle = float(params[0])
            lines.append(f"ry({angle}) q[{qubits[0]}];")

        elif name == "RZ":
            angle = float(params[0])
            lines.append(f"rz({angle}) q[{qubits[0]}];")

        elif name in ("CNOT", "CX"):
            # CNOT via MS gate decomposition
            lines.append(f"ry({-np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"ms q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rx({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"ry({np.pi / 2}) q[{qubits[1]}];")

        elif name == "CZ":
            lines.append(f"ry({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"ms q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"ry({-np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"ry({-np.pi / 2}) q[{qubits[1]}];")

        elif name == "SWAP":
            # SWAP = 3 CNOTs
            for _ in range(3):
                lines.append(f"ry({-np.pi / 2}) q[{qubits[1]}];")
                lines.append(f"ms q[{qubits[0]}],q[{qubits[1]}];")
                lines.append(f"rx({np.pi / 2}) q[{qubits[0]}];")
                lines.append(f"ry({np.pi / 2}) q[{qubits[1]}];")

    for i in range(circuit.num_qubits):
        lines.append(f"measure q[{i}] -> c[{i}];")

    return "\n".join(lines)
