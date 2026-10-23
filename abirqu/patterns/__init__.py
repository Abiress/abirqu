"""Quantum design patterns for reusable circuit construction."""

from .core_patterns import (
    PatternKind,
    PatternMatch,
    detect_patterns,
    entanglement_pattern,
    initialization_pattern,
    oracle_pattern,
    superposition_pattern,
)
from .detector import PatternAwareOptimizer
from .registry import PatternRegistry
from .templates import (
    grover_template,
    qaoa_template,
    vqe_ansatz_template,
)

__all__ = [
    "PatternKind",
    "PatternMatch",
    "initialization_pattern",
    "superposition_pattern",
    "entanglement_pattern",
    "oracle_pattern",
    "detect_patterns",
    "grover_template",
    "qaoa_template",
    "vqe_ansatz_template",
    "PatternAwareOptimizer",
    "PatternRegistry",
]
