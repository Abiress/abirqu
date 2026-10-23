"""
Simulation Backends
===================
Multiple quantum simulation strategies.
"""

from .clifford import CliffordSimulator, is_clifford_only
from .density_sim import DensityMatrixSimulator
from .gpu_sim import GPUSimulator, gpu_available
from .monte_carlo import MonteCarloResult, MonteCarloWavefunctionSimulator, NoiseChannel
from .mps import MPSSimulator, estimate_bond_dimension
from .ode_solver import (
    HamiltonianBuilder,
    HamiltonianTerm,
    LindbladOperator,
    ThermalStateSolver,
    TimeEvolutionSolver,
)
from .waveform import (
    PulseShapeLibrary,
    WaveformComposer,
    WaveformEnvelope,
    WaveformGenerator,
    WaveformModulator,
    WaveformType,
)

__all__ = [
    # Existing
    "DensityMatrixSimulator",
    "GPUSimulator",
    "gpu_available",
    "CliffordSimulator",
    "is_clifford_only",
    "MPSSimulator",
    "estimate_bond_dimension",
    # Monte Carlo
    "MonteCarloWavefunctionSimulator",
    "NoiseChannel",
    "MonteCarloResult",
    # ODE Solver
    "TimeEvolutionSolver",
    "HamiltonianBuilder",
    "HamiltonianTerm",
    "LindbladOperator",
    "ThermalStateSolver",
    # Waveforms
    "WaveformGenerator",
    "WaveformEnvelope",
    "WaveformModulator",
    "WaveformComposer",
    "PulseShapeLibrary",
    "WaveformType",
]
