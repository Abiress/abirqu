"""
AbirQu QEC Module
Copyright 2026 Abir Maheshwari

Quantum Error Correction: stabilizer codes, surface codes, color codes,
syndrome decoders, magic state distillation, fault-tolerant compilation.
"""
from .codes import (
    StabilizerCode, RepetitionCode, BitFlipCode, PhaseFlipCode,
    ShorCode, SteaneCode, SurfaceCode, ColorCode, EncodedState,
)
from .surface_code import RotatedSurfaceCode
from .decoder import (
    SyndromeDecoder, SurfaceCodeDecoder, BeliefPropagationDecoder,
    MWPMDecoder, GPUAcceleratedDecoder,
)
from .magic_state import (
    MagicState, MagicStateDistiller, HStateDistiller,
    TStateFactory, TGateInjector,
)
from .ft_compiler import (
    FaultTolerantCompiler, TransversalGateSet,
    CompilationResult, GateInfo,
)
from .ldpc import LDPCCode

__all__ = [
    # Codes
    'StabilizerCode', 'RepetitionCode', 'BitFlipCode', 'PhaseFlipCode',
    'ShorCode', 'SteaneCode', 'SurfaceCode', 'ColorCode', 'EncodedState',
    'RotatedSurfaceCode', 'LDPCCode',
    # Decoders
    'SyndromeDecoder', 'SurfaceCodeDecoder', 'BeliefPropagationDecoder',
    'MWPMDecoder', 'GPUAcceleratedDecoder',
    # Magic states
    'MagicState', 'MagicStateDistiller', 'HStateDistiller',
    'TStateFactory', 'TGateInjector',
    # FT compilation
    'FaultTolerantCompiler', 'TransversalGateSet',
    'CompilationResult', 'GateInfo',
]
