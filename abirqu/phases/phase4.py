"""Phase 4: Quantum Design Patterns wiring layer."""

from __future__ import annotations

from ..patterns import (
    PatternAwareOptimizer,
    PatternKind,
    PatternMatch,
    PatternRegistry,
    detect_patterns,
    entanglement_pattern,
    grover_template,
    initialization_pattern,
    oracle_pattern,
    qaoa_template,
    superposition_pattern,
    vqe_ansatz_template,
)


__all__ = [
    "PatternKind",
    "PatternMatch",
    "PatternRegistry",
    "PatternAwareOptimizer",
    "detect_patterns",
    "initialization_pattern",
    "superposition_pattern",
    "entanglement_pattern",
    "oracle_pattern",
    "grover_template",
    "qaoa_template",
    "vqe_ansatz_template",
]
