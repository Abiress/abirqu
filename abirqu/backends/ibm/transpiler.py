"""
IBM Quantum Transpiler
======================
Transpile AbirQu circuits to IBM native gate set (ECR, ID, RZ, X, SX).
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from ...circuit import Circuit


# IBM native gate set for Eagle/Heron processors
IBM_NATIVE_GATES = ["ECR", "ID", "RZ", "X", "SX"]


def transpile_to_ibm_native(circuit: Circuit) -> str:
    """Transpile an AbirQu circuit to IBM native gates and return QASM.

    IBM's Eagle/Heron processors use the native gate set:
    - ECR (Echoed Cross-Resonance) — two-qubit gate
    - ID (Identity)
    - RZ (Z-rotation)
    - X (Pauli-X)
    - SX (Square root of X)

    This transpiler decomposes standard gates to this native set.
    """
    lines = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"qubit[{circuit.num_qubits}] q;",
        f"bit[{circuit.num_qubits}] c;",
    ]

    for gate in getattr(circuit, "gates", []):
        name = gate.name.upper()
        qubits = list(gate.qubits)
        params = list(gate.params)

        if name == "H":
            # H = SX.RZ(π).SX.RZ(π/2)
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")

        elif name == "X":
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")

        elif name == "Y":
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")

        elif name == "Z":
            lines.append(f"rz({np.pi}) q[{qubits[0]}];")

        elif name == "S":
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")

        elif name == "S_DAG":
            lines.append(f"rz({-np.pi / 2}) q[{qubits[0]}];")

        elif name == "T":
            lines.append(f"rz({np.pi / 4}) q[{qubits[0]}];")

        elif name == "T_DAG":
            lines.append(f"rz({-np.pi / 4}) q[{qubits[0]}];")

        elif name == "RX":
            angle = float(params[0])
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({angle}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[0]}];")

        elif name == "RY":
            angle = float(params[0])
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({angle}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[0]}];")

        elif name == "RZ":
            angle = float(params[0])
            lines.append(f"rz({angle}) q[{qubits[0]}];")

        elif name in ("CNOT", "CX"):
            # CNOT via ECR: CNOT = (I⊗RZ(π/2)).ECR.(I⊗RZ(-π/2))
            lines.append(f"rz({np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[1]}];")

        elif name == "CZ":
            # CZ via ECR decomposition
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"sx q[{qubits[0]}];")
            lines.append(f"rz({np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[1]}];")

        elif name == "ECR":
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")

        elif name == "SWAP":
            # SWAP = 3 CNOTs
            lines.append(f"rz({np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"ecr q[{qubits[1]}],q[{qubits[0]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"rz({np.pi / 2}) q[{qubits[1]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[1]}];")

        elif name == "TOFFOLI":
            # Toffoli decomposition via ECR
            lines.append(f"rz({np.pi / 2}) q[{qubits[2]}];")
            lines.append(f"ecr q[{qubits[1]}],q[{qubits[2]}];")
            lines.append(f"rz({-np.pi / 4}) q[{qubits[2]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[2]}];")
            lines.append(f"rz({np.pi / 4}) q[{qubits[2]}];")
            lines.append(f"ecr q[{qubits[1]}],q[{qubits[2]}];")
            lines.append(f"rz({-np.pi / 4}) q[{qubits[2]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[2]}];")
            lines.append(f"rz({np.pi / 4}) q[{qubits[1]}];")
            lines.append(f"rz({np.pi / 4}) q[{qubits[2]}];")
            lines.append(f"ecr q[{qubits[1]}],q[{qubits[2]}];")
            lines.append(f"rz({-np.pi / 2}) q[{qubits[0]}];")
            lines.append(f"rz({np.pi / 4}) q[{qubits[1]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rz({-np.pi / 4}) q[{qubits[1]}];")
            lines.append(f"ecr q[{qubits[0]}],q[{qubits[1]}];")
            lines.append(f"rz({np.pi / 4}) q[{qubits[0]}];")
            lines.append(f"rz({np.pi / 2}) q[{qubits[0]}];")

    # Measurements
    for i in range(circuit.num_qubits):
        lines.append(f"c[{i}] = measure q[{i}];")

    return "\n".join(lines)
