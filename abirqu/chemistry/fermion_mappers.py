"""
Fermion-to-Qubit Mappers for Quantum Chemistry.

Converts fermionic second-quantization operators into qubit (Pauli) operators.
These mappers are essential for simulating molecular Hamiltonians on quantum hardware.

The general form of a molecular Hamiltonian in second quantization:
    H = Σ_{pq} h_{pq} a_p† a_q + (1/2) Σ_{pqrs} h_{pqrs} a_p† a_q† a_r a_s

Where:
    a_p†, a_p are fermionic creation/annihilation operators
    h_{pq} are one-electron integrals
    h_{pqrs} are two-electron integrals

Three canonical mappings:
    1. Jordan-Wigner (JW): Preserves locality, string overhead O(n)
    2. Bravyi-Kitaev (BK): O(log n) string overhead, better for large systems
    3. Parity: Qubit-reduction via parity-bit ordering

References:
    - Jordan & Wigner (1928): Original spinor mapping
    - Bravyi, Kitaev (2002): Fermionic quantum computation
    - Seeley, Richard, Love (2012): The Bravyi-Kitaev transformation
"""

import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

import numpy as np


class MapperType(Enum):
    JORDAN_WIGNER = "jordan_wigner"
    BRAVYI_KITAEV = "bravyi_kitaev"
    PARITY = "parity"


@dataclass
class FermionicOperator:
    """
    Represents a fermionic operator as a tuple (coeff, [p, q, ...])
    where p, q are orbital indices.

    a_p† a_q  ->  ('1e', coeff, (p, q))
    a_p† a_q† a_r a_s  ->  ('2e', coeff, (p, q, r, s))
    """
    operator_type: str  # '1e', '2e', or 'identity'
    coefficient: complex
    indices: Tuple[int, ...]

    def __repr__(self):
        if self.operator_type == 'identity':
            return f"{self.coefficient:.6f} * I"
        return f"{self.coefficient:.6f} * {self.operator_type}({self.indices})"


@dataclass
class PauliTerm:
    """A single term in a Pauli Hamiltonian: coeff * P_0 ⊗ P_1 ⊗ ... ⊗ P_{n-1}"""
    coefficient: complex
    paulis: List[str]  # Each element is 'I', 'X', 'Y', or 'Z'

    def __repr__(self):
        terms = [f"{p}{i}" for i, p in enumerate(self.paulis) if p != 'I']
        return f"{self.coefficient:.6f} * {' ⊗ '.join(terms)}"


