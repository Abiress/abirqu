"""
VS Code Extension Support

Provides syntax highlighting, circuit visualization preview,
inline circuit optimization suggestions, and quantum debugger integration.
"""

import json
from typing import Dict, List, Any, Optional

class VSCodeExtension:
    """Generates VS Code extension configuration and support files."""
    
    def __init__(self):
        self.extension_id = "abirqu.abirqu"
        self.display_name = "AbirQu Quantum Development"
        
    def generate_extension_manifest(self) -> Dict[str, Any]:
        """Generate package.json for VS Code extension."""
        return {
            "name": "abirqu",
            "displayName": self.display_name,
            "description": "Next-generation quantum computing development with AbirQu",
            "version": "1.0.0",
            "engines": {
                "vscode": "^1.80.0"
            },
            "categories": ["Programming Languages", "Snippets", "Visualization"],
            "keywords": ["quantum", "abirqu", "quantum computing", "qiskit", "cirq"],
            "activationEvents": [
                "onLanguage:abirqu",
                "onCommand:abirqu.visualizeCircuit",
                "onCommand:abirqu.optimizeCircuit"
            ],
            "contributes": {
                "languages": [{
                    "id": "abirqu",
                    "extensions": [".abirqu", ".aq"],
                    "aliases": ["AbirQu", "abirqu"],
                    "configuration": "./language-configuration.json"
                }],
                "grammars": [{
                    "language": "abirqu",
                    "scopeName": "source.abirqu",
                    "path": "./syntaxes/abirqu.tmLanguage.json"
                }],
                "commands": [
                    {
                        "command": "abirqu.visualizeCircuit",
                        "title": "Visualize Quantum Circuit",
                        "category": "AbirQu"
                    },
                    {
                        "command": "abirqu.optimizeCircuit",
                        "title": "Optimize Circuit",
                        "category": "AbirQu"
                    },
                    {
                        "command": "abirqu.runSimulation",
                        "title": "Run Simulation",
                        "category": "AbirQu"
                    }
                ],
                "viewsContainers": {
                    "activitybar": [{
                        "id": "abirqu",
                        "title": "AbirQu",
                        "icon": "$(symbol-field)"
                    }]
                },
                "views": {
                    "abirqu": [
                        {
                            "id": "abirquCircuits",
                            "name": "Circuit Explorer"
                        },
                        {
                            "id": "abirquBackends",
                            "name": "Quantum Backends"
                        }
                    ]
                },
                "keybindings": [
                    {
                        "command": "abirqu.visualizeCircuit",
                        "key": "ctrl+shift+v",
                        "mac": "cmd+shift+v",
                        "when": "editorTextFocus && resourceLangId == abirqu"
                    }
                ],
                "configuration": {
                    "title": "AbirQu",
                    "properties": {
                        "abirqu.defaultBackend": {
                            "type": "string",
                            "default": "simulator",
                            "description": "Default quantum backend"
                        },
                        "abirqu.simulatorQubits": {
                            "type": "integer",
                            "default": 10,
                            "description": "Max qubits for local simulator"
                        },
                        "abirqu.optimizationLevel": {
                            "type": "integer",
                            "default": 2,
                            "description": "Default optimization level (0-3)"
                        }
                    }
                }
            }
        }

class CircuitPreviewPanel:
    """Generates HTML/JS for circuit visualization preview panel."""
    
    def generate_preview_html(self, circuit_data: Dict) -> str:
        """Generate HTML for circuit preview."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>AbirQu Circuit Preview</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 20px; font-family: Arial, sans-serif; }}
        .qubit-line {{ stroke: #333; stroke-width: 2; }}
        .gate {{ fill: #4CAF50; stroke: #333; cursor: pointer; }}
        .gate-text {{ fill: white; font-size: 12px; text-anchor: middle; }}
        .measurement {{ fill: #2196F3; stroke: #333; }}
    </style>
</head>
<body>
    <h2>AbirQu Circuit: {circuit_data.get('name', 'Untitled')}</h2>
    <p>Qubits: {circuit_data.get('num_qubits', 0)} | Gates: {len(circuit_data.get('gates', []))}</p>
    <svg id="circuit-svg" width="800" height="400"></svg>
    <script>
        const circuitData = {json.dumps(circuit_data)};
        // Render circuit visualization
        renderCircuit(circuitData);
    </script>
</body>
</html>
"""

