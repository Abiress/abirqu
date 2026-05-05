"""
Pattern Detection Engine

Detects design patterns in existing circuits.
Implements pattern-specific optimization rules.
Supports anti-pattern detection with suggested fixes.
Builds metrics dashboard showing pattern prevalence and code quality.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any
from collections import defaultdict

class PatternDetector:
    """
    Engine that detects design patterns and anti-patterns in quantum circuits.
    """
    
    def __init__(self):
        self.pattern_counts = defaultdict(int)
        self.anti_pattern_counts = defaultdict(int)
        self.circuit_metrics = {}
        
    def analyze_circuit(self, circuit: List[Tuple[str, List[int]]]) -> Dict[str, Any]:
        """
        Analyze a circuit for patterns and anti-patterns.
        
        Args:
            circuit: List of (gate_name, qubits) tuples
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            'patterns': [],
            'anti_patterns': [],
            'metrics': {},
            'suggestions': []
        }
        
        # Detect patterns
        results['patterns'].extend(self._detect_initialization(circuit))
        results['patterns'].extend(self._detect_superposition(circuit))
        results['patterns'].extend(self._detect_entanglement(circuit))
        results['patterns'].extend(self._detect_oracle(circuit))
        
        # Detect anti-patterns
        results['anti_patterns'].extend(self._detect_redundant_gates(circuit))
        results['anti_patterns'].extend(self._detect_deep_circuits(circuit))
        results['anti_patterns'].extend(self._detect_unused_qubits(circuit))
        
        # Compute metrics
        results['metrics'] = self._compute_metrics(circuit)
        
        # Generate suggestions
        results['suggestions'] = self._generate_suggestions(results)
        
        # Update internal counts
        for p in results['patterns']:
            self.pattern_counts[p['type']] += 1
        for ap in results['anti_patterns']:
            self.anti_pattern_counts[ap['type']] += 1
            
        return results
    
    def _detect_initialization(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """Detect initialization patterns."""
        patterns = []
        if not circuit:
            return patterns
            
        # Check first gates on each qubit
        first_gates = {}
        for gate, qubits in circuit:
            for q in qubits:
                if q not in first_gates:
                    first_gates[q] = gate
                    
        # Look for initialization gates (X, H, etc.)
        init_gates = {'X', 'H', 'RX', 'RY', 'RZ', 'I'}
        init_qubits = [q for q, g in first_gates.items() if g in init_gates]
        
        if init_qubits:
            patterns.append({
                'type': 'initialization',
                'qubits': init_qubits,
                'confidence': 0.9,
                'description': f'Initialization on qubits {init_qubits}'
            })
            
        return patterns
    
    def _detect_superposition(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """Detect superposition patterns."""
        patterns = []
        
        # Look for Hadamard gates
        h_qubits = set()
        for gate, qubits in circuit:
            if gate == 'H':
                h_qubits.update(qubits)
                
        if h_qubits:
            patterns.append({
                'type': 'superposition',
                'qubits': list(h_qubits),
                'confidence': 0.85,
                'description': f'Superposition created on qubits {list(h_qubits)}'
            })
            
        return patterns
    
    def _detect_entanglement(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """Detect entanglement patterns."""
        patterns = []
        
        # Look for 2-qubit gates
        entangle_gates = {'CNOT', 'CZ', 'SWAP', 'TOFFOLI'}
        entangled_pairs = set()
        
        for gate, qubits in circuit:
            if gate in entangle_gates and len(qubits) >= 2:
                entangled_pairs.add(tuple(sorted(qubits[:2])))
                
        if entangled_pairs:
            patterns.append({
                'type': 'entanglement',
                'pairs': [list(p) for p in entangled_pairs],
                'confidence': 0.95,
                'description': f'Entanglement between {len(entangled_pairs)} qubit pairs'
            })
            
        return patterns
    
    def _detect_oracle(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """Detect oracle patterns."""
        patterns = []
        
        # Look for multi-controlled gates
        multi_qubit_gates = {'TOFFOLI', 'MCZ', 'MCX'}
        oracle_found = False
        
        for gate, qubits in circuit:
            if gate in multi_qubit_gates or (gate in ['CZ', 'CNOT'] and len(qubits) > 2):
                oracle_found = True
                break
                
        if oracle_found:
            patterns.append({
                'type': 'oracle',
                'confidence': 0.8,
                'description': 'Oracle-like multi-controlled operation detected'
            })
            
        return patterns
    
    def _detect_redundant_gates(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """Detect redundant gate sequences (anti-pattern)."""
        anti_patterns = []
        
        # Check for adjacent cancelling gates
        for i in range(len(circuit) - 1):
            g1, q1 = circuit[i]
            g2, q2 = circuit[i+1]
            
            if q1 == q2 and g1 == g2:
                # Same gate twice (for some gates) = identity
                if g1 in ['H', 'X', 'Y', 'Z']:
                    anti_patterns.append({
                        'type': 'redundant_gates',
                        'position': [i, i+1],
                        'gates': [g1, g2],
                        'severity': 'high',
                        'description': f'Redundant {g1} gates at positions {i}, {i+1}'
                    })
                    
        return anti_patterns
    
    def _detect_deep_circuits(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """Detect unnecessarily deep circuits (anti-pattern)."""
        anti_patterns = []
        
        # Simple heuristic: circuit depth > 2 * num_qubits = deep
        num_qubits = self._get_num_qubits(circuit)
        depth = len(circuit)
        
        if depth > 2 * num_qubits and num_qubits > 0:
            anti_patterns.append({
                'type': 'deep_circuit',
                'depth': depth,
                'num_qubits': num_qubits,
                'severity': 'medium',
                'description': f'Circuit depth ({depth}) much larger than qubit count ({num_qubits})'
            })
            
        return anti_patterns
    
    def _detect_unused_qubits(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """Detect qubits that are allocated but unused."""
        anti_patterns = []
        
        used_qubits = set()
        for _, qubits in circuit:
            used_qubits.update(qubits)
            
        # Assume qubits are 0..max
        if used_qubits:
            max_qubit = max(used_qubits)
            all_qubits = set(range(max_qubit + 1))
            unused = all_qubits - used_qubits
            
            if unused:
                anti_patterns.append({
                    'type': 'unused_qubits',
                    'unused': list(unused),
                    'severity': 'low',
                    'description': f'Qubits {list(unused)} are unused'
                })
                
        return anti_patterns
    
    def _compute_metrics(self, circuit: List[Tuple[str, List[int]]]) -> Dict[str, Any]:
        """Compute code quality metrics."""
        num_qubits = self._get_num_qubits(circuit)
        depth = len(circuit)
        
        # Gate distribution
        gate_counts = defaultdict(int)
        for gate, _ in circuit:
            gate_counts[gate] += 1
            
        # Two-qubit gate count
        two_qubit_gates = sum(c for g, c in gate_counts.items() 
                               if g in ['CNOT', 'CZ', 'SWAP', 'TOFFOLI'])
        
        metrics = {
            'num_qubits': num_qubits,
            'depth': depth,
            'gate_count': len(circuit),
            'gate_types': dict(gate_counts),
            'two_qubit_gate_count': two_qubit_gates,
            'two_qubit_ratio': two_qubit_gates / len(circuit) if circuit else 0,
            'estimated_fidelity': self._estimate_fidelity(gate_counts)
        }
        
        self.circuit_metrics = metrics
        return metrics
    
    def _estimate_fidelity(self, gate_counts: Dict[str, int]) -> float:
        """Estimate overall circuit fidelity."""
        # Simplified fidelity model
        fidelity = 1.0
        gate_fidelities = {
            'I': 1.0, 'X': 0.9999, 'Y': 0.9999, 'Z': 1.0, 'H': 0.9999,
            'S': 0.9999, 'T': 0.9998, 'CNOT': 0.995, 'CZ': 0.995, 'SWAP': 0.99
        }
        
        for gate, count in gate_counts.items():
            fid = gate_fidelities.get(gate, 0.99)
            fidelity *= fid ** count
            
        return fidelity
    
    def _get_num_qubits(self, circuit: List[Tuple[str, List[int]]]) -> int:
        """Get number of qubits used in circuit."""
        qubits = set()
        for _, q in circuit:
            qubits.update(q)
        return len(qubits)
    
    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        # Based on anti-patterns
        for ap in analysis['anti_patterns']:
            if ap['type'] == 'redundant_gates':
                suggestions.append(f"Remove redundant gates at positions {ap['position']}")
            elif ap['type'] == 'deep_circuit':
                suggestions.append("Consider circuit optimization to reduce depth")
            elif ap['type'] == 'unused_qubits':
                suggestions.append(f"Remove unused qubits: {ap['unused']}")
                
        # Pattern-based suggestions
        pattern_types = [p['type'] for p in analysis['patterns']]
        
        if 'initialization' not in pattern_types:
            suggestions.append("Consider adding proper initialization")
        if 'superposition' not in pattern_types and len(analysis['patterns']) > 0:
            suggestions.append("Consider adding superposition with Hadamard gates")
            
        return suggestions
    
    def get_pattern_metrics(self) -> Dict:
        """Get metrics about pattern usage."""
        total_patterns = sum(self.pattern_counts.values())
        total_anti_patterns = sum(self.anti_pattern_counts.values())
        
        return {
            'pattern_counts': dict(self.pattern_counts),
            'anti_pattern_counts': dict(self.anti_pattern_counts),
            'total_patterns': total_patterns,
            'total_anti_patterns': total_anti_patterns,
            'pattern_density': total_patterns / max(1, total_patterns + total_anti_patterns)
        }

# Example usage and tests
if __name__ == "__main__":
    print("Testing Pattern Detection Engine...")
    
    detector = PatternDetector()
    
    # Test circuit with patterns
    test_circuit = [
        ('H', [0]),  # Superposition
        ('H', [1]),  # Superposition
        ('CNOT', [0, 1]),  # Entanglement
        ('H', [0]),  # Redundant (cancels first H)
        ('H', [0]),  # Redundant
        ('TOFFOLI', [0, 1, 2])  # Oracle-like
    ]
    
    print(f"\nAnalyzing circuit with {len(test_circuit)} gates...")
    results = detector.analyze_circuit(test_circuit)
    
    print(f"\nDetected Patterns:")
    for p in results['patterns']:
        print(f"  - {p['type']}: {p['description']}")
        
    print(f"\nDetected Anti-Patterns:")
    for ap in results['anti_patterns']:
        print(f"  - {ap['type']} (severity: {ap['severity']}): {ap['description']}")
        
    print(f"\nMetrics:")
    for k, v in results['metrics'].items():
        print(f"  {k}: {v}")
        
    print(f"\nSuggestions:")
    for s in results['suggestions']:
        print(f"  - {s}")
        
    print(f"\nPattern Metrics:")
    pm = detector.get_pattern_metrics()
    print(f"  {pm}")