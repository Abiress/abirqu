# Tutorial 4: Circuit Optimization and Compilation

## Introduction

This tutorial covers optimizing quantum circuits for hardware execution:
- Circuit simplification
- Gate decomposition
- Noise-adaptive compilation
- Target hardware optimization

## Prerequisites

```python
from abirqu.circuit import Circuit
from abirqu.optimize import CircuitSimplifier
from abirqu.optimize.circuit_compiler import CircuitCompiler, GateDecomposer, NATIVE_GATE_SETS
from abirqu.backend import get_best_backend
import numpy as np
```

## 1. Circuit Simplification

Remove redundant gates and simplify circuits.

```python
# Create a circuit with redundant gates
circuit = Circuit(2, "unoptimized")
circuit.add_gate("H", [0])
circuit.add_gate("X", [0])
circuit.add_gate("X", [0])  # X squared = Identity
circuit.add_gate("H", [0])  # H squared = Identity

print(f"Original: {len(circuit.gates)} gates")

# Simplify
simplifier = CircuitSimplifier()
simplified = simplifier.simplify(circuit)

print(f"Simplified: {len(simplified.gates)} gates")
```

### What Simplification Does

1. **Gate cancellation**: Remove adjacent inverse gates (X·X = I)
2. **Identity removal**: Remove gates that equal identity (H·H = I)
3. **Gate merging**: Combine rotation gates (RX(a)·RX(b) = RX(a+b))

```python
# More complex example
circuit = Circuit(1, "rotations")
circuit.add_gate("RX", [0], params=[np.pi / 4])
circuit.add_gate("RX", [0], params=[np.pi / 4])
circuit.add_gate("RY", [0], params=[np.pi / 2])
circuit.add_gate("RY", [0], params=[-np.pi / 2])  # Cancels previous

print(f"Original: {len(circuit.gates)} gates")
simplified = CircuitSimplifier().simplify(circuit)
print(f"Simplified: {len(simplified.gates)} gates")
```

## 2. Gate Decomposition

Decompose gates into hardware-native gate sets.

```python
# Check native gate sets for different hardware
print("Native Gate Sets:")
print("-" * 40)
print("universal: ['H', 'T', 'CNOT']")
print("clifford: ['H', 'S', 'CNOT']")
print("rigetti: ['CZ', 'RX', 'RZ']")
print("\nNote: IBM/Google/IonQ native gates are defined but some")
print("(SX, ECR, PhasedXPow) are not yet implemented in AbirQu.")
```

### IBM Native Gates

```python
# Compile to universal gate set
compiler = CircuitCompiler(target='universal')

# Create a circuit with non-native gates
circuit = Circuit(2, "to_compile")
circuit.add_gate("H", [0])
circuit.add_gate("CNOT", [0, 1])
circuit.add_gate("SWAP", [0, 1])

print(f"Original: {len(circuit.gates)} gates")
compiled = compiler.compile(circuit)
print(f"Compiled (universal): {len(compiled.gates)} gates")
```

### Clifford Compilation

```python
# Compile to Clifford gates
compiler = CircuitCompiler(target='clifford')

circuit = Circuit(2, "clifford_target")
circuit.add_gate("H", [0])
circuit.add_gate("CNOT", [0, 1])

compiled = compiler.compile(circuit)
print(f"Compiled (Clifford): {len(compiled.gates)} gates")
```

## 3. Universal Compilation

Decompose any circuit into universal gate sets.

```python
# Universal compilation
compiler = CircuitCompiler(target='universal')

# Create a circuit with various gates
circuit = Circuit(2, "universal_test")
circuit.add_gate("H", [0])
circuit.add_gate("CNOT", [0, 1])
circuit.add_gate("T", [0])
circuit.add_gate("S", [1])

compiled = compiler.compile(circuit)
stats = compiler.get_stats()

print(f"Original gates: {stats['original_gates']}")
print(f"Compiled gates: {stats['compiled_gates']}")
print(f"Optimizations: {stats['optimizations_applied']}")
```

## 4. Custom Gate Decomposer

```python
# Create a custom decomposer
decomposer = GateDecomposer(['H', 'T', 'CNOT'])

# Decompose a single gate
from abirqu.circuit import Gate
gate = Gate("S", [0])
decomposed = decomposer.decompose(gate)

print(f"S gate decomposed to {len(decomposed)} gates:")
for g in decomposed:
    print(f"  {g.name} on qubits {g.qubits}")
```

## 5. Optimization Pipeline

```python
def optimize_circuit(circuit, target='universal', optimize=True):
    """Full optimization pipeline."""
    # Step 1: Simplify
    simplifier = CircuitSimplifier()
    simplified = simplifier.simplify(circuit)

    # Step 2: Compile to target
    compiler = CircuitCompiler(target=target)
    compiled = compiler.compile(simplified, optimize=optimize)

    return compiled, compiler.get_stats()

# Example
circuit = Circuit(2, "pipeline_test")
circuit.add_gate("H", [0])
circuit.add_gate("CNOT", [0, 1])
circuit.add_gate("X", [0])
circuit.add_gate("X", [0])  # Will be cancelled

optimized, stats = optimize_circuit(circuit, target='universal')
print(f"Optimization results:")
print(f"  Original: {stats['original_gates']} gates")
print(f"  Optimized: {stats['compiled_gates']} gates")
print(f"  Reduction: {stats['original_gates'] - stats['compiled_gates']} gates")
```

## 6. Hardware-Specific Optimization

```python
# Compare compilation across targets
circuit = Circuit(2, "comparison")
circuit.add_gate("H", [0])
circuit.add_gate("CNOT", [0, 1])
circuit.add_gate("T", [0])
circuit.add_gate("S", [1])

targets = ['universal', 'clifford']
for target in targets:
    compiler = CircuitCompiler(target=target)
    compiled = compiler.compile(circuit)
    stats = compiler.get_stats()
    print(f"{target:10}: {stats['original_gates']} → {stats['compiled_gates']} gates")
```

## 7. Running Optimized Circuits

```python
# Create, optimize, and run
circuit = Circuit(2, "run_test")
circuit.add_gate("H", [0])
circuit.add_gate("CNOT", [0, 1])
circuit.add_gate("T", [0])
circuit.add_gate("S", [1])

# Optimize
compiler = CircuitCompiler(target='universal')
optimized = compiler.compile(circuit)

# Run
backend = get_best_backend(n_qubits=2)
result = backend.run_circuit(optimized, shots=1000)
print("Optimized circuit executed successfully!")
```

## Summary

In this tutorial, you learned:
1. **Circuit simplification**: Remove redundant gates
2. **Gate decomposition**: Convert to hardware-native gates
3. **Target compilation**: Optimize for specific hardware
4. **Optimization pipelines**: Combine multiple techniques
5. **Hardware-specific optimization**: Choose the best compilation strategy

## Best Practices

1. Always simplify before compiling
2. Choose the right target for your hardware
3. Profile gate counts before and after optimization
4. Consider noise characteristics when optimizing
