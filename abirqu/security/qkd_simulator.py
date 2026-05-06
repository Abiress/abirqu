"""QKD Simulator for AbirQu with real quantum state simulations."""

import numpy as np
from typing import List, Dict, Tuple, Optional


class QKDSimulator:
    """Simulates Quantum Key Distribution protocols (BB84, E91, B92) with real quantum states."""

    def __init__(self, protocol: str = "BB84"):
        self.protocol = protocol
        self.eavesdropper = False
        self.qber_threshold = 0.11

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

    def _prepare_bb84_state(self, bit: int, basis: int) -> np.ndarray:
        """Prepare qubit state for BB84."""
        if basis == 0:  # Z basis.
            if bit == 0:
                return np.array([1.0, 0.0], dtype=complex)  # |0>.
            else:
                return np.array([0.0, 1.0], dtype=complex)  # |1>.
        else:  # X basis.
            if bit == 0:
                return np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)  # |+>.
            else:
                return np.array([1/np.sqrt(2), -1/np.sqrt(2)], dtype=complex)  # |->.

    def _measure_bb84(self, state: np.ndarray, basis: int) -> int:
        """Measure qubit in given basis."""
        if basis == 0:  # Z basis.
            probs = [np.abs(state[0])**2, np.abs(state[1])**2]
        else:  # X basis - rotate state.
            x_state = np.array([
                (state[0] + state[1])/np.sqrt(2),
                (state[0] - state[1])/np.sqrt(2)
            ], dtype=complex)
            probs = [np.abs(x_state[0])**2, np.abs(x_state[1])**2]

        # Normalize.
        probs = np.array(probs) / np.sum(probs)

        # Measure.
        return np.random.choice(2, p=probs)

    def _run_bb84(self, key_len: int, error_rate: float) -> Tuple[List[int], Dict]:
        """Simulate BB84 protocol with quantum states."""
        # Alice generates random bits and bases.
        alice_bits = np.random.randint(0, 2, key_len * 2)  # Overshoot.
        alice_bases = np.random.randint(0, 2, key_len * 2)  # 0=Z, 1=X.

        # Bob chooses random bases.
        bob_bases = np.random.randint(0, 2, key_len * 2)

        bob_results = []

        for i in range(len(alice_bits)):
            # Alice prepares state.
            state = self._prepare_bb84_state(alice_bits[i], alice_bases[i])

            # (Optional) Eve intercepts here if eavesdropper=True.
            if self.eavesdropper:
                # Eve measures in random basis.
                eve_basis = np.random.randint(0, 2)
                eve_result = self._measure_bb84(state, eve_basis)
                # Eve prepares new state based on her measurement.
                state = self._prepare_bb84_state(eve_result, eve_basis)

            # Bob measures in his basis.
            result = self._measure_bb84(state, bob_bases[i])
            bob_results.append(result)

        bob_bits = np.array(bob_results)

        # Sifting: keep only matching bases.
        matching = alice_bases == bob_bases
        sifted_alice = alice_bits[matching]
        sifted_bob = bob_bits[matching]

        # Add channel noise/errors.
        if error_rate > 0:
            num_errors = int(len(sifted_alice) * error_rate)
            if num_errors > 0:
                error_indices = np.random.choice(len(sifted_alice), num_errors, replace=False)
                sifted_bob[error_indices] = 1 - sifted_bob[error_indices]

        # Calculate QBER.
        min_len = min(len(sifted_alice), len(sifted_bob))
        errors = np.sum(sifted_alice[:min_len] != sifted_bob[:min_len])
        qber = errors / max(min_len, 1)

        # Check if QBER is acceptable.
        secure = qber < self.qber_threshold

        # Return key (truncate to requested length).
        key = sifted_alice[:key_len].tolist()

        stats = {
            'protocol': 'BB84',
            'key_len': key_len,
            'sifted_len': len(sifted_alice),
            'qber': qber,
            'secure': secure,
            'actual_errors': int(errors),
            'eavesdropper': self.eavesdropper
        }

        return key, stats

    def _create_e91_pair(self) -> np.ndarray:
        """Create entangled pair (Bell state |Φ+>)."""
        bell_state = np.zeros(4, dtype=complex)
        bell_state[0] = 1/np.sqrt(2)  # |00>.
        bell_state[3] = 1/np.sqrt(2)  # |11>.
        return bell_state

    def _measure_e91(self, bell_state: np.ndarray, basis: int, qubit: int) -> int:
        """Measure one qubit of entangled pair."""
        if basis == 0:  # Z basis.
            if qubit == 0:
                probs = [np.abs(bell_state[0])**2 + np.abs(bell_state[1])**2,
                        np.abs(bell_state[2])**2 + np.abs(bell_state[3])**2]
            else:
                probs = [np.abs(bell_state[0])**2 + np.abs(bell_state[2])**2,
                        np.abs(bell_state[1])**2 + np.abs(bell_state[3])**2]
        else:  # X basis.
            # Transform to X basis.
            x_state = np.array([
                (bell_state[0] + bell_state[1] + bell_state[2] + bell_state[3])/2,
                (bell_state[0] - bell_state[1] + bell_state[2] - bell_state[3])/2,
                (bell_state[0] + bell_state[1] - bell_state[2] - bell_state[3])/2,
                (bell_state[0] - bell_state[1] - bell_state[2] + bell_state[3])/2
            ], dtype=complex)
            if qubit == 0:
                probs = [np.abs(x_state[0])**2 + np.abs(x_state[1])**2,
                        np.abs(x_state[2])**2 + np.abs(x_state[3])**2]
            else:
                probs = [np.abs(x_state[0])**2 + np.abs(x_state[2])**2,
                        np.abs(x_state[1])**2 + np.abs(x_state[3])**2]

        probs = np.array(probs) / np.sum(probs)
        return np.random.choice(2, p=probs)

    def _run_e91(self, key_len: int, error_rate: float) -> Tuple[List[int], Dict]:
        """Simulate E91 protocol with entangled pairs."""
        num_pairs = int(key_len * 1.5)

        alice_bits = []
        bob_bits = []
        alice_bases = np.random.randint(0, 3, num_pairs)  # 0=Z, 1=X, 2=Y.
        bob_bases = np.random.randint(0, 3, num_pairs)

        for i in range(num_pairs):
            # Create entangled pair.
            bell_state = self._create_e91_pair()

            # Alice measures her qubit.
            a_bit = self._measure_e91(bell_state, alice_bases[i], 0)
            alice_bits.append(a_bit)

            # Bob measures his qubit.
            b_bit = self._measure_e91(bell_state, bob_bases[i], 1)
            bob_bits.append(b_bit)

        alice_bits = np.array(alice_bits)
        bob_bits = np.array(bob_bits)

        # Sift: keep only matching bases.
        matching = alice_bases == bob_bases
        sifted_alice = alice_bits[matching]
        sifted_bob = bob_bits[matching]

        # Add errors.
        if error_rate > 0:
            num_errors = int(len(sifted_alice) * error_rate)
            if num_errors > 0:
                error_indices = np.random.choice(len(sifted_alice), num_errors, replace=False)
                sifted_bob[error_indices] = 1 - sifted_bob[error_indices]

        qber = np.sum(sifted_alice != sifted_bob) / max(len(sifted_alice), 1)

        key = sifted_alice[:key_len].tolist()

        stats = {
            'protocol': 'E91',
            'key_len': key_len,
            'sifted_len': len(sifted_alice),
            'qber': qber,
            'secure': qber < 0.11
        }

        return key, stats

    def _run_b92(self, key_len: int, error_rate: float) -> Tuple[List[int], Dict]:
        """Simulate B92 protocol (2-state protocol)."""
        # B92 uses only |0> and |+> states.
        key = []
        stats = {'protocol': 'B92', 'key_len': key_len}

        while len(key) < key_len:
            # Alice sends |0> or |+>.
            alice_bit = np.random.randint(0, 2)
            if alice_bit == 0:
                state = np.array([1.0, 0.0], dtype=complex)  # |0>.
            else:
                state = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)  # |+>.

            # Bob measures in |+> or |−> basis (simplified).
            bob_basis = np.random.randint(0, 2)
            if bob_basis == 0:  # Measures in |+>/|−> basis.
                x_state = np.array([
                    (state[0] + state[1])/np.sqrt(2),
                    (state[0] - state[1])/np.sqrt(2)
                ], dtype=complex)
                probs = [np.abs(x_state[0])**2, np.abs(x_state[1])**2]
            else:  # Measures in |0>/|1> basis.
                probs = [np.abs(state[0])**2, np.abs(state[1])**2]

            probs = np.array(probs) / np.sum(probs)
            bob_result = np.random.choice(2, p=probs)

            # In B92, only certain results are kept (simplified).
            if bob_result == 1:  # Ambiguous result - keep.
                key.append(alice_bit)

        stats['qber'] = error_rate
        stats['secure'] = error_rate < 0.11

        return key[:key_len], stats
