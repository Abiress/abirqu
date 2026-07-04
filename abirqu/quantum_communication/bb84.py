"""
BB84 Quantum Key Distribution Protocol
Copyright 2026 Abir Maheshwari

The BB84 protocol (Bennett & Brassard, 1984) was the first QKD protocol.
It uses 4 states in 2 conjugate bases (rectilinear and diagonal).

Protocol:
1. Alice prepares qubits in random states from { |0⟩, |1⟩, |+⟩, |−⟩ }
2. Bob measures in random bases { Z, X }
3. They publicly compare bases (not results)
4. Keep only matching-basis results as key
5. Estimate eavesdropping via error rate

Security: Eavesdropping introduces ~25% error rate on intercepted bits.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class Basis(Enum):
    """Measurement bases."""
    Z = "Z"  # Rectilinear: |0⟩, |1⟩
    X = "X"  # Diagonal: |+⟩, |−⟩


@dataclass
class BB84Result:
    """Result of BB84 protocol execution."""
    raw_key_alice: List[int]
    raw_key_bob: List[int]
    basis_alice: List[Basis]
    basis_bob: List[Basis]
    sifted_key_alice: List[int]
    sifted_key_bob: List[int]
    error_rate: float
    final_key: Optional[List[int]] = None
    eavesdropper_detected: bool = False
    qber_threshold: float = 0.11


class BB84Protocol:
    """
    BB84 Quantum Key Distribution Protocol.

    Usage:
        bb84 = BB84Protocol(num_bits=1024, eavesdrop=False)
        result = bb84.run()
        if not result.eavesdropper_detected:
            print(f"Secure key: {result.final_key}")
    """

    def __init__(self, num_bits: int = 1024, eavesdrop: bool = False,
                 eve_basis: Basis = Basis.Z, seed: Optional[int] = None):
        self.num_bits = num_bits
        self.eavesdrop = eavesdrop
        self.eve_basis = eve_basis
        self.rng = np.random.default_rng(seed)

    def run(self) -> BB84Result:
        """Execute the BB84 protocol."""
        # Step 1: Alice prepares qubits
        alice_bits, alice_bases = self._prepare_qubits()

        # Step 2: Send through quantum channel (with optional eavesdropping)
        received_bits = self._quantum_channel(alice_bits, alice_bases)

        # Step 3: Bob measures
        bob_bases = self._random_bases()
        bob_bits = self._measure(received_bits, bob_bases)

        # Step 4: Sifting (compare bases publicly)
        sifted_alice, sifted_bob = self._sift_keys(
            alice_bits, bob_bits, alice_bases, bob_bases
        )

        # Step 5: Error estimation
        error_rate = self._estimate_error(sifted_alice, sifted_bob)

        # Step 6: Eavesdropping detection
        eavesdropper_detected = error_rate > 0.11  # ~11% threshold

        # Step 7: Privacy amplification (if secure)
        final_key = None
        if not eavesdropper_detected and len(sifted_alice) > 0:
            final_key = self._privacy_amplify(sifted_alice)

        return BB84Result(
            raw_key_alice=alice_bits,
            raw_key_bob=bob_bits,
            basis_alice=alice_bases,
            basis_bob=bob_bases,
            sifted_key_alice=sifted_alice,
            sifted_key_bob=sifted_bob,
            error_rate=error_rate,
            final_key=final_key,
            eavesdropper_detected=eavesdropper_detected,
        )

    def _prepare_qubits(self) -> Tuple[List[int], List[Basis]]:
        """Alice prepares random bits in random bases."""
        bits = self.rng.integers(0, 2, size=self.num_bits).tolist()
        bases = self._random_bases()
        return bits, bases

    def _random_bases(self) -> List[Basis]:
        """Generate random basis choices."""
        return [Basis.Z if b else Basis.X
                for b in self.rng.integers(0, 2, size=self.num_bits)]

    def _quantum_channel(self, bits: List[int], bases: List[Basis]) -> List[int]:
        """Simulate quantum channel with optional eavesdropping."""
        received = bits.copy()

        if self.eavesdrop:
            eve_bases = self._random_bases()
            for i in range(len(bits)):
                # Eve intercepts and measures
                if eve_bases[i] == bases[i]:
                    # Same basis: no error
                    pass
                else:
                    # Different basis: 50% chance of error
                    if self.rng.random() < 0.5:
                        received[i] = 1 - received[i]

        return received

    def _measure(self, bits: List[int], bases: List[Basis]) -> List[int]:
        """Bob measures qubits in his chosen bases."""
        return bits.copy()

    def _sift_keys(self, alice_bits, bob_bits, alice_bases, bob_bases):
        """Keep only bits where bases match."""
        sifted_alice = []
        sifted_bob = []
        for i in range(len(alice_bits)):
            if alice_bases[i] == bob_bases[i]:
                sifted_alice.append(alice_bits[i])
                sifted_bob.append(bob_bits[i])
        return sifted_alice, sifted_bob

    def _estimate_error(self, sifted_alice: List[int], sifted_bob: List[int]) -> float:
        """Estimate quantum bit error rate (QBER)."""
        if len(sifted_alice) == 0:
            return 0.0
        errors = sum(a != b for a, b in zip(sifted_alice, sifted_bob))
        return errors / len(sifted_alice)

    def _privacy_amplify(self, key: List[int]) -> List[int]:
        """Privacy amplification using hash compression."""
        if len(key) == 0:
            return []
        # Simple: take every other bit (real implementation uses universal hashing)
        return key[::2]


class BB84Simulator:
    """
    Simulate BB84 over noisy channels.

    Usage:
        sim = BB84Simulator(distance_km=100, fiber_loss_db_km=0.2)
        result = sim.simulate(num_bits=1024)
        print(f"Secret key rate: {result['key_rate']:.2f} bits/pulse")
    """

    def __init__(self, distance_km: float = 100.0,
                 fiber_loss_db_km: float = 0.2,
                 detector_efficiency: float = 0.9,
                 dark_count_rate: float = 1e-6,
                 misalignment: float = 0.01,
                 seed: Optional[int] = None):
        self.distance_km = distance_km
        self.fiber_loss_db_km = fiber_loss_db_km
        self.detector_efficiency = detector_efficiency
        self.dark_count_rate = dark_count_rate
        self.misalignment = misalignment
        self.rng = np.random.default_rng(seed)

    def simulate(self, num_bits: int = 1024) -> Dict[str, Any]:
        """Simulate BB84 with realistic parameters."""
        # Channel transmission
        total_loss_db = self.fiber_loss_db_km * self.distance_km
        channel_transmission = 10 ** (-total_loss_db / 10)

        # Surviving pulses
        surviving_pulses = int(num_bits * channel_transmission * self.detector_efficiency)

        # Error sources
        misalignment_errors = self.misalignment
        dark_count_errors = self.dark_count_rate * 1e6  # Normalize
        total_error_rate = misalignment_errors + dark_count_errors

        # Secure key generation
        if total_error_rate < 0.11:
            # Privacy amplification factor
            h = self._binary_entropy(total_error_rate)
            key_rate = max(0, 1 - 2 * h)
            final_key_length = int(surviving_pulses * key_rate)
        else:
            key_rate = 0
            final_key_length = 0

        return {
            'distance_km': self.distance_km,
            'channel_transmission': channel_transmission,
            'surviving_pulses': surviving_pulses,
            'error_rate': total_error_rate,
            'key_rate': key_rate,
            'final_key_length': final_key_length,
            'secure': total_error_rate < 0.11,
        }

    def _binary_entropy(self, p: float) -> float:
        """Binary entropy function H(p)."""
        if p <= 0 or p >= 1:
            return 0.0
        return -p * np.log2(p) - (1 - p) * np.log2(1 - p)

    def key_rate_vs_distance(self, distances: List[float]) -> Dict[str, List[float]]:
        """Compute key rate as a function of distance."""
        rates = []
        for d in distances:
            sim = BB84Simulator(
                distance_km=d,
                fiber_loss_db_km=self.fiber_loss_db_km,
                detector_efficiency=self.detector_efficiency,
                dark_count_rate=self.dark_count_rate,
            )
            result = sim.simulate(num_bits=1024)
            rates.append(result['key_rate'])
        return {'distances': distances, 'key_rates': rates}
