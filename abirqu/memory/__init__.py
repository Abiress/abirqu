"""
Phase 12: Quantum Memory Management & Optimization.

Task 12.1 - Quantum RAM (QRAM) Simulation
Task 12.2 - Quantum State Compression  
Task 12.3 - Quantum Cache Manager
Task 12.4 - Quantum Garbage Collection
Task 12.5 - Memory-Aware Compilation
"""

from .qram import QRAMSimulator, QRAMArchitecture, QRAMQuery
from .compression import (QuantumStateCompressor, TensorDecomposition, 
                          CompressionResult, CompressionMethod)
from .cache import QuantumCacheManager, CacheEntry, CacheAnalytics
from .garbage import (QuantumGarbageCollector, UncomputationEngine, 
                         QubitReuseScheduler)
from .compilation import (MemoryAwareCompiler, CircuitCutter, MemoryProfiler,
                           OptimizationStrategy, MemoryProfile, CutCircuit)

__all__ = [
    # Task 12.1
    'QRAMSimulator', 'QRAMArchitecture', 'QRAMQuery',
    # Task 12.2
    'QuantumStateCompressor', 'TensorDecomposition', 
    'CompressionResult', 'CompressionMethod',
    # Task 12.3
    'QuantumCacheManager', 'CacheEntry', 'CacheAnalytics',
    # Task 12.4
    'QuantumGarbageCollector', 'UncomputationEngine', 
    'QubitReuseScheduler',
    # Task 12.5
    'MemoryAwareCompiler', 'CircuitCutter', 'MemoryProfiler',
    'OptimizationStrategy', 'MemoryProfile', 'CutCircuit',
]
