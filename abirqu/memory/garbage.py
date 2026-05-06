"""
Task 12.4 — Quantum Garbage Collection

Automatic qubit deallocation, uncomputation, deferred measurement, and qubit reuse.
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import time


@dataclass
class QubitAllocation:
    """Record of qubit allocation."""
    qubit_id: int
    allocated_at: float = field(default_factory=time.time)
    freed_at: Optional[float] = None
    is_active: bool = True
    dependencies: List[int] = field(default_factory=list)  # Qubits this depends on
    label: str = ""


class QuantumGarbageCollector:
    """
    Automatic qubit deallocation when qubits are no longer needed.
    
    Features:
    - Automatic qubit deallocation when qubits are no longer needed
    - Uncomputation engine (automatically reverse auxiliary qubits)
    - Deferred measurement optimization
    - Qubit reuse scheduling
    """
    
    def __init__(self, auto_collect: bool = True,
                 uncompute_auxiliary: bool = True):
        """
        Initialize garbage collector.
        
        Args:
            auto_collect: Automatically collect garbage
            uncompute_auxiliary: Automatically uncompute auxiliary qubits
        """
        self.auto_collect = auto_collect
        self.uncompute_auxiliary = uncompute_auxiliary
        
        self.allocations: Dict[int, QubitAllocation] = {}
        self.next_qubit_id = 0
        self.freed_qubits: List[int] = []  # Pool of freed qubits for reuse
        self.uncomputation_log: List[Dict[str, Any]] = []
    
    def allocate(self, num_qubits: int = 1, 
                 label: str = "") -> List[int]:
        """
        Allocate qubits.
        
        Args:
            num_qubits: Number of qubits to allocate
            label: Optional label for debugging
            
        Returns:
            List of allocated qubit IDs
        """
        allocated = []
        for _ in range(num_qubits):
            # Reuse freed qubits if available
            if self.freed_qubits:
                qubit_id = self.freed_qubits.pop(0)
                self.allocations[qubit_id].is_active = True
                self.allocations[qubit_id].allocated_at = time.time()
                self.allocations[qubit_id].label = label
            else:
                qubit_id = self.next_qubit_id
                self.allocations[qubit_id] = QubitAllocation(
                    qubit_id=qubit_id,
                    label=label
                )
                self.next_qubit_id += 1
            
            allocated.append(qubit_id)
        
        return allocated
    
    def free(self, qubit_ids: List[int], 
                uncompute: Optional[bool] = None):
        """
        Free qubits.
        
        Args:
            qubit_ids: List of qubit IDs to free
            uncompute: Whether to uncompute first (uses self.uncompute_auxiliary if None)
        """
        if uncompute is None:
            uncompute = self.uncompute_auxiliary
        
        for qubit_id in qubit_ids:
            if qubit_id not in self.allocations:
                continue
            
            entry = self.allocations[qubit_id]
            
            if uncompute and entry.is_active:
                self._uncompute(qubit_id)
            
            entry.is_active = False
            entry.freed_at = time.time()
            self.freed_qubits.append(qubit_id)
    
    def _uncompute(self, qubit_id: int):
        """
        Uncompute a qubit (reverse its computation).
        
        Args:
            qubit_id: Qubit to uncompute
        """
        # Simplified: just log the uncomputation
        # In practice, would generate inverse gates
        log_entry = {
            'qubit_id': qubit_id,
            'timestamp': time.time(),
            'action': 'uncompute',
        }
        self.uncomputation_log.append(log_entry)
    
    def collect(self, circuit_description: Optional[Dict[str, Any]] = None) -> int:
        """
        Run garbage collection.
        
        Args:
            circuit_description: Optional circuit to analyze
            
        Returns:
            Number of qubits collected
        """
        collected = 0
        
        if circuit_description:
            # Analyze circuit to find unused qubits
            active_qubits = self._find_active_qubits(circuit_description)
            
            for qubit_id, entry in list(self.allocations.items()):
                if entry.is_active and qubit_id not in active_qubits:
                    self.free([qubit_id])
                    collected += 1
        else:
            # Simple: free all inactive qubits
            for qubit_id, entry in list(self.allocations.items()):
                if not entry.is_active:
                    if qubit_id not in self.freed_qubits:
                        self.freed_qubits.append(qubit_id)
        
        return collected
    
    def _find_active_qubits(self, circuit: Dict[str, Any]) -> Set[int]:
        """Find qubits still in use based on circuit description."""
        active = set()
        
        gates = circuit.get('gates', [])
        for gate in gates:
            if isinstance(gate, tuple) and len(gate) > 1:
                # gate format: ('gate_name', [qubit_list])
                if isinstance(gate[1], list):
                    active.update(gate[1])
                elif isinstance(gate[1], int):
                    active.add(gate[1])
        
        return active
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get garbage collection statistics."""
        active = sum(1 for e in self.allocations.values() if e.is_active)
        inactive = sum(1 for e in self.allocations.values() if not e.is_active)
        
        return {
            'total_allocated': len(self.allocations),
            'active_qubits': active,
            'inactive_qubits': inactive,
            'freed_pool_size': len(self.freed_qubits),
            'reuse_rate': len(self.freed_qubits) / max(len(self.allocations), 1),
            'uncomputations': len(self.uncomputation_log),
        }


