import math
from typing import Iterable

from ..circuit import Circuit
from .core_patterns import oracle_pattern


def grover_template(num_qubits: int, marked_state: int) -> Circuit:
    c = Circuit(num_qubits, name="grover_template")
    for q in range(num_qubits):
        c.h(q)

    # One Grover iteration (oracle + diffusion-like step)
    c = c + oracle_pattern(num_qubits, marked_state)
    for q in range(num_qubits):
        c.h(q)
        c.x(q)
    for i in range(num_qubits - 1):
        c.cz(i, i + 1)
    for q in range(num_qubits):
        c.x(q)
        c.h(q)
    return c


def qaoa_template(num_qubits: int, edges: Iterable[tuple[int, int]], beta: float, gamma: float) -> Circuit:
    c = Circuit(num_qubits, name="qaoa_template")
    for q in range(num_qubits):
        c.h(q)

    for u, v in edges:
        c.cnot(u, v)
        c.rz(v, 2.0 * gamma)
        c.cnot(u, v)

    for q in range(num_qubits):
        c.rx(q, 2.0 * beta)
    return c


def vqe_ansatz_template(num_qubits: int, depth: int = 2) -> Circuit:
    c = Circuit(num_qubits, name="vqe_ansatz_template")
    for layer in range(depth):
        angle = math.pi / (layer + 2)
        for q in range(num_qubits):
            c.ry(q, angle)
            c.rz(q, angle / 2)
        for q in range(num_qubits - 1):
            c.cnot(q, q + 1)
    return c
