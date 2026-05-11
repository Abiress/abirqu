"""Approximate simulation methods for large circuits."""


def simulate_approximate(circuit, *, tolerance=1e-3):
    """Placeholder approximate simulator that returns metadata."""
    return {"status": "not-implemented", "tolerance": tolerance, "gates": len(getattr(circuit, "gates", []))}
