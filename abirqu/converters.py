"""
AbirQu Circuit Converters
==========================
Unified conversion from AbirQu Circuit objects to provider-native formats.

Each converter returns a native circuit object ready for the target backend.
Import errors in provider-specific converters are handled gracefully — if
the provider SDK is not installed, the converter raises a clear error.
"""

from __future__ import annotations

from typing import Any, List

from .circuit import Circuit, Gate


# ──────────────────────────────────────────────────────────────────────────────
# Generic converter dispatcher
# ──────────────────────────────────────────────────────────────────────────────

def convert_circuit(circuit: Circuit, target: str) -> Any:
    """Convert an AbirQu Circuit to a provider-native circuit.

    Parameters
    ----------
    circuit : Circuit
        The AbirQu circuit to convert.
    target : str
        One of: ``"qiskit"``, ``"braket"``, ``"cirq"``, ``"ionq_json"``,
        ``"pytket"``, ``"quil"``, ``"openqasm"``.

    Returns
    -------
    Provider-native circuit object.

    Raises
    ------
    ValueError
        If *target* is not recognised.
    RuntimeError
        If the required provider SDK is not installed.
    """
    converters = {
        "qiskit": to_qiskit,
        "braket": to_braket,
        "cirq": to_cirq,
        "ionq_json": to_ionq_json,
        "ionq": to_ionq_json,
        "pytket": to_pytket,
        "tket": to_pytket,
        "quil": to_quil,
        "openqasm": to_openqasm,
        "qasm": to_openqasm,
    }
    fn = converters.get(target.lower())
    if fn is None:
        raise ValueError(
            f"Unknown conversion target '{target}'. "
            f"Available: {sorted(converters.keys())}"
        )
    return fn(circuit)


# ──────────────────────────────────────────────────────────────────────────────
# Gate-by-gate helpers
# ──────────────────────────────────────────────────────────────────────────────

def _iter_gates(circuit: Circuit):
    """Yield (gate_name, qubits, params) for every gate in the circuit."""
    for gate in getattr(circuit, "gates", []):
        name = gate.name.upper()
        qubits = list(gate.qubits)
        params = list(gate.params)
        yield name, qubits, params


# ──────────────────────────────────────────────────────────────────────────────
# Qiskit converter
# ──────────────────────────────────────────────────────────────────────────────

def to_qiskit(circuit: Circuit) -> Any:
    """Convert AbirQu Circuit to a Qiskit ``QuantumCircuit``."""
    try:
        from qiskit import QuantumCircuit as QkCircuit
    except ImportError as exc:
        raise RuntimeError(
            "Qiskit not installed. Install with: pip install qiskit"
        ) from exc

    qc = QkCircuit(circuit.num_qubits, circuit.num_qubits)
    for name, q, p in _iter_gates(circuit):
        if name == "H":
            qc.h(q[0])
        elif name in ("CNOT", "CX"):
            qc.cx(q[0], q[1])
        elif name == "X":
            qc.x(q[0])
        elif name == "Y":
            qc.y(q[0])
        elif name == "Z":
            qc.z(q[0])
        elif name == "S":
            qc.s(q[0])
        elif name == "S_DAG":
            qc.sdg(q[0])
        elif name == "T":
            qc.t(q[0])
        elif name == "T_DAG":
            qc.tdg(q[0])
        elif name == "RX":
            qc.rx(float(p[0]), q[0])
        elif name == "RY":
            qc.ry(float(p[0]), q[0])
        elif name == "RZ":
            qc.rz(float(p[0]), q[0])
        elif name == "CZ":
            qc.cz(q[0], q[1])
        elif name == "SWAP":
            qc.swap(q[0], q[1])
        elif name == "TOFFOLI":
            qc.ccx(q[0], q[1], q[2])
        elif name == "ECR":
            qc.ecr(q[0], q[1])
        elif name == "ISWAP":
            qc.iswap(q[0], q[1])
        else:
            qc.append(getattr(qc, name.lower(), None) or qc.u(float(p[0]) if p else 0, 0, 0, q[0]), q)
    qc.measure_all()
    return qc


