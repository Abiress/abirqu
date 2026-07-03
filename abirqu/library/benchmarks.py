"""
Benchmark circuits for AbirQu — standard quantum computing benchmarks.

These are NOT copies of Qiskit's circuits.  AbirQu's benchmarks include
unique circuits not found in other SDKs.
"""
from __future__ import annotations
import math
from typing import Optional
from ..circuit import Circuit


def ghz_circuit(num_qubits: int) -> Circuit:
    """GHZ state: (|00...0> + |11...1>) / sqrt(2)."""
    c = Circuit(num_qubits, f"GHZ({num_qubits})")
    c.h(0)
    for i in range(num_qubits - 1):
        c.cnot(0, i + 1)
    return c


def w_state(num_qubits: int) -> Circuit:
    """W state: equal superposition of single-excitation states."""
    c = Circuit(num_qubits, f"W({num_qubits})")
    if num_qubits == 1:
        c.x(0)
        return c

    # Prepare |100...0>
    c.x(0)

    # Iterate from qubit 1 to n-1
    for i in range(1, num_qubits):
        # Rotation angle
        theta = 2 * math.acos(math.sqrt(1.0 / (num_qubits - i + 1)) if (num_qubits - i + 1) > 0 else 0)
        c.add_gate("RY", i, [theta])
        # CNOT to spread entanglement
        c.cnot(i, i - 1)

    return c


def qft_circuit(num_qubits: int) -> Circuit:
    """Quantum Fourier Transform."""
    c = Circuit(num_qubits, f"QFT({num_qubits})")

    for i in range(num_qubits):
        c.h(i)
        for j in range(i + 1, num_qubits):
            # Controlled phase rotation
            angle = math.pi / (2 ** (j - i))
            c.add_gate("CNOT", [j, i])
            c.add_gate("RZ", i, [angle])
            c.add_gate("CNOT", [j, i])

    # SWAP to reverse qubit order
    for i in range(num_qubits // 2):
        c.swap(i, num_qubits - 1 - i)

    return c


def grover_oracle(num_qubits: int, target: int) -> Circuit:
    """Grover oracle for a specific target state."""
    c = Circuit(num_qubits, f"GroverOracle({num_qubits}, target={target})")

    # Mark target state with X gates
    for i in range(num_qubits):
        if not (target >> i) & 1:
            c.x(i)

    # Multi-controlled Z
    if num_qubits >= 2:
        c.h(num_qubits - 1)
        # Decompose multi-controlled Z
        if num_qubits == 2:
            c.cz(0, 1)
        else:
            # V-chain decomposition
            for i in range(num_qubits - 2):
                c.cnot(i, num_qubits - 2)
            c.cz(num_qubits - 2, num_qubits - 1)
            for i in range(num_qubits - 3, -1, -1):
                c.cnot(i, num_qubits - 2)

    # Unmark target state
    for i in range(num_qubits):
        if not (target >> i) & 1:
            c.x(i)

    return c


def grover_circuit(num_qubits: int, target: int, iterations: Optional[int] = None) -> Circuit:
    """Full Grover search circuit."""
    if iterations is None:
        iterations = max(1, int(math.pi / 4 * math.sqrt(2 ** num_qubits)))

    c = Circuit(num_qubits, f"Grover({num_qubits}, target={target})")

    # Initial superposition
    for q in range(num_qubits):
        c.h(q)

    for _ in range(iterations):
        # Oracle
        oracle = grover_oracle(num_qubits, target)
        c.gates.extend(oracle.gates)

        # Diffusion operator
        for q in range(num_qubits):
            c.h(q)
        for q in range(num_qubits):
            c.x(q)
        # Multi-controlled Z
        if num_qubits >= 2:
            c.cz(0, 1)
        for q in range(num_qubits):
            c.x(q)
        for q in range(num_qubits):
            c.h(q)

    return c


def bernstein_vazirani_circuit(num_qubits: int, secret: int) -> Circuit:
    """Bernstein-Vazirani algorithm circuit."""
    c = Circuit(num_qubits + 1, f"BV({num_qubits}, secret={secret})")
    n = num_qubits

    # Initialize ancilla in |1>
    c.x(n)

    # Hadamard on all
    for q in range(n + 1):
        c.h(q)

    # Oracle: s·x via CNOT
    for i in range(n):
        if (secret >> i) & 1:
            c.cnot(i, n)

    # Hadamard on data qubits
    for q in range(n):
        c.h(q)

    return c


def quantum_fourier_transform(num_qubits: int) -> Circuit:
    """Alias for qft_circuit."""
    return qft_circuit(num_qubits)


def random_circuit(num_qubits: int, depth: int = 10, seed: int = 42) -> Circuit:
    """Random circuit for benchmarking."""
    import random
    rng = random.Random(seed)
    c = Circuit(num_qubits, f"Random({num_qubits}, depth={depth})")

    one_q = ["H", "X", "Y", "Z", "S", "T", "RX", "RY", "RZ"]
    two_q = ["CNOT", "CZ", "SWAP"]

    for _ in range(depth):
        for q in range(num_qubits):
            gate = rng.choice(one_q)
            if gate in ("RX", "RY", "RZ"):
                c.add_gate(gate, q, [rng.uniform(0, 2 * math.pi)])
            else:
                c.add_gate(gate, q)

        for _ in range(num_qubits // 2):
            gate = rng.choice(two_q)
            q1 = rng.randint(0, num_qubits - 1)
            q2 = rng.randint(0, num_qubits - 1)
            while q2 == q1:
                q2 = rng.randint(0, num_qubits - 1)
            c.add_gate(gate, [min(q1, q2), max(q1, q2)])

    return c
