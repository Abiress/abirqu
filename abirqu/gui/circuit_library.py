"""
AbirQu Circuit Library
Copyright 2026 Abir Maheshwari

Built-in circuit library with common quantum algorithms and circuits.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CircuitTemplate:
    """A circuit template in the library."""
    template_id: str
    name: str
    description: str
    category: str
    num_qubits: int
    depth: int
    gates: List[Dict]
    tags: List[str]
    difficulty: str = 'beginner'  # 'beginner', 'intermediate', 'advanced'
    author: str = 'AbirQu'

    def to_dict(self) -> Dict:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'num_qubits': self.num_qubits,
            'depth': self.depth,
            'gates': self.gates,
            'tags': self.tags,
            'difficulty': self.difficulty,
            'author': self.author,
        }


class CircuitLibraryPanel:
    """Circuit library with built-in templates and user circuits."""

    def __init__(self):
        self.templates: Dict[str, CircuitTemplate] = {}
        self.user_circuits: Dict[str, CircuitTemplate] = {}
        self.categories = set()
        self._callbacks = []
        self._register_builtin_circuits()

    def _register_builtin_circuits(self):
        builtins = [
            CircuitTemplate(
                template_id='bell_state',
                name='Bell State',
                description='Creates a Bell pair (|00⟩ + |11⟩) / √2',
                category='Fundamental',
                num_qubits=2,
                depth=2,
                gates=[
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'CNOT', 'qubits': [0, 1]},
                ],
                tags=['entanglement', 'bell', 'basic'],
                difficulty='beginner',
            ),
            CircuitTemplate(
                template_id='ghz_state',
                name='GHZ State',
                description='N-qubit GHZ state: (|000...0⟩ + |111...1⟩) / √2',
                category='Fundamental',
                num_qubits=5,
                depth=5,
                gates=[
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'CNOT', 'qubits': [0, 1]},
                    {'name': 'CNOT', 'qubits': [1, 2]},
                    {'name': 'CNOT', 'qubits': [2, 3]},
                    {'name': 'CNOT', 'qubits': [3, 4]},
                ],
                tags=['entanglement', 'ghz', 'multi-qubit'],
                difficulty='beginner',
            ),
            CircuitTemplate(
                template_id='quantum_teleportation',
                name='Quantum Teleportation',
                description='Teleports an arbitrary state from q0 to q2',
                category='Algorithms',
                num_qubits=3,
                depth=5,
                gates=[
                    {'name': 'Ry', 'qubits': [0], 'params': [0.785]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'CNOT', 'qubits': [1, 2]},
                    {'name': 'CNOT', 'qubits': [0, 1]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'Measure', 'qubits': [0]},
                    {'name': 'Measure', 'qubits': [1]},
                ],
                tags=['teleportation', 'entanglement', 'communication'],
                difficulty='intermediate',
            ),
            CircuitTemplate(
                template_id='deutsch_jozsa',
                name='Deutsch-Jozsa',
                description='Determines if a function is constant or balanced',
                category='Algorithms',
                num_qubits=3,
                depth=4,
                gates=[
                    {'name': 'X', 'qubits': [2]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'H', 'qubits': [2]},
                    {'name': 'CNOT', 'qubits': [0, 2]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                ],
                tags=['oracle', 'decision', 'quantum-advantage'],
                difficulty='intermediate',
            ),
            CircuitTemplate(
                template_id='grover_2qubit',
                name="Grover's Search (2-qubit)",
                description="Searches for |11⟩ in 4 items with 1 iteration",
                category='Algorithms',
                num_qubits=2,
                depth=6,
                gates=[
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'CZ', 'qubits': [0, 1]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'X', 'qubits': [0]},
                    {'name': 'X', 'qubits': [1]},
                    {'name': 'CZ', 'qubits': [0, 1]},
                    {'name': 'X', 'qubits': [0]},
                    {'name': 'X', 'qubits': [1]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                ],
                tags=['search', 'amplitude-amplification', 'oracle'],
                difficulty='intermediate',
            ),
            CircuitTemplate(
                template_id='qft_3qubit',
                name='Quantum Fourier Transform (3-qubit)',
                description='QFT on 3 qubits',
                category='Algorithms',
                num_qubits=3,
                depth=6,
                gates=[
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'Rz', 'qubits': [1], 'params': [1.5708]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'Rz', 'qubits': [2], 'params': [0.7854]},
                    {'name': 'Rz', 'qubits': [2], 'params': [1.5708]},
                    {'name': 'H', 'qubits': [2]},
                    {'name': 'SWAP', 'qubits': [0, 2]},
                ],
                tags=['qft', 'fourier', 'phase-estimation'],
                difficulty='advanced',
            ),
            CircuitTemplate(
                template_id='bernstein_vazirani',
                name='Bernstein-Vazirani',
                description='Finds hidden bitstring s using quantum query',
                category='Algorithms',
                num_qubits=4,
                depth=3,
                gates=[
                    {'name': 'X', 'qubits': [3]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'H', 'qubits': [2]},
                    {'name': 'H', 'qubits': [3]},
                    {'name': 'CNOT', 'qubits': [0, 3]},
                    {'name': 'CNOT', 'qubits': [2, 3]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'H', 'qubits': [2]},
                ],
                tags=['oracle', 'hidden-subgroup', 'bernstein-vazirani'],
                difficulty='intermediate',
            ),
            CircuitTemplate(
                template_id='bit_flip_code',
                name='3-Qubit Bit-Flip Code',
                description='Encodes and corrects single bit-flip errors',
                category='QEC',
                num_qubits=3,
                depth=2,
                gates=[
                    {'name': 'CNOT', 'qubits': [0, 1]},
                    {'name': 'CNOT', 'qubits': [0, 2]},
                ],
                tags=['error-correction', 'bit-flip', 'qec'],
                difficulty='beginner',
            ),
            CircuitTemplate(
                template_id='phase_flip_code',
                name='3-Qubit Phase-Flip Code',
                description='Encodes and corrects single phase-flip errors',
                category='QEC',
                num_qubits=3,
                depth=4,
                gates=[
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'H', 'qubits': [2]},
                    {'name': 'CNOT', 'qubits': [0, 1]},
                    {'name': 'CNOT', 'qubits': [0, 2]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'H', 'qubits': [1]},
                    {'name': 'H', 'qubits': [2]},
                ],
                tags=['error-correction', 'phase-flip', 'qec'],
                difficulty='beginner',
            ),
            CircuitTemplate(
                template_id='qram',
                name='QRAM (Quantum RAM)',
                description='Quantum random access memory circuit',
                category='Circuits',
                num_qubits=4,
                depth=4,
                gates=[
                    {'name': 'X', 'qubits': [2]},
                    {'name': 'CNOT', 'qubits': [2, 0]},
                    {'name': 'CNOT', 'qubits': [2, 1]},
                    {'name': 'X', 'qubits': [2]},
                    {'name': 'CNOT', 'qubits': [3, 0]},
                    {'name': 'CNOT', 'qubits': [3, 1]},
                ],
                tags=['memory', 'data-structure', 'qram'],
                difficulty='advanced',
            ),
            CircuitTemplate(
                template_id='swap_test',
                name='Swap Test',
                description='Computes overlap between two quantum states',
                category='Circuits',
                num_qubits=3,
                depth=4,
                gates=[
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'CNOT', 'qubits': [0, 1]},
                    {'name': 'CNOT', 'qubits': [0, 2]},
                    {'name': 'H', 'qubits': [0]},
                    {'name': 'Measure', 'qubits': [0]},
                ],
                tags=['overlap', 'comparison', 'swap-test'],
                difficulty='intermediate',
            ),
            CircuitTemplate(
                template_id='w_state',
                name='W State',
                description='Creates W state: (|001⟩ + |010⟩ + |100⟩) / √3',
                category='Fundamental',
                num_qubits=3,
                depth=5,
                gates=[
                    {'name': 'Ry', 'qubits': [0], 'params': [1.2310]},
                    {'name': 'CNOT', 'qubits': [0, 1]},
                    {'name': 'CNOT', 'qubits': [0, 2]},
                    {'name': 'Ry', 'qubits': [1], 'params': [0.9553]},
                    {'name': 'CNOT', 'qubits': [1, 2]},
                    {'name': 'X', 'qubits': [1]},
                    {'name': 'CNOT', 'qubits': [2, 1]},
                    {'name': 'X', 'qubits': [1]},
                ],
                tags=['entanglement', 'w-state', 'multi-qubit'],
                difficulty='intermediate',
            ),
        ]
        for c in builtins:
            self.templates[c.template_id] = c
            self.categories.add(c.category)

    def on(self, event: str, callback):
        self._callbacks.append((event, callback))

    def _emit(self, event: str, data: Any):
        for ev, cb in self._callbacks:
            if ev == event:
                try:
                    cb(data)
                except Exception:
                    pass

    def get_template(self, template_id: str) -> Optional[CircuitTemplate]:
        return self.templates.get(template_id) or self.user_circuits.get(template_id)

    def get_by_category(self, category: str) -> List[CircuitTemplate]:
        return [t for t in self.templates.values() if t.category == category]

    def search(self, query: str) -> List[CircuitTemplate]:
        query_lower = query.lower()
        results = []
        for t in list(self.templates.values()) + list(self.user_circuits.values()):
            if (query_lower in t.name.lower() or
                query_lower in t.description.lower() or
                any(query_lower in tag for tag in t.tags)):
                results.append(t)
        return results

    def save_user_circuit(self, template: CircuitTemplate):
        self.user_circuits[template.template_id] = template
        self.categories.add(template.category)
        self._emit('circuit_saved', template.to_dict())

    def delete_user_circuit(self, template_id: str) -> bool:
        if template_id in self.user_circuits:
            del self.user_circuits[template_id]
            self._emit('circuit_deleted', template_id)
            return True
        return False

    def get_categories(self) -> List[str]:
        return sorted(self.categories)

    def get_render_data(self) -> Dict:
        builtin = [t.to_dict() for t in self.templates.values()]
        user = [t.to_dict() for t in self.user_circuits.values()]
        return {
            'builtin': builtin,
            'user': user,
            'categories': self.get_categories(),
            'total': len(self.templates) + len(self.user_circuits),
        }

    def __len__(self):
        return len(self.templates) + len(self.user_circuits)

    def __repr__(self):
        return f"CircuitLibraryPanel(templates={len(self.templates)}, user={len(self.user_circuits)})"
