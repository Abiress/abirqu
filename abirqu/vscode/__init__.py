"""VS Code Extension for AbirQu. Copyright 2026 Abir Maheshwari"""
from typing import List, Dict, Any, Optional
from ..core.circuit import Circuit
from ..patterns import PatternDetector, ComponentRegistry

class VSCodeExtension:
    """VS Code extension integration for AbirQu."""
    
    def __init__(self):
        self.extension_id = "abirmaheshwari.abirqu"
        self.version = "0.1.0"
        self.capabilities = [
            'circuit_visualization',
            'syntax_highlighting',
            'pattern_detection',
            'code_completion',
            'simulation_preview'
        ]
        
    def get_extension_manifest(self) -> Dict:
        """Return VS Code extension manifest."""
        return {
            "name": "abirqu",
            "displayName": "AbirQu Quantum Development",
            "description": "Next-generation quantum computing development in VS Code",
            "version": self.version,
            "publisher": "abirmaheshwari",
            "author": "Abir Maheshwari",
            "license": "MIT",
            "engines": {
                "vscode": "^1.60.0"
            },
            "categories": ["Programming Languages", "Snippets"],
            "keywords": ["quantum", "qubit", "circuit", "abirqu"],
            "activationEvents": [
                "onLanguage:python",
                "onCommand:abirqu.createCircuit"
            ],
            "contributes": {
                "commands": [
                    {
                        "command": "abirqu.createCircuit",
                        "title": "AbirQu: Create Circuit"
                    },
                    {
                        "command": "abirqu.runCircuit",
                        "title": "AbirQu: Run Circuit"
                    },
                    {
                        "command": "abirqu.optimizeCircuit",
                        "title": "AbirQu: Optimize Circuit"
                    }
                ],
                "languages": [
                    {
                        "id": "abirqu-qasm",
                        "extensions": [".qasm"],
                        "aliases": ["QASM", "OpenQASM"]
                    }
                ],
                "grammars": [
                    {
                        "language": "abirqu-qasm",
                        "scopeName": "source.qasm",
                        "path": "./syntaxes/qasm.tmLanguage.json"
                    }
                ]
            }
        }
        
    def analyze_python_file(self, code: str) -> Dict[str, Any]:
        """Analyze Python file for AbirQu usage."""
        analysis = {
            'imports': [],
            'circuits': [],
            'patterns_detected': [],
            'suggestions': []
        }
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Check for AbirQu imports
            if 'import abirqu' in line or 'from abirqu' in line:
                analysis['imports'].append({
                    'line': i + 1,
                    'content': line.strip()
                })
            
            # Check for circuit creation
            if 'Circuit(' in line:
                analysis['circuits'].append({
                    'line': i + 1,
                    'content': line.strip()
                })
        
        # Pattern detection (simplified)
        if analysis['circuits']:
            # Create a test circuit for pattern detection
            test_circuit = Circuit(2, 'test')
            test_circuit.h(0).cnot(0, 1)
            
            detector = PatternDetector()
            patterns = detector.detect(test_circuit)
            analysis['patterns_detected'] = patterns
            
            # Suggestions
            if 'bell_pair' in patterns:
                analysis['suggestions'].append("Consider running optimization")
        
        return analysis
        
    def get_code_snippets(self) -> List[Dict]:
        """Return code snippets for IntelliSense."""
        return [
            {
                'label': 'Create Bell Pair',
                'insert_text': 'circuit = Circuit(2, "bell")\\ncircuit.h(0).cnot(0, 1)',
                'detail': 'Creates a Bell pair (|00> + |11>)/sqrt(2)',
                'kind': 'Snippet'
            },
            {
                'label': 'Create GHZ State',
                'insert_text': 'circuit = Circuit({num_qubits}, "ghz")\\ncircuit.h(0)\\nfor i in range(1, {num_qubits}):\\n    circuit.cnot(0, i)',
                'detail': 'Creates a GHZ state (|00...0> + |11...1>)/sqrt(2)',
                'kind': 'Snippet'
            },
            {
                'label': 'VQE Ansatz',
                'insert_text': 'circuit = Circuit({num_qubits}, "vqe")\\nfor q in range({num_qubits}):\\n    circuit.ry(q, params[q])\\nfor q in range({num_qubits}-1):\\n    circuit.cnot(q, q+1)',
                'detail': 'Hardware-efficient VQE ansatz',
                'kind': 'Snippet'
            }
        ]
        
    def visualize_circuit(self, circuit: Circuit) -> Dict:
        """Generate visualization data for circuit."""
        nodes = []
        edges = []
        
        # Add qubit nodes
        for q in range(circuit.num_qubits):
            nodes.append({
                'id': f'q{q}',
                'label': f'Qubit {q}',
                'type': 'qubit'
            })
        
        # Add gate nodes
        for i, (gate, qubits) in enumerate(circuit.gates):
            gate_id = f'g{i}'
            nodes.append({
                'id': gate_id,
                'label': gate.name,
                'type': 'gate'
            })
            
            # Connect to qubits
            for q in qubits:
                edges.append({
                    'source': gate_id,
                    'target': f'q{q}'
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'depth': circuit.depth(),
            'gate_count': len(circuit.gates)
        }
        
    def get_diagnostics(self, code: str) -> List[Dict]:
        """Get diagnostics for code (errors, warnings)."""
        diagnostics = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Check for common issues
            if 'import abirqu' in line and 'from abirqu' not in line:
                diagnostics.append({
                    'line': i + 1,
                    'severity': 'info',
                    'message': 'Consider using "from abirqu import" for specific modules'
                })
            
            # Check for unused qubits
            if 'Circuit(' in line:
                # Simplified check
                pass
        
        return diagnostics