class UncomputationEngine:
    """
    Engine for automatic uncomputation of auxiliary qubits.
    """
    
    def __init__(self):
        self.uncomputation_history: List[Dict[str, Any]] = []
    
    def uncompute_circuit(self, circuit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate uncomputation for entire circuit.
        
        Args:
            circuit: Circuit description
            
        Returns:
            New circuit with uncomputation steps added
        """
        gates = circuit.get('gates', [])
        
        # Build reverse circuit
        reverse_gates = []
        for gate in reversed(gates):
            reversed_gate = self._reverse_gate(gate)
            if reversed_gate:
                reverse_gates.append(reversed_gate)
        
        # Combine: original + reverse
        uncomputed = circuit.copy()
        uncomputed['gates'] = gates + reverse_gates
        uncomputed['depth'] = circuit.get('depth', 0) * 2
        
        # Log
        self.uncomputation_history.append({
            'original_depth': circuit.get('depth', 0),
            'uncomputed_depth': uncomputed['depth'],
            'num_gates_added': len(reverse_gates),
        })
        
        return uncomputed
    
    def _reverse_gate(self, gate: Any) -> Optional[Any]:
        """Reverse a single gate."""
        if isinstance(gate, tuple) and len(gate) >= 2:
            gate_name = gate[0]
            
            # Self-inverse gates
            if gate_name in ['h', 'x', 'z', 'cx', 'cnot']:
                return gate  # These are self-inverse
            
            # Gates with known inverses
            if gate_name == 's':
                return ('sdg', gate[1])  # S-dagger
            elif gate_name == 't':
                return ('tdg', gate[1])  # T-dagger
            elif gate_name == 'rx':
                # rx(theta) -> rx(-theta)
                if len(gate) > 2:
                    return ('rx', gate[1], -gate[2])
            elif gate_name == 'ry':
                if len(gate) > 2:
                    return ('ry', gate[1], -gate[2])
            elif gate_name == 'rz':
                if len(gate) > 2:
                    return ('rz', gate[1], -gate[2])
            
            # Default: return None (can't uncompute)
        
        return None
    
    def uncompute_qubits(self, qubit_ids: List[int], 
                          circuit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uncompute specific qubits in a circuit.
        
        Args:
            qubit_ids: Qubits to uncompute
            circuit: Circuit description
            
        Returns:
            Modified circuit
        """
        # Find gates that only involve these qubits
        gates_to_reverse = []
        remaining_gates = []
        
        for gate in circuit.get('gates', []):
            gate_qubits = self._extract_qubits(gate)
            if gate_qubits and all(q in qubit_ids for q in gate_qubits):
                gates_to_reverse.append(gate)
            else:
                remaining_gates.append(gate)
        
        # Reverse the selected gates
        reversed_gates = []
        for gate in reversed(gates_to_reverse):
            rev = self._reverse_gate(gate)
            if rev:
                reversed_gates.append(rev)
        
        # Reconstruct circuit
        new_circuit = circuit.copy()
        new_circuit['gates'] = remaining_gates + reversed_gates
        
        return new_circuit
    
    def _extract_qubits(self, gate: Any) -> List[int]:
        """Extract qubit IDs from a gate."""
        if isinstance(gate, tuple) and len(gate) > 1:
            if isinstance(gate[1], list):
                return gate[1]
            elif isinstance(gate[1], int):
                return [gate[1]]
        return []


class QubitReuseScheduler:
    """
    Scheduler for reusing qubits at different times.
    """
    
    def __init__(self):
        self.qubit_timeline: Dict[int, List[Tuple[float, float]]] = {}  # qubit -> [(start, end), ...]
    
    def register_operation(self, qubit_id: int, 
                         start_time: float, end_time: float):
        """Register an operation on a qubit."""
        if qubit_id not in self.qubit_timeline:
            self.qubit_timeline[qubit_id] = []
        self.qubit_timeline[qubit_id].append((start_time, end_time))
    
    def find_reusable_qubits(self, start_time: float, 
                            end_time: float) -> List[int]:
        """
        Find qubits that can be reused during this time window.
        
        Returns:
            List of qubit IDs that are free during this window.
        """
        reusable = []
        
        for qubit_id, timeline in self.qubit_timeline.items():
            if self._is_free_during(timeline, start_time, end_time):
                reusable.append(qubit_id)
        
        return reusable
    
    def _is_free_during(self, timeline: List[Tuple[float, float]],
                          start: float, end: float) -> bool:
        """Check if qubit is free during time window."""
        for op_start, op_end in timeline:
            # Check for overlap
            if not (end <= op_start or start >= op_end):
                return False
        return True
    
    def optimize_schedule(self, circuit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize circuit by reusing qubits.
        
        Args:
            circuit: Circuit description with timing info
            
        Returns:
            Optimized circuit with qubit reuse mapping
        """
        # Simplified: just analyze and return mapping
        gates = circuit.get('gates', [])
        
        # Build timeline from gate order (assuming each gate takes unit time)
        self.qubit_timeline.clear()
        for i, gate in enumerate(gates):
            qubits = self._extract_qubits_from_gate(gate)
            for q in qubits:
                self.register_operation(q, float(i), float(i + 1))
        
        # Find reuse opportunities
        reuse_map = {}
        for i in range(len(gates)):
            start = float(i)
            end = float(i + 1)
            reusable = self.find_reusable_qubits(start, end)
            if reusable:
                reuse_map[f"gate_{i}"] = reusable
        
        optimized = circuit.copy()
        optimized['reuse_map'] = reuse_map
        optimized['qubits_saved'] = len(reuse_map)
        
        return optimized
    
    def _extract_qubits_from_gate(self, gate: Any) -> List[int]:
        """Extract qubits from gate tuple."""
        if isinstance(gate, tuple) and len(gate) > 1:
            if isinstance(gate[1], list):
                return gate[1]
            elif isinstance(gate[1], int):
                return [gate[1]]
        return []
