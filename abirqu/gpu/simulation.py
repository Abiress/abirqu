"""
GPU Quantum Simulator with real CUDA operations.
Uses PyTorch for GPU acceleration.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import time


class SimulationType(Enum):
    """Types of GPU simulation."""
    STATE_VECTOR = "state_vector"
    TENSOR_NETWORK = "tensor_network"
    MPS = "mps"


class GPUQuantumSimulator:
    """GPU-accelerated quantum simulator using PyTorch."""
    
    def __init__(self, num_qubits: int = 5, device: str = "cuda"):
        self.num_qubits = num_qubits
        self.device = device
        self.state_vector: Optional[Any] = None
        self.gpu_available = False
        self.torch = None
        
        # Try to import torch.
        try:
            import torch
            self.torch = torch
            self.gpu_available = torch.cuda.is_available()
            if not self.gpu_available:
                self.device = "cpu"
        except ImportError:
            self.device = "cpu"
        
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize state vector to |00...0>."""
        N = 2 ** self.num_qubits
        
        if self.torch and self.gpu_available:
            # GPU tensor initialization.
            self.state_vector = self.torch.zeros(N, dtype=self.torch.complex64, device=self.device)
            self.state_vector[0] = 1.0 + 0j
        else:
            # CPU fallback with numpy.
            self.state_vector = np.zeros(N, dtype=complex)
            self.state_vector[0] = 1.0 + 0j
    
    def apply_gate(self, gate_matrix: np.ndarray, target_qubits: List[int]):
        """Apply gate to state vector using matrix multiplication."""
        if self.state_vector is None:
            self._initialize_state()
        
        N = 2 ** self.num_qubits
        
        if self.torch and self.gpu_available:
            # GPU: Use PyTorch tensor operations.
            return self._apply_gate_gpu(gate_matrix, target_qubits)
        else:
            # CPU: Use numpy.
            return self._apply_gate_cpu(gate_matrix, target_qubits)
    
    def _apply_gate_gpu(self, gate_matrix: np.ndarray,
                         target_qubits: List[int]) -> Any:
        """Apply gate on GPU using PyTorch."""
        # Convert gate to tensor.
        gate_tensor = self.torch.tensor(gate_matrix, dtype=self.torch.complex64, device=self.device)
        
        # Build full unitary matrix.
        full_unitary = self._build_full_unitary_gpu(gate_tensor, target_qubits)
        
        # Apply: |psi'> = U|psi>.
        # Reshape state for matrix multiplication: (1, N) @ (N, N) -> (1, N).
        psi = self.state_vector.unsqueeze(0)  # (1, N).
        psi_new = self.torch.matmul(psi, full_unitary)  # (1, N).
        self.state_vector = psi_new.squeeze(0)  # (N,).
        
        return self.state_vector
    
    def _build_full_unitary_gpu(self, gate: Any,
                               target_qubits: List[int]) -> Any:
        """Build full unitary matrix on GPU."""
        N = 2 ** self.num_qubits
        
        # Start with identity.
        full = self.torch.eye(N, dtype=self.torch.complex64, device=self.device)
        
        # For single-qubit gate.
        if len(target_qubits) == 1:
            q = target_qubits[0]
            # Build tensor product: I⊗...⊗gate⊗...⊗I.
            # Simplified: just return gate embedded in full space.
            return self._embed_single_qubit_gate_gpu(gate, q)
        
        # For two-qubit gate.
        elif len(target_qubits) == 2:
            return self._embed_two_qubit_gate_gpu(gate, target_qubits[0], target_qubits[1])
        
        return full
    
    def _embed_single_qubit_gate_gpu(self, gate: Any, qubit: int) -> Any:
        """Embed single-qubit gate in full Hilbert space on GPU."""
        N = 2 ** self.num_qubits
        
        # Build the full operator: I⊗...⊗gate⊗...⊗I.
        # Use Kronecker product.
        ops = []
        for q in range(self.num_qubits):
            if q == qubit:
                ops.append(gate)
            else:
                ops.append(self.torch.eye(2, dtype=self.torch.complex64, device=self.device))
        
        # Tensor product.
        result = ops[0]
        for op in ops[1:]:
            result = self.torch.kron(result, op)
        
        return result
    
    def _embed_two_qubit_gate_gpu(self, gate: Any, q1: int, q2: int) -> Any:
        """Embed two-qubit gate in full Hilbert space on GPU."""
        N = 2 ** self.num_qubits
        I = self.torch.eye(2, dtype=self.torch.complex64, device=self.device)
        
        # Build operator: I⊗...⊗gate⊗...⊗I.
        # Gate acts on qubits q1 and q2.
        # Simplified: expand gate to full space.
        
        # Full space: 2^n dimensions.
        full = self.torch.zeros((N, N), dtype=self.torch.complex64, device=self.device)
        
        # Populate the 4x4 block for qubits q1, q2.
        gate_np = gate.cpu().numpy()
        
        for i in range(N):
            for j in range(N):
                # Extract bits for q1 and q2.
                i1 = (i >> (self.num_qubits - 1 - q1)) & 1
                i2 = (i >> (self.num_qubits - 1 - q2)) & 1
                j1 = (j >> (self.num_qubits - 1 - q1)) & 1
                j2 = (j >> (self.num_qubits - 1 - q2)) & 1
                
                # Index in 4x4 gate.
                gate_i = i1 * 2 + i2
                gate_j = j1 * 2 + j2
                
                full[i, j] = gate_np[gate_i, gate_j]
        
        return full
    
    def _apply_gate_cpu(self, gate_matrix: np.ndarray,
                         target_qubits: List[int]) -> np.ndarray:
        """Apply gate on CPU using numpy."""
        N = 2 ** self.num_qubits
        
        if len(target_qubits) == 1:
            full_unitary = self._embed_single_qubit_gate_cpu(gate_matrix, target_qubits[0])
        elif len(target_qubits) == 2:
            full_unitary = self._embed_two_qubit_gate_cpu(
                gate_matrix, target_qubits[0], target_qubits[1]
            )
        else:
            full_unitary = np.eye(N, dtype=complex)
        
        # Apply gate: |psi'> = U|psi>.
        self.state_vector = full_unitary @ self.state_vector
        
        return self.state_vector
    
    def _embed_single_qubit_gate_cpu(self, gate: np.ndarray, qubit: int) -> np.ndarray:
        """Embed single-qubit gate in full Hilbert space (CPU)."""
        ops = []
        for q in range(self.num_qubits):
            if q == qubit:
                ops.append(gate)
            else:
                ops.append(np.eye(2, dtype=complex))
        
        result = ops[0]
        for op in ops[1:]:
            result = np.kron(result, op)
        
        return result
    
    def _embed_two_qubit_gate_cpu(self, gate: np.ndarray,
                                q1: int, q2: int) -> np.ndarray:
        """Embed two-qubit gate in full Hilbert space (CPU)."""
        N = 2 ** self.num_qubits
        full = np.zeros((N, N), dtype=complex)
        
        for i in range(N):
            for j in range(N):
                i1 = (i >> (self.num_qubits - 1 - q1)) & 1
                i2 = (i >> (self.num_qubits - 1 - q2)) & 1
                j1 = (j >> (self.num_qubits - 1 - q1)) & 1
                j2 = (j >> (self.num_qubits - 1 - q2)) & 1
                
                gate_i = i1 * 2 + i2
                gate_j = j1 * 2 + j2
                
                full[i, j] = gate[gate_i, gate_j]
        
        return full
    
    def measure(self, shots: int = 1024) -> Dict[str, int]:
        """Measure the state."""
        if self.state_vector is None:
            return {}
        
        N = 2 ** self.num_qubits
        
        # Compute probabilities.
        if self.torch and self.gpu_available:
            probabilities = self.torch.abs(self.state_vector) ** 2
            probs = probabilities.cpu().numpy()
        else:
            probs = np.abs(self.state_vector) ** 2
        
        # Sample measurements.
        outcomes = np.random.choice(N, size=shots, p=probs)
        
        # Count outcomes.
        counts = {}
        for outcome in outcomes:
            bitstring = format(outcome, f'0{self.num_qubits}b')
            counts[bitstring] = counts.get(bitstring, 0) + 1
        
        return counts
    
    def get_state_vector(self) -> Any:
        """Get current state vector."""
        return self.state_vector
    
    def benchmark(self, gates: List[Tuple[np.ndarray, List[int]]],
                   num_runs: int = 10) -> Dict[str, Any]:
        """Benchmark GPU vs CPU performance."""
        results = {'gpu_times': [], 'cpu_times': []}
        
        # GPU benchmark.
        if self.gpu_available:
            for _ in range(num_runs):
                start = time.time()
                for gate_mat, qubits in gates:
                    self.apply_gate(gate_mat, qubits)
                results['gpu_times'].append(time.time() - start)
                self._initialize_state()
        
        # CPU comparison.
        cpu_sim = GPUQuantumSimulator(self.num_qubits, device="cpu")
        for _ in range(num_runs):
            start = time.time()
            for gate_mat, qubits in gates:
                cpu_sim.apply_gate(gate_mat, qubits)
            results['cpu_times'].append(time.time() - start)
            cpu_sim._initialize_state()
        
        results['gpu_avg'] = np.mean(results['gpu_times']) if results['gpu_times'] else 0
        results['cpu_avg'] = np.mean(results['cpu_times'])
        results['speedup'] = results['cpu_avg'] / max(results['gpu_avg'], 1e-6)
        
        return results


__all__ = ['GPUQuantumSimulator', 'SimulationType']
