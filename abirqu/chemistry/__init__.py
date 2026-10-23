"""
AbirQu Chemistry — Production Quantum Chemistry Module.

Fermion-to-qubit mappers, molecular Hamiltonian construction,
chemistry ansatzes, and classical-quantum integration hooks.

Supports:
- Jordan-Wigner, Bravyi-Kitaev, Parity transformations
- UCCSD (Unitary Coupled Cluster Singles and Doubles) ansatz
- PySCF / OpenFermion integration hooks
- Matchgate Shadows for rapid state tomography
"""
from .chemistry_integration import (
    MolecularData,
    OpenFermionHook,
    PySCFHook,
    run_molecular_vqe,
)
from .fermion_mappers import (
    BravyiKitaevMapper,
    FermionicOperator,
    JordanWignerMapper,
    ParityMapper,
    build_hamiltonian_from_integrals,
)
from .matchgate_shadows import MatchgateShadows

__all__ = [
    "JordanWignerMapper",
    "BravyiKitaevMapper",
    "ParityMapper",
    "FermionicOperator",
    "build_hamiltonian_from_integrals",
    "PySCFHook",
    "OpenFermionHook",
    "MolecularData",
    "run_molecular_vqe",
    "MatchgateShadows",
]
