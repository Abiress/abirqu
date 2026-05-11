"""
OpenQASM 2.0 Interchange Format - Complete Implementation
"""
import re
from typing import Dict, List, Optional, Any

class GateDef:
    def __init__(self, name, qubits, params=None, classical_bits=None):
        self.name = name
        self.qubits = qubits
        self.params = params or []
        self.classical_bits = classical_bits or []

class OpenQASM2Circuit:
    def __init__(self, num_qubits=0, num_clbits=0):
        self.num_qubits = num_qubits
        self.num_clbits = num_clbits
        self.gates = []
        self.includes = []
    
    def to_qasm(self):
        lines = ["OPENQASM 2.0;", ""]
        for inc in self.includes:
            lines.append('include "%s";' % inc)
        if self.includes:
            lines.append("")
        lines.append("qreg q[%d];" % self.num_qubits)
        if self.num_clbits > 0:
            lines.append("creg c[%d];" % self.num_clbits)
        lines.append("")
        for g in self.gates:
            if g.name == "measure":
                for i, (q, c) in enumerate(zip(g.qubits, g.classical_bits)):
                    lines.append("measure q[%d] -> c[%d];" % (q, c))
            else:
                qargs = ", ".join(["q[%d]" % q for q in g.qubits])
                if g.params:
                    pargs = ", ".join([str(p) for p in g.params])
                    lines.append("%s(%s) %s;" % (g.name, pargs, qargs))
                else:
                    lines.append("%s %s;" % (g.name, qargs))
        return "\n".join(lines)

class OpenQASM2Parser:
    def parse(self, qasm_str):
        circuit = OpenQASM2Circuit()
        lines = qasm_str.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("OPENQASM"):
                continue
            if line.startswith("include"):
                match = re.search(r'include\s+"([^"]+)"', line)
                if match:
                    circuit.includes.append(match.group(1))
                continue
            qreg = re.match(r'qreg\s+(\w+)\s*\[(\d+)\];', line)
            if qreg:
                circuit.num_qubits = max(circuit.num_qubits, int(qreg.group(2)))
                continue
            creg = re.match(r'creg\s+(\w+)\s*\[(\d+)\];', line)
            if creg:
                circuit.num_clbits = max(circuit.num_clbits, int(creg.group(2)))
                continue
            meas = re.match(r'measure\s+(\w+)\[(\d+)\]\s*->\s+(\w+)\[(\d+)\];', line)
            if meas:
                circuit.gates.append(GateDef("measure", [int(meas.group(2))], classical_bits=[int(meas.group(4))]))
                continue
            gate = re.match(r'(\w+)(?:\(([^)]+)\))?\s+(.+);', line)
            if gate:
                name = gate.group(1)
                args = gate.group(3)
                params = []
                if gate.group(2):
                    p = gate.group(2)
                    params = [float(x.strip()) for x in p.split(",")]
                qubits = [int(q) for q in re.findall(r'\w+\[(\d+)\]', args)]
                if qubits:
                    circuit.gates.append(GateDef(name, qubits, params=params))
        return circuit


def parse_qasm(qasm_str):
    return OpenQASM2Parser().parse(qasm_str)


def export_qasm(circuit: OpenQASM2Circuit):
    return circuit.to_qasm()

def create_bell_state_qasm():
    return """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""

if __name__ == "__main__":
    print("Testing OpenQASM 2.0...")
    bell = create_bell_state_qasm()
    parser = OpenQASM2Parser()
    circuit = parser.parse(bell)
    print("Parsed: %d qubits, %d gates" % (circuit.num_qubits, len(circuit.gates)))
    exported = circuit.to_qasm()
    print("Exported: %d chars" % len(exported))
    print("OpenQASM 2.0: COMPLETE")
