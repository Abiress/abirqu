"""
Data encoding circuits for AbirQu — quantum ML feature maps.

Unique to AbirQu:
- Amplitude encoding (log2(n) qubits for n features)
- Angle encoding (1 qubit per feature)
- ZZFeatureMap with custom entanglement
- IQP-style encoding for quantum kernels
"""
from __future__ import annotations
import math
from typing import List, Optional
from ..circuit import Circuit


def angle_encoding(num_qubits: int, features: Optional[List[float]] = None,
                   gate: str = "RY") -> Circuit:
    """
    Angle encoding: encode each feature as a rotation angle.

    |x> = RX(x_0) ⊗ RY(x_1) ⊗ ... ⊗ RZ(x_{n-1}) |0...0>

    Simple but limited to n features for n qubits.
    """
    c = Circuit(num_qubits, f"AngleEncoding({num_qubits})")
    if features is None:
        features = [0.0] * num_qubits

    for i, f in enumerate(features[:num_qubits]):
        c.add_gate(gate, i, [float(f)])

    return c


def amplitude_encoding(num_qubits: int, features: Optional[List[float]] = None) -> Circuit:
    """
    Amplitude encoding: encode n features into 2^n amplitudes.

    Uses RY rotations in a tree structure to distribute amplitudes.
    This is more efficient than angle encoding (log2(n) qubits for n features).

    Note: This is a simplified version. Full amplitude encoding
    requires controlled rotations.
    """
    c = Circuit(num_qubits, f"AmplitudeEncoding({num_qubits})")
    if features is None:
        features = [1.0 / math.sqrt(2 ** num_qubits)] * (2 ** num_qubits)

    # Normalize
    norm = math.sqrt(sum(f ** 2 for f in features))
    if norm > 0:
        features = [f / norm for f in features]

    # Tree-based amplitude encoding
    _amplitude_encode_tree(c, features, list(range(num_qubits)), 0)

    return c


def _amplitude_encode_tree(circuit: Circuit, features: List[float],
                           qubits: List[int], start_idx: int):
    """Recursive tree-based amplitude encoding."""
    if len(qubits) == 0 or start_idx >= len(features):
        return

    if len(qubits) == 1:
        # Leaf: encode single feature
        q = qubits[0]
        val = features[start_idx] if start_idx < len(features) else 0
        angle = 2 * math.asin(min(1.0, abs(val)))
        circuit.add_gate("RY", q, [angle])
        return

    # Split features between left and right subtrees
    mid = len(features) // 2
    left_features = features[:mid]
    right_features = features[mid:]

    # Apply controlled rotation
    q = qubits[0]
    total = math.sqrt(sum(f ** 2 for f in left_features)) if left_features else 0
    total_all = math.sqrt(sum(f ** 2 for f in features)) if features else 1
    angle = 2 * math.asin(min(1.0, total / total_all)) if total_all > 0 else 0
    circuit.add_gate("RY", q, [angle])

    # Recurse on subtrees
    _amplitude_encode_tree(circuit, left_features, qubits[1:], start_idx)
    _amplitude_encode_tree(circuit, right_features, qubits[1:], start_idx + mid)


def zz_feature_map(num_qubits: int, features: Optional[List[float]] = None,
                   reps: int = 1, prefix: str = "x") -> Circuit:
    """
    ZZFeatureMap — data-dependent entanglement for quantum kernels.

    Each layer:
    1. RZ(x_i) on each qubit
    2. ZZ(x_i * x_j) on each pair

    This creates a feature map where entanglement depends on
    the input data, useful for quantum kernel methods.
    """
    c = Circuit(num_qubits, f"ZZFeatureMap({num_qubits})")
    if features is None:
        features = [0.0] * num_qubits

    for rep in range(reps):
        # Hadamard layer
        for q in range(num_qubits):
            c.h(q)

        # Data encoding
        for i, f in enumerate(features[:num_qubits]):
            c.add_gate("RZ", i, [float(f)])

        # ZZ entanglement
        for i in range(num_qubits):
            for j in range(i + 1, min(i + 3, num_qubits)):
                # ZZ(x_i * x_j) via CNOT + RZ + CNOT
                fi = features[i] if i < len(features) else 0
                fj = features[j] if j < len(features) else 0
                angle = fi * fj
                c.add_gate("CNOT", [i, j])
                c.add_gate("RZ", j, [angle])
                c.add_gate("CNOT", [i, j])

    return c


def iqp_encoding(num_qubits: int, features: Optional[List[float]] = None,
                 prefix: str = "x") -> Circuit:
    """
    IQP (Instantaneous Quantum Polynomial) encoding.

    Unique to AbirQu: creates highly entangled states useful
    for quantum advantage demonstrations.

    Structure: H ⊗ H ⊗ ... ⊗ H → diag(XX+ZZ+XZXZX) → H ⊗ H ⊗ ...
    """
    c = Circuit(num_qubits, f"IQPEncoding({num_qubits})")
    if features is None:
        features = [0.0] * num_qubits

    # Initial Hadamards
    for q in range(num_qubits):
        c.h(q)

    # Diagonal unitary
    for i in range(num_qubits):
        fi = features[i] if i < len(features) else 0
        c.add_gate("RZ", i, [float(fi)])

    for i in range(num_qubits):
        for j in range(i + 1, num_qubits):
            fi = features[i] if i < len(features) else 0
            fj = features[j] if j < len(features) else 0
            angle = fi * fj
            c.add_gate("CNOT", [i, j])
            c.add_gate("RZ", j, [angle])
            c.add_gate("CNOT", [i, j])

    # Final Hadamards
    for q in range(num_qubits):
        c.h(q)

    return c
