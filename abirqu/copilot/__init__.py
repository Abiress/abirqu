"""
LLM Copilot Circuit Design
===========================
Natural-language to quantum-circuit translation using template matching,
keyword extraction, and optional LLM integration for advanced generation.
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..circuit import Circuit


# ---------------------------------------------------------------------------
# Circuit template
# ---------------------------------------------------------------------------

@dataclass
class CircuitTemplate:
    """A named circuit template with keyword triggers and a builder function.

    Parameters
    ----------
    name : str
        Human-readable template name.
    keywords : list of str
        Trigger words that indicate this template should be used.
    description : str
        Short description of what the template builds.
    build : callable
        ``(num_qubits: int, params: dict) → Circuit``.
    param_schema : dict
        Mapping from parameter name to ``(default, description)``.
    """

    name: str
    keywords: List[str]
    description: str
    build: callable  # type: ignore[valid-type]
    param_schema: Dict[str, Tuple[Any, str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Template library
# ---------------------------------------------------------------------------

def _bell(num_qubits: int = 2, **kw: Any) -> Circuit:
    c = Circuit(2, "bell_state")
    c.h(0)
    c.cnot(0, 1)
    return c


def _ghz(num_qubits: int = 2, **kw: Any) -> Circuit:
    n = max(2, num_qubits)
    c = Circuit(n, "ghz")
    c.h(0)
    for i in range(n - 1):
        c.cnot(i, i + 1)
    return c


def _qft(num_qubits: int = 4, **kw: Any) -> Circuit:
    n = max(1, num_qubits)
    c = Circuit(n, "qft")
    for i in range(n):
        c.h(i)
        for j in range(i + 1, n):
            angle = math.pi / (2 ** (j - i))
            c.rz(j, angle)
            c.cnot(j, i)
            c.rz(j, -angle)
            c.cnot(j, i)
    return c


def _teleportation(num_qubits: int = 3, **kw: Any) -> Circuit:
    c = Circuit(3, "teleportation")
    c.h(1)
    c.cnot(1, 2)
    c.cnot(0, 1)
    c.h(0)
    c.measure(0, 0)
    c.measure(1, 1)
    return c


def _grover_oracle(num_qubits: int = 2, **kw: Any) -> Circuit:
    """Grover oracle marking the |11…1⟩ state."""
    n = max(2, num_qubits)
    c = Circuit(n, "grover_oracle")
    for i in range(n):
        c.x(i)
    if n == 2:
        c.cz(0, 1)
    else:
        # Multi-control: Toffoli decomposition
        for i in range(n - 2):
            c.toffoli(i, i + 1, i + 2)
        c.cz(n - 2, n - 1)
        for i in range(n - 3, -1, -1):
            c.toffoli(i, i + 1, i + 2)
    for i in range(n):
        c.x(i)
    return c


def _grover(num_qubits: int = 2, **kw: Any) -> Circuit:
    """Full Grover search with diffusion operator."""
    n = max(2, num_qubits)
    c = Circuit(n, "grover")
    # Superposition
    for i in range(n):
        c.h(i)
    # Oracle + diffusion (one iteration for small n)
    oracle = _grover_oracle(n)
    for g in getattr(oracle, "gates", []):
        c.add_gate(g.name, list(g.qubits), list(g.params))
    # Diffusion
    for i in range(n):
        c.h(i)
        c.x(i)
    if n == 2:
        c.cz(0, 1)
    else:
        for i in range(n - 3, -1, -1):
            c.toffoli(i, i + 1, i + 2)
        c.cz(n - 2, n - 1)
        for i in range(n - 2):
            c.toffoli(i, i + 1, i + 2)
    for i in range(n):
        c.x(i)
        c.h(i)
    return c


def _vqe_ansatz(num_qubits: int = 4, **kw: Any) -> Circuit:
    """Hardware-efficient VQE ansatz (single layer)."""
    n = max(2, num_qubits)
    c = Circuit(n, "vqe_ansatz")
    for i in range(n):
        c.ry(i, kw.get("theta", 0.5))
    for i in range(0, n - 1, 2):
        c.cnot(i, i + 1)
    for i in range(n):
        c.rz(i, kw.get("phi", 0.3))
    for i in range(1, n - 1, 2):
        c.cnot(i, i + 1)
    return c


def _qaoa(num_qubits: int = 4, **kw: Any) -> Circuit:
    """QAOA circuit (one layer)."""
    n = max(2, num_qubits)
    c = Circuit(n, "qaoa")
    gamma = kw.get("gamma", 0.5)
    beta = kw.get("beta", 0.3)
    for i in range(n):
        c.h(i)
    # Problem unitary
    for i in range(0, n - 1, 2):
        c.cnot(i, i + 1)
        c.rz(i + 1, gamma)
        c.cnot(i, i + 1)
    # Mixer unitary
    for i in range(n):
        c.rx(i, 2 * beta)
    return c


_TEMPLATE_LIBRARY: List[CircuitTemplate] = [
    CircuitTemplate(
        name="bell",
        keywords=["bell", "bell state", "epr", "pair", "entangle two"],
        description="Bell state entanglement (|Φ+⟩)",
        build=_bell,
    ),
    CircuitTemplate(
        name="ghz",
        keywords=["ghz", "ghz state", "multi-partite", "greenberger"],
        description="GHZ state across N qubits",
        build=_ghz,
    ),
    CircuitTemplate(
        name="qft",
        keywords=[
            "qft", "quantum fourier", "fourier transform",
            "fourier", "frequency",
        ],
        description="Quantum Fourier Transform",
        build=_qft,
    ),
    CircuitTemplate(
        name="teleportation",
        keywords=["teleport", "quantum teleport", "teleportation"],
        description="Quantum teleportation protocol",
        build=_teleportation,
    ),
    CircuitTemplate(
        name="grover",
        keywords=[
            "grover", "search", "amplitude amplification", "oracle",
            "grover search", "amplify",
        ],
        description="Grover's search algorithm",
        build=_grover,
    ),
    CircuitTemplate(
        name="vqe",
        keywords=[
            "vqe", "variational", "ansatz", "eigensolver",
            "variational quantum", "hardware efficient",
        ],
        description="Variational Quantum Eigensolver ansatz",
        build=_vqe_ansatz,
    ),
    CircuitTemplate(
        name="qaoa",
        keywords=[
            "qaoa", "optimization", "max cut", "combinatorial",
            "quantum approximate",
        ],
        description="Quantum Approximate Optimization Algorithm",
        build=_qaoa,
    ),
]


# ---------------------------------------------------------------------------
# NL Parser
# ---------------------------------------------------------------------------

class NLParser:
    """Parse natural-language circuit descriptions into structured specs.

    Extracts:
    - Template name (via keyword matching)
    - Number of qubits (via regex)
    - Parameters (theta, phi, gamma, beta) from text
    """

    _QUBIT_PATTERNS = [
        re.compile(r"(\d+)\s*-?\s*qubit", re.IGNORECASE),
        re.compile(r"for\s+(\d+)\s+qubit", re.IGNORECASE),
        re.compile(r"(\d+)\s+q", re.IGNORECASE),
    ]

    _PARAM_PATTERNS = {
        "theta": re.compile(r"theta\s*=\s*([\d.]+)", re.IGNORECASE),
        "phi": re.compile(r"phi\s*=\s*([\d.]+)", re.IGNORECASE),
        "gamma": re.compile(r"gamma\s*=\s*([\d.]+)", re.IGNORECASE),
        "beta": re.compile(r"beta\s*=\s*([\d.]+)", re.IGNORECASE),
    }

    @classmethod
    def parse(cls, description: str) -> Dict[str, Any]:
        """Parse *description* and return a spec dict."""
        lower = description.lower()
        template_name = cls._match_template(lower)
        num_qubits = cls._extract_qubits(lower)
        params = cls._extract_params(description)
        return {
            "template": template_name,
            "num_qubits": num_qubits,
            "params": params,
            "raw": description,
        }

    @classmethod
    def _match_template(cls, text: str) -> Optional[str]:
        best_name: Optional[str] = None
        best_score = 0
        for tmpl in _TEMPLATE_LIBRARY:
            score = sum(1 for kw in tmpl.keywords if kw in text)
            if score > best_score:
                best_score = score
                best_name = tmpl.name
        return best_name

    @classmethod
    def _extract_qubits(cls, text: str) -> int:
        for pat in cls._QUBIT_PATTERNS:
            m = pat.search(text)
            if m:
                return int(m.group(1))
        return 2

    @classmethod
    def _extract_params(cls, text: str) -> Dict[str, float]:
        params: Dict[str, float] = {}
        for key, pat in cls._PARAM_PATTERNS.items():
            m = pat.search(text)
            if m:
                params[key] = float(m.group(1))
        return params


# ---------------------------------------------------------------------------
# Quantum Copilot
# ---------------------------------------------------------------------------

class QuantumCopilot:
    """Natural-language to quantum-circuit copilot.

    Uses template matching and keyword extraction by default.
    Optionally integrates with LLM APIs for advanced circuit generation.

    Example::

        copilot = QuantumCopilot()
        circuit = copilot.generate_circuit("Create a 4-qubit GHZ state")

        # With LLM integration:
        copilot = QuantumCopilot(llm_api_key="your-key")
        circuit = copilot.generate_circuit("Create a quantum circuit for portfolio optimization")
    """

    def __init__(
        self,
        templates: Optional[List[CircuitTemplate]] = None,
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-4",
        llm_provider: str = "openai",
    ) -> None:
        self.templates = templates or list(_TEMPLATE_LIBRARY)
        self.parser = NLParser()
        self.llm_api_key = llm_api_key or os.environ.get("OPENAI_API_KEY")
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self._llm_available = self.llm_api_key is not None

    # -- generate -----------------------------------------------------------

    def generate_circuit(self, description: str) -> Circuit:
        """Generate a circuit from a natural-language *description*.

        First tries template matching. If no template matches and LLM is
        available, uses LLM for advanced generation.
        """
        spec = self.parser.parse(description)
        template_name = spec["template"]
        num_qubits = spec["num_qubits"]
        params = spec["params"]

        for tmpl in self.templates:
            if tmpl.name == template_name:
                return tmpl.build(num_qubits, **params)

        if self._llm_available:
            try:
                return self._llm_generate(description)
            except Exception:
                pass

        return self._generic_circuit(num_qubits)

    def _llm_generate(self, description: str) -> Circuit:
        """Use LLM to generate a circuit from natural language."""
        import urllib.request

        prompt = f"""You are a quantum computing expert. Convert this description into a quantum circuit.

