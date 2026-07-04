# Tutorial 1: Bell States and Basic Circuits

## Introduction

This tutorial covers the fundamentals of quantum computing with AbirQu:
- Creating quantum circuits
- Applying quantum gates
- Measuring results
- Creating Bell states

## Prerequisites

```python
from abirqu.circuit import Circuit, Gate
from abirqu.backend import get_best_backend
import numpy as np
```

## 1. Creating Your First Circuit

```python
# Create a 2-qubit circuit
circuit = Circuit(num_qubits=2, name="my_first_circuit")

# Apply a Hadamard gate to qubit 0
circuit.add_gate("H", [0])

# Apply a CNOT gate (control=0, target=1)
circuit.add_gate("CNOT", [0, 1])

print(f"Circuit: {circuit.name}")
print(f"Qubits: {circuit.num_qubits}")
print(f"Gates: {len(circuit.gates)}")
```

## 2. Running on a Simulator

```python
# Get the best available backend
backend = get_best_backend(n_qubits=2)

# Run the circuit
result = backend.run_circuit(circuit, shots=1000)

# The result contains measurement outcomes
print(f"Result type: {type(result)}")
```

## 3. Creating Bell States

A Bell state is a maximally entangled 2-qubit state. The four Bell states are:

| State | Circuit |
|-------|---------|
| \|Φ+⟩ = (\|00⟩ + \|11⟩)/√2 | H(0), CNOT(0,1) |
| \|Φ-⟩ = (\|00⟩ - \|11⟩)/√2 | H(0), CNOT(0,1), Z(0) |
| \|Ψ+⟩ = (\|01⟩ + \|10⟩)/√2 | H(0), CNOT(0,1), X(1) |
| \|Ψ-⟩ = (\|01⟩ - \|10⟩)/√2 | H(0), CNOT(0,1), X(1), Z(0) |

```python
def create_bell_state(state_type="phi_plus"):
    """Create one of the four Bell states."""
    c = Circuit(2, f"bell_{state_type}")

    # Start with |00>
    # Apply H to first qubit
    c.add_gate("H", [0])

    # Apply CNOT
    c.add_gate("CNOT", [0, 1])

    # Modify based on desired state
    if state_type == "phi_minus":
        c.add_gate("Z", [0])
    elif state_type == "psi_plus":
        c.add_gate("X", [1])
    elif state_type == "psi_minus":
        c.add_gate("X", [1])
        c.add_gate("Z", [0])

    return c

# Create and run Bell state |Φ+⟩
bell_circuit = create_bell_state("phi_plus")
backend = get_best_backend(n_qubits=2)
result = backend.run_circuit(bell_circuit, shots=1000)
print("Bell state |Φ+⟩ created and measured!")
```

## 4. Single-Qubit Gates

```python
# Common single-qubit gates
circuit = Circuit(1, "single_qubit_gates")

# Pauli gates
circuit.add_gate("X", [0])  # Bit flip (NOT gate)
circuit.add_gate("Y", [0])  # Bit + phase flip
circuit.add_gate("Z", [0])  # Phase flip

# Rotation gates
circuit.add_gate("RX", [0], params=[np.pi / 4])  # Rotation around X
circuit.add_gate("RY", [0], params=[np.pi / 4])  # Rotation around Y
circuit.add_gate("RZ", [0], params=[np.pi / 4])  # Rotation around Z

print(f"Circuit with {len(circuit.gates)} single-qubit gates")
```

## 5. Two-Qubit Gates

```python
# Common two-qubit gates
circuit = Circuit(2, "two_qubit_gates")

circuit.add_gate("CNOT", [0, 1])  # Controlled-NOT
circuit.add_gate("CZ", [0, 1])    # Controlled-Z
circuit.add_gate("SWAP", [0, 1])  # Swap

print(f"Circuit with {len(circuit.gates)} two-qubit gates")
```

## 6. Running with Noise

```python
from abirqu.noise import NoiseModel

# Create a noise model
noise_model = NoiseModel(num_qubits=2)
noise_model.add_depolarizing_error(0, 0.01)  # 1% error on qubit 0
noise_model.add_depolarizing_error(1, 0.01)  # 1% error on qubit 1

# Create and run a noisy circuit
circuit = Circuit(2, "noisy_bell")
circuit.add_gate("H", [0])
circuit.add_gate("CNOT", [0, 1])

backend = get_best_backend(n_qubits=2)
result = backend.run_circuit(circuit, shots=1000)
print("Noisy Bell state simulation completed!")
```

## Summary

In this tutorial, you learned:
1. How to create quantum circuits
2. How to apply single and multi-qubit gates
3. How to create Bell states
4. How to run circuits on simulators
5. How to add noise to simulations

## Next Steps

- Tutorial 2: Quantum Algorithms (Grover, Shor, QFT)
- Tutorial 3: Quantum Error Correction
- Tutorial 4: Circuit Optimization and Compilation
- Tutorial 5: Quantum Chemistry with VQE
