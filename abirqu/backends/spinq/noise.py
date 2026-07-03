"""
SpinQ Noise Profile
===================
Noise models for SpinQ trapped-ion processors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np


@dataclass
class SpinQNoiseProfile:
    """Noise profile for a SpinQ trapped-ion processor.

    Trapped-ion characteristics:
    - Long coherence times (T1 ~ 10s, T2 ~ 1s)
    - High gate fidelity (>99.5% single-qubit, >99% two-qubit)
    - All-to-all connectivity within chain
    """
    t1: Dict[int, float] = field(default_factory=dict)  # seconds
    t2: Dict[int, float] = field(default_factory=dict)  # seconds
    gate_error_1q: Dict[int, float] = field(default_factory=dict)
    gate_error_2q: Dict = field(default_factory=dict)
    readout_error: Dict[int, float] = field(default_factory=dict)
    gate_time_1q: float = 10.0  # microseconds
    gate_time_2q: float = 100.0  # microseconds
    ms_gate_time: float = 200.0  # microseconds (Molmer-Sorensen)

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
                    readout_err = self.readout_error.get(i, 0.005)
                    if np.random.random() < readout_err:
                        noisy_bits[i] = "1" if noisy_bits[i] == "0" else "0"
                key = "".join(noisy_bits)
                noisy[key] = noisy.get(key, 0) + 1
        return noisy


def get_spinq3_noise_profile() -> SpinQNoiseProfile:
    """Pre-configured noise profile for SpinQ-3 (3 qubits)."""
    return SpinQNoiseProfile(
        t1={i: 10.0 + np.random.uniform(-1, 1) for i in range(3)},
        t2={i: 1.0 + np.random.uniform(-0.1, 0.1) for i in range(3)},
        gate_error_1q={i: 0.0005 + np.random.uniform(0, 0.0002) for i in range(3)},
        gate_error_2q={
            (0, 1): 0.008, (1, 0): 0.008,
            (1, 2): 0.009, (2, 1): 0.009,
            (0, 2): 0.012, (2, 0): 0.012,
        },
        readout_error={i: 0.005 + np.random.uniform(0, 0.005) for i in range(3)},
        gate_time_1q=10.0,
        gate_time_2q=100.0,
        ms_gate_time=200.0,
    )


def get_spinq6_noise_profile() -> SpinQNoiseProfile:
    """Pre-configured noise profile for SpinQ-6 (6 qubits)."""
    return SpinQNoiseProfile(
        t1={i: 10.0 + np.random.uniform(-1, 1) for i in range(6)},
        t2={i: 1.0 + np.random.uniform(-0.1, 0.1) for i in range(6)},
        gate_error_1q={i: 0.0005 + np.random.uniform(0, 0.0003) for i in range(6)},
        gate_error_2q={
            (i, j): 0.01 + abs(i - j) * 0.002
            for i in range(6) for j in range(i + 1, 6)
        },
        readout_error={i: 0.005 + np.random.uniform(0, 0.005) for i in range(6)},
        gate_time_1q=10.0,
        gate_time_2q=100.0,
        ms_gate_time=200.0,
    )
