"""
Quantum Circuit Simplifier for AbirQu
Copyright 2026 Abir Maheshwari

Combines rule-based simplification with algebraic phase polynomial optimization.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from abirqu.circuit import Circuit

class CircuitSimplifier:
    """
    Optimizes quantum circuits using a combination of:
    1. Basic rule-based simplification (Inverse cancellation, rotation merging)
    2. Advanced Phase Polynomial optimization (Matroid partitioning, Gaussian elimination)
    """

    def __init__(self):
        self.stats = {'original': 0, 'optimized': 0, 'removed': 0, 'pct': 0.0}

    def optimize(self, circuit: Circuit) -> Circuit:
        """
        Main optimization entry point.
        Applies a pipeline of optimization passes.
        """
        self.stats['original'] = len(circuit.gates)
        
        # Pass 1: Basic rule-based simplification (inverse cancellation, etc.)
        gates = list(circuit.gates)
        gates = self._cancel_inverses(gates)
        gates = self._merge_rotations(gates)
        gates = self._remove_identities(gates)
        
        # Re-build intermediate circuit for phase poly pass
        temp_circ = Circuit(circuit.num_qubits)
        for g in gates:
            self._add_gate_to_circuit(temp_circ, g)
            
        # Pass 2: Algebraic Phase Polynomial Optimization
        # (This handles CNOT count minimization for {CNOT, RZ} subcircuits)
        optimized_circ = self._algebraic_optimize(temp_circ)
        
        self.stats['optimized'] = len(optimized_circ.gates)
        self.stats['removed'] = self.stats['original'] - self.stats['optimized']
        if self.stats['original'] > 0:
            self.stats['pct'] = 100.0 * self.stats['removed'] / self.stats['original']
            
        return optimized_circ

    def simplify(self, circuit: Circuit) -> Circuit:
        """Alias for optimize() to maintain consistency with other frameworks."""
        return self.optimize(circuit)

    def _cancel_inverses(self, gates):
        self_inverse = {'H', 'X', 'Y', 'Z', 'CNOT', 'CX', 'SWAP'}
        result = []
        i = 0
        while i < len(gates):
            if i + 1 < len(gates):
                g1, g2 = gates[i], gates[i + 1]
                if (g1.name.upper() == g2.name.upper()
                        and g1.qubits == g2.qubits
                        and g1.name.upper() in self_inverse):
                    i += 2
                    continue
            result.append(gates[i])
            i += 1
        return result

    def _merge_rotations(self, gates):
        rotation_gates = {'RZ', 'RX', 'RY'}
        result = []
        i = 0
        while i < len(gates):
            g = gates[i]
            if g.name.upper() in rotation_gates and g.params:
                total_angle = g.params[0]
                j = i + 1
                while j < len(gates):
                    g2 = gates[j]
                    if (g2.name.upper() == g.name.upper()
                            and g2.qubits == g.qubits and g2.params):
                        total_angle += g2.params[0]
                        j += 1
                    else:
                        break
                merged = _SimpleGate(g.name, g.qubits, [total_angle])
                result.append(merged)
                i = j
            else:
                result.append(g)
                i += 1
        return result

    def _remove_identities(self, gates):
        result = []
        for g in gates:
            if g.name.upper() in ('RZ', 'RX', 'RY', 'Z', 'S', 'T') and g.params:
                angle = g.params[0] % (2 * np.pi)
                if abs(angle) < 1e-10 or abs(angle - 2 * np.pi) < 1e-10:
                    continue
            result.append(g)
        return result

    def _add_gate_to_circuit(self, circ, g):
        name = g.name.upper()
        if name == 'H': circ.h(g.qubits[0])
        elif name == 'X': circ.x(g.qubits[0])
        elif name == 'Y': circ.y(g.qubits[0])
        elif name == 'Z': circ.z(g.qubits[0])
        elif name == 'S': circ.s(g.qubits[0])
        elif name == 'T': circ.t(g.qubits[0])
        elif name in ('CNOT', 'CX'): circ.cnot(g.qubits[0], g.qubits[1])
        elif name == 'CZ': circ.cz(g.qubits[0], g.qubits[1])
        elif name == 'RZ': circ.rz(g.qubits[0], g.params[0])
        elif name == 'RX': circ.rx(g.qubits[0], g.params[0])
        elif name == 'RY': circ.ry(g.qubits[0], g.params[0])
        elif name == 'SWAP': circ.swap(g.qubits[0], g.qubits[1])

    def _algebraic_optimize(self, circuit: Circuit) -> Circuit:
        """Optimizes {CNOT, RZ} blocks. Only keeps changes if gate count decreases."""
        gates = circuit.gates
        blocks = []
        current_block = []
        is_phase_block = True
        phase_gate_names = {'CNOT', 'CX', 'RZ', 'Z', 'S', 'T'}
        
        for g in gates:
            name = g.name.upper()
            if name in phase_gate_names:
                if not is_phase_block:
                    blocks.append(('other', current_block))
                    current_block = []
                    is_phase_block = True
                current_block.append(g)
            else:
                if is_phase_block and current_block:
                    blocks.append(('phase', current_block))
                    current_block = []
                is_phase_block = False
                current_block.append(g)
        if current_block:
            blocks.append(('phase' if is_phase_block else 'other', current_block))
            
        opt = Circuit(circuit.num_qubits)
        for btype, block in blocks:
            if btype == 'other':
                for g in block: self._add_gate_to_circuit(opt, g)
            else:
                # Try to optimize
                temp_opt = Circuit(circuit.num_qubits)
                self._optimize_phase_block(temp_opt, block, circuit.num_qubits)
                
                # Only use optimized version if it's actually better or equal
                if len(temp_opt.gates) <= len(block):
                    for g in temp_opt.gates: self._add_gate_to_circuit(opt, g)
                else:
                    for g in block: self._add_gate_to_circuit(opt, g)
        return opt

    def _optimize_phase_block(self, opt: Circuit, block: List[Any], n: int):
        # 1. Parity Matrix Extraction
        V = np.eye(n, dtype=int)
        phases = {}
        for g in block:
            name = g.name.upper()
            if name in ('CNOT', 'CX'):
                c, t = g.qubits
                V[t] = (V[t] ^ V[c])
            else:
                q = g.qubits[0]
                if name == 'RZ': angle = g.params[0]
                elif name == 'Z': angle = np.pi
                elif name == 'S': angle = np.pi/2
                elif name == 'T': angle = np.pi/4
                else: continue
                p = tuple(V[q])
                phases[p] = (phases.get(p, 0.0) + angle) % (2 * np.pi)
        
        non_zero_phases = {p: a for p, a in phases.items() if abs(a) > 1e-10 and any(p)}
        
        # 2. Matroid Partitioning
        indep_sets = []
        for v in non_zero_phases:
            placed = False
            for s in indep_sets:
                if self._is_independent(s + [v], n):
                    s.append(v)
                    placed = True
                    break
            if not placed: indep_sets.append([v])
            
        # 3. Synthesis
        C = np.eye(n, dtype=int)
        for s in indep_sets:
            T = self._extend_to_basis(s, n)
            cnots = self._synthesize_linear_transform(C, T, n)
            for c, t in cnots: opt.cnot(c, t)
            C = T.copy()
            for p in s:
                for i in range(n):
                    if tuple(C[i]) == p:
                        opt.rz(i, non_zero_phases[p])
                        break
        
        # 4. Final Basis
        cnots = self._synthesize_linear_transform(C, V, n)
        for c, t in cnots: opt.cnot(c, t)

    def _is_independent(self, vectors, n):
        if len(vectors) > n: return False
        mat = np.array(vectors, dtype=int)
        rank = 0
        for col in range(n):
            if rank >= len(vectors): break
            pivot = -1
            for row in range(rank, len(vectors)):
                if mat[row, col] == 1: pivot = row; break
            if pivot != -1:
                mat[[rank, pivot]] = mat[[pivot, rank]]
                for row in range(len(vectors)):
                    if row != rank and mat[row, col] == 1: mat[row] ^= mat[rank]
                rank += 1
        return rank == len(vectors)

    def _extend_to_basis(self, vectors, n):
        mat = np.zeros((n, n), dtype=int)
        for i, v in enumerate(vectors): mat[i] = v
        rank = len(vectors); basis = list(vectors)
        for i in range(n):
            if rank == n: break
            e = tuple(1 if j == i else 0 for j in range(n))
            if self._is_independent(basis + [e], n):
                mat[rank] = e; basis.append(e); rank += 1
        return mat

    def _synthesize_linear_transform(self, A, B, n):
        curr, target = A.copy(), B.copy()
        def to_id(m):
            ops = []
            for i in range(n):
                if m[i, i] == 0:
                    for j in range(i+1, n):
                        if m[j, i] == 1: ops.append((j, i)); m[i] ^= m[j]; break
                for j in range(i+1, n):
                    if m[j, i] == 1: ops.append((i, j)); m[j] ^= m[i]
            for i in range(n-1, -1, -1):
                for j in range(i):
                    if m[j, i] == 1: ops.append((i, j)); m[j] ^= m[i]
            return ops
        ops_a, ops_b = to_id(curr), to_id(target)
        all_ops = ops_a + list(reversed(ops_b))
        opt_ops = []
        for op in all_ops:
            if opt_ops and opt_ops[-1] == op: opt_ops.pop()
            else: opt_ops.append(op)
        return opt_ops

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)

class _SimpleGate:
    def __init__(self, name, qubits, params):
        self.name = name; self.qubits = qubits; self.params = params
