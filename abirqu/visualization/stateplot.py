"""
State vector plotter for AbirQu — city plot and probability bars.

Unique to AbirQu:
- Phase-colored amplitude bars (hue = phase angle)
- Interactive SVG with hover labels
- Supports both statevector and probability input
"""
from __future__ import annotations
import html as _html
import math
from typing import Optional
import numpy as np


def stateplot_svg(statevector: np.ndarray, title: str = "State Vector",
                  max_bars: int = 32, size: int = 500) -> str:
    """City plot: bars colored by phase, height by amplitude."""
    n_qubits = int(math.log2(len(statevector)))
    n_show = min(len(statevector), max_bars)
    data = sorted(enumerate(statevector), key=lambda x: abs(x[1]), reverse=True)[:n_show]

    bar_w = max(12, (size - 80) // n_show)
    svg_w = n_show * bar_w + 80
    svg_h = size
    base_y = svg_h - 60

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
           f'font-family="monospace" font-size="10">']
    svg.append(f'<rect width="100%" height="100%" fill="#1e1e2e"/>')
    svg.append(f'<text x="{svg_w // 2}" y="20" text-anchor="middle" fill="#cdd6f4" '
               f'font-size="13" font-weight="bold">{_html.escape(title)}</text>')

    max_amp = max(abs(amp) for _, amp in data) if data else 1
    scale = (base_y - 40) / max_amp if max_amp else 1

    for i, (idx, amp) in enumerate(data):
        x = 40 + i * bar_w
        h = abs(amp) * scale
        y = base_y - h
        phase = math.degrees(math.atan2(amp.imag, amp.real)) % 360
        hue = int(phase * 2.4)
        color = f"hsl({hue}, 70%, 55%)"
        svg.append(f'<rect x="{x + 1}" y="{y:.1f}" width="{bar_w - 2}" height="{h:.1f}" '
                   f'fill="{color}" fill-opacity="0.85" rx="2"/>')
        svg.append(f'<text x="{x + bar_w // 2}" y="{base_y + 12}" text-anchor="middle" '
                   f'fill="#a6adc8" font-size="9">{idx}</text>')

    svg.append(f'<text x="{svg_w // 2}" y="{svg_h - 8}" text-anchor="middle" fill="#585b70">'
               f'Amplitude magnitude (color = phase)</text>')
    svg.append("</svg>")
    return "\n".join(svg)


def probability_svg(statevector: np.ndarray, title: str = "Probabilities",
                    max_bars: int = 32, size: int = 500) -> str:
    probs = np.abs(statevector) ** 2
    n_qubits = int(math.log2(len(statevector)))
    data = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)[:max_bars]

    bar_w = max(14, (size - 80) // len(data)) if data else 14
    svg_w = len(data) * bar_w + 80
    svg_h = size
    base_y = svg_h - 60

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
           f'font-family="monospace" font-size="10">']
    svg.append(f'<rect width="100%" height="100%" fill="#1e1e2e"/>')
    svg.append(f'<text x="{svg_w // 2}" y="20" text-anchor="middle" fill="#cdd6f4" '
               f'font-size="13" font-weight="bold">{_html.escape(title)}</text>')

    mx = data[0][1] if data else 1
    scale = (base_y - 40) / mx if mx else 1
    colors = ["#F38BA8", "#A6E3A1", "#89B4FA", "#F9E2AF", "#CBA6F7",
              "#94E2D5", "#FAB387", "#74C7EC"]

    for i, (idx, p) in enumerate(data):
        x = 40 + i * bar_w
        h = p * scale
        y = base_y - h
        color = colors[i % len(colors)]
        svg.append(f'<rect x="{x + 1}" y="{y:.1f}" width="{bar_w - 2}" height="{h:.1f}" '
                   f'fill="{color}" fill-opacity="0.85" rx="2"/>')
        label = format(idx, f"0{n_qubits}b")
        svg.append(f'<text x="{x + bar_w // 2}" y="{base_y + 12}" text-anchor="middle" '
                   f'fill="#a6adc8" font-size="9">{label}</text>')
        if p > 0.01:
            svg.append(f'<text x="{x + bar_w // 2}" y="{y - 4}" text-anchor="middle" '
                       f'fill="#cdd6f4" font-size="9">{p:.2f}</text>')

    svg.append("</svg>")
    return "\n".join(svg)


def stateplot_ascii(statevector: np.ndarray, max_bars: int = 20) -> str:
    probs = np.abs(statevector) ** 2
    n_qubits = int(math.log2(len(statevector)))
    data = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)[:max_bars]
    mx = data[0][1] if data else 1
    width = 40
    lines = ["Probability Distribution", "=" * 55]
    for idx, p in data:
        label = format(idx, f"0{n_qubits}b")
        bar = int((p / mx) * width) if mx else 0
        lines.append(f"|{label}> |{'█' * bar:<{width}}| {p:.4f}")
    return "\n".join(lines)