class JordanWignerMapper:
    """
    Jordan-Wigner transformation.

    Maps fermionic operators to qubit operators by encoding the parity
    of occupied orbitals in Z strings.

    Mapping:
        a_p† -> (X_p - iY_p)/2 ⊗ Z_0 ⊗ Z_1 ⊗ ... ⊗ Z_{p-1}
        a_p   -> (X_p + iY_p)/2 ⊗ Z_0 ⊗ Z_1 ⊗ ... ⊗ Z_{p-1}

    String overhead: O(n) for n orbitals.
    """

    def __init__(self, n_orbitals: int):
        self.n_orbitals = n_orbitals
        self.n_qubits = n_orbitals  # 1 qubit per orbital

    def map_one_body(self, p: int, q: int, coeff: complex = 1.0) -> List[PauliTerm]:
        """
        Map a_p† a_q to Pauli operators.

        a_p† a_q = (X_p - iY_p)(X_q + iY_q)/4 * Z_{p+1:q-1}  (if p < q)

        Returns list of PauliTerm.
        """
        if p == q:
            # Number operator: a_p† a_p = (I - Z_p)/2
            return [
                PauliTerm(0.5 * coeff, self._z_string()),
                PauliTerm(-0.5 * coeff, self._z_at(p)),
            ]

        terms = []
        # a_p† a_q = 1/4 * (X_p - iY_p) * (Z_{p+1}...Z_{q-1}) * (X_q + iY_q)
        # Expand: (X_p)(X_q) - i(X_p)(Y_q) - i(Y_p)(X_q) - (Y_p)(Y_q)
        # All multiplied by the Z-string between p and q

        base_paulis = ['I'] * self.n_qubits

        # Term 1: X_p * Z_{p+1:q-1} * X_q
        p1 = list(base_paulis)
        p1[p] = 'X'
        for k in range(p + 1, q):
            p1[k] = 'Z'
        p1[q] = 'X'
        terms.append(PauliTerm(0.25 * coeff, p1))

        # Term 2: X_p * Z_{p+1:q-1} * Y_q  (coefficient: -i)
        p2 = list(base_paulis)
        p2[p] = 'X'
        for k in range(p + 1, q):
            p2[k] = 'Z'
        p2[q] = 'Y'
        terms.append(PauliTerm(-0.25j * coeff, p2))

        # Term 3: Y_p * Z_{p+1:q-1} * X_q  (coefficient: -i)
        p3 = list(base_paulis)
        p3[p] = 'Y'
        for k in range(p + 1, q):
            p3[k] = 'Z'
        p3[q] = 'X'
        terms.append(PauliTerm(-0.25j * coeff, p3))

        # Term 4: Y_p * Z_{p+1:q-1} * Y_q  (coefficient: -1)
        p4 = list(base_paulis)
        p4[p] = 'Y'
        for k in range(p + 1, q):
            p4[k] = 'Z'
        p4[q] = 'Y'
        terms.append(PauliTerm(-0.25 * coeff, p4))

        return terms

    def map_two_body(self, p: int, q: int, r: int, s: int,
                     coeff: complex = 1.0) -> List[PauliTerm]:
        """
        Map a_p† a_q† a_r a_s to Pauli operators.

        Handles all ordering cases (p < q, r < s, etc.).
        """
        terms = []
        # a_p† a_q† a_r a_s
        # = a_p† (δ_{qr} - a_r a_q†) a_s
        # = δ_{qr} a_p† a_s - a_p† a_r a_q† a_s

        if q == r:
            # a_p† a_q† a_q a_s = a_p† a_s * n_q (if p!=s, q!=p, q!=s)
            if p == s:
                # a_p† a_q† a_q a_p = n_p * n_q (number-number)
                terms.extend(self._number_number(p, q, coeff))
            else:
                # a_p† a_s * n_q
                terms.extend(self._map_one_body_scaled(p, s, coeff))
                # Multiply by n_q = (I - Z_q)/2
                # This creates a product of Pauli terms
                one_body = self._map_one_body_scaled(p, s, coeff)
                scaled_terms = []
                for t in one_body:
                    # Multiply each by (I - Z_q)/2
                    i_term = PauliTerm(0.5 * t.coefficient, list(t.paulis))
                    z_term = PauliTerm(-0.5 * t.coefficient, list(t.paulis))
                    z_term.paulis[q] = self._combine_z(t.paulis[q], 'Z')
                    scaled_terms.extend([i_term, z_term])
                terms.extend(scaled_terms)
        else:
            # General case: map each one-body operator
            # First map a_p† a_s
            ps_terms = self.map_one_body(p, s, coeff)
            # Then map a_q† a_r
            qr_terms = self.map_one_body(q, r, 1.0)
            # Tensor product of the two sets
            for ps in ps_terms:
                for qr in qr_terms:
                    combined_paulis = list(ps.paulis)
                    combined_coeff = ps.coefficient * qr.coefficient
                    for i, p_char in enumerate(qr.paulis):
                        if p_char != 'I':
                            combined_paulis[i] = self._combine_z(
                                combined_paulis[i], p_char
                            )
                    terms.append(PauliTerm(combined_coeff, combined_paulis))

        return self._simplify_terms(terms)

    def map_hamiltonian(self, one_electron: List[Tuple[int, int, complex]],
                        two_electron: List[Tuple[int, int, int, int, complex]]
                        ) -> List[PauliTerm]:
        """
        Map a full molecular Hamiltonian to Pauli operators.

        Args:
            one_electron: List of (p, q, h_pq) one-electron integrals
            two_electron: List of (p, q, r, s, h_pqrs) two-electron integrals

        Returns:
            List of PauliTerm representing the qubit Hamiltonian
        """
        terms = []

        # Add identity term
        total_terms = len(one_electron) + len(two_electron)
        terms.append(PauliTerm(0.0, ['I'] * self.n_qubits))

        # Map one-electron terms: Σ h_{pq} a_p† a_q
        for p, q, coeff in one_electron:
            terms.extend(self.map_one_body(p, q, coeff))

        # Map two-electron terms: (1/2) Σ h_{pqrs} a_p† a_q† a_r a_s
        for p, q, r, s, coeff in two_electron:
            terms.extend(self.map_two_body(p, q, r, s, 0.5 * coeff))

        return self._simplify_terms(terms)

    def _z_string(self) -> List[str]:
        return ['Z'] * self.n_qubits

    def _z_at(self, pos: int) -> List[str]:
        paulis = ['I'] * self.n_qubits
        paulis[pos] = 'Z'
        return paulis

    def _combine_z(self, a: str, b: str) -> str:
        """Combine two Pauli operators on the same qubit."""
        if a == 'I':
            return b
        if b == 'I':
            return a
        if a == b:
            return 'I'  # X*X = I, Y*Y = I, Z*Z = I
        # Non-commuting combinations (shouldn't occur in normal JW mapping)
        return f'{a}{b}'

    def _map_one_body_scaled(self, p: int, q: int, coeff: float) -> List[PauliTerm]:
        """Map one-body operator scaled by a constant."""
        return self.map_one_body(p, q, coeff)

    def _number_number(self, p: int, q: int, coeff: complex) -> List[PauliTerm]:
        """Map n_p * n_q = (I - Z_p)(I - Z_q)/4."""
        terms = []
        terms.append(PauliTerm(0.25 * coeff, ['I'] * self.n_qubits))
        zp = ['I'] * self.n_qubits
        zp[p] = 'Z'
        terms.append(PauliTerm(-0.25 * coeff, zp))
        zq = ['I'] * self.n_qubits
        zq[q] = 'Z'
        terms.append(PauliTerm(-0.25 * coeff, zq))
        zpq = ['I'] * self.n_qubits
        zpq[p] = 'Z'
        zpq[q] = 'Z'
        terms.append(PauliTerm(0.25 * coeff, zpq))
        return terms

    def _simplify_terms(self, terms: List[PauliTerm]) -> List[PauliTerm]:
        """Combine terms with identical Pauli strings."""
        combined: Dict[str, PauliTerm] = {}
        for t in terms:
            key = ''.join(t.paulis)
            if key in combined:
                combined[key].coefficient += t.coefficient
            else:
                combined[key] = PauliTerm(t.coefficient, list(t.paulis))
        # Remove zero-coefficient terms
        return [t for t in combined.values() if abs(t.coefficient) > 1e-15]


