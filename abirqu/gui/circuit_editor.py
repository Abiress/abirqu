"""
AbirQu Visual Circuit Editor
Copyright 2026 Abir Maheshwari

Drag-and-drop quantum circuit editor with real-time visualization.
"""
import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field


GATE_COLORS = {
    'H': '#7c3aed', 'X': '#f85149', 'Y': '#d29922', 'Z': '#3fb950',
    'CNOT': '#58a6ff', 'CX': '#58a6ff', 'CZ': '#58a6ff',
    'S': '#a855f7', 'Sdg': '#a855f7',
    'T': '#f0883e', 'Tdg': '#f0883e',
    'Rx': '#f85149', 'Ry': '#d29922', 'Rz': '#3fb950',
    'SWAP': '#da3633', 'Toffoli': '#bc8cff', 'CCX': '#bc8cff',
    'Measure': '#f0883e',
    'I': '#8b949e',
}

GATE_PARAMETERS = {
    'Rx': {'params': ['angle'], 'default_params': [0.0]},
    'Ry': {'params': ['angle'], 'default_params': [0.0]},
    'Rz': {'params': ['angle'], 'default_params': [0.0]},
    'CRx': {'params': ['angle'], 'default_params': [0.0]},
    'CRy': {'params': ['angle'], 'default_params': [0.0]},
    'CRz': {'params': ['angle'], 'default_params': [0.0]},
}

MULTI_QUBIT_GATES = {'CNOT', 'CX', 'CZ', 'SWAP', 'Toffoli', 'CCX', 'CRx', 'CRy', 'CRz'}


@dataclass
class GateItem:
    """A single gate in the circuit."""
    name: str
    qubit: int
    target_qubit: Optional[int] = None
    params: List[float] = field(default_factory=list)
    col: int = 0
    gate_id: str = ''

    def __post_init__(self):
        if not self.gate_id:
            self.gate_id = f"{self.name}_{self.qubit}_{self.col}"

    @property
    def color(self) -> str:
        return GATE_COLORS.get(self.name, '#8b949e')

    @property
    def is_multi_qubit(self) -> bool:
        return self.name in MULTI_QUBIT_GATES

    @property
    def box_width(self) -> float:
        if self.is_multi_qubit:
            return 0.8
        return 0.6

    def to_dict(self) -> Dict:
        d = {'name': self.name, 'qubits': [self.qubit]}
        if self.target_qubit is not None:
            d['qubits'].append(self.target_qubit)
        if self.params:
            d['params'] = self.params
        return d

    def __repr__(self):
        qubits = [self.qubit]
        if self.target_qubit is not None:
            qubits.append(self.target_qubit)
        return f"Gate({self.name}, qubits={qubits}, col={self.col})"


AVAILABLE_GATES = [
    {'name': 'H', 'category': 'Clifford', 'description': 'Hadamard', 'qubits': 1},
    {'name': 'X', 'category': 'Pauli', 'description': 'Pauli-X (NOT)', 'qubits': 1},
    {'name': 'Y', 'category': 'Pauli', 'description': 'Pauli-Y', 'qubits': 1},
    {'name': 'Z', 'category': 'Pauli', 'description': 'Pauli-Z', 'qubits': 1},
    {'name': 'S', 'category': 'Clifford', 'description': 'S (√Z)', 'qubits': 1},
    {'name': 'Sdg', 'category': 'Clifford', 'description': 'S†', 'qubits': 1},
    {'name': 'T', 'category': 'Non-Clifford', 'description': 'T (π/8)', 'qubits': 1},
    {'name': 'Tdg', 'category': 'Non-Clifford', 'description': 'T†', 'qubits': 1},
    {'name': 'Rx', 'category': 'Rotation', 'description': 'Rx(θ)', 'qubits': 1, 'params': ['angle']},
    {'name': 'Ry', 'category': 'Rotation', 'description': 'Ry(θ)', 'qubits': 1, 'params': ['angle']},
    {'name': 'Rz', 'category': 'Rotation', 'description': 'Rz(θ)', 'qubits': 1, 'params': ['angle']},
    {'name': 'CNOT', 'category': 'Entangling', 'description': 'CNOT (CX)', 'qubits': 2},
    {'name': 'CZ', 'category': 'Entangling', 'description': 'CZ', 'qubits': 2},
    {'name': 'SWAP', 'category': 'Entangling', 'description': 'SWAP', 'qubits': 2},
    {'name': 'Toffoli', 'category': 'Multi-qubit', 'description': 'Toffoli (CCX)', 'qubits': 3},
    {'name': 'Measure', 'category': 'Measurement', 'description': 'Measurement', 'qubits': 1},
]


