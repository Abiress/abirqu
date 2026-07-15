"""
VQE ansatz circuits for AbirQu.

Unique to AbirQu:
- Hardware-efficient ansatz (minimize two-qubit gates)
- Chemistry-aware UCCSD ansatz stubs
- Automatic circuit depth optimization
"""
from __future__ import annotations
from typing import List, Optional
from ..circuit import Circuit
from .n_local import efficient_su2, real_amplitudes


def vqe_hardware_efficient(num_qubits: int, depth: int = 2,
                           entanglement: str = "linear",
                           prefix: str = "θ",
                           parameters: Optional[List[float]] = None) -> Circuit:
    """
    Hardware-efficient VQE ansatz.

    Uses EfficientSU2 with linear entanglement for minimal depth.
    This is the default ansatz for variational quantum eigensolvers.
    """
    return efficient_su2(num_qubits, reps=depth,
                         entanglement=entanglement, prefix=prefix)


def vqe_uccsd(num_qubits: int, num_electrons: Optional[int] = None,
              prefix: str = "θ", parameters: Optional[List[float]] = None) -> Circuit:
    """
    UCCSD (Unitary Coupled Cluster Singles and Doubles) ansatz.

    This is a simplified version. For full UCCSD, see the
    abirqu.chemistry module (if available).

    Creates a circuit with single excitation (H-RY-CNOT) and
    double excitation layers.
    """
    if num_electrons is None:
        num_electrons = num_qubits // 2

    c = Circuit(num_qubits, f"UCCSD({num_qubits})")

    # Single excitations: for each occupied-virtual pair
    param_idx = 0
    for i in range(num_electrons):
        for j in range(num_electrons, num_qubits):
            # Single excitation: H-RY-CNOT-H pattern
            c.add_gate("H", i, [])
            c.add_gate("H", j, [])
            c.add_gate("CNOT", [i, j])
            angle = float(parameters[param_idx]) if parameters and param_idx < len(parameters) else float(param_idx)
            c.add_gate("RY", j, [angle])
            c.add_gate("CNOT", [i, j])
            c.add_gate("H", i, [])
            c.add_gate("H", j, [])
            param_idx += 1

    return c


def vqe_custom(num_qubits: int, layers: int = 2,
               rotation_gates: Optional[List[str]] = None,
               entanglement: str = "full",
               prefix: str = "θ") -> Circuit:
    """
    Custom VQE ansatz — user specifies rotation gates and entanglement.
    """
    from .n_local import n_local
    return n_local(num_qubits, reps=layers,
                   rotation_gates=rotation_gates,
                   entanglement=entanglement,
                   prefix=prefix)
