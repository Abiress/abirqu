"""
Gate map / coupling map visualizer for AbirQu.
"""
from __future__ import annotations
import html as _html
import math
from typing import Dict, List, Optional, Set, Tuple


def gate_map_svg(num_qubits: int,
                 edges: Optional[List[Tuple[int, int]]] = None,
                 title: str = "Coupling Map",
                 gate_counts: Optional[Dict[Tuple[int, int], int]] = None,
                 size: int = 400) -> str:
    cx, cy = size // 2, size // 2
    r = size // 2 - 40
    edge_set = set()
    if edges:
        for a, b in edges:
            edge_set.add((min(a, b), max(a, b)))

    positions = {}
    for q in range(num_qubits):
        angle = 2 * math.pi * q / num_qubits - math.pi / 2
        positions[q] = (cx + r * math.cos(angle), cy + r * math.sin(angle))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" font-family="monospace">']
    svg.append(f'<rect width="100%" height="100%" fill="#1e1e2e"/>')
    svg.append(f'<text x="{cx}" y="22" text-anchor="middle" fill="#cdd6f4" font-size="13" font-weight="bold">{_html.escape(title)}</text>')

    max_count = max(gate_counts.values()) if gate_counts else 1
    for a, b in edge_set:
        x1, y1 = positions[a]
        x2, y2 = positions[b]
        w = 1.5
        opacity = "0.6"
        if gate_counts and (a, b) in gate_counts:
            c = gate_counts[(a, b)]
            w = 1 + (c / max_count) * 4
            opacity = str(0.3 + (c / max_count) * 0.7)
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#89B4FA" stroke-width="{w:.1f}" stroke-opacity="{opacity}"/>')

    for q in range(num_qubits):
        x, y = positions[q]
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="#313244" stroke="#89B4FA" stroke-width="2"/>')
        svg.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" fill="#cdd6f4" font-size="12" font-weight="bold">q{q}</text>')

    svg.append("</svg>")
    return "\n".join(svg)
