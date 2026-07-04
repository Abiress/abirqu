"""
AbirQu QNLP Module — Quantum Natural Language Processing.
Copyright 2026 Abir Maheshwari

Novel contribution: Stochastic-Phase Amplitude Encoding (SPAE)
for real-time quantum NLP and voice analysis.
"""

from abirqu.qnlp.phonemes import (
    text_to_phonemes, phoneme_to_index, phoneme_sequence_to_indices,
    index_to_phoneme, PHONEMES, NUM_PHONEMES
)
from abirqu.qnlp.bitstream import StochasticBitstream, BinaryStochasticEncoder
from abirqu.qnlp.spae import SPAEEncoder, SPAEEncoding, SPAEPipeline

__all__ = [
    'text_to_phonemes', 'phoneme_to_index', 'phoneme_sequence_to_indices',
    'index_to_phoneme', 'PHONEMES', 'NUM_PHONEMES',
    'StochasticBitstream', 'BinaryStochasticEncoder',
    'SPAEEncoder', 'SPAEEncoding', 'SPAEPipeline',
]
