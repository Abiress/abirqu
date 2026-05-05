"""
AbirQu Patterns Module
Quantum Design Patterns Library and Algorithm Templates.
"""

from .core_patterns import (
    QuantumPattern, PatternType,
    InitializationPattern, SuperpositionPattern,
    EntanglementPattern, OraclePattern
)
from .templates import (
    AlgorithmTemplate, VQETemplate, QAOATemplate,
    GroversTemplate, QPE Template
)
from .detector import PatternDetector
from .registry import (
    ComponentRegistry, QuantumComponent, ComponentMetadata,
    ComponentType
)

__all__ = [
    'QuantumPattern', 'PatternType',
    'InitializationPattern', 'SuperpositionPattern',
    'EntanglementPattern', 'OraclePattern',
    'AlgorithmTemplate', 'VQETemplate', 'QAOATemplate',
    'GroversTemplate', 'QPE Template',
    'PatternDetector',
    'ComponentRegistry', 'QuantumComponent', 'ComponentMetadata',
    'ComponentType',
]