"""Tensor-network simulation helper functions."""


def contraction_order(num_tensors):
    """Simple left-to-right contraction order."""
    return list(range(max(0, num_tensors)))
