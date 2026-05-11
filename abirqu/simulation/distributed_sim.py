"""Distributed simulation coordinator hooks."""


def partition_qubits(num_qubits, workers):
    """Return contiguous qubit partitions for a worker pool."""
    chunk = max(1, num_qubits // max(1, workers))
    return [(i, min(num_qubits, i + chunk)) for i in range(0, num_qubits, chunk)]
