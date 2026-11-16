"""
Quantikz LaTeX Circuit Drawer
=============================
Generates standard publication-ready LaTeX quantikz code from an AbirQu Circuit.
"""
from typing import List
from abirqu.circuit import Circuit


def to_quantikz(circuit: Circuit) -> str:
    """Generate LaTeX quantikz code for the given Circuit."""
    n = circuit.num_qubits
    if n == 0:
        return "\\begin{quantikz}\n\\end{quantikz}"

    # Build grid of operations per wire
    # We step gate by gate
    wire_ops: List[List[str]] = [[] for _ in range(n)]

    for gate in circuit.gates:
        name = gate.name.upper()
        qubits = gate.qubits
        params = getattr(gate, "params", []) or []

        if name in ("CNOT", "CX") and len(qubits) == 2:
            ctrl, tgt = qubits[0], qubits[1]
            offset = tgt - ctrl
            for q in range(n):
                if q == ctrl:
                    wire_ops[q].append(f"\\ctrl{{{offset}}}")
                elif q == tgt:
                    wire_ops[q].append("\\targ{}")
                else:
                    wire_ops[q].append("\\qw")
        elif name == "CZ" and len(qubits) == 2:
            ctrl, tgt = qubits[0], qubits[1]
            offset = tgt - ctrl
            for q in range(n):
                if q == ctrl:
                    wire_ops[q].append(f"\\ctrl{{{offset}}}")
                elif q == tgt:
                    wire_ops[q].append("\\gate{Z}")
                else:
                    wire_ops[q].append("\\qw")
        elif name == "SWAP" and len(qubits) == 2:
            q1, q2 = qubits[0], qubits[1]
            offset = q2 - q1
            for q in range(n):
                if q == q1:
                    wire_ops[q].append(f"\\swap{{{offset}}}")
                elif q == q2:
                    wire_ops[q].append("\\targX{}")
                else:
                    wire_ops[q].append("\\qw")
        elif len(qubits) == 1:
            q = qubits[0]
            label = name
            if params:
                param_str = ", ".join(f"{p:.3f}" if isinstance(p, float) else str(p) for p in params)
                label = f"{name}({param_str})"
            for wire in range(n):
                if wire == q:
                    wire_ops[wire].append(f"\\gate{{{label}}}")
                else:
                    wire_ops[wire].append("\\qw")
        else:
            for wire in range(n):
                if wire in qubits:
                    wire_ops[wire].append(f"\\gate{{{name}}}")
                else:
                    wire_ops[wire].append("\\qw")

    # Add measurements if any
    if hasattr(circuit, "measurements") and circuit.measurements:
        for wire in range(n):
            if any(m.qubit == wire for m in circuit.measurements):
                wire_ops[wire].append("\\meter{}")
            else:
                wire_ops[wire].append("\\qw")

    # Format LaTeX lines
    lines = ["\\begin{quantikz}"]
    for q in range(n):
        ops = wire_ops[q]
        row_str = f"\\lstick{{\\ket{{0}}}}"
        if ops:
            row_str += " & " + " & ".join(ops)
        else:
            row_str += " & \\qw"
        if q < n - 1:
            row_str += " \\\\"
        lines.append(row_str)
    lines.append("\\end{quantikz}")

    return "\n".join(lines)

