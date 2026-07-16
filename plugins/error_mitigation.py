"""
AbirQu Plugin: Quantum Error Mitigation
Zero-noise extrapolation (ZNE), probabilistic error cancellation (PEC),
and Clifford data regression (CDR) error mitigation strategies.
"""
import math
import random
from typing import Any, Dict, List, Optional


PLUGIN_NAME = "error_mitigation"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "Error mitigation strategies for quantum circuits"


def activate(context: Dict[str, Any]) -> None:
    """Called when the plugin is loaded."""
    pass


def deactivate() -> None:
    """Called when the plugin is unloaded."""
    pass


def get_manifest() -> Dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "author": PLUGIN_AUTHOR,
        "description": PLUGIN_DESCRIPTION,
    }


# ─────────────────────────────────────────────────────────────
# Zero-Noise Extrapolation (ZNE)
# ─────────────────────────────────────────────────────────────

def zero_noise_extrapolation(
    ideal_result: Dict[str, Any],
    noisy_results: List[Dict[str, Any]],
    noise_levels: List[float],
    method: str = "linear",
) -> Dict[str, Any]:
    """Extrapolate to zero noise from noisy results at different noise levels.

    Args:
        ideal_result: The noiseless reference result (from simulation).
        noisy_results: List of noisy measurement results at increasing noise levels.
        noise_levels: Noise amplification factors (e.g., [1.0, 2.0, 3.0]).
        method: Extrapolation method - "linear", "richardson", or "exponential".

    Returns:
        Dict with mitigated expectation value, variance, and extrapolation details.
    """
    if not noisy_results or len(noisy_results) != len(noise_levels):
        raise ValueError("noisy_results and noise_levels must have the same length")

    noisy_expvals = []
    for r in noisy_results:
        counts = r.get("counts", {})
        shots = sum(counts.values()) if counts else 1
        expval = 0.0
        for bitstring, count in counts.items():
            # Map bitstring to eigenvalue: even parity -> +1, odd -> -1
            parity = sum(1 for b in bitstring if b == '1')
            eigenvalue = 1 if parity % 2 == 0 else -1
            expval += eigenvalue * count / shots
        noisy_expvals.append(expval)

    if method == "linear" and len(noise_levels) >= 2:
        x = noise_levels
        y = noisy_expvals
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        denom = n * sum_x2 - sum_x * sum_x
        if abs(denom) > 1e-12:
            slope = (n * sum_xy - sum_x * sum_y) / denom
            intercept = (sum_y - slope * sum_x) / n
        else:
            slope = 0.0
            intercept = sum_y / n
        mitigated = intercept
        residuals = [y - (slope * x + intercept) for x, y in zip(x, y)]
        variance = sum(r * r for r in residuals) / max(n - 2, 1)

    elif method == "richardson" and len(noise_levels) >= 2:
        # Richardson extrapolation: alternating-sign weighted sum
        n = len(noisy_expvals)
        mitigated = 0.0
        for i in range(n):
            coeff = 1.0
            for j in range(n):
                if j != i:
                    coeff *= noise_levels[j] / (noise_levels[j] - noise_levels[i])
            mitigated += coeff * noisy_expvals[i]
        variance = sum((v - mitigated) ** 2 for v in noisy_expvals) / n

    elif method == "exponential" and len(noise_levels) >= 2:
        # Fit y = a * exp(-b * x) + c
        ln_y = [math.log(abs(v) + 1e-15) for v in noisy_expvals]
        n = len(noise_levels)
        sum_x = sum(noise_levels)
        sum_lny = sum(ln_y)
        sum_x2 = sum(x * x for x in noise_levels)
        sum_xlny = sum(x * ly for x, ly in zip(noise_levels, ln_y))
        denom = n * sum_x2 - sum_x * sum_x
        if abs(denom) > 1e-12:
            b = -(n * sum_xlny - sum_x * sum_lny) / denom
            a = math.exp((sum_lny + b * sum_x) / n)
        else:
            b = 0.0
            a = math.exp(sum_lny / n)
        mitigated = a
        variance = sum((v - a * math.exp(-b * x)) ** 2 for v, x in zip(noisy_expvals, noise_levels)) / n

    else:
        mitigated = noisy_expvals[0]
        variance = 0.0

    return {
        "mitigated_expval": mitigated,
        "noisy_expvals": noisy_expvals,
        "noise_levels": noise_levels,
        "method": method,
        "variance": variance,
        "improvement": abs(noisy_expvals[0] - mitigated) if noisy_expvals else 0.0,
    }


# ─────────────────────────────────────────────────────────────
# Probabilistic Error Cancellation (PEC)
# ─────────────────────────────────────────────────────────────

