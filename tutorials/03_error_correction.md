# Tutorial 3: Quantum Error Correction

## Introduction

Quantum Error Correction (QEC) protects quantum information from noise and decoherence.

## Prerequisites

```python
from abirqu.qec import SurfaceCode, LDPCCode
from abirqu.circuit import Circuit
from abirqu.backend import get_best_backend
```

## 1. Why Error Correction?

Quantum states are fragile:
- **Decoherence**: Environmental interactions destroy superposition
- **Gate errors**: Imperfect operations introduce errors
- **Measurement errors**: Readout is imperfect

Classical error correction duplicates bits. Quantum error correction uses entanglement.

## 2. Surface Codes

Surface codes are the most promising QEC approach for near-term devices.

```python
# Create a distance-3 surface code
code = SurfaceCode(distance=3)

print(f"Surface Code (d=3):")
print(f"  Distance: {code.distance}")
print(f"  Can correct: {(code.distance - 1) // 2} errors")
```

### Surface Code Properties

| Distance | Physical Qubits | Logical Qubits | Error Threshold |
|----------|----------------|----------------|-----------------|
| 3        | 17             | 1              | ~1%             |
| 5        | 49             | 1              | ~1%             |
| 7        | 97             | 1              | ~1%             |

```python
# Distance-5 surface code
code5 = SurfaceCode(distance=5)
print(f"Distance-5 code can correct {(code5.distance - 1) // 2} errors")
```

## 3. LDPC Codes

Low-Density Parity-Check (LDPC) codes are another class of QEC codes.

```python
# Create an LDPC code
code = LDPCCode()
print(f"LDPC Code: {code}")
```

## 4. Error Correction Workflow

```python
def qec_workflow():
    """Demonstrate the QEC workflow."""

    # 1. Create the code
    code = SurfaceCode(distance=3)

    # 2. Encode logical qubit
    # (In practice, this creates entanglement between data and ancilla qubits)

    # 3. Syndrome measurement
    # (Measure stabilizer operators to detect errors)

    # 4. Decoding
    # (Use classical algorithm to determine error location)

    # 5. Correction
    # (Apply recovery operation)

    print("QEC Workflow:")
    print("1. Encoding")
    print("2. Syndrome measurement")
    print("3. Decoding")
    print("4. Correction")

qec_workflow()
```

## 5. Logical vs Physical Operations

```python
# Logical operations on encoded qubits
code = SurfaceCode(distance=3)

print("Logical Operations:")
print("-" * 30)
print("Logical X: Applies X to all data qubits")
print("Logical Z: Applies Z to all data qubits")
print("Logical H: Transforms between X and Z stabilizers")
print("Logical CNOT: Uses lattice surgery")
```

## 6. Error Thresholds

```python
# Error threshold analysis
codes = [
    ("Surface d=3", 3),
    ("Surface d=5", 5),
    ("Surface d=7", 7),
]

print("Error Thresholds:")
print("-" * 40)
for name, distance in codes:
    threshold = 0.01  # ~1% for surface codes
    print(f"{name}: ~{threshold*100}% error threshold")
```

## 7. Resource Overhead

```python
# Resource estimation
def estimate_resources(distance, logical_qubits):
    """Estimate physical qubits needed."""
    # Surface code: ~d² physical qubits per logical qubit
    physical_per_logical = distance ** 2
    total = physical_per_logical * logical_qubits
    return total

print("Resource Estimation:")
print("-" * 40)
for d in [3, 5, 7, 9, 11]:
    total = estimate_resources(d, logical_qubits=10)
    print(f"Distance {d}: {total} physical qubits for 10 logical qubits")
```

## Summary

In this tutorial, you learned:
1. Why quantum error correction is necessary
2. How surface codes work
3. The QEC workflow (encode, measure, decode, correct)
4. Error thresholds and resource overhead

## Next Steps

- Tutorial 4: Circuit Optimization and Compilation
- Tutorial 5: Quantum Chemistry with VQE
