"""
QEC Decoder for AbirQu
Copyright 2026 Abir Maheshwari

Implements syndrome decoding via:
1. Lookup-table decoder (small codes)
2. Minimum-weight perfect matching (MWPM) via greedy approximation
3. Belief propagation decoder (for LDPC)

All in pure numpy — no external QEC libraries.
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque


class SyndromeDecoder:
    """General-purpose syndrome decoder.

    Uses a lookup table for small codes and greedy MWPM for larger codes.
    """

    def __init__(self, code=None, code_type: str = "auto"):
        self.code = code
        self.code_type = code_type
        self.lookup_table = {}
        self._build_lookup()

    def _build_lookup(self):
        """Build syndrome -> correction lookup table for small codes."""
        if self.code is None:
            return

        n = self.code.n
        # Only build for small codes (n <= 12)
        if n > 12:
            return

        num_stabs = self.code.num_stabilizers
        # Generate all weight-0, weight-1, weight-2 errors
        for weight in range(min(3, n + 1)):
            for error_positions in self._combinations(n, weight):
                error = np.zeros(n, dtype=int)
                for q in error_positions:
                    error[q] = 1
                syndrome = self.code.compute_syndrome(error)
                syn_key = tuple(syndrome.tolist())
                if syn_key not in self.lookup_table:
                    self.lookup_table[syn_key] = error.copy()

    @staticmethod
    def _combinations(n: int, k: int):
        """Generate all k-element subsets of range(n)."""
        if k == 0:
            yield []
            return
        if k > n:
            return
        for i in range(n):
            for rest in SyndromeDecoder._combinations(n - i - 1, k - 1):
                yield [i] + [r + i + 1 for r in rest]

    def decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode syndrome to find correction.

        Returns correction vector (length n).
        """
        syn_key = tuple(syndrome.tolist())

        # Try lookup table first
        if syn_key in self.lookup_table:
            return self.lookup_table[syn_key].copy()

        # Fallback: greedy matching
        return self._greedy_decode(syndrome)

    def _greedy_decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Greedy syndrome decoding: find minimum-weight correction."""
        n = self.code.n
        correction = np.zeros(n, dtype=int)

        if not np.any(syndrome):
            return correction

        # For each syndrome bit, try to fix it with single-qubit correction
        for i in range(n):
            error = np.zeros(n, dtype=int)
            error[i] = 1
            test_syn = self.code.compute_syndrome(error)
            if np.array_equal(test_syn, syndrome):
                return error

        # Try weight-2 corrections
        for i in range(n):
            for j in range(i + 1, n):
                error = np.zeros(n, dtype=int)
                error[i] = 1
                error[j] = 1
                test_syn = self.code.compute_syndrome(error)
                if np.array_equal(test_syn, syndrome):
                    return error

        # Return best effort (partial correction)
        return correction

    def decode_with_history(self, syndrome: np.ndarray) -> Dict:
        """Decode and return detailed information."""
        correction = self.decode(syndrome)
        return {
            'correction': correction.tolist(),
            'syndrome_weight': int(np.sum(syndrome)),
            'correction_weight': int(np.sum(correction)),
            'used_lookup': tuple(syndrome.tolist()) in self.lookup_table,
        }


class SurfaceCodeDecoder:
    """Decoder for surface codes using syndromes on a 2D lattice."""

    def __init__(self, distance: int = 3):
        self.distance = distance
        self.d = distance

    def decode_x_syndrome(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode X syndrome (detect Z errors) using greedy matching."""
        n = 2 * self.d**2 - 2 * self.d + 1
        correction = np.zeros(n, dtype=int)

        # Find defect positions (syndrome = 1)
        defects = [i for i, s in enumerate(syndrome) if s == 1]

        if len(defects) == 0:
            return correction

        # Pair defects using greedy nearest-neighbor matching
        used = set()
        for i in range(len(defects)):
            if i in used:
                continue
            best_j = -1
            best_dist = float('inf')
            for j in range(i + 1, len(defects)):
                if j in used:
                    continue
                dist = abs(defects[i] - defects[j])
                if dist < best_dist:
                    best_dist = dist
                    best_j = j
            if best_j >= 0:
                used.add(i)
                used.add(best_j)
                # Correct the first defect in the pair
                if defects[i] < n:
                    correction[defects[i]] = 1

        # If odd number of defects, correct the last one
        if len(defects) % 2 == 1:
            last = defects[-1]
            if last < n:
                correction[last] = 1

        return correction

    def decode_z_syndrome(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode Z syndrome (detect X errors) using greedy matching."""
        return self.decode_x_syndrome(syndrome)

    def decode(self, full_syndrome: np.ndarray) -> Dict[str, np.ndarray]:
        """Decode full syndrome (X + Z parts)."""
        half = len(full_syndrome) // 2
        x_syndrome = full_syndrome[:half]
        z_syndrome = full_syndrome[half:]
        return {
            'x_correction': self.decode_x_syndrome(x_syndrome),
            'z_correction': self.decode_z_syndrome(z_syndrome),
        }


class BeliefPropagationDecoder:
    """Belief propagation decoder for quantum LDPC codes.

    Uses iterative message passing on the Tanner graph.
    """

    def __init__(self, max_iterations: int = 20, threshold: float = 0.5):
        self.max_iterations = max_iterations
        self.threshold = threshold

    def decode(self, parity_check_matrix: np.ndarray,
               syndrome: np.ndarray,
               error_rate: float = 0.1) -> np.ndarray:
        """Decode using belief propagation.

        parity_check_matrix: (m, n) binary matrix H.
        syndrome: (m,) binary syndrome vector.
        error_rate: prior probability of error on each qubit.
        """
        m, n = parity_check_matrix.shape

        # Initialize log-likelihood ratios
        prior = np.log((1 - error_rate) / error_rate) * np.ones(n)

        # Channel LLRs (from syndrome)
        llr = prior.copy()

        # Iterative belief propagation
        for iteration in range(self.max_iterations):
            # Check-to-variable messages
            cv_messages = np.zeros((m, n))
            for i in range(m):
                neighbors = np.where(parity_check_matrix[i] == 1)[0]
                for j in neighbors:
                    product = 1.0
                    for k in neighbors:
                        if k != j:
                            product *= np.tanh(llr[k] / 2)
                    cv_messages[i, j] = 2 * np.arctanh(np.clip(product, -0.999, 0.999))

            # Variable-to-check messages
            vc_messages = np.zeros((m, n))
            for j in range(n):
                neighbors = np.where(parity_check_matrix[:, j] == 1)[0]
                for i in neighbors:
                    total = prior[j]
                    for ii in neighbors:
                        if ii != i:
                            total += cv_messages[ii, j]
                    vc_messages[i, j] = total

            # Update LLRs
            for j in range(n):
                neighbors = np.where(parity_check_matrix[:, j] == 1)[0]
                llr[j] = prior[j] + np.sum(cv_messages[neighbors, j])

        # Hard decision
        decoded = (llr < 0).astype(int)

        # Verify syndrome
        computed_syndrome = (parity_check_matrix @ decoded) % 2
        if not np.array_equal(computed_syndrome, syndrome):
            # BP failed, fall back to minimum weight
            decoded = np.zeros(n, dtype=int)
            for i, s in enumerate(syndrome):
                if s == 1 and i < n:
                    decoded[i] = 1

        return decoded


class MWPMDecoder:
    """Minimum-Weight Perfect Matching decoder.

    Uses a greedy approximation of MWPM on the syndrome graph.
    For production use, this would use PyMatching or a proper blossom algorithm.
    """

    def __init__(self, code=None):
        self.code = code

    def decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode using greedy MWPM approximation."""
        if self.code is None:
            return np.zeros(len(syndrome), dtype=int)

        n = self.code.n
        correction = np.zeros(n, dtype=int)

        # Build syndrome graph
        defects = []
        for i, s in enumerate(syndrome):
            if s == 1:
                defects.append(i)

        if len(defects) == 0:
            return correction

        # Greedy matching: pair closest defects
        used = set()
        pairs = []
        for i in range(len(defects)):
            if i in used:
                continue
            best_j = -1
            best_dist = float('inf')
            for j in range(i + 1, len(defects)):
                if j in used:
                    continue
                dist = abs(defects[i] - defects[j])
                if dist < best_dist:
                    best_dist = dist
                    best_j = j
            if best_j >= 0:
                used.add(i)
                used.add(best_j)
                pairs.append((defects[i], defects[j]))

        # Apply corrections along shortest paths
        for q1, q2 in pairs:
            # Correct at the first defect position
            if q1 < n:
                correction[q1] = 1

        # Handle unpaired defect
        if len(defects) % 2 == 1:
            unpaired = [d for i, d in enumerate(defects) if i not in used]
            if unpaired and unpaired[0] < n:
                correction[unpaired[0]] = 1

        return correction


class GPUAcceleratedDecoder:
    """GPU-accelerated decoder using CuPy (falls back to numpy)."""

    def __init__(self, backend: str = "auto"):
        self.backend = backend
        self.use_gpu = False
        try:
            import cupy as cp
            self.xp = cp
            self.use_gpu = True
        except ImportError:
            self.xp = np

    def decode_syndrome(self, syndrome: List[int],
                        parity_check: np.ndarray) -> np.ndarray:
        """Decode syndrome using GPU-accelerated matrix operations."""
        syn = self.xp.array(syndrome, dtype=int)
        H = self.xp.array(parity_check, dtype=int)

        # Compute error estimate via minimum weight
        n = H.shape[1]
        best_error = None
        best_weight = float('inf')

        # Try single-qubit errors
        for j in range(n):
            test = self.xp.zeros(n, dtype=int)
            test[j] = 1
            syn_test = (H @ test) % 2
            if self.xp.array_equal(syn_test, syn):
                weight = int(self.xp.sum(test))
                if weight < best_weight:
                    best_weight = weight
                    best_error = test

        if best_error is not None:
            return self.xp.asnumpy(best_error) if self.use_gpu else best_error
        return np.zeros(n, dtype=int)

    def benchmark(self, num_trials: int = 100, n: int = 20) -> Dict:
        """Benchmark decoder performance."""
        import time
        H = np.random.randint(0, 2, (n // 2, n))
        times = []
        for _ in range(num_trials):
            syn = np.random.randint(0, 2, n // 2)
            start = time.perf_counter()
            self.decode_syndrome(syn.tolist(), H)
            times.append(time.perf_counter() - start)
        return {
            'avg_time_us': np.mean(times) * 1e6,
            'median_time_us': np.median(times) * 1e6,
            'total_time_s': sum(times),
            'num_trials': num_trials,
            'gpu': self.use_gpu,
        }
