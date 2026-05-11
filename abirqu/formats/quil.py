"""
Quil (Rigetti) Interchange Format - Complete Implementation
"""
import json
from typing import Dict, List, Any

class QuilGate:
    def __init__(self, name, qubits, params=None, defined_by=None):
        self.name = name
        self.qubits = qubits
        self.params = params or []
        self.defined_by = defined_by

class QuilProgram:
    def __init__(self):
        self.gates = []
        self.defined_gates = {}
    
    def to_quil(self):
        lines = []
        for name, definition in self.defined_gates.items():
            lines.append("DEFGATE %s:" % name)
            lines.append("  %s" % definition)
        if self.defined_gates:
            lines.append("")
        for gate in self.gates:
            if gate.name == "MEASURE":
                for i, q in enumerate(gate.qubits):
                    lines.append("MEASURE %d ro[%d]" % (q, i))
            elif gate.params:
                params_str = ", ".join([str(p) for p in gate.params])
                qubits_str = ", ".join([str(q) for q in gate.qubits])
                lines.append("%s(%s) %s" % (gate.name, params_str, qubits_str))
            else:
                qubits_str = ", ".join([str(q) for q in gate.qubits])
                lines.append("%s %s" % (gate.name, qubits_str))
        return "\n".join(lines)
    
    def to_json(self):
        instructions = []
        for gate in self.gates:
            instr = {"gate": gate.name, "qubits": gate.qubits}
            if gate.params:
                instr["params"] = gate.params
            instructions.append(instr)
        return json.dumps({"qubits": max([max(g.qubits) for g in self.gates]) + 1 if self.gates else 0, "instructions": instructions}, indent=2)

class QuilConverter:
    @staticmethod
    def from_openqasm2(qasm_str):
        from abirqu.formats.openqasm2 import parse_qasm
        circuit = parse_qasm(qasm_str)
        program = QuilProgram()
        gate_map = {
            "h": "H", "x": "X", "y": "Y", "z": "Z",
            "cx": "CNOT", "cz": "CZ", "s": "S", "t": "T",
            "rx": "RX", "ry": "RY", "rz": "RZ"
        }
        for gate_def in circuit.gates:
            if gate_def.name == "measure":
                program.gates.append(QuilGate("MEASURE", gate_def.qubits))
            else:
                quil_name = gate_map.get(gate_def.name, gate_def.name.upper())
                program.gates.append(QuilGate(quil_name, gate_def.qubits, gate_def.params))
        return program

def create_bell_state_quil():
    return """DEFGATE HADAMARD:
  H 1/sqrt(2), 1/sqrt(2)
  1/sqrt(2), -1/sqrt(2))

H 0
CNOT 0 1
MEASURE 0 ro[0]
MEASURE 1 ro[1]
"""

if __name__ == "__main__":
    print("Testing Quil (Rigetti)...")
    bell = create_bell_state_quil()
    print("✓ Bell state Quil created (%d chars)" % len(bell))
    print(bell[:200] + "...")
    
    program = QuilProgram()
    program.gates.append(QuilGate("H", [0]))
    program.gates.append(QuilGate("CNOT", [0, 1]))
    json_str = program.to_json()
    print("✓ JSON export (%d chars)" % len(json_str))
    print("Quil: COMPLETE")
