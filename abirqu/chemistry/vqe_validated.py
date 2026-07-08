"""
VQE Convergence Validation — H₂ Molecule
==========================================

Variational Quantum Eigensolver (VQE) convergence validation for the H₂
hydrogen molecule ground state energy. Uses exact statevector evaluation
(no sampling noise) with COBYLA optimizer and hardware-efficient ansatz.

Reference: H₂ FCI ground state at 0.74 Å ≈ −1.137 Ha.
Target: Chemical accuracy (< 0.0016 Ha error).
"""
import math
import numpy as np
from typing import List, Tuple, Optional

from abirqu import Circuit


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

# Build the full 4×4 Hamiltonian matrix
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

# FCI reference energy
FCI_ENERGY = -1.137270

# Chemical accuracy threshold (1 kcal/mol in Hartree)
CHEMICAL_ACCURACY = 0.0016


# ─────────────────────────────────────────────────────────────
# Statevector simulation
# ─────────────────────────────────────────────────────────────

def _get_statevector(circuit: Circuit) -> np.ndarray:
    """Simulate circuit and return exact statevector (no sampling noise)."""
    from abirqu.numpy_sim import NumPySimulator
    sim = NumPySimulator(num_qubits=circuit.num_qubits)
    sim.run_circuit(circuit)
    return sim.get_state_vector().copy()


def _energy_from_statevector(statevector: np.ndarray) -> float:
    """Compute <ψ|H|ψ> exactly from a statevector."""
    return float(np.real(statevector.conj() @ HAMILTONIAN @ statevector))


# ─────────────────────────────────────────────────────────────
# VQE ansatz
# ─────────────────────────────────────────────────────────────

def _make_vqe_circuit(params: List[float], n_qubits: int = 2) -> Circuit:
    """Build parameterised VQE circuit with RY rotations and CNOT entanglement.

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
# VQE optimisation
# ─────────────────────────────────────────────────────────────

def run_vqe_h2(
    n_qubits: int = 2,
    maxiter: int = 500,
    seed: int = 42,
    rhobeg: float = 0.5,
) -> Tuple[float, List[float], List[float]]:
    """
    Run VQE for H₂ molecule ground state energy.

    Uses COBYLA optimizer for faster convergence to chemical accuracy.
    Returns (best_energy, energy_history, param_history).

    Parameters
    ----------
    n_qubits : int
        Number of qubits (2 for STO-3G).
    maxiter : int
        Maximum optimizer iterations.
    seed : int
        Random seed for reproducibility.
    rhobeg : float
        Initial step size for COBYLA.

    Returns
    -------
    Tuple[float, List[float], List[float]]
        (best_energy, energy_history, parameter_history)
    """
    from scipy.optimize import minimize

    n_params = 3 * n_qubits  # 3 layers × n_qubits
    np.random.seed(seed)
    params = np.random.uniform(0, 2 * math.pi, n_params)

    energy_history = []
    param_history = []

    def cost_function(p):
        c = _make_vqe_circuit(list(p), n_qubits)
        sv = _get_statevector(c)
        energy = _energy_from_statevector(sv)
        energy_history.append(energy)
        param_history.append(list(p))
        return energy

    result = minimize(
        cost_function,
        params,
        method="COBYLA",
        options={"maxiter": maxiter, "rhobeg": rhobeg},
    )

    return result.fun, energy_history, param_history


def print_vqe_report(
    best_energy: float,
    energy_history: List[float],
    param_history: Optional[List[List[float]]] = None,
) -> bool:
    """Print VQE convergence report and return True if chemical accuracy achieved."""
    error = abs(best_energy - FCI_ENERGY)
    achieved = error < CHEMICAL_ACCURACY

    print(f"\n{'─'*50}")
    print(f"  VQE Convergence Report")
    print(f"{'─'*50}")
    print(f"  Best VQE energy   : {best_energy:.6f} Ha")
    print(f"  FCI reference     : {FCI_ENERGY:.6f} Ha")
    print(f"  Energy error      : {error:.6f} Ha")
    print(f"  Chemical accuracy : {'ACHIEVED ✓' if achieved else 'NOT achieved'}")
    print(f"  Target error      : < {CHEMICAL_ACCURACY} Ha (1 kcal/mol)")
    print(f"  Iterations        : {len(energy_history)}")
    print(f"{'─'*50}")

    if energy_history:
        print(f"\n  Convergence trajectory:")
        n = len(energy_history)
        checkpoints = [0, n // 4, n // 2, 3 * n // 4, n - 1]
        for i in checkpoints:
            e = energy_history[i]
            print(f"    Iter {i:4d}: {e:.6f} Ha (err: {abs(e - FCI_ENERGY):.6f})")

    print()
    return achieved


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AbirQu — VQE Convergence Validation")
    print("====================================")
    print("\nH₂ ground state FCI energy ≈ −1.137 Hartree (reference)\n")

    best_e, e_history, p_history = run_vqe_h2(n_qubits=2, maxiter=500)

    achieved = print_vqe_report(best_e, e_history, p_history)

    if achieved:
        print("  RESULT: VQE achieves chemical accuracy for H₂ molecule")
    else:
        print("  RESULT: VQE did not reach chemical accuracy — needs tuning")

    print("\nDone!")
