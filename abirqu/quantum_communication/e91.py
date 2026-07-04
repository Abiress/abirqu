"""
E91 Quantum Key Distribution Protocol
Copyright 2026 Abir Maheshwari

The E91 protocol (Ekert, 1991) uses entangled photon pairs and
Bell's inequality to detect eavesdropping.

Protocol:
1. Source creates entangled pairs |Φ+⟩ = (|00⟩ + |11⟩)/√2
2. Alice and Bob each receive one photon
3. They measure in random bases
4. Use Bell's inequality (CHSH) to detect eavesdropping
5. Extract key from correlated measurements

Security: Based on quantum entanglement and Bell's theorem.
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MeasurementBasis(Enum):
    """Measurement bases for E91."""
    A1 = 0      # Alice's first basis (0°)
    A2 = 45     # Alice's second basis (45°)
    A3 = 90     # Alice's third basis (90°)
    B1 = 22.5   # Bob's first basis (22.5°)
    B2 = 0      # Bob's second basis (0°)
    B3 = 67.5   # Bob's third basis (67.5°)


@dataclass
class E91Result:
    """Result of E91 protocol execution."""
    alice_bases: List[MeasurementBasis]
    bob_bases: List[MeasurementBasis]
    alice_results: List[int]
    bob_results: List[int]
    bell_violation: float
    sifted_key_alice: List[int]
    sifted_key_bob: List[int]
    error_rate: float
    final_key: Optional[List[int]] = None
    eavesdropper_detected: bool = False


class E91Protocol:
    """
    E91 Quantum Key Distribution Protocol.

    Usage:
        e91 = E91Protocol(num_pairs=1024)
        result = e91.run()
        print(f"Bell violation: {result.bell_violation:.3f}")
        print(f"Secure: {not result.eavesdropper_detected}")
    """

    def __init__(self, num_pairs: int = 1024, eavesdrop: bool = False,
                 seed: Optional[int] = None):
        self.num_pairs = num_pairs
        self.eavesdrop = eavesdrop
        self.rng = np.random.default_rng(seed)

    def run(self) -> E91Result:
        """Execute the E91 protocol."""
        # Step 1: Generate entangled pairs
        alice_bases = self._random_bases(alice=True)
        bob_bases = self._random_bases(alice=False)

        # Step 2: Measure entangled pairs
        alice_results, bob_results = self._measure_entangled_pairs(
            alice_bases, bob_bases
        )

        # Step 3: Bell inequality test
        bell_violation = self._compute_bell_inequality(
            alice_bases, bob_bases, alice_results, bob_results
        )

        # Step 4: Eavesdropping detection
        eavesdropper_detected = bell_violation <= 2.0  # Classical limit

        # Step 5: Key extraction from A1-B1 measurements
        sifted_alice, sifted_bob = self._extract_key(
            alice_bases, bob_bases, alice_results, bob_results
        )

        # Step 6: Error estimation
        error_rate = self._estimate_error(sifted_alice, sifted_bob)

        # Step 7: Privacy amplification
        final_key = None
        if not eavesdropper_detected and len(sifted_alice) > 0:
            final_key = self._privacy_amplify(sifted_alice)

        return E91Result(
            alice_bases=alice_bases,
            bob_bases=bob_bases,
            alice_results=alice_results,
            bob_results=bob_results,
            bell_violation=bell_violation,
            sifted_key_alice=sifted_alice,
            sifted_key_bob=sifted_bob,
            error_rate=error_rate,
            final_key=final_key,
            eavesdropper_detected=eavesdropper_detected,
        )

    def _random_bases(self, alice: bool = True) -> List[MeasurementBasis]:
        """Generate random measurement bases."""
        if alice:
            bases_list = [MeasurementBasis.A1, MeasurementBasis.A2, MeasurementBasis.A3]
        else:
            bases_list = [MeasurementBasis.B1, MeasurementBasis.B2, MeasurementBasis.B3]
        return [self.rng.choice(bases_list) for _ in range(self.num_pairs)]

    def _measure_entangled_pairs(self, alice_bases, bob_bases):
        """Simulate measurement of entangled pairs."""
        alice_results = []
        bob_results = []

        for i in range(self.num_pairs):
            # For |Φ+⟩ = (|00⟩ + |11⟩)/√2, the correlation is cos(2*theta)
            # where theta is the angle between measurement bases
            a_angle = math.radians(alice_bases[i].value)
            b_angle = math.radians(bob_bases[i].value)
            angle_diff = abs(a_angle - b_angle)

            # Quantum probability: P(same outcome) = cos²(θ)
            # where θ is the angle between measurement bases
            correlation = math.cos(angle_diff) ** 2

            alice_bit = self.rng.integers(0, 2)

            # Bob's result correlates with Alice's based on angle difference
            if self.rng.random() < correlation:
                bob_bit = alice_bit  # Same outcome
            else:
                bob_bit = 1 - alice_bit  # Different outcome

            if self.eavesdrop and self.rng.random() < 0.1:
                bob_bit = 1 - bob_bit

            alice_results.append(alice_bit)
            bob_results.append(bob_bit)

        return alice_results, bob_results

    def _compute_bell_inequality(self, alice_bases, bob_bases,
                                  alice_results, bob_results) -> float:
        """
        Compute CHSH Bell inequality parameter S.

        S = |E(A1,B1) - E(A1,B3) + E(A3,B1) + E(A3,B3)|

        Classical limit: S ≤ 2
        Quantum maximum: S = 2√2 ≈ 2.828
        """
        # Compute correlations for specific basis combinations
        # CHSH: S = E(A1,B1) - E(A1,B3) + E(A2,B1) + E(A2,B3)
        correlations = {}
        for a_basis, b_basis in [
            (MeasurementBasis.A1, MeasurementBasis.B1),
            (MeasurementBasis.A1, MeasurementBasis.B3),
            (MeasurementBasis.A2, MeasurementBasis.B1),
            (MeasurementBasis.A2, MeasurementBasis.B3),
        ]:
            # Find pairs with these bases
            pairs = [(a, b) for a, ab, b, bb in
                     zip(range(self.num_pairs), alice_bases,
                         bob_results, bob_bases)
                     if ab == a_basis and bb == b_basis]

            if pairs:
                # Compute correlation using bipolar values (-1)^a * (-1)^b = (-1)^(a+b)
                a_vals = [alice_results[p[0]] for p in pairs]
                b_vals = [bob_results[p[0]] for p in pairs]
                correlation = np.mean([(-1)**(a + b) for a, b in zip(a_vals, b_vals)])
                correlations[(a_basis, b_basis)] = correlation
            else:
                correlations[(a_basis, b_basis)] = 0.0

        # CHSH parameter: S = E(A1,B1) - E(A1,B3) + E(A2,B1) + E(A2,B3)
        S = abs(
            correlations.get((MeasurementBasis.A1, MeasurementBasis.B1), 0) -
            correlations.get((MeasurementBasis.A1, MeasurementBasis.B3), 0) +
            correlations.get((MeasurementBasis.A2, MeasurementBasis.B1), 0) +
            correlations.get((MeasurementBasis.A2, MeasurementBasis.B3), 0)
        )

        return S

    def _extract_key(self, alice_bases, bob_bases, alice_results, bob_results):
        """Extract key from A1-B1 measurements."""
        sifted_alice = []
        sifted_bob = []

        for i in range(self.num_pairs):
            if (alice_bases[i] == MeasurementBasis.A1 and
                bob_bases[i] == MeasurementBasis.B1):
                sifted_alice.append(alice_results[i])
                sifted_bob.append(bob_results[i])

        return sifted_alice, sifted_bob

    def _estimate_error(self, sifted_alice, sifted_bob) -> float:
        """Estimate error rate in sifted key."""
        if len(sifted_alice) == 0:
            return 0.0
        errors = sum(a != b for a, b in zip(sifted_alice, sifted_bob))
        return errors / len(sifted_alice)

    def _privacy_amplify(self, key: List[int]) -> List[int]:
        """Privacy amplification."""
        if len(key) == 0:
            return []
        return key[::2]


class E91Simulator:
    """
    Simulate E91 over long-distance links.

    Usage:
        sim = E91Simulator(distance_km=100)
        result = sim.simulate(num_pairs=1024)
    """

    def __init__(self, distance_km: float = 100.0,
                 fiber_loss_db_km: float = 0.2,
                 detector_efficiency: float = 0.9,
                 entanglement_fidelity: float = 0.95,
                 seed: Optional[int] = None):
        self.distance_km = distance_km
        self.fiber_loss_db_km = fiber_loss_db_km
        self.detector_efficiency = detector_efficiency
        self.entanglement_fidelity = entanglement_fidelity
        self.rng = np.random.default_rng(seed)

    def simulate(self, num_pairs: int = 1024) -> Dict[str, Any]:
        """Simulate E91 with realistic parameters."""
        # Channel transmission
        total_loss_db = self.fiber_loss_db_km * self.distance_km
        channel_transmission = 10 ** (-total_loss_db / 10)

        # Surviving pairs
        surviving_pairs = int(num_pairs * channel_transmission * self.detector_efficiency)

        # Bell violation with imperfect entanglement
        ideal_violation = 2 * np.sqrt(2)
        actual_violation = 2 + (ideal_violation - 2) * self.entanglement_fidelity

        # Secure if violation > 2
        secure = actual_violation > 2.0

        # Key rate
        if secure:
            h = 0.5  # Simplified
            key_rate = max(0, 1 - h)
        else:
            key_rate = 0

        return {
            'distance_km': self.distance_km,
            'channel_transmission': channel_transmission,
            'surviving_pairs': surviving_pairs,
            'bell_violation': actual_violation,
            'key_rate': key_rate,
            'final_key_length': int(surviving_pairs * key_rate),
            'secure': secure,
        }
