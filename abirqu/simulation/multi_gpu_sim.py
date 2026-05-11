"""Multi-GPU simulation orchestration hooks."""


def split_statevector_length(total_length, device_count):
    """Return per-device shard lengths."""
    device_count = max(1, device_count)
    base = total_length // device_count
    rem = total_length % device_count
    return [base + (1 if i < rem else 0) for i in range(device_count)]
