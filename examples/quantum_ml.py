"""
Quantum Machine Learning — AbirQu
====================================
Demonstrates a variational quantum classifier (VQC) on a 2-class dataset.

The circuit encodes data as rotation angles, applies trainable rotations,
and measures to classify. This is the core pattern behind QML:

    Encode → Parameterise → Measure → Classical Loss → Update Params
"""
import math
import random
from typing import List, Tuple

from abirqu import Circuit, NumPySimulator


# ─────────────────────────────────────────────────────────────
# Data encoding (angle embedding)
# ─────────────────────────────────────────────────────────────

def encode_data(circuit: Circuit, data_point: List[float]) -> None:
    """Encode classical data as qubit rotation angles (RY gates)."""
    for qubit, value in enumerate(data_point):
        if qubit < circuit.num_qubits:
            circuit.ry(qubit, value * math.pi)


# ─────────────────────────────────────────────────────────────
# Variational ansatz (trainable layer)
# ─────────────────────────────────────────────────────────────

def variational_layer(circuit: Circuit, params: List[float]) -> None:
    """One variational layer: RY rotations + CNOT entangling gates."""
    n = circuit.num_qubits
    for i in range(n):
        circuit.ry(i, params[i])
    for i in range(n - 1):
        circuit.cnot(i, i + 1)


# ─────────────────────────────────────────────────────────────
# Classifier
# ─────────────────────────────────────────────────────────────

def classify(data_point: List[float], params: List[float], n_qubits: int = 2) -> float:
    """
    Run VQC and return probability of measuring |0...0⟩.
    Use this as the class-0 probability.
    """
    c = Circuit(n_qubits)
    encode_data(c, data_point)
    variational_layer(c, params[:n_qubits])
    variational_layer(c, params[n_qubits:])
    c.measure_all()

    sim = NumPySimulator(n_qubits)
    sim.run_circuit(c)
    probs = sim.get_probabilities()
    return probs.get("0" * n_qubits, 0.0)


def binary_cross_entropy(y_pred: float, y_true: int) -> float:
    eps = 1e-9
    y_pred = max(eps, min(1 - eps, y_pred))
    return -(y_true * math.log(y_pred) + (1 - y_true) * math.log(1 - y_pred))


# ─────────────────────────────────────────────────────────────
# Toy dataset: two clusters in [0,1]²
# ─────────────────────────────────────────────────────────────

def make_dataset(n: int = 8, seed: int = 42) -> List[Tuple[List[float], int]]:
    """Generate two linearly separable clusters."""
    random.seed(seed)
    dataset = []
    for _ in range(n // 2):
        # Class 0: cluster near (0.2, 0.2)
        x1 = 0.2 + random.gauss(0, 0.08)
        x2 = 0.2 + random.gauss(0, 0.08)
        dataset.append(([x1, x2], 0))
        # Class 1: cluster near (0.8, 0.8)
        x1 = 0.8 + random.gauss(0, 0.08)
        x2 = 0.8 + random.gauss(0, 0.08)
        dataset.append(([x1, x2], 1))
    random.shuffle(dataset)
    return dataset


# ─────────────────────────────────────────────────────────────
# Training loop
# ─────────────────────────────────────────────────────────────

def train(epochs: int = 20, n_qubits: int = 2) -> None:
    dataset = make_dataset(n=8)
    n_params = n_qubits * 2
    params = [random.uniform(0, 2 * math.pi) for _ in range(n_params)]

    print(f"\n  n_qubits={n_qubits}, parameters={n_params}, epochs={epochs}")
    print(f"  Training on {len(dataset)} samples\n")

    for epoch in range(epochs):
        total_loss = 0.0
        correct = 0
        for data_point, label in dataset:
            p0 = classify(data_point, params, n_qubits)
            # Class 0 → want high p0; Class 1 → want low p0
            y_pred = p0 if label == 0 else (1 - p0)
            loss = binary_cross_entropy(y_pred, 1)
            total_loss += loss

            pred_class = 0 if p0 > 0.5 else 1
            if pred_class == label:
                correct += 1

            # Gradient-free parameter update (random perturbation)
            if loss > 0.3:
                idx = random.randint(0, n_params - 1)
                params[idx] += random.gauss(0, 0.2)

        avg_loss = total_loss / len(dataset)
        accuracy = correct / len(dataset)
        bar = "█" * round(accuracy * 20)
        print(f"  Epoch {epoch+1:3d} | loss={avg_loss:.4f} | acc={accuracy:.2f}  {bar}")

    print(f"\n  Final accuracy: {correct}/{len(dataset)}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AbirQu — Variational Quantum Classifier")
    print("=========================================")
    print("\nBuilding a 2-class quantum ML model using angle embedding")
    print("and a 2-layer variational ansatz.\n")

    random.seed(0)
    train(epochs=15, n_qubits=2)

    # Show inference on new points
    print("\nInference on test points:")
    params_test = [0.5, 1.0, 1.5, 0.3]
    for point, label in [([0.2, 0.2], 0), ([0.8, 0.8], 1), ([0.5, 0.5], "?")]:
        p0 = classify(point, params_test, n_qubits=2)
        pred = "Class 0" if p0 > 0.5 else "Class 1"
        print(f"  x={point}  p(class 0)={p0:.4f}  → {pred}")

    print("\nDone! Try examples/qec_surface_code.py next.")
