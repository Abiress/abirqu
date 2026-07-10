"""
Classical Chemistry Integration Hooks.

Bridges AbirQu with classical quantum chemistry software:
- PySCF: Gaussian basis set calculations
- OpenFermion: Fermionic operator algebra

Workflow:
    1. Classical software defines the molecule (geometry, basis, charge)
    2. AbirQu compiles the quantum circuit
    3. AbirQu executes on simulator or real hardware
    4. Returns the energy landscape for optimization

References:
    - Sun et al. (2018): PySCF: the Python-based simulations of chemistry framework
    - McClean et al. (2020): OpenFermion: The Electronic Structure Package for
      Quantum Simulations
"""

import math
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field

import numpy as np

from .fermion_mappers import (
    JordanWignerMapper,
    BravyiKitaevMapper,
    ParityMapper,
    build_hamiltonian_from_integrals,
    PauliTerm,
)


@dataclass
class MolecularData:
    """
    Container for molecular data needed for quantum chemistry simulation.

    Attributes:
        name: Molecule name (e.g., "H2", "LiH", "H2O")
        atoms: List of (atomic_symbol, [x, y, z]) for each atom
        basis: Basis set name (e.g., "sto-3g", "6-31g", "cc-pvdz")
        charge: Total molecular charge
        multiplicity: Spin multiplicity (2S+1)
        n_electrons: Total number of electrons
        n_orbitals: Number of spatial orbitals (from basis set)
        one_electron_integrals: h_pq matrix (n_orbitals x n_orbitals)
        two_electron_integrals: h_pqrs tensor (n_orbitals^4)
        nuclear_repulsion: Nuclear repulsion energy
        classical_energy: Classical Hartree-Fock energy (if available)
        metadata: Additional metadata (source, method, etc.)
    """
    name: str = "H2"
    atoms: List[Tuple[str, List[float]]] = field(default_factory=lambda: [
        ("H", [0.0, 0.0, 0.0]),
        ("H", [0.0, 0.0, 0.74]),
    ])
    basis: str = "sto-3g"
    charge: int = 0
    multiplicity: int = 1
    n_electrons: int = 2
    n_orbitals: int = 2
    one_electron_integrals: Optional[np.ndarray] = None
    two_electron_integrals: Optional[np.ndarray] = None
    nuclear_repulsion: float = 0.7199689944499149
    classical_energy: float = -1.1372838361995019
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def n_qubits_jw(self) -> int:
        """Number of qubits for Jordan-Wigner mapping."""
        return self.n_orbitals

    @property
    def n_qubits_bk(self) -> int:
        """Number of qubits for Bravyi-Kitaev mapping."""
        return self.n_orbitals

    @property
    def n_qubits_parity(self) -> int:
        """Number of qubits for Parity mapping (with reduction)."""
        return self.n_orbitals - 1

    def get_hamiltonian(self, mapper: str = "jordan_wigner") -> Tuple[List[PauliTerm], int]:
        """
        Get the qubit Hamiltonian using specified mapper.

        Args:
            mapper: "jordan_wigner", "bravyi_kitaev", or "parity"

        Returns:
            (PauliTerm list, number of qubits)
        """
        if self.one_electron_integrals is None or self.two_electron_integrals is None:
            raise ValueError("Integrals not computed. Run classical calculation first.")

        return build_hamiltonian_from_integrals(
            self.one_electron_integrals,
            self.two_electron_integrals,
            self.n_electrons,
            mapper_type=mapper,
            nuclear_repulsion=self.nuclear_repulsion,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "atoms": self.atoms,
            "basis": self.basis,
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "n_electrons": self.n_electrons,
            "n_orbitals": self.n_orbitals,
            "nuclear_repulsion": self.nuclear_repulsion,
            "classical_energy": self.classical_energy,
            "metadata": self.metadata,
        }


