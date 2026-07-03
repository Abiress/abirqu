"""
Estimator — compute expectation values <ψ|O|ψ> of observables.

NOT a copy of Qiskit.  AbirQu's Estimator computes ALL observables
in a single pass over the statevector, not per-observable.  This
means 100 observables cost ~the same as 1.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import numpy as np
from ..circuit import Circuit
from .quantum_run import QuantumRun, EstimatorResult as _EstimatorResult


class Estimator:
    """
    Compute expectation values of Pauli operators / matrices.

    Usage:
        estimator = Estimator()
        result = estimator.run(
            circuits=[bell],
            observables=[
                {"ZZ": [[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]]},
                {"XX": [[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]]},
            ],
        )
        result.values  # [1.0, 1.0]  (both ZZ and XX are +1 for Bell)
    """

    def __init__(self, backend: Any = None, seed: Optional[int] = None):
        self._backend = backend
        self._seed = seed

    def run(
        self,
        circuits: Union[Circuit, List[Circuit]],
        observables: List[Dict],
        shots: int = 0,
    ) -> _EstimatorResult:
        qr = QuantumRun(
            circuits=circuits,
            observables=observables,
            shots=shots,
            backend=self._backend,
            seed=self._seed,
        )
        exp_results = qr.expectations
        if exp_results is None:
            raise ValueError("No observables provided")
        # Merge all circuit results into one EstimatorResult
        all_values = []
        all_meta = []
        for er in exp_results:
            all_values.extend(er.values)
            all_meta.extend(er.metadata)
        return _EstimatorResult(values=all_values, metadata=all_meta)
