"""
Error map visualizer for AbirQu — per-qubit error rates as a heatmap.
"""
from __future__ import annotations
import html as _html
from typing import Dict, List, Optional, Tuple


def error_map_svg(num_qubits: int,
                  readout_errors: Optional[List[float]] = None,
                  t1_times: Optional[List[float]] = None,
                  t2_times: Optional[List[float]] = None,
                  gate_errors: Optional[Dict[Tuple[int, int], float]] = None,
                  title: str = "Error Map", size: int = 500) -> str:
    n = num_qubits
    cell_w = max(40, size // (n + 2))
    label_h = 60
    row_h = 32
    total_h = label_h + n * row_h + 40
    total_w = n * cell_w + 160

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" font-family="monospace" font-size="11">']
    svg.append(f'<rect width="100%" height="100%" fill="#1e1e2e"/>')
    svg.append(f'<text x="{total_w // 2}" y="20" text-anchor="middle" fill="#cdd6f4" font-size="13" font-weight="bold">{_html.escape(title)}</text>')

    def _color(e):
        if e < 0.005: return "#A6E3A1"
        elif e < 0.02: return "#F9E2AF"
        elif e < 0.05: return "#FAB387"
        else: return "#F38BA8"

    header_y = 35
    svg.append(f'<text x="10" y="{header_y}" fill="#a6adc8">Qubit</text>')
    for q in range(n):
        x = 80 + q * cell_w + cell_w // 2
        svg.append(f'<text x="{x}" y="{header_y}" text-anchor="middle" fill="#a6adc8">q{q}</text>')

    rows_data = [("Readout", readout_errors)]
    if t1_times:
        rows_data.append(("T1 (us)", t1_times))
    if t2_times:
        rows_data.append(("T2 (us)", t2_times))

    for ri, (label, data) in enumerate(rows_data):
        y = label_h + ri * row_h
        svg.append(f'<text x="10" y="{y + 14}" fill="#a6adc8">{label}</text>')
        for q in range(n):
            x = 80 + q * cell_w
            if data and q < len(data):
                val = data[q]
                if label == "Readout":
                    color = _color(val)
                    svg.append(f'<rect x="{x + 1}" y="{y}" width="{cell_w - 2}" height="{row_h - 2}" rx="3" fill="{color}" fill-opacity="0.8"/>')
                    svg.append(f'<text x="{x + cell_w // 2}" y="{y + 14}" text-anchor="middle" fill="#1e1e2e" font-weight="bold">{val:.3f}</text>')
                else:
                    svg.append(f'<rect x="{x + 1}" y="{y}" width="{cell_w - 2}" height="{row_h - 2}" rx="3" fill="#45475a"/>')
                    svg.append(f'<text x="{x + cell_w // 2}" y="{y + 14}" text-anchor="middle" fill="#cdd6f4">{val:.0f}</text>')

    svg.append("</svg>")
    return "\n".join(svg)