class CircuitEditor:
    """Visual quantum circuit editor with drag-and-drop support."""

    def __init__(self, num_qubits: int = 3):
        self.num_qubits = num_qubits
        self.gates: List[GateItem] = []
        self._grid: Dict[Tuple[int, int], GateItem] = {}
        self.max_cols = 0
        self.selected_gate: Optional[GateItem] = None
        self._callbacks: Dict[str, List] = {
            'gate_added': [],
            'gate_removed': [],
            'circuit_changed': [],
            'selection_changed': [],
        }

    def on(self, event: str, callback):
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any = None):
        for cb in self._callbacks.get(event, []):
            try:
                cb(data)
            except Exception:
                pass

    def add_gate(self, name: str, qubit: int, target_qubit: Optional[int] = None,
                 params: Optional[List[float]] = None, col: Optional[int] = None) -> GateItem:
        if col is None:
            col = self._find_next_col(qubit)
            if target_qubit is not None:
                col = max(col, self._find_next_col(target_qubit))

        if (col, qubit) in self._grid:
            self.remove_gate_at(qubit, col)
        if target_qubit is not None and (col, target_qubit) in self._grid:
            self.remove_gate_at(target_qubit, col)

        gate = GateItem(
            name=name, qubit=qubit, target_qubit=target_qubit,
            params=params or [], col=col,
        )
        self.gates.append(gate)
        self._grid[(col, qubit)] = gate
        if target_qubit is not None:
            self._grid[(col, target_qubit)] = gate
        self.max_cols = max(self.max_cols, col + 1)

        self._emit('gate_added', gate)
        self._emit('circuit_changed', self)
        return gate

    def remove_gate_at(self, qubit: int, col: int) -> Optional[GateItem]:
        gate = self._grid.pop((col, qubit), None)
        if gate:
            self._remove_gate_connections(gate)
            self.gates = [g for g in self.gates if g.gate_id != gate.gate_id]
            self._emit('gate_removed', gate)
            self._emit('circuit_changed', self)
        return gate

    def _remove_gate_connections(self, gate: GateItem):
        keys_to_remove = []
        for (c, q), g in self._grid.items():
            if g.gate_id == gate.gate_id:
                keys_to_remove.append((c, q))
        for k in keys_to_remove:
            self._grid.pop(k, None)

    def move_gate(self, gate: GateItem, new_qubit: int, new_col: int):
        self._remove_gate_connections(gate)
        gate.qubit = new_qubit
        gate.col = new_col
        if gate.target_qubit is not None:
            if new_qubit != gate.qubit:
                old_target = gate.target_qubit
                gate.target_qubit = new_qubit + (old_target - gate.qubit)
        self._grid[(new_col, new_qubit)] = gate
        if gate.target_qubit is not None:
            self._grid[(new_col, gate.target_qubit)] = gate
        self.max_cols = max(self.max_cols, new_col + 1)
        self._emit('circuit_changed', self)

    def _find_next_col(self, qubit: int) -> int:
        col = 0
        while (col, qubit) in self._grid:
            col += 1
        return col

    def insert_col(self, after_col: int):
        new_grid = {}
        for (c, q), g in self._grid.items():
            if c > after_col:
                new_grid[(c + 1, q)] = g
                g.col = c + 1
            else:
                new_grid[(c, q)] = g
        self._grid = new_grid
        self.max_cols += 1
        self._emit('circuit_changed', self)

    def delete_col(self, col: int):
        gates_in_col = set()
        keys_to_remove = []
        for (c, q), g in self._grid.items():
            if c == col:
                gates_in_col.add(g.gate_id)
                keys_to_remove.append((c, q))
        for k in keys_to_remove:
            self._grid.pop(k, None)
        self.gates = [g for g in self.gates if g.gate_id not in gates_in_col]

        new_grid = {}
        for (c, q), g in self._grid.items():
            if c > col:
                new_grid[(c - 1, q)] = g
                g.col = c - 1
            else:
                new_grid[(c, q)] = g
        self._grid = new_grid
        self.max_cols = max(0, self.max_cols - 1)
        self._emit('circuit_changed', self)

    def clear(self):
        self.gates.clear()
        self._grid.clear()
        self.max_cols = 0
        self.selected_gate = None
        self._emit('circuit_changed', self)

    def get_gate_at(self, qubit: int, col: int) -> Optional[GateItem]:
        return self._grid.get((col, qubit))

    def get_column(self, col: int) -> List[GateItem]:
        seen = set()
        result = []
        for q in range(self.num_qubits):
            gate = self._grid.get((col, q))
            if gate and gate.gate_id not in seen:
                seen.add(gate.gate_id)
                result.append(gate)
        return result

    def select_gate(self, gate: Optional[GateItem]):
        self.selected_gate = gate
        self._emit('selection_changed', gate)

    def get_circuit_data(self) -> Dict:
        return {
            'num_qubits': self.num_qubits,
            'depth': self.max_cols,
            'gates': [g.to_dict() for g in self.gates],
        }

    def to_json(self) -> str:
        return json.dumps(self.get_circuit_data(), indent=2)

    def from_json(self, json_str: str):
        data = json.loads(json_str)
        self.clear()
        self.num_qubits = data.get('num_qubits', 3)
        for g in data.get('gates', []):
            qubits = g.get('qubits', [0])
            self.add_gate(
                name=g['name'],
                qubit=qubits[0],
                target_qubit=qubits[1] if len(qubits) > 1 else None,
                params=g.get('params', []),
            )

    def get_render_data(self) -> Dict:
        """Get data for rendering the circuit as a grid."""
        grid = {}
        for (col, qubit), gate in self._grid.items():
            if col not in grid:
                grid[col] = {}
            grid[col][qubit] = {
                'name': gate.name,
                'color': gate.color,
                'is_multi': gate.is_multi_qubit,
                'target': gate.target_qubit,
                'params': gate.params,
            }
        return {
            'num_qubits': self.num_qubits,
            'num_cols': self.max_cols,
            'grid': grid,
            'qubit_labels': [f'q{i}' for i in range(self.num_qubits)],
        }

    def import_from_abirqu_circuit(self, circuit) -> Dict:
        """Import from an abirqu Circuit object."""
        if hasattr(circuit, 'gates'):
            self.clear()
            for gate in circuit.gates:
                name = gate.get('name', '') if isinstance(gate, dict) else getattr(gate, 'name', '')
                qubits = gate.get('qubits', [0]) if isinstance(gate, dict) else getattr(gate, 'qubits', [0])
                self.add_gate(
                    name=name,
                    qubit=qubits[0] if qubits else 0,
                    target_qubit=qubits[1] if len(qubits) > 1 else None,
                )
            return self.get_circuit_data()
        return {'num_qubits': 0, 'depth': 0, 'gates': []}

    def __len__(self):
        return len(self.gates)

    def __repr__(self):
        return f"CircuitEditor(qubits={self.num_qubits}, gates={len(self.gates)}, depth={self.max_cols})"
