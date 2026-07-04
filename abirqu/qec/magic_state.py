"""
Magic State Distillation for AbirQu
Copyright 2026 Abir Maheshwari

Implements the 15-to-1 magic state distillation protocol for |T> states,
and the 20-to-4 protocol for |H> states.

Magic states enable non-Clifford gates (T gate, Toffoli) in
fault-tolerant quantum computation.
"""
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MagicState:
    """A magic state with quality metrics."""
    state_type: str         # 'T' or 'H'
    fidelity: float
    is_noisy: bool = False
    creation_round: int = 0

    def __repr__(self):
        return f"MagicState({self.state_type}, F={self.fidelity:.4f})"


class MagicStateDistiller:
    """15-to-1 magic state distillation for |T> states.

    Takes 15 noisy |T> states with fidelity > 1/2 + epsilon
    and produces 1 |T> state with higher fidelity.

    The T state: |T> = T|+> = (|0> + e^{iπ/4}|1>)/√2
    """

    def __init__(self, rounds: int = 1):
        self.rounds = rounds
        self.input_count = 15
        self.output_count = 1

    def distill(self, noisy_states: List[MagicState],
                rounds: Optional[int] = None) -> MagicState:
        """Distill noisy magic states.

        Args:
            noisy_states: List of 15 (or more, take first 15) noisy states.
            rounds: Override number of distillation rounds.

        Returns:
            Single distilled MagicState with improved fidelity.
        """
        if rounds is None:
            rounds = self.rounds

        if len(noisy_states) < self.input_count:
            raise ValueError(
                f"Need {self.input_count} states, got {len(noisy_states)}")

        # Take the best 15 states
        sorted_states = sorted(noisy_states,
                               key=lambda s: s.fidelity, reverse=True)
        input_states = sorted_states[:self.input_count]

        # Average input fidelity
        avg_fidelity = np.mean([s.fidelity for s in input_states])

        fidelity = avg_fidelity
        for _ in range(rounds):
            fidelity = self._distill_round(fidelity)

        return MagicState(
            state_type='T',
            fidelity=min(fidelity, 1.0),
            creation_round=rounds,
        )

    def _distill_round(self, input_fidelity: float) -> float:
        """Single round of 15-to-1 distillation.

        Output fidelity ≈ 1 - 35 * (1 - F)^3 for input fidelity F.
        This works when F > 0.5.
        """
        eps = 1.0 - input_fidelity
        # Leading order: output error ≈ 35 * eps^3
        output_error = 35.0 * eps ** 3
        return max(0.5, 1.0 - output_error)

    def estimate_resources(self, target_fidelity: float = 0.99,
                           initial_fidelity: float = 0.9) -> dict:
        """Estimate resources needed to reach target fidelity."""
        rounds = 0
        fidelity = initial_fidelity
        total_states = 1

        while fidelity < target_fidelity and rounds < 10:
            rounds += 1
            fidelity = self._distill_round(fidelity)
            total_states *= self.input_count

        return {
            'rounds': rounds,
            'final_fidelity': min(fidelity, 1.0),
            'total_input_states': total_states,
            'overhead_factor': total_states,
        }


class HStateDistiller:
    """20-to-4 distillation for |H> states.

    |H> = cos(π/8)|0> + sin(π/8)|1>
    Used for implementing the Toffoli gate fault-tolerantly.
    """

    def __init__(self, rounds: int = 1):
        self.rounds = rounds
        self.input_count = 20
        self.output_count = 4

    def distill(self, noisy_states: List[MagicState],
                rounds: Optional[int] = None) -> List[MagicState]:
        """Distill 20 noisy H states into 4 better H states."""
        if rounds is None:
            rounds = self.rounds

        if len(noisy_states) < self.input_count:
            raise ValueError(
                f"Need {self.input_count} states, got {len(noisy_states)}")

        avg_fidelity = np.mean([s.fidelity for s in noisy_states[:self.input_count]])

        fidelity = avg_fidelity
        for _ in range(rounds):
            fidelity = self._distill_round(fidelity)

        return [
            MagicState(state_type='H', fidelity=min(fidelity, 1.0),
                       creation_round=rounds)
            for _ in range(self.output_count)
        ]

    def _distill_round(self, input_fidelity: float) -> float:
        """Single round of 20-to-4 distillation.

        Output fidelity ≈ 1 - 140 * (1 - F)^3.
        """
        eps = 1.0 - input_fidelity
        output_error = 140.0 * eps ** 3
        return max(0.5, 1.0 - output_error)


class TStateFactory:
    """Factory for producing |T> magic states at scale.

    Combines state preparation, distillation, and injection.
    """

    def __init__(self, distillation_rounds: int = 1,
                 initial_fidelity: float = 0.9):
        self.distillation_rounds = distillation_rounds
        self.initial_fidelity = initial_fidelity
        self.distiller = MagicStateDistiller(distillation_rounds)
        self.states_produced = 0
        self.total_states_consumed = 0

    def produce(self, count: int = 1) -> List[MagicState]:
        """Produce `count` distilled magic states."""
        produced = []
        for _ in range(count):
            # Generate noisy input states
            noisy_states = self._generate_noisy_states(15)
            self.total_states_consumed += 15

            # Distill
            result = self.distiller.distill(noisy_states, self.distillation_rounds)
            produced.append(result)
            self.states_produced += 1

        return produced

    def _generate_noisy_states(self, count: int) -> List[MagicState]:
        """Generate noisy |T> states with given fidelity."""
        states = []
        for _ in range(count):
            # Add random noise to fidelity
            noise = np.random.normal(0, 0.05)
            fidelity = np.clip(self.initial_fidelity + noise, 0.5, 1.0)
            states.append(MagicState(state_type='T', fidelity=fidelity))
        return states

    def get_stats(self) -> dict:
        return {
            'states_produced': self.states_produced,
            'total_states_consumed': self.total_states_consumed,
            'efficiency': (self.states_produced /
                           max(1, self.total_states_consumed)),
            'distillation_rounds': self.distillation_rounds,
        }


class TGateInjector:
    """Inject T gate using magic state teleportation.

    Protocol:
    1. Prepare |T> magic state
    2. Create Bell pair between data qubit and ancilla
    3. Perform CNOT from magic state to ancilla
    4. Measure ancilla in X basis
    5. Apply conditional S gate and T correction
    """

    def __init__(self):
        self.states_injected = 0
        self.fidelity_sum = 0.0

    def inject(self, magic_state: MagicState,
               measurement_outcome: int = 0) -> dict:
        """Simulate T gate injection via magic state teleportation.

        Returns dict with gate fidelity and any corrections needed.
        """
        self.states_injected += 1
        self.fidelity_sum += magic_state.fidelity

        # Gate fidelity ≈ magic state fidelity (leading order)
        gate_fidelity = magic_state.fidelity

        # Corrections
        corrections = []
        if measurement_outcome == 1:
            corrections.append('S')

        return {
            'gate_fidelity': gate_fidelity,
            'corrections': corrections,
            'magic_state_fidelity': magic_state.fidelity,
            'state_type': magic_state.state_type,
        }

    def get_avg_fidelity(self) -> float:
        if self.states_injected == 0:
            return 0.0
        return self.fidelity_sum / self.states_injected

    def __repr__(self):
        return (f"TGateInjector(injected={self.states_injected}, "
                f"avg_fidelity={self.get_avg_fidelity():.4f})")
