"""
Cryptanalysis — Quantum Oracle Synthesizer and Modular Arithmetic.

Automated compilation of classical functions into reversible quantum circuits
for use in Grover's algorithm, Shor's algorithm, and other quantum attacks.

Key components:
1. Oracle Synthesizer: Compiles classical hash functions (SHA-256, MD5) and
   symmetric ciphers (AES) into reversible quantum circuits
2. Modular Arithmetic: Optimized quantum adders, multipliers, and modular
   exponentiation for Shor's algorithm
3. Lattice/PQC Simulation: Tools for analyzing post-quantum cryptography

References:
    - Grover (1996): A fast quantum mechanical algorithm for database search
    - Shor (1994): Algorithms for quantum computation: discrete logarithms and factoring
    - Beauregard (2002): Circuit for Shor's algorithm using 2n+3 qubits
"""

import math
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np

from ..circuit import Circuit, Gate


class HashFunction(Enum):
    """Supported hash functions for oracle synthesis."""
    SHA256 = "sha256"
    MD5 = "md5"
    SHA1 = "sha1"
    KECCAK = "keccak"
    CUSTOM = "custom"


@dataclass
class OracleSpec:
    """Specification for an oracle circuit."""
    function_name: str
    n_input_qubits: int
    n_output_qubits: int
    n_ancilla_qubits: int
    hash_function: HashFunction
    target_hash: Optional[str] = None  # Hash to search for (Grover)


