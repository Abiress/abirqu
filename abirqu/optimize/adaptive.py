"""
Adaptive Compiler for AbirQu
Copyright 2026 Abir Maheshwari

Adapts compilation strategy based on circuit characteristics.
"""
from typing import Dict, Any, Optional, List
from abirqu.circuit import Circuit
from .phase_poly import PhasePolynomialOptimizer
from .transpiler import HardwareAwareTranspiler
from .depth import CircuitDepthMinimizer

class AdaptiveCompiler:
    """Adapts compilation strategy based on circuit characteristics."""
    
    STRATEGIES = ['auto', 'aggressive', 'conservative', 'balanced']
    
    def __init__(self, strategy: str = "auto"):
        self.strategy = strategy
        self.metrics: Dict[str, Any] = {}
        self.compilation_history: List[Dict] = []
        
    def compile(self, circuit: Circuit, backend_info: Optional[Dict] = None) -> 'CompiledCircuit':
        """Compile circuit with adaptive strategy."""
        # Analyze circuit
        analysis = self._analyze_circuit(circuit)
        
        # Select strategy if auto
        strategy = self.strategy
        if strategy == 'auto':
            strategy = self._select_strategy(analysis, backend_info)
            
        # Apply compilation passes based on strategy
        compiled = self._apply_strategy(circuit, strategy, backend_info)
        
        # Record metrics
        self.metrics = {
            'strategy': strategy,
            'original_gates': len(circuit.gates),
            'compiled_gates': len(compiled.circuit.gates),
            'original_depth': circuit.depth(),
            'compiled_depth': compiled.circuit.depth(),
            'analysis': analysis
        }
        
        self.compilation_history.append(self.metrics)
        return compiled
        
    def _analyze_circuit(self, circuit: Circuit) -> Dict[str, Any]:
        """Analyze circuit characteristics."""
        gate_counts = circuit.count_gates()
        
        analysis = {
            'num_qubits': circuit.num_qubits,
            'num_gates': len(circuit.gates),
            'depth': circuit.depth(),
            'gate_types': gate_counts,
            'has_multi_qubit': any(gate_counts.get(t, 0) > 0 for t in ['CNOT', 'CZ', 'SWAP']),
            'single_qubit_ratio': sum(gate_counts.get(t, 0) for t in ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ']) / max(len(circuit.gates), 1),
            'estimated_error': self._estimate_error(circuit)
        }
        
        return analysis
        
    def _estimate_error(self, circuit: Circuit) -> float:
        """Estimate circuit error (simplified)."""
        gate_counts = circuit.count_gates()
        # Simplified: assume single-qubit error 0.001, two-qubit 0.01
        error = 0.0
        for gate, count in gate_counts.items():
            if gate in ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ']:
                error += count * 0.001
            else:
                error += count * 0.01
        return error
        
    def _select_strategy(self, analysis: Dict, backend_info: Optional[Dict]) -> str:
        """Select best strategy based on analysis."""
        if analysis['depth'] > 50:
            return 'aggressive'
        elif analysis['estimated_error'] > 0.1:
            return 'conservative'
        elif analysis['has_multi_qubit']:
            return 'balanced'
        else:
            return 'aggressive'
        
    def _apply_strategy(self, circuit: Circuit, strategy: str, 
                       backend_info: Optional[Dict]) -> 'CompiledCircuit':
        """Apply compilation strategy."""
        compiled_circuit = Circuit(circuit.num_qubits, f"{circuit.name}_compiled")
        
        if strategy == 'aggressive':
            # Apply all optimizations
            optimizer = PhasePolynomialOptimizer()
            result = optimizer.optimize(circuit)
            compiled_circuit = result.optimized
            
        elif strategy == 'conservative':
            # Minimal optimizations
            compiled_circuit = Circuit(circuit.num_qubits, circuit.name)
            for gate, qubits in circuit.gates:
                compiled_circuit.add_gate(gate, qubits)
                
        elif strategy == 'balanced':
            # Apply some optimizations
            minimizer = CircuitDepthMinimizer()
            result = minimizer.minimize(circuit)
            compiled_circuit = result.minimized
            
        # Transpile if backend info provided
        if backend_info and 'backend' in backend_info:
            transpiler = HardwareAwareTranspiler(backend_info['backend'])
            transpiled = transpiler.transpile(compiled_circuit)
            compiled_circuit = transpiled.transpiled
            
        return CompiledCircuit(circuit, compiled_circuit, strategy)
        
    def set_strategy(self, strategy: str):
        if strategy in self.STRATEGIES:
            self.strategy = strategy
        
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()
        
    def get_history(self) -> List[Dict]:
        return self.compilation_history.copy()

class CompiledCircuit:
    def __init__(self, original: Circuit, compiled: Circuit, strategy: str):
        self.original = original
        self.circuit = compiled
        self.strategy = strategy
        
    def __repr__(self):
        return f"CompiledCircuit(strategy={self.strategy}, gates={len(self.circuit.gates)}, depth={self.circuit.depth()})"
