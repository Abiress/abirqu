"""Clifford/stabilizer simulation entry points."""


def is_clifford_only(circuit):
    """Best-effort check for Clifford-only gate set."""
    names = {getattr(g, "name", "").upper() for g in getattr(circuit, "gates", [])}
    return names.issubset({"H", "S", "SDG", "X", "Y", "Z", "CX", "CNOT", "CZ", "SWAP"})
