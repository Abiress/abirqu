"""
AbirQu Inbound Circuit Converters
===================================
Convert circuits from external SDKs (Qiskit, Cirq, PennyLane) and QASM
strings into native AbirQu Circuit objects.

Supports: H, X, Y, Z, S, T, Rx, Ry, Rz, CNOT, CZ, SWAP, Toffoli, measure.

Pure numpy — no external SDKs required at import time.  Each converter
raises ``RuntimeError`` with a clear install hint when its dependency is
missing.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .circuit import Circuit, Measurement


# ── Gate name normalisation helpers ─────────────────────────────────────────

# Maps external gate names → AbirQu canonical names
_QISKIT_GATE_MAP: Dict[str, str] = {
    "h": "H", "x": "X", "y": "Y", "z": "Z",
    "s": "S", "sdg": "S_dag", "t": "T", "tdg": "T_dag",
    "rx": "RX", "ry": "RY", "rz": "RZ",
    "cx": "CNOT", "cnot": "CNOT", "cz": "CZ",
    "swap": "SWAP", "ccx": "TOFFOLI", "ccnot": "TOFFOLI",
    "toffoli": "TOFFOLI",
}

_CIRQ_GATE_MAP: Dict[str, str] = {
    "h": "H", "x": "X", "y": "Y", "z": "Z",
    "s": "S", "t": "T",
    "rx": "RX", "ry": "RY", "rz": "RZ",
    "cx": "CNOT", "cnot": "CNOT", "cz": "CZ",
    "swap": "SWAP", "ccx": "TOFFOLI", "ccnot": "TOFFOLI",
    "toffoli": "TOFFOLI",
}


def _normalise_qiskit_name(name: str) -> str:
    """Normalise a Qiskit gate name to AbirQu canonical form."""
    return _QISKIT_GATE_MAP.get(name.lower(), name.upper())


def _normalise_cirq_name(name: str) -> str:
    """Normalise a Cirq gate name to AbirQu canonical form."""
    return _CIRQ_GATE_MAP.get(name.lower(), name.upper())


# ── Qiskit → AbirQu ────────────────────────────────────────────────────────

def from_qiskit(qc: Any) -> Circuit:
    """Convert a Qiskit ``QuantumCircuit`` to an AbirQu :class:`Circuit`.

    Parameters
    ----------
    qc : qiskit.QuantumCircuit
        The Qiskit circuit to convert.

    Returns
    -------
    Circuit
        Equivalent AbirQu circuit.

    Raises
    ------
    RuntimeError
        If Qiskit is not installed.
    TypeError
        If *qc* is not a Qiskit ``QuantumCircuit``.
    """
    try:
        from qiskit.circuit import QuantumCircuit as QkCircuit
    except ImportError as exc:
        raise RuntimeError(
            "Qiskit not installed. Install with: pip install qiskit"
        ) from exc

    if not isinstance(qc, QkCircuit):
        raise TypeError(f"Expected a Qiskit QuantumCircuit, got {type(qc).__name__}")

    num_qubits = qc.num_qubits
    num_clbits = qc.num_clbits
    circ = Circuit(num_qubits, name=qc.name or None)
    circ.classical_bits = num_clbits

    for instruction in qc.data:
        gate_name = instruction.operation.name
        qubit_indices = [qc.find_bit(q).index for q in instruction.qubits]
        cbit_indices = [qc.find_bit(c).index for c in instruction.clbits] if instruction.clbits else []

        norm = _normalise_qiskit_name(gate_name)

        if norm in ("H", "X", "Y", "Z", "S", "S_DAG", "T", "T_DAG"):
            circ.add_gate(norm, qubit_indices)
        elif norm in ("RX", "RY", "RZ"):
            param = float(instruction.operation.params[0])
            circ.add_gate(norm, qubit_indices, [param])
        elif norm == "CNOT":
            circ.add_gate("CNOT", qubit_indices)
        elif norm == "CZ":
            circ.add_gate("CZ", qubit_indices)
        elif norm == "SWAP":
            circ.add_gate("SWAP", qubit_indices)
        elif norm == "TOFFOLI":
            circ.add_gate("TOFFOLI", qubit_indices)
        else:
            # Attempt to map via parameter list
            if instruction.operation.params:
                circ.add_gate(norm, qubit_indices,
                              [float(p) for p in instruction.operation.params])
            else:
                circ.add_gate(norm, qubit_indices)

    # Measurements
    for instruction in qc.data:
        if instruction.operation.name == "measure":
            qubit_idx = qc.find_bit(instruction.qubits[0]).index
            cbit_idx = qc.find_bit(instruction.clbits[0]).index if instruction.clbits else qubit_idx
            circ.measurements.append(Measurement(qubit_idx, cbit_idx))

    return circ


# ── Cirq → AbirQu ──────────────────────────────────────────────────────────

def from_cirq(circuit: Any, qubits: Any) -> Circuit:
    """Convert a Cirq ``Circuit`` to an AbirQu :class:`Circuit`.

    Parameters
    ----------
    circuit : cirq.Circuit
        The Cirq circuit.
    qubits : list of cirq.LineQubit
        The qubit register used in the circuit.  Used to build an
        index mapping.

    Returns
    -------
    Circuit
        Equivalent AbirQu circuit.

    Raises
    ------
    RuntimeError
        If Cirq is not installed.
    """
    try:
        import cirq
    except ImportError as exc:
        raise RuntimeError(
            "Cirq not installed. Install with: pip install cirq"
        ) from exc

    qubit_map = {q: i for i, q in enumerate(qubits)}
    num_qubits = len(qubits)
    circ = Circuit(num_qubits)

    for moment in circuit:
        for op in moment:
            qubit_indices = [qubit_map[q] for q in op.qubits]
            gate = op.gate

            if gate is None:
                continue

            gate_str = str(gate)

            # Try string-based gate name extraction
            name_match = re.match(r"([A-Za-z]+)", gate_str)
            if name_match:
                raw_name = name_match.group(1)
            else:
                raw_name = gate_str

            norm = _normalise_cirq_name(raw_name)

            # Rotation gates have exponent attributes
            if hasattr(gate, "_exponent") and norm in ("RX", "RY", "RZ"):
                angle = float(gate._exponent) * np.pi
                circ.add_gate(norm, qubit_indices, [angle])
            elif norm in ("H", "X", "Y", "Z", "S", "T", "CNOT", "CZ", "SWAP", "TOFFOLI"):
                circ.add_gate(norm, qubit_indices)
            else:
                # Try to extract parameters from gate string representation
                param_match = re.search(r"rads?\(([\d.e+-]+)\)", gate_str)
                if param_match and norm in ("RX", "RY", "RZ"):
                    angle = float(param_match.group(1))
                    circ.add_gate(norm, qubit_indices, [angle])
                else:
                    # Fallback — use gate str as name
                    circ.add_gate(raw_name, qubit_indices)

    # Measurements
    for moment in circuit:
        for op in moment:
            if isinstance(op.gate, type(cirq.ops.MeasurementGate)):
                for q in op.qubits:
                    circ.measurements.append(Measurement(qubit_map[q], qubit_map[q]))

    return circ


# ── PennyLane → AbirQu ─────────────────────────────────────────────────────

def from_pennylane(tape: Any) -> Circuit:
    """Convert a PennyLane ``QuantumTape`` (or ``QScript``) to an AbirQu :class:`Circuit`.

    Parameters
    ----------
    tape : pennylane.tape.QuantumTape
        The PennyLane quantum tape.

    Returns
    -------
    Circuit
        Equivalent AbirQu circuit.

    Raises
    ------
    RuntimeError
        If PennyLane is not installed.
    """
    try:
        import pennylane as qml
    except ImportError as exc:
        raise RuntimeError(
            "PennyLane not installed. Install with: pip install pennylane"
        ) from exc

    num_qubits = tape.num_qubits
    circ = Circuit(num_qubits)

    # Gate mapping: PennyLane name → AbirQu name
    pl_gate_map = {
        "Hadamard": "H",
        "PauliX": "X",
        "PauliY": "Y",
        "PauliZ": "Z",
        "S": "S",
        "T": "T",
        "CNOT": "CNOT",
        "CZ": "CZ",
        "SWAP": "SWAP",
        "Toffoli": "TOFFOLI",
        "RX": "RX",
        "RY": "RY",
        "RZ": "RZ",
        "RX": "RX",
        "RY": "RY",
        "RZ": "RZ",
        "PhaseShift": "RZ",
    }

    for op in tape.operations:
        name = op.name
        qubit_indices = [op.wires.index(w) for w in op.wires]

        norm = pl_gate_map.get(name, name.upper())

        if norm in ("H", "X", "Y", "Z", "S", "T", "CNOT", "CZ", "SWAP", "TOFFOLI"):
            circ.add_gate(norm, qubit_indices)
        elif norm in ("RX", "RY", "RZ"):
            # PennyLane rotation gates store params as a list
            param = float(op.parameters[0])
            circ.add_gate(norm, qubit_indices, [param])
        else:
            # Attempt to map parameterised ops
            if op.parameters:
                params = [float(p) for p in op.parameters]
                circ.add_gate(norm, qubit_indices, params)
            else:
                circ.add_gate(norm, qubit_indices)

    # Measurements
    for mp in tape.measurements:
        if hasattr(mp, "wires") and mp.wires:
            for w in mp.wires:
                wire_idx = tape.wires.index(w)
                circ.measurements.append(Measurement(wire_idx, wire_idx))

    return circ


# ── QASM string → AbirQu (re-export from formats.openqasm2) ───────────────

def from_qasm(qasm_str: str) -> Circuit:
    """Parse an OpenQASM 2.0 string into an AbirQu :class:`Circuit`.

    Uses :func:`abirqu.formats.openqasm2.parse_qasm` under the hood.

    Parameters
    ----------
    qasm_str : str
        OpenQASM 2.0 program text.

    Returns
    -------
    Circuit
        Parsed AbirQu circuit.

    Raises
    ------
    ValueError
        If the QASM string is malformed.
    """
    from .formats import openqasm2

    qasm_circ = openqasm2.parse_qasm(qasm_str)

    num_qubits = getattr(qasm_circ, "num_qubits", 0)
    circ = Circuit(num_qubits, name=getattr(qasm_circ, "name", None))

    for gate in getattr(qasm_circ, "gates", []):
        if gate.name == "measure":
            # measurements are handled separately below
            continue

        name = gate.name.upper()
        qubits = list(gate.qubits)
        params = list(gate.params) if hasattr(gate, "params") else []

        # Normalise common aliases
        alias_map = {
            "CX": "CNOT",
            "CCX": "TOFFOLI",
            "CCNOT": "TOFFOLI",
            "SDG": "S_DAG",
            "TDG": "T_DAG",
        }
        name = alias_map.get(name, name)

        if name in ("H", "X", "Y", "Z", "S", "S_DAG", "T", "T_DAG",
                     "CNOT", "CZ", "SWAP", "TOFFOLI"):
            circ.add_gate(name, qubits)
        elif name in ("RX", "RY", "RZ"):
            circ.add_gate(name, qubits, [float(p) for p in params])
        else:
            if params:
                circ.add_gate(name, qubits, [float(p) for p in params])
            else:
                circ.add_gate(name, qubits)

    # Measurements — OpenQASM2 GateDef stores measure ops with
    # classical_bits attribute
    for gate in getattr(qasm_circ, "gates", []):
        if gate.name == "measure":
            qubit = gate.qubits[0] if gate.qubits else 0
            cbit = gate.classical_bits[0] if hasattr(gate, "classical_bits") and gate.classical_bits else qubit
            circ.measurements.append(Measurement(qubit, cbit))

    return circ


# ── Public API ──────────────────────────────────────────────────────────────

__all__ = [
    "from_qiskit",
    "from_cirq",
    "from_pennylane",
    "from_qasm",
]
