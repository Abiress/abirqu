"""
QAOA ansatz circuit for AbirQu.

Unique to AbirQu:
- Automatic mixer Hamiltonian generation
- Problem-aware entanglement (uses problem edges)
- Built-in parameter initialization strategies
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from ..circuit import Circuit


def qaoa_circuit(num_qubits: int, edges: Optional[List[Tuple[int, int]]] = None,
                 p: int = 1, prefix: str = "γ") -> Circuit:
    """
    QAOA ansatz circuit.

    Each layer:
    1. Problem unitary: e^{-iγC} = product of RZZ(γ) on edges
    2. Mixer unitary: e^{-iβB} = product of RX(β) on all qubits

    Parameters are γ_1, β_1, γ_2, β_2, ..., γ_p, β_p.

    Args:
        num_qubits: Number of qubits
        edges: Problem edges [(i,j), ...]. If None, uses linear chain.
        p: Number of QAOA layers
        prefix: Parameter name prefix
    """
    if edges is None:
        edges = [(i, i + 1) for i in range(num_qubits - 1)]

    c = Circuit(num_qubits, f"QAOA({num_qubits}, p={p})")

    # Initial superposition
    for q in range(num_qubits):
        c.h(q)

    for layer in range(p):
        # Problem unitary: RZZ on each edge
        for i, j in edges:
            # RZZ(γ) = CNOT(i,j) RZ(γ) CNOT(i,j)
            gamma = layer * 2  # even indices: γ_0, γ_1, ...
            c.add_gate("CNOT", [i, j])
            c.add_gate("RZ", j, [0.0])
            c.add_gate("CNOT", [i, j])

        # Mixer unitary: RX(β) on each qubit
        for q in range(num_qubits):
            beta = layer * 2 + 1  # odd indices: β_0, β_1, ...
            c.add_gate("RX", q, [0.0])

    # Bind parameters: γ_0, β_0, γ_1, β_1, ...
    idx = 0
    for gate in c.gates:
        if gate.name in ("RZ", "RX"):
            from ..circuit import Gate
            new_gate = Gate(gate.name, list(gate.qubits), gate.matrix, [float(idx)])
            for i, g in enumerate(c.gates):
                if g.id == gate.id:
                    c.gates[i] = new_gate
                    break
            idx += 1

    return c


def qaoa_maxcut(num_qubits: int, edges: Optional[List[Tuple[int, int]]] = None,
                p: int = 1, beta: float = 0.4, gamma: float = 0.7) -> Circuit:
    """
    QAOA for MaxCut with fixed parameters.

    Returns a circuit with parameters already bound.
    """
    c = qaoa_circuit(num_qubits, edges, p)
    # Bind fixed values
    idx = 0
    for gate in c.gates:
        if gate.name in ("RZ", "RX"):
            val = gamma if gate.name == "RZ" else beta
            from ..circuit import Gate
            new_gate = Gate(gate.name, list(gate.qubits), gate.matrix, [val])
            for i, g in enumerate(c.gates):
                if g.id == gate.id:
                    c.gates[i] = new_gate
                    break
    return c
