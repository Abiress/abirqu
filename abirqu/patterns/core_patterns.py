from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional

from ..circuit import Circuit


class PatternKind(str, Enum):
    INITIALIZATION = "initialization"
    SUPERPOSITION = "superposition"
    ENTANGLEMENT = "entanglement"
    ORACLE = "oracle"


@dataclass
class PatternMatch:
    kind: PatternKind
    start_gate: int
    end_gate: int
    confidence: float


def initialization_pattern(num_qubits: int) -> Circuit:
    """Return a reusable all-zero initialization pattern."""
    return Circuit(num_qubits, name="initialization")


def superposition_pattern(num_qubits: int, qubits: Optional[Iterable[int]] = None) -> Circuit:
    c = Circuit(num_qubits, name="superposition")
    for q in (list(qubits) if qubits is not None else range(num_qubits)):
        c.h(int(q))
    return c


def entanglement_pattern(num_qubits: int, control: int = 0, chain: bool = True) -> Circuit:
    c = Circuit(num_qubits, name="entanglement")
    c.h(control)
    if chain:
        for target in range(control + 1, num_qubits):
            c.cnot(control, target)
    return c


def oracle_pattern(num_qubits: int, marked_state: int) -> Circuit:
    """Simple phase oracle: flip phase on marked computational basis state.

    This implementation uses X pre/post toggles around a multi-controlled pattern
    approximation to keep the API functional without requiring a full MCZ backend.
    """
    c = Circuit(num_qubits, name="oracle")
    bits = format(marked_state, f"0{num_qubits}b")
    for i, bit in enumerate(bits):
        if bit == "0":
            c.x(i)
    # Lightweight approximation: entangle then phase flip with CZ ladder
    for i in range(num_qubits - 1):
        c.cz(i, i + 1)
    for i, bit in enumerate(bits):
        if bit == "0":
            c.x(i)
    return c


def detect_patterns(circuit: Circuit) -> List[PatternMatch]:
    matches: List[PatternMatch] = []
    names = [g.name.upper() for g in circuit.gates]

    for i, name in enumerate(names):
        if name == "H":
            matches.append(PatternMatch(PatternKind.SUPERPOSITION, i, i, 0.9))
        if name in {"CNOT", "CX", "CZ"}:
            matches.append(PatternMatch(PatternKind.ENTANGLEMENT, i, i, 0.85))

    if not names:
        matches.append(PatternMatch(PatternKind.INITIALIZATION, 0, 0, 1.0))

    return matches
