"""Export Module for AbirQu. Copyright 2026 Abir Maheshwari"""
import json
from typing import List, Dict, Any, Optional
from ..circuit import Circuit
from ..qec.codes import SurfaceCode, LDPCCode

class Exporter:
    """Exports quantum circuits and results to various formats."""
    
    def __init__(self):
        self.supported_formats = ['qasm', 'json', 'csv', 'html', 'latex']
        
    def export_circuit(self, circuit: Circuit, filepath: str, format: str = 'qasm'):
        """Export circuit to specified format."""
        if format == 'qasm':
            self._export_qasm(circuit, filepath)
        elif format == 'json':
            self._export_json(circuit, filepath)
        elif format == 'html':
            self._export_html(circuit, filepath)
        elif format == 'latex':
            self._export_latex(circuit, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _export_qasm(self, circuit: Circuit, filepath: str):
        """Export to OpenQASM 2.0."""
        qasm = circuit.to_qasm()
        with open(filepath, 'w') as f:
            f.write(qasm)
            
    def _export_json(self, circuit: Circuit, filepath: str):
        """Export circuit structure to JSON."""
        data = {
            'name': circuit.name,
            'num_qubits': circuit.num_qubits,
            'gates': []
        }
        
        for gate in circuit.gates:
            data['gates'].append({
                'name': gate.name,
                'qubits': gate.qubits
            })
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _export_html(self, circuit: Circuit, filepath: str):
        """Export circuit to HTML visualization."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quantum Circuit: {circuit.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>Quantum Circuit: {circuit.name}</h1>
    <h2>Properties</h2>
    <p><b>Number of Qubits:</b> {circuit.num_qubits}</p>
    <p><b>Number of Gates:</b> {len(circuit.gates)}</p>
    <p><b>Depth:</b> {circuit.depth()}</p>
    
    <h2>Gate Sequence</h2>
    <table>
        <tr><th>#</th><th>Gate</th><th>Qubits</th></tr>
"""
        for i, gate in enumerate(circuit.gates):
            html += f"        <tr><td>{i+1}</td><td>{gate.name}</td><td>{gate.qubits}</td></tr>\n"
            
        html += """    </table>
</body>
</html>"""
        
        with open(filepath, 'w') as f:
            f.write(html)
            
    def _export_latex(self, circuit: Circuit, filepath: str):
        """Export circuit to LaTeX."""
        latex = f"""
\\documentclass{{article}}
\\usepackage{{qcircuit}}
\\begin{{document}}

\\section{{Quantum Circuit: {circuit.name}}}

\\begin{{equation}}
\\Qcircuit @C=1em @R=.7em {{
"""
        for gate in circuit.gates:
            qubits = gate.qubits
            if len(qubits) == 1:
                latex += f"    & \\gate{{{gate.name}}} & \\qw{{{qubits[0]}}} \\\\\n"
            elif len(qubits) == 2:
                latex += f"    & \\gate{{{gate.name}}} & \\qw{{{qubits[0]}}} \\\\\n"
                
        latex += """}
\\end{equation}

\\end{document}"""
        
        with open(filepath, 'w') as f:
            f.write(latex)
            
    def export_results(self, counts: Dict[str, int], filepath: str, format: str = 'csv'):
        """Export measurement results."""
        if format == 'csv':
            self._export_csv(counts, filepath)
        elif format == 'json':
            self._export_results_json(counts, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _export_csv(self, counts: Dict[str, int], filepath: str):
        """Export results to CSV."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['State', 'Count', 'Probability'])
            
            total = sum(counts.values())
            for state, count in sorted(counts.items()):
                prob = count / total if total > 0 else 0
                writer.writerow([state, count, prob])
                
    def _export_results_json(self, counts: Dict[str, int], filepath: str):
        """Export results to JSON."""
        total = sum(counts.values())
        data = {
            'total_shots': total,
            'states': []
        }
        
        for state, count in sorted(counts.items()):
            prob = count / total if total > 0 else 0
            data['states'].append({
                'state': state,
                'count': count,
                'probability': prob
            })
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def export_code_comparison(self, codes: List[Any], filepath: str):
        """Export comparison of QEC codes."""
        data = {
            'codes': []
        }
        
        for code in codes:
            if isinstance(code, SurfaceCode):
                data['codes'].append({
                    'type': 'SurfaceCode',
                    'distance': code.distance,
                    'physical_qubits': code.get_overhead()
                })
            elif isinstance(code, LDPCCode):
                data['codes'].append({
                    'type': 'LDPCCode',
                    'n': code.n,
                    'k': code.k,
                    'rate': code.get_rate()
                })
                
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