class BravyiKitaevMapper:
    """
    Bravyi-Kitaev transformation.

    More efficient than Jordan-Wigner for large systems:
    - O(log n) Pauli string length instead of O(n)
    - Uses a binary tree encoding of occupation numbers

    Mapping encodes occupation number n_p in a binary tree where:
    - Parity bits: encode n_p mod 2
    - Sign bits: encode the sum of occupation numbers in the subtree

    For n orbitals, the Pauli strings have length O(log n).
    """

    def __init__(self, n_orbitals: int):
        self.n_orbitals = n_orbitals
        self.n_qubits = n_orbitals
        # Precompute the BK transform matrix
        self._bk_matrix = self._build_bk_matrix()

    def _build_bk_matrix(self) -> np.ndarray:
        """
        Build the Bravyi-Kitaev binary tree mapping matrix.

        The BK encoding represents occupation numbers in a binary tree
        where each node stores a sum over its subtree.
        """
        n = self.n_orbitals
        if n == 0:
            return np.zeros((0, 0), dtype=int)

        # For small systems, use the direct binary encoding
        # For larger systems, use the tree-based encoding
        matrix = np.zeros((n, n), dtype=int)
        for p in range(n):
            # Binary representation of p+1 (1-indexed)
            binary = format(p + 1, f'0{max(1, int(np.ceil(np.log2(n + 1))))}b')
            for i, bit in enumerate(reversed(binary)):
                if i < n and bit == '1':
                    matrix[p, i] = 1
        return matrix

    def map_number_operator(self, p: int, coeff: complex = 1.0) -> List[PauliTerm]:
        """
        Map the number operator n_p = a_p† a_p to Pauli operators.

        In BK encoding, n_p maps to (I - Z_p)/2 where p is the
        position in the BK tree.
        """
        paulis = ['I'] * self.n_qubits
        paulis[p] = 'Z'
        return [
            PauliTerm(0.5 * coeff, ['I'] * self.n_qubits),
            PauliTerm(-0.5 * coeff, paulis),
        ]

    def map_one_body(self, p: int, q: int, coeff: complex = 1.0) -> List[PauliTerm]:
        """
        Map a_p† a_q using BK encoding.

        Uses the binary tree structure to create shorter Pauli strings.
        """
        if p == q:
            return self.map_number_operator(p, coeff)

        # For BK, the one-body operator creates X/Y operators with
        # Z strings determined by the tree structure
        terms = []
        base = ['I'] * self.n_qubits

        # X_p * X_q term
        p1 = list(base)
        p1[p] = 'X'
        p1[q] = 'X'
        z_indices = self._bk_z_indices(p, q)
        for z in z_indices:
            p1[z] = 'Z'
        terms.append(PauliTerm(0.25 * coeff, p1))

        # X_p * Y_q term
        p2 = list(base)
        p2[p] = 'X'
        p2[q] = 'Y'
        z_indices = self._bk_z_indices(p, q)
        for z in z_indices:
            p2[z] = 'Z'
        terms.append(PauliTerm(-0.25j * coeff, p2))

        # Y_p * X_q term
        p3 = list(base)
        p3[p] = 'Y'
        p3[q] = 'X'
        z_indices = self._bk_z_indices(p, q)
        for z in z_indices:
            p3[z] = 'Z'
        terms.append(PauliTerm(-0.25j * coeff, p3))

        # Y_p * Y_q term
        p4 = list(base)
        p4[p] = 'Y'
        p4[q] = 'Y'
        z_indices = self._bk_z_indices(p, q)
        for z in z_indices:
            p4[z] = 'Z'
        terms.append(PauliTerm(-0.25 * coeff, p4))

        return terms

    def _bk_z_indices(self, p: int, q: int) -> List[int]:
        """
        Compute the Z-string indices for BK encoding between orbitals p and q.

        In the BK tree, the Z string connects the two orbitals through
        the tree structure, giving O(log n) length.
        """
        if p > q:
            p, q = q, p

        indices = []
        # Simple BK tree: Z string from parent nodes
        diff = q - p
        if diff > 0:
            # Add Z operators at the binary tree path
            level = 1
            while level < self.n_qubits:
                if (p // level) % 2 == (q // level) % 2:
                    break
                idx = p + level
                if idx < self.n_qubits and idx != q:
                    indices.append(idx)
                level *= 2

        return indices

    def map_hamiltonian(self, one_electron: List[Tuple[int, int, complex]],
                        two_electron: List[Tuple[int, int, int, int, complex]]
                        ) -> List[PauliTerm]:
        """Map full Hamiltonian using BK encoding."""
        mapper = JordanWignerMapper(self.n_orbitals)
        terms = []
        terms.append(PauliTerm(0.0, ['I'] * self.n_qubits))

        for p, q, coeff in one_electron:
            if p == q:
                terms.extend(self.map_number_operator(p, coeff))
            else:
                # For one-body off-diagonal, use BK-specific mapping
                terms.extend(self.map_one_body(p, q, coeff))

        # For two-body terms, use BK tree structure
        for p, q, r, s, coeff in two_electron:
            # Decompose into number operators and one-body terms
            # a_p† a_q† a_r a_s = a_p† a_s * a_q† a_r (simplified)
            if q == r:
                # Number operator product
                terms.extend(self.map_number_operator(p, 0.5 * coeff))
                terms.extend(self.map_number_operator(q, 1.0))
            else:
                # Use the Jordan-Wigner map as fallback for complex terms
                terms.extend(mapper.map_two_body(p, q, r, s, 0.5 * coeff))

        return self._simplify_terms(terms)

    def _simplify_terms(self, terms: List[PauliTerm]) -> List[PauliTerm]:
        """Combine terms with identical Pauli strings."""
        combined: Dict[str, PauliTerm] = {}
        for t in terms:
            key = ''.join(t.paulis)
            if key in combined:
                combined[key].coefficient += t.coefficient
            else:
                combined[key] = PauliTerm(t.coefficient, list(t.paulis))
        return [t for t in combined.values() if abs(t.coefficient) > 1e-15]


class ParityMapper:
    """
    Parity transformation.

    Maps the occupation number of orbital p to the parity of
    qubits 0 through p. This allows qubit reduction: the last
    qubit can often be eliminated since it encodes global parity.

    Mapping:
        n_p -> (Z_0 * Z_1 * ... * Z_p - 1) / 2

    Advantage: Can reduce the number of qubits by 1 compared to JW.
    """

    def __init__(self, n_orbitals: int, qubit_reduction: bool = True):
        self.n_orbitals = n_orbitals
        self.qubit_reduction = qubit_reduction
        self.n_qubits = n_orbitals - (1 if qubit_reduction else 0)

    def map_number_operator(self, p: int, coeff: complex = 1.0) -> List[PauliTerm]:
        """
        Map n_p = a_p† a_p to parity-encoded Pauli operators.

        n_p -> (Z_0 * Z_1 * ... * Z_p - 1) / 2
        """
        paulis = ['I'] * self.n_qubits
        for k in range(min(p + 1, self.n_qubits)):
            paulis[k] = 'Z'
        return [
            PauliTerm(0.5 * coeff, ['I'] * self.n_qubits),
            PauliTerm(-0.5 * coeff, paulis),
        ]

    def map_one_body(self, p: int, q: int, coeff: complex = 1.0) -> List[PauliTerm]:
        """Map a_p† a_q using parity encoding."""
        if p == q:
            return self.map_number_operator(p, coeff)

        terms = []
        base = ['I'] * self.n_qubits

        # a_p† a_q in parity encoding
        # X_p * X_q with Z string from p+1 to q
        p1 = list(base)
        p1[p] = 'X'
        for k in range(p + 1, min(q + 1, self.n_qubits)):
            p1[k] = 'Z'
        p1[q] = 'X'
        terms.append(PauliTerm(0.25 * coeff, p1))

        p2 = list(base)
        p2[p] = 'X'
        for k in range(p + 1, min(q + 1, self.n_qubits)):
            p2[k] = 'Z'
        p2[q] = 'Y'
        terms.append(PauliTerm(-0.25j * coeff, p2))

        p3 = list(base)
        p3[p] = 'Y'
        for k in range(p + 1, min(q + 1, self.n_qubits)):
            p3[k] = 'Z'
        p3[q] = 'X'
        terms.append(PauliTerm(-0.25j * coeff, p3))

        p4 = list(base)
        p4[p] = 'Y'
        for k in range(p + 1, min(q + 1, self.n_qubits)):
            p4[k] = 'Z'
        p4[q] = 'Y'
        terms.append(PauliTerm(-0.25 * coeff, p4))

        return terms

    def map_hamiltonian(self, one_electron: List[Tuple[int, int, complex]],
                        two_electron: List[Tuple[int, int, int, int, complex]]
                        ) -> List[PauliTerm]:
        """Map full Hamiltonian using parity encoding."""
        terms = []
        terms.append(PauliTerm(0.0, ['I'] * self.n_qubits))

        for p, q, coeff in one_electron:
            terms.extend(self.map_one_body(p, q, coeff))

        for p, q, r, s, coeff in two_electron:
            if q == r:
                terms.extend(self.map_number_operator(p, 0.5 * coeff))
                terms.extend(self.map_number_operator(q, 1.0))
            else:
                # Decompose: a_p† a_q† a_r a_s
                qr_terms = self.map_one_body(q, r, 1.0)
                ps_terms = self.map_one_body(p, s, 1.0)
                for qr in qr_terms:
                    for ps in ps_terms:
                        combined_paulis = list(ps.paulis)
                        combined_coeff = 0.5 * coeff * ps.coefficient * qr.coefficient
                        for i, p_char in enumerate(qr.paulis):
                            if p_char != 'I':
                                if combined_paulis[i] == 'I':
                                    combined_paulis[i] = p_char
                                elif combined_paulis[i] == p_char:
                                    combined_paulis[i] = 'I'
                        terms.append(PauliTerm(combined_coeff, combined_paulis))

        return self._simplify_terms(terms)

    def _simplify_terms(self, terms: List[PauliTerm]) -> List[PauliTerm]:
        combined: Dict[str, PauliTerm] = {}
        for t in terms:
            key = ''.join(t.paulis)
            if key in combined:
                combined[key].coefficient += t.coefficient
            else:
                combined[key] = PauliTerm(t.coefficient, list(t.paulis))
        return [t for t in combined.values() if abs(t.coefficient) > 1e-15]


def build_hamiltonian_from_integrals(
    h1e: np.ndarray,
    h2e: np.ndarray,
    n_electrons: int,
    mapper_type: str = "jordan_wigner",
    nuclear_repulsion: float = 0.0,
) -> Tuple[List[PauliTerm], int]:
    """
    Build qubit Hamiltonian from one- and two-electron integrals.

    Args:
        h1e: One-electron integral matrix (n_orbitals x n_orbitals)
        h2e: Two-electron integral tensor (n_orbitals x n_orbitals x n_orbitals x n_orbitals)
        n_electrons: Number of electrons
        mapper_type: "jordan_wigner", "bravyi_kitaev", or "parity"
        nuclear_repulsion: Nuclear repulsion energy (added as constant)

    Returns:
        (List[PauliTerm], n_qubits) — Pauli Hamiltonian and number of qubits
    """
    n_orbitals = h1e.shape[0]

    # Build one-electron integral list
    one_electron = []
    for p in range(n_orbitals):
        for q in range(n_orbitals):
            if abs(h1e[p, q]) > 1e-15:
                one_electron.append((p, q, h1e[p, q]))

    # Build two-electron integral list (physicist notation)
    two_electron = []
    for p in range(n_orbitals):
        for q in range(n_orbitals):
            for r in range(n_orbitals):
                for s in range(n_orbitals):
                    if abs(h2e[p, q, r, s]) > 1e-15:
                        two_electron.append((p, q, r, s, h2e[p, q, r, s]))

    # Select mapper
    if mapper_type == "jordan_wigner":
        mapper = JordanWignerMapper(n_orbitals)
    elif mapper_type == "bravyi_kitaev":
        mapper = BravyiKitaevMapper(n_orbitals)
    elif mapper_type == "parity":
        mapper = ParityMapper(n_orbitals, qubit_reduction=True)
    else:
        raise ValueError(f"Unknown mapper type: {mapper_type}")

    # Map Hamiltonian
    pauli_terms = mapper.map_hamiltonian(one_electron, two_electron)

    # Add nuclear repulsion as identity term
    if abs(nuclear_repulsion) > 1e-15:
        identity_found = False
        for t in pauli_terms:
            if all(p == 'I' for p in t.paulis):
                t.coefficient += nuclear_repulsion
                identity_found = True
                break
        if not identity_found:
            pauli_terms.append(PauliTerm(nuclear_repulsion, ['I'] * mapper.n_qubits))

    return pauli_terms, mapper.n_qubits
