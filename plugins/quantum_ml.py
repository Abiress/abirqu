"""
AbirQu Plugin: Quantum Machine Learning
Quantum kernels, variational classifiers, and QNN building blocks.
"""
import math
from typing import Any, Dict, List, Optional, Tuple


PLUGIN_NAME = "quantum_ml"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "Quantum ML kernels, classifiers, and QNN building blocks"


def activate(context: Dict[str, Any]) -> None:
    pass


def deactivate() -> None:
    pass


def get_manifest() -> Dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "author": PLUGIN_AUTHOR,
        "description": PLUGIN_DESCRIPTION,
    }


# ─────────────────────────────────────────────────────────────
# Quantum Feature Maps
# ─────────────────────────────────────────────────────────────

def angle_encoding(x: List[float], num_qubits: int) -> Dict[str, Any]:
    """Encode classical data as rotation angles.

    Args:
        x: Input features.
        num_qubits: Number of qubits.

    Returns:
        Dict with gate specification.
    """
    gates = []
    for i in range(min(len(x), num_qubits)):
        gates.append({"type": "Ry", "qubit": i, "angle": x[i]})
    return {"gates": gates, "num_qubits": num_qubits, "encoding": "angle"}


def amplitude_encoding(x: List[float], num_qubits: int) -> Dict[str, Any]:
    """Encode classical data as amplitudes.

    Args:
        x: Input features (will be normalized).
        num_qubits: Number of qubits (2^num_qubits >= len(x)).

    Returns:
        Dict with gate specification.
    """
    norm = math.sqrt(sum(v * v for v in x)) or 1.0
    normalized = [v / norm for v in x]
    return {"amplitudes": normalized, "num_qubits": num_qubits, "encoding": "amplitude"}


def data_reuploading_encoding(x: List[float], num_qubits: int, layers: int) -> Dict[str, Any]:
    """Data re-uploading: encode features in each layer.

    Args:
        x: Input features.
        num_qubits: Number of qubits.
        layers: Number of encoding layers.

    Returns:
        Dict with gate specification.
    """
    gates = []
    param_idx = 0
    for layer in range(layers):
        for i in range(min(len(x), num_qubits)):
            gates.append({"type": "Ry", "qubit": i, "angle": x[i], "layer": layer})
            param_idx += 1
        for i in range(num_qubits - 1):
            gates.append({"type": "CNOT", "control": i, "target": i + 1, "layer": layer})
    return {"gates": gates, "num_qubits": num_qubits, "encoding": "data_reuploading"}


# ─────────────────────────────────────────────────────────────
# Quantum Kernels
# ─────────────────────────────────────────────────────────────

def quantum_kernel_matrix(
    x1: List[List[float]],
    x2: List[List[float]],
    num_qubits: int,
    encoding: str = "angle",
) -> Dict[str, Any]:
    """Compute quantum kernel matrix K(x1, x2) = |<phi(x1)|phi(x2)>|^2.

    Args:
        x1: First set of feature vectors.
        x2: Second set of feature vectors.
        num_qubits: Number of qubits.
        encoding: Encoding type.

    Returns:
        Dict with kernel matrix.
    """
    n1 = len(x1)
    n2 = len(x2)
    matrix = [[0.0] * n2 for _ in range(n1)]

    for i in range(n1):
        for j in range(n2):
            overlap = 0.0
            for k in range(min(len(x1[i]), len(x2[j]), num_qubits)):
                diff = x1[i][k] - x2[j][k]
                overlap += math.exp(-diff * diff / 2.0)
            matrix[i][j] = overlap / min(num_qubits, max(len(x1[i]), 1))

    return {"kernel_matrix": matrix, "shape": [n1, n2], "encoding": encoding}


def fidelity_kernel(x1: List[float], x2: List[float], num_qubits: int) -> float:
    """Compute fidelity-based quantum kernel between two feature vectors.

    Returns:
        Kernel value in [0, 1].
    """
    angle1 = angle_encoding(x1, num_qubits)
    angle2 = angle_encoding(x2, num_qubits)

    fidelity = 0.0
    n = min(len(x1), len(x2), num_qubits)
    for i in range(n):
        diff = x1[i] - x2[i]
        fidelity += math.cos(diff / 2) ** 2

    return fidelity / max(n, 1)


# ─────────────────────────────────────────────────────────────
# Variational Quantum Classifier
# ─────────────────────────────────────────────────────────────

def variational_classifier(
    num_qubits: int,
    num_classes: int = 2,
    ansatz: str = "hardware_efficient",
    optimizer: str = "adam",
) -> Dict[str, Any]:
    """Design a variational quantum classifier.

    Args:
        num_qubits: Number of qubits.
        num_classes: Number of output classes.
        ansatz: Ansatz type.
        optimizer: Optimizer to use.

    Returns:
        Dict with classifier specification.
    """
    if ansatz == "hardware_efficient":
        params_per_layer = num_qubits * 2  # Ry + Rz per qubit
    elif ansatz == "data_reuploading":
        params_per_layer = num_qubits
    else:
        params_per_layer = num_qubits

    total_params = params_per_layer * 3

    return {
        "num_qubits": num_qubits,
        "num_classes": num_classes,
        "num_parameters": total_params,
        "ansatz": ansatz,
        "optimizer": optimizer,
        "measurement": "expectation_value" if num_classes == 2 else "multi_class",
        "type": "variational_classifier",
    }


# ─────────────────────────────────────────────────────────────
# Quantum Neural Network Layers
# ─────────────────────────────────────────────────────────────

def qnn_dense_layer(
    num_qubits: int,
    entangler: str = "linear",
) -> Dict[str, Any]:
    """Single dense QNN layer: parameterized rotations + entangling gates.

    Returns:
        Dict with gate specification.
    """
    gates = []
    param_idx = 0
    for q in range(num_qubits):
        gates.append({"type": "Ry", "qubit": q, "param": param_idx})
        param_idx += 1
        gates.append({"type": "Rz", "qubit": q, "param": param_idx})
        param_idx += 1

    if entangler == "linear":
        for q in range(num_qubits - 1):
            gates.append({"type": "CNOT", "control": q, "target": q + 1})
    elif entangler == "circular":
        for q in range(num_qubits):
            gates.append({"type": "CNOT", "control": q, "target": (q + 1) % num_qubits})
    elif entangler == "full":
        for q in range(num_qubits):
            for r in range(q + 1, num_qubits):
                gates.append({"type": "CNOT", "control": q, "target": r})

    return {"gates": gates, "num_parameters": param_idx, "num_qubits": num_qubits}


def quantum_dropout(gates: List[Dict], drop_rate: float = 0.1, seed: Optional[int] = None) -> List[Dict]:
    """Randomly drop gates from a circuit for regularization.

    Args:
        gates: Original gate list.
        drop_rate: Fraction of gates to drop.
        seed: Random seed.

    Returns:
        Filtered gate list.
    """
    import random
    rng = random.Random(seed)
    return [g for g in gates if rng.random() > drop_rate]
