"""
Neutral Atom Noise Profile
==========================
Noise models for neutral atom (Rydberg) processors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np


@dataclass
class NeutralAtomNoiseProfile:
    """Noise profile for a neutral atom (Rydberg) processor.

    Neutral atom characteristics:
    - Atom loss (atoms can be lost during trapping)
    - Dephasing (random Z rotations from fluctuating fields)
    - Rydberg decay (excited state decays)
    - Detection errors (imperfect state readout)
    """
    atom_loss_rate: float = 0.01  # probability of atom loss per gate
    dephasing_rate: float = 0.005  # Z-error probability per gate
    rydberg_decay_rate: float = 0.003  # Rydberg state decay probability
    detection_error: float = 0.02  # readout error per qubit
    gate_time_1q: float = 0.5  # microseconds
    gate_time_2q: float = 1.0  # microseconds (CZ via Rydberg)
    coherence_time: float = 100.0  # microseconds (T2)
    trapping_fidelity: float = 0.99  # initial trapping fidelity

    def apply_to_counts(
        self,
        counts: Dict[str, int],
        num_qubits: int,
    ) -> Dict[str, int]:
        """Apply noise model to measurement counts."""
        noisy: Dict[str, int] = {}
        for bitstring, count in counts.items():
            for _ in range(count):
                noisy_bits = list(bitstring)
                for i in range(num_qubits):
                    # Atom loss → random result
                    if np.random.random() < self.atom_loss_rate:
                        noisy_bits[i] = np.random.choice(["0", "1"])
                    # Detection error
                    elif np.random.random() < self.detection_error:
                        noisy_bits[i] = "1" if noisy_bits[i] == "0" else "0"
                key = "".join(noisy_bits)
                noisy[key] = noisy.get(key, 0) + 1
        return noisy


def get_fresnel_noise_profile() -> NeutralAtomNoiseProfile:
    """Pre-configured noise profile for Pasqal Fresnel (100 atoms)."""
    return NeutralAtomNoiseProfile(
        atom_loss_rate=0.01,
        dephasing_rate=0.005,
        rydberg_decay_rate=0.003,
        detection_error=0.02,
        gate_time_1q=0.5,
        gate_time_2q=1.0,
        coherence_time=100.0,
        trapping_fidelity=0.99,
    )


def get_eileen_noise_profile() -> NeutralAtomNoiseProfile:
    """Pre-configured noise profile for Pasqal Eileen (200 atoms)."""
    return NeutralAtomNoiseProfile(
        atom_loss_rate=0.015,
        dephasing_rate=0.008,
        rydberg_decay_rate=0.005,
        detection_error=0.025,
        gate_time_1q=0.5,
        gate_time_2q=1.0,
        coherence_time=80.0,
        trapping_fidelity=0.985,
    )


def get_aquila_noise_profile() -> NeutralAtomNoiseProfile:
    """Pre-configured noise profile for QuEra Aquila (256 atoms)."""
    return NeutralAtomNoiseProfile(
        atom_loss_rate=0.02,
        dephasing_rate=0.01,
        rydberg_decay_rate=0.008,
        detection_error=0.03,
        gate_time_1q=0.5,
        gate_time_2q=1.5,
        coherence_time=60.0,
        trapping_fidelity=0.98,
    )
