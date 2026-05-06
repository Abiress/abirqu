"""
Phase 11: Quantum Resource Estimation & Planning

Task 11.1 - Physical Resource Calculator
Task 11.2 - Error Budget Manager
Task 11.3 - Hardware Requirement Profiler
Task 11.4 - Cost Estimation Engine
Task 11.5 - Feasibility Assessment Tool
"""

from .calculator import (PhysicalResourceCalculator, ResourceBreakdown, 
                         GateCountEstimator, QECCodeType)
from .error_budget import ErrorBudgetManager, ErrorBudget, ErrorAllocation, ErrorType
from .profiler import (HardwareProfiler, HardwareRequirement, ThresholdAnalysis,
                        HardwareSpec, HardwareType)
from .cost import CostEstimationEngine, CostEstimate, ProviderPricing, ProviderType
from .feasibility import (FeasibilityAssessment, FeasibilityReport, RecommendationEngine,
                          FeasibilityStatus, AlgorithmComplexity, ClassicalHardnessAnalyzer,
                          TimelineEstimator)

__all__ = [
    # Task 11.1
    'PhysicalResourceCalculator', 'ResourceBreakdown', 'GateCountEstimator', 'QECCodeType',
    # Task 11.2
    'ErrorBudgetManager', 'ErrorBudget', 'ErrorAllocation', 'ErrorType',
    # Task 11.3
    'HardwareProfiler', 'HardwareRequirement', 'ThresholdAnalysis',
    'HardwareSpec', 'HardwareType',
    # Task 11.4
    'CostEstimationEngine', 'CostEstimate', 'ProviderPricing', 'ProviderType',
    # Task 11.5
    'FeasibilityAssessment', 'FeasibilityReport', 'RecommendationEngine',
    'FeasibilityStatus', 'AlgorithmComplexity', 'ClassicalHardnessAnalyzer', 'TimelineEstimator',
]
