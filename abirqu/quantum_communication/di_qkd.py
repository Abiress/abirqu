"""
Device-Independent Quantum Key Distribution (DI-QKD)
Copyright 2026 Abir Maheshwari

DI-QKD doesn't trust the quantum devices. Security is based on
Bell inequality violation alone.

Most secure form of QKD - even if devices are compromised.
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class DIQKDResult:
    """Result of DI-QKD protocol."""
    bell_violation: float
    chsh_parameter: float
    key_rate: float
    error_rate: float
    secure: bool
    final_key: Optional[List[int]] = None


class DIQKDProtocol:
    """
    Device-Independent QKD Protocol.

    Security based only on Bell inequality violation.

    Usage:
        diqkd = DIQKDProtocol(num_rounds=1024)
        result = diqkd.run()
        print(f"Bell violation: {result.chsh_parameter:.3f}")
        print(f"Secure: {result.secure}")
    """

    def __init__(self, num_rounds: int = 1024,
                 noise_level: float = 0.05,
                 detection_efficiency: float = 0.95,
                 seed: Optional[int] = None):
        self.num_rounds = num_rounds
        self.noise_level = noise_level
        self.detection_efficiency = detection_efficiency
        self.rng = np.random.default_rng(seed)

    def run(self) -> DIQKDResult:
        """Execute DI-QKD protocol."""
        # Step 1: Generate Bell pairs
        # Step 2: Alice and Bob measure in random bases
        alice_inputs = self.rng.integers(0, 3, size=self.num_rounds)
        bob_inputs = self.rng.integers(0, 3, size=self.num_rounds)

        # Step 3: Simulate measurements with noise
        alice_outputs = []
        bob_outputs = []

        # CHSH measurement angles: indices 0,2 used in CHSH combination
        # S = E(0,0) - E(0,2) + E(2,0) + E(2,2)
        # For max S = 2√2: need θ(0,0)=22.5°, θ(0,2)=67.5°, θ(2,0)=22.5°, θ(2,2)=22.5°
        alice_angles = [0, 90, 45]  # degrees
        bob_angles = [22.5, 45, 67.5]  # degrees

        for i in range(self.num_rounds):
            a_idx = alice_inputs[i] % 3
            b_idx = bob_inputs[i] % 3

            a_angle = math.radians(alice_angles[a_idx])
            b_angle = math.radians(bob_angles[b_idx])

            # For Bell state |Φ+⟩, P(same) = cos²(θ)
            angle_diff = abs(a_angle - b_angle)
            correlation = math.cos(angle_diff) ** 2

            a = self.rng.integers(0, 2)

            # Bob's result correlates based on quantum mechanics
            if self.rng.random() < correlation:
                b = a
            else:
                b = 1 - a

            # Add noise
            if self.rng.random() < self.noise_level:
                b = 1 - b

            # Detection loss
            if self.rng.random() > self.detection_efficiency:
                a = -1
                b = -1

            alice_outputs.append(a)
            bob_outputs.append(b)

        # Step 4: Compute CHSH parameter
        chsh = self._compute_chsh(alice_inputs, bob_inputs,
                                   alice_outputs, bob_outputs)

        # Step 5: Security analysis
        secure = chsh > 2.0 and self.detection_efficiency > 0.828

        # Step 6: Key extraction
        error_rate = self._compute_error_rate(alice_outputs, bob_outputs)

        key_rate = 0.0
        final_key = None
        if secure:
            key_rate = max(0, 1 - self._binary_entropy(error_rate))
            # Extract key from X=0, Y=0 outcomes
            final_key = self._extract_key(alice_inputs, bob_inputs,
                                           alice_outputs, bob_outputs)

        return DIQKDResult(
            bell_violation=chsh,
            chsh_parameter=chsh,
            key_rate=key_rate,
            error_rate=error_rate,
            secure=secure,
            final_key=final_key,
        )

    def _compute_chsh(self, alice_inputs, bob_inputs,
                       alice_outputs, bob_outputs) -> float:
        """Compute CHSH Bell inequality parameter."""
        # Filter valid detections
        valid = [(a, b, ai, bi) for a, b, ai, bi in
                 zip(alice_outputs, bob_outputs, alice_inputs, bob_inputs)
                 if a >= 0 and b >= 0]

        if len(valid) == 0:
            return 0.0

        # Compute correlations for each input combination
        correlations = {}
        for x in range(3):
            for y in range(3):
                pairs = [(a, b) for a, b, ai, bi in valid if ai == x and bi == y]
                if pairs:
                    corr = np.mean([(-1)**(a + b) for a, b in pairs])
                    correlations[(x, y)] = corr
                else:
                    correlations[(x, y)] = 0.0

        # CHSH: S = |E(0,0) - E(0,2) + E(2,0) + E(2,2)|
        S = abs(
            correlations.get((0, 0), 0) -
            correlations.get((0, 2), 0) +
            correlations.get((2, 0), 0) +
            correlations.get((2, 2), 0)
        )

        return S

    def _compute_error_rate(self, alice_outputs, bob_outputs) -> float:
        """Compute error rate."""
        valid = [(a, b) for a, b in zip(alice_outputs, bob_outputs)
                 if a >= 0 and b >= 0]
        if len(valid) == 0:
            return 0.0
        errors = sum(a != b for a, b in valid)
        return errors / len(valid)

    def _extract_key(self, alice_inputs, bob_inputs,
                      alice_outputs, bob_outputs) -> List[int]:
        """Extract key from specific input combinations."""
        key = []
        for a, b, ai, bi in zip(alice_outputs, bob_outputs,
                                  alice_inputs, bob_inputs):
            if ai == 0 and bi == 0 and a >= 0:
                key.append(a)
        return key[::2]  # Privacy amplification

    def _binary_entropy(self, p: float) -> float:
        """Binary entropy function."""
        if p <= 0 or p >= 1:
            return 0.0
        return -p * np.log2(p) - (1 - p) * np.log2(1 - p)


class BellTest:
    """Bell inequality testing utilities."""

    @staticmethod
    def chsh_inequality(correlations: Dict[Tuple[int, int], float]) -> float:
        """Compute CHSH parameter from correlations."""
        S = abs(
            correlations.get((0, 0), 0) -
            correlations.get((0, 1), 0) +
            correlations.get((1, 0), 0) +
            correlations.get((1, 1), 0)
        )
        return S

    @staticmethod
    def is_violated(chsh: float) -> bool:
        """Check if CHSH inequality is violated."""
        return chsh > 2.0

    @staticmethod
    def quantum_bound() -> float:
        """Maximum quantum violation (Tsirelson bound)."""
        return 2 * np.sqrt(2)
