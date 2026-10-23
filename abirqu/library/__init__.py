"""
Circuit Library for AbirQu — parameterized ansatz circuits, encoders, benchmarks.

Unique features:
- N-local circuits with "sca" entanglement (shifted circular alternating)
- QAOA with automatic mixer Hamiltonian
- VQE with hardware-efficient and UCCSD ansatz
- Feature maps: angle, amplitude, ZZ, IQP
- Benchmark circuits: GHZ, W, QFT, Grover, BV, random
"""
from .benchmarks import (
    bernstein_vazirani_circuit,
    ghz_circuit,
    grover_circuit,
    grover_oracle,
    qft_circuit,
    quantum_fourier_transform,
    random_circuit,
    w_state,
)
from .encoders import amplitude_encoding, angle_encoding, iqp_encoding, zz_feature_map
from .n_local import efficient_su2, n_local, real_amplitudes
from .qaoa_ansatz import qaoa_circuit, qaoa_maxcut
from .vqe_ansatz import vqe_custom, vqe_hardware_efficient, vqe_uccsd

__all__ = [
    # N-local
    "real_amplitudes", "efficient_su2", "n_local",
    # QAOA
    "qaoa_circuit", "qaoa_maxcut",
    # VQE
    "vqe_hardware_efficient", "vqe_uccsd", "vqe_custom",
    # Encoders
    "angle_encoding", "amplitude_encoding", "zz_feature_map", "iqp_encoding",
    # Benchmarks
    "ghz_circuit", "w_state", "qft_circuit", "grover_circuit",
    "grover_oracle", "bernstein_vazirani_circuit", "quantum_fourier_transform",
    "random_circuit",
]