class PySCFHook:
    """
    Integration hook for PySCF.

    If PySCF is installed, this runs the actual Hartree-Fock calculation
    and extracts integrals. If not, provides pre-computed integrals for
    common benchmark molecules.

    Usage:
        hook = PySCFHook()
        mol_data = hook.run_calculation("H2", basis="sto-3g")
        hamiltonian, n_qubits = mol_data.get_hamiltonian("jordan_wigner")
    """

    # Pre-computed integrals for benchmark molecules (sto-3g basis)
    BENCHMARK_MOLECULES = {
        "H2": {
            "n_electrons": 2,
            "n_orbitals": 2,
            "nuclear_repulsion": 0.7199689944499149,
            "classical_energy": -1.1372838361995019,
            "one_electron_integrals": np.array([
                [-1.25633907, 0.0],
                [0.0, -0.47189601],
            ]),
            "two_electron_integrals": np.array([
                [[
                    [0.67449252, 0.39948290],
                    [0.39948290, 0.69739833],
                ], [
                    [0.39948290, 0.18090259],
                    [0.18090259, 0.66347210],
                ]], [[
                    [0.39948290, 0.18090259],
                    [0.18090259, 0.66347210],
                ], [
                    [0.39948290, 0.69739833],
                    [0.69739833, 0.67449252],
                ]],
            ]),
        },
        "LiH": {
            "n_electrons": 4,
            "n_orbitals": 6,
            "nuclear_repulsion": 2.8293540399999998,
            "classical_energy": -7.882276573856126,
            "one_electron_integrals": np.array([
                [-3.42806408, -0.10193732, 0.0, 0.0, -0.06733755, 0.0],
                [-0.10193732, -0.79858341, 0.0, 0.0, -0.10033233, 0.0],
                [0.0, 0.0, -0.53679202, 0.0, 0.0, -0.10033233],
                [0.0, 0.0, 0.0, -0.53679202, 0.0, -0.10033233],
                [-0.06733755, -0.10033233, 0.0, 0.0, -0.38338754, 0.0],
                [0.0, 0.0, -0.10033233, -0.10033233, 0.0, -0.38338754],
            ]),
            "two_electron_integrals": None,  # Would be 6^4 tensor
        },
        "H2O": {
            "n_electrons": 10,
            "n_orbitals": 7,
            "nuclear_repulsion": 9.168588518152064,
            "classical_energy": -75.01497128979146,
            "one_electron_integrals": np.array([
                [-2.00254147e+01,  0.00000000e+00, -2.64758802e-01,
                  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                  0.00000000e+00],
                [0.00000000e+00, -2.00254147e+01,  0.00000000e+00,
                 -2.64758802e-01,  0.00000000e+00,  0.00000000e+00,
                 0.00000000e+00],
                [-2.64758802e-01,  0.00000000e+00, -4.03342262e+00,
                  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                  0.00000000e+00],
                [0.00000000e+00, -2.64758802e-01,  0.00000000e+00,
                 -4.03342262e+00,  0.00000000e+00,  0.00000000e+00,
                 0.00000000e+00],
                [0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                 0.00000000e+00, -3.80234470e+00,  0.00000000e+00,
                 0.00000000e+00],
                [0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                 0.00000000e+00,  0.00000000e+00, -3.80234470e+00,
                 0.00000000e+00],
                [0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                 0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                 -3.80234470e+00],
            ]),
            "two_electron_integrals": None,
        },
    }

    def __init__(self, pyscf_available: Optional[bool] = None):
        if pyscf_available is None:
            try:
                import pyscf
                self._pyscf = pyscf
                self._available = True
            except ImportError:
                self._pyscf = None
                self._available = False
        else:
            self._available = pyscf_available
            self._pyscf = None

    @property
    def available(self) -> bool:
        return self._available

    def run_calculation(
        self,
        molecule_name: str = None,
        atoms: List[Tuple[str, List[float]]] = None,
        basis: str = "sto-3g",
        charge: int = 0,
        multiplicity: int = 1,
        method: str = "rhf",
    ) -> MolecularData:
        """
        Run Hartree-Fock calculation and return MolecularData.

        If PySCF is available, runs the real calculation.
        Otherwise, uses pre-computed benchmark data.

        Args:
            molecule_name: Name of molecule (for benchmark lookup)
            atoms: List of (symbol, [x, y, z]) positions
            basis: Basis set name
            charge: Molecular charge
            multiplicity: Spin multiplicity
            method: SCF method ("rhf", "uhf", "rohf")

        Returns:
            MolecularData with computed integrals
        """
        if self._available and atoms is not None:
            return self._run_pyscf(atoms, basis, charge, multiplicity, method)
        elif molecule_name and molecule_name in self.BENCHMARK_MOLECULES:
            return self._load_benchmark(molecule_name)
        else:
            raise ValueError(
                f"Molecule '{molecule_name}' not in benchmark set. "
                f"Available: {list(self.BENCHMARK_MOLECULES.keys())}. "
                f"Or install PySCF and provide atoms list."
            )

    def _run_pyscf(self, atoms, basis, charge, multiplicity, method) -> MolecularData:
        """Run actual PySCF calculation."""
        mol = self._pyscf.gto.M()
        mol.atom = [(a, tuple(pos)) for a, pos in atoms]
        mol.basis = basis
        mol.charge = charge
        mol.spin = multiplicity - 1
        mol.build()

        if method == "rhf":
            mf = self._pyscf.scf.RHF(mol)
        elif method == "uhf":
            mf = self._pyscf.scf.UHF(mol)
        else:
            mf = self._pyscf.scf.RHF(mol)

        energy = mf.kernel()

        # Extract integrals
        h1e = mol.intor('int1e_kin') + mol.intor('int1e_nuc')
        h2e = mol.intor('int2e')

        return MolecularData(
            name=f"Molecule({len(atoms)} atoms)",
            atoms=atoms,
            basis=basis,
            charge=charge,
            multiplicity=multiplicity,
            n_electrons=mol.nelectron,
            n_orbitals=mol.nao_nr(),
            one_electron_integrals=h1e,
            two_electron_integrals=h2e,
            nuclear_repulsion=mol.energy_nuc(),
            classical_energy=energy,
            metadata={"method": method, "converged": mf.converged},
        )

    def _load_benchmark(self, name: str) -> MolecularData:
        """Load pre-computed benchmark data."""
        data = self.BENCHMARK_MOLECULES[name]
        return MolecularData(
            name=name,
            basis="sto-3g",
            n_electrons=data["n_electrons"],
            n_orbitals=data["n_orbitals"],
            one_electron_integrals=data["one_electron_integrals"],
            two_electron_integrals=data["two_electron_integrals"],
            nuclear_repulsion=data["nuclear_repulsion"],
            classical_energy=data["classical_energy"],
            metadata={"source": "benchmark", "method": "rhf"},
        )

    def compute_integrals(self, mol_data: MolecularData) -> MolecularData:
        """Recompute integrals for a MolecularData object."""
        if self._available:
            return self._run_pyscf(
                mol_data.atoms, mol_data.basis,
                mol_data.charge, mol_data.multiplicity, "rhf"
            )
        return mol_data


