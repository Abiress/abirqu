"""
Phase 22: Advanced Quantum Algorithms.

Implement advanced algorithms: Shor's, Grover's, QAOA, VQE, HHL.
Supports 20+ qubit simulations with GPU acceleration.
"""

from .advanced import (
    AdvancedAlgorithms, AlgorithmResult,
    ShorsAlgorithm, GroversAlgorithm,
    QAOAlgorithm, VQEAlgorithm, HHLAlgorithm
)

__all__ = [
    'AdvancedAlgorithms', 'AlgorithmResult',
    'ShorsAlgorithm', 'GroversAlgorithm',
    'QAOAlgorithm', 'VQEAlgorithm', 'HHLAlgorithm',
]
