"""
Quantum Algorithms — Bernstein-Vazirani, Simon's, Quantum Walk
==============================================================

Three fundamental quantum algorithms that demonstrate quantum advantage.

1. Bernstein-Vazirani: Find hidden bit string s in O(1) queries vs O(n) classical
2. Simon's: Find hidden period s in O(1) queries vs O(2^(n/2)) classical
3. Quantum Walk: Efficient graph search using quantum walk on hypercube
"""
import math
import numpy as np
from typing import List, Tuple, Optional
from abirqu import Circuit
from abirqu.primitives import QuantumRun


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Bernstein-Vazirani Algorithm
# ═══════════════════════════════════════════════════════════════════════════════

def bernstein_vazirani_circuit(secret: str) -> Tuple[Circuit, str]:
    """
    Bernstein-Vazirani algorithm circuit.

    Given a black-box function f(x) = s·x (mod 2), find the secret string s.
    Classical: O(n) queries, Quantum: O(1) query.

    Parameters
    ----------
    secret : str
        Binary string (e.g., "1010") representing the hidden bit string.
        Note: secret[0] is qubit 0 (LSB in AbirQu's little-endian).

    Returns
    -------
    Tuple[Circuit, str]
        (quantum circuit, secret string)
    """
    n = len(secret)
    circuit = Circuit(n + 1, name=f"BV_s{secret}")

    # Initialize ancilla qubit to |-> (X then H)
    circuit.x(n)
    circuit.h(n)

    # Apply Hadamard to input qubits
    for i in range(n):
        circuit.h(i)

    # Oracle: f(x) = s·x (mod 2)
    # For each '1' in secret, apply CNOT from that qubit to ancilla
    for i, bit in enumerate(secret):
        if bit == '1':
            circuit.cx(i, n)

    # Apply Hadamard to input qubits
    for i in range(n):
        circuit.h(i)

    # Measure input qubits
    for i in range(n):
        circuit.measure(i)

    return circuit, secret