class OpenFermionHook:
    """
    Integration hook for OpenFermion.

    Converts between OpenFermion FermionOperator and AbirQu PauliTerm format.
    If OpenFermion is installed, provides bidirectional conversion.
    """

    def __init__(self):
        try:
            from openfermion import FermionOperator, QubitOperator
            self._of = __import__('openfermion')
            self._available = True
        except ImportError:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def from_openfermion_operator(self, of_operator) -> List[PauliTerm]:
        """
        Convert OpenFermion QubitOperator to AbirQu PauliTerm list.
        """
        if not self._available:
            raise ImportError("OpenFermion not installed")

        terms = []
        for term, coeff in of_operator.terms.items():
            paulis = ['I'] * max(term.keys()) if term else ['I']
            for qubit, pauli_char in term.items():
                paulis[qubit] = pauli_char.upper()
            terms.append(PauliTerm(complex(coeff), paulis))
        return terms

    def to_openfermion_operator(self, pauli_terms: List[PauliTerm]):
        """
        Convert AbirQu PauliTerm list to OpenFermion QubitOperator.
        """
        if not self._available:
            raise ImportError("OpenFermion not installed")

        qubit_op = self._of.QubitOperator()
        for pt in pauli_terms:
            term = ()
            for i, p in enumerate(pt.paulis):
                if p != 'I':
                    term += ((i, p.lower()),)
            qubit_op += self._of.QubitOperator(term, pt.coefficient)
        return qubit_op

    def from_fermion_operator(self, fermion_op) -> List[PauliTerm]:
        """
        Convert OpenFermion FermionOperator to AbirQu PauliTerm using JW mapping.
        """
        if not self._available:
            raise ImportError("OpenFermion not installed")

        # Use OpenFermion's built-in JW mapping
        qubit_op = self._of.jordan_wigner(fermion_op)
        return self.from_openfermion_operator(qubit_op)