# ──────────────────────────────────────────────────────────────────────────────
# Braket converter
# ──────────────────────────────────────────────────────────────────────────────

def to_braket(circuit: Circuit) -> Any:
    """Convert AbirQu Circuit to an Amazon Braket ``Circuit``."""
    try:
        from braket.circuits import Circuit as BCircuit
    except ImportError as exc:
        raise RuntimeError(
            "Amazon Braket SDK not installed. Install with: pip install amazon-braket-sdk"
        ) from exc

    bc = BCircuit()
    for name, q, p in _iter_gates(circuit):
        if name == "H":
            bc.h(q[0])
        elif name in ("CNOT", "CX"):
            bc.cnot(q[0], q[1])
        elif name == "X":
            bc.x(q[0])
        elif name == "Y":
            bc.y(q[0])
        elif name == "Z":
            bc.z(q[0])
        elif name == "S":
            bc.s(q[0])
        elif name == "T":
            bc.t(q[0])
        elif name == "RX":
            bc.rx(q[0], float(p[0]))
        elif name == "RY":
            bc.ry(q[0], float(p[0]))
        elif name == "RZ":
            bc.rz(q[0], float(p[0]))
        elif name == "CZ":
            bc.cz(q[0], q[1])
        elif name == "SWAP":
            bc.swap(q[0], q[1])
        elif name == "TOFFOLI":
            bc.ccnot(q[0], q[1], q[2])
        else:
            raise ValueError(f"Gate '{name}' not supported in Braket conversion")
    return bc


# ──────────────────────────────────────────────────────────────────────────────
# Cirq converter
# ──────────────────────────────────────────────────────────────────────────────

def to_cirq(circuit: Circuit, add_measurement: bool = True):
    """Convert AbirQu Circuit to a Cirq ``Circuit``.

    Returns ``(circuit, qubits)`` where *qubits* is a list of
    ``cirq.LineQubit`` objects.
    """
    try:
        import cirq
    except ImportError as exc:
        raise RuntimeError(
            "Cirq not installed. Install with: pip install cirq"
        ) from exc

    qubits = cirq.LineQubit.range(circuit.num_qubits)
    ops: list = []
    for name, q, p in _iter_gates(circuit):
        if name == "H":
            ops.append(cirq.H(qubits[q[0]]))
        elif name in ("CNOT", "CX"):
            ops.append(cirq.CNOT(qubits[q[0]], qubits[q[1]]))
        elif name == "X":
            ops.append(cirq.X(qubits[q[0]]))
        elif name == "Y":
            ops.append(cirq.Y(qubits[q[0]]))
        elif name == "Z":
            ops.append(cirq.Z(qubits[q[0]]))
        elif name == "S":
            ops.append(cirq.S(qubits[q[0]]))
        elif name == "S_DAG":
            ops.append(cirq.S(qubits[q[0]]) ** -1)
        elif name == "T":
            ops.append(cirq.T(qubits[q[0]]))
        elif name == "T_DAG":
            ops.append(cirq.T(qubits[q[0]]) ** -1)
        elif name == "RX":
            ops.append(cirq.rx(float(p[0]))(qubits[q[0]]))
        elif name == "RY":
            ops.append(cirq.ry(float(p[0]))(qubits[q[0]]))
        elif name == "RZ":
            ops.append(cirq.rz(float(p[0]))(qubits[q[0]]))
        elif name == "CZ":
            ops.append(cirq.CZ(qubits[q[0]], qubits[q[1]]))
        elif name == "SWAP":
            ops.append(cirq.SWAP(qubits[q[0]], qubits[q[1]]))
        elif name == "TOFFOLI":
            ops.append(cirq.TOFFOLI(qubits[q[0]], qubits[q[1]], qubits[q[2]]))
        else:
            raise ValueError(f"Gate '{name}' not supported in Cirq conversion")

    if add_measurement:
        ops.append(cirq.measure(*qubits, key="result"))

    return cirq.Circuit(ops), qubits


