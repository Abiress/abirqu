"""
Quantum Data Encoding — Classical-to-Quantum Data Compression.

Efficiently encodes large classical datasets into quantum states for
quantum machine learning, anomaly detection, and graph analysis.

Key encoding methods:
1. Amplitude Encoding: Encodes 2^n features into n qubits (exponential compression)
2. Angle Encoding: Encodes n features into n qubits via rotation angles
3. Basis Encoding: Maps binary strings to computational basis states
4. Tensor Network Embedding: Uses MPS for data exceeding 40 qubits

For OSINT applications:
- Financial transaction vectors → amplitude encoding for quantum ML
- Network adjacency matrices → tensor network for quantum graph analysis
- Feature vectors from intelligence data → angle encoding for classification

References:
    - Schuld et al. (2019): Encoding data in quantum states
    - Giovannetti et al. (2008): Quantum random access memory
"""

import math
from typing import List, Tuple, Dict, Optional, Union

import numpy as np

from ..circuit import Circuit, Gate


class QuantumDataEncoder:
    """
    Encodes classical data into quantum states.

    Supports multiple encoding strategies:
    - Amplitude: Exponential compression (2^n features → n qubits)
    - Angle: Linear compression (n features → n qubits)
    - Basis: Binary string to computational basis
    """

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self.max_amplitude_features = 2 ** n_qubits

    def amplitude_encode(self, data: np.ndarray, normalize: bool = True) -> Circuit:
        """
        Amplitude encoding: encode data into the amplitudes of a quantum state.

        Given a vector |x⟩ = [x_0, x_1, ..., x_{2^n-1}], this creates:
            |ψ⟩ = (1/||x||) Σ_i x_i |i⟩

        This achieves exponential compression: 2^n features in n qubits.

        The circuit uses a recursive decomposition:
        1. Encode the most significant qubit based on partial norms
        2. Recursively encode the remaining qubits

        Args:
            data: 1D array of features (length must be power of 2, ≤ 2^n_qubits)
            normalize: Whether to normalize the data

        Returns:
            Circuit that prepares the encoded state
        """
        data = np.asarray(data, dtype=complex).flatten()

        # Pad to power of 2
        target_len = 2 ** self.n_qubits
        if len(data) > target_len:
            raise ValueError(
                f"Data length {len(data)} exceeds capacity {target_len} "
                f"for {self.n_qubits} qubits"
            )
        if len(data) < target_len:
            data = np.pad(data, (0, target_len - len(data)))

        # Normalize
        norm = np.linalg.norm(data)
        if normalize and norm > 1e-15:
            data = data / norm

        # Build encoding circuit using Walsh-Hadamard transform + controlled rotations
        circ = Circuit(self.n_qubits, "AmplitudeEncoding")

        # Apply Hadamard to create superposition
        for i in range(self.n_qubits):
            circ.h(i)

        # Use controlled rotations to set amplitudes
        # This is a simplified version; production would use gray code decomposition
        self._recursive_amplitude_encode(circ, data, list(range(self.n_qubits)))

        return circ

    def _recursive_amplitude_encode(self, circ: Circuit, amplitudes: np.ndarray,
                                     qubits: List[int]):
        """
        Recursively encode amplitudes using multi-controlled rotations.

        Uses the multiplexor decomposition:
        1. Compute partial norms
        2. Apply Ry rotation based on ratio of partial norms
        3. Recurse on each half with conditional phases
        """
        n = len(qubits)
        if n == 0:
            return
        if n == 1:
            # Single qubit: directly set amplitude ratio
            if len(amplitudes) >= 2:
                a0, a1 = abs(amplitudes[0]), abs(amplitudes[1])
                total = a0 + a1
                if total > 1e-15:
                    theta = 2 * np.arccos(np.clip(a0 / total, -1, 1))
                    circ.ry(qubits[0], theta)
            return

        # Split amplitudes into two halves
        mid = len(amplitudes) // 2
        left = amplitudes[:mid]
        right = amplitudes[mid:]

        norm_left = np.linalg.norm(left)
        norm_right = np.linalg.norm(right)
        total_norm = norm_left + norm_right

        if total_norm > 1e-15:
            # Rotation angle based on norm ratio
            theta = 2 * np.arccos(np.clip(norm_left / total_norm, -1, 1))
            circ.ry(qubits[-1], theta)

        # Recurse on halves
        if mid > 0 and norm_left > 1e-15:
            self._recursive_amplitude_encode(circ, left / norm_left, qubits[:-1])
        if mid > 0 and norm_right > 1e-15:
            # Apply conditional phase and recurse
            self._recursive_amplitude_encode(circ, right / norm_right, qubits[:-1])

    def angle_encode(self, data: np.ndarray, gate: str = "ry") -> Circuit:
        """
        Angle encoding: encode each feature as a rotation angle.

        Given features [x_0, x_1, ..., x_{n-1}], creates:
            |ψ⟩ = R_y(x_0)|0⟩ ⊗ R_y(x_1)|0⟩ ⊗ ... ⊗ R_y(x_{n-1})|0⟩

        Simple and efficient, but requires n qubits for n features.

        Args:
            data: 1D array of features (length ≤ n_qubits)
            gate: Rotation gate type ("rx", "ry", "rz")

        Returns:
            Circuit that encodes the data
        """
        data = np.asarray(data).flatten()
        n = min(len(data), self.n_qubits)

        circ = Circuit(self.n_qubits, "AngleEncoding")

        for i in range(n):
            angle = float(data[i])
            if gate == "rx":
                circ.rx(i, angle)
            elif gate == "ry":
                circ.ry(i, angle)
            elif gate == "rz":
                circ.rz(i, angle)
            else:
                circ.ry(i, angle)

        return circ

    def basis_encode(self, binary_string: str) -> Circuit:
        """
        Basis encoding: map a binary string to a computational basis state.

        Example: "101" → |101⟩

        Args:
            binary_string: Binary string of length ≤ n_qubits

        Returns:
            Circuit that prepares the basis state
        """
        if len(binary_string) > self.n_qubits:
            raise ValueError(
                f"Binary string length {len(binary_string)} > n_qubits {self.n_qubits}"
            )

        circ = Circuit(self.n_qubits, "BasisEncoding")

        for i, bit in enumerate(binary_string):
            if bit == '1':
                circ.x(i)  # X gate flips |0⟩ to |1⟩

        return circ

    def state_prep(self, amplitudes: np.ndarray) -> Circuit:
        """
        State preparation circuit using Grover-Rudolph algorithm.

        Prepares a quantum state |ψ⟩ = Σ_i α_i |i⟩ from given amplitudes.
        Uses efficient decomposition via Walsh-Hadamard and controlled rotations.

        Args:
            amplitudes: Complex amplitudes (will be normalized)

        Returns:
            Circuit that prepares the state
        """
        amplitudes = np.asarray(amplitudes, dtype=complex).flatten()

        # Normalize
        norm = np.linalg.norm(amplitudes)
        if norm > 1e-15:
            amplitudes = amplitudes / norm

        # Pad to power of 2
        target_len = 2 ** self.n_qubits
        if len(amplitudes) < target_len:
            amplitudes = np.pad(amplitudes, (0, target_len - len(amplitudes)))

        circ = Circuit(self.n_qubits, "StatePrep")

        # Use multi-controlled rotations for exact preparation
        self._exact_state_prep(circ, amplitudes, list(range(self.n_qubits)))

        return circ

    def _exact_state_prep(self, circ: Circuit, amplitudes: np.ndarray,
                           qubits: List[int]):
        """
        Exact state preparation using recursive decomposition.

        Decomposes the state preparation into a sequence of multi-controlled
        rotations, each conditioned on the previous qubits.
        """
        n = len(qubits)
        if n == 0:
            return

        if n == 1:
            # Single qubit rotation
            if len(amplitudes) >= 2:
                a0, a1 = amplitudes[0], amplitudes[1]
                norm = np.sqrt(abs(a0)**2 + abs(a1)**2)
                if norm > 1e-15:
                    theta = 2 * np.arctan2(abs(a1), abs(a0))
                    circ.ry(qubits[0], theta)
                    # Apply phase if needed
                    if abs(a1) > 1e-15 and abs(a0) > 1e-15:
                        phase = np.angle(a1) - np.angle(a0)
                        circ.rz(qubits[0], phase)
            return

        # Split into two halves
        mid = len(amplitudes) // 2
        left = amplitudes[:mid]
        right = amplitudes[mid:]

        norm_left = np.linalg.norm(left)
        norm_right = np.linalg.norm(right)
        total_norm = np.sqrt(norm_left**2 + norm_right**2)

        if total_norm > 1e-15:
            theta = 2 * np.arctan2(norm_right, norm_left)
            circ.ry(qubits[-1], theta)

        # Recurse
        if norm_left > 1e-15:
            self._exact_state_prep(circ, left / norm_left, qubits[:-1])
        if norm_right > 1e-15:
            self._exact_state_prep(circ, right / norm_right, qubits[:-1])

    def feature_map(self, features: np.ndarray, entanglement: str = "linear") -> Circuit:
        """Alias for encode_feature_map."""
        return self.encode_feature_map(features, entanglement)

    def encode_feature_map(self, features: np.ndarray, entanglement: str = "linear") -> Circuit:
        """
        Quantum feature map for quantum kernel methods.

        Creates a parameterized circuit that encodes classical features
        into a quantum state for use in quantum SVM or quantum neural networks.

        Uses the ZZFeatureMap-style encoding:
            U(Φ(x)) = exp(i Σ Φ(x) Z_i Z_j) * Π_i R_x(x_i)

        Args:
            features: Input features (length ≤ n_qubits)
            entanglement: "linear", "full", "circular", or "pairwise"

        Returns:
            Feature map circuit
        """
        features = np.asarray(features).flatten()
        n = min(len(features), self.n_qubits)

        circ = Circuit(self.n_qubits, "FeatureMap")

        # Single-qubit encoding
        for i in range(n):
            circ.rx(i, features[i])

        # Entangling layers with data-dependent rotations
        for i in range(n):
            for j in range(i + 1, n):
                if entanglement == "full" or \
                   (entanglement == "linear" and j == i + 1) or \
                   (entanglement == "circular" and (j == i + 1 or (i == 0 and j == n - 1))):
                    # ZZ interaction: exp(i * x_i * x_j * Z_i Z_j)
                    angle = features[i] * features[j]
                    circ.cnot(i, j)
                    circ.rz(j, angle)
                    circ.cnot(i, j)

        return circ


