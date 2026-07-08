"""
Validated QEC: Threshold analysis for surface codes (distance 3/5/7).

Simulates error correction at multiple code distances to estimate the
error correction threshold — the crossing point where larger codes
start outperforming smaller ones.
"""

import numpy as np
from typing import Dict, List
from ..qec.surface_code import RotatedSurfaceCode
from ..qec.decoder import SyndromeDecoder


def _simulate_error_correction(
    distance: int,
    error_rate: float,
    num_trials: int,
    seed: int = 42,
) -> float:
    """Simulate error correction at a given distance and error rate.

    Returns the fraction of trials where the decoder successfully corrects errors.
    """
    rng = np.random.RandomState(seed + distance * 1000 + int(error_rate * 10000))
    code = RotatedSurfaceCode(distance=distance)
    decoder = SyndromeDecoder(code)

    n_data = len(code.data_qubits)
    success = 0

    for _ in range(num_trials):
        # Generate random X errors on data qubits
        errors = rng.random(n_data) < error_rate
        error_indices = np.where(errors)[0]

        if len(error_indices) == 0:
            success += 1
            continue

        # Compute syndrome from errors (pass as binary array)
        syndrome = code.syndrome_x(errors.astype(int))

        # Decode
        try:
            correction = dec.decode(syndrome)

            # Apply correction and check if errors remain
            corrected_errors = errors.copy()
            for idx in range(len(correction)):
                if idx < len(corrected_errors) and correction[idx]:
                    corrected_errors[idx] ^= 1

            # Success if no errors remain
            if not np.any(corrected_errors):
                success += 1
        except Exception:
            pass  # Decoder failed = logical error

    return success / num_trials


def threshold_analysis(
    distances: List[int] = [3, 5, 7],
    error_rates: List[float] = None,
    num_trials: int = 1500,
) -> Dict:
    """Run multi-distance threshold crossing analysis.

    Returns dict with results including threshold estimate.
    """
    if error_rates is None:
        error_rates = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25]

    results = {}
    for d in distances:
        success_rates = []
        for p in error_rates:
            success = _simulate_error_correction(d, p, num_trials)
            success_rates.append(success)
        results[d] = {
            "error_rates": error_rates,
            "success_rates": success_rates,
            "logical_error_rates": [1 - s for s in success_rates],
        }

    threshold = _estimate_threshold(results, error_rates)

    return {
        "distances": distances,
        "error_rates": error_rates,
        "results": results,
        "threshold_estimate": threshold,
        "num_trials": num_trials,
    }


def _estimate_threshold(results: Dict, error_rates: List[float]) -> float:
    """Estimate threshold from crossing point of different distances."""
    distances = sorted(results.keys())
    if len(distances) < 2:
        return 0.0

    d_min, d_max = distances[0], distances[-1]
    log_err_min = results[d_min]["logical_error_rates"]
    log_err_max = results[d_max]["logical_error_rates"]

    threshold = error_rates[-1]
    for i in range(len(error_rates) - 1):
        diff_before = log_err_min[i] - log_err_max[i]
        diff_after = log_err_min[i + 1] - log_err_max[i + 1]
        if diff_before * diff_after < 0:
            threshold = error_rates[i] + (error_rates[i + 1] - error_rates[i]) * (
                abs(diff_before) / (abs(diff_before) + abs(diff_after))
            )
            break

    return threshold


def print_threshold_report(analysis: Dict):
    """Print a formatted threshold analysis report."""
    print("=" * 70)
    print("QEC THRESHOLD ANALYSIS — Rotated Surface Code")
    print("=" * 70)
    print(f"Distances tested: {analysis['distances']}")
    print(f"Trials per point: {analysis['num_trials']}")
    print()

    header = f"{'p (physical)':>12}"
    for d in analysis["distances"]:
        header += f"  {'d=' + str(d) + ' log_err':>14}"
    print(header)
    print("-" * 70)

    for i, p in enumerate(analysis["error_rates"]):
        row = f"{p:>12.3f}"
        for d in analysis["distances"]:
            log_err = analysis["results"][d]["logical_error_rates"][i]
            row += f"  {log_err:>14.4f}"
        print(row)

    print("-" * 70)
    th = analysis["threshold_estimate"]
    print(f"Estimated threshold: {th:.4f} ({th*100:.2f}%)")
    print()
    print("Surface code literature threshold: ~0.5-1.0%")
    print("=" * 70)


if __name__ == "__main__":
    analysis = threshold_analysis()
    print_threshold_report(analysis)