# ──────────────────────────────────────────────────────────────────────────────
# IonQ JSON converter
# ──────────────────────────────────────────────────────────────────────────────

def to_ionq_json(circuit: Circuit) -> dict:
    """Convert AbirQu Circuit to IonQ native JSON gate format.

    Returns a dict with ``qubits`` and ``circuit`` (list of gate dicts).
    """
    ops: List[dict] = []
    for name, q, p in _iter_gates(circuit):
        if name == "H":
            ops.append({"gate": "h", "target": q[0]})
        elif name in ("CNOT", "CX"):
            ops.append({"gate": "cnot", "control": q[0], "target": q[1]})
        elif name == "X":
            ops.append({"gate": "x", "target": q[0]})
        elif name == "Y":
            ops.append({"gate": "y", "target": q[0]})
        elif name == "Z":
            ops.append({"gate": "z", "target": q[0]})
        elif name == "S":
            ops.append({"gate": "s", "target": q[0]})
        elif name == "T":
            ops.append({"gate": "t", "target": q[0]})
        elif name == "RX":
            ops.append({"gate": "rx", "target": q[0], "rotation": float(p[0])})
        elif name == "RY":
            ops.append({"gate": "ry", "target": q[0], "rotation": float(p[0])})
        elif name == "RZ":
            ops.append({"gate": "rz", "target": q[0], "rotation": float(p[0])})
        elif name == "CZ":
            ops.append({"gate": "cz", "control": q[0], "target": q[1]})
        elif name == "SWAP":
            ops.append({"gate": "swap", "targets": [q[0], q[1]]})
        else:
            raise ValueError(f"Gate '{name}' not supported in IonQ JSON conversion")
    return {"qubits": circuit.num_qubits, "circuit": ops}


# ──────────────────────────────────────────────────────────────────────────────
# pytket converter
# ──────────────────────────────────────────────────────────────────────────────

def to_pytket(circuit: Circuit) -> Any:
    """Convert AbirQu Circuit to a pytket ``Circuit``."""
    try:
        from pytket import Circuit as TkCircuit, OpType
    except ImportError as exc:
        raise RuntimeError(
            "pytket not installed. Install with: pip install pytket"
        ) from exc

    tc = TkCircuit(circuit.num_qubits)
    for name, q, p in _iter_gates(circuit):
        if name == "H":
            tc.add_gate(OpType.H, [q[0]])
        elif name in ("CNOT", "CX"):
            tc.add_gate(OpType.CX, [q[0], q[1]])
        elif name == "X":
            tc.add_gate(OpType.X, [q[0]])
        elif name == "Y":
            tc.add_gate(OpType.Y, [q[0]])
        elif name == "Z":
            tc.add_gate(OpType.Z, [q[0]])
        elif name == "S":
            tc.add_gate(OpType.S, [q[0]])
        elif name == "S_DAG":
            tc.add_gate(OpType.Sdg, [q[0]])
        elif name == "T":
            tc.add_gate(OpType.T, [q[0]])
        elif name == "T_DAG":
            tc.add_gate(OpType.Tdg, [q[0]])
        elif name == "RX":
            tc.add_gate(OpType.Rx, [float(p[0])], [q[0]])
        elif name == "RY":
            tc.add_gate(OpType.Ry, [float(p[0])], [q[0]])
        elif name == "RZ":
            tc.add_gate(OpType.Rz, [float(p[0])], [q[0]])
        elif name == "CZ":
            tc.add_gate(OpType.CZ, [q[0], q[1]])
        elif name == "SWAP":
            tc.add_gate(OpType.SWAP, [q[0], q[1]])
        elif name == "TOFFOLI":
            tc.add_gate(OpType.CCX, [q[0], q[1], q[2]])
        else:
            raise ValueError(f"Gate '{name}' not supported in pytket conversion")
    return tc


# ──────────────────────────────────────────────────────────────────────────────
# Quil converter
# ──────────────────────────────────────────────────────────────────────────────

