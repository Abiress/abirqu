"""
Circuit Library for AbirQu — parameterized ansatz circuits, encoders, benchmarks.

Unique features:
- N-local circuits with "sca" entanglement (shifted circular alternating)
- QAOA with automatic mixer Hamiltonian
- VQE with hardware-efficient and UCCSD ansatz
- Feature maps: angle, amplitude, ZZ, IQP
- Benchmark circuits: GHZ, W, QFT, Grover, BV, random
"""
from .n_local import real_amplitudes, efficient_su2, n_local
from .qaoa_ansatz import qaoa_circuit, qaoa_maxcut
from .vqe_ansatz import vqe_hardware_efficient, vqe_uccsd, vqe_custom
from .encoders import angle_encoding, amplitude_encoding, zz_feature_map, iqp_encoding
from .benchmarks import (
    ghz_circuit, w_state, qft_circuit, grover_circuit,
    grover_oracle, bernstein_vazirani_circuit, quantum_fourier_transform,
    random_circuit,
)

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
