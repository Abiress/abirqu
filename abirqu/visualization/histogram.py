"""
Histogram plotter for AbirQu — text and SVG.
"""
from __future__ import annotations
import html as _html
from typing import Dict, Optional


def histogram_text(counts: Dict[str, int], title: str = "Results",
                   max_bars: int = 30, width: int = 50) -> str:
    if not counts:
        return "No data"
    total = sum(counts.values())
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:max_bars]
    mx = items[0][1]
    lines = [f"\n{title}", "=" * (width + 25)]
    for state, count in items:
        bar = int((count / mx) * width) if mx else 0
        pct = count / total * 100
        lines.append(f"{state:>12} |{'█' * bar:<{width}}| {count:>6} ({pct:5.1f}%)")
    if len(counts) > max_bars:
        lines.append(f"  ... +{len(counts) - max_bars} more")
    lines.append(f"{'Total':>12}   {total} shots")
    return "\n".join(lines)


def histogram_svg(counts: Dict[str, int], title: str = "Results",
                  width: int = 700, bar_height: int = 24,
                  max_bars: int = 40) -> str:
    if not counts:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40"><text x="10" y="25" fill="#cdd6f4">No data</text></svg>'
    total = sum(counts.values())
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:max_bars]
    mx = items[0][1]
    n = len(items)
    label_w = max(len(s) for s, _ in items) * 8 + 10
    bar_area = width - label_w - 80
    row_h = bar_height + 4
    svg_h = n * row_h + 50

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{svg_h}" '
           f'font-family="monospace" font-size="12">']
    svg.append(f'<rect width="100%" height="100%" fill="#1e1e2e"/>')
    svg.append(f'<text x="{width // 2}" y="20" text-anchor="middle" fill="#cdd6f4" '
               f'font-size="14" font-weight="bold">{_html.escape(title)}</text>')

    colors = ["#F38BA8", "#A6E3A1", "#89B4FA", "#F9E2AF", "#CBA6F7",
              "#94E2D5", "#FAB387", "#74C7EC", "#BAC2DE", "#F5C2E7"]

    for i, (state, count) in enumerate(items):
        y = 35 + i * row_h
        bar_w = (count / mx) * bar_area if mx else 0
        pct = count / total * 100
        color = colors[i % len(colors)]
        svg.append(f'<text x="{label_w - 5}" y="{y + 15}" text-anchor="end" fill="#cdd6f4">{state}</text>')
        svg.append(f'<rect x="{label_w}" y="{y + 2}" width="{bar_w:.1f}" height="{bar_height}" rx="3" fill="{color}" fill-opacity="0.85"/>')
        svg.append(f'<text x="{label_w + bar_w + 5}" y="{y + 15}" fill="#a6adc8">{count} ({pct:.1f}%)</text>')

    svg.append("</svg>")
    return "\n".join(svg)