class SyntaxHighlighter:
    """Provides syntax highlighting rules for AbirQu DSL."""
    
    @staticmethod
    def get_textmate_grammar() -> Dict:
        """Generate TextMate grammar for AbirQu."""
        return {
            "scopeName": "source.abirqu",
            "patterns": [
                {
                    "name": "keyword.control.abirqu",
                    "match": "\\b(circuit|h|x|y|z|s|t|rx|ry|rz|cnot|cz|swap|toffoli)\\b"
                },
                {
                    "name": "constant.numeric.abirqu",
                    "match": "\\b\\d+(\\.\\d+)?\\b"
                },
                {
                    "name": "string.quoted.double.abirqu",
                    "begin": "\"",
                    "end": "\"",
                    "patterns": [{"name": "constant.character.escape.abirqu", "match": "\\\\."}]
                },
                {
                    "name": "comment.line.abirqu",
                    "match": "#.*$"
                }
            ]
        }

class OptimizationSuggestionProvider:
    """Provides inline optimization suggestions."""
    
    def get_suggestions(self, circuit_code: str) -> List[Dict[str, Any]]:
        """Analyze circuit code and provide optimization suggestions."""
        suggestions = []
        
        lines = circuit_code.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Detect redundant gates
            if 'h' in line_lower and i + 1 < len(lines):
                if 'h' in lines[i + 1].lower():
                    suggestions.append({
                        'line': i + 1,
                        'type': 'redundant_gate',
                        'message': 'Adjacent H gates cancel out (H² = I)',
                        'fix': 'Remove both H gates'
                    })
                    
            # Detect missing initialization
            if 'cnot' in line_lower or 'cz' in line_lower:
                if not any('h(' in l.lower() for l in lines[:i]):
                    suggestions.append({
                        'line': i + 1,
                        'type': 'missing_superposition',
                        'message': 'Consider adding H gate for superposition',
                        'fix': 'Add H gate before entanglement'
                    })
                    
        return suggestions

class QuantumDebugger:
    """Integration with VS Code debugger for quantum circuits."""
    
    def generate_debug_config(self) -> Dict:
        """Generate launch.json configuration for debugging."""
        return {
            "version": "0.2.0",
            "configurations": [
                {
                    "type": "python",
                    "request": "launch",
                    "name": "Debug AbirQu Circuit",
                    "program": "${file}",
                    "justMyCode": False,
                    "env": {
                        "ABIRQU_DEBUG": "1",
                        "ABIRQU_LOG_LEVEL": "DEBUG"
                    }
                },
                {
                    "type": "python",
                    "request": "launch",
                    "name": "Simulate Circuit",
                    "program": "python",
                    "args": ["-m", "abirqu", "circuit", "run", "--file", "${file}"]
                }
            ]
        }

# Example usage
if __name__ == "__main__":
    print("Testing VS Code Extension Support...")
    
    # Test extension manifest
    ext = VSCodeExtension()
    manifest = ext.generate_extension_manifest()
    print(f"Extension: {manifest['displayName']}")
    print(f"Version: {manifest['version']}")
    print(f"Commands: {len(manifest['contributes']['commands'])}")
    
    # Test circuit preview
    preview = CircuitPreviewPanel()
    sample_circuit = {
        'name': 'Bell State',
        'num_qubits': 2,
        'gates': [
            {'name': 'H', 'qubits': [0]},
            {'name': 'CNOT', 'qubits': [0, 1]}
        ]
    }
    html = preview.generate_preview_html(sample_circuit)
    print(f"\nPreview HTML length: {len(html)} chars")
    
    # Test syntax highlighting
    syntax = SyntaxHighlighter()
    grammar = syntax.get_textmate_grammar()
    print(f"\nTextMate grammar patterns: {len(grammar['patterns'])}")
    
    # Test optimization suggestions
    provider = OptimizationSuggestionProvider()
    sample_code = """
circuit = Circuit(2)
circuit.h(0)
circuit.h(0)  # Redundant!
circuit.cnot(0, 1)
"""
    suggestions = provider.get_suggestions(sample_code)
    print(f"\nOptimization suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"  Line {s['line']}: {s['message']}")
    
    print("\nVS Code Extension support ready!")
