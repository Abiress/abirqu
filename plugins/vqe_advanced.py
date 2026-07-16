"""
AbirQu Plugin: Advanced VQE
UCCSD, hardware-efficient, and adaptive VQE variants with advanced optimizers.
"""
import math
from typing import Any, Dict, List, Optional, Tuple


PLUGIN_NAME = "vqe_advanced"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "Advanced VQE ansatze and optimizers for quantum chemistry"


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
# Advanced VQE Ansatze
# ─────────────────────────────────────────────────────────────

def uccsd_ansatz(num_qubits: int, num_electrons: int, depth: int = 1) -> Dict[str, Any]:
    """Generate UCCSD ansatz circuit specification.

    Args:
        num_qubits: Number of qubits.
        num_electrons: Number of electrons.
        depth: Number of UCCSD layers.

    Returns:
        Dict with gate sequence and parameter count.
    """
    num_occupied = num_electrons // 2
    num_virtual = num_qubits // 2 - num_occupied

    gates = []
    param_count = 0

    for _ in range(depth):
        for i in range(num_occupied):
            for a in range(num_virtual):
                occ_idx = i
                virt_idx = num_occupied + a
                gates.append({"type": "X", "qubit": occ_idx, "param": param_count})
                param_count += 1
                gates.append({"type": "CNOT", "control": occ_idx, "target": virt_idx})
                for j in range(i + 1, num_occupied):
                    occ_idx2 = j
                    gates.append({"type": "CNOT", "control": occ_idx, "target": occ_idx2})
                    param_count += 1

    return {
        "num_qubits": num_qubits,
        "num_parameters": param_count,
        "gates": gates,
        "ansatz": "uccsd",
    }


def hardware_efficient_ansatz(
    num_qubits: int,
    entangler: str = "circular",
    repetitions: int = 1,
) -> Dict[str, Any]:
    """Generate hardware-efficient ansatz circuit specification.

    Args:
        num_qubits: Number of qubits.
        entangler: Entangler type - "circular", "linear", or "full".
        repetitions: Number of repetitions.

    Returns:
        Dict with gate sequence and parameter count.
    """
    gates = []
    param_count = 0

    for rep in range(repetitions):
        for q in range(num_qubits):
            gates.append({"type": "Ry", "qubit": q, "param": param_count})
            param_count += 1
            gates.append({"type": "Rz", "qubit": q, "param": param_count})
            param_count += 1

        if entangler == "circular":
            for q in range(num_qubits):
                target = (q + 1) % num_qubits
                gates.append({"type": "CNOT", "control": q, "target": target})
        elif entangler == "linear":
            for q in range(num_qubits - 1):
                gates.append({"type": "CNOT", "control": q, "target": q + 1})
        elif entangler == "full":
            for q in range(num_qubits):
                for r in range(q + 1, num_qubits):
                    gates.append({"type": "CNOT", "control": q, "target": r})

    return {
        "num_qubits": num_qubits,
        "num_parameters": param_count,
        "gates": gates,
        "ansatz": "hardware_efficient",
    }


# ─────────────────────────────────────────────────────────────
# VQE Optimizers
# ─────────────────────────────────────────────────────────────

def adam_optimizer(
    params: List[float],
    gradients: List[float],
    state: Optional[Dict[str, Any]] = None,
    lr: float = 0.01,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8,
) -> Tuple[List[float], Dict[str, Any]]:
    """Adam optimizer step.

    Returns:
        Tuple of (updated_params, new_state).
    """
    if state is None:
        state = {"t": 0, "m": [0.0] * len(params), "v": [0.0] * len(params)}

    state["t"] += 1
    t = state["t"]

    new_params = []
    for i in range(len(params)):
        state["m"][i] = beta1 * state["m"][i] + (1 - beta1) * gradients[i]
        state["v"][i] = beta2 * state["v"][i] + (1 - beta2) * gradients[i] ** 2
        m_hat = state["m"][i] / (1 - beta1 ** t)
        v_hat = state["v"][i] / (1 - beta2 ** t)
        new_params.append(params[i] - lr * m_hat / (math.sqrt(v_hat) + epsilon))

    return new_params, state


def sgd_momentum_optimizer(
    params: List[float],
    gradients: List[float],
    velocity: Optional[List[float]] = None,
    lr: float = 0.01,
    momentum: float = 0.9,
) -> Tuple[List[float], List[float]]:
    """SGD with momentum.

    Returns:
        Tuple of (updated_params, new_velocity).
    """
    if velocity is None:
        velocity = [0.0] * len(params)

    new_velocity = []
    new_params = []
    for i in range(len(params)):
        v = momentum * velocity[i] + lr * gradients[i]
        new_velocity.append(v)
        new_params.append(params[i] - v)

    return new_params, new_velocity


def spsa_optimizer(
    params: List[float],
    objective_fn,
    a: float = 0.2,
    c: float = 0.1,
    k: int = 0,
    A: float = 10,
) -> Tuple[List[float], float]:
    """Simultaneous Perturbation Stochastic Approximation.

    Args:
        params: Current parameters.
        objective_fn: Function that takes parameters and returns cost.
        a: Step size scaling.
        c: Perturbation size.
        k: Iteration counter.
        A: Stability constant.

    Returns:
        Tuple of (updated_params, current_cost).
    """
    ak = a / (k + 1 + A) ** 0.602
    ck = c / (k + 1) ** 0.101

    cost_plus = objective_fn([p + ck for p in params])
    cost_minus = objective_fn([p - ck for p in params])

    gradient_estimate = [(cost_plus - cost_minus) / (2 * ck) for _ in params]

    new_params = [p - ak * g for p, g in zip(params, gradient_estimate)]

    return new_params, (cost_plus + cost_minus) / 2


# ─────────────────────────────────────────────────────────────
# Adaptive VQE
# ─────────────────────────────────────────────────────────────

def adaptive_vqe(
    num_qubits: int,
    num_electrons: int,
    max_ops: int = 20,
    threshold: float = 1e-4,
) -> Dict[str, Any]:
    """Design an adaptive VQE circuit by greedily selecting operators.

    Args:
        num_qubits: Number of qubits.
        num_electrons: Number of electrons.
        max_ops: Maximum number of operators.
        threshold: Convergence threshold.

    Returns:
        Dict with selected operators and expected convergence.
    """
    num_occupied = num_electrons // 2
    operators = []

    for i in range(num_occupied):
        for a in range(num_occupied, num_qubits // 2):
            operators.append({
                "type": "excitation",
                "from": i,
                "to": a,
                "weight": 1.0 / (a - i + 1),
            })

    operators.sort(key=lambda x: x["weight"], reverse=True)
    selected = operators[:max_ops]

    return {
        "num_qubits": num_qubits,
        "num_operators": len(selected),
        "operators": selected,
        "convergence_threshold": threshold,
        "ansatz": "adaptive_vqe",
    }
