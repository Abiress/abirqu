"""Surface-code specific helpers (high-level wrappers)."""


def estimate_surface_overhead(distance):
    """Return rough physical-qubit overhead for distance-d code."""
    return 2 * distance * distance - 1
