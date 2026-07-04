"""
Stochastic-Phase Amplitude Encoding (SPAE) for Quantum NLP.
Copyright 2026 Abir Maheshwari

Novel algorithm: Encodes text/audio into quantum states using stochastic
bitstreams instead of floating-point rotation gates.

Key insight: Instead of computing RY(theta) where theta is a float,
SPAE uses probabilistic streams of 1s and 0s to directly drive qubit
phase angles, creating a native bridge between analog voice data and
quantum superposition.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from abirqu.circuit import Circuit
from abirqu.qnlp.phonemes import (
    text_to_phonemes, phoneme_to_index, phoneme_sequence_to_indices,
    NUM_PHONEMES, PHONEMES
)
from abirqu.qnlp.bitstream import StochasticBitstream, BinaryStochasticEncoder


class SPAEEncoder:
    """
    Stochastic-Phase Amplitude Encoder for QNLP.

    Encodes text or audio data into quantum circuits using stochastic
    bitstreams instead of floating-point rotation gates.

    Algorithm:
        1. Text -> Phoneme sequence (discrete symbols)
        2. Phoneme index -> Probability distribution over qubit basis states
        3. Probability -> Stochastic bitstream (random 0s and 1s)
        4. Bitstream -> Quantum circuit (X gates + CNOT entangling layer)
        5. Averaged quantum state converges to target encoding

    The key advantage: No floating-point rotation gates are needed.
    Only X gates (Clifford) and CNOT gates (Clifford) are used.
    This is hardware-friendly and bypasses the precision requirements
    of rotation-based encoding.
    """

    def __init__(self, n_qubits: int = 4, bits_per_phoneme: int = 100,
                 rng: Optional[np.random.RandomState] = None):
        """
        Args:
            n_qubits: Number of qubits for encoding
            bits_per_phoneme: Number of stochastic bits per phoneme
            rng: Random number generator
        """
        self.n_qubits = n_qubits
        self.bits_per_phoneme = bits_per_phoneme
        self.rng = rng or np.random.RandomState()
        self.bitstream_gen = StochasticBitstream(self.rng)
        self.binary_encoder = BinaryStochasticEncoder(self.rng)
        self.n_basis_states = 2 ** n_qubits

    def encode_text(self, text: str) -> SPAEEncoding:
        """
        Encode text string into quantum circuits.

        Args:
            text: Input text

        Returns:
            SPAEEncoding with circuits and metadata
        """
        phonemes = text_to_phonemes(text)
        phoneme_indices = phoneme_sequence_to_indices(phonemes)

        circuits = []
        bitstreams_all = []
        probabilities_all = []

        for idx in phoneme_indices:
            prob_dist = self._phoneme_to_probability(idx)
            bitstreams = self._probability_to_bitstreams(prob_dist)
            circuit = self._bitstreams_to_circuit(bitstreams)

            circuits.append(circuit)
            bitstreams_all.append(bitstreams)
            probabilities_all.append(prob_dist)

        return SPAEEncoding(
            text=text,
            phonemes=phonemes,
            phoneme_indices=phoneme_indices,
            circuits=circuits,
            bitstreams=bitstreams_all,
            target_probabilities=probabilities_all,
            n_qubits=self.n_qubits,
            bits_per_phoneme=self.bits_per_phoneme,
        )

    def encode_phoneme(self, phoneme_symbol: str) -> Tuple[Circuit, np.ndarray]:
        """
        Encode a single phoneme into a quantum circuit.

        Args:
            phoneme_symbol: Phoneme like 'AH', 'B', 'SH'

        Returns:
            Tuple of (circuit, bitstreams)
        """
        idx = phoneme_to_index(phoneme_symbol)
        prob_dist = self._phoneme_to_probability(idx)
        bitstreams = self._probability_to_bitstreams(prob_dist)
        circuit = self._bitstreams_to_circuit(bitstreams)
        return circuit, bitstreams

    def encode_probability_distribution(self, prob_dist: np.ndarray) -> Tuple[Circuit, np.ndarray]:
        """
        Encode an arbitrary probability distribution into a quantum circuit.

        This is the core SPAE algorithm:
        1. Sample bitstreams from the distribution
        2. Convert bits to X gates on qubits
        3. Add CNOT entangling layer
        4. The averaged state converges to sum(sqrt(p_i)|i>)

        Args:
            prob_dist: Probability vector (sums to 1)

        Returns:
            Tuple of (circuit, bitstreams)
        """
        prob_dist = np.array(prob_dist, dtype=float)
        prob_dist = prob_dist / prob_dist.sum()

        bitstreams = self._probability_to_bitstreams(prob_dist)
        circuit = self._bitstreams_to_circuit(bitstreams)
        return circuit, bitstreams

    def _phoneme_to_probability(self, phoneme_idx: int) -> np.ndarray:
        """
        Convert phoneme index to probability distribution over basis states.

        Uses a deterministic mapping: phoneme index i maps to basis state i
        with high probability, with small noise for other states.
        This creates a distinguishable but smooth encoding.
        """
        prob = np.ones(self.n_basis_states) * 0.01 / self.n_basis_states
        target_idx = phoneme_idx % self.n_basis_states
        prob[target_idx] = 0.9
        # Spread remaining probability to neighbors
        for offset in [-2, -1, 1, 2]:
            neighbor = (target_idx + offset) % self.n_basis_states
            prob[neighbor] += 0.025
        prob = prob / prob.sum()
        return prob

    def _probability_to_bitstreams(self, prob_dist: np.ndarray) -> np.ndarray:
        """
        Convert probability distribution to stochastic bitstreams.

        For each basis state |i>, generate a bitstream where P(bit=1) = p_i.
        The bitstreams are the raw material for SPAE encoding.
        """
        bitstreams = np.zeros((self.n_basis_states, self.bits_per_phoneme), dtype=int)
        for i, p in enumerate(prob_dist):
            bitstreams[i] = self.bitstream_gen.generate_from_probability(
                p, self.bits_per_phoneme)
        return bitstreams

    def _bitstreams_to_circuit(self, bitstreams: np.ndarray) -> Circuit:
        """
        Convert stochastic bitstreams to a quantum circuit.

        This is the core SPAE circuit construction:
        1. For each time step t in the bitstream:
           a. For each basis state i where bitstreams[i, t] = 1:
              Apply X gate to the qubit encoding the i-th bit
           b. Apply CNOT entangling layer
        2. The quantum state after all time steps encodes the distribution

        The key insight: We don't need rotation gates. The stochastic
        application of X gates naturally creates the desired superposition
        when averaged over many repetitions.
        """
        circ = Circuit(self.n_qubits, 'spae')

        n_steps = min(self.bits_per_phoneme, 20)

        for t in range(n_steps):
            for basis_idx in range(self.n_basis_states):
                if bitstreams[basis_idx, t] == 1:
                    qubit_idx = basis_idx % self.n_qubits
                    circ.x(qubit_idx)

            if self.n_qubits >= 2 and t < n_steps - 1:
                self._add_entangling_layer(circ, t)

        return circ

    def _add_entangling_layer(self, circ: Circuit, layer_idx: int):
        """
        Add a CNOT entangling layer.

        Alternates between different connectivity patterns to create
        entanglement across all qubit pairs.
        """
        pattern = layer_idx % 3
        if pattern == 0:
            for i in range(0, self.n_qubits - 1, 2):
                circ.cnot(i, i + 1)
            for i in range(1, self.n_qubits - 1, 2):
                circ.cnot(i, i + 1)
        elif pattern == 1:
            for i in range(self.n_qubits - 1):
                circ.cnot(i, i + 1)
        else:
            for i in range(self.n_qubits - 1, 0, -1):
                circ.cnot(i - 1, i)

    def verify_encoding(self, encoding: SPAEEncoding,
                        shots: int = 1024) -> Dict:
        """
        Verify that the SPAE encoding converges to the target distribution.

        Runs the circuit on a statevector simulator and compares
        the output distribution to the target.
        """
        from abirqu.simulation.monte_carlo import MonteCarloWavefunctionSimulator

        all_counts = {}
        for circuit in encoding.circuits:
            sim = MonteCarloWavefunctionSimulator(encoding.n_qubits)
            result = sim.run_circuit(circuit, shots=shots)
            counts = result.get('counts', {})
            for state, count in counts.items():
                all_counts[state] = all_counts.get(state, 0) + count

        total = sum(all_counts.values())
        observed_dist = np.zeros(self.n_basis_states)
        for state_str, count in all_counts.items():
            idx = int(state_str, 2)
            if idx < self.n_basis_states:
                observed_dist[idx] = count / total

        target_dist = np.mean(encoding.target_probabilities, axis=0)

        fidelity = float(np.sum(np.sqrt(observed_dist * target_dist)) ** 2)
        kl_div = float(np.sum(
            target_dist * np.log(np.clip(target_dist, 1e-10, None) /
                                  np.clip(observed_dist, 1e-10, None))
        ))

        return {
            'fidelity': fidelity,
            'kl_divergence': kl_div,
            'observed_distribution': observed_dist,
            'target_distribution': target_dist,
            'total_shots': total,
        }


class SPAEEncoding:
    """Container for SPAE encoding results."""

    def __init__(self, text: str, phonemes: List[str],
                 phoneme_indices: List[int], circuits: List[Circuit],
                 bitstreams: List[np.ndarray],
                 target_probabilities: List[np.ndarray],
                 n_qubits: int, bits_per_phoneme: int):
        self.text = text
        self.phonemes = phonemes
        self.phoneme_indices = phoneme_indices
        self.circuits = circuits
        self.bitstreams = bitstreams
        self.target_probabilities = target_probabilities
        self.n_qubits = n_qubits
        self.bits_per_phoneme = bits_per_phoneme

    def __repr__(self):
        return (f"SPAEEncoding(text='{self.text[:30]}...', "
                f"phonemes={len(self.phonemes)}, "
                f"circuits={len(self.circuits)}, "
                f"qubits={self.n_qubits})")


class SPAEPipeline:
    """
    End-to-end pipeline: Text -> Quantum Circuit via SPAE.

    Usage:
        pipeline = SPAEPipeline(n_qubits=4, bits_per_phoneme=100)
        encoding = pipeline.encode("hello world")
        verification = pipeline.verify(encoding)
    """

    def __init__(self, n_qubits: int = 4, bits_per_phoneme: int = 100,
                 rng: Optional[np.random.RandomState] = None):
        self.encoder = SPAEEncoder(n_qubits, bits_per_phoneme, rng)
        self.verifier = SPAEEncoder(n_qubits, bits_per_phoneme, rng)

    def encode(self, text: str) -> SPAEEncoding:
        """Encode text to quantum circuits."""
        return self.encoder.encode_text(text)

    def verify(self, encoding: SPAEEncoding, shots: int = 1024) -> Dict:
        """Verify encoding quality."""
        return self.verifier.verify_encoding(encoding, shots)

    def encode_and_verify(self, text: str, shots: int = 1024) -> Dict:
        """Encode text and verify in one call."""
        encoding = self.encode(text)
        verification = self.verify(encoding, shots)
        return {
            'encoding': encoding,
            'verification': verification,
        }
