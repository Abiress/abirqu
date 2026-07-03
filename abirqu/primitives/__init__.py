"""
AbirQu Primitives — Unified quantum execution interface.

The ONE function that does everything:
    from abirqu.primitives import QuantumRun
    result = QuantumRun(circuits=circ, shots=4096)

Or use specialized wrappers for specific tasks:
    from abirqu.primitives import Sampler, Estimator, QNN
"""
from .quantum_run import (
    QuantumRun,
    SamplerResult,
    EstimatorResult,
    MitigationResult,
    QNNResult,
)
from .sampler import Sampler, QuasiDistribution
from .estimator import Estimator
from .qnn import QNN

__all__ = [
    "QuantumRun",
    "SamplerResult",
    "EstimatorResult",
    "MitigationResult",
    "QNNResult",
    "Sampler",
    "QuasiDistribution",
    "Estimator",
    "QNN",
]
