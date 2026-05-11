"""Phase 5: Agentic AI Integration wiring layer."""

from __future__ import annotations

from typing import Dict

import numpy as np

from ..circuit import Circuit
from ..patterns import grover_template, qaoa_template, vqe_ansatz_template
from ..optimize.circuit_simplifier import CircuitSimplifier
from ..patterns import detect_patterns


class CircuitGenerationAgent:
    """NL-to-circuit helper with template-aware generation and constraints."""

    def generate(self, prompt: str, num_qubits: int = 2) -> Circuit:
        text = prompt.lower()
        if "grover" in text:
            return grover_template(num_qubits=max(2, num_qubits), marked_state=min(1, (1 << max(2, num_qubits)) - 1))
        if "qaoa" in text:
            n = max(2, num_qubits)
            edges = [(i, i + 1) for i in range(n - 1)]
            return qaoa_template(num_qubits=n, edges=edges, beta=0.4, gamma=0.7)
        if "vqe" in text:
            return vqe_ansatz_template(num_qubits=max(2, num_qubits), depth=2)

        circuit = Circuit(num_qubits=num_qubits, name="agent-generated")
        if "ghz" in text:
            circuit.h(0)
            for q in range(1, num_qubits):
                circuit.cnot(0, q)
            return circuit

        if "bell" in text or "entangle" in text:
            if num_qubits < 2:
                raise ValueError("Bell/entanglement circuit requires at least 2 qubits")
            circuit.h(0).cnot(0, 1)
            return circuit

        if "qft" in text:
            for i in range(num_qubits):
                circuit.h(i)
                for j in range(i + 1, num_qubits):
                    circuit.rz(j, np.pi / (2 ** (j - i)))
            return circuit

        for q in range(num_qubits):
            circuit.h(q)
        return circuit

    def generate_with_constraints(
        self,
        prompt: str,
        num_qubits: int = 2,
        max_depth: int | None = None,
        allowed_gates: set[str] | None = None,
    ) -> Circuit:
        circuit = self.generate(prompt, num_qubits=num_qubits)
        if max_depth is not None and len(circuit.gates) > max_depth:
            circuit = circuit.slice(0, max_depth)

        if allowed_gates is not None:
            allowed = {g.upper() for g in allowed_gates}
            constrained = Circuit(circuit.num_qubits, name=f"{circuit.name}_constrained")
            for g in circuit.gates:
                if g.name.upper() in allowed:
                    constrained.add_gate(g.name, g.qubits, g.params if g.params else None)
            circuit = constrained
        return circuit


class OptimizationAgent:
    def __init__(self) -> None:
        self._optimizer = CircuitSimplifier()

    def optimize(self, circuit: Circuit) -> Circuit:
        return self._optimizer.optimize(circuit)


class VerificationAgent:
    def verify(self, circuit: Circuit) -> Dict[str, object]:
        patterns = detect_patterns(circuit)
        return {"valid": True, "patterns": patterns, "pattern_count": len(patterns)}


class AgenticDevelopmentHarness:
    def __init__(self) -> None:
        self.generator = CircuitGenerationAgent()
        self.optimizer = OptimizationAgent()
        self.verifier = VerificationAgent()

    def run(self, prompt: str, num_qubits: int = 2) -> Dict[str, object]:
        original = self.generator.generate(prompt, num_qubits=num_qubits)
        optimized = self.optimizer.optimize(original)
        verification = self.verifier.verify(optimized)
        return {
            "original": original,
            "optimized": optimized,
            "verification": verification,
        }


__all__ = [
    "CircuitGenerationAgent",
    "OptimizationAgent",
    "VerificationAgent",
    "AgenticDevelopmentHarness",
]
