# AbirQu Quantum SDK — Beginner Guide

Welcome to AbirQu! This guide will take you from zero to building your first quantum circuits.

**What is AbirQu?** A pedagogical quantum computing SDK written in pure NumPy. It's a learning tool for understanding quantum computing concepts, not a production quantum platform.

---

## 1. What is Quantum Computing?

Classical computers use **bits** (0 or 1). Quantum computers use **qubits** which can be in a **superposition** of both states simultaneously, and can be **entangled** with other qubits.

**Important:** AbirQu *simulates* quantum computing on classical hardware. It does not run on real quantum computers.

### Key Concepts

| Concept | Classical | Quantum |
|---------|-----------|---------|
| Basic unit | Bit (0 or 1) | Qubit (0, 1, or both) |
| Operations | Logic gates (AND, OR) | Quantum gates (H, CNOT, X) |
| State | Deterministic | Probabilistic |
| Parallelism | Sequential | Exponential |

---

## 2. Installation

AbirQu is not published on PyPI. Install from source:

```bash
git clone https://github.com/Abiress/abirqu.git
cd abirqu
pip install -e .
```

### Verify Installation
```python
import abirqu
print(abirqu.__version__)  # 1.0.0
```

---

## 3. Your First Circuit

```python
from abirqu import Circuit, Measure

# Create a circuit with 1 qubit
circuit = Circuit(1, name="hello")

# Apply a Hadamard gate (puts qubit in superposition)
circuit.h(0)

# Measure the qubit
circuit.measure([0])

# Run it
from abirqu.primitives import QuantumRun
result = QuantumRun(circuit, shots=100)
print(result.counts)
# Output: {'0': 50, '1': 50} (approximately)
```

### What Happened?
1. `Circuit(1)` — Created a circuit with 1 qubit
2. `circuit.h(0)` — Applied Hadamard gate to qubit 0, putting it in superposition
3. `circuit.measure([0])` — Marked qubit 0 for measurement
4. `QuantumRun(circuit, shots=100)` — Ran the circuit 100 times
5. `result.counts` — Showed how many times each outcome occurred

---

## 4. Quantum Gates

Quantum gates manipulate qubits. Here are the most common:

| Gate | Name | Effect | Code |
|------|------|--------|------|
| X | NOT | Flips 0↔1 | `circuit.x(0)` |
| H | Hadamard | Creates superposition | `circuit.h(0)` |
| Z | Pauli-Z | Phase flip | `circuit.z(0)` |
| CNOT | Controlled-NOT | Flips target if control is 1 | `circuit.cnot(0, 1)` |
| Ry(θ) | Rotation-Y | Rotates around Y-axis | `circuit.ry(0, theta)` |
| Rz(θ) | Rotation-Z | Rotates around Z-axis | `circuit.rz(0, theta)` |

### Example: Superposition
```python
from abirqu import Circuit
from abirqu.primitives import QuantumRun

circuit = Circuit(1)
circuit.h(0)  # Put in superposition
circuit.measure([0])

result = QuantumRun(circuit, shots=1000)
print(result.counts)  # ~50% '0', ~50% '1'
```

### Example: Entanglement (Bell State)
```python
from abirqu import Circuit
from abirqu.primitives import QuantumRun

circuit = Circuit(2)
circuit.h(0)      # Superposition on qubit 0
circuit.cnot(0, 1)  # Entangle qubits 0 and 1
circuit.measure([0, 1])

result = QuantumRun(circuit, shots=1000)
print(result.counts)  # Only '00' and '11' (never '01' or '10')
```

---

## 5. Reading Results

`QuantumRun` returns a result with:

- `result.counts` — Dictionary of measurement outcomes and their counts
- `result.probabilities` — Dictionary of outcome probabilities
- `result.mean` — Average measurement value

```python
result = QuantumRun(circuit, shots=1000)
print(result.counts)         # {'00': 500, '11': 500}
print(result.probabilities)  # {'00': 0.5, '11': 0.5}
```

---

## 6. Building Bigger Circuits

### 3-Qubit GHZ State
```python
from abirqu import Circuit
from abirqu.primitives import QuantumRun

circuit = Circuit(3)
circuit.h(0)
circuit.cnot(0, 1)
circuit.cnot(1, 2)
circuit.measure([0, 1, 2])

result = QuantumRun(circuit, shots=1000)
print(result.counts)  # Only '000' and '111'
```

### Quantum Fourier Transform
```python
from abirqu import Circuit
from abirqu.primitives import QuantumRun
import math

n = 3
circuit = Circuit(n)

# Initialize |001>
circuit.x(2)

# QFT
for i in range(n):
    circuit.h(i)
    for j in range(i+1, n):
        circuit.cnot(j, i)

circuit.measure(list(range(n)))
result = QuantumRun(circuit, shots=1000)
print(result.counts)
```

---

## 7. Using Different Backends

AbirQu supports 12 hardware backends. Most are adapter stubs that call vendor SDKs.

### D-Wave (Verified Locally)
```python
from abirqu.dwave import DWave
from abirqu.optimization import QUBO

qubo = QUBO({(0,0): -1, (1,1): -1, (0,1): 2})
backend = DWave()
result = backend.sample_qubo(qubo, num_reads=100)
print(result.best_sample)
```

### IBM Quantum (SDK-wired, not tested against real hardware)
```python
from abirqu import Circuit
from abirqu.backends import IBMBackend

circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure([0, 1])

# Note: Requires IBM Quantum token and qiskit-ibm-runtime
# backend = IBMBackend(token="your_token", backend_name="ibmq_manila")
# result = backend.run(circuit, shots=1024)
```

**Important:** Most hardware backends are SDK-wired adapters. They have NOT been tested against real quantum hardware.

---

## 8. What AbirQu Is NOT

Be clear about limitations:

| AbirQu | Real Production Tools |
|--------|----------------------|
| NumPy simulator | IBM Qiskit, Google Cirq |
| Educational chemistry | PySCF, OpenFermion |
| Simplified PQC | liboqs, pqcrypto |
| Toy-scale QEC | Qiskit Qiskit Experiments |
| Learning tool | Production quantum platform |

---

## 9. Next Steps

Now that you know the basics, explore these topics:

### Learning Path

1. **Tutorials 1-10** — Quantum fundamentals (superposition, entanglement, QFT, QPE)
2. **Tutorials 11-20** — Algorithms (Grover's, Shor's, VQE, QAOA)
3. **Tutorials 21-30** — Machine learning (quantum neural networks, classifiers)
4. **Tutorials 31-40** — Chemistry and error correction
5. **Tutorials 41-50** — Advanced topics (compilers, networks, sensing)
6. **Tutorials 51-100** — Expert-level topics
7. **Tutorials 101-200** — Cutting-edge applications

### Full Tutorial Index

See [tutorials/INDEX.md](../tutorials/INDEX.md) for the complete list of 200 tutorials.

---

## 10. Getting Help

- **GitHub**: [github.com/Abiress/abirqu](https://github.com/Abiress/abirqu)
- **Issues**: [github.com/Abiress/abirqu/issues](https://github.com/Abiress/abirqu/issues)
- **Author**: Abir Maheshwari — abhirsxn@gmail.com

---

*Built as part of the Indian Quantum Mission. Made in India, for the World.*
