"""
Variational Quantum Eigensolver (VQE) — H₂ Molecule
=====================================================
VQE is a hybrid quantum-classical algorithm to find the ground-state energy
of a quantum Hamiltonian. Here we simulate the H₂ (hydrogen molecule)
ground state using a parameterised ansatz in the STO-3G basis with
Jordan-Wigner mapping.

The exact FCI ground state energy of H₂ at equilibrium (0.74 Å) is ≈ −1.137 Ha.
This implementation achieves < 0.002 Ha error.
"""
import math
import numpy as np
from typing import List, Tuple
from abirqu import Circuit
from abirqu.primitives import QuantumRun


# ─────────────────────────────────────────────────────────────
# H₂ Hamiltonian in STO-3G with Jordan-Wigner mapping (2 qubits)
# ─────────────────────────────────────────────────────────────

# Nuclear repulsion energy at R = 0.74 Å (1.398 Bohr)
_NUCLEAR_REPULSION = 1.0 / (0.74 / 0.52917721092)  # ≈ 0.7151 Ha

# Electronic Hamiltonian coefficients (from OpenFermion / Qiskit textbook)
# H_elec = g0_e*I + g1*Z0 + g2*Z1 + g3*Z0Z1 + g4*X0X1 + g5*Y0Y1
_G0_ELECTRONIC = -0.4804
_G1 = +0.3435
_G2 = -0.4347
_G3 = +0.5716
_G4 = +0.0910
_G5 = +0.0910

# Total constant term includes nuclear repulsion
_G0 = _G0_ELECTRONIC + _NUCLEAR_REPULSION

# Build the full 4×4 Hamiltonian matrix for exact expectation values
_I2 = np.eye(2, dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)

HAMILTONIAN = (
    _G0 * np.kron(_I2, _I2)
    + _G1 * np.kron(_Z, _I2)
    + _G2 * np.kron(_I2, _Z)
    + _G3 * np.kron(_Z, _Z)
    + _G4 * np.kron(_X, _X)
    + _G5 * np.kron(_Y, _Y)
)


def _get_statevector(circuit: Circuit) -> np.ndarray:
    """Simulate circuit and return exact statevector (no sampling noise)."""
    from abirqu.numpy_sim import NumPySimulator
    sim = NumPySimulator(num_qubits=circuit.num_qubits)
    sim.run_circuit(circuit)
    return sim.get_state_vector().copy()


def h2_energy_from_statevector(statevector: np.ndarray) -> float:
    """Compute <ψ|H|ψ> exactly from a statevector."""
    return float(np.real(statevector.conj() @ HAMILTONIAN @ statevector))


# ─────────────────────────────────────────────────────────────
# Parameterised ansatz (hardware-efficient, 3 layers)
# ─────────────────────────────────────────────────────────────

def make_vqe_circuit(params: List[float], n_qubits: int = 2) -> Circuit:
    """Build a parameterised VQE circuit with RY rotations and CNOT entanglement.

    Uses 3 layers of [RY on each qubit, CNOT chain] for sufficient
    expressiveness to reach chemical accuracy on the 2-qubit H₂ problem.
    """
    c = Circuit(n_qubits, name="vqe_ansatz")
    idx = 0
    for layer in range(3):
        for q in range(n_qubits):
            if idx < len(params):
                c.ry(q, params[idx])
                idx += 1
        for q in range(n_qubits - 1):
            c.cnot(q, q + 1)
    return c


# ─────────────────────────────────────────────────────────────
# VQE optimisation with scipy (COBYLA optimizer)
# ─────────────────────────────────────────────────────────────

def run_vqe(n_qubits: int = 2, iterations: int = 500) -> Tuple[float, List[float]]:
    """Run VQE using COBYLA optimizer for faster convergence to chemical accuracy."""
    from scipy.optimize import minimize

    n_params = 6  # 3 layers × 2 qubits
    np.random.seed(42)
    params = np.random.uniform(0, 2 * math.pi, n_params)

    energy_history = []

    def cost_function(p):
        c = make_vqe_circuit(list(p), n_qubits)
        sv = _get_statevector(c)
        energy = h2_energy_from_statevector(sv)
        energy_history.append(energy)
        return energy

    result = minimize(
        cost_function,
        params,
        method="COBYLA",
        options={"maxiter": iterations, "rhobeg": 0.5},
    )

    return result.fun, energy_history


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AbirQu — VQE for H₂ Molecule")
    print("==============================")
    print("\nH₂ ground state FCI energy ≈ −1.137 Hartree (reference)\n")

    best_e, history = run_vqe(n_qubits=2, iterations=500)

    fci_ref = -1.137270
    error = abs(best_e - fci_ref)

    print(f"\n{'─'*45}")
    print(f"  Best VQE energy  : {best_e:.6f} Ha")
    print(f"  FCI reference    : {fci_ref:.6f} Ha")
    print(f"  Energy error     : {error:.6f} Ha")
    print(f"  Chemical accuracy: {'YES ✓' if error < 0.0016 else 'NO (< 0.0016 Ha)'}")
    print(f"  VQE iterations   : {len(history)}")
    print(f"{'─'*45}")
    print("\nImprovements over original:")
    print("  • Correct Hamiltonian (nuclear repulsion in constant term)")
    print("  • Exact energy from statevector (no measurement sampling noise)")
    print("  • COBYLA optimizer (faster convergence than random perturbation)")
    print("  • 3-layer ansatz (6 params) for better expressiveness")
    print("\nDone! Try examples/qaoa_maxcut.py next.")
