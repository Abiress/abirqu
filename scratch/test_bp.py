import numpy as np
from abirqu.qec.ldpc import LDPCDecoder

n, k, d = 40, 20, 5
m = n - k
failures = 0
iterations = 100

class TestCode:
    def __init__(self, H, G, n, k):
        self.H = H
        self.G = G
        self.n = n
        self.k = k
    def encode(self, message):
        msg = np.array(message, dtype=int)
        return ((msg @ self.G) % 2).tolist()

def generate_parity_matrix(n, k, col_weight=3):
    m = n - k
    P = np.zeros((k, m), dtype=int)
    
    if k == m:
        for w in range(col_weight):
            for attempt in range(100):
                perm = np.random.permutation(m)
                if not np.any(P[np.arange(k), perm] == 1):
                    P[np.arange(k), perm] = 1
                    break
    else:
        for i in range(k):
            col_idxs = np.random.choice(m, col_weight, replace=False)
            P[i, col_idxs] = 1
            
    H = np.zeros((m, n), dtype=int)
    H[:, :k] = P.T
    H[:, k:] = np.eye(m, dtype=int)
    
    G = np.zeros((k, n), dtype=int)
    G[:, :k] = np.eye(k, dtype=int)
    G[:, k:] = P
    
    return H, G

for i in range(iterations):
    H, G = generate_parity_matrix(n, k)
    code = TestCode(H, G, n, k)
    
    msg = [np.random.randint(0, 2) for _ in range(k)]
    codeword = code.encode(msg)
    
    corrupted = list(codeword)
    error_idx = np.random.randint(0, n)
    corrupted[error_idx] ^= 1
    
    received = [0.01 if x == 0 else 0.99 for x in corrupted]
    
    decoder = LDPCDecoder()
    decoder.load_code(code)
    decoded_codeword = decoder.decode(received)
    decoded_msg = decoded_codeword[:k]
    
    if decoded_msg != msg:
        failures += 1

print(f"Total iterations: {iterations}")
print(f"Failures: {failures}")
