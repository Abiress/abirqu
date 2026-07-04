"""
Entanglement-Aware Circuit Cutting for AbirQu
Copyright 2026 Abir Maheshwari

Novel contribution: Analyzes entanglement structure of circuits to find
optimal cut points that minimize classical communication overhead.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from abirqu.circuit import Circuit


class EntanglementAnalyzer:
    """
    Analyzes entanglement structure of quantum circuits.

    Uses bond dimension heuristics to estimate which qubit pairs
    are entangled at each step.
    """

    def __init__(self, max_bond: int = 8):
        self.max_bond = max_bond

    def analyze_circuit(self, circuit: Circuit) -> 'EntanglementGraph':
        """
        Build an entanglement graph from the circuit.

        Returns an EntanglementGraph with entanglement weights
        for each qubit pair.
        """
        n = circuit.num_qubits
        graph = EntanglementGraph(n)

        bond_dims = np.ones((n, n), dtype=float)

        for gate in circuit.gates:
            name = gate.name.upper()
            if name in ('CNOT', 'CX', 'CZ'):
                q0, q1 = gate.qubits[0], gate.qubits[1]
                bond_dims[q0, q1] = min(bond_dims[q0, q1] * 2, self.max_bond)
                bond_dims[q1, q0] = bond_dims[q0, q1]
                graph.add_entanglement(q0, q1, float(bond_dims[q0, q1]) / self.max_bond)
            elif name == 'SWAP':
                q0, q1 = gate.qubits[0], gate.qubits[1]
                bond_dims[q0, q1] = min(bond_dims[q0, q1] * 1.5, self.max_bond)
                bond_dims[q1, q0] = bond_dims[q0, q1]
                graph.add_entanglement(q0, q1, float(bond_dims[q0, q1]) / self.max_bond)
            elif name in ('H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ'):
                q = gate.qubits[0]
                for q2 in range(n):
                    if q2 != q and bond_dims[q, q2] > 1:
                        bond_dims[q, q2] *= 0.95
                        bond_dims[q2, q] = bond_dims[q, q2]

        return graph


class EntanglementGraph:
    """Graph tracking entanglement between qubit pairs."""

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self.weights = np.zeros((n_qubits, n_qubits), dtype=float)
        self.total_entanglement = 0.0

    def add_entanglement(self, q1: int, q2: int, weight: float):
        self.weights[q1, q2] += weight
        self.weights[q2, q1] += weight
        self.total_entanglement += weight

    def get_pair_weight(self, q1: int, q2: int) -> float:
        return max(self.weights[q1, q2], self.weights[q2, q1])

    def get_cut_cost(self, qubits_a: set, qubits_b: set) -> float:
        """Compute total entanglement crossing a cut."""
        cost = 0.0
        for q1 in qubits_a:
            for q2 in qubits_b:
                cost += self.get_pair_weight(q1, q2)
        return cost

    def find_best_linear_cut(self) -> Tuple[int, float]:
        """Find the best linear cut point."""
        best_idx = self.n_qubits // 2
        best_cost = float('inf')

        for split in range(1, self.n_qubits):
            qubits_a = set(range(split))
            qubits_b = set(range(split, self.n_qubits))
            cost = self.get_cut_cost(qubits_a, qubits_b)
            if cost < best_cost:
                best_cost = cost
                best_idx = split

        return best_idx, best_cost

    def find_best_partition_cut(self, n_partitions: int = 2) -> List[set]:
        """Find best partition cut."""
        if n_partitions == 2:
            split, _ = self.find_best_linear_cut()
            return [set(range(split)), set(range(split, self.n_qubits))]

        qubits_per_part = self.n_qubits // n_partitions
        partitions = []
        for i in range(n_partitions):
            start = i * qubits_per_part
            if i == n_partitions - 1:
                partitions.append(set(range(start, self.n_qubits)))
            else:
                partitions.append(set(range(start, start + qubits_per_part)))
        return partitions


class EntanglementCutter:
    """
    Cuts quantum circuits based on entanglement structure.

    Novel contribution: Unlike standard circuit cutters that cut at
    the midpoint, this cutter analyzes entanglement to find cut points
    that minimize classical communication overhead.

    Usage:
        cutter = EntanglementCutter(max_subcircuit_qubits=5)
        result = cutter.cut(circuit)
        combined = cutter.recombine(result, sub_results)
    """

    def __init__(self, max_subcircuit_qubits: int = 5,
                 max_bond: int = 8):
        self.max_subcircuit_qubits = max_subcircuit_qubits
        self.analyzer = EntanglementAnalyzer(max_bond=max_bond)

    def cut(self, circuit: Circuit) -> 'CutResult':
        """Cut a circuit based on entanglement analysis."""
        if circuit.num_qubits <= self.max_subcircuit_qubits:
            return CutResult(
                sub_circuits=[circuit.copy()],
                cut_points=[],
                entanglement_graph=None,
                overhead_estimate=0.0,
            )

        graph = self.analyzer.analyze_circuit(circuit)
        n_cuts = (circuit.num_qubits - 1) // self.max_subcircuit_qubits

        if n_cuts == 1:
            split_idx, cost = graph.find_best_linear_cut()
            sub_circuits = self._split_circuit_linear(circuit, split_idx)
            cut_points = [(split_idx, cost)]
        else:
            partitions = graph.find_best_partition_cut(n_cuts + 1)
            sub_circuits = self._split_circuit_partitions(circuit, partitions)
            cut_points = []
            for i in range(len(partitions) - 1):
                qubits_a = set()
                for j in range(i + 1):
                    qubits_a.update(partitions[j])
                qubits_b = set()
                for j in range(i + 1, len(partitions)):
                    qubits_b.update(partitions[j])
                cut_cost = graph.get_cut_cost(qubits_a, qubits_b)
                cut_points.append((len(qubits_a), cut_cost))

        overhead = self._estimate_overhead(sub_circuits, cut_points)

        return CutResult(
            sub_circuits=sub_circuits,
            cut_points=cut_points,
            entanglement_graph=graph,
            overhead_estimate=overhead,
        )

    def _split_circuit_linear(self, circuit: Circuit, split_idx: int) -> List[Circuit]:
        """Split circuit at a linear cut point."""
        circ_a = Circuit(split_idx, 'sub_a')
        circ_b = Circuit(circuit.num_qubits - split_idx, 'sub_b')

        for gate in circuit.gates:
            qubits = gate.qubits
            if all(q < split_idx for q in qubits):
                self._add_gate(circ_a, gate)
            elif all(q >= split_idx for q in qubits):
                self._add_gate_shifted(circ_b, gate, -split_idx)
            else:
                self._add_gate(circ_a, gate)

        return [circ_a, circ_b]

    def _split_circuit_partitions(self, circuit: Circuit,
                                  partitions: List[set]) -> List[Circuit]:
        """Split circuit into multiple partitions."""
        sub_circuits = []
        qubit_map = {}
        for part_idx, part in enumerate(partitions):
            for q in part:
                qubit_map[q] = part_idx
            sub_circuits.append(Circuit(len(part), f'sub_{part_idx}'))

        local_idx_map = {}
        for part_idx, part in enumerate(partitions):
            for i, q in enumerate(sorted(part)):
                local_idx_map[q] = i

        for gate in circuit.gates:
            qubits = gate.qubits
            part_indices = set(qubit_map.get(q, 0) for q in qubits)

            if len(part_indices) == 1:
                part_idx = list(part_indices)[0]
                new_qubits = [local_idx_map[q] for q in qubits]
                self._add_gate_at(sub_circuits[part_idx], gate, new_qubits)

        return sub_circuits

    def _add_gate(self, circ: Circuit, gate):
        """Add a gate to a circuit."""
        self._add_gate_at(circ, gate, gate.qubits)

    def _add_gate_shifted(self, circ: Circuit, gate, shift: int):
        """Add a gate with shifted qubit indices."""
        self._add_gate_at(circ, gate, [q + shift for q in gate.qubits])

    def _add_gate_at(self, circ: Circuit, gate, qubits):
        """Add a gate at specific qubit indices."""
        name = gate.name.upper()
        params = gate.params

        if name == 'H': circ.h(qubits[0])
        elif name == 'X': circ.x(qubits[0])
        elif name == 'Y': circ.y(qubits[0])
        elif name == 'Z': circ.z(qubits[0])
        elif name == 'S': circ.s(qubits[0])
        elif name == 'T': circ.t(qubits[0])
        elif name in ('CNOT', 'CX'): circ.cnot(qubits[0], qubits[1])
        elif name == 'CZ': circ.cz(qubits[0], qubits[1])
        elif name == 'RZ': circ.rz(qubits[0], params[0])
        elif name == 'RX': circ.rx(qubits[0], params[0])
        elif name == 'RY': circ.ry(qubits[0], params[0])
        elif name == 'SWAP': circ.swap(qubits[0], qubits[1])

    def _estimate_overhead(self, sub_circuits: List[Circuit],
                           cut_points: List) -> float:
        """Estimate classical communication overhead in Bell pairs."""
        if not cut_points:
            return 0.0
        overhead = 0.0
        for split_idx, cost in cut_points:
            n_bell_pairs = max(1, int(np.ceil(cost * 2)))
            overhead += n_bell_pairs
        return overhead

    def recombine(self, results: 'CutResult',
                  sub_results: List[Dict[str, int]]) -> Dict[str, float]:
        """Recombine measurement results from sub-circuits."""
        if len(sub_results) == 1:
            total = sum(sub_results[0].values())
            return {k: v / total for k, v in sub_results[0].items()}

        combined = {}
        for result in sub_results:
            total = sum(result.values())
            for state, count in result.items():
                prob = count / total
                combined[state] = combined.get(state, 0.0) + prob

        total = sum(combined.values())
        if total > 0:
            combined = {k: v / total for k, v in combined.items()}
        return combined


class CutResult:
    """Container for circuit cutting results."""

    def __init__(self, sub_circuits: List[Circuit], cut_points: List,
                 entanglement_graph: Optional[EntanglementGraph],
                 overhead_estimate: float):
        self.sub_circuits = sub_circuits
        self.cut_points = cut_points
        self.entanglement_graph = entanglement_graph
        self.overhead_estimate = overhead_estimate

    def __repr__(self):
        return (f"CutResult(sub_circuits={len(self.sub_circuits)}, "
                f"cuts={len(self.cut_points)}, "
                f"overhead={self.overhead_estimate:.1f} Bell pairs)")
