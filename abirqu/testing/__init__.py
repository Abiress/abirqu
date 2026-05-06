"""
Phase 14: Quantum Software Testing & Verification Framework.

Task 14.1 — Circuit Equivalence Checker
Task 14.2 — Quantum Property-Based Testing
Task 14.3 — Quantum Formal Verification
Task 14.4 — Noise Robustness Testing
Task 14.5 — Regression & Continuous Testing
"""

from .equivalence import (
    CircuitEquivalenceChecker, ExactEquivalence, ApproximateEquivalence,
    NoiseAwareEquivalence, SymbolicEquivalence, EquivalenceResult,
    EquivalenceType
)
from .property_testing import (
    QuantumPropertyTester, PropertyBasedGenerator, InvariantChecker,
    RandomizedTester, CoverageMetrics, PropertyTestResult
)
from .formal_verification import (
    QuantumHoareLogic, WeakestPrecondition, InvariantGenerator,
    ProofCertificate, VerificationResult, VerificationStatus
)
from .noise_robustness import (
    NoiseSensitivityAnalyzer, MonteCarloNoiseSimulator,
    ThresholdAnalyzer, RobustnessCertifier, RobustnessResult,
    RobustnessMetric
)
from .regression import (
    QuantumRegressionSuite, CIRegression, SnapshotTester,
    TestDashboard, AutoTestGenerator, RegressionResult
)

__all__ = [
    # Task 14.1
    'CircuitEquivalenceChecker', 'ExactEquivalence', 'ApproximateEquivalence',
    'NoiseAwareEquivalence', 'SymbolicEquivalence', 'EquivalenceResult',
    'EquivalenceType',
    # Task 14.2
    'QuantumPropertyTester', 'PropertyBasedGenerator', 'InvariantChecker',
    'RandomizedTester', 'CoverageMetrics', 'PropertyTestResult',
    # Task 14.3
    'QuantumHoareLogic', 'WeakestPrecondition', 'InvariantGenerator',
    'ProofCertificate', 'VerificationResult', 'VerificationStatus',
    # Task 14.4
    'NoiseSensitivityAnalyzer', 'MonteCarloNoiseSimulator',
    'ThresholdAnalyzer', 'RobustnessCertifier', 'RobustnessResult',
    'RobustnessMetric',
    # Task 14.5
    'QuantumRegressionSuite', 'CIRegression', 'SnapshotTester',
    'TestDashboard', 'AutoTestGenerator', 'RegressionResult',
]
