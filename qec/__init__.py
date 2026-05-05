"""
AbirQu QEC Module
Quantum Error Correction with LDPC codes and GPU-accelerated decoders.
"""

from .codes import (
    StabilizerCode, SurfaceCode, ColorCode, ToricCode, RepetitionCode
)
from .ldpc import LDPCCode, CSSCodeConstructor, ParityCheckMatrixGenerator
from .decoder import (
    UnionFindDecoder, BeliefPropagationDecoder, 
    GPUSyndromeDecoder, DecoderBenchmark
)
from .patch import Patch, PatchManager, MagicStateFactory
from .ft_compiler import (
    FaultTolerantCompiler, LogicalGate, OverheadEstimate,
    FaultTolerantCircuit
)

__all__ = [
    'StabilizerCode', 'SurfaceCode', 'ColorCode', 'ToricCode', 'RepetitionCode',
    'LDPCCode', 'CSSCodeConstructor', 'ParityCheckMatrixGenerator',
    'UnionFindDecoder', 'BeliefPropagationDecoder', 
    'GPUSyndromeDecoder', 'DecoderBenchmark',
    'Patch', 'PatchManager', 'MagicStateFactory',
    'FaultTolerantCompiler', 'LogicalGate', 'OverheadEstimate',
    'FaultTolerantCircuit',
]