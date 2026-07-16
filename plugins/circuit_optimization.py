"""
AbirQu Plugin: Circuit Optimization
Gate fusion, template optimization, and circuit simplification.
"""
from typing import Any, Dict, List, Optional, Tuple


PLUGIN_NAME = "circuit_optimization"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "Circuit optimization: gate fusion, template rewriting, and simplification"


def activate(context: Dict[str, Any]) -> None:
    pass


def deactivate() -> None:
    pass


def get_manifest() -> Dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "author": PLUGIN_AUTHOR,
        "description": PLUGIN_DESCRIPTION,
    }


# ─────────────────────────────────────────────────────────────
# Gate Fusion Rules
# ─────────────────────────────────────────────────────────────

FUSION_RULES = {
    ("H", "H"): [],
    ("X", "X"): [],
    ("Y", "Y"): [],
    ("Z", "Z"): [],
    ("S", "S"): [("Z",)],
    ("Sdg", "Sdg"): [("Z",)],
    ("T", "T"): [("S",)],
    ("Tdg", "Tdg"): [("Sdg",)],
    ("Rx", "Rx"): [("Rx", "add_angles")],
    ("Ry", "Ry"): [("Ry", "add_angles")],
    ("Rz", "Rz"): [("Rz", "add_angles")],
    ("SX", "SX"): [("X",)],
}


def fuse_gates(gates: List[Dict], num_qubits: int) -> Dict[str, Any]:
    """Apply gate fusion rules to reduce gate count.

    Args:
        gates: Gate list (each dict has 'type', 'qubit', optional 'angle').
        num_qubits: Number of qubits.

    Returns:
        Dict with fused gates and statistics.
    """
    qubit_wires: Dict[int, List[Dict]] = {i: [] for i in range(num_qubits)}
    for g in gates:
        q = g.get("qubit", 0)
        if q in qubit_wires:
            qubit_wires[q].append(g.copy())

    fused_wires: Dict[int, List[Dict]] = {}
    total_fused = 0

    for q in range(num_qubits):
        wire = qubit_wires[q]
        result = []
        i = 0
        while i < len(wire):
            fused = False
            if i + 1 < len(wire):
                g1, g2 = wire[i], wire[i + 1]
                key = (g1["type"], g2["type"])
                if key in FUSION_RULES:
                    rules = FUSION_RULES[key]
                    total_fused += 2
                    if len(rules) == 0:
                        i += 2
                        fused = True
                    else:
                        for rule in rules:
                            if rule[0] == "add_angles":
                                angle1 = g1.get("angle", 0)
                                angle2 = g2.get("angle", 0)
                                new_angle = angle1 + angle2
                                if abs(new_angle) > 1e-10:
                                    result.append({"type": g1["type"], "qubit": q, "angle": new_angle})
                            else:
                                result.append({"type": rule[0], "qubit": q})
                        i += 2
                        fused = True
            if not fused:
                result.append(wire[i])
                i += 1
        fused_wires[q] = result

    output_gates = []
    for q in range(num_qubits):
        output_gates.extend(fused_wires.get(q, []))

    return {
        "gates": output_gates,
        "original_count": len(gates),
        "fused_count": len(output_gates),
        "gates_fused": total_fused,
    }


# ─────────────────────────────────────────────────────────────
# Template Optimization
# ─────────────────────────────────────────────────────────────

TEMPLATES = [
    {"pattern": [("CNOT", 0, 1), ("H", 0), ("H", 1), ("CNOT", 0, 1)],
     "replacement": [("CNOT", 0, 1)],
     "description": "CNOT-HH-CNOT -> CNOT"},
    {"pattern": [("CNOT", 0, 1), ("X", 1), ("CNOT", 0, 1)],
     "replacement": [("X", 0), ("CNOT", 0, 1)],
     "description": "CNOT-X-CNOT -> X-CNOT"},
    {"pattern": [("H", 0), ("CNOT", 0, 1), ("H", 0)],
     "replacement": [("CNOT", 1, 0)],
     "description": "H-CNOT-H -> reverse CNOT"},
    {"pattern": [("S", 0), ("H", 0), ("S", 0)],
     "replacement": [("H", 0)],
     "description": "S-H-S -> H"},
    {"pattern": [("X", 0), ("Z", 0)],
     "replacement": [("Z", 0), ("X", 0)],
     "description": "XZ -> ZX (commutation)"},
]


