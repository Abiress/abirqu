"""
Quantum Circuit-to-Circuit Compiler for AbirQu
Copyright 2026 Abir Maheshwari

Compiles quantum circuits from one gate set to another,
optimizing for depth, gate count, and fidelity.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from abirqu.circuit import Circuit, Gate


# Native gate sets for common hardware
NATIVE_GATE_SETS = {
    'ibm': ['ECR', 'SX', 'RZ', 'X', 'ID'],
    'google': ['CZ', 'PhasedXPow', 'XPow', 'ZPow'],
    'ionq': ['RXX', 'Ry', 'Rz'],
    'rigetti': ['CZ', 'RX', 'RZ'],
    'neutral_atom': ['CZ', 'Ry', 'Rz'],
    'universal': ['H', 'T', 'CNOT'],
    'clifford': ['H', 'S', 'CNOT'],
}


def get_rotation_matrix(axis: str, angle: float) -> np.ndarray:
    """Get rotation matrix for single-qubit rotation."""
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    if axis == 'X':
        return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)
    elif axis == 'Y':
        return np.array([[c, -s], [s, c]], dtype=complex)
    elif axis == 'Z':
        return np.array([[np.exp(-1j * angle / 2), 0],
                         [0, np.exp(1j * angle / 2)]], dtype=complex)
    return np.eye(2, dtype=complex)


class GateDecomposer:
    """Decompose gates into native gate sets."""

    def __init__(self, target_gates: List[str]):
        self.target_gates = target_gates

    def decompose(self, gate: Gate) -> List[Gate]:
        """Decompose a gate into target gate set."""
        name = gate.name.upper()
        qubits = gate.qubits
        params = gate.params or []

        if name in self.target_gates:
            return [gate]

        # Decompose common gates
        if name == 'H':
            return self._decompose_h(qubits[0])
        elif name == 'T':
            return self._decompose_t(qubits[0])
        elif name == 'S':
            return self._decompose_s(qubits[0])
        elif name == 'X':
            return self._decompose_x(qubits[0])
        elif name == 'Y':
            return self._decompose_y(qubits[0])
        elif name == 'Z':
            return self._decompose_z(qubits[0])
        elif name in ('CNOT', 'CX'):
            return self._decompose_cnot(qubits[0], qubits[1])
        elif name == 'CZ':
            return self._decompose_cz(qubits[0], qubits[1])
        elif name == 'SWAP':
            return self._decompose_swap(qubits[0], qubits[1])
        elif name == 'RX':
            return self._decompose_rx(qubits[0], params[0] if params else 0)
        elif name == 'RY':
            return self._decompose_ry(qubits[0], params[0] if params else 0)
        elif name == 'RZ':
            return self._decompose_rz(qubits[0], params[0] if params else 0)
        elif name == 'TOFFOLI':
            return self._decompose_toffoli(qubits[0], qubits[1], qubits[2])

        return [gate]

    def _decompose_h(self, q: int) -> List[Gate]:
        """Decompose H using RZ and SX (IBM native)."""
        if 'SX' in self.target_gates and 'RZ' in self.target_gates:
            return [
                Gate('RZ', [q], params=[np.pi / 2]),
                Gate('SX', [q]),
                Gate('RZ', [q], params=[np.pi / 2]),
            ]
        elif 'H' in self.target_gates:
            return [Gate('H', [q])]
        else:
            # Fallback to T and CNOT
            return [
                Gate('RZ', [q], params=[np.pi / 2]),
                Gate('SX', [q]),
                Gate('RZ', [q], params=[np.pi / 2]),
            ]

    def _decompose_t(self, q: int) -> List[Gate]:
        """Decompose T gate."""
        if 'RZ' in self.target_gates:
            return [Gate('RZ', [q], params=[np.pi / 4])]
        elif 'T' in self.target_gates:
            return [Gate('T', [q])]
        else:
            return [Gate('RZ', [q], params=[np.pi / 4])]

    def _decompose_s(self, q: int) -> List[Gate]:
        """Decompose S gate."""
        if 'RZ' in self.target_gates:
            return [Gate('RZ', [q], params=[np.pi / 2])]
        elif 'S' in self.target_gates:
            return [Gate('S', [q])]
        else:
            return [Gate('RZ', [q], params=[np.pi / 2])]

    def _decompose_x(self, q: int) -> List[Gate]:
        """Decompose X gate."""
        if 'RX' in self.target_gates:
            return [Gate('RX', [q], params=[np.pi])]
        elif 'X' in self.target_gates:
            return [Gate('X', [q])]
        else:
            return [Gate('RX', [q], params=[np.pi])]

    def _decompose_y(self, q: int) -> List[Gate]:
        """Decompose Y gate."""
        if 'RY' in self.target_gates:
            return [Gate('RY', [q], params=[np.pi])]
        elif 'Y' in self.target_gates:
            return [Gate('Y', [q])]
        else:
            return [Gate('RY', [q], params=[np.pi])]

    def _decompose_z(self, q: int) -> List[Gate]:
        """Decompose Z gate."""
        if 'RZ' in self.target_gates:
            return [Gate('RZ', [q], params=[np.pi])]
        elif 'Z' in self.target_gates:
            return [Gate('Z', [q])]
        else:
            return [Gate('RZ', [q], params=[np.pi])]

    def _decompose_cnot(self, c: int, t: int) -> List[Gate]:
        """Decompose CNOT using CZ."""
        if 'CZ' in self.target_gates:
            return [
                Gate('H', [t]),
                Gate('CZ', [c, t]),
                Gate('H', [t]),
            ]
        elif 'CNOT' in self.target_gates or 'CX' in self.target_gates:
            return [Gate('CNOT', [c, t])]
        else:
            return [Gate('CNOT', [c, t])]

    def _decompose_cz(self, c: int, t: int) -> List[Gate]:
        """Decompose CZ using CNOT."""
        if 'CNOT' in self.target_gates or 'CX' in self.target_gates:
            return [
                Gate('H', [t]),
                Gate('CNOT', [c, t]),
                Gate('H', [t]),
            ]
        elif 'CZ' in self.target_gates:
            return [Gate('CZ', [c, t])]
        else:
            return [Gate('CZ', [c, t])]

    def _decompose_swap(self, q1: int, q2: int) -> List[Gate]:
        """Decompose SWAP using 3 CNOTs."""
        return [
            Gate('CNOT', [q1, q2]),
            Gate('CNOT', [q2, q1]),
            Gate('CNOT', [q1, q2]),
        ]

    def _decompose_rx(self, q: int, angle: float) -> List[Gate]:
        """Decompose RX."""
        if 'RX' in self.target_gates:
            return [Gate('RX', [q], params=[angle])]
        elif 'RZ' in self.target_gates and 'SX' in self.target_gates:
            return [
                Gate('RZ', [q], params=[-np.pi / 2]),
                Gate('SX', [q]),
                Gate('RZ', [q], params=[angle]),
                Gate('SX', [q]),
                Gate('RZ', [q], params=[np.pi / 2]),
            ]
        return [Gate('RX', [q], params=[angle])]

    def _decompose_ry(self, q: int, angle: float) -> List[Gate]:
        """Decompose RY."""
        if 'RY' in self.target_gates:
            return [Gate('RY', [q], params=[angle])]
        elif 'RZ' in self.target_gates and 'SX' in self.target_gates:
            return [
                Gate('RZ', [q], params=[np.pi / 2]),
                Gate('SX', [q]),
                Gate('RZ', [q], params=[angle]),
                Gate('SX', [q]),
                Gate('RZ', [q], params=[-np.pi / 2]),
            ]
        return [Gate('RY', [q], params=[angle])]

    def _decompose_rz(self, q: int, angle: float) -> List[Gate]:
        """Decompose RZ."""
        if 'RZ' in self.target_gates:
            return [Gate('RZ', [q], params=[angle])]
        return [Gate('RZ', [q], params=[angle])]

    def _decompose_toffoli(self, c1: int, c2: int, t: int) -> List[Gate]:
        """Decompose Toffoli using CNOT and single-qubit gates."""
        gates = []
        gates.append(Gate('H', [t]))
        gates.append(Gate('CNOT', [c2, t]))
        gates.append(Gate('T_DAG', [t]))
        gates.append(Gate('CNOT', [c1, t]))
        gates.append(Gate('T', [t]))
        gates.append(Gate('CNOT', [c2, t]))
        gates.append(Gate('T_DAG', [t]))
        gates.append(Gate('CNOT', [c1, t]))
        gates.append(Gate('T', [c2]))
        gates.append(Gate('T', [t]))
        gates.append(Gate('H', [t]))
        gates.append(Gate('CNOT', [c1, c2]))
        gates.append(Gate('T', [c1]))
        gates.append(Gate('T_DAG', [c2]))
        gates.append(Gate('CNOT', [c1, c2]))
        return gates


class CircuitCompiler:
    """
    Compile quantum circuits to target hardware.

    Features:
    - Gate decomposition to native gate sets
    - Circuit optimization (gate merging, cancellation)
    - Routing for connectivity constraints
    - Depth optimization

    Usage:
        compiler = CircuitCompiler(target='ibm')
        compiled = compiler.compile(circuit)
    """

    def __init__(self, target: str = 'universal', custom_gates: Optional[List[str]] = None):
        self.target = target
        self.native_gates = custom_gates or NATIVE_GATE_SETS.get(target, ['H', 'T', 'CNOT'])
        self.decomposer = GateDecomposer(self.native_gates)
        self.stats = {
            'original_gates': 0,
            'compiled_gates': 0,
            'original_depth': 0,
            'compiled_depth': 0,
            'optimizations_applied': 0,
        }

    def compile(self, circuit: Circuit, optimize: bool = True) -> Circuit:
        """
        Compile circuit to target gate set.

        Steps:
        1. Decompose all gates to native gate set
        2. Apply optimization passes
        3. Return compiled circuit
        """
        self.stats['original_gates'] = len(circuit.gates)
        self.stats['original_depth'] = self._compute_depth(circuit)

        # Step 1: Decompose
        compiled = Circuit(circuit.num_qubits, f"{circuit.name}_compiled")
        for gate in circuit.gates:
            decomposed = self.decomposer.decompose(gate)
            for g in decomposed:
                compiled.add_gate(g.name, g.qubits, g.params)

        # Step 2: Optimize
        if optimize:
            compiled = self._optimize(compiled)

        self.stats['compiled_gates'] = len(compiled.gates)
        self.stats['compiled_depth'] = self._compute_depth(compiled)

        return compiled

    def _optimize(self, circuit: Circuit) -> Circuit:
        """Apply optimization passes."""
        optimized = Circuit(circuit.num_qubits, circuit.name)

        # Gate cancellation: remove adjacent inverse gates
        i = 0
        while i < len(circuit.gates):
            gate = circuit.gates[i]

            # Check if next gate cancels this one
            if i + 1 < len(circuit.gates):
                next_gate = circuit.gates[i + 1]
                if self._gates_cancel(gate, next_gate):
                    self.stats['optimizations_applied'] += 1
                    i += 2
                    continue

            # Check if next gate merges with this one
            if i + 1 < len(circuit.gates):
                next_gate = circuit.gates[i + 1]
                merged = self._try_merge(gate, next_gate)
                if merged is not None:
                    for g in merged:
                        optimized.add_gate(g.name, g.qubits, g.params)
                    self.stats['optimizations_applied'] += 1
                    i += 2
                    continue

            optimized.add_gate(gate.name, gate.qubits, gate.params)
            i += 1

        return optimized

    def _gates_cancel(self, g1: Gate, g2: Gate) -> bool:
        """Check if two gates cancel each other (g1 * g2 = I)."""
        if g1.qubits != g2.qubits:
            return False

        name1, name2 = g1.name.upper(), g2.name.upper()

        # Same gate cancels with itself (X*X=I, H*H=I, etc.)
        if name1 == name2 and name1 in ('X', 'Y', 'Z', 'H', 'CNOT', 'CX', 'CZ'):
            return True

        # Gate and its inverse cancel
        inverse_pairs = {
            ('S', 'S_DAG'), ('T', 'T_DAG'), ('RX', 'RX'),
            ('RY', 'RY'), ('RZ', 'RZ'),
        }

        if (name1, name2) in inverse_pairs or (name2, name1) in inverse_pairs:
            if name1 in ('RX', 'RY', 'RZ') and name2 in ('RX', 'RY', 'RZ'):
                # Check if angles sum to 2*pi
                angle1 = g1.params[0] if g1.params else 0
                angle2 = g2.params[0] if g2.params else 0
                return abs(angle1 + angle2) < 1e-10 or abs(angle1 + angle2 - 2 * np.pi) < 1e-10
            return True

        return False

    def _try_merge(self, g1: Gate, g2: Gate) -> Optional[List[Gate]]:
        """Try to merge two gates into one."""
        if g1.qubits != g2.qubits or len(g1.qubits) != 1:
            return None

        name1, name2 = g1.name.upper(), g2.name.upper()

        # Merge rotations: R_X(a) * R_X(b) = R_X(a+b)
        if name1 == name2 and name1 in ('RX', 'RY', 'RZ'):
            angle1 = g1.params[0] if g1.params else 0
            angle2 = g2.params[0] if g2.params else 0
            merged_angle = angle1 + angle2
            # Normalize to [0, 2*pi]
            merged_angle = merged_angle % (2 * np.pi)
            if merged_angle < 1e-10:
                return []  # Cancel out
            return [Gate(name1, g1.qubits, params=[merged_angle])]

        return None

    def _compute_depth(self, circuit: Circuit) -> int:
        """Compute circuit depth (longest path)."""
        if not circuit.gates:
            return 0

        # Simple depth estimation
        depth = 0
        layers = {}
        for gate in circuit.gates:
            qubits = gate.qubits
            layer = max((layers.get(q, 0) for q in qubits), default=0)
            for q in qubits:
                layers[q] = layer + 1
            depth = max(depth, layer + 1)

        return depth

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


class RoutingCompiler:
    """
    Route circuits for hardware with limited connectivity.

    Inserts SWAP gates to make non-adjacent qubits interact.
    """

    def __init__(self, coupling_map: Optional[List[Tuple[int, int]]] = None):
        self.coupling_map = coupling_map or []
        self.swap_count = 0

    def route(self, circuit: Circuit) -> Circuit:
        """Route circuit to match hardware connectivity."""
        if not self.coupling_map:
            return circuit

        routed = Circuit(circuit.num_qubits, f"{circuit.name}_routed")
        qubit_map = list(range(circuit.num_qubits))

        for gate in circuit.gates:
            if len(gate.qubits) <= 1:
                routed.add_gate(gate.name, gate.qubits, gate.params)
                continue

            q0, q1 = gate.qubits[0], gate.qubits[1]
            phys_q0 = qubit_map[q0]
            phys_q1 = qubit_map[q1]

            # Check if qubits are connected
            if self._are_connected(phys_q0, phys_q1):
                routed.add_gate(gate.name, gate.qubits, gate.params)
            else:
                # Insert SWAP to bring qubits closer
                path = self._find_swapping_path(phys_q0, phys_q1)
                for swap_q in path:
                    # Find logical qubit at swap position
                    for logical, physical in enumerate(qubit_map):
                        if physical == swap_q:
                            routed.add_gate('SWAP', [logical, logical + 1])
                            qubit_map[logical], qubit_map[logical + 1] = (
                                qubit_map[logical + 1], qubit_map[logical]
                            )
                            self.swap_count += 1
                routed.add_gate(gate.name, gate.qubits, gate.params)

        return routed

    def _are_connected(self, q1: int, q2: int) -> bool:
        """Check if two qubits are directly connected."""
        return (q1, q2) in self.coupling_map or (q2, q1) in self.coupling_map

    def _find_swapping_path(self, source: int, target: int) -> List[int]:
        """Find SWAP path between two qubits using BFS."""
        from collections import deque

        adjacency = {}
        for q1, q2 in self.coupling_map:
            if q1 not in adjacency:
                adjacency[q1] = []
            if q2 not in adjacency:
                adjacency[q2] = []
            adjacency[q1].append(q2)
            adjacency[q2].append(q1)

        visited = {source}
        queue = deque([(source, [])])

        while queue:
            current, path = queue.popleft()
            if current == target:
                return path

            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []
