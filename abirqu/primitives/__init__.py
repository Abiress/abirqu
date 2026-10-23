"""
AbirQu Primitives — Unified quantum execution interface.

The ONE function that does everything:
    from abirqu.primitives import QuantumRun
    result = QuantumRun(circuits=circ, shots=4096)

Or use specialized wrappers for specific tasks:
    from abirqu.primitives import Sampler, Estimator, QNN
"""
from .estimator import Estimator
from .qnn import QNN
from .quantum_run import (
    EstimatorResult,
    MitigationResult,
    QNNResult,
    QuantumRun,
    SamplerResult,
)
from .sampler import QuasiDistribution, Sampler

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
