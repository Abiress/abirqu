"""Hardware-aware transpiler that works with AbirQu's Circuit API."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from abirqu.circuit import Circuit


@dataclass
class TranspileStats:
    original_gates: int
    transpiled_gates: int
    inserted_swaps: int
    decomposed_gates: int


class HardwareAwareTranspiler:
    """Transpile to backend-friendly gates and satisfy coupling constraints."""

    GATE_SETS: Dict[str, Dict[str, Sequence[str]]] = {
        "IBM": {
            "basis": ["X", "H", "RZ", "CNOT"],
            "two_qubit": ["CNOT"],
        },
        "Google": {
            "basis": ["X", "Y", "Z", "RZ", "H", "CZ"],
            "two_qubit": ["CZ"],
        },
        "IonQ": {
            "basis": ["X", "Y", "Z", "RX", "RY", "RZ", "CNOT"],
            "two_qubit": ["CNOT"],
        },
        "generic": {
            "basis": ["X", "Y", "Z", "H", "S", "T", "RX", "RY", "RZ", "CNOT", "CZ", "SWAP"],
            "two_qubit": ["CNOT", "CZ"],
        },
    }

    def __init__(self, backend: str = "generic") -> None:
        self.backend = backend
        self.gate_set = self.GATE_SETS.get(backend, self.GATE_SETS["generic"])
        self.coupling_map: Optional[List[Tuple[int, int]]] = None

    def set_backend(self, backend: str) -> None:
        self.backend = backend
        self.gate_set = self.GATE_SETS.get(backend, self.GATE_SETS["generic"])

    def set_coupling_map(self, coupling: List[Tuple[int, int]]) -> None:
        self.coupling_map = coupling

    def get_native_gates(self) -> List[str]:
        return list(self.gate_set["basis"])

    def transpile(self, circuit: Circuit) -> "TranspiledCircuit":
        staged = Circuit(circuit.num_qubits, f"{circuit.name}_staged")
        decomposed = 0

        for gate in circuit.gates:
            expanded = self._decompose_to_basis(gate.name, gate.qubits, gate.params)
            if len(expanded) > 1 or expanded[0][0] != gate.name:
                decomposed += 1
            for g_name, qbs, params in expanded:
                staged.add_gate(g_name, qbs, params if params else None)

        routed, swaps = self._apply_routing(staged)
        stats = TranspileStats(
            original_gates=len(circuit.gates),
            transpiled_gates=len(routed.gates),
            inserted_swaps=swaps,
            decomposed_gates=decomposed,
        )
        return TranspiledCircuit(circuit, routed, self.backend, stats)

    def _decompose_to_basis(self, name: str, qubits: List[int], params: List[float]) -> List[Tuple[str, List[int], List[float]]]:
        upper = name.upper()
        if upper in self.gate_set["basis"]:
            return [(upper, list(qubits), list(params or []))]

        if upper == "S":
            return [("RZ", [qubits[0]], [float(np.pi / 2)])]
        if upper == "T":
            return [("RZ", [qubits[0]], [float(np.pi / 4)])]

        # Keep RX/RY/RZ native where possible, else fallback to H-RZ-H.
        if upper in {"RX", "RY"} and "RZ" in self.gate_set["basis"] and "H" in self.gate_set["basis"]:
            theta = float(params[0]) if params else 0.0
            return [("H", [qubits[0]], []), ("RZ", [qubits[0]], [theta]), ("H", [qubits[0]], [])]

        if upper == "SWAP" and "CNOT" in self.gate_set["basis"]:
            q0, q1 = qubits
            return [
                ("CNOT", [q0, q1], []),
                ("CNOT", [q1, q0], []),
                ("CNOT", [q0, q1], []),
            ]

        return [(upper, list(qubits), list(params or []))]

    def _build_adjacency(self) -> Dict[int, List[int]]:
        if not self.coupling_map:
            return {}
        adj: Dict[int, List[int]] = {}
        for a, b in self.coupling_map:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        return adj

    def _shortest_path(self, src: int, dst: int, adj: Dict[int, List[int]]) -> Optional[List[int]]:
        if src == dst:
            return [src]
        q: deque[Tuple[int, List[int]]] = deque([(src, [src])])
        seen = {src}
        while q:
            node, path = q.popleft()
            for nxt in adj.get(node, []):
                if nxt in seen:
                    continue
                npath = path + [nxt]
                if nxt == dst:
                    return npath
                seen.add(nxt)
                q.append((nxt, npath))
        return None

    def _apply_routing(self, circuit: Circuit) -> Tuple[Circuit, int]:
        if not self.coupling_map:
            return circuit, 0

        adj = self._build_adjacency()
        connected = {(a, b) for a, b in self.coupling_map} | {(b, a) for a, b in self.coupling_map}
        routed = Circuit(circuit.num_qubits, f"{circuit.name}_routed")
        swaps = 0

        for gate in circuit.gates:
            if len(gate.qubits) != 2:
                routed.add_gate(gate.name, gate.qubits, gate.params if gate.params else None)
                continue

            q0, q1 = gate.qubits
            if (q0, q1) in connected:
                routed.add_gate(gate.name, [q0, q1], gate.params if gate.params else None)
                continue

            path = self._shortest_path(q0, q1, adj)
            if not path or len(path) < 2:
                raise ValueError(f"Cannot route gate {gate.name} on disconnected qubits {q0},{q1}")

            # Bring q0 next to q1, apply gate, then restore mapping.
            forward_swaps = list(zip(path[:-2], path[1:-1]))
            for a, b in forward_swaps:
                routed.swap(a, b)
                swaps += 1

            control = path[-2]
            target = path[-1]
            routed.add_gate(gate.name, [control, target], gate.params if gate.params else None)

            for a, b in reversed(forward_swaps):
                routed.swap(a, b)
                swaps += 1

        return routed, swaps


class TranspiledCircuit:
    def __init__(self, original: Circuit, transpiled: Circuit, backend: str, stats: TranspileStats):
        self.original = original
        self.transpiled = transpiled
        self.backend = backend
        self.stats = stats

    def run(self, shots: int = 1024):
        return self.transpiled.run(shots=shots)

    def __repr__(self):
        return (
            f"TranspiledCircuit(backend={self.backend}, original={self.stats.original_gates}, "
            f"transpiled={self.stats.transpiled_gates}, swaps={self.stats.inserted_swaps})"
        )
