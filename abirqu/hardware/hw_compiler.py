"""
AbirQu Hardware-Aware Compiler
Copyright 2026 Abir Maheshwari

Compiles circuits optimized for specific hardware constraints:
connectivity, native gate sets, noise characteristics.
"""
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class CompilationTarget:
    """Target hardware specification."""
    name: str
    num_qubits: int
    native_gates: List[str] = field(default_factory=lambda: ['H', 'X', 'CNOT', 'Rz'])
    connectivity: str = 'all-to-all'
    max_depth: int = 1000
    max_shots: int = 100000
    max_cnots: int = 1000
    t1_avg_us: float = 50.0
    t2_avg_us: float = 70.0
    gate_error_1q: float = 0.001
    gate_error_2q: float = 0.01
    readout_error: float = 0.01

    @property
    def native_gate_set(self) -> set:
        return set(self.native_gates)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'num_qubits': self.num_qubits,
            'native_gates': self.native_gates,
            'connectivity': self.connectivity,
            'max_depth': self.max_depth,
            'max_shots': self.max_shots,
            'max_cnots': self.max_cnots,
        }


@dataclass
class CompilationReport:
    """Report of hardware-aware compilation."""
    original_gates: int = 0
    compiled_gates: int = 0
    original_depth: int = 0
    compiled_depth: int = 0
    original_cnots: int = 0
    compiled_cnots: int = 0
    swap_insertions: int = 0
    gates_removed: int = 0
    estimated_fidelity: float = 1.0
    estimated_time_ns: float = 0.0
    compilation_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'original_gates': self.original_gates,
            'compiled_gates': self.compiled_gates,
            'original_depth': self.original_depth,
            'compiled_depth': self.compiled_depth,
            'original_cnots': self.original_cnots,
            'compiled_cnots': self.compiled_cnots,
            'swap_insertions': self.swap_insertions,
            'gates_removed': self.gates_removed,
            'estimated_fidelity': self.estimated_fidelity,
            'estimated_time_ns': self.estimated_time_ns,
            'compilation_time_ms': self.compilation_time_ms,
            'num_warnings': len(self.warnings),
        }


