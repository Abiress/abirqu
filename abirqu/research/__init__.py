"""
Phase 15: Quantum Algorithm Discovery & Research Engine.

Task 15.1 — Algorithm Search Space Explorer
Task 15.2 — Quantum Complexity Analyzer
Task 15.3 — Quantum Advantage Validator
Task 15.4 — Literature-Aware Circuit Suggestion
Task 15.5 — Quantum Algorithm Benchmarking Suite
"""

from .search_space import (
    AlgorithmSearchSpace, GeneticCircuitEvolution, RLCircuitDiscovery,
    NoveltyDetector, SearchResult, SearchStrategy
)
from .complexity import (
    ComplexityAnalyzer, ResourceScalingAnalyzer, ClassicalComparator,
    ComplexityEstimator, ComplexityResult, ComplexityClass
)
from .advantage import (
    QuantumAdvantageValidator, ClassicalSimulationComparator,
    StatisticalTester, ReproducibleBenchmark, AdvantageResult
)
from .benchmarking import (
    QuantumBenchmarkSuite, StandardizedBenchmark, BenchmarkFramework,
    LeaderboardGenerator, HistoricalTracker, BenchmarkResult, BenchmarkType
)
from .literature import (
    AlgorithmKnowledgeBase, SimilaritySearch, CitationRecommender,
    AlgorithmAdapter, LiteratureResult
)
from .benchmarking import (
    QuantumBenchmarkSuite, StandardizedBenchmark, BenchmarkFramework,
    LeaderboardGenerator, HistoricalTracker, BenchmarkResult
)

__all__ = [
    # Task 15.1
    'AlgorithmSearchSpace', 'GeneticCircuitEvolution', 'RLCircuitDiscovery',
    'NoveltyDetector', 'SearchResult', 'SearchStrategy',
    # Task 15.2
    'ComplexityAnalyzer', 'ResourceScalingAnalyzer', 'ClassicalComparator',
    'ComplexityEstimator', 'ComplexityResult', 'ComplexityClass',
    # Task 15.3
    'QuantumAdvantageValidator', 'ClassicalSimulationComparator',
    'StatisticalTester', 'ReproducibleBenchmark', 'AdvantageResult',
    'BenchmarkResult',
    # Task 15.4
    'AlgorithmKnowledgeBase', 'SimilaritySearch', 'CitationRecommender',
    'AlgorithmAdapter', 'LiteratureResult',
    # Task 15.5
    'QuantumBenchmarkSuite', 'StandardizedBenchmark', 'BenchmarkFramework',
    'LeaderboardGenerator', 'HistoricalTracker', 'BenchmarkResult', 'BenchmarkType',
]
