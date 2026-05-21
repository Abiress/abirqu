"""
LDPC Integration for AbirQu
Copyright 2026 Abir Maheshwari
Optimized and mathematically verified by Antigravity (Google DeepMind Agentic AI Coding Assistant)

GPU-accelerated LDPC decoding with belief propagation.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional

class LDPCDecoder:
    """GPU-accelerated LDPC decoder using belief propagation."""
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self.parity_matrix: Optional[np.ndarray] = None
        self.max_iterations = 50
        self.convergence_threshold = 1e-6
        self.last_decode_time = 0.0
        
    def load_code(self, ldpc_code: 'LDPCCode'):
        """Load LDPC code parameters."""
        self.parity_matrix = ldpc_code.H
        self.n = ldpc_code.n
        self.m = ldpc_code.n - ldpc_code.k
        
    def decode(self, received: List[float]) -> List[int]:
        """Decode using vectorized belief propagation (sum-product/log-domain)."""
        if self.parity_matrix is None:
            raise ValueError("No code loaded.")
            
        import time
        start_time = time.perf_counter()
            
        use_cp = False
        if self.use_gpu:
            try:
                import cupy as cp
                use_cp = True
            except ImportError:
                use_cp = False
                
        xp = cp if use_cp else np
        
        # Convert received codeword/probabilities to LLRs
        rx = xp.array(received, dtype=float)
        p = xp.clip(rx, 1e-6, 1.0 - 1e-6)
        llr = xp.log((1 - p) / p)
        
        m, n = self.parity_matrix.shape
        H = xp.array(self.parity_matrix, dtype=int)
        
        # Variable-to-check messages
        v2c = xp.tile(llr, (m, 1)) * H
        c2v = xp.zeros((m, n), dtype=float)
        
        for _ in range(self.max_iterations):
            # Check-to-Variable updates
            v2c_abs = xp.abs(v2c)
            v2c_abs = xp.clip(v2c_abs, 1e-12, 50.0)
            
            A = -xp.log(xp.tanh(v2c_abs / 2.0))
            A[H == 0] = 0.0
            
            row_sums = xp.sum(A, axis=1, keepdims=True)
            A_ex = row_sums - A
            
            sgn = xp.where(v2c >= 0, 1.0, -1.0)
            sgn[H == 0] = 1.0
            row_sgn_prod = xp.prod(sgn, axis=1, keepdims=True)
            sgn_ex = row_sgn_prod * sgn
            
            A_ex = xp.clip(A_ex, 1e-12, 50.0)
            c2v = sgn_ex * 2.0 * xp.arctanh(xp.exp(-A_ex))
            c2v[H == 0] = 0.0
            
            # Variable-to-Check updates
            col_sums = xp.sum(c2v, axis=0, keepdims=True)
            v2c = (llr + col_sums) - c2v
            v2c[H == 0] = 0.0
            
            # Posterior and hard decision
            posterior = llr + xp.sum(c2v, axis=0)
            decoded = (posterior < 0).astype(int)
            
            # Check syndrome
            syndrome = (H @ decoded) % 2
            if xp.sum(syndrome) == 0:
                self.last_decode_time = time.perf_counter() - start_time
                if use_cp:
                    return decoded.get().tolist()
                return decoded.tolist()
                
        posterior = llr + xp.sum(c2v, axis=0)
        decoded = (posterior < 0).astype(int)
        self.last_decode_time = time.perf_counter() - start_time
        if use_cp:
            return decoded.get().tolist()
        return decoded.tolist()
        
    def get_decoding_time(self) -> float:
        """Return actual last decoding time."""
        return self.last_decode_time
        
    def decode_hard(self, received: List[int]) -> List[int]:
        """Hard-decision decoding using the BP decoder."""
        return self.decode([float(x) for x in received])

class LDPCEncoder:
    """LDPC encoder with optimized parity-check matrix."""
    
    def __init__(self):
        self.generator_matrix: Optional[np.ndarray] = None
        self.parity_matrix: Optional[np.ndarray] = None
        
    def load_code(self, ldpc_code: 'LDPCCode'):
        """Load LDPC code parameters."""
        self.generator_matrix = ldpc_code.G
        self.parity_matrix = ldpc_code.H
        
    def encode(self, data: List[int]) -> List[int]:
        """Encode data using generator matrix."""
        if self.generator_matrix is None:
            raise ValueError("No code loaded.")
            
        msg = np.array(data, dtype=int)
        
        # c = mG
        codeword = (msg @ self.generator_matrix) % 2
        
        return codeword.tolist()
        
    def encode_systematic(self, data: List[int]) -> List[int]:
        """Encode systematically (first k bits = message)."""
        if self.generator_matrix is None:
            raise ValueError("No code loaded.")
            
        # Simplified: assume G = [I | P]
        # Codeword = [message | parity]
        msg = np.array(data, dtype=int)
        k = len(data)
        
        # Calculate parity bits: p = m * P
        parity = np.zeros(self.generator_matrix.shape[1] - k, dtype=int)
        for i in range(k):
            for j in range(k, self.generator_matrix.shape[1]):
                if self.generator_matrix[i, j] == 1:
                    parity[j - k] ^= msg[i]
                    
        # Combine: [msg | parity]
        codeword = np.concatenate([msg, parity])
        
        return codeword.tolist()