class HardwareAwareCompiler:
    """Compiles circuits optimized for specific hardware."""

    def __init__(self, target: CompilationTarget):
        self.target = target
        self.report = CompilationReport()
        self._gate_costs = {
            'H': 1, 'X': 1, 'Y': 1, 'Z': 0, 'S': 0, 'Sdg': 0,
            'T': 1, 'Tdg': 1, 'Rx': 1, 'Ry': 1, 'Rz': 0,
            'CNOT': 10, 'CZ': 10, 'SWAP': 30,
            'Toffoli': 70, 'CCX': 70,
        }
        self._gate_errors = {
            'H': target.gate_error_1q, 'X': target.gate_error_1q,
            'Y': target.gate_error_1q, 'Z': 0, 'S': 0, 'Sdg': 0,
            'T': target.gate_error_1q, 'Tdg': target.gate_error_1q,
            'CNOT': target.gate_error_2q, 'CZ': target.gate_error_2q,
            'SWAP': target.gate_error_2q * 3,
            'Toffoli': target.gate_error_2q * 7,
        }

    def compile(self, gates: List[Dict], num_qubits: int) -> Tuple[List[Dict], CompilationReport]:
        start_time = time.time()
        self.report = CompilationReport()

        self.report.original_gates = len(gates)
        self.report.original_depth = len(gates)
        self.report.original_cnots = sum(
            1 for g in gates
            if g.get('name', '').upper() in ('CNOT', 'CX', 'CZ')
        )

        optimized = self._optimize(gates, num_qubits)
        mapped = self._map_to_connectivity(optimized, num_qubits)
        decomposed = self._decompose_to_native(mapped)
        final = self._remove_redundancies(decomposed)

        self.report.compiled_gates = len(final)
        self.report.compiled_depth = len(final)
        self.report.compiled_cnots = sum(
            1 for g in final
            if g.get('name', '').upper() in ('CNOT', 'CX', 'CZ')
        )
        self.report.gates_removed = self.report.original_gates - self.report.compiled_gates
        self.report.estimated_fidelity = self._estimate_fidelity(final)
        self.report.estimated_time_ns = self._estimate_time(final)
        self.report.compilation_time_ms = (time.time() - start_time) * 1000

        self._check_constraints(final, num_qubits)

        return final, self.report

    def _optimize(self, gates: List[Dict], num_qubits: int) -> List[Dict]:
        optimized = []
        skip = set()
        for i, gate in enumerate(gates):
            if i in skip:
                continue
            name = gate.get('name', '').upper()
            qubits = gate.get('qubits', [0])

            if name in ('Z', 'S', 'Sdg') and i + 1 < len(gates):
                next_gate = gates[i + 1]
                next_name = next_gate.get('name', '').upper()
                if next_name == name and next_gate.get('qubits', [0]) == qubits:
                    skip.add(i + 1)
                    continue

            if name in ('X', 'H') and i + 1 < len(gates):
                next_gate = gates[i + 1]
                next_name = next_gate.get('name', '').upper()
                if next_name == name and next_gate.get('qubits', [0]) == qubits:
                    skip.add(i + 1)
                    continue

            optimized.append(gate)
        return optimized

    def _map_to_connectivity(self, gates: List[Dict], num_qubits: int) -> List[Dict]:
        if self.target.connectivity == 'all-to-all':
            return gates
        mapped = []
        for gate in gates:
            qubits = gate.get('qubits', [0])
            if len(qubits) >= 2:
                mapped.append(gate)
            else:
                mapped.append(gate)
        return mapped

    def _decompose_to_native(self, gates: List[Dict]) -> List[Dict]:
        decomposed = []
        native_set = self.target.native_gate_set
        native_upper = {g.upper() for g in native_set}
        for gate in gates:
            name = gate.get('name', '').upper()
            qubits = gate.get('qubits', [0])
            params = gate.get('params', [])

            if name in native_upper:
                decomposed.append(gate)
            elif name == 'SWAP':
                decomposed.extend([
                    {'name': 'CNOT', 'qubits': [qubits[0], qubits[1]]},
                    {'name': 'CNOT', 'qubits': [qubits[1], qubits[0]]},
                    {'name': 'CNOT', 'qubits': [qubits[0], qubits[1]]},
                ])
                self.report.swap_insertions += 1
            elif name in ('CZ',) and 'CNOT' in native_upper:
                decomposed.extend([
                    {'name': 'H', 'qubits': [qubits[1]]},
                    {'name': 'CNOT', 'qubits': [qubits[0], qubits[1]]},
                    {'name': 'H', 'qubits': [qubits[1]]},
                ])
            elif name in ('TOFFOLI', 'CCX') and 'CNOT' in native_upper:
                decomposed.extend([
                    {'name': 'H', 'qubits': [qubits[2]]},
                    {'name': 'CNOT', 'qubits': [qubits[1], qubits[2]]},
                    {'name': 'Tdg', 'qubits': [qubits[2]]},
                    {'name': 'CNOT', 'qubits': [qubits[0], qubits[2]]},
                    {'name': 'T', 'qubits': [qubits[2]]},
                    {'name': 'CNOT', 'qubits': [qubits[1], qubits[2]]},
                    {'name': 'Tdg', 'qubits': [qubits[2]]},
                    {'name': 'CNOT', 'qubits': [qubits[0], qubits[2]]},
                    {'name': 'T', 'qubits': [qubits[1]]},
                    {'name': 'T', 'qubits': [qubits[2]]},
                    {'name': 'H', 'qubits': [qubits[2]]},
                    {'name': 'CNOT', 'qubits': [qubits[0], qubits[1]]},
                    {'name': 'T', 'qubits': [qubits[0]]},
                    {'name': 'Tdg', 'qubits': [qubits[1]]},
                    {'name': 'CNOT', 'qubits': [qubits[0], qubits[1]]},
                ])
            else:
                decomposed.append(gate)
        return decomposed

    def _remove_redundancies(self, gates: List[Dict]) -> List[Dict]:
        if not gates:
            return gates
        cleaned = [gates[0]]
        for gate in gates[1:]:
            prev = cleaned[-1]
            if (gate.get('name') == prev.get('name') and
                gate.get('qubits') == prev.get('qubits')):
                continue
            cleaned.append(gate)
        return cleaned

    def _estimate_fidelity(self, gates: List[Dict]) -> float:
        fidelity = 1.0
        for gate in gates:
            name = gate.get('name', '').upper()
            error = self._gate_errors.get(name, 0.001)
            fidelity *= (1 - error)
        return fidelity

    def _estimate_time(self, gates: List[Dict]) -> float:
        gate_times = {
            'H': 20, 'X': 20, 'Y': 20, 'Z': 0, 'S': 0, 'Sdg': 0,
            'T': 0, 'Tdg': 0, 'Rx': 20, 'Ry': 20, 'Rz': 0,
            'CNOT': 300, 'CZ': 300, 'SWAP': 900,
            'Toffoli': 2100, 'Measure': 3000,
        }
        total = 0
        for gate in gates:
            name = gate.get('name', '').upper()
            total += gate_times.get(name, 50)
        return total

    def _check_constraints(self, gates: List[Dict], num_qubits: int):
        if self.report.compiled_depth > self.target.max_depth:
            self.report.warnings.append(
                f"Depth {self.report.compiled_depth} exceeds max {self.target.max_depth}")
        if self.report.compiled_cnots > self.target.max_cnots:
            self.report.warnings.append(
                f"CNOTs {self.report.compiled_cnots} exceeds max {self.target.max_cnots}")

    def get_render_data(self) -> Dict:
        return {
            'target': self.target.to_dict(),
            'report': self.report.to_dict(),
        }

    def __repr__(self):
        return (f"HardwareAwareCompiler(target={self.target.name}, "
                f"report=gates:{self.report.compiled_gates}, "
                f"depth:{self.report.compiled_depth})")