def template_optimize(
    gates: List[Dict],
    num_qubits: int,
    max_iterations: int = 100,
) -> Dict[str, Any]:
    """Apply template-based circuit optimization.

    Args:
        gates: Gate list.
        num_qubits: Number of qubits.
        max_iterations: Maximum optimization passes.

    Returns:
        Dict with optimized gates and statistics.
    """
    optimized = [g.copy() for g in gates]
    total_saves = 0

    for iteration in range(max_iterations):
        changed = False
        new_gates = []
        i = 0
        while i < len(optimized):
            matched = False
            for template in TEMPLATES:
                pat = template["pattern"]
                if i + len(pat) <= len(optimized):
                    match = True
                    for j, p_gate in enumerate(pat):
                        o_gate = optimized[i + j]
                        if o_gate["type"] != p_gate[0]:
                            match = False
                            break
                        if len(p_gate) > 1 and o_gate.get("qubit", 0) != p_gate[1]:
                            match = False
                            break
                        if len(p_gate) > 2 and o_gate.get("target", o_gate.get("qubit", 0)) != p_gate[2]:
                            match = False
                            break
                    if match:
                        for r_gate in template["replacement"]:
                            new_gates.append({"type": r_gate[0], "qubit": r_gate[1] if len(r_gate) > 1 else 0})
                        total_saves += len(pat) - len(template["replacement"])
                        i += len(pat)
                        matched = True
                        changed = True
                        break
            if not matched:
                new_gates.append(optimized[i])
                i += 1
        optimized = new_gates
        if not changed:
            break

    return {
        "gates": optimized,
        "original_count": len(gates),
        "optimized_count": len(optimized),
        "gates_saved": total_saves,
        "iterations": iteration + 1,
    }


# ─────────────────────────────────────────────────────────────
# Circuit Depth Reduction
# ─────────────────────────────────────────────────────────────

def reduce_depth(
    gates: List[Dict],
    num_qubits: int,
) -> Dict[str, Any]:
    """Reorder gates to minimize circuit depth by parallelizing independent gates.

    Args:
        gates: Gate list.
        num_qubits: Number of qubits.

    Returns:
        Dict with depth-optimized gate schedule.
    """
    qubit_usage: Dict[int, int] = {i: 0 for i in range(num_qubits)}
    layers: List[List[Dict]] = []
    gate_count = 0

    for gate in gates:
        q = gate.get("qubit", 0)
        t = gate.get("target", gate.get("control", None))

        earliest = qubit_usage[q]
        if t is not None:
            earliest = max(earliest, qubit_usage[t])

        placed = False
        for layer_idx in range(earliest, len(layers)):
            layer_qubits = set()
            for g in layers[layer_idx]:
                layer_qubits.add(g.get("qubit", 0))
                if "target" in g:
                    layer_qubits.add(g["target"])
                if "control" in g:
                    layer_qubits.add(g["control"])
            if q not in layer_qubits and (t is None or t not in layer_qubits):
                layers[layer_idx].append(gate.copy())
                qubit_usage[q] = layer_idx + 1
                if t is not None:
                    qubit_usage[t] = layer_idx + 1
                placed = True
                break

        if not placed:
            layers.append([gate.copy()])
            qubit_usage[q] = len(layers)
            if t is not None:
                qubit_usage[t] = len(layers)

        gate_count += 1

    original_depth = sum(1 for _ in range(num_qubits))
    optimized_depth = len(layers)

    return {
        "layers": [layer for layer in layers],
        "depth": optimized_depth,
        "gate_count": gate_count,
        "depth_reduction": max(0, original_depth - optimized_depth),
    }


# ─────────────────────────────────────────────────────────────
# Commutation-Based Optimization
# ─────────────────────────────────────────────────────────────

def commute_optimize(
    gates: List[Dict],
    num_qubits: int,
) -> Dict[str, Any]:
    """Reorder commuting gates to expose fusion opportunities.

    Args:
        gates: Gate list.
        num_qubits: Number of qubits.

    Returns:
        Dict with reordered gates.
    """
    def _affects_same_qubit(g1: Dict, g2: Dict) -> bool:
        q1 = g1.get("qubit", 0)
        q2 = g2.get("qubit", 0)
        t1 = g1.get("target", g1.get("control", None))
        t2 = g2.get("target", g2.get("control", None))
        if q1 == q2:
            return True
        if t1 is not None and t1 == q2:
            return True
        if t2 is not None and t2 == q1:
            return True
        if t1 is not None and t2 is not None and (t1 == t2 or t1 == q2 or t2 == q1):
            return True
        return False

    def _commutes(g1: Dict, g2: Dict) -> bool:
        if not _affects_same_qubit(g1, g2):
            return True
        if g1["type"] in ("X", "Y", "Z") and g2["type"] in ("X", "Y", "Z"):
            return True
        return False

    result = list(gates)
    changed = True
    swaps = 0
    seen = set()
    while changed:
        changed = False
        for i in range(len(result) - 1):
            key = (result[i]["type"], result[i + 1]["type"], i)
            if key in seen:
                continue
            if _commutes(result[i], result[i + 1]):
                if result[i]["type"] != result[i + 1]["type"]:
                    result[i], result[i + 1] = result[i + 1], result[i]
                    swaps += 1
                    changed = True
                    seen.add(key)
                    break

    return {
        "gates": result,
        "original_count": len(gates),
        "swaps_made": swaps,
    }
