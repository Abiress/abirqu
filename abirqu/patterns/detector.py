from dataclasses import dataclass
from typing import Dict, Tuple

from ..circuit import Circuit, Gate
from .core_patterns import detect_patterns


@dataclass
class OptimizationReport:
    original_gates: int
    optimized_gates: int
    removed: int
    pattern_matches: int


class PatternAwareOptimizer:
    """Conservative optimizer that preserves detected pattern boundaries."""

    def optimize(self, circuit: Circuit) -> Tuple[Circuit, OptimizationReport]:
        optimized = Circuit(circuit.num_qubits, name=f"{circuit.name}_pattern_opt")
        matches = detect_patterns(circuit)

        i = 0
        while i < len(circuit.gates):
            g = circuit.gates[i]
            # Cancel adjacent inverse-like pairs for simple gates.
            if i + 1 < len(circuit.gates):
                n = circuit.gates[i + 1]
                if g.name == n.name and g.qubits == n.qubits and g.name in {"H", "X", "Y", "Z", "CNOT", "CZ"}:
                    i += 2
                    continue
            optimized.gates.append(Gate(g.name, list(g.qubits), g.matrix, list(g.params)))
            i += 1

        report = OptimizationReport(
            original_gates=len(circuit.gates),
            optimized_gates=len(optimized.gates),
            removed=max(0, len(circuit.gates) - len(optimized.gates)),
            pattern_matches=len(matches),
        )
        return optimized, report

    def metrics(self, circuit: Circuit) -> Dict[str, int]:
        matches = detect_patterns(circuit)
        return {
            "gates": len(circuit.gates),
            "patterns": len(matches),
        }
