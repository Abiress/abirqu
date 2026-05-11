import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from ..circuit import Circuit


@dataclass
class TemplateSpec:
    name: str
    version: str
    description: str


class CircuitTemplateLibrary:
    def __init__(self) -> None:
        self.templates: Dict[str, Callable[..., Circuit]] = {}

    def register(self, name: str, builder: Callable[..., Circuit]) -> None:
        self.templates[name] = builder

    def build(self, name: str, *args, **kwargs) -> Circuit:
        if name not in self.templates:
            raise KeyError(f"Unknown template: {name}")
        return self.templates[name](*args, **kwargs)


class CircuitArtifactStore:
    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def save(self, name: str, circuit: Circuit, tags: List[str]) -> str:
        payload = circuit.to_json()
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self._store[digest] = {"name": name, "payload": payload, "tags": list(tags)}
        return digest

    def load(self, digest: str) -> Circuit:
        if digest not in self._store:
            raise KeyError("artifact not found")
        return Circuit.from_json(self._store[digest]["payload"])


class CircuitValidator:
    def validate(self, circuit: Circuit) -> Dict[str, Any]:
        errors = []
        for i, g in enumerate(circuit.gates):
            if any(q < 0 or q >= circuit.num_qubits for q in g.qubits):
                errors.append({"index": i, "issue": "invalid qubit index"})
        return {"valid": len(errors) == 0, "errors": errors, "gate_count": len(circuit.gates)}


class CircuitTemplateEngine:
    def bell(self) -> Circuit:
        c = Circuit(2)
        c.h(0).cnot(0, 1)
        return c

    def ghz(self, qubits: int) -> Circuit:
        c = Circuit(qubits)
        c.h(0)
        for q in range(1, qubits):
            c.cnot(0, q)
        return c
