"""
Phoneme dictionary for English text-to-quantum encoding.
Copyright 2026 Abir Maheshwari

Maps characters and digraphs to phoneme symbols.
Based on ARPAbet phoneme set used in speech synthesis.
"""

# ARPAbet phoneme set (44 English phonemes)
PHONEMES = {
    # Vowels
    'AA': 0,   # odd
    'AE': 1,   # at
    'AH': 2,   # hut
    'AO': 3,   # ought
    'AW': 4,   # cow
    'AY': 5,   # hide
    'EH': 6,   # Ed
    'ER': 7,   # hurt
    'EY': 8,   # ate
    'IH': 9,   # it
    'IY': 10,  # eat
    'OW': 11,  # oat
    'OY': 12,  # toy
    'UH': 13,  # hood
    'UW': 14,  # two
    # Consonants
    'B':  15,  # be
    'CH': 16,  # cheese
    'D':  17,  # dee
    'DH': 18,  # thee
    'F':  19,  # fee
    'G':  20,  # green
    'HH': 21,  # he
    'JH': 22,  # gee
    'K':  23,  # key
    'L':  24,  # lee
    'M':  25,  # me
    'N':  26,  # knee
    'NG': 27,  # ping
    'P':  28,  # pee
    'R':  29,  # read
    'S':  30,  # sea
    'SH': 31,  # she
    'T':  32,  # tea
    'TH': 33,  # thin
    'V':  34,  # ve
    'W':  35,  # we
    'Y':  36,  # yield
    'Z':  37,  # zee
    'ZH': 38,  # seizure
    # Special
    'SIL': 39,  # silence
    'SP':  40,  # short pause
    'SPA': 41,  # long pause
}

NUM_PHONEMES = len(PHONEMES)

# Character to phoneme mapping (simplified English)
CHAR_TO_PHONEME = {
    # Vowels
    'a': ['AE'], 'A': ['AE'],
    'e': ['EH'], 'E': ['EH'],
    'i': ['IH'], 'I': ['IY'],
    'o': ['AO'], 'O': ['OW'],
    'u': ['AH'], 'U': ['UW'],
    # Consonants
    'b': ['B'], 'B': ['B'],
    'c': ['K'], 'C': ['K'],
    'd': ['D'], 'D': ['D'],
    'f': ['F'], 'F': ['F'],
    'g': ['G'], 'G': ['G'],
    'h': ['HH'], 'H': ['HH'],
    'j': ['JH'], 'J': ['JH'],
    'k': ['K'], 'K': ['K'],
    'l': ['L'], 'L': ['L'],
    'm': ['M'], 'M': ['M'],
    'n': ['N'], 'N': ['N'],
    'p': ['P'], 'P': ['P'],
    'q': ['K'], 'Q': ['K'],
    'r': ['R'], 'R': ['R'],
    's': ['S'], 'S': ['S'],
    't': ['T'], 'T': ['T'],
    'v': ['V'], 'V': ['V'],
    'w': ['W'], 'W': ['W'],
    'x': ['K', 'S'], 'X': ['K', 'S'],
    'y': ['Y'], 'Y': ['Y'],
    'z': ['Z'], 'Z': ['Z'],
}

# Digraph mappings
DIGRAPHS = {
    'sh': ['SH'], 'SH': ['SH'],
    'ch': ['CH'], 'CH': ['CH'],
    'th': ['TH'], 'TH': ['TH'],
    'ph': ['F'],  'PH': ['F'],
    'wh': ['W'],  'WH': ['W'],
    'ng': ['NG'], 'NG': ['NG'],
    'ck': ['K'],  'CK': ['K'],
    'ee': ['IY'], 'EE': ['IY'],
    'oo': ['UW'], 'OO': ['UW'],
    'ea': ['IY'], 'EA': ['IY'],
    'ai': ['EY'], 'AI': ['EY'],
    'ay': ['EY'], 'AY': ['EY'],
    'ou': ['AW'], 'OU': ['AW'],
    'ow': ['AW'], 'OW': ['AW'],
    'oi': ['OY'], 'OI': ['OY'],
    'oy': ['OY'], 'OY': ['OY'],
    'ie': ['IY'], 'IE': ['IY'],
    'ei': ['EY'], 'EI': ['EY'],
    'au': ['AO'], 'AU': ['AO'],
    'aw': ['AO'], 'AW': ['AO'],
}


def text_to_phonemes(text: str) -> list:
    """
    Convert text string to phoneme sequence.

    Args:
        text: Input text string

    Returns:
        List of phoneme symbols (strings like 'AH', 'B', 'SH', etc.)
    """
    phonemes = []
    i = 0
    text_lower = text.lower()

    while i < len(text_lower):
        if text_lower[i].isspace():
            phonemes.append('SIL')
            i += 1
            continue

        # Check for digraphs first
        if i + 1 < len(text_lower):
            digraph = text_lower[i:i + 2]
            if digraph in DIGRAPHS:
                phonemes.extend(DIGRAPHS[digraph])
                i += 2
                continue

        # Single character
        char = text_lower[i]
        if char in CHAR_TO_PHONEME:
            phonemes.extend(CHAR_TO_PHONEME[char])
        elif char.isdigit():
            phonemes.append('SIL')
        i += 1

    # Remove consecutive silences
    result = []
    for p in phonemes:
        if not (p == 'SIL' and result and result[-1] == 'SIL'):
            result.append(p)

    return result


def phoneme_to_index(phoneme: str) -> int:
    """Convert phoneme symbol to integer index."""
    return PHONEMES.get(phoneme.upper(), PHONEMES['SIL'])


def phoneme_sequence_to_indices(phonemes: list) -> list:
    """Convert list of phoneme symbols to integer indices."""
    return [phoneme_to_index(p) for p in phonemes]


def index_to_phoneme(idx: int) -> str:
    """Convert integer index back to phoneme symbol."""
    for sym, i in PHONEMES.items():
        if i == idx:
            return sym
    return 'SIL'
