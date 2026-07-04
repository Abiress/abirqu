"""
Continuous-Variable Quantum Key Distribution (CV-QKD)
Copyright 2026 Abir Maheshwari

CV-QKD uses continuous variables (quadratures X and P) instead of
discrete qubit states. Higher key rates over short distances.

Gaussian-modulated coherent state protocol (GG02).
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CVQKDResult:
    """Result of CV-QKD protocol."""
    alice_symbols: List[Tuple[float, float]]  # (x, p) quadratures
    bob_symbols: List[Tuple[float, float]]
    excess_noise: float
    channel_transmittance: float
    mutual_information: float
    secret_key_rate: float
    final_key: Optional[List[int]] = None


class CVQKDProtocol:
    """
    Continuous-Variable QKD Protocol (GG02).

    Uses Gaussian-modulated coherent states.

    Usage:
        cvqkd = CVQKDProtocol(num_symbols=1024, modulation_variance=4.0)
        result = cvqkd.run()
        print(f"Key rate: {result.secret_key_rate:.3f} bits/symbol")
    """

    def __init__(self, num_symbols: int = 1024,
                 modulation_variance: float = 4.0,
                 excess_noise: float = 0.1,
                 transmittance: float = 0.5,
                 electronic_noise: float = 0.01,
                 seed: Optional[int] = None):
        self.num_symbols = num_symbols
        self.modulation_variance = modulation_variance
        self.excess_noise = excess_noise
        self.transmittance = transmittance
        self.electronic_noise = electronic_noise
        self.rng = np.random.default_rng(seed)

    def run(self) -> CVQKDResult:
        """Execute CV-QKD protocol."""
        # Step 1: Alice generates Gaussian random symbols
        alice_symbols = self._generate_symbols()

        # Step 2: Alice encodes on coherent states
        encoded_states = self._encode(alice_symbols)

        # Step 3: Channel transmission
        received_states = self._channel(encoded_states)

        # Step 4: Bob measures (homodyne/heterodyne)
        bob_symbols = self._measure(received_states)

        # Step 5: Parameter estimation
        mutual_info = self._compute_mutual_info(alice_symbols, bob_symbols)

        # Step 6: Secret key rate
        key_rate = self._compute_key_rate(mutual_info)

        # Step 7: Error correction and privacy amplification
        final_key = self._post_process(alice_symbols, bob_symbols, key_rate)

        return CVQKDResult(
            alice_symbols=alice_symbols,
            bob_symbols=bob_symbols,
            excess_noise=self.excess_noise,
            channel_transmittance=self.transmittance,
            mutual_information=mutual_info,
            secret_key_rate=key_rate,
            final_key=final_key,
        )

    def _generate_symbols(self) -> List[Tuple[float, float]]:
        """Alice generates Gaussian random (x, p) pairs."""
        symbols = []
        for _ in range(self.num_symbols):
            x = self.rng.normal(0, np.sqrt(self.modulation_variance))
            p = self.rng.normal(0, np.sqrt(self.modulation_variance))
            symbols.append((x, p))
        return symbols

    def _encode(self, symbols: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Encode symbols on coherent states."""
        return symbols

    def _channel(self, states: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Simulate channel with loss and noise."""
        received = []
        for x, p in states:
            # Loss
            x_received = np.sqrt(self.transmittance) * x
            p_received = np.sqrt(self.transmittance) * p

            # Excess noise
            x_received += self.rng.normal(0, np.sqrt(self.excess_noise))
            p_received += self.rng.normal(0, np.sqrt(self.excess_noise))

            # Electronic noise
            x_received += self.rng.normal(0, np.sqrt(self.electronic_noise))
            p_received += self.rng.normal(0, np.sqrt(self.electronic_noise))

            received.append((x_received, p_received))
        return received

    def _measure(self, states: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Bob measures quadratures."""
        return states

    def _compute_mutual_info(self, alice: List[Tuple[float, float]],
                              bob: List[Tuple[float, float]]) -> float:
        """Compute mutual information I(A:B)."""
        if len(alice) == 0:
            return 0.0

        # Compute variances
        alice_x = [s[0] for s in alice]
        bob_x = [s[0] for s in bob]

        var_alice = np.var(alice_x)
        var_bob = np.var(bob_x)

        # Covariance
        cov = np.mean([(a - np.mean(alice_x)) * (b - np.mean(bob_x))
                       for a, b in zip(alice_x, bob_x)])

        # Mutual information (simplified)
        if var_alice > 0 and var_bob > 0:
            rho_sq = cov**2 / (var_alice * var_bob)
            if rho_sq < 1:
                mi = -0.5 * np.log2(1 - rho_sq)
            else:
                mi = 0.0
        else:
            mi = 0.0

        return mi

    def _compute_key_rate(self, mutual_info: float) -> float:
        """Compute secret key rate."""
        # Simplified key rate formula
        # Real implementation uses更 complex Holevo bound calculations
        noise_factor = self.excess_noise / self.transmittance
        key_rate = max(0, mutual_info - noise_factor)
        return key_rate

    def _post_process(self, alice, bob, key_rate) -> Optional[List[int]]:
        """Error correction and privacy amplification."""
        if key_rate <= 0 or len(alice) == 0:
            return None

        # Simple key extraction from x quadratures
        key = []
        threshold = np.mean([s[0] for s in alice])
        for a, b in zip(alice, bob):
            if abs(a[0] - b[0]) < 0.5:  # Error correction threshold
                key.append(1 if a[0] > threshold else 0)

        # Privacy amplification
        key = key[::2]
        return key if len(key) > 0 else None


class GaussianModulation:
    """Gaussian modulation utilities for CV-QKD."""

    def __init__(self, variance: float = 4.0, seed: Optional[int] = None):
        self.variance = variance
        self.rng = np.random.default_rng(seed)

    def generate_symbols(self, n: int) -> List[Tuple[float, float]]:
        """Generate n Gaussian random symbols."""
        symbols = []
        for _ in range(n):
            x = self.rng.normal(0, np.sqrt(self.variance))
            p = self.rng.normal(0, np.sqrt(self.variance))
            symbols.append((x, p))
        return symbols

    def estimate_variance(self, symbols: List[Tuple[float, float]]) -> float:
        """Estimate modulation variance from symbols."""
        x_vals = [s[0] for s in symbols]
        p_vals = [s[1] for s in symbols]
        return (np.var(x_vals) + np.var(p_vals)) / 2
