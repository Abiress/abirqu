# Tutorial 2: Quantum Algorithms

## Introduction

This tutorial covers fundamental quantum algorithms implemented in AbirQu:
- Grover's Search Algorithm
- Shor's Factorization Algorithm
- Quantum Fourier Transform (QFT)
- Bernstein-Vazirani Algorithm

## Prerequisites

```python
from abirqu.circuit import Circuit
from abirqu.backend import get_best_backend
from abirqu.algorithms import (
    grover_search, shor_factorization, qft_circuit,
    bernstein_vazirani, quantum_walk
)
import numpy as np
```

## 1. Grover's Search Algorithm

Grover's algorithm searches an unsorted database of N items in O(√N) time.

```python
# Search for state |11⟩ (target=3) in a 2-qubit system
circuit = grover_search(target_state=3, num_qubits=2)

print(f"Circuit name: {circuit.name}")
print(f"Number of qubits: {circuit.num_qubits}")
print(f"Number of gates: {len(circuit.gates)}")

# Run the algorithm
backend = get_best_backend(n_qubits=2)
result = backend.run_circuit(circuit, shots=1000)
print("Grover's search completed!")
```

### How Grover's Algorithm Works

1. **Initialize**: Apply Hadamard to all qubits (uniform superposition)
2. **Oracle**: Mark the target state with a phase flip
3. **Diffusion**: Amplify the marked state's amplitude
4. **Repeat**: Steps 2-3 approximately √N times
5. **Measure**: Collapses to the target state

```python
# Grover with 3 qubits (searching 8 items)
circuit_3q = grover_search(target_state=5, num_qubits=3)
print(f"3-qubit Grover circuit: {len(circuit_3q.gates)} gates")
```

## 2. Shor's Factorization Algorithm

Shor's algorithm factors integers in polynomial time using quantum period finding.

```python
# Factor 15 (classically: 15 = 3 × 5)
circuit, metadata = shor_factorization(num_to_factor=15, num_qubits=8)

print(f"Number to factor: {metadata['num_to_factor']}")
print(f"Factors found: {metadata['factorization']}")
print(f"Success: {metadata['success']}")
print(f"Algorithm: {metadata['algorithm']}")
```

### How Shor's Algorithm Works

1. **Classical Part**: Choose random a < N, check if gcd(a, N) > 1
2. **Quantum Part**: Find period r of f(x) = aˣ mod N
3. **Classical Part**: If r is even, compute gcd(aʳ/² ± 1, N)

```python
# Factor another number
circuit, meta = shor_factorization(num_to_factor=21, num_qubits=10)
print(f"Factors of 21: {meta['factorization']}")
```

## 3. Quantum Fourier Transform (QFT)

QFT is the quantum analog of the discrete Fourier transform.

```python
# Create QFT circuit for 3 qubits
circuit = qft_circuit(num_qubits=3)

print(f"QFT circuit: {circuit.num_qubits} qubits, {len(circuit.gates)} gates")

# Run it
backend = get_best_backend(n_qubits=3)
result = backend.run_circuit(circuit, shots=1000)
print("QFT completed!")
```

### QFT Applications

- **Phase estimation**: Finding eigenvalues
- **Shor's algorithm**: Period finding
- **Quantum simulation**: Hamiltonian simulation

## 4. Bernstein-Vazirani Algorithm

Finds a hidden string s in one query (classical requires n queries).

```python
# Secret string: 101
circuit = bernstein_vazirani(secret="101")

print(f"Bernstein-Vazirani circuit: {circuit.num_qubits} qubits")
print(f"Secret string: 101")

# Run it
backend = get_best_backend(n_qubits=circuit.num_qubits)
result = backend.run_circuit(circuit, shots=1000)
print("Bernstein-Vazirani completed!")
```

## 5. Quantum Walk

Quantum walks are the quantum analog of classical random walks.

```python
# Create a quantum walk circuit
circuit = quantum_walk(num_qubits=2, steps=6)

print(f"Quantum walk: {circuit.num_qubits} qubits, {len(circuit.gates)} gates")

# Run it
backend = get_best_backend(n_qubits=2)
result = backend.run_circuit(circuit, shots=1000)
print("Quantum walk completed!")
```

## 6. Comparing Algorithms

```python
# Compare circuit sizes
algorithms = {
    "Grover (2-qubit)": grover_search(target_state=3, num_qubits=2),
    "Grover (3-qubit)": grover_search(target_state=5, num_qubits=3),
    "QFT (2-qubit)": qft_circuit(num_qubits=2),
    "QFT (3-qubit)": qft_circuit(num_qubits=3),
    "Bernstein-Vazirani": bernstein_vazirani(secret="101"),
}

print("Algorithm Comparison:")
print("-" * 40)
for name, circuit in algorithms.items():
    print(f"{name}: {len(circuit.gates)} gates")
```

## Summary

In this tutorial, you learned:
1. **Grover's Search**: Quadratic speedup for unstructured search
2. **Shor's Algorithm**: Exponential speedup for integer factorization
3. **QFT**: Foundation for many quantum algorithms
4. **Bernstein-Vazirani**: Linear speedup for hidden string problems
5. **Quantum Walk**: Quantum analog of random walks

## References

- Grover, L.K. (1996). "A fast quantum mechanical algorithm for database search"
- Shor, P.W. (1994). "Algorithms for quantum computation: discrete logarithms and factoring"
- Bernstein, E. & Vazirani, U. (1997). "Quantum complexity theory"
