"""
Circuit Depth Minimizer for AbirQu
Copyright 2026 Abir Maheshwari

Minimizes circuit depth through gate reordering and parallelization.
"""
from typing import List, Dict, Tuple, Set
from abirqu.circuit import Circuit
from ..core.gates import Gate

class CircuitDepthMinimizer:
    """Minimizes circuit depth through gate reordering and parallelization."""
    
    def __init__(self):
        self.depth_reduction = 0
        self.original_depth = 0
        self.minimized_depth = 0
        
    def minimize(self, circuit: Circuit) -> 'MinimizedCircuit':
        """Minimize circuit depth by parallelizing independent gates."""
        self.original_depth = circuit.depth()
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(circuit)
        
        # Topological sort with parallelization
        scheduled = self._parallel_schedule(circuit, dependencies)
        
        # Build minimized circuit
        minimized = Circuit(circuit.num_qubits, f"{circuit.name}_minimized")
        for gate, qubits in scheduled:
            minimized.add_gate(gate, qubits)
            
        self.minimized_depth = minimized.depth()
        self.depth_reduction = self.original_depth - self.minimized_depth
        
        return MinimizedCircuit(circuit, minimized, self.depth_reduction)
        
    def _build_dependency_graph(self, circuit: Circuit) -> Dict[int, Set[int]]:
        """Build gate dependency graph based on qubit conflicts."""
        n = len(circuit.gates)
        dependencies = {i: set() for i in range(n)}
        qubit_last_used = {}  # Last gate that used each qubit
        
        for i, (gate, qubits) in enumerate(circuit.gates):
            # This gate depends on all previous gates that used the same qubits
            for q in qubits:
                if q in qubit_last_used:
                    dependencies[i].add(qubit_last_used[q])
            # Update last used
            for q in qubits:
                qubit_last_used[q] = i
                
        return dependencies
        
    def _parallel_schedule(self, circuit: Circuit, dependencies: Dict[int, Set[int]]) -> List[Tuple[Gate, List[int]]]:
        """Schedule gates in parallel where possible."""
        n = len(circuit.gates)
        scheduled = []
        scheduled_indices = set()
        qubit_busy_until = {}  # qubit -> time step
        
        # Greedy scheduling: process gates in original order but parallelize
        current_time = 0
        remaining = list(range(n))
        
        while remaining:
            # Find gates that can be scheduled at current time
            ready = []
            for i in remaining:
                # Check if all dependencies are scheduled
                if dependencies[i].issubset(scheduled_indices):
                    # Check if qubits are free
                    qubits = circuit.gates[i][1]
                    if all(qubit_busy_until.get(q, -1) < current_time for q in qubits):
                        ready.append(i)
                        
            if ready:
                # Schedule all ready gates
                for i in sorted(ready):  # Sort to maintain some order
                    gate, qubits = circuit.gates[i]
                    scheduled.append((gate, qubits))
                    scheduled_indices.add(i)
                    remaining.remove(i)
                    # Mark qubits busy
                    duration = 1 if len(qubits) == 1 else 2
                    for q in qubits:
                        qubit_busy_until[q] = current_time + duration
                current_time += 1
            else:
                # No gates ready, advance time
                current_time += 1
                
        return scheduled
        
    def get_depth_savings(self) -> int:
        return self.depth_reduction
        
    def get_stats(self) -> Dict[str, Any]:
        return {
            'original_depth': self.original_depth,
            'minimized_depth': self.minimized_depth,
            'depth_reduction': self.depth_reduction,
            'reduction_percentage': (self.depth_reduction / max(self.original_depth, 1)) * 100
        }

class MinimizedCircuit:
    def __init__(self, original: Circuit, minimized: Circuit, reduction: int):
        self.original = original
        self.minimized = minimized
        self.reduction = reduction
        
    def __repr__(self):
        return f"MinimizedCircuit(original_depth={self.original.depth()}, minimized_depth={self.minimized.depth()}, reduction={self.reduction})"
