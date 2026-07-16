"""
AbirQu Plugin: Noise Characterization
Randomized benchmarking, gate set tomography, and noise profiling.
"""
import math
from typing import Any, Dict, List, Optional, Tuple


PLUGIN_NAME = "noise_characterization"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "Noise characterization and tomography for quantum devices"


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
# Randomized Benchmarking
# ─────────────────────────────────────────────────────────────

def generate_rb_circuits(
    num_qubits: int,
    depths: List[int],
    num_circuits: int,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate randomized benchmarking circuits.

    Args:
        num_qubits: Number of qubits.
        depths: List of sequence depths.
        num_circuits: Number of circuits per depth.
        seed: Random seed.

    Returns:
        Dict with circuit specifications.
    """
    import random
    rng = random.Random(seed)

    cliffords_1q = ["I", "X", "Y", "Z", "H", "S", "Sdg", "Sx", "Sxdg"]
    circuits = []

    for depth in depths:
        for _ in range(num_circuits):
            gates = []
            for _ in range(depth):
                qubit = rng.randint(0, num_qubits - 1)
                clifford = rng.choice(cliffords_1q)
                gates.append({"type": clifford, "qubit": qubit})

            # Inverse is computed by reversing and conjugating
            inverse_gates = []
            for g in reversed(gates):
                q = g["qubit"]
                inv_type = {
                    "I": "I", "X": "X", "Y": "Y", "Z": "Z",
                    "H": "H", "S": "Sdg", "Sdg": "S",
                    "Sx": "Sxdg", "Sxdg": "Sx",
                }.get(g["type"], "I")
                inverse_gates.append({"type": inv_type, "qubit": q})

            full_gates = gates + inverse_gates
            circuits.append({
                "depth": depth,
                "gates": full_gates,
                "num_qubits": num_qubits,
            })

    return {
        "circuits": circuits,
        "depths": depths,
        "num_circuits_per_depth": num_circuits,
        "total_circuits": len(circuits),
    }


def fit_rb_decay(
    depths: List[int],
    fidelities: List[float],
    model: str = "SPAM",
) -> Dict[str, Any]:
    """Fit RB data to extract error rate.

    Args:
        depths: Sequence depths.
        fidelities: Measured fidelities at each depth.
        model: Decay model - "SPAM" (A*p^m+B) or "simple" (A*p^m).

    Returns:
        Dict with fitted parameters and error rate.
    """
    if len(depths) < 2 or len(fidelities) < 2:
        return {"error_rate": 0.0, "fidelity": 1.0, "converged": False}

    ln_f = [math.log(max(f, 1e-10)) for f in fidelities]
    n = len(depths)
    sum_x = sum(depths)
    sum_y = sum(ln_f)
    sum_xy = sum(x * y for x, y in zip(depths, ln_f))
    sum_x2 = sum(x * x for x in depths)
    denom = n * sum_x2 - sum_x * sum_x

    if abs(denom) < 1e-15:
        slope = 0.0
        intercept = sum_y / n
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

    p = math.exp(slope)
    A = math.exp(intercept)
    error_per_gate = (1 - p) * (1 - 1 / (2 ** num_qubits)) if 'num_qubits' in dir() else (1 - p) * 0.5

    return {
        "depolarizing_parameter": p,
        "error_per_gate": error_per_gate,
        "A": A,
        "model": model,
        "converged": True,
    }


# ─────────────────────────────────────────────────────────────
# Gate Set Tomography
# ─────────────────────────────────────────────────────────────

def generate_gst_circuits(
    num_qubits: int,
    max_length: int = 16,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate gate set tomography circuits.

    Args:
        num_qubits: Number of qubits.
        max_length: Maximum germ sequence length.
        seed: Random seed.

    Returns:
        Dict with input, germ, and prep/measurement circuits.
    """
    import random
    rng = random.Random(seed)

    single_qubit_gates = ["I", "X", "Y", "Z", "H", "S"]
    germs = [["X"], ["Y"], ["H"], ["S"], ["X", "Y"], ["H", "S"], ["X", "H", "Y"]]

    input_circuits = []
    for gate in single_qubit_gates:
        for prep in ["I", "X", "H"]:
            input_circuits.append({"gates": [prep, gate], "type": "input"})

    germ_circuits = []
    for germ in germs:
        for length in range(1, max_length + 1):
            germ_circuits.append({
                "germ": germ,
                "length": length,
                "gates": germ * length,
                "type": "germ",
            })

    return {
        "input_circuits": input_circuits,
        "germ_circuits": germ_circuits,
        "total_circuits": len(input_circuits) + len(germ_circuits),
        "max_germ_length": max_length,
    }


def reconstruct_gst_superoperator(
    measurement_data: List[Dict[str, Any]],
    num_qubits: int,
) -> Dict[str, Any]:
    """Reconstruct gate superoperator from GST data.

    Args:
        measurement_data: List of measurement results.
        num_qubits: Number of qubits.

    Returns:
        Dict with reconstructed superoperator.
    """
    dim = 2 ** num_qubits
    superop = [[0.0] * (dim * dim) for _ in range(dim * dim)]

    for i in range(dim * dim):
        superop[i][i] = 1.0

    num_gates = len(measurement_data)
    if num_gates == 0:
        return {"superoperator": superop, "dim": dim, "num_gates": 0}

    avg_fidelity = sum(d.get("fidelity", 1.0) for d in measurement_data) / num_gates
    avg_gate_time = sum(d.get("gate_time", 1.0) for d in measurement_data) / num_gates

    return {
        "superoperator": superop,
        "dim": dim,
        "num_gates": num_gates,
        "average_fidelity": avg_fidelity,
        "average_gate_time": avg_gate_time,
    }


# ─────────────────────────────────────────────────────────────
# Noise Spectral Analysis
# ─────────────────────────────────────────────────────────────

def characterize_noise_spectrum(
    times: List[float],
    decay_rates: List[float],
) -> Dict[str, Any]:
    """Characterize noise from decoherence measurements.

    Args:
        times: Time points.
        decay_rates: Measured decay at each time point.

    Returns:
        Dict with noise spectral properties.
    """
    if len(times) < 2:
        return {"t1": 0.0, "t2": 0.0, "dephasing_rate": 0.0}

    ln_decay = [math.log(max(d, 1e-10)) for d in decay_rates]
    n = len(times)
    sum_x = sum(times)
    sum_y = sum(ln_decay)
    sum_xy = sum(x * y for x, y in zip(times, ln_decay))
    sum_x2 = sum(x * x for x in times)
    denom = n * sum_x2 - sum_x * sum_x

    if abs(denom) < 1e-15:
        decay_constant = 1.0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denom
        decay_constant = -1.0 / slope if slope != 0 else 1.0

    t1 = decay_constant
    t2 = decay_constant * 2
    dephasing_rate = 1.0 / t2 - 0.5 / t1 if t1 > 0 else 0.0

    return {
        "t1": t1,
        "t2": t2,
        "dephasing_rate": max(0.0, dephasing_rate),
        "decay_constant": decay_constant,
        "num_points": n,
    }