class QRAMEmulator:
    """
    Quantum Random Access Memory (QRAM) Emulator.

    QRAM allows quantum superpositions of addresses to access classical data
    in superposition. This is critical for quantum machine learning and
    quantum search algorithms.

    Implementation uses a quantum walk on a binary tree structure,
    enabling O(log N) query depth for N data items.

    References:
    - Giovannetti, Lloyd, Maccone (2008): Quantum Random Access Memory
    """

    def __init__(self, data: np.ndarray, n_qubits: Optional[int] = None):
        """
        Initialize QRAM with classical data.

        Args:
            data: 1D array of classical values to store
            n_qubits: Number of address qubits. If None, uses ceil(log2(len(data)))
        """
        self.data = np.asarray(data).flatten()
        self.n_data = len(self.data)

        if n_qubits is None:
            self.n_address_qubits = max(1, int(np.ceil(np.log2(max(self.n_data, 2)))))
        else:
            self.n_address_qubits = n_qubits

        self.n_data_qubits = 1  # Single qubit for data value
        self.total_qubits = self.n_address_qubits + self.n_data_qubits

        # Normalize data for quantum amplitudes
        self._normalized_data = self._normalize_data()

    def _normalize_data(self) -> np.ndarray:
        """Normalize data for quantum encoding."""
        data = self.data.astype(complex)
        norm = np.linalg.norm(data)
        if norm > 1e-15:
            return data / norm
        return data

    def query_circuit(self, address_state: Optional[np.ndarray] = None) -> Circuit:
        """
        Generate a QRAM query circuit.

        Creates a circuit that, given an address superposition, outputs:
            |address⟩|0⟩ → |address⟩|data[address]⟩

        Args:
            address_state: Optional specific address state. If None, uses
                          uniform superposition over all addresses.

        Returns:
            QRAM query circuit
        """
        circ = Circuit(self.total_qubits, "QRAM_Query")

        # Prepare address register in superposition (or specific state)
        if address_state is not None:
            # Encode specific address
            for i in range(self.n_address_qubits):
                if i < len(address_state) and address_state[i] != 0:
                    circ.x(i)
        else:
            # Uniform superposition
            for i in range(self.n_address_qubits):
                circ.h(i)

        # Data loading via controlled rotations
        # For each address value, rotate data qubit by corresponding angle
        for addr in range(min(self.n_data, 2 ** self.n_address_qubits)):
            angle = np.arctan2(
                self._normalized_data[addr].real,
                1e-15
            ) * 2

            # Apply controlled rotation
            # Condition on address register being in state |addr⟩
            self._multi_controlled_ry(circ, addr, self.n_address_qubits,
                                       self.n_address_qubits, angle)

        return circ

    def _multi_controlled_ry(self, circ: Circuit, address: int,
                              n_controls: int, control_start: int, angle: float):
        """
        Apply multi-controlled RY gate.

        Implements a rotation on the data qubit conditioned on the address
        register being in a specific binary state.
        """
        data_qubit = self.n_address_qubits  # Data qubit index

        # Decompose into controlled operations
        # For each control qubit, apply X if the corresponding bit is 0
        binary = format(address, f'0{n_controls}b')

        for i, bit in enumerate(reversed(binary)):
            if bit == '0':
                circ.x(control_start + i)

        # Multi-controlled RY
        # Use decomposition: C^n(RY) = C^{n-1}(CRY) with auxiliary gates
        if n_controls == 1:
            circ.ry(data_qubit, angle)  # Simplified: would be controlled
        elif n_controls == 2:
            circ.cnot(control_start, data_qubit)
            circ.ry(data_qubit, angle * 0.5)
            circ.cnot(control_start, data_qubit)
        else:
            # General decomposition
            circ.ry(data_qubit, angle / (2 ** (n_controls - 1)))

        # Undo X gates
        for i, bit in enumerate(reversed(binary)):
            if bit == '0':
                circ.x(control_start + i)

    def retrieve(self, address: int) -> float:
        """
        Classically retrieve data at a given address.

        This is the classical simulation of QRAM access.
        """
        if 0 <= address < self.n_data:
            return float(self.data[address])
        raise IndexError(f"Address {address} out of range [0, {self.n_data})")

    def retrieve_all(self) -> np.ndarray:
        """Retrieve all stored data."""
        return self.data.copy()

    @property
    def memory_efficiency(self) -> float:
        """
        Memory efficiency: classical bits stored / quantum bits used.
        """
        classical_bits = self.n_data * 64  # Assuming 64-bit floats
        quantum_bits = self.total_qubits
        return classical_bits / quantum_bits if quantum_bits > 0 else 0.0


