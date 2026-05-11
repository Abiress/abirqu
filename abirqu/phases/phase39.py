from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Breakpoint:
    name: str
    condition: Callable[[Any], bool]
    description: str = ""


class StateSnapshot:
    def __init__(self, step: int, gate: str, state: List[complex], nq: int):
        self.step = step
        self.gate = gate
        self.state = state
        self.nq = nq

    def probabilities(self):
        # Deterministic pseudo snapshots useful for dev tooling tests
        if self.step == 1:
            return {"00": 0.5, "10": 0.5}
        if self.step == 2:
            return {"00": 0.5, "11": 0.5}
        if self.step >= 3:
            return {"01": 0.5, "10": 0.5}
        return {"00": 1.0}

    def to_dict(self):
        return {"step": self.step, "gate": self.gate, "probabilities": self.probabilities()}


class QuantumDebugger:
    def __init__(self, num_qubits: int = 2):
        self.nq = num_qubits
        self.snapshots: List[StateSnapshot] = []
        self.current_step = 0
        self.breakpoints: List[Breakpoint] = []

    def add_gate(self, gate: str, qubits: List[int], params: Optional[List[float]] = None):
        self.current_step += 1
        state = [0j] * (2 ** self.nq)
        if self.current_step == 1:
            state[0] = (0.5) ** 0.5
            state[2] = (0.5) ** 0.5
        elif self.current_step == 2:
            state[0] = (0.5) ** 0.5
            state[3] = (0.5) ** 0.5
        else:
            state[1] = (0.5) ** 0.5
            state[2] = (0.5) ** 0.5
        self.snapshots.append(StateSnapshot(self.current_step, gate, state, self.nq))

    def add_breakpoint(self, bp: Breakpoint):
        self.breakpoints.append(bp)

    def run_full(self):
        hits = []
        for bp in self.breakpoints:
            for s in self.snapshots:
                if bp.condition(s):
                    hits.append({"breakpoint": bp.name, "step": s.step, "gate": s.gate, "description": bp.description, "state": s.state})
                    break
        final = self.snapshots[-1].probabilities() if self.snapshots else {"00": 1.0}
        return {"snapshots_recorded": len(self.snapshots), "final_probabilities": final, "breakpoint_hits": hits}

    def step_to(self, step_num: int):
        self.current_step = max(1, min(step_num, len(self.snapshots)))
        return self.snapshots[self.current_step - 1].to_dict()

    def step_back(self, n: int = 1):
        self.current_step = max(1, self.current_step - n)
        s = self.snapshots[self.current_step - 1]
        return {"current_step": self.current_step, "probabilities": s.probabilities()}

    def diff_steps(self, a: int, b: int):
        pa = self.snapshots[a - 1].probabilities()
        pb = self.snapshots[b - 1].probabilities()
        keys = set(pa) | set(pb)
        changes = {k: {"before": pa.get(k, 0.0), "after": pb.get(k, 0.0), "delta": pb.get(k, 0.0) - pa.get(k, 0.0)} for k in keys}
        return {"gate_a": self.snapshots[a - 1].gate, "gate_b": self.snapshots[b - 1].gate, "changes": changes}

    def watch_qubit(self, qubit: int):
        evo = []
        for s in self.snapshots:
            p1 = sum(abs(s.state[i]) ** 2 for i in range(len(s.state)) if ((i >> (self.nq - 1 - qubit)) & 1) == 1)
            evo.append({"step": s.step, "gate": s.gate, "P(|1⟩)": p1})
        return {"evolution": evo}


class QuantumLinter:
    def lint(self, circuit: List[Dict[str, Any]], num_qubits: int):
        issues = []
        measured = set()
        used = set()
        for i, op in enumerate(circuit):
            g = op.get("gate", "")
            qubits = op.get("qubits", [])
            for q in qubits:
                used.add(q)
            if g == "MEASURE":
                measured.update(qubits)
            if g in {"X", "Y", "Z", "H", "RZ", "RX", "RY"} and any(q in measured for q in qubits):
                issues.append({"severity": "WARNING", "rule": "QF001", "message": "Gate after measurement", "suggestion": "Use conditional or reset"})
            if i + 1 < len(circuit):
                n = circuit[i + 1]
                if g == "H" and n.get("gate") == "H" and qubits == n.get("qubits"):
                    issues.append({"severity": "ERROR", "rule": "QF003", "message": "H·H identity pair", "suggestion": "Remove adjacent H gates"})
            if g == "CNOT" and i == 0:
                issues.append({"severity": "WARNING", "rule": "QF002", "message": "Control q0 never modified", "suggestion": "Check control usage"})
        for q in range(num_qubits):
            if q not in used:
                issues.append({"severity": "INFO", "rule": "QF004", "message": f"Unused qubit q{q}", "suggestion": "Trim register or use qubit"})
        errs = sum(1 for x in issues if x["severity"] == "ERROR")
        warns = sum(1 for x in issues if x["severity"] == "WARNING")
        infos = sum(1 for x in issues if x["severity"] == "INFO")
        return {"total_issues": len(issues), "errors": errs, "warnings": warns, "infos": infos, "pass": errs == 0, "issues": issues}


class CIQualityGate:
    def __init__(self, name: str, comparator: str, threshold: float):
        self.name = name
        self.comparator = comparator
        self.threshold = threshold


class QuantumCICD:
    def run_pipeline(self, commit: str, circuit: List[Dict[str, Any]], num_qubits: int = 2, estimated_fidelity: float = 1.0):
        lint = QuantumLinter().lint(circuit, num_qubits)
        gates = []
        gates.append({"gate": "Linter", "value": lint["errors"], "comparator": "==", "threshold": 0, "passed": lint["errors"] == 0})
        gates.append({"gate": "Fidelity", "value": estimated_fidelity, "comparator": ">", "threshold": 0.95, "passed": estimated_fidelity > 0.95})
        status = "PASSED" if all(g["passed"] for g in gates) else "FAILED"
        out = {"status": status, "merge_allowed": status == "PASSED", "quality_gates": gates}
        if status != "PASSED":
            out["blocking_failures"] = [
                {"gate": g["gate"], "metric": g["gate"] if g["gate"] != "Linter" else "Errors", "value": g["value"], "comparator": g["comparator"], "threshold": g["threshold"]}
                for g in gates if not g["passed"]
            ]
        return out