def to_quil(circuit: Circuit) -> str:
    """Convert AbirQu Circuit to a Quil program string."""
    lines: List[str] = []
    lines.append(f"DECLARE ro BIT[{circuit.num_qubits}]")
    for name, q, p in _iter_gates(circuit):
        if name == "H":
            lines.append(f"H {q[0]}")
        elif name in ("CNOT", "CX"):
            lines.append(f"CNOT {q[0]} {q[1]}")
        elif name == "X":
            lines.append(f"X {q[0]}")
        elif name == "Y":
            lines.append(f"Y {q[0]}")
        elif name == "Z":
            lines.append(f"Z {q[0]}")
        elif name == "S":
            lines.append(f"S {q[0]}")
        elif name == "T":
            lines.append(f"T {q[0]}")
        elif name == "RX":
            lines.append(f"RX({float(p[0])}) {q[0]}")
        elif name == "RY":
            lines.append(f"RY({float(p[0])}) {q[0]}")
        elif name == "RZ":
            lines.append(f"RZ({float(p[0])}) {q[0]}")
        elif name == "CZ":
            lines.append(f"CZ {q[0]} {q[1]}")
        elif name == "SWAP":
            lines.append(f"SWAP {q[0]} {q[1]}")
        elif name == "TOFFOLI":
            lines.append(f"CCNOT {q[0]} {q[1]} {q[2]}")
        else:
            raise ValueError(f"Gate '{name}' not supported in Quil conversion")
    for i in range(circuit.num_qubits):
        lines.append(f"MEASURE {i} ro[{i}]")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# OpenQASM 2.0 converter
# ──────────────────────────────────────────────────────────────────────────────

def to_openqasm(circuit: Circuit, version: str = "2.0") -> str:
    """Convert AbirQu Circuit to OpenQASM string."""
    lines: List[str] = []
    lines.append(f'OPENQASM {version};')
    lines.append('include "qelib1.inc";')
    lines.append(f'qreg q[{circuit.num_qubits}];')
    lines.append(f'creg c[{circuit.num_qubits}];')
    for name, q, p in _iter_gates(circuit):
        if name == "H":
            lines.append(f'h q[{q[0]}];')
        elif name in ("CNOT", "CX"):
            lines.append(f'cx q[{q[0]}],q[{q[1]}];')
        elif name == "X":
            lines.append(f'x q[{q[0]}];')
        elif name == "Y":
            lines.append(f'y q[{q[0]}];')
        elif name == "Z":
            lines.append(f'z q[{q[0]}];')
        elif name == "S":
            lines.append(f's q[{q[0]}];')
        elif name == "S_DAG":
            lines.append(f'sdg q[{q[0]}];')
        elif name == "T":
            lines.append(f't q[{q[0]}];')
        elif name == "T_DAG":
            lines.append(f'tdg q[{q[0]}];')
        elif name == "RX":
            lines.append(f'rx({float(p[0])}) q[{q[0]}];')
        elif name == "RY":
            lines.append(f'ry({float(p[0])}) q[{q[0]}];')
        elif name == "RZ":
            lines.append(f'rz({float(p[0])}) q[{q[0]}];')
        elif name == "CZ":
            lines.append(f'cz q[{q[0]}],q[{q[1]}];')
        elif name == "SWAP":
            lines.append(f'swap q[{q[0]}],q[{q[1]}];')
        elif name == "TOFFOLI":
            lines.append(f'ccx q[{q[0]}],q[{q[1]}],q[{q[2]}];')
        else:
            raise ValueError(f"Gate '{name}' not supported in OpenQASM conversion")
    for i in range(circuit.num_qubits):
        lines.append(f'measure q[{i}] -> c[{i}];')
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Public exports
# ──────────────────────────────────────────────────────────────────────────────

__all__ = [
    "convert_circuit",
    "to_qiskit",
    "to_braket",
    "to_cirq",
    "to_ionq_json",
    "to_pytket",
    "to_quil",
    "to_openqasm",
]
