"""
AbirQu Plugin: Quantum Circuit Visualization
Provides ASCII, histogram, and Bloch sphere rendering for quantum circuits.
"""
import cmath
import math
from typing import Any, Dict, List, Optional, Tuple


PLUGIN_NAME = "visualization"
PLUGIN_VERSION = "0.1.0"
PLUGIN_AUTHOR = "AbirQu Core Team"
PLUGIN_DESCRIPTION = "ASCII art and text-based visualization for quantum circuits and states"


# ─────────────────────────────────────────────────────────────
# ASCII Circuit Renderer
# ─────────────────────────────────────────────────────────────

def render_circuit_ascii(
    qubits: int,
    gates: List[Dict[str, Any]],
    title: str = "Quantum Circuit",
) -> str:
    """Render a quantum circuit as ASCII art."""
    wires: List[List[str]] = [["──"] for _ in range(qubits)]

    for op in gates:
        name = op.get("gate", "?")
        targets = op.get("qubits", [0])

        # Single-qubit gate
        if len(targets) == 1:
            q = targets[0]
            if 0 <= q < qubits:
                label = name[:3].center(5, "─")
                wires[q].append(f"┤{label}├")
                for r in range(qubits):
                    if r != q:
                        wires[r].append("─────")

        # Two-qubit gate (e.g., CNOT, CZ)
        elif len(targets) == 2:
            ctrl, tgt = targets[0], targets[1]
            if 0 <= ctrl < qubits and 0 <= tgt < qubits:
                for r in range(qubits):
                    if r == ctrl:
                        wires[r].append("──●──")
                    elif r == tgt:
                        label = name[:3].center(5, "─")
                        wires[r].append(f"┤{label}├")
                    elif min(ctrl, tgt) < r < max(ctrl, tgt):
                        wires[r].append("──│──")
                    else:
                        wires[r].append("─────")

    lines = [f"\n  {title}\n"]
    for q, wire in enumerate(wires):
        row = "".join(wire) + "──"
        lines.append(f"  q{q}: {row}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Measurement Histogram
# ─────────────────────────────────────────────────────────────

def render_histogram(
    counts: Dict[str, int],
    max_bars: int = 40,
    title: str = "Measurement Results",
) -> str:
    """Render a measurement histogram from a counts dict."""
    total = sum(counts.values()) or 1
    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
    max_count = max(counts.values()) if counts else 1

    lines = [f"\n  {title}  (total shots: {total})\n"]
    for state, count in sorted_counts:
        prob = count / total
        bar_len = round((count / max_count) * max_bars)
        bar = "█" * bar_len
        lines.append(f"  |{state}⟩ {bar:<{max_bars}} {count:>6}  ({prob:.2%})")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Bloch Sphere (text representation)
# ─────────────────────────────────────────────────────────────

def bloch_angles(alpha: complex, beta: complex) -> Tuple[float, float]:
    """
    Compute Bloch sphere angles (θ, φ) from single-qubit state |ψ⟩ = α|0⟩ + β|1⟩.
    Returns (theta_deg, phi_deg).
    """
    theta = 2 * math.acos(min(1.0, abs(alpha)))
    phi = cmath.phase(beta) - cmath.phase(alpha)
    return math.degrees(theta), math.degrees(phi)


def render_bloch_sphere(
    alpha: complex,
    beta: complex,
    qubit_label: str = "q0",
) -> str:
    """Render a text description of a Bloch sphere state."""
    norm = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
    if norm < 1e-9:
        return f"  {qubit_label}: invalid state (zero norm)"
    alpha, beta = alpha / norm, beta / norm

    theta, phi = bloch_angles(alpha, beta)
    x = math.sin(math.radians(theta)) * math.cos(math.radians(phi))
    y = math.sin(math.radians(theta)) * math.sin(math.radians(phi))
    z = math.cos(math.radians(theta))

    lines = [
        f"\n  Bloch Sphere — {qubit_label}",
        f"  ─────────────────────",
        f"  |0⟩ amplitude : {alpha:.4f}",
        f"  |1⟩ amplitude : {beta:.4f}",
        f"  θ (polar)     : {theta:.2f}°",
        f"  φ (azimuthal) : {phi:.2f}°",
        f"  Bloch vector  : ({x:.4f}, {y:.4f}, {z:.4f})",
    ]

    # Simple ASCII compass to indicate direction
    if z > 0.7:
        lines.append("  Position      : near |0⟩ (north pole)")
    elif z < -0.7:
        lines.append("  Position      : near |1⟩ (south pole)")
    elif abs(z) < 0.2:
        lines.append("  Position      : equatorial (superposition)")
    else:
        lines.append("  Position      : intermediate state")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Statevector Pretty Printer
# ─────────────────────────────────────────────────────────────

def render_statevector(
    sv: List[complex],
    n_qubits: Optional[int] = None,
    threshold: float = 1e-6,
    title: str = "Statevector",
) -> str:
    """Print statevector amplitudes with probabilities."""
    n = n_qubits or int(math.log2(len(sv)))
    lines = [f"\n  {title}  ({n} qubits, {len(sv)} amplitudes)\n"]
    for idx, amp in enumerate(sv):
        if abs(amp) < threshold:
            continue
        prob = abs(amp) ** 2
        state_label = format(idx, f"0{n}b")
        phase_str = f"∠{math.degrees(cmath.phase(amp)):.1f}°"
        bar = "█" * round(prob * 20)
        lines.append(
            f"  |{state_label}⟩  {amp.real:+.4f}{amp.imag:+.4f}j  "
            f"p={prob:.4f} {phase_str}  {bar}"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Plugin hook
# ─────────────────────────────────────────────────────────────

def on_circuit_run(data: Any) -> Dict[str, Any]:
    """Hook: generate ASCII circuit art after a run."""
    qubits = data.get("qubit_count", 2) if isinstance(data, dict) else 2
    gates = data.get("gates", []) if isinstance(data, dict) else []
    ascii_art = render_circuit_ascii(qubits, gates)
    return {"visualization": ascii_art}
