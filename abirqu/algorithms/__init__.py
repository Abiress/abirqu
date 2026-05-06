"""
Phase 20 & 24: Advanced Quantum Algorithms.

Implement advanced algorithms: Shor's, Grover's, QAOA, VQE, HHL.
Supports 20+ qubit simulations with VQE and QAOA.
Also includes Quantum ML extensions (QNN, QSVM, QKMeans, QPCA).
"""

from .advanced import (
    AdvancedAlgorithms, AlgorithmResult,
    ShorsAlgorithm, GroversAlgorithm,
    QAOAAlgorithm, VQEAlgorithm, HHLAlgorithm
)

try:
    from .extensions import (
        AlgorithmType, AdvancedAlgorithmResult,
        GroverAdaptiveSearch, QuantumApproximateKernel,
        QuantumNeuralNetwork, QuantumSupportVectorMachine,
        QuantumKMeans, QuantumPCA,
        QuantumFourierTransform, QuantumPhaseEstimation,
        create_algorithm
    )
    __all__ = [
        'AdvancedAlgorithms', 'AlgorithmResult',
        'ShorsAlgorithm', 'GroversAlgorithm',
        'QAOAAlgorithm', 'VQEAlgorithm', 'HHLAlgorithm',
        'AlgorithmType', 'AdvancedAlgorithmResult',
        'GroverAdaptiveSearch', 'QuantumApproximateKernel',
        'QuantumNeuralNetwork', 'QuantumSupportVectorMachine',
        'QuantumKMeans', 'QuantumPCA',
        'QuantumFourierTransform', 'QuantumPhaseEstimation',
        'create_algorithm',
    ]
except ImportError:
    __all__ = [
        'AdvancedAlgorithms', 'AlgorithmResult',
        'ShorsAlgorithm', 'GroversAlgorithm',
        'QAOAAlgorithm', 'VQEAlgorithm', 'HHLAlgorithm',
    ]
