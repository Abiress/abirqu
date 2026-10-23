"""
AbirQu QNLP Module — Quantum Natural Language Processing.
Copyright 2026 Abir Maheshwari

Novel contribution: Stochastic-Phase Amplitude Encoding (SPAE)
for real-time quantum NLP and voice analysis.
"""

from abirqu.qnlp.bitstream import BinaryStochasticEncoder, StochasticBitstream
from abirqu.qnlp.phonemes import (
    NUM_PHONEMES,
    PHONEMES,
    index_to_phoneme,
    phoneme_sequence_to_indices,
    phoneme_to_index,
    text_to_phonemes,
)
from abirqu.qnlp.spae import SPAEEncoder, SPAEEncoding, SPAEPipeline

__all__ = [
    'text_to_phonemes', 'phoneme_to_index', 'phoneme_sequence_to_indices',
    'index_to_phoneme', 'PHONEMES', 'NUM_PHONEMES',
    'StochasticBitstream', 'BinaryStochasticEncoder',
    'SPAEEncoder', 'SPAEEncoding', 'SPAEPipeline',
]