Description: {description}

Return ONLY a JSON object with this structure:
{{
  "num_qubits": <int>,
  "gates": [
    {{"name": "H", "qubits": [0]}},
    {{"name": "CNOT", "qubits": [0, 1]}},
    {{"name": "RZ", "qubits": [0], "params": [0.5]}},
    ...
  ]
}}

Valid gate names: H, X, Y, Z, S, S_DAG, T, T_DAG, RX, RY, RZ, CNOT, CZ, SWAP, TOFFOLI, ECR, ISWAP
"""

        payload = json.dumps({
            "model": self.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1000,
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())

        content = data["choices"][0]["message"]["content"]
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            raise ValueError("LLM response did not contain valid JSON")

        circuit_spec = json.loads(json_match.group())
        return self._build_from_spec(circuit_spec)

    def _build_from_spec(self, spec: Dict[str, Any]) -> Circuit:
        """Build a circuit from a JSON spec dict."""
        n_qubits = spec.get("num_qubits", 2)
        circuit = Circuit(n_qubits, "llm_generated")

        for gate_spec in spec.get("gates", []):
            name = gate_spec.get("name", "H").upper()
            qubits = gate_spec.get("qubits", [0])
            params = gate_spec.get("params", [])

            if name == "H":
                circuit.h(qubits[0])
            elif name == "X":
                circuit.x(qubits[0])
            elif name == "Y":
                circuit.y(qubits[0])
            elif name == "Z":
                circuit.z(qubits[0])
            elif name == "S":
                circuit.s(qubits[0])
            elif name == "S_DAG":
                circuit.s_dag(qubits[0])
            elif name == "T":
                circuit.t(qubits[0])
            elif name == "T_DAG":
                circuit.t_dag(qubits[0])
            elif name == "RX":
                circuit.rx(qubits[0], params[0] if params else 0.0)
            elif name == "RY":
                circuit.ry(qubits[0], params[0] if params else 0.0)
            elif name == "RZ":
                circuit.rz(qubits[0], params[0] if params else 0.0)
            elif name == "CNOT":
                circuit.cnot(qubits[0], qubits[1] if len(qubits) > 1 else 0)
            elif name == "CZ":
                circuit.cz(qubits[0], qubits[1] if len(qubits) > 1 else 0)
            elif name == "SWAP":
                circuit.swap(qubits[0], qubits[1] if len(qubits) > 1 else 1)

        return circuit

    def _generic_circuit(self, n: int) -> Circuit:
        c = Circuit(n, "generic_superposition")
        for i in range(n):
            c.h(i)
        for i in range(0, n - 1, 2):
            c.cnot(i, i + 1)
        return c

    # -- suggestions --------------------------------------------------------

    def suggest_optimization(self, circuit: Circuit) -> List[str]:
        """Return a list of natural-language optimisation suggestions."""
        suggestions: List[str] = []
        gates = getattr(circuit, "gates", [])
        n = circuit.num_qubits

        # Check for redundant H pairs
        h_positions: Dict[int, List[int]] = {}
        for idx, g in enumerate(gates):
            if g.name.upper() == "H" and len(g.qubits) == 1:
                h_positions.setdefault(g.qubits[0], []).append(idx)
        for q, pos in h_positions.items():
            for i in range(len(pos) - 1):
                if pos[i + 1] - pos[i] == 1:
                    suggestions.append(
                        f"Qubit {q}: adjacent H gates at positions "
                        f"{pos[i]} and {pos[i+1]} can be cancelled."
                    )

        # Check for adjacent inverse rotations
        for i in range(len(gates) - 1):
            g1, g2 = gates[i], gates[i + 1]
            if (
                g1.name == g2.name
                and g1.qubits == g2.qubits
                and g1.name.upper() in ("RX", "RY", "RZ")
                and g1.params
                and g2.params
                and abs(g1.params[0] + g2.params[0]) < 1e-10
            ):
                suggestions.append(
                    f"Positions {i}–{i+1}: adjacent {g1.name} gates with "
                    "opposite angles cancel each other."
                )

        # Depth suggestion
        if len(gates) > 20:
            suggestions.append(
                f"Circuit has {len(gates)} gates on {n} qubits. "
                "Consider decomposing into parallel layers to reduce depth."
            )

        if not suggestions:
            suggestions.append("No obvious optimisations found. Circuit looks good!")

        return suggestions

    # -- explain ------------------------------------------------------------

    def explain_circuit(self, circuit: Circuit) -> str:
        """Return a natural-language explanation of *circuit*."""
        gates = getattr(circuit, "gates", [])
        n = circuit.num_qubits
        lines = [
            f"Quantum circuit with {n} qubits and {len(gates)} gate(s).",
        ]

        gate_counts: Dict[str, int] = {}
        for g in gates:
            gate_counts[g.name] = gate_counts.get(g.name, 0) + 1
        if gate_counts:
            counts_str = ", ".join(
                f"{name}×{cnt}" for name, cnt in sorted(gate_counts.items())
            )
            lines.append(f"Gate composition: {counts_str}.")

        two_qubit = sum(1 for g in gates if len(g.qubits) >= 2)
        if two_qubit:
            lines.append(
                f"{two_qubit} two-qubit gate(s) — these dominate "
                "execution time and error."
            )

        # Detect known patterns
        pattern = self._detect_pattern(gates, n)
        if pattern:
            lines.append(f"Detected pattern: {pattern}.")

        return " ".join(lines)

    def _detect_pattern(self, gates: list, n: int) -> Optional[str]:
        names = [g.name.upper() for g in gates]
        if names[:1] == ["H"] and names[1:2] == ["CNOT"]:
            return "Bell-state entanglement"
        if names.count("H") >= n and names.count("CNOT") >= n - 1:
            return "GHZ / entangling circuit"
        if "RZ" in names and "CNOT" in names and any(
            "RX" in g.name for g in gates
        ):
            return "VQE / variational ansatz"
        return None

    # -- complete -----------------------------------------------------------

    def complete_circuit(self, partial_circuit: Circuit) -> Circuit:
        """Complete a partial circuit with measurement and finalisation."""
        completed = partial_circuit.copy()
        n = completed.num_qubits
        has_measure = len(completed.measurements) > 0
        if not has_measure:
            for i in range(n):
                completed.measure(i, i)
        return completed

    # -- template access ----------------------------------------------------

    def list_templates(self) -> List[Dict[str, Any]]:
        """Return metadata for all available templates."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "keywords": t.keywords,
                "parameters": {
                    k: {"default": v[0], "description": v[1]}
                    for k, v in t.param_schema.items()
                },
            }
            for t in self.templates
        ]


__all__ = [
    "QuantumCopilot",
    "CircuitTemplate",
    "NLParser",
]
