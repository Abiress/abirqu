"""
Bloch sphere renderer for AbirQu — text and SVG with 3D projection.

Unique to AbirQu:
- Multi-qubit partial trace support
- State trajectory visualization
- Interactive rotation via elevation/azimuth parameters
"""
from __future__ import annotations
import math
from typing import Optional, Tuple, List
import numpy as np


def _bloch_vector(statevector: np.ndarray, qubit: int, n_qubits: int) -> Tuple[float, float, float]:
    """Extract reduced Bloch vector for a single qubit via partial trace."""
    rho = np.outer(statevector, statevector.conj())
    rho_red = np.zeros((2, 2), dtype=complex)
    for i in range(2 ** n_qubits):
        for j in range(2 ** n_qubits):
            bi = (i >> qubit) & 1
            bj = (j >> qubit) & 1
            if (i >> (qubit + 1)) == (j >> (qubit + 1)) and \
               ((i & ((1 << qubit) - 1)) == (j & ((1 << qubit) - 1))):
                rho_red[bi, bj] += rho[i, j]
    x = 2.0 * rho_red[0, 1].real
    y = 2.0 * rho_red[0, 1].imag
    z = rho_red[0, 0].real - rho_red[1, 1].real
    return float(x), float(y), float(z)


def _project(x: float, y: float, z: float, elev: float, azim: float) -> Tuple[float, float]:
    ce, se = math.cos(elev), math.sin(elev)
    ca, sa = math.cos(azim), math.sin(azim)
    x1 = x * ce + z * se
    z1 = -x * se + z * ce
    x2 = x1 * ca - y * sa
    y2 = x1 * sa + y * ca
    return x2, y2


class BlochSphere:
    """Render Bloch sphere as ASCII art or SVG."""

    def __init__(self, elevation: float = 0.3, azimuth: float = -0.5):
        self.elevation = elevation
        self.azimuth = azimuth

    def ascii(self, statevector: np.ndarray, qubit: int = 0,
              n_qubits: Optional[int] = None, width: int = 40) -> str:
        if n_qubits is None:
            n_qubits = int(math.log2(len(statevector)))
        bx, by, bz = _bloch_vector(statevector, qubit, n_qubits)

        rows = []
        half = width // 2
        for row in range(width):
            line = [" "] * width
            cy = (row - half) / half
            for col in range(width):
                cx = (col - half) / half
                r2 = cx * cx + cy * cy
                if abs(r2 - 1.0) < 0.04:
                    line[col] = "."
                if abs(cy) < 0.06 and r2 <= 1.0:
                    line[col] = ":"
            rows.append("".join(line))

        px, py = _project(bx, by, bz, self.elevation, self.azimuth)
        ci = max(0, min(width - 1, int((px + 1) / 2 * (width - 1))))
        ri = max(0, min(width - 1, int((-py + 1) / 2 * (width - 1))))
        rows[ri] = rows[ri][:ci] + "*" + rows[ri][ci + 1:]

        header = f"Bloch q{qubit}: ({bx:.3f}, {by:.3f}, {bz:.3f})"
        return header + "\n" + "\n".join(rows)

    def svg(self, statevector: np.ndarray, qubit: int = 0,
            n_qubits: Optional[int] = None, size: int = 260) -> str:
        if n_qubits is None:
            n_qubits = int(math.log2(len(statevector)))
        bx, by, bz = _bloch_vector(statevector, qubit, n_qubits)
        cx, cy = size // 2, size // 2
        r = size // 2 - 25

        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
               f'font-family="monospace">']
        svg.append(f'<rect width="100%" height="100%" fill="#1e1e2e"/>')
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                   f'stroke="#585b70" stroke-width="1.5"/>')
        svg.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r * 0.3}" '
                   f'fill="none" stroke="#585b70" stroke-width="1" stroke-dasharray="4,3"/>')
        svg.append(f'<line x1="{cx - r}" y1="{cy}" x2="{cx + r}" y2="{cy}" '
                   f'stroke="#45475a" stroke-width="1"/>')
        svg.append(f'<line x1="{cx}" y1="{cy - r}" x2="{cx}" y2="{cy + r}" '
                   f'stroke="#45475a" stroke-width="1"/>')
        svg.append(f'<text x="{cx + r + 5}" y="{cy + 4}" fill="#a6adc8">X</text>')
        svg.append(f'<text x="{cx - 5}" y="{cy - r - 5}" fill="#a6adc8">Z</text>')
        svg.append(f'<text x="{cx + 4}" y="{cy + r + 14}" fill="#a6adc8">|1></text>')
        svg.append(f'<text x="{cx + 4}" y="{cy - r + 14}" fill="#a6adc8">|0></text>')

        px, py = _project(bx, by, bz, self.elevation, self.azimuth)
        tip_x = cx + px * r
        tip_y = cy - py * r
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{tip_x}" y2="{tip_y}" '
                   f'stroke="#F38BA8" stroke-width="2.5"/>')
        svg.append(f'<circle cx="{tip_x}" cy="{tip_y}" r="4" fill="#F38BA8"/>')
        svg.append(f'<text x="8" y="{size - 8}" fill="#a6adc8" font-size="11">'
                   f'({bx:.3f}, {by:.3f}, {bz:.3f})</text>')
        svg.append("</svg>")
        return "\n".join(svg)
