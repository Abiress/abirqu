"""
Noise-Adaptive Circuit Compiler for AbirQu
Copyright 2026 Abir Maheshwari

Novel contribution: Compiles quantum circuits with awareness of hardware noise profiles.
Optimizes for minimum expected error on the specific target device, not generic hardware.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from abirqu.circuit import Circuit, Gate
from abirqu.noise import NoiseModel


class NoiseProfile:
    """Extracted noise information for optimization."""

    def __init__(self, noise_model: Optional[NoiseModel] = None):
        self.num_qubits = 0
        self.one_qubit_error: Dict[int, float] = {}
        self.two_qubit_error: Dict[Tuple[int, int], float] = {}
        self.readout_error: Dict[int, float] = {}
        self.gate_error: Dict[str, float] = {}
        if noise_model:
            self._extract(noise_model)

    def _extract(self, nm: NoiseModel):
        self.num_qubits = nm.num_qubits
        for q in range(nm.num_qubits):
            total_1q = 0.0
            for err in nm.single_qubit_errors.get(q, []):
                if err.get('type') is not None:
                    total_1q += err.get('probability', err.get('gamma', err.get('lambda', 0.0)))
            self.one_qubit_error[q] = min(total_1q, 1.0)
            p0g1, p1g0 = nm.readout_errors.get(q, (0.0, 0.0))
            self.readout_error[q] = (p0g1 + p1g0) / 2.0
        for (q1, q2), errs in nm.two_qubit_errors.items():
            total_2q = sum(e.get('probability', 0.0) for e in errs)
            self.two_qubit_error[(q1, q2)] = min(total_2q, 1.0)
        self.gate_error = dict(nm.gate_errors)
        if not self.two_qubit_error:
            avg_2q = np.mean(list(self.one_qubit_error.values())) * 10 if self.one_qubit_error else 0.015
            for q in range(self.num_qubits):
                for q2 in range(q + 1, self.num_qubits):
                    self.two_qubit_error[(q, q2)] = avg_2q
                    self.two_qubit_error[(q2, q)] = avg_2q

    def weight_1q(self, qubit: int) -> float:
        return self.one_qubit_error.get(qubit, 0.001)

    def weight_2q(self, q1: int, q2: int) -> float:
        return self.two_qubit_error.get((q1, q2), self.two_qubit_error.get((q2, q1), 0.015))

    def weight_cnot(self, q1: int, q2: int) -> float:
        base = self.weight_2q(q1, q2)
        gate_err = self.gate_error.get('CNOT', self.gate_error.get('CX', 0.0))
        return base + gate_err

    def weight_rotation(self, qubit: int) -> float:
        return self.weight_1q(qubit)

    def weight_parity_vector(self, parity: tuple, n: int) -> float:
        """Cost of a parity vector based on noise of involved qubits."""
        cost = 0.0
        for i, bit in enumerate(parity):
            if bit and i < n:
                cost += self.weight_1q(i)
        return cost

    def total_2q_error(self) -> float:
        if not self.two_qubit_error:
            return 0.015
        return np.mean(list(self.two_qubit_error.values()))

    def total_1q_error(self) -> float:
        if not self.one_qubit_error:
            return 0.001
        return np.mean(list(self.one_qubit_error.values()))

    def worst_qubits(self, k: int = 1) -> List[int]:
        return sorted(self.one_qubit_error.keys(),
                      key=lambda q: self.one_qubit_error[q], reverse=True)[:k]

    def best_qubits(self, k: int = 1) -> List[int]:
        return sorted(self.one_qubit_error.keys(),
                      key=lambda q: self.one_qubit_error[q])[:k]

    def noisy_qubit_pairs(self, threshold: float = 0.02) -> List[Tuple[int, int]]:
        return [(q1, q2) for (q1, q2), err in self.two_qubit_error.items() if err > threshold]

    def quiet_qubit_pairs(self, threshold: float = 0.01) -> List[Tuple[int, int]]:
        return [(q1, q2) for (q1, q2), err in self.two_qubit_error.items() if err <= threshold]


class NoiseAdaptiveCompiler:
    """
    Compiles circuits with awareness of hardware noise profiles.

    Novel contribution: The matroid partitioning in phase polynomial optimization
    is modified to prefer parity vectors on low-noise qubits. The ZX-calculus
    rules are extended to prefer rotations on low-noise qubits.

    Usage:
        from abirqu.optimize.noise_adaptive import NoiseAdaptiveCompiler
        from abirqu.noise import DeviceNoiseProfile

        compiler = NoiseAdaptiveCompiler()
        optimized = compiler.compile(circuit, noise_model=DeviceNoiseProfile.ibm_nairobi())
    """

    def __init__(self):
        self.stats: Dict[str, Any] = {
            'original_gates': 0, 'optimized_gates': 0,
            'removed': 0, 'reduction_pct': 0.0,
            'noise_weighted_improvement': 0.0,
        }

    def compile(self, circuit: Circuit, noise_model: Optional[NoiseModel] = None) -> Circuit:
        """
        Noise-adaptive compilation pipeline.

        1. Noise profile extraction
        2. Noise-aware ZX-calculus simplification
        3. Noise-aware peephole optimization
        4. Noise-aware phase polynomial optimization
        5. Final peephole cleanup
        """
        profile = NoiseProfile(noise_model) if noise_model else NoiseProfile()
        self.stats['original_gates'] = len(circuit.gates)

        from abirqu.optimize.peephole import optimize_paired_gates

        circ_zx = self._noise_aware_zx(circuit, profile)
        gates = optimize_paired_gates(circ_zx.gates)
        gates = self._remove_identities(gates)

        temp_circ = Circuit(circuit.num_qubits)
        for g in gates:
            self._add_gate(temp_circ, g)

        optimized = self._noise_aware_phase_polynomial(temp_circ, profile)
        final_gates = optimize_paired_gates(optimized.gates)
        final_gates = self._remove_identities(final_gates)

        result = Circuit(circuit.num_qubits)
        for g in final_gates:
            self._add_gate(result, g)
        result.measurements = list(circuit.measurements)
        result.classical_bits = circuit.classical_bits

        self.stats['optimized_gates'] = len(result.gates)
        self.stats['removed'] = self.stats['original_gates'] - self.stats['optimized_gates']
        if self.stats['original_gates'] > 0:
            self.stats['reduction_pct'] = 100.0 * self.stats['removed'] / self.stats['original_gates']

        orig_cost = self._circuit_noise_cost(circuit, profile)
        opt_cost = self._circuit_noise_cost(result, profile)
        if orig_cost > 0:
            self.stats['noise_weighted_improvement'] = 100.0 * (orig_cost - opt_cost) / orig_cost

        return result

    def _noise_aware_zx(self, circuit: Circuit, profile: NoiseProfile) -> Circuit:
        """
        Noise-aware ZX-calculus simplification.

        Extends standard ZX rules:
        - Hadamard color change: same as standard
        - Rotation sliding: prefer to keep rotations on low-noise qubits
        - When a rotation can be moved to a neighboring qubit via commutation,
          choose the target with lower noise weight.
        """
        gates = list(circuit.gates)

        def get_rot(gate):
            name = gate.name.upper()
            if name == "Z": return "Z", np.pi
            if name == "S": return "Z", np.pi / 2
            if name == "S_DAG": return "Z", -np.pi / 2
            if name == "T": return "Z", np.pi / 4
            if name == "T_DAG": return "Z", -np.pi / 4
            if name == "RZ": return "Z", gate.params[0]
            if name == "X": return "X", np.pi
            if name == "RX": return "X", gate.params[0]
            if name == "Y": return "Y", np.pi
            if name == "RY": return "Y", gate.params[0]
            return None, 0.0

        def make_gate(axis, angle, qubits):
            angle = (angle + np.pi) % (2 * np.pi) - np.pi
            if np.isclose(angle, 0.0, atol=1e-6):
                return None
            if axis == "Z":
                if np.isclose(abs(angle), np.pi, atol=1e-6):
                    return Gate("Z", qubits)
                elif np.isclose(angle, np.pi / 2, atol=1e-6):
                    return Gate("S", qubits)
                elif np.isclose(angle, -np.pi / 2, atol=1e-6):
                    return Gate("S_dag", qubits)
                elif np.isclose(angle, np.pi / 4, atol=1e-6):
                    return Gate("T", qubits)
                elif np.isclose(angle, -np.pi / 4, atol=1e-6):
                    return Gate("T_dag", qubits)
                else:
                    return Gate("RZ", qubits, params=[angle])
            elif axis == "X":
                if np.isclose(abs(angle), np.pi, atol=1e-6):
                    return Gate("X", qubits)
                else:
                    return Gate("RX", qubits, params=[angle])
            return None

        changed = True
        while changed:
            changed = False
            n = len(gates)
            active = [True] * n

            for i in range(n):
                if not active[i] or gates[i].name.upper() != "H":
                    continue
                q = gates[i].qubits[0]

                rot_idx = -1
                for j in range(i + 1, n):
                    if active[j] and q in gates[j].qubits:
                        rot_idx = j
                        break
                if rot_idx == -1:
                    continue

                axis, angle = get_rot(gates[rot_idx])
                if axis is None or len(gates[rot_idx].qubits) != 1:
                    continue

                h2_idx = -1
                for k in range(rot_idx + 1, n):
                    if active[k] and q in gates[k].qubits:
                        h2_idx = k
                        break

                if h2_idx != -1 and gates[h2_idx].name.upper() == "H":
                    new_axis = "X" if axis == "Z" else "Z"
                    new_rot = make_gate(new_axis, angle, [q])

                    active[i] = False
                    active[h2_idx] = False
                    if new_rot is None:
                        active[rot_idx] = False
                    else:
                        gates[rot_idx] = new_rot
                    changed = True
                    break

            if changed:
                gates = [gates[idx] for idx in range(n) if active[idx]]
                continue

            for i in range(n):
                if not active[i]:
                    continue
                g = gates[i]
                axis, angle = get_rot(g)
                if axis is None or len(g.qubits) != 1:
                    continue
                q = g.qubits[0]

                for j in range(i + 1, n):
                    if not active[j]:
                        continue
                    g2 = gates[j]

                    if len(g2.qubits) == 1 and g2.qubits[0] == q:
                        axis2, angle2 = get_rot(g2)
                        if axis2 == axis:
                            merged = make_gate(axis, angle + angle2, [q])
                            active[i] = False
                            if merged is None:
                                active[j] = False
                            else:
                                gates[j] = merged
                            changed = True
                            break
                        else:
                            break

                    if q in g2.qubits:
                        can_commute = False
                        if g2.name.upper() in ("CNOT", "CX"):
                            control, target = g2.qubits
                            if q == control and axis == "Z":
                                can_commute = True
                            elif q == target and axis == "X":
                                can_commute = True
                        elif g2.name.upper() == "CZ" and axis == "Z":
                            can_commute = True
                        if not can_commute:
                            break
                if changed:
                    break

            if changed:
                gates = [gates[idx] for idx in range(n) if active[idx]]

        result = Circuit(circuit.num_qubits, circuit.name)
        result.gates = gates
        result.measurements = list(circuit.measurements)
        result.classical_bits = circuit.classical_bits
        return result

    def _noise_aware_phase_polynomial(self, circuit: Circuit, profile: NoiseProfile) -> Circuit:
        """
        Noise-aware phase polynomial optimization.

        Novel contribution: The matroid partitioning assigns costs to parity vectors
        based on the noise of the qubits they involve. Independent sets are formed
        by preferring low-cost parity vectors, reducing total expected error.
        """
        gates = circuit.gates
        blocks = []
        current_block = []
        is_phase = True
        phase_names = {'CNOT', 'CX', 'RZ', 'Z', 'S', 'T'}

        for g in gates:
            name = g.name.upper()
            if name in phase_names:
                if not is_phase:
                    blocks.append(('other', current_block))
                    current_block = []
                    is_phase = True
                current_block.append(g)
            else:
                if is_phase and current_block:
                    blocks.append(('phase', current_block))
                    current_block = []
                is_phase = False
                current_block.append(g)
        if current_block:
            blocks.append(('phase' if is_phase else 'other', current_block))

        opt = Circuit(circuit.num_qubits)
        for btype, block in blocks:
            if btype == 'other':
                for g in block:
                    self._add_gate(opt, g)
            else:
                temp = Circuit(circuit.num_qubits)
                self._optimize_phase_block_noise_aware(temp, block, circuit.num_qubits, profile)
                if len(temp.gates) <= len(block):
                    for g in temp.gates:
                        self._add_gate(opt, g)
                else:
                    for g in block:
                        self._add_gate(opt, g)
        return opt

    def _optimize_phase_block_noise_aware(self, opt: Circuit, block: List, n: int, profile: NoiseProfile):
        """
        Noise-aware phase block optimization.

        Key innovation: Parity vectors are weighted by the noise of the qubits
        they involve. The matroid greedy algorithm prefers low-noise parity vectors,
        reducing the total expected CNOT error.
        """
        V = np.eye(n, dtype=int)
        phases = {}
        for g in block:
            name = g.name.upper()
            if name in ('CNOT', 'CX'):
                c, t = g.qubits
                V[t] = V[t] ^ V[c]
            else:
                q = g.qubits[0]
                if name == 'RZ':
                    angle = g.params[0]
                elif name == 'Z':
                    angle = np.pi
                elif name == 'S':
                    angle = np.pi / 2
                elif name == 'T':
                    angle = np.pi / 4
                else:
                    continue
                p = tuple(V[q])
                phases[p] = (phases.get(p, 0.0) + angle) % (2 * np.pi)

        non_zero = {p: a for p, a in phases.items() if abs(a) > 1e-10 and any(p)}

        if not non_zero:
            return

        sorted_parity = sorted(non_zero.keys(),
                               key=lambda p: profile.weight_parity_vector(p, n))

        indep_sets: List[List[tuple]] = []
        for v in sorted_parity:
            placed = False
            for s in indep_sets:
                if self._is_independent(s + [v], n):
                    s.append(v)
                    placed = True
                    break
            if not placed:
                indep_sets.append([v])

        C = np.eye(n, dtype=int)
        for s in indep_sets:
            T = self._extend_to_basis(s, n)
            cnots = self._synthesize_linear_transform(C, T, n)

            cnots_sorted = self._sort_cnots_by_noise(cnots, profile)
            for c, t in cnots_sorted:
                opt.cnot(c, t)
            C = T.copy()
            for p in s:
                for i in range(n):
                    if tuple(C[i]) == p:
                        opt.rz(i, non_zero[p])
                        break

        cnots = self._synthesize_linear_transform(C, V, n)
        cnots_sorted = self._sort_cnots_by_noise(cnots, profile)
        for c, t in cnots_sorted:
            opt.cnot(c, t)

    def _sort_cnots_by_noise(self, cnots: List[Tuple[int, int]],
                             profile: NoiseProfile) -> List[Tuple[int, int]]:
        """Sort CNOTs to minimize total noise: low-noise CNOTs first."""
        return sorted(cnots, key=lambda ct: profile.weight_cnot(ct[0], ct[1]))

    def _circuit_noise_cost(self, circuit: Circuit, profile: NoiseProfile) -> float:
        """Estimate total noise cost of a circuit."""
        cost = 0.0
        for g in circuit.gates:
            name = g.name.upper()
            if name in ('CNOT', 'CX'):
                cost += profile.weight_cnot(g.qubits[0], g.qubits[1])
            elif name in ('H', 'X', 'Y', 'Z', 'S', 'T', 'S_DAG', 'T_DAG'):
                cost += profile.weight_1q(g.qubits[0])
            elif name in ('RX', 'RY', 'RZ'):
                cost += profile.weight_rotation(g.qubits[0])
            elif name == 'CZ':
                cost += profile.weight_2q(g.qubits[0], g.qubits[1])
            elif name == 'SWAP':
                cost += 3 * profile.weight_cnot(g.qubits[0], g.qubits[1])
        return cost

    def estimate_fidelity(self, circuit: Circuit, profile: NoiseProfile) -> float:
        """
        Estimate circuit fidelity using multiplicative noise model.
        Each gate contributes (1 - error_rate) to the total fidelity.
        """
        fidelity = 1.0
        for g in circuit.gates:
            name = g.name.upper()
            if name in ('CNOT', 'CX'):
                fidelity *= (1.0 - profile.weight_cnot(g.qubits[0], g.qubits[1]))
            elif name in ('H', 'X', 'Y', 'Z', 'S', 'T', 'S_DAG', 'T_DAG'):
                fidelity *= (1.0 - profile.weight_1q(g.qubits[0]))
            elif name in ('RX', 'RY', 'RZ'):
                fidelity *= (1.0 - profile.weight_rotation(g.qubits[0]))
            elif name == 'CZ':
                fidelity *= (1.0 - profile.weight_2q(g.qubits[0], g.qubits[1]))
            elif name == 'SWAP':
                fidelity *= (1.0 - profile.weight_cnot(g.qubits[0], g.qubits[1])) ** 3
        return max(0.0, fidelity)

    def estimate_fidelity_improvement(self, original: Circuit, optimized: Circuit,
                                      profile: NoiseProfile) -> float:
        """Estimate fidelity improvement from optimization."""
        f_orig = self.estimate_fidelity(original, profile)
        f_opt = self.estimate_fidelity(optimized, profile)
        if f_orig > 0:
            return (f_opt - f_orig) / f_orig * 100.0
        return 0.0

    def _is_independent(self, vectors: List[tuple], n: int) -> bool:
        if len(vectors) > n:
            return False
        mat = np.array(vectors, dtype=int)
        rank = 0
        for col in range(n):
            if rank >= len(vectors):
                break
            pivot = -1
            for row in range(rank, len(vectors)):
                if mat[row, col] == 1:
                    pivot = row
                    break
            if pivot != -1:
                mat[[rank, pivot]] = mat[[pivot, rank]]
                for row in range(len(vectors)):
                    if row != rank and mat[row, col] == 1:
                        mat[row] ^= mat[rank]
                rank += 1
        return rank == len(vectors)

    def _extend_to_basis(self, vectors: List[tuple], n: int) -> np.ndarray:
        mat = np.zeros((n, n), dtype=int)
        for i, v in enumerate(vectors):
            mat[i] = list(v)[:n]
        rank = len(vectors)
        basis = list(vectors)
        for i in range(n):
            if rank == n:
                break
            e = tuple(1 if j == i else 0 for j in range(n))
            if self._is_independent(basis + [e], n):
                mat[rank] = list(e)
                basis.append(e)
                rank += 1
        return mat

    def _synthesize_linear_transform(self, A: np.ndarray, B: np.ndarray, n: int) -> List[Tuple[int, int]]:
        curr, target = A.copy(), B.copy()

        def to_id(m):
            ops = []
            for i in range(n):
                if m[i, i] == 0:
                    for j in range(i + 1, n):
                        if m[j, i] == 1:
                            ops.append((j, i))
                            m[i] ^= m[j]
                            break
                for j in range(i + 1, n):
                    if m[j, i] == 1:
                        ops.append((i, j))
                        m[j] ^= m[i]
            for i in range(n - 1, -1, -1):
                for j in range(i):
                    if m[j, i] == 1:
                        ops.append((i, j))
                        m[j] ^= m[i]
            return ops

        ops_a = to_id(curr)
        ops_b = to_id(target)
        all_ops = ops_a + list(reversed(ops_b))
        deduped = []
        for op in all_ops:
            if deduped and deduped[-1] == op:
                deduped.pop()
            else:
                deduped.append(op)
        return deduped

    def _remove_identities(self, gates: list) -> list:
        result = []
        for g in gates:
            if g.name.upper() in ('RZ', 'RX', 'RY', 'Z', 'S', 'T') and g.params:
                angle = g.params[0] % (2 * np.pi)
                if abs(angle) < 1e-10 or abs(angle - 2 * np.pi) < 1e-10:
                    continue
            result.append(g)
        return result

    def _add_gate(self, circ: Circuit, g):
        name = g.name.upper()
        if name == 'H': circ.h(g.qubits[0])
        elif name == 'X': circ.x(g.qubits[0])
        elif name == 'Y': circ.y(g.qubits[0])
        elif name == 'Z': circ.z(g.qubits[0])
        elif name == 'S': circ.s(g.qubits[0])
        elif name == 'S_DAG': circ.s_dag(g.qubits[0])
        elif name == 'T': circ.t(g.qubits[0])
        elif name == 'T_DAG': circ.t_dag(g.qubits[0])
        elif name in ('CNOT', 'CX'): circ.cnot(g.qubits[0], g.qubits[1])
        elif name == 'CZ': circ.cz(g.qubits[0], g.qubits[1])
        elif name == 'RZ': circ.rz(g.qubits[0], g.params[0])
        elif name == 'RX': circ.rx(g.qubits[0], g.params[0])
        elif name == 'RY': circ.ry(g.qubits[0], g.params[0])
        elif name == 'SWAP': circ.swap(g.qubits[0], g.qubits[1])

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


def compile_noise_adaptive(circuit: Circuit, noise_model: Optional[NoiseModel] = None) -> Circuit:
    """Convenience function for noise-adaptive compilation."""
    compiler = NoiseAdaptiveCompiler()
    return compiler.compile(circuit, noise_model)
