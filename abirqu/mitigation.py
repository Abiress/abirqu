"""Error mitigation helpers wired to phase 20 implementations."""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def counts_to_probabilities(counts: Dict[str, int]) -> Dict[str, float]:
    total = float(sum(counts.values()))
    if total <= 0:
        return {}
    return {state: float(c) / total for state, c in counts.items()}


def probabilities_to_vector(probs: Dict[str, float]) -> np.ndarray:
    if not probs:
        return np.array([], dtype=float)
    ordered = sorted(probs.items(), key=lambda kv: kv[0])
    return np.array([p for _, p in ordered], dtype=float)


class ErrorMitigationFlow:
    """Convenience wrapper for readout mitigation + ZNE extrapolation."""

    def __init__(self) -> None:
        from .phases.phase20 import ErrorMitigationPipeline, ReadoutErrorMitigator, ZeroNoiseExtrapolator

        self._readout = ReadoutErrorMitigator()
        self._zne = ZeroNoiseExtrapolator()
        self._pipe = ErrorMitigationPipeline()

    def run_from_probabilities(
        self,
        probs: Dict[str, float],
        confusion: Sequence[Sequence[float]],
        noise_scales: Sequence[float],
        measured_values: Sequence[float],
    ) -> Dict[str, float]:
        p = probabilities_to_vector(probs)
        if p.size == 0:
            return {"zne_zero_noise": 0.0, "corrected_sum": 0.0, "max_corrected_prob": 0.0}
        return self._pipe.run(
            noisy_probs=p,
            confusion=np.asarray(confusion, dtype=float),
            noise_scales=noise_scales,
            measured_values=measured_values,
        )

    def run_from_counts(
        self,
        counts: Dict[str, int],
        confusion: Sequence[Sequence[float]],
        noise_scales: Sequence[float],
        measured_values: Sequence[float],
    ) -> Dict[str, float]:
        return self.run_from_probabilities(
            probs=counts_to_probabilities(counts),
            confusion=confusion,
            noise_scales=noise_scales,
            measured_values=measured_values,
        )
