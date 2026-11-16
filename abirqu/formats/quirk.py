"""
Quirk Quantum Circuit URL and JSON Importer/Exporter
=====================================================
Supports importing from and exporting to Quirk simulator JSON format
and Quirk URLs (e.g. https://algassert.com/quirk#circuit={"cols":[["H"],["•","X"]]}).
"""

import json
import urllib.parse
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from abirqu.circuit import Circuit


def from_quirk_json(data: Union[str, Dict[str, Any]]) -> "Circuit":
    """Parse Quirk JSON object or JSON string into an AbirQu Circuit."""
    from abirqu.circuit import Circuit
    if isinstance(data, str):
        data = json.loads(data)

    cols = data.get("cols", [])
    if not cols:
        return Circuit(1)

    # Determine maximum number of qubits across columns
    num_qubits = max((len(col) for col in cols), default=1)
    num_qubits = max(num_qubits, 1)

    circuit = Circuit(num_qubits)

    for col in cols:
        controls: List[int] = []
        targets: List[int] = []
        gate_types: Dict[int, str] = {}

        for q, cell in enumerate(col):
            if cell in (1, 0, None, "", "1"):
                continue
            if isinstance(cell, str):
                s = cell.strip()
                if s in ("•", "Control"):
                    controls.append(q)
                else:
                    targets.append(q)
                    gate_types[q] = s

        if not targets and not controls:
            continue

        # Controlled gates
        if controls:
            if len(controls) == 1 and len(targets) == 1:
                ctrl = controls[0]
                tgt = targets[0]
                gt = gate_types[tgt].upper()
                if gt == "X":
                    circuit.cx(ctrl, tgt)
                elif gt == "Z":
                    circuit.cz(ctrl, tgt)
                elif gt == "Y":
                    circuit.add_gate("CY", [ctrl, tgt])
                else:
                    circuit.add_gate(f"C{gt}", [ctrl, tgt])
            elif len(controls) == 2 and len(targets) == 1:
                ctrl1, ctrl2 = controls[0], controls[1]
                tgt = targets[0]
                gt = gate_types[tgt].upper()
                if gt == "X":
                    circuit.toffoli(ctrl1, ctrl2, tgt)
                else:
                    circuit.add_gate(f"CC{gt}", [ctrl1, ctrl2, tgt])
            else:
                for tgt in targets:
                    circuit.add_gate(gate_types[tgt].upper(), [tgt])
        else:
            # Check for multi-qubit gates like SWAP
            swap_qubits = [q for q, gt in gate_types.items() if gt.lower() == "swap"]
            if len(swap_qubits) == 2:
                circuit.swap(swap_qubits[0], swap_qubits[1])
                for q, gt in gate_types.items():
                    if q not in swap_qubits:
                        _apply_single_gate(circuit, gt, q)
            else:
                for q, gt in gate_types.items():
                    _apply_single_gate(circuit, gt, q)

    return circuit


def _apply_single_gate(circuit: Any, gate_name: str, qubit: int):
    name = gate_name.strip()
    upper = name.upper()
    if upper == "H":
        circuit.h(qubit)
    elif upper == "X":
        circuit.x(qubit)
    elif upper == "Y":
        circuit.y(qubit)
    elif upper == "Z":
        circuit.z(qubit)
    elif upper == "S":
        circuit.s(qubit)
    elif upper == "T":
        circuit.t(qubit)
    elif upper in ("MEASURE", "M"):
        circuit.measure(qubit, qubit)
    else:
        circuit.add_gate(upper, [qubit])


def from_quirk_url(url: str) -> "Circuit":
    """Parse a Quirk URL into an AbirQu Circuit."""
    parsed = urllib.parse.urlparse(url)
    fragment = parsed.fragment
    if not fragment and "#" in url:
        fragment = url.split("#", 1)[1]

    prefix = "circuit="
    if fragment.startswith(prefix):
        raw_json = urllib.parse.unquote(fragment[len(prefix):])
    else:
        raw_json = urllib.parse.unquote(fragment)

    return from_quirk_json(raw_json)


def to_quirk_json(circuit: Any) -> Dict[str, Any]:
    """Serialize an AbirQu Circuit to Quirk JSON format."""
    cols = []
    n = circuit.num_qubits

    for gate in circuit.gates:
        col = [1] * n
        name = gate.name.upper()
        qubits = gate.qubits

        if name in ("CNOT", "CX") and len(qubits) == 2:
            col[qubits[0]] = "•"
            col[qubits[1]] = "X"
        elif name == "CZ" and len(qubits) == 2:
            col[qubits[0]] = "•"
            col[qubits[1]] = "Z"
        elif name in ("TOFFOLI", "CCX") and len(qubits) == 3:
            col[qubits[0]] = "•"
            col[qubits[1]] = "•"
            col[qubits[2]] = "X"
        elif name == "SWAP" and len(qubits) == 2:
            col[qubits[0]] = "Swap"
            col[qubits[1]] = "Swap"
        elif len(qubits) == 1:
            col[qubits[0]] = name
        else:
            for q in qubits:
                col[q] = name

        cols.append(col)

    return {"cols": cols}

