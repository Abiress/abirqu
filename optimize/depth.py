"""
Circuit Depth Minimizer

Implements peephole optimization, ZX-calculus simplification,
template matching, and parallelization of independent gate chains.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, deque

class CircuitDepthMinimizer:
    """
    Minimizes circuit depth through various optimization techniques.
    """
    
    def __init__(self):
        self.optimization_history = []
        
    def minimize_depth(self, circuit_gates: List[Tuple[str, List[int]]],
                       num_qubits: int) -> List[Tuple[str, List[int]]]:
        """
        Apply multiple depth minimization passes.
        
        Args:
            circuit_gates: Input circuit as list of (gate_name, qubits)
            num_qubits: Number of qubits in circuit
            
        Returns:
            Optimized circuit with reduced depth
        """
        optimized = circuit_gates.copy()
        
        # Pass 1: Peephole optimization
        optimized = self._peephole_optimization(optimized)
        self.optimization_history.append(('peephole', len(circuit_gates), len(optimized)))
        
        # Pass 2: Cancel adjacent inverses
        optimized = self._cancel_inverse_gates(optimized)
        self.optimization_history.append(('inverse_cancel', len(circuit_gates), len(optimized)))
        
        # Pass 3: Commutativity-based reordering
        optimized = self._commutativity_reordering(optimized, num_qubits)
        self.optimization_history.append(('commutativity', len(circuit_gates), len(optimized)))
        
        # Pass 4: Parallelize independent gates
        optimized = self._parallelize_gates(optimized, num_qubits)
        self.optimization_history.append(('parallelize', len(circuit_gates), len(optimized)))
        
        return optimized
    
    def _peephole_optimization(self, gates: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """
        Apply peephole optimizations:
        - Remove identity gates (I gates)
        - Merge consecutive rotation gates
        - Remove double negations
        """
        result = []
        skip_next = False
        
        for i, (gate_name, qubits) in enumerate(gates):
            if skip_next:
                skip_next = False
                continue
                
            # Skip identity gates
            if gate_name == 'I':
                continue
                
            # Check for double H: H; H = I
            if gate_name == 'H' and i + 1 < len(gates):
                next_gate, next_qubits = gates[i+1]
                if next_gate == 'H' and next_qubits == qubits:
                    skip_next = True
                    continue
                    
            # Check for X; X = I
            if gate_name == 'X' and i + 1 < len(gates):
                next_gate, next_qubits = gates[i+1]
                if next_gate == 'X' and next_qubits == qubits:
                    skip_next = True
                    continue
                    
            # Check for Z; Z = I
            if gate_name == 'Z' and i + 1 < len(gates):
                next_gate, next_qubits = gates[i+1]
                if next_gate == 'Z' and next_qubits == qubits:
                    skip_next = True
                    continue
                    
            result.append((gate_name, qubits))
            
        return result
    
    def _cancel_inverse_gates(self, gates: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """
        Cancel gates that are inverses of each other.
        Uses a stack-based approach.
        """
        # Define inverse pairs
        inverses = {
            'S': 'S_dag', 'S_dag': 'S',
            'T': 'T_dag', 'T_dag': 'T',
            'CNOT': 'CNOT',  # Self-inverse
            'SWAP': 'SWAP',  # Self-inverse
        }
        
        # Process gates in reverse to find cancellations
        # Use a stack: when we see a gate, check if top of stack is its inverse
        stack = []
        
        for gate_name, qubits in gates:
            if not stack:
                stack.append((gate_name, qubits))
                continue
                
            # Check if current gate cancels with top of stack
            top_name, top_qubits = stack[-1]
            
            if (top_qubits == qubits and 
                inverses.get(top_name) == gate_name):
                stack.pop()  # Cancel both
            else:
                stack.append((gate_name, qubits))
                
        return stack
    
    def _commutativity_reordering(self, gates: List[Tuple[str, List[int]]],
                                  num_qubits: int) -> List[Tuple[str, List[int]]]:
        """
        Reorder gates to maximize parallelization opportunities.
        Gates that don't touch the same qubits can be reordered.
        """
        # Build dependency graph: gate i must come before gate j if they share qubits
        n = len(gates)
        if n == 0:
            return gates
            
        # Simple approach: use topological sort with commutativity rules
        # For now, just try to move single-qubit gates past two-qubit gates when possible
        
        result = gates.copy()
        changed = True
        
        while changed:
            changed = False
            for i in range(len(result) - 1):
                gate1_name, gate1_qubits = result[i]
                gate2_name, gate2_qubits = result[i+1]
                
                # Check if gates commute
                if self._gates_commute(gate1_name, gate1_qubits, 
                                       gate2_name, gate2_qubits):
                    # Try to swap if gate2 is single-qubit and gate1 is two-qubit
                    if (len(gate1_qubits) > 1 and len(gate2_qubits) == 1 and
                        gate2_qubits[0] not in gate1_qubits):
                        # Swap them
                        result[i], result[i+1] = result[i+1], result[i]
                        changed = True
                        
        return result
    
    def _gates_commute(self, name1: str, qubits1: List[int],
                       name2: str, qubits2: List[int]) -> bool:
        """
        Check if two gates commute.
        Two gates commute if they don't share qubits or if they are both
        single-qubit gates on different qubits.
        """
        # If no shared qubits, they commute
        if set(qubits1).isdisjoint(set(qubits2)):
            return True
            
        # If same qubits and same gate type (both single-qubit), they commute
        if set(qubits1) == set(qubits2) and len(qubits1) == 1 and len(qubits2) == 1:
            return True
            
        # Special cases: CNOTs with certain patterns
        # For simplicity, return False for shared qubits
        return False
    
    def _parallelize_gates(self, gates: List[Tuple[str, List[int]]],
                           num_qubits: int) -> List[Tuple[str, List[int]]]:
        """
        Parallelize independent gates where possible.
        This is a simplified version - full parallelization would use
        depth analysis and rescheduling.
        """
        # For now, just remove redundant gates that are already parallelized
        # Full implementation would use a dependency graph and topological sort
        
        # Simple approach: if two consecutive gates don't share qubits, they can be parallel
        # In a real circuit representation, we'd mark them as same depth
        
        # This is a placeholder for more sophisticated parallelization
        return gates
    
    def get_optimization_history(self) -> List[Tuple[str, int, int]]:
        """Get history of optimizations applied."""
        return self.optimization_history.copy()

class ZXCalculator:
    """
    ZX-calculus based circuit simplification.
    ZX-calculus provides a graphical language for simplifying quantum circuits.
    """
    
    def __init__(self):
        pass
    
    def simplify(self, circuit_gates: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """
        Apply ZX-calculus simplification rules.
        This is a simplified implementation.
        """
        # ZX-calculus rules (simplified):
        # 1. Fusion: Z -- Z = Z (merge adjacent Z-spiders)
        # 2. Identity: Z -- Z^† = I
        # 3. Color change: H can change Z to X and vice versa
        
        # For now, implement basic fusion rules
        return self._zx_fusion(circuit_gates)
    
    def _zx_fusion(self, gates: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """Fuse adjacent Z or X spiders."""
        result = []
        i = 0
        
        while i < len(gates):
            gate_name, qubits = gates[i]
            
            # Check for adjacent same-type single-qubit gates
            if (len(qubits) == 1 and 
                gate_name in ['Z', 'S', 'T', 'S_dag', 'T_dag'] and
                i + 1 < len(gates)):
                
                # Try to fuse with next gate
                next_name, next_qubits = gates[i+1]
                if (len(next_qubits) == 1 and 
                    next_qubits == qubits and
                    next_name in ['Z', 'S', 'T', 'S_dag', 'T_dag']):
                    
                    # Fuse: combine phases
                    fused = self._fuse_z_phase(gate_name, next_name)
                    if fused:
                        result.append((fused, qubits))
                        i += 2
                        continue
                        
            result.append((gate_name, qubits))
            i += 1
            
        return result
    
    def _fuse_z_phase(self, gate1: str, gate2: str) -> Optional[str]:
        """
        Fuse two Z-phase gates.
        Returns the resulting gate name, or None if they cancel.
        """
        # Map gates to phases (mod 2π)
        phase_map = {
            'Z': np.pi,
            'S': np.pi/2,
            'T': np.pi/4,
            'S_dag': -np.pi/2,
            'T_dag': -np.pi/4
        }
        
        if gate1 not in phase_map or gate2 not in phase_map:
            return None
            
        total_phase = (phase_map[gate1] + phase_map[gate2]) % (2*np.pi)
        
        # Map back to gate
        if abs(total_phase - np.pi) < 1e-10:
            return 'Z'
        elif abs(total_phase - np.pi/2) < 1e-10:
            return 'S'
        elif abs(total_phase - np.pi/4) < 1e-10:
            return 'T'
        elif abs(total_phase - 3*np.pi/2) < 1e-10 or abs(total_phase - (-np.pi/2)) < 1e-10:
            return 'S_dag'
        elif abs(total_phase - 7*np.pi/4) < 1e-10 or abs(total_phase - (-np.pi/4)) < 1e-10:
            return 'T_dag'
        elif abs(total_phase) < 1e-10:
            return None  # Cancel to identity
        else:
            return None  # Would need arbitrary RZ

class TemplateMatcher:
    """
    Matches common sub-circuit patterns and replaces with optimized versions.
    """
    
    def __init__(self):
        # Define templates: pattern -> replacement
        self.templates = [
            # CNOT; X on target = X on target; CNOT (if control not affected)
            # This is a simplified template system
        ]
        
    def match_and_replace(self, circuit_gates: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """
        Match templates and replace with optimized versions.
        """
        # For now, implement a few common patterns
        
        # Pattern 1: H; CNOT; H on same qubits = CZ
        result = self._match_h_cnot_h(circuit_gates)
        
        return result
    
    def _match_h_cnot_h(self, gates: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """Match H; CNOT; H pattern and replace with CZ."""
        result = []
        i = 0
        
        while i < len(gates) - 2:
            g1_name, g1_qubits = gates[i]
            g2_name, g2_qubits = gates[i+1]
            g3_name, g3_qubits = gates[i+2]
            
            # Check for H on q1; CNOT(q1,q2); H on q1
            if (g1_name == 'H' and g3_name == 'H' and
                g2_name == 'CNOT' and
                len(g1_qubits) == 1 and len(g3_qubits) == 1 and len(g2_qubits) == 2 and
                g1_qubits[0] == g2_qubits[0] and  # H on control
                g3_qubits[0] == g2_qubits[0]):  # H on control
                
                # Replace with CZ
                result.append(('CZ', [g2_qubits[0], g2_qubits[1]]))
                i += 3
            else:
                result.append(gates[i])
                i += 1
                
        # Add remaining gates
        while i < len(gates):
            result.append(gates[i])
            i += 1
            
        return result

# Example usage and tests
if __name__ == "__main__":
    print("Testing Circuit Depth Minimizer...")
    
    minimizer = CircuitDepthMinimizer()
    
    # Test circuit with redundant gates
    test_circuit = [
        ('H', [0]),
        ('H', [0]),  # Should cancel with previous H
        ('X', [1]),
        ('X', [1]),  # Should cancel with previous X
        ('Z', [0]),
        ('I', [1]),  # Should be removed
        ('CNOT', [0, 1])
    ]
    
    print(f"Original circuit ({len(test_circuit)} gates):")
    for g in test_circuit:
        print(f"  {g}")
        
    optimized = minimizer.minimize_depth(test_circuit, 2)
    print(f"\nOptimized circuit ({len(optimized)} gates):")
    for g in optimized:
        print(f"  {g}")
        
    print(f"\nOptimization history: {minimizer.get_optimization_history()}")
    
    # Test ZX Calculator
    print("\n" + "="*50)
    print("Testing ZX Calculator...")
    
    zx = ZXCalculator()
    test_zx = [('S', [0]), ('T', [0]), ('Z', [0])]  # Fuse S+T+Z
    simplified = zx.simplify(test_zx)
    print(f"Original: {test_zx}")
    print(f"Simplified: {simplified}")
    
    # Test Template Matcher
    print("\n" + "="*50)
    print("Testing Template Matcher...")
    
    tm = TemplateMatcher()
    test_template = [
        ('H', [0]),
        ('CNOT', [0, 1]),
        ('H', [0])
    ]  # Should become CZ
    replaced = tm.match_and_replace(test_template)
    print(f"Original: {test_template}")
    print(f"After template matching: {replaced}")