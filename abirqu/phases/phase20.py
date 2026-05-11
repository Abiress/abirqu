from typing import Dict, List, Sequence

import numpy as np


class ReadoutErrorMitigator:
    def calibrate(self, measured_confusion: np.ndarray) -> np.ndarray:
        mat = np.asarray(measured_confusion, dtype=float)
        if mat.shape[0] != mat.shape[1]:
            raise ValueError("confusion matrix must be square")
        # Regularized inverse for numerical stability
        reg = 1e-8 * np.eye(mat.shape[0])
        return np.linalg.pinv(mat + reg)

    def mitigate(self, noisy_probs: np.ndarray, inv_confusion: np.ndarray) -> np.ndarray:
        p = np.asarray(noisy_probs, dtype=float)
        corrected = inv_confusion @ p
        corrected = np.clip(corrected, 0.0, None)
        s = corrected.sum()
        return corrected / s if s > 0 else corrected


class ZeroNoiseExtrapolator:
    def extrapolate(self, noise_scales: Sequence[float], values: Sequence[float]) -> float:
        x = np.asarray(noise_scales, dtype=float)
        y = np.asarray(values, dtype=float)
        if len(x) != len(y) or len(x) < 2:
            raise ValueError("Need at least 2 scale/value points")
        # Fit y = a*x + b; return b at x=0
        a, b = np.polyfit(x, y, 1)
        return float(b)


class PauliTwirlingPass:
    def twirl_metadata(self, gate_count: int, seed: int = 0) -> Dict[str, int]:
        rng = np.random.default_rng(seed)
        x = int(rng.integers(0, gate_count + 1))
        y = int(rng.integers(0, gate_count + 1 - x))
        z = gate_count - x - y
        return {"X": x, "Y": y, "Z": z, "total": gate_count}


class ErrorMitigationPipeline:
    def run(
        self,
        noisy_probs: np.ndarray,
        confusion: np.ndarray,
        noise_scales: Sequence[float],
        measured_values: Sequence[float],
    ) -> Dict[str, float]:
        rem = ReadoutErrorMitigator()
        inv = rem.calibrate(confusion)
        corrected = rem.mitigate(noisy_probs, inv)
        zne = ZeroNoiseExtrapolator().extrapolate(noise_scales, measured_values)
        return {
            "zne_zero_noise": zne,
            "corrected_sum": float(corrected.sum()),
            "max_corrected_prob": float(np.max(corrected) if len(corrected) else 0.0),
        }