def run_molecular_vqe(
    mol_data: MolecularData,
    ansatz: str = "uccsd",
    mapper: str = "jordan_wigner",
    optimizer: str = "cobyla",
    max_iterations: int = 100,
    shots: int = 4096,
) -> Dict[str, Any]:
    """
    Run a complete VQE calculation for a molecule.

    Uses scipy.optimize.minimize (COBYLA) with real circuit simulation
    via QuantumRun for energy evaluation.

    Args:
        mol_data: MolecularData with integrals
        ansatz: "uccsd" or "hardware_efficient"
        mapper: "jordan_wigner", "bravyi_kitaev", or "parity"
        optimizer: Classical optimizer name (cobyla, nelder_mead, powell)
        max_iterations: Maximum VQE iterations
        shots: Number of measurement shots

    Returns:
        Dictionary with:
            - "energy": Optimized ground state energy
            - "classical_energy": Hartree-Fock energy
            - "error": Chemical accuracy error
            - "n_qubits": Number of qubits used
            - "n_parameters": Number of ansatz parameters
            - "convergence": List of energies per iteration
            - "converged": Whether optimizer converged
    """
    from scipy.optimize import minimize as scipy_minimize

    # Ensure integrals are loaded
    if mol_data.one_electron_integrals is None:
        hook = PySCFHook(pyscf_available=False)
        mol_data = hook.run_calculation(mol_data.name)

    # Get Hamiltonian
    hamiltonian, n_qubits = mol_data.get_hamiltonian(mapper)

    # Import VQE ansatz from library
    from ..library.vqe_ansatz import vqe_uccsd, vqe_hardware_efficient

    if ansatz == "uccsd":
        circuit_fn = lambda params: vqe_uccsd(
            num_qubits=n_qubits,
            num_electrons=mol_data.n_electrons,
            parameters=params,
        )
        n_params = n_qubits * 4
    else:
        circuit_fn = lambda params: vqe_hardware_efficient(
            num_qubits=n_qubits,
            parameters=params,
        )
        n_params = n_qubits * 6

    convergence = []

    def objective(params):
        energy = _evaluate_energy(params, hamiltonian, n_qubits, circuit_fn, shots)
        convergence.append(float(energy))
        return energy

    # Initial parameters
    x0 = np.random.uniform(-np.pi, np.pi, n_params)

    # Run VQE with scipy optimizer
    opt_result = scipy_minimize(
        objective,
        x0,
        method=optimizer.upper() if optimizer.upper() in ('COBYLA', 'NELDER_MEAD', 'POWELL') else 'COBYLA',
        options={
            'maxiter': max_iterations,
            'rhobeg': 0.5,
            'tol': 1e-6,
        },
    )

    best_energy = opt_result.fun
    best_params = opt_result.x

    return {
        "energy": float(best_energy),
        "classical_energy": mol_data.classical_energy,
        "error": abs(float(best_energy) - mol_data.classical_energy),
        "n_qubits": n_qubits,
        "n_parameters": n_params,
        "convergence": convergence,
        "mapper": mapper,
        "ansatz": ansatz,
        "converged": opt_result.success,
        "optimizer": opt_result.message,
    }


def _evaluate_energy(params, hamiltonian, n_qubits, circuit_fn, shots=1024):
    """Evaluate energy expectation value <ψ|H|ψ> for given parameters.

    Uses real quantum circuit simulation via QuantumRun.
    """
    from ..primitives.quantum_run import QuantumRun

    # Build parameterized circuit
    circuit = circuit_fn(params)

    # Run circuit to get statevector
    qr = QuantumRun(circuits=circuit, shots=shots)
    result = qr[0]

    # Get statevector for exact expectation values
    sv = result.statevector
    if sv is None:
        # Fallback: use counts to estimate expectations
        counts = result.counts
        total = sum(counts.values()) if counts else 1
        sv = np.zeros(2**n_qubits, dtype=complex)
        for bitstring, count in counts.items():
            idx = int(bitstring, 2)
            sv[idx] = np.sqrt(count / total)

    # Compute <ψ|H|ψ> exactly
    total_energy = 0.0
    for term in hamiltonian:
        if all(p == 'I' for p in term.paulis):
            total_energy += term.coefficient.real
            continue

        # Build Pauli matrix for this term
        pauli_matrix = np.array([[1.0]], dtype=complex)
        for p in term.paulis:
            if p == 'I':
                pauli_matrix = np.kron(pauli_matrix, np.eye(2, dtype=complex))
            elif p == 'X':
                pauli_matrix = np.kron(pauli_matrix, np.array([[0, 1], [1, 0]], dtype=complex))
            elif p == 'Y':
                pauli_matrix = np.kron(pauli_matrix, np.array([[0, -1j], [1j, 0]], dtype=complex))
            elif p == 'Z':
                pauli_matrix = np.kron(pauli_matrix, np.array([[1, 0], [0, -1]], dtype=complex))

        # <ψ|P|ψ> = sv† · P · sv
        expectation = np.real(np.conj(sv) @ pauli_matrix @ sv)
        total_energy += term.coefficient.real * expectation

    return total_energy
