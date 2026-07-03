"""
D-Wave Noise Profile
====================
Noise models for D-Wave quantum annealers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np


@dataclass
class DWaveNoiseProfile:
    """Noise profile for a D-Wave quantum annealer.

    Parameters
    ----------
    chain_break_fraction : float
        Expected fraction of chain breaks (0-1).
    spin_flip_probability : float
        Probability of a spin flip error per qubit.
    coupling_error_std : float
        Standard deviation of coupling strength errors.
    thermal_populations : dict
        Thermal excitation probabilities per qubit.
    readout_error : float
        Readout error probability.
    anneal_offset_std : float
        Standard deviation of per-qubit anneal offset calibration errors.
    """
    chain_break_fraction: float = 0.01
    spin_flip_probability: float = 0.005
    coupling_error_std: float = 0.02
    thermal_populations: Dict[int, float] = field(default_factory=dict)
    readout_error: float = 0.01
    anneal_offset_std: float = 0.001

    def apply_to_counts(
        self,
        counts: Dict[str, int],
        shots: int,
        num_qubits: int,
    ) -> Dict[str, int]:
        """Apply noise model to measurement counts."""
        noisy_counts: Dict[str, int] = {}

        for bitstring, count in counts.items():
            for _ in range(count):
                # Apply spin flip errors
                noisy_bits = list(bitstring)
                for i in range(num_qubits):
                    if np.random.random() < self.spin_flip_probability:
                        noisy_bits[i] = "1" if noisy_bits[i] == "0" else "0"
                noisy_key = "".join(noisy_bits)
                noisy_counts[noisy_key] = noisy_counts.get(noisy_key, 0) + 1

        return noisy_counts

    def apply_to_probabilities(
        self,
        probs: Dict[str, float],
        num_qubits: int,
    ) -> Dict[str, float]:
        """Apply noise model to probability distribution."""
        noisy: Dict[str, float] = {}

        for bitstring, prob in probs.items():
            # Each bit has a chance of being flipped
            for i in range(num_qubits):
                p_flip = self.spin_flip_probability
                if bitstring[i] == "0":
                    noisy[bitstring] = noisy.get(bitstring, 0) + prob * (1 - p_flip)
                    flipped = bitstring[:i] + "1" + bitstring[i+1:]
                    noisy[flipped] = noisy.get(flipped, 0) + prob * p_flip
                else:
                    noisy[bitstring] = noisy.get(bitstring, 0) + prob * (1 - p_flip)
                    flipped = bitstring[:i] + "0" + bitstring[i+1:]
                    noisy[flipped] = noisy.get(flipped, 0) + prob * p_flip

        # Normalize
        total = sum(noisy.values())
        if total > 0:
            noisy = {k: v / total for k, v in noisy.items()}

        return noisy


def get_advantage_noise_profile() -> DWaveNoiseProfile:
    """Pre-configured noise profile for D-Wave Advantage."""
    return DWaveNoiseProfile(
        chain_break_fraction=0.01,
        spin_flip_probability=0.005,
        coupling_error_std=0.02,
        readout_error=0.01,
        anneal_offset_std=0.001,
    )


def get_advantage2_noise_profile() -> DWaveNoiseProfile:
    """Pre-configured noise profile for D-Wave Advantage2."""
    return DWaveNoiseProfile(
        chain_break_fraction=0.005,
        spin_flip_probability=0.003,
        coupling_error_std=0.015,
        readout_error=0.008,
        anneal_offset_std=0.0005,
    )


def get_simulated_annealing_profile() -> DWaveNoiseProfile:
    """Noise profile for simulated annealing (minimal noise)."""
    return DWaveNoiseProfile(
        chain_break_fraction=0.0,
        spin_flip_probability=0.0,
        coupling_error_std=0.0,
        readout_error=0.0,
        anneal_offset_std=0.0,
    )
