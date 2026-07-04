"""
Stochastic bitstream generator for SPAE encoding.
Copyright 2026 Abir Maheshwari

Generates probabilistic bitstreams from probability distributions.
Bypasses floating-point rotation gates entirely.
"""

import numpy as np
from typing import List, Optional


class StochasticBitstream:
    """
    Generates stochastic bitstreams from probability distributions.

    Instead of encoding a value as a rotation angle (floating-point),
    this encodes it as a probability in a stream of random bits.

    The key insight: a qubit in superposition can be driven by random bits
    instead of precise rotation angles, enabling native analog-to-quantum
    conversion without floating-point math.
    """

    def __init__(self, rng: Optional[np.random.RandomState] = None):
        self.rng = rng or np.random.RandomState()

    def generate_from_probability(self, probability: float, length: int) -> np.ndarray:
        """
        Generate a bitstream where P(bit=1) = probability.

        Args:
            probability: Target probability in [0, 1]
            length: Number of bits in the stream

        Returns:
            Array of 0s and 1s
        """
        probability = np.clip(probability, 0.0, 1.0)
        return (self.rng.random(length) < probability).astype(int)

    def generate_from_distribution(self, distribution: np.ndarray, length: int) -> np.ndarray:
        """
        Generate a bitstream from a categorical distribution.

        Each bit encodes which category was sampled.

        Args:
            distribution: Probability vector (sums to 1)
            length: Number of samples

        Returns:
            Array of category indices
        """
        distribution = np.array(distribution, dtype=float)
        distribution = distribution / distribution.sum()
        return self.rng.choice(len(distribution), size=length, p=distribution)

    def generate_parallel_bitstreams(self, probabilities: List[float],
                                     bits_per_value: int) -> np.ndarray:
        """
        Generate parallel bitstreams for multiple values.

        Args:
            probabilities: List of probabilities, one per qubit
            bits_per_value: Number of bits per probability

        Returns:
            Matrix of shape (len(probabilities), bits_per_value)
        """
        n = len(probabilities)
        streams = np.zeros((n, bits_per_value), dtype=int)
        for i, p in enumerate(probabilities):
            streams[i] = self.generate_from_probability(p, bits_per_value)
        return streams

    def estimate_probability(self, bitstream: np.ndarray) -> float:
        """Estimate the probability encoded in a bitstream."""
        return np.mean(bitstream)

    def KL_divergence(self, bitstream: np.ndarray, target_prob: float) -> float:
        """Compute KL divergence between bitstream and target distribution."""
        est = self.estimate_probability(bitstream)
        est = np.clip(est, 1e-10, 1 - 1e-10)
        target_prob = np.clip(target_prob, 1e-10, 1 - 1e-10)
        return (target_prob * np.log(target_prob / est) +
                (1 - target_prob) * np.log((1 - target_prob) / (1 - est)))


class BinaryStochasticEncoder:
    """
    Encodes binary values using stochastic bitstreams.

    For SPAE: instead of applying RY(theta) where theta is a float,
    this generates a bitstream and applies X gates based on the bits.
    """

    def __init__(self, rng: Optional[np.random.RandomState] = None):
        self.bitstream_gen = StochasticBitstream(rng)

    def encode_value(self, value: float, n_bits: int) -> np.ndarray:
        """
        Encode a scalar value in [0, 1] as a stochastic bitstream.

        Args:
            value: Scalar value in [0, 1]
            n_bits: Number of bits in the stream

        Returns:
            Bitstream array
        """
        return self.bitstream_gen.generate_from_probability(value, n_bits)

    def encode_vector(self, vector: np.ndarray, bits_per_component: int) -> np.ndarray:
        """
        Encode a vector as parallel stochastic bitstreams.

        Args:
            vector: Input vector (values in [0, 1])
            bits_per_component: Bits per vector component

        Returns:
            Matrix of shape (len(vector), bits_per_component)
        """
        return self.bitstream_gen.generate_parallel_bitstreams(
            vector.tolist(), bits_per_component)

    def decode_stream(self, bitstream: np.ndarray) -> float:
        """Decode a stochastic bitstream back to a probability estimate."""
        return self.bitstream_gen.estimate_probability(bitstream)

    def convergence_rate(self, bitstream: np.ndarray, target: float) -> np.ndarray:
        """
        Compute running estimate convergence as a function of stream length.

        Returns array where element i is the estimate after i+1 bits.
        """
        cumsum = np.cumsum(bitstream)
        indices = np.arange(1, len(bitstream) + 1)
        return cumsum / indices
