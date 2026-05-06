"""Debug Agent for AbirQu. Copyright 2026 Abir Maheshwari"""
from typing import Optional, Dict, List, Any
from ..core.circuit import Circuit
from ..core.gates import Gate

class DebuggingAgent:
    """Identifies issues in quantum circuits."""
    
    def __init__(self):
        self.name = "DebugAgent"
        
    def debug(self, circuit: Circuit) -> List[Dict[str, Any]]:
        """Identify issues in a quantum circuit."""
        issues = []
        
        # Check for unterminated qubits
        used_qubits = set()
        for gate, qubits in circuit.gates:
            used_qubits.update(qubits)
            
        unused = set(range(circuit.num_qubits)) - used_qubits
        if unused:
            issues.append({
                'type': 'unused_qubit',
                'severity': 'warning',
                'message': f"Qubits {unused} are not used in any gate",
                'qubits': list(unused)
            })
            
        # Check for consecutive identical gates that cancel
        for i in range(len(circuit.gates) - 1):
            gate1, qubits1 = circuit.gates[i]
            gate2, qubits2 = circuit.gates[i+1]
            
            if gate1.name == gate2.name and qubits1 == qubits2:
                # Check if they cancel
                if gate1.name in ['X', 'Y', 'Z', 'H']:
                    issues.append({
                        'type': 'gate_cancellation',
                        'severity': 'info',
                        'message': f"Gates at positions {i} and {i+1} may cancel",
                        'position': i
                    })
                    
        # Check for redundant measurements
        measured_qubits = set()
        for m in circuit.measurements:
            if m['qubit'] in measured_qubits:
                issues.append({
                    'type': 'redundant_measurement',
                    'severity': 'warning',
                    'message': f"Qubit {m['qubit']} is measured multiple times",
                    'qubit': m['qubit']
                })
            measured_qubits.add(m['qubit'])
            
        # Check depth vs gate count
        if circuit.depth() > len(circuit.gates) * 2:
            issues.append({
                'type': 'high_depth',
                'severity': 'info',
                'message': f"Circuit depth ({circuit.depth()}) is much higher than gate count",
                'depth': circuit.depth(),
                'gate_count': len(circuit.gates)
            })
            
        return issues
        
    def verify(self, circuit: Circuit) -> Dict[str, Any]:
        """Verify circuit correctness."""
        issues = self.debug(circuit)
        
        return {
            'valid': len([i for i in issues if i['severity'] == 'error']) == 0,
            'issues': issues,
            'issue_count': len(issues),
            'warnings': len([i for i in issues if i['severity'] == 'warning']),
            'errors': len([i for i in issues if i['severity'] == 'error'])
        }
        
    def suggest_fixes(self, circuit: Circuit) -> List[Dict[str, Any]]:
        """Suggest fixes for identified issues."""
        issues = self.debug(circuit)
        suggestions = []
        
        for issue in issues:
            if issue['type'] == 'unused_qubit':
                suggestions.append({
                    'issue': issue,
                    'fix': f"Remove unused qubits or add gates to qubits {issue['qubits']}",
                    'action': 'modify_circuit'
                })
            elif issue['type'] == 'gate_cancellation':
                suggestions.append({
                    'issue': issue,
                    'fix': 'Remove redundant gates',
                    'action': 'remove_gates',
                    'positions': [issue['position'], issue['position'] + 1]
                })
                
        return suggestions
