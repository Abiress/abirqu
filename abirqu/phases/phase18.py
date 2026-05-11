from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Sequence

from ..circuit import Circuit
from ..numpy_sim import NumPySimulator


class InteractiveQuantumCourse:
    def __init__(self) -> None:
        self.modules = [{"id": i + 1, "title": f"Module {i + 1}", "difficulty": "beginner" if i < 3 else "intermediate" if i < 7 else "advanced"} for i in range(10)]

    def list_modules(self) -> List[Dict[str, Any]]:
        return list(self.modules)

    def grade_quiz(self, answers: Sequence[str], key: Sequence[str]) -> Dict[str, Any]:
        correct = sum(1 for a, k in zip(answers, key) if a == k)
        return {"score": correct, "total": len(key), "passed": correct >= int(0.7 * max(1, len(key)))}


class QuantumAlgorithmPlayground:
    def step_execute(self, circuit: Circuit) -> List[Dict[str, Any]]:
        steps = []
        for i in range(len(circuit.gates) + 1):
            partial = circuit.slice(0, i)
            probs = NumPySimulator(circuit.num_qubits).run_circuit(partial)
            steps.append({"step": i, "gates": i, "probabilities": probs})
        return steps

    def compare_classical_quantum(self, quantum_cost: float, classical_cost: float) -> Dict[str, Any]:
        return {"quantum_cost": quantum_cost, "classical_cost": classical_cost, "speedup": classical_cost / max(1e-9, quantum_cost)}


class QuantumCodingChallenges:
    def __init__(self) -> None:
        self._challenges: Dict[str, Callable[[Any], bool]] = {}

    def add_challenge(self, name: str, checker: Callable[[Any], bool]) -> None:
        self._challenges[name] = checker

    def verify(self, name: str, solution: Any) -> Dict[str, Any]:
        if name not in self._challenges:
            return {"exists": False, "passed": False}
        ok = bool(self._challenges[name](solution))
        return {"exists": True, "passed": ok}


class AbirQuCertificationProgram:
    LEVELS = ["Associate", "Professional", "Expert", "Architect"]

    def evaluate_exam(self, points: int, max_points: int) -> Dict[str, Any]:
        pct = 100.0 * points / max(1, max_points)
        if pct >= 90:
            level = self.LEVELS[3]
        elif pct >= 80:
            level = self.LEVELS[2]
        elif pct >= 70:
            level = self.LEVELS[1]
        else:
            level = self.LEVELS[0]
        return {"score_pct": pct, "level": level, "certified": pct >= 70}


class ResearchPaperReproductionTool:
    def reproduce(self, paper_id: str, runner: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        result = runner()
        return {"paper_id": paper_id, "result": result, "reproducibility_score": 1.0 if result.get("success", False) else 0.0}

    def regenerate_tables(self, rows: Sequence[Dict[str, Any]], columns: Sequence[str]) -> List[Dict[str, Any]]:
        return [{k: row.get(k) for k in columns} for row in rows]

    def parameter_exploration(self, fn: Callable[[float], float], values: Sequence[float]) -> Dict[str, Any]:
        out = [{"x": v, "y": fn(v)} for v in values]
        return {"samples": out, "best": min(out, key=lambda r: r["y"]) if out else None}
