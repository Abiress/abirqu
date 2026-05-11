"""Phase 3: Quantum Error Correction wiring layer."""

from __future__ import annotations

from ..qec import EncodedState, LDPCCode, LDPCDecoder, LDPCEncoder, SurfaceCode


class QECFramework:
    """Factory helper for common QEC workflows."""

    def create_surface_code(self, distance: int = 3) -> SurfaceCode:
        return SurfaceCode(distance=distance)

    def create_ldpc_code(self, n: int = 100, k: int = 50, d: int = 10) -> LDPCCode:
        return LDPCCode(n=n, k=k, d=d)


__all__ = [
    "QECFramework",
    "SurfaceCode",
    "LDPCCode",
    "EncodedState",
    "LDPCDecoder",
    "LDPCEncoder",
]
