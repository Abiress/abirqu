"""Simulator Backend for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
from typing import Dict, Any, List
from ..core.circuit import Circuit
from ..core.qvm import QuantumVirtualMachine

class SimulatorBackend:
    """Local quantum circuit simulation backend."""
    
    def __init__(self, use_gpu: bool = False):
        self.name = "Simulator"
        self.use_gpu = use_gpu
        self.qvm = None
        self.results = {}
        
    def run(self, circuit: Circuit, shots: int = 1024, 
            noise_model=None) -> Dict[str, Any]:
        """Run circuit on local simulator."""
        # Initialize QVM
        self.qvm = QuantumVirtualMachine(circuit.num_qubits, use_gpu=self.use_gpu)
        
        # Apply gates
        for gate, qubits in circuit.gates:
            self.qvm.apply_gate(gate.matrix, qubits)
            
        # Get state probabilities
        probs = self.qvm.get_probabilities()
        
        # Sample shots
        results = self._sample_shots(probs, shots, circuit.num_qubits)
        
        # Classical register results
        creg_size = max((m['cbit'] for m in circuit.measurements), default=0) + 1 if circuit.measurements else circuit.num_qubits
        
        # Map to classical bits
        classical_results = self._map_to_classical(results, circuit.measurements, creg_size)
        
        return {
            'success': True,
            'backend': self.name,
            'shots': shots,
            'counts': classical_results,
            'state_vector': self.qvm.get_statevector().tolist(),
            'probabilities': probs,
            'execution_time': 0.1 * len(circuit.gates),
            'circuit_depth': circuit.depth()
        }
        
    def _sample_shots(self, probs: Dict[str, float], shots: int, num_qubits: int) -> Dict[str, int]:
        """Sample measurement outcomes."""
        import random
        
        # Convert probabilities to list
        basis_states = list(probs.keys())
        probabilities = list(probs.values())
        
        # Normalize
        total = sum(probabilities)
        if total == 0:
            probabilities = [1.0/len(basis_states)] * len(basis_states)
        else:
            probabilities = [p/total for p in probabilities]
            
        # Sample
        results = {}
        for _ in range(shots):
            outcome = np.random.choice(basis_states, p=probabilities)
            results[outcome] = results.get(outcome, 0) + 1
            
        return results
        
    def _map_to_classical(self, quantum_results: Dict[str, int], 
                          measurements: List[Dict], creg_size: int) -> Dict[str, int]:
        """Map quantum measurement results to classical register."""
        classical = {}
        
        for q_state, count in quantum_results.items():
            # Convert to classical bitstring based on measurements
            if measurements:
                c_bits = ['0'] * creg_size
                for m in measurements:
                    q = m['qubit']
                    c = m['cbit']
                    if q < len(q_state):
                        c_bits[c] = q_state[q]
                c_state = ''.join(c_bits)
            else:
                c_state = q_state
                
            classical[c_state] = classical.get(c_state, 0) + count
            
        return classical
        
    def run_batch(self, circuits: List[Circuit], shots: int = 1024) -> List[Dict]:
        """Run multiple circuits in batch."""
        results = []
        for circuit in circuits:
            result = self.run(circuit, shots)
            results.append(result)
        return results
        
    def get_available_qubits(self) -> int:
        """Return maximum number of qubits simulator can handle."""
        return 32  # Practical limit for local simulation
        
    def estimate_runtime(self, circuit: Circuit) -> float:
        """Estimate simulation runtime."""
        # Rough estimate: 2^n * depth * 1e-6 seconds
        return 2**circuit.num_qubits * circuit.depth() * 1e-6
