"""Optimization Agent for AbirQu. Copyright 2026 Abir Maheshwari"""
from typing import Optional, Dict, List, Any
from ..core.circuit import Circuit
from ..optimize.phase_poly import PhasePolynomialOptimizer
from ..optimize.depth import CircuitDepthMinimizer

class OptimizationAgent:
    """Optimizes quantum circuits using various techniques."""
    
    def __init__(self):
        self.name = "OptAgent"
        self.optimizer = PhasePolynomialOptimizer()
        self.depth_minimizer = CircuitDepthMinimizer()
        
    def optimize(self, circuit: Circuit, strategy: str = "auto") -> Circuit:
        """Optimize a quantum circuit."""
        if strategy == "auto":
            strategy = self._select_strategy(circuit)
            
        if strategy == "phase_poly":
            result = self.optimizer.optimize(circuit)
            return result.optimized
        elif strategy == "depth":
            result = self.depth_minimizer.minimize(circuit)
            return result.minimized
        elif strategy == "combined":
            # First apply phase polynomial, then depth
            result1 = self.optimizer.optimize(circuit)
            result2 = self.depth_minimizer.minimize(result1.optimized)
            return result2.minimized
        else:
            return circuit
            
    def _select_strategy(self, circuit: Circuit) -> str:
        """Select optimization strategy based on circuit characteristics."""
        gate_counts = circuit.count_gates()
        
        # If many rotation gates, use phase polynomial
        rot_gates = sum(gate_counts.get(g, 0) for g in ['RX', 'RY', 'RZ'])
        if rot_gates > len(circuit.gates) * 0.5:
            return "phase_poly"
            
        # If deep circuit, minimize depth
        if circuit.depth() > 10:
            return "depth"
            
        return "combined"
        
    def analyze(self, circuit: Circuit) -> Dict[str, Any]:
        """Analyze circuit and provide optimization suggestions."""
        gate_counts = circuit.count_gates()
        
        suggestions = []
        if 'CNOT' in gate_counts and gate_counts['CNOT'] > 5:
            suggestions.append("Consider gate merging for CNOT gates")
        if circuit.depth() > len(circuit.gates):
            suggestions.append("Circuit is deep - consider depth minimization")
            
        return {
            'num_gates': len(circuit.gates),
            'depth': circuit.depth(),
            'gate_types': gate_counts,
            'suggestions': suggestions
        }
        
    def benchmark(self, circuit: Circuit, num_trials: int = 10) -> Dict[str, float]:
        """Benchmark optimization strategies."""
        import time
        
        results = {}
        
        # Original
        start = time.perf_counter()
        for _ in range(num_trials):
            pass  # Circuit execution would go here
        original_time = time.perf_counter() - start
        
        # Optimized
        start = time.perf_counter()
        optimized = self.optimize(circuit)
        optimized_time = time.perf_counter() - start
        
        results = {
            'original_gates': len(circuit.gates),
            'optimized_gates': len(optimized.gates),
            'original_depth': circuit.depth(),
            'optimized_depth': optimized.depth(),
            'gate_reduction': len(circuit.gates) - len(optimized.gates),
            'depth_reduction': circuit.depth() - optimized.depth(),
        }
        
        return results
