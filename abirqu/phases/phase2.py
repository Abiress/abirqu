"""Phase 2: Optimization Engine wiring layer."""

from __future__ import annotations

from ..circuit import Circuit
from ..optimize.circuit_simplifier import CircuitSimplifier


class OptimizationEngine:
    """Facade for the phase polynomial and simplification stack."""

    def __init__(self) -> None:
        self._simplifier = CircuitSimplifier()

    def optimize(self, circuit: Circuit) -> Circuit:
        return self._simplifier.optimize(circuit)

    def stats(self):
        return dict(self._simplifier.stats)


def simplify_circuit(circuit: Circuit) -> Circuit:
    return CircuitSimplifier().simplify(circuit)


__all__ = [
    "OptimizationEngine",
    "CircuitSimplifier",
    "simplify_circuit",
]
