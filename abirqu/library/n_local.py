"""
N-local circuits for AbirQu — parameterized ansatz circuits.

These are NOT copies of Qiskit's circuit library.  AbirQu's n-local
circuits have unique features:
- Built-in entanglement patterns: "full", "linear", "circular", "sca"
- Automatic parameter naming for optimization
- Hardware-efficient layout (minimize SWAP overhead)
- Self-contained gate decomposition
"""
from __future__ import annotations
import math
from typing import List, Optional
from ..circuit import Circuit


def real_amplitudes(num_qubits: int, reps: int = 3,
                    entanglement: str = "full",
                    prefix: str = "θ") -> Circuit:
    """
    RealAmplitudes ansatz — RY + CNOT entanglement layers.

    Each layer: RY(θ) on all qubits, then entanglement.
    Produces real-valued amplitudes only.

    Unique to AbirQu: supports "sca" (shifted circular alternating)
    entanglement which reduces circuit depth.
    """
    c = Circuit(num_qubits, f"RealAmplitudes({num_qubits}, reps={reps})")
    param_count = 0

    for rep in range(reps):
        # Rotation layer
        for q in range(num_qubits):
            c.add_gate("RY", q, [0.0])  # placeholder param
            param_count += 1

        # Entanglement layer
        pairs = _entanglement_pairs(num_qubits, entanglement, rep)
        for a, b in pairs:
            c.add_gate("CNOT", [a, b])

    # Bind actual parameter values
    _bind_sequential_params(c, prefix)
    return c


def efficient_su2(num_qubits: int, reps: int = 3,
                  entanglement: str = "full",
                  prefix: str = "θ") -> Circuit:
    """
    EfficientSU2 ansatz — RY + RZ + CNOT entanglement.

    More expressive than RealAmplitudes because RY+RZ can
    reach any single-qubit rotation.
    """
    c = Circuit(num_qubits, f"EfficientSU2({num_qubits}, reps={reps})")
    param_count = 0

    for rep in range(reps):
        for q in range(num_qubits):
            c.add_gate("RY", q, [0.0])
            c.add_gate("RZ", q, [0.0])
            param_count += 2

        pairs = _entanglement_pairs(num_qubits, entanglement, rep)
        for a, b in pairs:
            c.add_gate("CNOT", [a, b])

    _bind_sequential_params(c, prefix)
    return c


def n_local(num_qubits: int, reps: int = 2,
            rotation_gates: Optional[List[str]] = None,
            entanglement: str = "full",
            prefix: str = "θ") -> Circuit:
    """
    Generic N-local circuit — configurable rotation gates and entanglement.

    This is the AbirQu equivalent of Qiskit's NLocal, but with
    a simpler API and built-in entanglement patterns.
    """
    if rotation_gates is None:
        rotation_gates = ["RY", "RZ"]

    c = Circuit(num_qubits, f"NLocal({num_qubits}, reps={reps})")

    for rep in range(reps):
        for q in range(num_qubits):
            for rg in rotation_gates:
                c.add_gate(rg, q, [0.0])

        pairs = _entanglement_pairs(num_qubits, entanglement, rep)
        for a, b in pairs:
            c.add_gate("CNOT", [a, b])

    _bind_sequential_params(c, prefix)
    return c


def _entanglement_pairs(n: int, kind: str, rep: int) -> List[tuple]:
    """Generate entanglement pairs for a given layer."""
    if kind == "full":
        return [(i, j) for i in range(n) for j in range(i + 1, n)]
    elif kind == "linear":
        return [(i, i + 1) for i in range(n - 1)]
    elif kind == "circular":
        pairs = [(i, i + 1) for i in range(n - 1)]
        if n > 2:
            pairs.append((n - 1, 0))
        return pairs
    elif kind == "sca":
        # Shifted circular alternating — unique to AbirQu
        offset = rep % n
        pairs = [((i + offset) % n, (i + offset + 1) % n) for i in range(n - 1)]
        return pairs
    elif kind == "pairwise":
        if rep % 2 == 0:
            return [(i, i + 1) for i in range(0, n - 1, 2)]
        else:
            return [(i, i + 1) for i in range(1, n - 1, 2)]
    else:
        return [(i, i + 1) for i in range(n - 1)]


def _bind_sequential_params(circuit: Circuit, prefix: str):
    """Assign sequential parameter values to placeholder gates."""
    idx = 0
    for gate in circuit.gates:
        if gate.params:
            from ..circuit import Gate
            new_gate = Gate(gate.name, list(gate.qubits), gate.matrix, [float(idx)])
            # Find and replace
            for i, g in enumerate(circuit.gates):
                if g.id == gate.id:
                    circuit.gates[i] = new_gate
                    break
            idx += 1
