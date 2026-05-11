"""
Quantum Error Correction — Surface Code & LDPC
=================================================
Fault-tolerant quantum computing requires error correction to protect
logical qubits from physical noise. This example demonstrates:

  1. Surface code encoding and syndrome measurement
  2. LDPC (Low-Density Parity-Check) code — used in India's QCI mission
  3. Code rate and overhead comparison

Reference: AbirQu Phase 40 — Fault-Tolerant Quantum Computing
"""
import random
import numpy as np
from abirqu.qec import SurfaceCode, LDPCCode, LDPCDecoder, LDPCEncoder


# ─────────────────────────────────────────────────────────────
# 1. Surface Code
# ─────────────────────────────────────────────────────────────

def demo_surface_code(distance: int = 3) -> None:
    print(f"\n=== Surface Code (distance={distance}) ===")
    sc = SurfaceCode(distance=distance)

    print(f"  Physical qubits : {sc.physical_qubits}")
    print(f"  Logical qubits  : {sc.logical_qubits}")
    print(f"  Overhead        : {sc.get_overhead()}× physical per logical")
    print(f"  Error threshold : ~1% physical error rate")

    # Encode logical |0⟩ state
    logical_state = [1, 0]  # |0⟩
    encoded = sc.encode(logical_state)
    print(f"\n  Encoded |0⟩ → {len(encoded)}-qubit physical state")
    print(f"  State (first 8 bits): {encoded[:8].tolist()}")

    # Syndrome measurement (no errors → all syndromes = 0)
    syndromes = sc.syndrome_measurement(encoded)
    n_errors = int(np.sum(syndromes))
    print(f"\n  Syndrome measurement: {syndromes[:8].tolist()}...")
    print(f"  Errors detected: {n_errors} (0 = clean state)")

    # Inject a synthetic error and re-measure
    corrupted = encoded.copy()
    if len(corrupted) > 2:
        corrupted[2] ^= 1  # Flip bit 2 (X error)
    syndromes_noisy = sc.syndrome_measurement(corrupted)
    n_errors_noisy = int(np.sum(syndromes_noisy))
    print(f"\n  After injecting X error on qubit 2:")
    print(f"  Syndromes (first 8): {syndromes_noisy[:8].tolist()}")
    print(f"  Errors flagged: {n_errors_noisy}")

    # Logical operators
    X_L, Z_L = sc.logical_operators()
    print(f"\n  Logical X operator weight: {int(np.sum(X_L))}")
    print(f"  Logical Z operator weight: {int(np.sum(Z_L))}")


# ─────────────────────────────────────────────────────────────
# 2. LDPC Code (Indian QCI mission focus)
# ─────────────────────────────────────────────────────────────

def demo_ldpc(n: int = 15, k: int = 7, d: int = 5) -> None:
    print(f"\n=== LDPC Code (n={n}, k={k}, d={d}) ===")
    code = LDPCCode(n=n, k=k, d=d)

    print(f"  Block length     : {code.n}")
    print(f"  Message length   : {code.k}")
    print(f"  Distance         : {code.d}")
    print(f"  Code rate        : {code.get_rate():.3f}")
    print(f"  Overhead         : {code.estimate_overhead():.2f}×")
    print(f"  H matrix shape   : {code.H.shape}")
    print(f"  G matrix shape   : {code.G.shape}")

    # Encode a random message
    encoder = LDPCEncoder()
    encoder.load_code(code)
    message = [random.randint(0, 1) for _ in range(code.k)]
    codeword = encoder.encode(message)
    print(f"\n  Message  ({k} bits): {message}")
    print(f"  Codeword ({n} bits): {codeword}")

    # Decode (no noise)
    decoder = LDPCDecoder()
    decoder.load_code(code)
    decoded = decoder.decode(codeword)
    match = decoded[:k] == message
    print(f"\n  Decoded  ({k} bits): {decoded[:k]}")
    print(f"  Decode success: {match}")

    # Decode with noise
    noisy = list(codeword)
    flip_idx = random.randint(0, n - 1)
    noisy[flip_idx] ^= 1
    decoded_noisy = decoder.decode(noisy)
    match_noisy = decoded_noisy[:k] == message
    print(f"\n  After flipping bit {flip_idx}:")
    print(f"  Decoded: {decoded_noisy[:k]}")
    print(f"  Corrected successfully: {match_noisy}")


# ─────────────────────────────────────────────────────────────
# 3. Code comparison
# ─────────────────────────────────────────────────────────────

def compare_codes() -> None:
    print("\n=== Error Correction Code Comparison ===\n")
    print(f"  {'Code':<25} {'Phys/Logical':<15} {'Rate':<10} {'Distance'}")
    print("  " + "─" * 60)

    for d in [3, 5, 7]:
        sc = SurfaceCode(distance=d)
        overhead = sc.get_overhead()
        rate = 1.0 / overhead if overhead else 0.0
        print(f"  {'Surface Code d=' + str(d):<25} {overhead:<15} {rate:<10.4f} {d}")

    for cfg in [(15, 7, 5), (30, 15, 6), (100, 50, 10)]:
        n, k, d = cfg
        lc = LDPCCode(n=n, k=k, d=d)
        rate = lc.get_rate()
        print(f"  {'LDPC (' + str(n) + ',' + str(k) + ')':<25} {n/k:<15.2f} {rate:<10.4f} {d}")

    print()
    print("  LDPC codes achieve much higher code rates than surface codes,")
    print("  making them suitable for quantum communication and storage.")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AbirQu — Quantum Error Correction")
    print("===================================")

    random.seed(42)

    demo_surface_code(distance=3)
    demo_ldpc(n=15, k=7, d=5)
    compare_codes()

    print("\nDone! Try examples/distributed_sim.py next.")
