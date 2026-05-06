"""Visualization Module for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from ..core.circuit import Circuit
from ..core.gates import Gate

class CircuitVisualizer:
    """Visualizes quantum circuits in various formats."""
    
    def __init__(self):
        self.style = 'text'  # text, ascii, unicode, mpl
        
    def visualize(self, circuit: Circuit, format: str = 'text') -> str:
        """Visualize circuit in specified format."""
        if format == 'text':
            return self._text_diagram(circuit)
        elif format == 'ascii':
            return self._ascii_art(circuit)
        elif format == 'unicode':
            return self._unicode_diagram(circuit)
        elif format == 'qasm':
            return circuit.to_qasm()
        else:
            raise ValueError(f"Unknown format: {format}")
            
    def _text_diagram(self, circuit: Circuit) -> str:
        """Generate text-based circuit diagram."""
        lines = []
        lines.append("Circuit: " + circuit.name)
        lines.append("=" * 40)
        
        # Header
        header = "Gate".ljust(10) + "Qubits".ljust(15) + "Details"
        lines.append(header)
        lines.append("-" * 40)
        
        # Gate list
        for i, (gate, qubits) in enumerate(circuit.gates):
            qubits_str = ', '.join(str(q) for q in qubits)
            lines.append(f"{gate.name.ljust(10)} {qubits_str.ljust(15)} (gate {i+1})")
            
        lines.append("=" * 40)
        lines.append(f"Total gates: {len(circuit.gates)}")
        lines.append(f"Depth: {circuit.depth()}")
        
        return '\n'.join(lines)
        
    def _ascii_art(self, circuit: Circuit) -> str:
        """Generate ASCII art circuit diagram."""
        n = circuit.num_qubits
        max_gates = len(circuit.gates)
        
        # Initialize grid
        grid = [['─' for _ in range(max_gates * 2)] for _ in range(n)]
        
        # Place gates
        for i, (gate, qubits) in enumerate(circuit.gates):
            col = i * 2
            name = gate.name.split('(')[0][:3]  # First 3 chars
            
            for q in range(n):
                if q in qubits:
                    grid[q][col] = name[0] if len(name) > 0 else '●'
                    if len(name) > 1:
                        grid[q][col+1] = name[1]
                else:
                    grid[q][col] = '─'
                    grid[q][col+1] = '─'
                    
        # Build diagram
        lines = []
        lines.append("    " + ' '.join(f"{i%10}" for i in range(max_gates)))
        lines.append("    " + '─' * (max_gates * 2))
        
        for q in range(n):
            line = f"q{q}: │" + '│'.join(grid[q]) + '│'
            lines.append(line)
            
        return '\n'.join(lines)
        
    def _unicode_diagram(self, circuit: Circuit) -> str:
        """Generate Unicode circuit diagram."""
        n = circuit.num_qubits
        lines = []
        lines.append("╔" + "═" * 40 + "╗")
        lines.append(f"║ Circuit: {circuit.name}")
        lines.append("╠" + "═" * 40 + "╣")
        
        for i, (gate, qubits) in enumerate(circuit.gates):
            gate_str = f"[{gate.name}]"
            qubit_str = f" → qubits {qubits}"
            lines.append(f"║ {i+1:2d}. {gate_str:<20}{qubit_str}")
            
        lines.append("╚" + "═" * 40 + "╝")
        return '\n'.join(lines)
        
    def export_html(self, circuit: Circuit, filepath: str):
        """Export circuit visualization to HTML."""
        html = f"""
<!DOCTYPE html>
<html>
<head><title>Circuit: {circuit.name}</title></head>
<body>
<h1>Quantum Circuit: {circuit.name}</h1>
<p><b>Qubits:</b> {circuit.num_qubits}</p>
<p><b>Gates:</b> {len(circuit.gates)}</p>
<p><b>Depth:</b> {circuit.depth()}</p>
<h2>Gate Sequence</h2>
<ol>
"""
        for i, (gate, qubits) in enumerate(circuit.gates):
            html += f"<li>{gate.name} on qubits {qubits}</li>\n"
            
        html += "</ol></body></html>"
        
        with open(filepath, 'w') as f:
            f.write(html)
            
    def get_gate_colors(self, gate_name: str) -> Tuple[str, str]:
        """Get color scheme for gate (foreground, background)."""
        colors = {
            'H': ('white', 'blue'),
            'X': ('black', 'yellow'),
            'Y': ('white', 'green'),
            'Z': ('white', 'red'),
            'CNOT': ('white', 'purple'),
            'RZ': ('black', 'cyan'),
            'RX': ('black', 'magenta'),
            'RY': ('black', 'orange'),
        }
        return colors.get(gate_name.split('(')[0], ('black', 'gray'))