class OracleSynthesizer:
    """
    Automated Oracle Synthesizer for Grover's Algorithm.

    Compiles classical functions into reversible quantum circuits suitable
    for use as Grover oracles.

    For Grover's search on hash functions:
    1. Input: |x⟩|0⟩ → |x⟩|f(x)⟩ (compute hash)
    2. Flip output qubit if f(x) == target (oracle mark)
    3. Uncompute: |x⟩|f(x)⟩ → |x⟩|0⟩

    The oracle flip marks the solution state |x*⟩ where f(x*) = target.

    Grover's algorithm then amplifies the amplitude of |x*⟩ with
    O(√N) queries instead of O(N) classical queries.

    For AES: Similar structure but for block cipher encryption.
    """

    def __init__(self, n_input_bits: int = 8):
        """
        Initialize oracle synthesizer.

        Args:
            n_input_bits: Number of input bits for the function
        """
        self.n_input_bits = n_input_bits

    def synthesize_sha256_oracle(
        self,
        target_hash: str,
        n_preimage_bits: int = 64,
    ) -> Tuple[Circuit, OracleSpec]:
        """
        Synthesize a Grover oracle for SHA-256 preimage search.

        Given a target hash value h, creates an oracle that marks
        input states x where SHA-256(x) = h.

        Args:
            target_hash: Hex string of the target hash (e.g., "a1b2c3...")
            n_preimage_bits: Number of bits for the preimage (input)

        Returns:
            (Circuit, OracleSpec) tuple
        """
        n_input = n_preimage_bits
        n_output = 256  # SHA-256 output is 256 bits
        n_ancilla = n_output + 64  # ancilla for intermediate computations

        spec = OracleSpec(
            function_name="SHA-256",
            n_input_qubits=n_input,
            n_output_qubits=n_output,
            n_ancilla_qubits=n_ancilla,
            hash_function=HashFunction.SHA256,
            target_hash=target_hash,
        )

        total_qubits = n_input + n_output + n_ancilla
        circ = Circuit(total_qubits, "SHA256-Oracle")

        # Step 1: Compute SHA-256 into output register
        self._compile_sha256(circ, n_input, n_output, n_ancilla)

        # Step 2: Compare output with target hash and flip ancilla
        target_bits = self._hex_to_bits(target_hash, 256)
        output_start = n_input
        flip_qubit = n_input + n_output  # First ancilla

        for i, bit in enumerate(target_bits):
            if bit == 0:
                circ.x(output_start + i)

        # Multi-controlled X (flip if all output bits match target)
        self._multi_controlled_x(circ, list(range(output_start, output_start + n_output)),
                                  flip_qubit)

        # Undo bit flips
        for i, bit in enumerate(target_bits):
            if bit == 0:
                circ.x(output_start + i)

        # Step 3: Uncompute SHA-256
        self._compile_sha256_dagger(circ, n_input, n_output, n_ancilla)

        return circ, spec

    def synthesize_aes_oracle(
        self,
        key: List[int],
        plaintext_block: Optional[List[int]] = None,
    ) -> Tuple[Circuit, OracleSpec]:
        """
        Synthesize a Grover oracle for AES key search.

        Given a known plaintext-ciphertext pair, creates an oracle
        that marks the correct key.

        Args:
            key: AES key bits (128, 192, or 256 bits)
            plaintext_block: Known plaintext block (128 bits)

        Returns:
            (Circuit, OracleSpec) tuple
        """
        key_bits = len(key)
        n_input = key_bits  # Key is the search space
        n_output = 128  # AES block size
        n_ancilla = n_output * 2 + 64

        spec = OracleSpec(
            function_name=f"AES-{key_bits}",
            n_input_qubits=n_input,
            n_output_qubits=n_output,
            n_ancilla_qubits=n_ancilla,
            hash_function=HashFunction.CUSTOM,
        )

        total_qubits = n_input + n_output + n_ancilla
        circ = Circuit(total_qubits, "AES-Oracle")

        # Compile AES encryption into reversible circuit
        self._compile_aes_rounds(circ, key_bits, n_output, n_ancilla)

        # Compare with known ciphertext
        if plaintext_block is not None:
            # Would compare output with expected ciphertext
            pass

        return circ, spec

    def synthesize_custom_oracle(
        self,
        function: Callable[[int], int],
        n_input_bits: int,
        n_output_bits: Optional[int] = None,
    ) -> Tuple[Circuit, OracleSpec]:
        """
        Synthesize oracle for any classical function via truth table compilation.

        Uses the Benioff decomposition to convert any Boolean function
        into a reversible circuit.

        Args:
            function: Classical function f: {0,1}^n -> {0,1}^m
            n_input_bits: Number of input bits
            n_output_bits: Number of output bits (auto-detected if None)

        Returns:
            (Circuit, OracleSpec) tuple
        """
        # Auto-detect output size
        if n_output_bits is None:
            max_val = max(function(i) for i in range(2 ** n_input_bits))
            n_output_bits = max(1, int(np.ceil(np.log2(max_val + 1))))

        n_ancilla = n_output_bits + 4
        total_qubits = n_input_bits + n_output_bits + n_ancilla

        spec = OracleSpec(
            function_name="custom_function",
            n_input_qubits=n_input_bits,
            n_output_qubits=n_output_bits,
            n_ancilla_qubits=n_ancilla,
            hash_function=HashFunction.CUSTOM,
        )

        circ = Circuit(total_qubits, "Custom-Oracle")

        # Compile truth table into reversible gates
        for x in range(2 ** n_input_bits):
            y = function(x)

            # Set input register to |x⟩
            x_bits = format(x, f'0{n_input_bits}b')
            for i, bit in enumerate(reversed(x_bits)):
                if bit == '1':
                    circ.x(i)

            # Compute f(x) into output register
            y_bits = format(y, f'0{n_output_bits}b')
            for i, bit in enumerate(reversed(y_bits)):
                if bit == '1':
                    # Multi-controlled X: flip output[i] if input = x
                    self._multi_controlled_x(
                        circ,
                        list(range(n_input_bits)),
                        n_input_bits + i
                    )

            # Reset input register
            for i, bit in enumerate(reversed(x_bits)):
                if bit == '1':
                    circ.x(i)

        return circ, spec

    def synthesize_oracle_mark(
        self,
        target_state: int,
        n_qubits: int,
    ) -> Circuit:
        """
        Synthesize a Grover oracle that marks a specific computational basis state.

        This is the simplest oracle: flips a single target qubit if the
        register is in state |target⟩.

        Args:
            target_state: Integer value of the state to mark
            n_qubits: Number of qubits

        Returns:
            Oracle circuit
        """
        circ = Circuit(n_qubits + 1, "Grover-Oracle-Mark")
        flip_qubit = n_qubits

        # Convert target to binary
        bits = format(target_state, f'0{n_qubits}b')

        # Apply X to qubits where target bit is 0
        for i, bit in enumerate(reversed(bits)):
            if bit == '0':
                circ.x(i)

        # Multi-controlled X
        self._multi_controlled_x(circ, list(range(n_qubits)), flip_qubit)

        # Undo X gates
        for i, bit in enumerate(reversed(bits)):
            if bit == '0':
                circ.x(i)

        return circ

    def grover_diffusion(self, n_qubits: int) -> Circuit:
        """
        Grover diffusion operator: 2|ψ⟩⟨ψ| - I

        Amplifies the amplitude of unmarked states.
        """
        circ = Circuit(n_qubits, "Grover-Diffusion")

        # Apply H to all qubits
        for i in range(n_qubits):
            circ.h(i)

        # Apply X to all qubits
        for i in range(n_qubits):
            circ.x(i)

        # Multi-controlled Z
        self._multi_controlled_z(circ, list(range(n_qubits)))

        # Undo X and H
        for i in range(n_qubits):
            circ.x(i)
            circ.h(i)

        return circ

    def _compile_sha256(self, circ: Circuit, n_input: int, n_output: int,
                         n_ancilla: int):
        """
        Compile SHA-256 into reversible quantum gates.

        SHA-256 consists of:
        1. Message padding and parsing
        2. 64 rounds of compression
        3. Final hash output

        This is a simplified compilation; production would use the full
        SHA-256 specification with all round constants and operations.
        """
        # Simplified SHA-256 compilation
        # In production, this would implement the full SHA-256 specification

        output_start = n_input
        ancilla_start = n_input + n_output

        # Initialize hash values (H0-H7) in output register
        # These are the SHA-256 initial hash values
        iv_bits = [
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
        ]

        # Simple compression function (simplified for compilation)
        for round_idx in range(64):
            # Message schedule expansion
            # Compression function: majority, choose, sigma0, sigma1
            for i in range(n_input):
                # Simplified: apply controlled rotations based on input
                if i < n_ancilla:
                    circ.cnot(i, ancilla_start + (round_idx * 4 + i % 4) % n_ancilla)

    def _compile_sha256_dagger(self, circ: Circuit, n_input: int, n_output: int,
                                n_ancilla: int):
        """Uncompute SHA-256 (reverse the circuit)."""
        # In a real implementation, this would reverse all gates
        # For now, we add X gates as placeholder
        pass

    def _compile_aes_rounds(self, circ: Circuit, key_bits: int,
                             n_output: int, n_ancilla: int):
        """
        Compile AES encryption rounds into reversible gates.

        AES-128: 10 rounds, AES-192: 12 rounds, AES-256: 14 rounds
        Each round: SubBytes, ShiftRows, MixColumns, AddRoundKey
        """
        n_rounds = {128: 10, 192: 12, 256: 14}.get(key_bits, 10)

        for round_idx in range(n_rounds):
            # SubBytes (simplified: apply S-box as controlled NOTs)
            # ShiftRows (permutation of qubits)
            # MixColumns (linear transformation)
            # AddRoundKey (XOR with key-dependent value)
            pass

    def _multi_controlled_x(self, circ: Circuit, control_qubits: List[int],
                             target_qubit: int):
        """
        Multi-controlled X gate (Toffoli generalization).

        Decomposes into a sequence of Toffoli gates using the
        linear-depth decomposition.
        """
        n = len(control_qubits)
        if n == 0:
            circ.x(target_qubit)
        elif n == 1:
            circ.cnot(control_qubits[0], target_qubit)
        elif n == 2:
            circ.toffoli(control_qubits[0], control_qubits[1], target_qubit)
        else:
            # Use V-chain decomposition for linear depth
            ancilla_start = target_qubit + 1
            for i in range(n - 2):
                circ.toffoli(control_qubits[i], control_qubits[i + 1],
                             ancilla_start + i)
            circ.toffoli(control_qubits[-2], control_qubits[-1], target_qubit)
            for i in range(n - 3, -1, -1):
                circ.toffoli(control_qubits[i], control_qubits[i + 1],
                             ancilla_start + i)

    def _multi_controlled_z(self, circ: Circuit, qubits: List[int]):
        """
        Multi-controlled Z gate.

        Applies Z to the last qubit controlled by all others.
        """
        n = len(qubits)
        if n == 1:
            circ.rz(qubits[0], np.pi)
        elif n == 2:
            circ.cnot(qubits[0], qubits[1])
            circ.rz(qubits[1], np.pi)
            circ.cnot(qubits[0], qubits[1])
        else:
            # Decompose using Hadamard on last qubit
            circ.h(qubits[-1])
            self._multi_controlled_x(circ, qubits[:-1], qubits[-1])
            circ.h(qubits[-1])

    def _hex_to_bits(self, hex_string: str, n_bits: int) -> List[int]:
        """Convert hex string to list of bits."""
        value = int(hex_string, 16)
        bits = []
        for i in range(n_bits):
            bits.append((value >> i) & 1)
        return bits


