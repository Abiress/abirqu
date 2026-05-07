import json
import math
from abirqu.compression import (
    SparseStateVector,
    NVMeStateMapper,
    LazyAmplitudeEvaluator,
    WignerFunctionComputer,
)

print("=" * 70)
print("  Phase 40: Extreme-Scale State Compression Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 40.1a: Sparse State Vector
# ---------------------------------------------------------
print("\n--- Test 40.1a: Sparse State Vector ---")
sparse = SparseStateVector(num_qubits=20)

# Initially |0...0⟩ — only 1 entry
stats = sparse.stats()
print(f"  Initial State (20 qubits):")
print(f"    Hilbert Dim:      {stats['hilbert_dim']:,}")
print(f"    Non-Zero Entries: {stats['non_zero_entries']}")
print(f"    Sparse Memory:    {stats['sparse_memory']}")
print(f"    Dense Memory:     {stats['dense_memory']}")
print(f"    Compression:      {stats['compression_ratio']}")

# Apply H to qubit 0 (creates 2 entries)
sparse.apply_h(0)
print(f"\n  After H(0): {sparse.nnz} entries, density={sparse.density:.8f}")

# Apply CNOT(0,1) — still 2 entries (entangled)
sparse.apply_cnot(0, 1)
print(f"  After CNOT(0,1): {sparse.nnz} entries")
probs = sparse.probabilities()
print(f"  Probabilities: {probs}")
assert abs(sum(probs.values()) - 1.0) < 1e-6, "Probabilities should sum to 1"

# Apply H to all 20 qubits (creates 2^20 entries — goes dense)
sparse2 = SparseStateVector(num_qubits=10)
for q in range(10):
    sparse2.apply_h(q)
stats2 = sparse2.stats()
print(f"\n  After H on all 10 qubits:")
print(f"    Non-Zero: {stats2['non_zero_entries']}")
print(f"    Density:  {stats2['density']}")
print(f"    Compression: {stats2['compression_ratio']}")
print(f"    Norm:     {stats2['norm']}")
assert abs(sparse2.norm() - 1.0) < 1e-6
print("✅ Sparse state vector passed")

# ---------------------------------------------------------
# Test 40.1b: NVMe Memory-Mapped State
# ---------------------------------------------------------
print("\n--- Test 40.1b: NVMe Memory-Mapped State ---")

# Small state — real mmap
mapper_small = NVMeStateMapper(num_qubits=10)
open_result = mapper_small.open()
print(f"  Small State (10 qubits):")
print(f"    File:     {open_result['file']}")
print(f"    Size:     {open_result['total_size']}")
print(f"    Mode:     {open_result['mode']}")

# Read initial state
amp_0 = mapper_small.read_amplitude(0)
amp_1 = mapper_small.read_amplitude(1)
print(f"    |0...0⟩ amplitude: {amp_0}")
print(f"    |0...1⟩ amplitude: {amp_1}")
assert abs(amp_0 - complex(1, 0)) < 1e-6

# Write and read back
mapper_small.write_amplitude(42, complex(0.5, 0.3))
readback = mapper_small.read_amplitude(42)
print(f"    Write(42, 0.5+0.3j) → Read: {readback}")
assert abs(readback - complex(0.5, 0.3)) < 1e-6

mapper_small.close()
print(f"  ✅ Small mmap passed")

# Large state — simulated (50 qubits = 16 PB)
print(f"\n  Large State (50 qubits):")
mapper_large = NVMeStateMapper(num_qubits=50)
open_large = mapper_large.open()
print(f"    Size:     {open_large['total_size']}")
print(f"    Mode:     {open_large['mode']}")

stats_large = mapper_large.stats()
print(f"    Hilbert:  {stats_large['hilbert_dim']}")
print(f"    State Size: {stats_large['total_state_size']}")

# Write/read in simulated mode
mapper_large.write_amplitude(0, complex(1, 0))
mapper_large.write_amplitude(1099511627775, complex(0.7, 0.1))  # Near max
amp = mapper_large.read_amplitude(1099511627775)
print(f"    Write & Read at address 2^40-1: {amp}")
assert abs(amp - complex(0.7, 0.1)) < 1e-6
mapper_large.close()
print("✅ NVMe memory-mapped state passed")

# ---------------------------------------------------------
# Test 40.2a: Lazy Amplitude Evaluation
# ---------------------------------------------------------
print("\n--- Test 40.2a: Lazy Amplitude Evaluation ---")
lazy = LazyAmplitudeEvaluator(num_qubits=3)
lazy.add_gate("H", [0])
lazy.add_gate("CNOT", [0, 1])
lazy.add_gate("CNOT", [1, 2])

# Evaluate specific amplitudes without full state vector
print(f"  GHZ Circuit: H(0) → CNOT(0,1) → CNOT(1,2)")
for state in [0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111]:
    amp = lazy.evaluate_amplitude(state)
    prob = abs(amp) ** 2
    label = format(state, "03b")
    bar = "█" * int(prob * 40)
    print(f"    |{label}⟩: amp={amp.real:+.4f}{amp.imag:+.4f}j  P={prob:.4f}  {bar}")

# Only |000⟩ and |111⟩ should have non-zero probability (GHZ state)
p000 = lazy.evaluate_probability(0b000)
p111 = lazy.evaluate_probability(0b111)
assert abs(p000 - 0.5) < 1e-6, f"P(|000⟩) should be 0.5, got {p000}"
assert abs(p111 - 0.5) < 1e-6, f"P(|111⟩) should be 0.5, got {p111}"
print(f"\n  Evaluations performed: {lazy._eval_count}")
print("✅ Lazy amplitude evaluation passed")

# ---------------------------------------------------------
# Test 40.2b: Progressive Wigner Function
# ---------------------------------------------------------
print("\n--- Test 40.2b: Progressive Wigner Function ---")

# Single-qubit |+⟩ state: Bloch vector r = (1, 0, 0)
# The Stratonovich-Weyl kernel W = (1/4π)(1 + √3 r·n) goes negative
# at the antipodal point n = (-1, 0, 0), i.e. θ=π/2, φ=π.
wigner_1q = WignerFunctionComputer(num_qubits=1, grid_points=11)
state_plus = [complex(1 / math.sqrt(2)), complex(1 / math.sqrt(2))]  # |+⟩

print(f"  |+⟩ State (single qubit, Bloch vector = (1,0,0)):")
refinements = wigner_1q.refine(state_plus, qubit=0)
for r in refinements:
    print(f"    Resolution {r['resolution']}: {r['grid_size']} grid, "
          f"{r['points_computed']} points, "
          f"cache={r['cache_reuse']}, "
          f"min_W={r['min_W']:.4f}, "
          f"non-classical={'YES ⚡' if r['non_classical'] else 'no'}")

finest_1q = wigner_1q.compute_progressive(state_plus, resolution=4, qubit=0)
print(f"\n  Finest Grid ({finest_1q['grid_size']}):")
print(f"    Min W:         {finest_1q['min_value']}")
print(f"    Max W:         {finest_1q['max_value']}")
print(f"    Non-Classical: {finest_1q['non_classical']}")
assert finest_1q["non_classical"], "|+⟩ must have negative Wigner values at antipode"

# Multi-qubit: Bell state reduced density matrix is maximally mixed
# (Bloch vector = 0), so single-qubit Wigner is uniform — that's physics!
wigner_2q = WignerFunctionComputer(num_qubits=2, grid_points=11)
bell = [complex(0)] * 4
bell[0] = complex(1 / math.sqrt(2))
bell[3] = complex(1 / math.sqrt(2))

finest_bell = wigner_2q.compute_progressive(bell, resolution=4, qubit=0)
print(f"\n  Bell State reduced q0 (maximally mixed):")
print(f"    Min W: {finest_bell['min_value']}, Max W: {finest_bell['max_value']}")
print(f"    Non-Classical: {finest_bell['non_classical']} (expected: maximally mixed = uniform)")
print("✅ Progressive Wigner function passed")

print("\n" + "=" * 70)
print("  Phase 40 — ALL TESTS PASSED SUCCESSFULLY  🎉")
print("  ╔═══════════════════════════════════════════╗")
print("  ║  ALL 40 PHASES COMPLETE — AbirQu v2.0.0  ║")
print("  ╚═══════════════════════════════════════════╝")
print("=" * 70)
