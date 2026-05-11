"""Matrix Product State simulation helpers."""


def estimate_bond_dimension(num_qubits, entanglement_level=0.5):
    """Heuristic MPS bond dimension estimator."""
    return max(2, int((2 ** (num_qubits / 4)) * max(0.1, entanglement_level)))
