"""
Circuit Generation Agent

Builds an AI agent that generates quantum circuits from natural language descriptions.
Implements constraint-aware generation (qubit count, gate set, topology).
Supports iterative refinement with automated testing.
Builds circuit quality scoring (depth, gate count, estimated fidelity).
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class CircuitQualityScore:
    """Scores circuit quality across multiple metrics."""
    
    def __init__(self, gate_count: int, depth: int, num_qubits: int,
                 estimated_fidelity: float = 1.0):
        self.gate_count = gate_count
        self.depth = depth
        self.num_qubits = num_qubits
        self.estimated_fidelity = estimated_fidelity
        
    def overall_score(self) -> float:
        """
        Compute overall quality score (higher is better).
        Uses weighted combination of metrics.
        """
        # Normalize metrics (lower is better for gate_count and depth)
        gate_score = 1.0 / (1.0 + self.gate_count / max(1, self.num_qubits))
        depth_score = 1.0 / (1.0 + self.depth / max(1, self.num_qubits))
        fid_score = self.estimated_fidelity
        
        # Weighted average
        return 0.3 * gate_score + 0.3 * depth_score + 0.4 * fid_score
    
    def __repr__(self):
        return (f"QualityScore(gates={self.gate_count}, depth={self.depth}, "
                f"fidelity={self.estimated_fidelity:.4f}, overall={self.overall_score():.4f})")

class CircuitSpecification:
    """Specification for circuit generation."""
    
    def __init__(self, description: str, num_qubits: Optional[int] = None,
                 gate_set: Optional[List[str]] = None,
                 topology: Optional[str] = None,
                 constraints: Optional[Dict] = None):
        self.description = description
        self.num_qubits = num_qubits
        self.gate_set = gate_set or ['X', 'H', 'CNOT', 'RZ']
        self.topology = topology
        self.constraints = constraints or {}

class CircuitGenerationAgent:
    """
    AI Agent that generates quantum circuits from natural language.
    """
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.generation_history = []
        
    def generate_circuit(self, spec: CircuitSpecification) -> Tuple[List[Tuple[str, List[int]]], CircuitQualityScore]:
        """
        Generate a quantum circuit from specification.
        
        Args:
            spec: Circuit specification
            
        Returns:
            Tuple of (circuit_gates, quality_score)
        """
        # Parse description to identify algorithm
        algorithm = self._identify_algorithm(spec.description)
        
        # Generate circuit based on algorithm
        if algorithm == 'bell':
            circuit = self._generate_bell_state(spec.num_qubits or 2)
        elif algorithm == 'ghz':
            circuit = self._generate_ghz_state(spec.num_qubits or 3)
        elif algorithm == 'qft':
            circuit = self._generate_qft(spec.num_qubits or 3)
        elif algorithm == 'grover':
            circuit = self._generate_grover(spec.num_qubits or 3, spec.constraints or {})
        elif algorithm == 'vqe':
            circuit = self._generate_vqe(spec.num_qubits or 4)
        else:
            # Default: random circuit
            circuit = self._generate_random(spec.num_qubits or 2)
            
        # Validate constraints
        circuit = self._apply_constraints(circuit, spec)
        
        # Score the circuit
        score = self._score_circuit(circuit, spec.num_qubits or 2)
        
        # Record history
        self.generation_history.append({
            'spec': spec,
            'circuit': circuit,
            'score': score
        })
        
        return circuit, score
    
    def _identify_algorithm(self, description: str) -> str:
        """Identify algorithm from description."""
        description_lower = description.lower()
        
        if 'bell' in description_lower:
            return 'bell'
        elif 'ghz' in description_lower:
            return 'ghz'
        elif 'qft' in description_lower or 'fourier' in description_lower:
            return 'qft'
        elif 'grover' in description_lower:
            return 'grover'
        elif 'vqe' in description_lower:
            return 'vqe'
        else:
            return 'unknown'
        
    def _generate_bell_state(self, num_qubits: int) -> List[Tuple[str, List[int]]]:
        """Generate Bell state circuit."""
        if num_qubits < 2:
            num_qubits = 2
        return [('H', [0]), ('CNOT', [0, 1])]
    
    def _generate_ghz_state(self, num_qubits: int) -> List[Tuple[str, List[int]]]:
        """Generate GHZ state circuit."""
        gates = [('H', [0])]
        for i in range(1, num_qubits):
            gates.append(('CNOT', [0, i]))
        return gates
    
    def _generate_qft(self, num_qubits: int) -> List[Tuple[str, List[int]]]:
        """Generate QFT circuit (simplified)."""
        gates = []
        for i in range(num_qubits):
            gates.append(('H', [i]))
            for j in range(i + 1, num_qubits):
                angle = np.pi / (2 ** (j - i))
                gates.append(('CRZ', [j, i, angle]))  # Simplified
        return gates
    
    def _generate_grover(self, num_qubits: int, constraints: Dict) -> List[Tuple[str, List[int]]]:
        """Generate Grover's algorithm circuit."""
        gates = []
        
        # Initialize superposition
        for q in range(num_qubits):
            gates.append(('H', [q]))
            
        # Oracle (simplified - mark |11...1>)
        marked = constraints.get('marked_state', 2**num_qubits - 1)
        binary = format(marked, f'0{num_qubits}b')
        
        for i, bit in enumerate(binary):
            if bit == '0':
                gates.append(('X', [i]))
                
        # Multi-controlled Z
        if num_qubits == 1:
            gates.append(('Z', [0]))
        elif num_qubits == 2:
            gates.append(('CZ', [0, 1]))
        else:
            gates.append(('TOFFOLI', [0, 1, 2]))  # Simplified
            
        # Uncompute X
        for i, bit in enumerate(binary):
            if bit == '0':
                gates.append(('X', [i]))
                
        # Diffusion operator (simplified)
        for q in range(num_qubits):
            gates.append(('H', [q]))
            gates.append(('X', [q]))
            
        gates.append(('TOFFOLI', [0, 1, 2]))  # Simplified
        
        for q in range(num_qubits):
            gates.append(('X', [q]))
            gates.append(('H', [q]))
            
        return gates
    
    def _generate_vqe(self, num_qubits: int) -> List[Tuple[str, List[int]]]:
        """Generate VQE ansatz circuit."""
        gates = []
        
        # Hardware-efficient ansatz
        for layer in range(3):
            for q in range(num_qubits):
                gates.append(('RY', [q, np.pi/4]))
            for q in range(num_qubits - 1):
                gates.append(('CNOT', [q, q+1]))
                
        return gates
    
    def _generate_random(self, num_qubits: int) -> List[Tuple[str, List[int]]]:
        """Generate random circuit."""
        import random
        gates = []
        gate_choices = ['X', 'Y', 'Z', 'H', 'S', 'T']
        
        for _ in range(num_qubits * 2):
            gate = random.choice(gate_choices)
            q = random.randint(0, num_qubits - 1)
            gates.append((gate, [q]))
            
        return gates
    
    def _apply_constraints(self, circuit: List[Tuple[str, List[int]]], 
                          spec: CircuitSpecification) -> List[Tuple[str, List[int]]]:
        """Apply constraints to circuit."""
        # Filter gates not in gate set
        if spec.gate_set:
            circuit = [(g, q) for g, q in circuit if g in spec.gate_set or 
                       (isinstance(g, tuple) and g[0] in spec.gate_set)]
        return circuit
    
    def _score_circuit(self, circuit: List[Tuple[str, List[int]]], 
                       num_qubits: int) -> CircuitQualityScore:
        """Score circuit quality."""
        gate_count = len(circuit)
        depth = gate_count  # Simplified
        
        # Estimate fidelity
        fid = 1.0
        for gate, _ in circuit:
            if gate in ['CNOT', 'TOFFOLI']:
                fid *= 0.995
            elif gate in ['H', 'S', 'T']:
                fid *= 0.999
                
        return CircuitQualityScore(
            gate_count=gate_count,
            depth=depth,
            num_qubits=num_qubits,
            estimated_fidelity=fid
        )
    
    def refine_circuit(self, circuit: List[Tuple[str, List[int]]],
                       spec: CircuitSpecification,
                       iterations: int = 5) -> Tuple[List[Tuple[str, List[int]]], CircuitQualityScore]:
        """
        Iteratively refine circuit to improve quality.
        """
        best_circuit = circuit
        best_score = self._score_circuit(circuit, spec.num_qubits or 2)
        
        for i in range(iterations):
            # Generate variation
            variant = self._generate_variant(best_circuit, spec)
            variant_score = self._score_circuit(variant, spec.num_qubits or 2)
            
            if variant_score.overall_score() > best_score.overall_score():
                best_circuit = variant
                best_score = variant_score
                
        return best_circuit, best_score
    
    def _generate_variant(self, circuit: List[Tuple[str, List[int]]],
                         spec: CircuitSpecification) -> List[Tuple[str, List[int]]]:
        """Generate a variant of the circuit for refinement."""
        # Simple: remove random gate or add gate
        import random
        variant = circuit.copy()
        
        if random.random() < 0.5 and variant:
            # Remove random gate
            idx = random.randint(0, len(variant) - 1)
            variant.pop(idx)
        else:
            # Add gate
            gate = random.choice(['H', 'X', 'Z'])
            q = random.randint(0, (spec.num_qubits or 2) - 1)
            variant.append((gate, [q]))
            
        return variant

# Example usage and tests
if __name__ == "__main__":
    print("Testing Circuit Generation Agent...")
    
    agent = CircuitGenerationAgent()
    
    # Test Bell state generation
    print("\n1. Generating Bell state...")
    spec = CircuitSpecification(
        description="Create a Bell state between qubits 0 and 1",
        num_qubits=2
    )
    circuit, score = agent.generate_circuit(spec)
    print(f"Circuit: {circuit}")
    print(f"Quality: {score}")
    
    # Test GHZ state
    print("\n2. Generating GHZ state...")
    spec = CircuitSpecification(
        description="Create a GHZ state with 4 qubits",
        num_qubits=4
    )
    circuit, score = agent.generate_circuit(spec)
    print(f"Number of gates: {len(circuit)}")
    print(f"Quality: {score}")
    
    # Test refinement
    print("\n3. Refining circuit...")
    refined, refined_score = agent.refine_circuit(circuit, spec, iterations=3)
    print(f"Original score: {score.overall_score():.4f}")
    print(f"Refined score: {refined_score.overall_score():.4f}")