def probabilistic_error_cancellation(
    noisy_counts: Dict[str, int],
    noise_model: Dict[str, float],
    shots: int,
) -> Dict[str, Any]:
    """Apply PEC to cancel readout and single-qubit errors.

    Args:
        noisy_counts: Measurement counts from noisy circuit.
        noise_model: Dict mapping (qubit, error_type) -> error_probability.
        shots: Total number of shots.

    Returns:
        Dict with mitigated counts.
    """
    qubits = set()
    for (qubit, _) in noise_model:
        qubits.add(qubit)

    def apply_inverse(counts: Dict[str, int], qubit: int, err_prob: float) -> Dict[str, int]:
        if err_prob <= 0 or err_prob >= 1:
            return counts
        scale = 1.0 / (1.0 - 2.0 * err_prob)
        new_counts: Dict[str, int] = {}
        for bitstring, count in counts.items():
            q_idx = qubit if qubit < len(bitstring) else len(bitstring) - 1
            flipped = list(bitstring)
            flipped[q_idx] = '0' if flipped[q_idx] == '1' else '1'
            flipped_str = ''.join(flipped)
            new_count = max(0, int(count * scale))
            flipped_count = max(0, int(count * err_prob * scale))
            new_counts[bitstring] = new_counts.get(bitstring, 0) + new_count
            new_counts[flipped_str] = new_counts.get(flipped_str, 0) + flipped_count
        return new_counts

    result = dict(noisy_counts)
    for (qubit, err_type), err_prob in noise_model.items():
        result = apply_inverse(result, qubit, err_prob)

    total = sum(result.values())
    if total > 0:
        scale_factor = shots / total
        result = {k: max(1, int(v * scale_factor)) for k, v in result.items()}

    return {"mitigated_counts": result, "noise_model": noise_model, "compensation_applied": True}


# ─────────────────────────────────────────────────────────────
# Clifford Data Regression (CDR)
# ─────────────────────────────────────────────────────────────

def clifford_data_regression(
    training_data: List[Dict[str, Any]],
    noisy_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply CDR to mitigate errors using near-Clifford training data.

    Args:
        training_data: List of dicts with 'ideal_expval' and 'noisy_expval'.
        noisy_results: Noisy results to mitigate.

    Returns:
        Dict with mitigated expectation values.
    """
    if not training_data:
        return {"mitigated_expvals": [], "warning": "no training data"}

    ideal_vals = [d["ideal_expval"] for d in training_data]
    noisy_vals = [d["noisy_expval"] for d in training_data]

    n = len(training_data)
    sum_x = sum(noisy_vals)
    sum_y = sum(ideal_vals)
    sum_xy = sum(x * y for x, y in zip(noisy_vals, ideal_vals))
    sum_x2 = sum(x * x for x in noisy_vals)
    denom = n * sum_x2 - sum_x * sum_x

    if abs(denom) > 1e-12:
        alpha = (n * sum_xy - sum_x * sum_y) / denom
        beta = (sum_y - alpha * sum_x) / n
    else:
        alpha = 1.0
        beta = 0.0

    mitigated = []
    for r in noisy_results:
        counts = r.get("counts", {})
        shots = sum(counts.values()) if counts else 1
        expval = 0.0
        for bitstring, count in counts.items():
            parity = sum(1 for b in bitstring if b == '1')
            eigenvalue = 1 if parity % 2 == 0 else -1
            expval += eigenvalue * count / shots
        mitigated_val = alpha * expval + beta
        mitigated.append(mitigated_val)

    residuals = [i - (alpha * n + beta) for i, n in zip(ideal_vals, noisy_vals)]
    train_mse = sum(r * r for r in residuals) / n

    return {
        "mitigated_expvals": mitigated,
        "alpha": alpha,
        "beta": beta,
        "train_mse": train_mse,
    }


# ─────────────────────────────────────────────────────────────
# Readout Error Mitigation
# ─────────────────────────────────────────────────────────────

def mitigate_readout_error(
    noisy_counts: Dict[str, int],
    calibration_matrix: List[List[float]],
    shots: int,
) -> Dict[str, Any]:
    """Apply readout error mitigation using a calibration (confusion) matrix.

    Args:
        noisy_counts: Measured bitstring counts.
        calibration_matrix: C[i][j] = P(measure i | true state j).
        shots: Total number of shots.

    Returns:
        Dict with mitigated counts.
    """
    n_states = len(calibration_matrix)
    if n_states == 0:
        return {"mitigated_counts": noisy_counts, "applied": False}

    max_bits = max((len(k) for k in noisy_counts.keys()), default=0)
    if max_bits == 0:
        return {"mitigated_counts": noisy_counts, "applied": False}

    probs = [0.0] * n_states
    for bitstring, count in noisy_counts.items():
        idx = int(bitstring, 2) if bitstring else 0
        if idx < n_states:
            probs[idx] = count / shots

    inv_matrix = [row[:] for row in calibration_matrix]
    n = min(n_states, len(inv_matrix))
    identity = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        max_val = abs(inv_matrix[i][i])
        max_row = i
        for k in range(i + 1, n):
            if abs(inv_matrix[k][i]) > max_val:
                max_val = abs(inv_matrix[k][i])
                max_row = k
        inv_matrix[i], inv_matrix[max_row] = inv_matrix[max_row], inv_matrix[i]
        identity[i], identity[max_row] = identity[max_row], identity[i]
        pivot = inv_matrix[i][i]
        if abs(pivot) < 1e-15:
            continue
        inv_matrix[i] = [x / pivot for x in inv_matrix[i]]
        identity[i] = [x / pivot for x in identity[i]]
        for k in range(n):
            if k == i:
                continue
            factor = inv_matrix[k][i]
            inv_matrix[k] = [inv_matrix[k][j] - factor * inv_matrix[i][j] for j in range(n)]
            identity[k] = [identity[k][j] - factor * identity[i][j] for j in range(n)]

    corrected = [0.0] * n_states
    for i in range(n_states):
        for j in range(n_states):
            corrected[i] += identity[i][j] * probs[j]

    mitigated_counts = {}
    for i in range(n_states):
        count = max(0, int(corrected[i] * shots + 0.5))
        if count > 0:
            bitstring = format(i, f'0{max_bits}b')
            mitigated_counts[bitstring] = count

    return {"mitigated_counts": mitigated_counts, "applied": True, "shots": shots}
