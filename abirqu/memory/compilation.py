"""
Task 12.5 — Memory-Aware Compilation.

Compiler pass that minimizes peak qubit count, circuit cutting, space-time tradeoffs.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class OptimizationStrategy(Enum):
    """Memory optimization strategies."""
    MINIMIZE_QUBITS = "minimize_qubits"
    MINIMIZE_TIME = "minimize_time"
    BALANCED = "balanced"
    CIRCUIT_CUTTING = "circuit_cutting"


@dataclass
class MemoryProfile:
    """Memory profile for a compilation strategy."""
    strategy: OptimizationStrategy
    peak_qubits: int
    total_time_steps: int
    memory_footprint_mb: float
    qubit_utilization: float  # 0-1
    gate_count: int
    depth: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy': self.strategy.value,
            'peak_qubits': self.peak_qubits,
            'total_time_steps': self.total_time_steps,
            'memory_footprint_mb': self.memory_footprint_mb,
            'qubit_utilization': self.qubit_utilization,
            'gate_count': self.gate_count,
            'depth': self.depth,
            'efficiency': self._calculate_efficiency(),
        }
    
    def _calculate_efficiency(self) -> float:
        """Calculate efficiency score (higher = better)."""
        if self.peak_qubits == 0:
            return 0.0
        # Combine qubit efficiency and time efficiency
        qubit_score = 1.0 / max(self.peak_qubits, 1)
        time_score = 1.0 / max(self.total_time_steps, 1)
        return (qubit_score + time_score) / 2.0


@dataclass
class CutCircuit:
    """Result of circuit cutting."""
    original_size: int
    num_subcircuits: int
    subcircuits: List[Dict[str, Any]]
    cut_qubits: List[int]
    classical_communication_cost: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_size': self.original_size,
            'num_subcircuits': self.num_subcircuits,
            'subcircuit_sizes': [len(sc.get('gates', [])) for sc in self.subcircuits],
            'cut_qubits': self.cut_qubits,
            'communication_cost': self.classical_communication_cost,
        }


class MemoryAwareCompiler:
    """
    Compiler that minimizes peak qubit count and optimizes memory.
    
    Features:
    - Compiler pass that minimizes peak qubit count
    - Circuit cutting to trade qubits for classical communication
    - Space-time tradeoff optimization
    - Memory footprint profiler for each compilation strategy
    """
    
    def __init__(self, default_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        """
        Initialize memory-aware compiler.
        
        Args:
            default_strategy: Default optimization strategy
        """
        self.default_strategy = default_strategy
        self.compilation_cache: Dict[str, Any] = {}
    
    def compile(self, circuit: Dict[str, Any],
                strategy: Optional[OptimizationStrategy] = None,
                **kwargs) -> Dict[str, Any]:
        """
        Compile circuit with memory-aware optimizations.
        
        Args:
            circuit: Circuit description dict
            strategy: Optimization strategy (uses default if None)
            **kwargs: Strategy-specific arguments
            
        Returns:
            Compiled circuit dict with optimizations applied
        """
        strategy = strategy or self.default_strategy
        
        if strategy == OptimizationStrategy.MINIMIZE_QUBITS:
            return self._minimize_qubits(circuit, **kwargs)
        elif strategy == OptimizationStrategy.MINIMIZE_TIME:
            return self._minimize_time(circuit, **kwargs)
        elif strategy == OptimizationStrategy.BALANCED:
            return self._balanced_optimization(circuit, **kwargs)
        elif strategy == OptimizationStrategy.CIRCUIT_CUTTING:
            return self._apply_circuit_cutting(circuit, **kwargs)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _minimize_qubits(self, circuit: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Minimize qubit count by reusing qubits."""
        gates = circuit.get('gates', [])
        num_qubits = circuit.get('num_qubits', 2)
        
        # Analyze qubit usage over time
        qubit_usage = self._analyze_qubit_usage(gates, num_qubits)
        
        # Find reusable qubits
        reuse_map = self._find_reuse_opportunities(qubit_usage)
        
        # Apply reuse
        optimized_gates = []
        qubit_map = {}  # old_qubit -> new_qubit
        
        for gate in gates:
            new_gate = self._remap_gate(gate, qubit_map, reuse_map)
            optimized_gates.append(new_gate)
        
        # Calculate new qubit count
        used_qubits = set()
        for gate in optimized_gates:
            qubits = self._extract_qubits(gate)
            used_qubits.update(qubits)
        
        new_num_qubits = max(used_qubits) + 1 if used_qubits else 0
        
        result = circuit.copy()
        result['gates'] = optimized_gates
        result['num_qubits'] = new_num_qubits
        result['depth'] = len(optimized_gates)
        result['optimization'] = 'minimize_qubits'
        result['qubits_saved'] = num_qubits - new_num_qubits
        
        return result
    
    def _minimize_time(self, circuit: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Minimize execution time (may use more qubits)."""
        gates = circuit.get('gates', [])
        
        # Simple: parallelize independent gates
        # Group gates that can run in parallel
        optimized_gates = []
        current_layer = []
        
        for gate in gates:
            if self._can_parallelize(gate, current_layer):
                current_layer.append(gate)
            else:
                optimized_gates.extend(current_layer)
                current_layer = [gate]
        
        if current_layer:
            optimized_gates.extend(current_layer)
        
        result = circuit.copy()
        result['gates'] = optimized_gates
        result['depth'] = len(optimized_gates) // 2  # Approximate parallel depth
        result['optimization'] = 'minimize_time'
        
        return result
    
    def _balanced_optimization(self, circuit: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Balance qubit count and time."""
        # First minimize qubits
        step1 = self._minimize_qubits(circuit)
        
        # Then optimize time on the result
        step2 = self._minimize_time(step1)
        
        step2['optimization'] = 'balanced'
        step2['optimization_steps'] = ['minimize_qubits', 'minimize_time']
        
        return step2
    
    def _apply_circuit_cutting(self, circuit: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Cut circuit to reduce qubit requirements."""
        cutter = CircuitCutter()
        cut_result = cutter.cut(
            circuit,
            max_qubits=kwargs.get('max_qubits', 10)
        )
        
        result = circuit.copy()
        result['subcircuits'] = cut_result.subcircuits
        result['num_subcircuits'] = cut_result.num_subcircuits
        result['cut_qubits'] = cut_result.cut_qubits
        result['optimization'] = 'circuit_cutting'
        result['communication_cost'] = cut_result.classical_communication_cost
        
        return result
    
    def _analyze_qubit_usage(self, gates: List[Any], num_qubits: int) -> Dict[int, List[int]]:
        """Analyze when each qubit is used."""
        usage = {i: [] for i in range(num_qubits)}
        
        for time_step, gate in enumerate(gates):
            qubits = self._extract_qubits(gate)
            for q in qubits:
                usage[q].append(time_step)
        
        return usage
    
    def _find_reuse_opportunities(self, qubit_usage: Dict[int, List[int]]) -> Dict[int, int]:
        """Find qubits that can be reused."""
        # Simple: map qubits to earliest available slot
        reuse_map = {}
        max_time = max((max(times) for times in qubit_usage.values() if times), default=0)
        
        # Sort qubits by last usage
        sorted_qubits = sorted(
            qubit_usage.keys(),
            key=lambda q: max(qubit_usage[q]) if qubit_usage[q] else 0
        )
        
        # Assign new qubit IDs
        for new_id, old_id in enumerate(sorted_qubits):
            reuse_map[old_id] = new_id
        
        return reuse_map
    
    def _remap_gate(self, gate: Any, qubit_map: Dict[int, int], 
                    reuse_map: Dict[int, int]) -> Any:
        """Remap qubits in a gate."""
        if isinstance(gate, tuple) and len(gate) > 1:
            old_qubits = gate[1]
            if isinstance(old_qubits, list):
                new_qubits = [reuse_map.get(q, q) for q in old_qubits]
                return (gate[0], new_qubits) + gate[2:]
            elif isinstance(old_qubits, int):
                new_q = reuse_map.get(old_qubits, old_qubits)
                return (gate[0], new_q) + gate[2:]
        return gate
    
    def _extract_qubits(self, gate: Any) -> List[int]:
        """Extract qubit list from gate."""
        if isinstance(gate, tuple) and len(gate) > 1:
            if isinstance(gate[1], list):
                return gate[1]
            elif isinstance(gate[1], int):
                return [gate[1]]
        return []
    
    def _can_parallelize(self, gate: Any, current_layer: List[Any]) -> bool:
        """Check if gate can be added to current parallel layer."""
        gate_qubits = set(self._extract_qubits(gate))
        
        for existing in current_layer:
            existing_qubits = set(self._extract_qubits(existing))
            if gate_qubits & existing_qubits:  # Overlap
                return False
        
        return True
    
    def profile_strategies(self, circuit: Dict[str, Any]) -> List[MemoryProfile]:
        """
        Profile memory footprint for each compilation strategy.
        
        Args:
            circuit: Circuit to profile
            
        Returns:
            List of MemoryProfile for each strategy
        """
        profiles = []
        
        for strategy in OptimizationStrategy:
            try:
                compiled = self.compile(circuit, strategy=strategy)
                profile = self._create_profile(compiled, strategy)
                profiles.append(profile)
            except Exception as e:
                print(f"Warning: Strategy {strategy.value} failed: {e}")
        
        return profiles
    
    def _create_profile(self, compiled: Dict[str, Any], 
                        strategy: OptimizationStrategy) -> MemoryProfile:
        """Create memory profile from compiled circuit."""
        gates = compiled.get('gates', [])
        num_qubits = compiled.get('num_qubits', 0)
        
        # Estimate memory
        # Assume 16 bytes per qubit-time step
        time_steps = compiled.get('depth', len(gates))
        memory_mb = (num_qubits * time_steps * 16) / (1024 ** 2)
        
        # Calculate utilization
        total_possible = num_qubits * time_steps
        actual_usage = sum(len(self._extract_qubits(g)) for g in gates)
        utilization = actual_usage / max(total_possible, 1)
        
        return MemoryProfile(
            strategy=strategy,
            peak_qubits=num_qubits,
            total_time_steps=time_steps,
            memory_footprint_mb=memory_mb,
            qubit_utilization=utilization,
            gate_count=len(gates),
            depth=compiled.get('depth', 0),
        )
    
    def space_time_tradeoff(self, circuit: Dict[str, Any],
                           target_metric: str = "balanced") -> Dict[str, Any]:
        """
        Optimize space-time tradeoff.
        
        Args:
            circuit: Circuit to optimize
            target_metric: 'minimize_space', 'minimize_time', or 'balanced'
            
        Returns:
            Dict with tradeoff analysis and recommendation
        """
        profiles = self.profile_strategies(circuit)
        
        if not profiles:
            return {'error': 'No profiles generated'}
        
        # Find best for each metric
        best_space = min(profiles, key=lambda p: p.peak_qubits)
        best_time = min(profiles, key=lambda p: p.total_time_steps)
        best_balanced = min(profiles, key=lambda p: p.peak_qubits + p.total_time_steps)
        
        recommendations = {
            'minimize_space': best_space,
            'minimize_time': best_time,
            'balanced': best_balanced,
        }
        
        return {
            'profiles': [p.to_dict() for p in profiles],
            'recommendation': recommendations.get(target_metric, best_balanced).to_dict(),
            'target_metric': target_metric,
        }


class CircuitCutter:
    """
    Cuts large circuits into smaller subcircuits.
    
    Trades qubits for classical communication overhead.
    """
    
    def __init__(self):
        self.cut_history: List[Dict[str, Any]] = []
    
    def cut(self, circuit: Dict[str, Any], 
           max_qubits: int = 10,
           strategy: str = "balanced") -> CutCircuit:
        """
        Cut circuit into subcircuits.
        
        Args:
            circuit: Circuit to cut
            max_qubits: Maximum qubits per subcircuit
            strategy: Cutting strategy
            
        Returns:
            CutCircuit with subcircuits
        """
        gates = circuit.get('gates', [])
        num_qubits = circuit.get('num_qubits', 0)
        
        if num_qubits <= max_qubits:
            # No cutting needed
            return CutCircuit(
                original_size=len(gates),
                num_subcircuits=1,
                subcircuits=[circuit],
                cut_qubits=[],
                classical_communication_cost=0.0,
            )
        
        # Simple cutting: split by qubits
        subcircuits = []
        cut_qubits = []
        qubit_assignment = {}  # qubit -> subcircuit_id
        
        current_subcircuit = []
        current_qubits = set()
        subcircuit_id = 0
        
        for gate in gates:
            gate_qubits = set(self._extract_qubits(gate))
            
            # Check if fits in current subcircuit
            if len(current_qubits | gate_qubits) <= max_qubits:
                current_subcircuit.append(gate)
                current_qubits |= gate_qubits
            else:
                # Start new subcircuit
                if current_subcircuit:
                    subcircuits.append({
                        'gates': current_subcircuit,
                        'num_qubits': len(current_qubits),
                    })
                
                current_subcircuit = [gate]
                current_qubits = gate_qubits
        
        # Don't forget last subcircuit
        if current_subcircuit:
            subcircuits.append({
                'gates': current_subcircuit,
                'num_qubits': len(current_qubits),
            })
        
        # Calculate communication cost
        # Simplified: proportional to cuts
        comm_cost = len(subcircuits) * 10.0  # 10 units per cut
        
        result = CutCircuit(
            original_size=len(gates),
            num_subcircuits=len(subcircuits),
            subcircuits=subcircuits,
            cut_qubits=cut_qubits,
            classical_communication_cost=comm_cost,
        )
        
        self.cut_history.append({
            'original_size': result.original_size,
            'num_subcircuits': result.num_subcircuits,
            'timestamp': len(self.cut_history),
        })
        
        return result
    
    def _extract_qubits(self, gate: Any) -> List[int]:
        """Extract qubits from gate."""
        if isinstance(gate, tuple) and len(gate) > 1:
            if isinstance(gate[1], list):
                return gate[1]
            elif isinstance(gate[1], int):
                return [gate[1]]
        return []
    
    def analyze_cut(self, cut_result: CutCircuit) -> Dict[str, Any]:
        """Analyze a circuit cut."""
        subcircuit_sizes = [len(sc.get('gates', [])) for sc in cut_result.subcircuits]
        
        return {
            'num_subcircuits': cut_result.num_subcircuits,
            'subcircuit_sizes': subcircuit_sizes,
            'avg_subcircuit_size': np.mean(subcircuit_sizes) if subcircuit_sizes else 0,
            'communication_cost': cut_result.classical_communication_cost,
            'qubits_saved': cut_result.original_size - sum(subcircuit_sizes),
            'efficiency': cut_result.original_size / max(cut_result.num_subcircuits, 1),
        }


class MemoryProfiler:
    """
    Profiles memory usage for different compilation strategies.
    """
    
    def __init__(self):
        self.profiles: List[MemoryProfile] = []
    
    def profile(self, circuit: Dict[str, Any],
                strategies: Optional[List[OptimizationStrategy]] = None) -> List[MemoryProfile]:
        """
        Profile memory for multiple strategies.
        
        Args:
            circuit: Circuit to profile
            strategies: Strategies to profile (all if None)
            
        Returns:
            List of MemoryProfiles
        """
        compiler = MemoryAwareCompiler()
        profiles = compiler.profile_strategies(circuit)
        self.profiles.extend(profiles)
        return profiles
    
    def compare(self, profile1: MemoryProfile, profile2: MemoryProfile) -> Dict[str, Any]:
        """Compare two memory profiles."""
        return {
            'qubit_diff': profile2.peak_qubits - profile1.peak_qubits,
            'time_diff': profile2.total_time_steps - profile1.total_time_steps,
            'memory_diff_mb': profile2.memory_footprint_mb - profile1.memory_footprint_mb,
            'efficiency_ratio': profile2.efficiency() / max(profile1.efficiency(), 1e-10),
            'recommendation': 'profile2' if profile2.efficiency() > profile1.efficiency() else 'profile1',
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all profiles."""
        if not self.profiles:
            return {'total_profiles': 0,
                    'message': 'No profiles available'}
        
        peak_qubits = [p.peak_qubits for p in self.profiles]
        memory_mb = [p.memory_footprint_mb for p in self.profiles]
        
        return {
            'total_profiles': len(self.profiles),
            'avg_peak_qubits': float(np.mean(peak_qubits)),
            'min_peak_qubits': int(min(peak_qubits)),
            'max_peak_qubits': int(max(peak_qubits)),
            'avg_memory_mb': float(np.mean(memory_mb)),
            'total_memory_mb': float(sum(memory_mb)),
        }