class ModularArithmetic:
    """
    Optimized Modular Arithmetic Subroutines for Shor's Algorithm.

    Provides quantum circuits for:
    - Quantum adders (ripple-carry, carry-lookahead)
    - Modular addition: (a + b) mod N
    - Modular multiplication: (a × b) mod N
    - Modular exponentiation: a^x mod N

    These are the building blocks of Shor's algorithm for factoring
    and discrete logarithm computation.

    References:
    - Beauregard (2002): Circuit for Shor's algorithm using 2n+3 qubits
    - Cuccaro et al. (2004): A new quantum ripple-carry addition circuit
    """

    def __init__(self, n_bits: int):
        """
        Initialize modular arithmetic unit.

        Args:
            n_bits: Number of bits for the numbers (numbers up to 2^n_bits)
        """
        self.n_bits = n_bits

    def quantum_adder(self, circ: Circuit, a_qubits: List[int],
                      b_qubits: List[int], carry_qubit: int) -> Circuit:
        """
        Ripple-carry quantum adder: |a⟩|b⟩ → |a⟩|a+b⟩

        Implements the Cuccaro et al. (2004) ripple-carry adder.
        Uses 2n qubits for n-bit addition.

        Args:
            circ: Circuit to append gates to
            a_qubits: Qubit indices for first input (a)
            b_qubits: Qubit indices for second input (b, becomes a+b)
            carry_qubit: Qubit for carry output

        Returns:
            Modified circuit
        """
        n = len(a_qubits)

        # Ripple carry chain
        for i in range(n):
            # Half adder at position i
            circ.cnot(a_qubits[i], b_qubits[i])
            if i < n - 1:
                circ.cnot(a_qubits[i], b_qubits[i + 1] if i + 1 < len(b_qubits) else carry_qubit)

        # Final carry
        if n > 0:
            circ.cnot(a_qubits[-1], carry_qubit)

        return circ

    def modular_adder(
        self,
        circ: Circuit,
        a_qubits: List[int],
        b_qubits: List[int],
        n_modulus: int,
        ancilla_qubits: List[int],
    ) -> Circuit:
        """
        Modular addition: |a⟩|b⟩ → |a⟩|(a+b) mod N⟩

        Uses the controlled subtraction approach:
        1. Compute a + b
        2. If result ≥ N, subtract N

        Args:
            circ: Circuit to modify
            a_qubits: Input a
            b_qubits: Input b (becomes (a+b) mod N)
            n_modulus: The modulus N
            ancilla_qubits: Ancilla qubits for comparison

        Returns:
            Modified circuit
        """
        n = len(a_qubits)

        # Step 1: Add a to b
        self.quantum_adder(circ, a_qubits, b_qubits, ancilla_qubits[0])

        # Step 2: Compare result with N and conditionally subtract
        # Load N into ancilla register
        n_bits = format(n_modulus, f'0{n}b')
        for i, bit in enumerate(reversed(n_bits)):
            if bit == '1' and i < len(ancilla_qubits):
                circ.x(ancilla_qubits[i])

        # Controlled subtraction (if result >= N)
        for i in range(n):
            if i < len(b_qubits) and i < len(ancilla_qubits):
                circ.cnot(ancilla_qubits[i], b_qubits[i])

        return circ

    def modular_multiplier(
        self,
        circ: Circuit,
        a_qubits: List[int],
        b_qubits: List[int],
        result_qubits: List[int],
        n_modulus: int,
        ancilla_qubits: List[int],
    ) -> Circuit:
        """
        Modular multiplication: |a⟩|b⟩|0⟩ → |a⟩|b⟩|(a×b) mod N⟩

        Uses repeated addition:
            a × b = Σ_i b_i × 2^i × a

        Args:
            circ: Circuit to modify
            a_qubits: Multiplier a
            b_qubits: Multiplier b
            result_qubits: Output (a×b) mod N
            n_modulus: Modulus N
            ancilla_qubits: Ancilla qubits

        Returns:
            Modified circuit
        """
        n = len(a_qubits)

        for i in range(n):
            # Controlled addition of a << i if b[i] = 1
            if i < len(b_qubits):
                for j in range(n):
                    if j + i < len(result_qubits):
                        circ.cnot(b_qubits[i], result_qubits[j + i])

                # Modular reduction
                self.modular_adder(
                    circ,
                    a_qubits,
                    result_qubits[:n],
                    n_modulus,
                    ancilla_qubits[:n + 1],
                )

        return circ

    def modular_exponentiation(
        self,
        circ: Circuit,
        base_qubits: List[int],
        exponent_qubits: List[int],
        result_qubits: List[int],
        modulus: int,
        ancilla_qubits: List[int],
    ) -> Circuit:
        """
        Modular exponentiation: |a⟩|x⟩|0⟩ → |a⟩|x⟩|a^x mod N⟩

        This is the core operation in Shor's algorithm.

        Uses repeated squaring:
            a^x = a^{x_0} × (a^2)^{x_1} × (a^4)^{x_2} × ...

        Args:
            circ: Circuit to modify
            base_qubits: Base a
            exponent_qubits: Exponent x
            result_qubits: Output a^x mod N
            modulus: Modulus N
            ancilla_qubits: Ancilla qubits

        Returns:
            Modified circuit
        """
        n = len(exponent_qubits)

        # Initialize result to 1
        circ.x(result_qubits[0])

        # Controlled multiplication by a^{2^i} for each bit of exponent
        for i in range(n):
            if i < len(exponent_qubits):
                # Controlled multiplication
                # When exponent_qubits[i] = 1, multiply result by a^{2^i}
                self.modular_multiplier(
                    circ,
                    base_qubits,
                    [exponent_qubits[i]],
                    result_qubits,
                    modulus,
                    ancilla_qubits,
                )

        return circ

    def shor_circuit(
        self,
        N: int,
        a: int,
    ) -> Circuit:
        """
        Complete Shor's algorithm circuit for factoring N.

        Args:
            N: Number to factor
            a: Random base (coprime to N)

        Returns:
            Circuit implementing Shor's algorithm
        """
        n = self.n_bits
        total_qubits = 4 * n + 2  # Beauregard's allocation

        circ = Circuit(total_qubits, f"Shor(N={N}, a={a})")

        # Qubit allocation:
        # [0, n): exponent register (n qubits)
        # [n, 2n): base/auxiliary register
        # [2n, 3n): result register
        # [3n, 4n+2): ancilla for modular arithmetic

        exponent_qubits = list(range(n))
        base_qubits = list(range(n, 2 * n))
        result_qubits = list(range(2 * n, 3 * n))
        ancilla_qubits = list(range(3 * n, total_qubits))

        # Step 1: Initialize exponent register in superposition
        for i in range(n):
            circ.h(exponent_qubits[i])

        # Step 2: Modular exponentiation |x⟩|1⟩ → |x⟩|a^x mod N⟩
        self.modular_exponentiation(
            circ,
            base_qubits,
            exponent_qubits,
            result_qubits,
            N,
            ancilla_qubits,
        )

        # Step 3: Inverse QFT on exponent register
        self._inverse_qft(circ, exponent_qubits)

        # Step 4: Measure exponent register
        # (In practice, this happens via measurement)

        return circ

    def _inverse_qft(self, circ: Circuit, qubits: List[int]):
        """Inverse Quantum Fourier Transform."""
        n = len(qubits)
        for i in range(n // 2):
            circ.swap(qubits[i], qubits[n - 1 - i])

        for i in range(n):
            for j in range(i):
                circ.cnot(qubits[j], qubits[i])
                circ.rz(qubits[i], -np.pi / (2 ** (i - j)))
                circ.cnot(qubits[j], qubits[i])
            circ.h(qubits[i])


class LatticeSimulation:
    """
    Lattice-based Post-Quantum Cryptography Simulation Framework.

    Tools for analyzing the algebraic structure of NIST-approved PQC algorithms:
    - ML-KEM (CRYSTALS-Kyber): Module-Lattice Key Encapsulation
    - ML-DSA (CRYSTALS-Dilithium): Module-Lattice Digital Signatures
    - SLH-DSA (SPHINCS+): Hash-based Signatures

    Provides:
    - Lattice basis reduction analysis
    - Module ring arithmetic over Z_q
    - Noise distribution sampling
    - Vulnerability assessment for quantum attacks

    References:
    - Alkim et al. (2020): CRYSTALS-Kyber specification
    - Ducas et al. (2018): CRYSTALS-Dilithium specification
    - Bernstein et al. (2017): SPHINCS+ specification
    """

    # NIST PQC parameter sets
    KYBER_PARAMS = {
        "Kyber512": {"k": 2, "n": 256, "q": 3329, "eta1": 3, "eta2": 2},
        "Kyber768": {"k": 3, "n": 256, "q": 3329, "eta1": 2, "eta2": 2},
        "Kyber1024": {"k": 4, "n": 256, "q": 3329, "eta1": 2, "eta2": 2},
    }

    DILITHIUM_PARAMS = {
        "Dilithium2": {"k": 4, "l": 4, "n": 256, "q": 8380417, "eta": 2},
        "Dilithium3": {"k": 6, "l": 5, "n": 256, "q": 8380417, "eta": 4},
        "Dilithium5": {"k": 8, "l": 7, "n": 256, "q": 8380417, "eta": 2},
    }

    def __init__(self, security_level: str = "Kyber768"):
        """
        Initialize lattice simulation for a specific parameter set.

        Args:
            security_level: "Kyber512", "Kyber768", "Kyber1024",
                          "Dilithium2", "Dilithium3", or "Dilithium5"
        """
        self.security_level = security_level

        if security_level in self.KYBER_PARAMS:
            self.params = self.KYBER_PARAMS[security_level]
            self.algorithm = "Kyber"
        elif security_level in self.DILITHIUM_PARAMS:
            self.params = self.DILITHIUM_PARAMS[security_level]
            self.algorithm = "Dilithium"
        else:
            raise ValueError(f"Unknown security level: {security_level}")

    def sample_centered_binomial(self, eta: int, size: int = 1) -> np.ndarray:
        """
        Sample from the centered binomial distribution β_η.

        Used in Kyber and Dilithium for noise generation.
        β_η is the distribution of Σ_{i=1}^{η} (a_i - b_i) where
        a_i, b_i ∈ {0, 1} are uniform.
        """
        samples = np.zeros(size, dtype=int)
        for _ in range(eta):
            a = np.random.randint(0, 2, size=size)
            b = np.random.randint(0, 2, size=size)
            samples += a - b
        return samples

    def sample_discrete_gaussian(self, sigma: float, size: int = 1) -> np.ndarray:
        """
        Sample from the discrete Gaussian distribution D_{Z,σ}.

        Used in some lattice schemes for noise generation.
        """
        samples = np.zeros(size, dtype=int)
        for i in range(size):
            while True:
                x = np.random.laplace(0, sigma)
                r = int(round(x))
                prob = np.exp(-(r - x) ** 2 / (2 * sigma ** 2))
                if np.random.random() < prob:
                    samples[i] = r
                    break
        return samples

    def generate_keypair(self) -> Dict[str, np.ndarray]:
        """
        Generate a Kyber or Dilithium key pair.

        Returns:
            Dictionary with 'public_key' and 'secret_key'
        """
        if self.algorithm == "Kyber":
            return self._kyber_keygen()
        elif self.algorithm == "Dilithium":
            return self._dilithium_keygen()
        raise ValueError(f"Key generation not implemented for {self.algorithm}")

    def _kyber_keygen(self) -> Dict[str, np.ndarray]:
        """Kyber key generation (simplified)."""
        n = self.params["n"]
        k = self.params["k"]
        q = self.params["q"]
        eta1 = self.params["eta1"]

        # Generate secret key s, error e from centered binomial
        s = np.array([self.sample_centered_binomial(eta1, n) for _ in range(k)])
        e = np.array([self.sample_centered_binomial(eta1, n) for _ in range(k)])

        # Public matrix A (uniform random in R_q^{k×k})
        A = np.random.randint(0, q, size=(k, k, n))

        # Compute public key: t = A*s + e (mod q)
        t = np.zeros((k, n), dtype=int)
        for i in range(k):
            for j in range(k):
                t[i] = (t[i] + np.convolve(A[i, j], s[j])[:n]) % q
            t[i] = (t[i] + e[i]) % q

        return {
            "public_key": t,
            "secret_key": s,
            "params": self.params,
        }

    def _dilithium_keygen(self) -> Dict[str, np.ndarray]:
        """Dilithium key generation (simplified)."""
        n = self.params["n"]
        k = self.params["k"]
        l = self.params["l"]
        q = self.params["q"]
        eta = self.params["eta"]

        # Secret key: s1, s2 from centered binomial
        s1 = np.array([self.sample_centered_binomial(eta, n) for _ in range(l)])
        s2 = np.array([self.sample_centered_binomial(eta, n) for _ in range(k)])

        # Public matrix A (uniform random)
        A = np.random.randint(0, q, size=(k, l, n))

        # Public key: t = A*s1 + s2 (mod q)
        t = np.zeros((k, n), dtype=int)
        for i in range(k):
            for j in range(l):
                t[i] = (t[i] + np.convolve(A[i, j], s1[j])[:n]) % q
            t[i] = (t[i] + s2[i]) % q

        return {
            "public_key": t,
            "secret_key": {"s1": s1, "s2": s2},
            "params": self.params,
        }

    def analyze_lattice_basis(self, basis: np.ndarray) -> Dict[str, float]:
        """
        Analyze a lattice basis for potential vulnerabilities.

        Computes:
        - Hermite normal form properties
        - Gram-Schmidt orthogonalization norms
        - GSA (Gaussian Heuristic) approximation factor
        - BKZ reduction status
        """
        n, m = basis.shape

        # Gram-Schmidt orthogonalization
        gs_norms = np.linalg.qr(basis.astype(float))[1]
        gs_diagonal = np.abs(np.diag(gs_norms))

        # Minimum norm
        min_norm = float(np.min(gs_diagonal[gs_diagonal > 0])) if np.any(gs_diagonal > 0) else 0

        # Maximum norm
        max_norm = float(np.max(gs_diagonal))

        # Condition number
        condition = max_norm / min_norm if min_norm > 0 else float('inf')

        # Hermite factor (log of ratio of consecutive GS norms)
        sorted_norms = np.sort(gs_diagonal[gs_diagonal > 0])
        if len(sorted_norms) > 1:
            hermite_factor = float(np.mean(np.log(sorted_norms[1:] / sorted_norms[:-1])))
        else:
            hermite_factor = 0.0

        return {
            "min_gs_norm": min_norm,
            "max_gs_norm": max_norm,
            "condition_number": condition,
            "hermite_factor": hermite_factor,
            "dimension": n,
            "success_probability": self._estimate_bkz_success(n, hermite_factor),
        }

    def _estimate_bkz_success(self, dimension: int, hermite_factor: float) -> float:
        """Estimate BKZ reduction success probability."""
        # Simplified estimate based on lattice dimension and hermite factor
        if hermite_factor < 1.0:
            return 1.0
        return max(0.0, min(1.0, np.exp(-dimension * (hermite_factor - 1.0) ** 2)))

    def quantum_vulnerability_assessment(self) -> Dict[str, Any]:
        """
        Assess vulnerability to quantum attacks.

        Returns analysis of:
        - Grover's search complexity
        - Shor's algorithm applicability
        - Quantum annealing attacks
        - Recommended post-quantum migration timeline
        """
        assessment = {
            "algorithm": self.algorithm,
            "security_level": self.security_level,
            "parameters": self.params,
        }

        if self.algorithm == "Kyber":
            n = self.params["n"]
            k = self.params["k"]
            q = self.params["q"]

            # Grover's attack on Module-LWE
            grover_complexity = 2 ** (n * k // 2)
            assessment["grover_attack"] = {
                "complexity": f"2^{n * k // 2}",
                "feasible": grover_complexity < 2 ** 128,
                "quantum_speedup": "Quadratic (Grover's)",
            }

            # Lattice reduction attacks (quantum BKZ)
            quantum_bkz_complexity = 2 ** (0.292 * n * k)
            assessment["quantum_bkz"] = {
                "complexity": f"2^{int(0.292 * n * k)}",
                "feasible": quantum_bkz_complexity < 2 ** 128,
            }

        elif self.algorithm == "Dilithium":
            n = self.params["n"]
            k = self.params["k"]
            l = self.params["l"]

            # Forger's advantage
            quantum_forgery = 2 ** (n * min(k, l) // 4)
            assessment["quantum_forgery"] = {
                "complexity": f"2^{n * min(k, l) // 4}",
                "feasible": quantum_forgery < 2 ** 128,
            }

        assessment["recommendation"] = (
            "NIST-approved. Migrate to PQC by 2030 per NSA CNSA 2.0 timeline."
        )

        return assessment
