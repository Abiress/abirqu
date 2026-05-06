"""QKD Simulator for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
from typing import List, Dict, Tuple, Optional

class QKDSimulator:
    """Simulates Quantum Key Distribution protocols (BB84, E91, B92)."""
    
    def __init__(self, protocol: str = "BB84"):
        self.protocol = protocol
        self.eavesdropper = False
        self.qber_threshold = 0.11  # QBER threshold for BB84
        
    def run(self, key_len: int, error_rate: float = 0.0) -> Tuple[List[int], Dict]:
        """Run QKD protocol and return shared key + stats."""
        if self.protocol == "BB84":
            return self._run_bb84(key_len, error_rate)
        elif self.protocol == "E91":
            return self._run_e91(key_len, error_rate)
        elif self.protocol == "B92":
            return self._run_b92(key_len, error_rate)
        else:
            raise ValueError(f"Unknown protocol: {self.protocol}")
            
    def _run_bb84(self, key_len: int, error_rate: float) -> Tuple[List[int], Dict]:
        """Simulate BB84 protocol."""
        # Alice generates random bits and bases
        alice_bits = np.random.randint(0, 2, key_len)
        alice_bases = np.random.randint(0, 2, key_len)  # 0=Z, 1=X
        
        # Bob chooses random bases
        bob_bases = np.random.randint(0, 2, key_len)
        
        # Bob's measurements (simplified: assume correct measurement)
        # In reality, would depend on Alice's preparation and Bob's basis
        bob_results = alice_bits.copy()  # Simplified
        
        # Sifting: keep only matching bases
        matching = alice_bases == bob_bases
        sifted_alice = alice_bits[matching]
        sifted_bob = bob_results[matching]
        
        # Estimate QBER (Quantum Bit Error Rate)
        # Add some errors
        errors = np.random.random(len(sifted_alice)) < error_rate
        sifted_bob[errors] = 1 - sifted_bob[errors]
        
        actual_errors = np.sum(sifted_alice != sifted_bob)
        qber = actual_errors / len(sifted_alice) if len(sifted_alice) > 0 else 0
        
        # Check if QBER is acceptable
        secure = qber < self.qber_threshold
        
        stats = {
            'protocol': 'BB84',
            'key_len': key_len,
            'sifted_len': len(sifted_alice),
            'qber': qber,
            'secure': secure,
            'actual_errors': int(actual_errors)
        }
        
        return sifted_alice.tolist()[:key_len], stats
        
    def _run_e91(self, key_len: int, error_rate: float) -> Tuple[List[int], Dict]:
        """Simulate E91 protocol (Entanglement-based)."""
        # Generate EPR pairs
        num_pairs = int(key_len * 1.5)  # Generate extra for sifting
        
        # Alice and Bob measure in random bases
        alice_bases = np.random.randint(0, 3, num_pairs)  # 0=Z, 1=X, 2=Y
        bob_bases = np.random.randint(0, 3, num_pairs)
        
        # Results (simplified: perfect correlation for same basis)
        alice_bits = np.random.randint(0, 2, num_pairs)
        bob_bits = alice_bits.copy()
        
        # Add errors
        errors = np.random.random(num_pairs) < error_rate
        bob_bits[errors] = 1 - bob_bits[errors]
        
        # Sift: keep only matching bases (simplified)
        matching = alice_bases == bob_bases
        sifted_alice = alice_bits[matching]
        sifted_bob = bob_bits[matching]
        
        qber = np.sum(sifted_alice != sifted_bob) / len(sifted_alice) if len(sifted_alice) > 0 else 0
        
        stats = {
            'protocol': 'E91',
            'key_len': key_len,
            'sifted_len': len(sifted_alice),
            'qber': qber,
            'secure': qber < 0.11
        }
        
        return sifted_alice.tolist()[:key_len], stats
        
    def _run_b92(self, key_len: int, error_rate: float) -> Tuple[List[int], Dict]:
        """Simulate B92 protocol (2-state protocol)."""
        # Simplified implementation
        bits = np.random.randint(0, 2, key_len)
        stats = {
            'protocol': 'B92',
            'key_len': key_len,
            'sifted_len': key_len,
            'qber': error_rate,
            'secure': error_rate < 0.11
        }
        return bits.tolist(), stats
        
    def enable_eavesdropper(self, probability: float = 0.5):
        """Simulate Eve's presence."""
        self.eavesdropper = True
        self.eavesdrop_prob = probability
        
    def get_security_level(self, key_len: int) -> Dict:
        """Estimate security level of generated key."""
        return {
            'key_len': key_len,
            'entropy': key_len,  # Ideal: 1 bit per bit
            'protocol': self.protocol,
            'secure': True
        }
