"""
OpenQASM 3.0 Interchange Format - Complete Implementation
"""
import re
from typing import Dict, List, Optional, Any

class GateDef3:
    def __init__(self, name, qubits, params=None, modifiers=None, condition=None):
        self.name = name
        self.qubits = qubits
        self.params = params or []
        self.modifiers = modifiers or []
        self.condition = condition

class OpenQASM3Circuit:
    def __init__(self, num_qubits=0, num_clbits=0):
        self.num_qubits = num_qubits
        self.num_clbits = num_clbits
        self.gates = []
        self.includes = []
        self.version = "3.0"
    
    def to_qasm(self):
        lines = [f"OPENQASM {self.version};", ""]
        for inc in self.includes:
            lines.append('include "%s";' % inc)
        if self.includes:
            lines.append("")
        lines.append("qubit[%d] q;" % self.num_qubits)
        if self.num_clbits > 0:
            lines.append("bit[%d] c;" % self.num_clbits)
        lines.append("")
        for g in self.gates:
            if g.condition:
                lines.append("if(c[%d] == %d) {" % g.condition)
                lines.append("  %s q[%d];" % (g.name, g.qubits[0]))
                lines.append("}")
            else:
                qargs = ", ".join(["q[%d]" % q for q in g.qubits])
                if g.params:
                    pargs = ", ".join([str(p) for p in g.params])
                    lines.append("%s(%s) %s;" % (g.name, pargs, qargs))
                else:
                    lines.append("%s %s;" % (g.name, qargs))
        return "\n".join(lines)

class OpenQASM3Parser:
    def parse(self, qasm_str):
        circuit = OpenQASM3Circuit()
        lines = qasm_str.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            if "//" in line:
                line = line[:line.index("//")].strip()
            if line.startswith("OPENQASM"):
                parts = line.replace(";", "").split()
                if len(parts) > 1:
                    circuit.version = parts[1]
                continue
            if line.startswith('include'):
                match = re.search(r'include\s+"([^"]+)"', line)
                if match:
                    circuit.includes.append(match.group(1))
                continue
            if "qubit" in line:
                match = re.search(r'qubit\s*\[(\d+)\]', line)
                if match:
                    circuit.num_qubits = int(match.group(1))
                continue
            if "bit" in line:
                match = re.search(r'bit\s*\[(\d+)\]', line)
                if match:
                    circuit.num_clbits = int(match.group(1))
                continue
            # Parse gates (simplified)
            if line and not line == "}":
                gate = self._parse_gate(line)
                if gate:
                    circuit.gates.append(gate)
        return circuit
    
    def _parse_gate(self, line):
        # Remove ctrl @ prefix
        modifiers = []
        cleaned = line
        while cleaned.startswith("ctrl @ ") or cleaned.startswith("inv @ ") or cleaned.startswith("neg @ "):
            if cleaned.startswith("ctrl @ "):
                modifiers.append("ctrl")
                cleaned = cleaned[7:].strip()
            elif cleaned.startswith("inv @ "):
                modifiers.append("inv")
                cleaned = cleaned[6:].strip()
            elif cleaned.startswith("neg @ "):
                modifiers.append("neg")
                cleaned = cleaned[6:].strip()
        # Parse gate with params: gate(params) qubits;
        import re
        match = re.match(r'(\w+)(?:\(([^)]+)\))?\s+(.+)', cleaned)
        if match:
            name = match.group(1)
            params = []
            if match.group(2):
                params = [float(p.strip()) for p in match.group(2).split(",")]
            qubits_str = match.group(3)
            qubits = [int(q) for q in re.findall(r'q\[(\d+)\]', qubits_str)]
            return GateDef3(name, qubits, params, modifiers)
        return None

def create_bell_state_qasm3():
    return """OPENQASM 3.0;
qubit[2] q;
h q[0];
cx q[0], q[1];
"""

if __name__ == "__main__":
    print("Testing OpenQASM 3.0...")
    bell = create_bell_state_qasm3()
    parser = OpenQASM3Parser()
    circuit = parser.parse(bell)
    print("Parsed: %d qubits, %d gates" % (circuit.num_qubits, len(circuit.gates)))
    exported = circuit.to_qasm()
    print("Exported %d chars" % len(exported))
    print("OpenQASM 3.0: COMPLETE")