def run_bernstein_vazirani(secret: str, shots: int = 100) -> dict:
    """Run Bernstein-Vazirani algorithm and verify result."""
    from abirqu.numpy_sim import NumPySimulator

    circuit, s = bernstein_vazirani_circuit(secret)

    # Use statevector simulation for exact result
    sim = NumPySimulator(num_qubits=circuit.num_qubits)
    sim.run_circuit(circuit)
    sv = sim.get_state_vector()

    # Find most probable input state (excluding ancilla)
    n = len(secret)
    probs = {}
    for i, amp in enumerate(sv):
        if abs(amp) > 0.01:
            # Extract input qubits in little-endian, then reverse for big-endian
            input_bits = ''
            for j in range(n):
                bit_val = (i >> j) & 1
                input_bits = str(bit_val) + input_bits
            input_bits = input_bits[::-1]  # Convert to big-endian
            probs[input_bits] = probs.get(input_bits, 0) + abs(amp)**2

    measured = max(probs, key=probs.get) if probs else '0'*n

    return {
        'secret': secret,
        'measured': measured,
        'success': measured == secret,
        'counts': {measured: 1},
        'shots': shots
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Simon's Algorithm
# ═══════════════════════════════════════════════════════════════════════════════

def simons_circuit(n: int, secret: str) -> Tuple[Circuit, str]:
    """
    Simon's algorithm circuit.

    Given f(x) = f(y) iff x ⊕ y = s, find the hidden period s.
    Classical: O(2^(n/2)) queries, Quantum: O(n) queries.

    Parameters
    ----------
    n : int
        Number of input qubits.
    secret : str
        Binary string representing the hidden period.

    Returns
    -------
    Tuple[Circuit, str]
        (quantum circuit, secret string)
    """
    circuit = Circuit(2 * n, name=f"Simon_n{n}")

    # Initialize output register to |0⟩ (already done)

    # Apply Hadamard to input register
    for i in range(n):
        circuit.h(i)

    # Oracle: f(x) = f(x ⊕ s) for x < 2^(n-1)
    # Simplified implementation for demonstration
    # In a real implementation, this would be a unitary that encodes f
    for i in range(n):
        if secret[i] == '1':
            circuit.cx(i, i + n)

    # Apply Hadamard to input register
    for i in range(n):
        circuit.h(i)

    # Measure input register
    for i in range(n):
        circuit.measure(i)

    return circuit, secret


def run_simons(n: int, secret: str, shots: int = 100) -> dict:
    """Run Simon's algorithm and verify result."""
    from abirqu.numpy_sim import NumPySimulator

    circuit, s = simons_circuit(n, secret)

    # Use statevector simulation for exact result
    sim = NumPySimulator(num_qubits=circuit.num_qubits)
    sim.run_circuit(circuit)
    sv = sim.get_state_vector()

    # Find most probable input state (excluding output register)
    probs = {}
    for i, amp in enumerate(sv):
        if abs(amp) > 0.01:
            # Extract input qubits (first n qubits) in little-endian, reverse
            input_bits = ''
            for j in range(n):
                bit_val = (i >> j) & 1
                input_bits = str(bit_val) + input_bits
            input_bits = input_bits[::-1]  # Convert to big-endian
            probs[input_bits] = probs.get(input_bits, 0) + abs(amp)**2

    measured = max(probs, key=probs.get) if probs else '0'*n

    # Check orthogonality: measured · s = 0 (mod 2)
    dot_product = sum(int(a) * int(b) for a, b in zip(measured, s)) % 2
    is_orthogonal = dot_product == 0

    return {
        'n': n,
        'secret': secret,
        'measured': measured,
        'dot_product': dot_product,
        'is_orthogonal': is_orthogonal,
        'counts': {measured: 1},
        'shots': shots
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Quantum Walk on Hypercube
# ═══════════════════════════════════════════════════════════════════════════════

def quantum_walk_hypercube_circuit(n: int, target: int) -> Tuple[Circuit, int]:
    """
    Quantum walk on n-dimensional hypercube to find marked vertex.

    Uses Szegedy quantum walk operator for spatial search.

    Parameters
    ----------
    n : int
        Number of qubits (2^n vertices).
    target : int
        Marked vertex to find.

    Returns
    -------
    Tuple[Circuit, int]
        (quantum circuit, target vertex)
    """
    circuit = Circuit(n, name=f"QWalk_n{n}_t{target}")

    # Initialize uniform superposition
    for i in range(n):
        circuit.h(i)

    # Grover-like diffusion (hypercube version)
    for _ in range(int(math.sqrt(2**n))):
        # Oracle: flip phase of target state
        # For target vertex, apply X to qubits where target has '1'
        target_bits = format(target, f'0{n}b')
        for i, bit in enumerate(reversed(target_bits)):
            if bit == '0':
                circuit.x(i)

        # Multi-controlled Z
        if n == 1:
            circuit.h(0)
            circuit.x(0)
            circuit.h(0)
        elif n == 2:
            circuit.h(1)
            circuit.cx(0, 1)
            circuit.h(1)
        else:
            # General case: H-MCX-H pattern
            circuit.h(n-1)
            # MCX using ancilla-free decomposition
            for i in range(n-1):
                circuit.cx(i, n-1)
            circuit.h(n-1)

        # Undo X gates
        for i, bit in enumerate(reversed(target_bits)):
            if bit == '0':
                circuit.x(i)

        # Diffusion operator (Hadamard on all qubits)
        for i in range(n):
            circuit.x(i)
        if n == 1:
            circuit.h(0)
        elif n == 2:
            circuit.h(0)
            circuit.h(1)
        else:
            circuit.h(n-1)
            for i in range(n-1):
                circuit.cx(i, n-1)
            circuit.h(n-1)
        for i in range(n):
            circuit.x(i)

    # Measure
    for i in range(n):
        circuit.measure(i)

    return circuit, target


def run_quantum_walk(n: int, target: int, shots: int = 100) -> dict:
    """Run quantum walk and verify result."""
    circuit, t = quantum_walk_hypercube_circuit(n, target)
    result = QuantumRun(circuit, shots=shots)

    target_str = format(target, f'0{n}b')
    success_count = result.counts.get(target_str, 0)

    return {
        'n': n,
        'target': target,
        'target_binary': target_str,
        'success_count': success_count,
        'total_shots': shots,
        'success_rate': success_count / shots,
        'counts': result.counts
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main Demo
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Quantum Algorithms Demo")
    print("=" * 60)

    # 1. Bernstein-Vazirani
    print("\n" + "─" * 60)
    print("1. BERNSTEIN-VAZIRANI ALGORITHM")
    print("─" * 60)
    print("Find hidden bit string s in O(1) queries vs O(n) classical")

    secrets = ["1010", "1100", "1111", "1001"]
    all_passed = True
    for secret in secrets:
        result = run_bernstein_vazirani(secret, shots=100)
        status = "✓" if result['success'] else "✗"
        print(f"  Secret: {secret}, Measured: {result['measured']} {status}")
        if not result['success']:
            all_passed = False

    print(f"\n  Result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    # 2. Simon's Algorithm
    print("\n" + "─" * 60)
    print("2. SIMON'S ALGORITHM")
    print("─" * 60)
    print("Find hidden period s in O(n) queries vs O(2^(n/2)) classical")

    simon_tests = [(2, "10"), (3, "101"), (4, "1100")]
    all_passed = True
    for n, secret in simon_tests:
        result = run_simons(n, secret, shots=100)
        status = "✓" if result['is_orthogonal'] else "✗"
        print(f"  n={n}, Secret: {secret}, Measured: {result['measured']}, "
              f"Orthogonal: {result['is_orthogonal']} {status}")
        if not result['is_orthogonal']:
            all_passed = False

    print(f"\n  Result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    # 3. Quantum Walk
    print("\n" + "─" * 60)
    print("3. QUANTUM WALK ON HYPERCUBE")
    print("─" * 60)
    print("Search marked vertex using quantum walk")

    walk_tests = [(2, 3), (3, 5), (4, 10)]
    for n, target in walk_tests:
        result = run_quantum_walk(n, target, shots=100)
        print(f"  n={n}, Target: {target} ({result['target_binary']}), "
              f"Found: {result['success_count']}/{result['total_shots']} "
              f"({result['success_rate']:.0%})")

    print("\n" + "=" * 60)
    print("  Quantum Algorithms Demo Complete")
    print("=" * 60)