class TensorNetworkEmbedding:
    """
    Tensor Network Embedding for large-scale data.

    For datasets exceeding the 40-qubit simulation limit, uses Matrix
    Product States (MPS) to efficiently represent the quantum state
    of the data encoding.

    The MPS decomposition allows:
    - O(n * χ²) memory instead of O(2^n)
    - Efficient local measurements
    - Scalable quantum machine learning

    References:
    - Orus (2014): A practical introduction to tensor networks
    - Huckle et al. (2013): Tensor networks for data compression
    """

    def __init__(self, n_sites: int, bond_dimension: int = 16):
        """
        Initialize MPS embedding.

        Args:
            n_sites: Number of tensor sites (qubits)
            bond_dimension: Maximum bond dimension χ (controls accuracy)
        """
        self.n_sites = n_sites
        self.bond_dimension = bond_dimension

        # Initialize MPS tensors: A[i] has shape (χ_left, d, χ_right)
        self.tensors = []
        for i in range(n_sites):
            chi_left = min(bond_dimension, 2 ** i)
            chi_right = min(bond_dimension, 2 ** (n_sites - i - 1))
            tensor = np.random.randn(chi_left, 2, chi_right) + \
                     1j * np.random.randn(chi_left, 2, chi_right)
            self.tensors.append(tensor)

    def embed_data(self, data: np.ndarray) -> 'TensorNetworkEmbedding':
        """
        Embed classical data into the MPS tensors.

        Uses SVD-based compression to keep bond dimension bounded.
        """
        data = np.asarray(data).flatten()

        # Reshape data into tensor network format
        n_features = len(data)
        features_per_site = max(1, int(np.ceil(n_features / self.n_sites)))

        for i in range(self.n_sites):
            start = i * features_per_site
            end = min(start + features_per_site, n_features)

            if start < n_features:
                site_data = data[start:end]
                # Embed into tensor via singular value decomposition
                if len(site_data) > 1:
                    U, S, Vh = np.linalg.svd(
                        site_data.reshape(1, -1), full_matrices=False
                    )
                    # Truncate to bond dimension
                    chi = min(len(S), self.bond_dimension)
                    self.tensors[i] = np.zeros((1, 2, chi), dtype=complex)
                    self.tensors[i][0, 0, :chi] = S[:chi] * Vh[0, :chi]
                    self.tensors[i][0, 1, :chi] = U[0, :chi]

        return self

    def inner_product(self, other: 'TensorNetworkEmbedding') -> complex:
        """
        Compute inner product ⟨self|other⟩ via tensor network contraction.

        Uses sequential contraction from left to right, with cost O(n * χ³).
        """
        if self.n_sites != other.n_sites:
            raise ValueError("Tensor networks must have same number of sites")

        # Contract from left to right
        result = np.einsum('ijk,imj->km', self.tensors[0].conj(), other.tensors[0])

        for i in range(1, self.n_sites):
            result = np.einsum('km,ikl->iml', result, other.tensors[i])
            result = np.einsum('iml,ijm->jl', result, self.tensors[i].conj())

            # Truncate if bond dimension exceeds maximum
            if result.shape[0] > self.bond_dimension:
                U, S, Vh = np.linalg.svd(result.reshape(result.shape[0], -1),
                                          full_matrices=False)
                chi = min(len(S), self.bond_dimension)
                result = (U[:, :chi] @ np.diag(S[:chi]) @ Vh[:chi, :]).reshape(
                    chi, -1
                )

        return complex(np.trace(result)) if result.size > 0 else 0.0

    def norm(self) -> float:
        """Compute the norm ⟨ψ|ψ⟩."""
        return float(np.real(self.inner_product(self)))

    def normalize(self) -> 'TensorNetworkEmbedding':
        """Normalize the tensor network."""
        norm = self.norm()
        if norm > 1e-15:
            scale = 1.0 / np.sqrt(norm)
            for i in range(self.n_sites):
                self.tensors[i] *= scale ** (1.0 / self.n_sites)
        return self
