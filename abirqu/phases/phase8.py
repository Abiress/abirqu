"""Phase 8: Developer Experience wiring layer."""

from __future__ import annotations

from ..tracker import BenchmarkPoint, QuantumAdvantageTracker


def cli_main(argv=None):
    from ..cli import main
    return main(argv)


def build_bell():
    from ..cli import build_bell as _build_bell
    return _build_bell()


__all__ = [
    "cli_main",
    "build_bell",
    "BenchmarkPoint",
    "QuantumAdvantageTracker",
]
