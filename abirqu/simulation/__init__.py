"""
Simulation Backends
===================
Multiple quantum simulation strategies.
"""

from .density_sim import DensityMatrixSimulator
from .gpu_sim import GPUSimulator, gpu_available
from .clifford import CliffordSimulator, is_clifford_only
from .mps import MPSSimulator, estimate_bond_dimension
from .monte_carlo import MonteCarloWavefunctionSimulator, NoiseChannel, MonteCarloResult
from .ode_solver import (
    TimeEvolutionSolver, HamiltonianBuilder, HamiltonianTerm,
    LindbladOperator, ThermalStateSolver
)
from .waveform import (
    WaveformGenerator, WaveformEnvelope, WaveformModulator,
    WaveformComposer, PulseShapeLibrary, WaveformType
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
