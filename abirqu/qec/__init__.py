"""
AbirQu QEC Module
Copyright 2026 Abir Maheshwari

Quantum Error Correction: stabilizer codes, surface codes, color codes,
syndrome decoders, magic state distillation, fault-tolerant compilation.
"""
from .codes import (
    BitFlipCode,
    ColorCode,
    EncodedState,
    PhaseFlipCode,
    RepetitionCode,
    ShorCode,
    StabilizerCode,
    SteaneCode,
    SurfaceCode,
)
from .decoder import (
    BeliefPropagationDecoder,
    GPUAcceleratedDecoder,
    MWPMDecoder,
    SurfaceCodeDecoder,
    SyndromeDecoder,
)
from .ft_compiler import (
    CompilationResult,
    FaultTolerantCompiler,
    GateInfo,
    TransversalGateSet,
)
from .ldpc import LDPCCode
from .magic_state import (
    HStateDistiller,
    MagicState,
    MagicStateDistiller,
    TGateInjector,
    TStateFactory,
)
from .surface_code import RotatedSurfaceCode
from .union_find_decoder import UnionFindDecoder

__all__ = [
    # Codes
    'StabilizerCode', 'RepetitionCode', 'BitFlipCode', 'PhaseFlipCode',
    'ShorCode', 'SteaneCode', 'SurfaceCode', 'ColorCode', 'EncodedState',
    'RotatedSurfaceCode', 'LDPCCode',
    # Decoders
    'SyndromeDecoder', 'SurfaceCodeDecoder', 'BeliefPropagationDecoder',
    'MWPMDecoder', 'GPUAcceleratedDecoder', 'UnionFindDecoder',
    # Magic states
    'MagicState', 'MagicStateDistiller', 'HStateDistiller',
    'TStateFactory', 'TGateInjector',
    # FT compilation
    'FaultTolerantCompiler', 'TransversalGateSet',
    'CompilationResult', 'GateInfo',
]
