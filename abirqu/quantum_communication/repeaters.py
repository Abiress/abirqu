"""
Quantum Repeaters
Copyright 2026 Abir Maheshwari

Quantum repeaters extend QKD range beyond direct transmission limits.
Uses entanglement swapping and purification.

Key concept: Divide long channel into shorter segments,
create entanglement locally, then swap.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class RepeaterSegment:
    """Parameters for a single repeater segment."""
    distance_km: float
    memory_coherence_time_s: float = 1.0
    entanglement_generation_rate: float = 1000.0
    swap_success_probability: float = 0.5
    purification_fidelity: float = 0.95


@dataclass
class RepeaterChain:
    """Chain of quantum repeaters."""
    num_segments: int
    segment_distance_km: float
    total_distance_km: float
    segments: List[RepeaterSegment]


@dataclass
class QuantumRepeaterResult:
    """Result of quantum repeater simulation."""
    total_distance_km: float
    num_segments: int
    end_to_end_fidelity: float
    key_rate: float
    key_length: int
    latency_ms: float
    segment_fidelities: List[float]


class QuantumRepeater:
    """
    Quantum Repeater Simulator.

    Simulates entanglement distribution via repeater chains.

    Usage:
        repeater = QuantumRepeater(total_distance_km=1000, num_segments=10)
        result = repeater.simulate()
        print(f"Fidelity: {result.end_to_end_fidelity:.3f}")
        print(f"Key rate: {result.key_rate:.2f} bits/s")
    """

    def __init__(self, total_distance_km: float = 1000.0,
                 num_segments: int = 10,
                 memory_coherence_time_s: float = 1.0,
                 entanglement_rate: float = 1000.0,
                 swap_success: float = 0.5,
                 purification_rounds: int = 1,
                 fiber_loss_db_km: float = 0.2,
                 seed: Optional[int] = None):
        self.total_distance_km = total_distance_km
        self.num_segments = num_segments
        self.memory_coherence_time_s = memory_coherence_time_s
        self.entanglement_rate = entanglement_rate
        self.swap_success = swap_success
        self.purification_rounds = purification_rounds
        self.fiber_loss_db_km = fiber_loss_db_km
        self.rng = np.random.default_rng(seed)

        # Build repeater chain
        self.segment_distance = total_distance_km / num_segments
        self.chain = self._build_chain()

    def _build_chain(self) -> RepeaterChain:
        """Build repeater chain."""
        segments = []
        for _ in range(self.num_segments):
            segment = RepeaterSegment(
                distance_km=self.segment_distance,
                memory_coherence_time_s=self.memory_coherence_time_s,
                entanglement_generation_rate=self.entanglement_rate,
                swap_success_probability=self.swap_success,
            )
            segments.append(segment)

        return RepeaterChain(
            num_segments=self.num_segments,
            segment_distance_km=self.segment_distance,
            total_distance_km=self.total_distance_km,
            segments=segments,
        )

    def simulate(self, num_pairs: int = 1000) -> QuantumRepeaterResult:
        """Simulate repeater chain operation."""
        # Step 1: Generate entanglement in each segment
        segment_fidelities = []
        segment_success_rates = []

        for segment in self.chain.segments:
            # Entanglement generation fidelity
            fidelity = self._generate_entanglement(segment)
            segment_fidelities.append(fidelity)

            # Success rate based on distance
            loss_db = self.fiber_loss_db_km * segment.distance_km
            success_rate = 10 ** (-loss_db / 10) * segment.entanglement_generation_rate
            segment_success_rates.append(success_rate)

        # Step 2: Entanglement swapping
        end_to_end_fidelity = self._swap_entanglement(segment_fidelities)

        # Step 3: Purification (optional)
        if self.purification_rounds > 0:
            end_to_end_fidelity = self._purify(end_to_end_fidelity)

        # Step 4: Key rate estimation
        min_success_rate = min(segment_success_rates) if segment_success_rates else 0
        swap_success_total = self.swap_success ** (self.num_segments - 1)
        key_rate = min_success_rate * swap_success_total

        # Step 5: Latency estimation
        latency = self._estimate_latency()

        return QuantumRepeaterResult(
            total_distance_km=self.total_distance_km,
            num_segments=self.num_segments,
            end_to_end_fidelity=end_to_end_fidelity,
            key_rate=key_rate,
            key_length=int(key_rate * self.memory_coherence_time_s),
            latency_ms=latency,
            segment_fidelities=segment_fidelities,
        )

    def _generate_entanglement(self, segment: RepeaterSegment) -> float:
        """Generate entanglement in a segment."""
        # Initial fidelity depends on distance
        base_fidelity = 0.99  # Near-perfect for short distances
        distance_penalty = 0.001 * segment.distance_km
        return max(0.5, base_fidelity - distance_penalty)

    def _swap_entanglement(self, fidelities: List[float]) -> float:
        """Compute end-to-end fidelity after swapping."""
        if not fidelities:
            return 0.5

        # For two Bell pairs with fidelities F1, F2:
        # F_swap = (3*F1*F2 + (1-F1)*(1-F2)) / 4
        fidelity = fidelities[0]
        for f in fidelities[1:]:
            fidelity = (3 * fidelity * f + (1 - fidelity) * (1 - f)) / 4

        return max(0.5, fidelity)

    def _purify(self, fidelity: float) -> float:
        """Purification improves fidelity using DEJMPS protocol."""
        for _ in range(self.purification_rounds):
            # DEJMPS: F_new = (F^2 + ((1-F)/3)^2) / (F^2 + 2F(1-F)/3 + ((1-F)/3)^2)
            F = fidelity
            num = F**2 + ((1 - F) / 3)**2
            den = F**2 + 2 * F * (1 - F) / 3 + ((1 - F) / 3)**2
            fidelity = num / den if den > 0 else 0.5
            fidelity = min(1.0, fidelity)
        return fidelity

    def _estimate_latency(self) -> float:
        """Estimate end-to-end latency in ms."""
        # Speed of light in fiber
        c_fiber = 2e8  # m/s
        total_distance_m = self.total_distance_km * 1000

        # Propagation time
        propagation_s = total_distance_m / c_fiber

        # Processing time at each repeater
        processing_per_repeater_ms = 0.1
        total_processing_ms = processing_per_repeater_ms * self.num_segments

        return (propagation_s * 1000) + total_processing_ms

    def optimize_segments(self, target_fidelity: float = 0.9) -> int:
        """Find optimal number of segments for target fidelity."""
        for n in range(1, 100):
            chain = QuantumRepeater(
                total_distance_km=self.total_distance_km,
                num_segments=n,
                memory_coherence_time_s=self.memory_coherence_time_s,
                entanglement_rate=self.entanglement_rate,
                swap_success=self.swap_success,
                purification_rounds=self.purification_rounds,
            )
            result = chain.simulate()
            if result.end_to_end_fidelity >= target_fidelity:
                return n
        return 100
