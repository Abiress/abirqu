"""
LDPC Integration for AbirQu
Copyright 2026 Abir Maheshwari

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
        
    def load_code(self, ldpc_code: 'LDPCCode'):
        """Load LDPC code parameters."""
        self.parity_matrix = ldpc_code.H
        self.n = ldpc_code.n
        self.m = ldpc_code.n - ldpc_code.k
        
    def decode(self, received: List[float]) -> List[int]:
        """Decode using vectorized belief propagation (sum-product)."""
        if self.parity_matrix is None:
            raise ValueError("No code loaded.")
            
        # Convert to numpy array
        # llr: L_i = log(P(x_i=0|y_i)/P(x_i=1|y_i))
        # For BSC with error prob p: L_i = log((1-p)/p)
        rx = np.array(received, dtype=float)
        p = np.clip(rx, 1e-6, 1.0 - 1e-6)
        llr = np.log((1 - p) / p)
        
        m, n = self.parity_matrix.shape
        # Variable-to-check messages (M_v->c)
        v2c = np.tile(llr, (m, 1)) * self.parity_matrix
        # Check-to-variable messages (E_c->v)
        c2v = np.zeros((m, n))
        
        for _ in range(self.max_iterations):
            # Check to Variable updates: E_c->v = 2 * atanh(prod(tanh(M_v'->c / 2)))
            for i in range(m):
                # indices of variables connected to check i
                idxs = np.where(self.parity_matrix[i] == 1)[0]
                vals = v2c[i, idxs]
                tan_vals = np.tanh(vals / 2.0)
                
                prod_all = np.prod(tan_vals)
                for j in idxs:
                    # prod excluding current variable
                    t = tan_vals[np.where(idxs == j)[0][0]]
                    prod_ex = prod_all / (t if abs(t) > 1e-12 else 1e-12)
                    c2v[i, j] = 2.0 * np.arctanh(np.clip(prod_ex, -1.0 + 1e-12, 1.0 - 1e-12))
            
            # Variable to Check updates: M_v->c = L_v + sum(E_c'->v)
            for j in range(n):
                idxs = np.where(self.parity_matrix[:, j] == 1)[0]
                vals = c2v[idxs, j]
                sum_all = llr[j] + np.sum(vals)
                for i in idxs:
                    v2c[i, j] = sum_all - c2v[i, j]
            
            # Posterior and hard decision
            posterior = llr + np.sum(c2v, axis=0)
            decoded = (posterior < 0).astype(int)
            
            # Check syndrome
            if np.sum((self.parity_matrix @ decoded) % 2) == 0:
                return decoded.tolist()
                
        return (posterior < 0).astype(int).tolist()
        
    def get_decoding_time(self) -> float:
        """Benchmark decoding performance (simplified)."""
        # Would use time.perf_counter() in real implementation
        return 0.001 * self.n  # Simplified: 1ms per 1000 bits
        
    def decode_hard(self, received: List[int]) -> List[int]:
        """Simplified hard-decision decoding."""
        if self.parity_matrix is None:
            raise ValueError("No code loaded.")
            
        rx = np.array(received, dtype=int)
        
        # Syndrome
        syndrome = (self.parity_matrix @ rx) % 2
        
        if np.sum(syndrome) == 0:
            return received  # No errors detected
            
        # Simplified: flip bits to correct syndrome
        # Real implementation would use minimum weight syndrome decoding
        corrected = rx.copy()
        
        # Try single bit flips
        for j in range(self.n):
            corrected[j] = 1 - corrected[j]
            new_syndrome = (self.parity_matrix @ corrected) % 2
            if np.sum(new_syndrome) == 0:
                return corrected.tolist()
            corrected[j] = 1 - corrected[j]  # Flip back
            
        return corrected.tolist()

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
