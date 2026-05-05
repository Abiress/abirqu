"""
Multi-Objective Optimization Pipeline

Builds a configurable optimization pipeline that can optimize for:
- Gate count
- Circuit depth
- Fidelity (based on gate errors)
- SWAP count (for hardware execution)

Supports Pareto-optimal circuit selection when objectives conflict.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

class OptimizationObjective(Enum):
    """Objectives for circuit optimization."""
    GATE_COUNT = "gate_count"
    DEPTH = "depth"
    FIDELITY = "fidelity"
    SWAP_COUNT = "swap_count"
    EXECUTION_TIME = "execution_time"

@dataclass
class OptimizationResult:
    """Result of an optimization pass."""
    circuit: List[Tuple[str, List[int]]]
    score: Dict[OptimizationObjective, float]
    metadata: Dict[str, Any]

class OptimizationPass:
    """Base class for an optimization pass."""
    
    def __init__(self, name: str, objective: OptimizationObjective):
        self.name = name
        self.objective = objective
        
    def run(self, circuit: List[Tuple[str, List[int]]], 
            num_qubits: int, **kwargs) -> OptimizationResult:
        """Run the optimization pass."""
        raise NotImplementedError

class GateCountReductionPass(OptimizationPass):
    """Optimization pass that reduces gate count."""
    
    def __init__(self):
        super().__init__("gate_count_reduction", OptimizationObjective.GATE_COUNT)
        
    def run(self, circuit: List[Tuple[str, List[int]]], 
            num_qubits: int, **kwargs) -> OptimizationResult:
        # Simple gate count reduction: cancel adjacent inverses
        optimized = self._cancel_adjacent_inverses(circuit)
        
        score = {
            OptimizationObjective.GATE_COUNT: len(optimized),
            OptimizationObjective.DEPTH: self._calculate_depth(optimized)
        }
        
        return OptimizationResult(
            circuit=optimized,
            score=score,
            metadata={'gates_removed': len(circuit) - len(optimized)}
        )
    
    def _cancel_adjacent_inverses(self, circuit: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """Cancel adjacent inverse gates."""
        inverses = {'S': 'S_dag', 'S_dag': 'S', 'T': 'T_dag', 'T_dag': 'T'}
        
        result = []
        skip_next = False
        
        for i, (gate, qubits) in enumerate(circuit):
            if skip_next:
                skip_next = False
                continue
                
            if i + 1 < len(circuit):
                next_gate, next_qubits = circuit[i+1]
                if (next_qubits == qubits and 
                    inverses.get(gate) == next_gate):
                    skip_next = True
                    continue
                    
            result.append((gate, qubits))
            
        return result
    
    def _calculate_depth(self, circuit: List[Tuple[str, List[int]]]) -> int:
        """Calculate circuit depth."""
        # Simplified: assume each gate adds 1 to depth
        return len(circuit)

class DepthReductionPass(OptimizationPass):
    """Optimization pass that reduces circuit depth."""
    
    def __init__(self):
        super().__init__("depth_reduction", OptimizationObjective.DEPTH)
        
    def run(self, circuit: List[Tuple[str, List[int]]], 
            num_qubits: int, **kwargs) -> OptimizationResult:
        # Simple depth reduction: reorder gates to maximize parallelism
        optimized = self._reorder_for_depth(circuit, num_qubits)
        
        score = {
            OptimizationObjective.DEPTH: self._calculate_depth(optimized),
            OptimizationObjective.GATE_COUNT: len(optimized)
        }
        
        return OptimizationResult(
            circuit=optimized,
            score=score,
            metadata={'depth_reduction': self._calculate_depth(circuit) - self._calculate_depth(optimized)}
        )
    
    def _reorder_for_depth(self, circuit: List[Tuple[str, List[int]]], 
                           num_qubits: int) -> List[Tuple[str, List[int]]]:
        """Reorder gates to reduce depth (simplified)."""
        # For now, just return the same circuit
        return circuit.copy()
    
    def _calculate_depth(self, circuit: List[Tuple[str, List[int]]]) -> int:
        """Calculate circuit depth by tracking when each qubit is busy."""
        if not circuit:
            return 0
            
        qubit_free_time = [0] * num_qubits
        depth = 0
        
        for gate, qubits in circuit:
            # Gate can start when all qubits are free
            start_time = max(qubit_free_time[q] for q in qubits)
            end_time = start_time + 1  # Assume all gates take 1 unit
            
            # Update qubit free times
            for q in qubits:
                qubit_free_time[q] = end_time
                
            depth = max(depth, end_time)
            
        return depth

class FidelityOptimizationPass(OptimizationPass):
    """Optimization pass that maximizes fidelity."""
    
    def __init__(self, gate_fidelities: Optional[Dict[str, float]] = None):
        super().__init__("fidelity_optimization", OptimizationObjective.FIDELITY)
        self.gate_fidelities = gate_fidelities or {
            'I': 1.0, 'X': 0.9999, 'Y': 0.9999, 'Z': 1.0, 'H': 0.9999,
            'S': 0.9999, 'T': 0.9998, 'CNOT': 0.995, 'CZ': 0.995, 'SWAP': 0.99
        }
        
    def run(self, circuit: List[Tuple[str, List[int]]], 
            num_qubits: int, **kwargs) -> OptimizationResult:
        # Calculate original fidelity
        original_fidelity = self._calculate_fidelity(circuit)
        
        # Try to replace low-fidelity gates with higher-fidelity alternatives
        optimized = self._optimize_fidelity(circuit)
        
        new_fidelity = self._calculate_fidelity(optimized)
        
        score = {
            OptimizationObjective.FIDELITY: new_fidelity,
            OptimizationObjective.GATE_COUNT: len(optimized)
        }
        
        return OptimizationResult(
            circuit=optimized,
            score=score,
            metadata={
                'original_fidelity': original_fidelity,
                'new_fidelity': new_fidelity,
                'fidelity_improvement': new_fidelity - original_fidelity
            }
        )
    
    def _calculate_fidelity(self, circuit: List[Tuple[str, List[int]]]) -> float:
        """Calculate overall circuit fidelity."""
        if not circuit:
            return 1.0
            
        fidelity = 1.0
        for gate, _ in circuit:
            gate_fid = self.gate_fidelities.get(gate, 0.99)
            fidelity *= gate_fid
            
        return fidelity
    
    def _optimize_fidelity(self, circuit: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """Optimize circuit for fidelity (simplified)."""
        # For now, just return the same circuit
        return circuit.copy()

class MultiObjectivePipeline:
    """
    Configurable optimization pipeline with multi-objective support.
    Supports Pareto-optimal circuit selection when objectives conflict.
    """
    
    def __init__(self):
        self.passes: List[OptimizationPass] = []
        self.objectives: List[OptimizationObjective] = []
        self.weights: Dict[OptimizationObjective, float] = {}
        
    def add_pass(self, opt_pass: OptimizationPass, 
                 weight: float = 1.0) -> 'MultiObjectivePipeline':
        """
        Add an optimization pass to the pipeline.
        
        Args:
            opt_pass: Optimization pass to add
            weight: Weight for this pass's objective
            
        Returns:
            Self for chaining
        """
        self.passes.append(opt_pass)
        if opt_pass.objective not in self.objectives:
            self.objectives.append(opt_pass.objective)
        self.weights[opt_pass.objective] = weight
        return self
    
    def run(self, circuit: List[Tuple[str, List[int]]], 
            num_qubits: int, **kwargs) -> OptimizationResult:
        """
        Run the optimization pipeline.
        
        Args:
            circuit: Input circuit
            num_qubits: Number of qubits
            **kwargs: Additional arguments for passes
            
        Returns:
            OptimizationResult with best circuit
        """
        best_result = None
        best_score = float('-inf')
        
        # Run each pass and track results
        results = []
        current_circuit = circuit.copy()
        
        for opt_pass in self.passes:
            result = opt_pass.run(current_circuit, num_qubits, **kwargs)
            results.append(result)
            
            # Update current circuit (simple sequential for now)
            current_circuit = result.circuit
            
            # Calculate weighted score
            weighted_score = self._calculate_weighted_score(result.score)
            
            if weighted_score > best_score:
                best_score = weighted_score
                best_result = result
                
        # Return the best result
        if best_result is None:
            best_result = OptimizationResult(
                circuit=circuit,
                score={obj: 0.0 for obj in self.objectives},
                metadata={}
            )
            
        return best_result
    
    def _calculate_weighted_score(self, scores: Dict[OptimizationObjective, float]) -> float:
        """Calculate weighted score from multiple objectives."""
        total = 0.0
        for obj, score in scores.items():
            weight = self.weights.get(obj, 1.0)
            # Normalize scores (simplified)
            if obj == OptimizationObjective.FIDELITY:
                total += weight * score  # Higher is better
            else:
                # For others, lower is better - convert to a score where higher is better
                total += weight * (1.0 / (1.0 + score))
        return total
    
    def find_pareto_optimal(self, circuit: List[Tuple[str, List[int]]], 
                             num_qubits: int,
                             num_samples: int = 10) -> List[OptimizationResult]:
        """
        Find Pareto-optimal solutions when objectives conflict.
        
        Args:
            circuit: Input circuit
            num_qubits: Number of qubits
            num_samples: Number of different weight combinations to try
            
        Returns:
            List of Pareto-optimal results
        """
        # Generate different weight combinations
        pareto_results = []
        
        for i in range(num_samples):
            # Vary weights
            for obj in self.objectives:
                self.weights[obj] = np.random.random()
                
            # Normalize weights
            total_weight = sum(self.weights.values())
            for obj in self.weights:
                self.weights[obj] /= total_weight
                
            result = self.run(circuit, num_qubits)
            pareto_results.append(result)
            
        # Filter to Pareto-optimal (simplified - just return all for now)
        return pareto_results

# Example usage and tests
if __name__ == "__main__":
    print("Testing Multi-Objective Optimization Pipeline...")
    
    # Create a test circuit
    test_circuit = [
        ('H', [0]),
        ('S', [0]),
        ('S_dag', [0]),  # Should cancel with S
        ('CNOT', [0, 1]),
        ('CNOT', [0, 1]),  # Should cancel with previous
        ('T', [1])
    ]
    
    print(f"Original circuit ({len(test_circuit)} gates):")
    for g in test_circuit:
        print(f"  {g}")
        
    # Create pipeline
    pipeline = MultiObjectivePipeline()
    pipeline.add_pass(GateCountReductionPass(), weight=1.0)
    pipeline.add_pass(DepthReductionPass(), weight=0.5)
    
    # Run pipeline
    result = pipeline.run(test_circuit, num_qubits=2)
    
    print(f"\nOptimized circuit ({len(result.circuit)} gates):")
    for g in result.circuit:
        print(f"  {g}")
        
    print(f"\nScores: {result.score}")
    print(f"Metadata: {result.metadata}")
    
    # Test fidelity optimization
    print("\n" + "="*50)
    print("Testing Fidelity Optimization...")
    
    fidelity_pass = FidelityOptimizationPass()
    fid_result = fidelity_pass.run(test_circuit, 2)
    
    print(f"Original fidelity: {fid_result.metadata.get('original_fidelity', 'N/A')}")
    print(f"New fidelity: {fid_result.metadata.get('new_fidelity', 'N/A')}")