"""
Quantum-Classical Hybrid Computing Framework

Unified execution runtime for seamless quantum-classical computation.
"""

from .runtime import HybridRuntime, ExecutionMode, WorkloadPartitioner, SharedMemorySpace
from .variational import VariationalAccelerator, ParameterOptimizer, GradientMethod
from .pipeline import ClassicalPipeline, DataEncoder, ResultDecoder, EncodingType, PrecisionManager
from .loops import IterativeLoop, FeedbackController, ConvergenceDetector, ResourceBudgetManager, LoopState
from .orchestration import (HybridOrchestrator, WorkflowEngine, BranchingEngine, 
                           ParallelExecutor, CostTimeQualityOptimizer, TaskType, WorkflowStatus)
from .orchestration import WorkflowTask  # Import WorkflowTask separately

__all__ = [
    'HybridRuntime', 'ExecutionMode', 'WorkloadPartitioner', 'SharedMemorySpace',
    'VariationalAccelerator', 'ParameterOptimizer', 'GradientMethod',
    'ClassicalPipeline', 'DataEncoder', 'ResultDecoder', 'EncodingType', 'PrecisionManager',
    'IterativeLoop', 'FeedbackController', 'ConvergenceDetector', 'ResourceBudgetManager', 'LoopState',
    'HybridOrchestrator', 'WorkflowEngine', 'BranchingEngine', 
    'ParallelExecutor', 'CostTimeQualityOptimizer', 'TaskType', 'WorkflowStatus', 'WorkflowTask',
]
