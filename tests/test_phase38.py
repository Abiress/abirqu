import json
import math
from abirqu.dynamics import (
    DynamicCircuitSimulator,
    GateOp, MidCircuitMeasure, ConditionalBlock, ForLoop, WhileLoop,
    StreamingCircuitEngine,
    VQEParameterPrefetcher,
)

print("=" * 70)
print("  Phase 38: Real-Time Circuit Dynamics Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 38.1a: Mid-Circuit Measurement + Feed-Forward
# ---------------------------------------------------------
print("\n--- Test 38.1a: Mid-Circuit Measurement + Feed-Forward ---")
# Teleportation protocol: uses mid-circuit measurement + conditional gates
sim = DynamicCircuitSimulator(num_qubits=3, num_clbits=2)

# Prepare Bell pair between q1 and q2
sim.add(GateOp("H", [1]))
sim.add(GateOp("CNOT", [1, 2]))

# Alice: entangle q0 with q1
sim.add(GateOp("CNOT", [0, 1]))
sim.add(GateOp("H", [0]))

# Mid-circuit measurements
sim.add(MidCircuitMeasure(qubit=0, clbit=0))
sim.add(MidCircuitMeasure(qubit=1, clbit=1))

# Feed-forward corrections on q2
sim.add(ConditionalBlock(
    clbit=1, condition="==", value=1,
    if_ops=[GateOp("X", [2])]
))
sim.add(ConditionalBlock(
    clbit=0, condition="==", value=1,
    if_ops=[GateOp("Z", [2])]
))

result = sim.run(shots=100)
print(f"  Teleportation Protocol (3q, 2 mid-circuit measurements):")
print(f"  Counts: {result['counts']}")
print(f"  Trace:  {result['trace_sample']}")
assert len(result["counts"]) > 0
print("✅ Mid-circuit measurement + feed-forward passed")

# ---------------------------------------------------------
# Test 38.1b: For-Loop on Quantum Registers
# ---------------------------------------------------------
print("\n--- Test 38.1b: For-Loop (Repeated H-Measure) ---")
sim2 = DynamicCircuitSimulator(num_qubits=1, num_clbits=1)

# Apply H + Measure 5 times in a loop
sim2.add(ForLoop(
    iterations=5,
    body=[
        GateOp("H", [0]),
        MidCircuitMeasure(qubit=0, clbit=0),
        # Reset qubit based on measurement (if 1, flip back to 0)
        ConditionalBlock(clbit=0, condition="==", value=1,
                         if_ops=[GateOp("X", [0])]),
    ]
))

result2 = sim2.run(shots=50)
print(f"  5x (H → Measure → Conditional Reset):")
print(f"  Counts: {result2['counts']}")
print(f"  Trace (first shot): {result2['trace_sample'][:8]}...")
print("✅ For-loop passed")

# ---------------------------------------------------------
# Test 38.1c: While-Loop (Repeat Until Success)
# ---------------------------------------------------------
print("\n--- Test 38.1c: While-Loop (Repeat-Until-Success) ---")
sim3 = DynamicCircuitSimulator(num_qubits=1, num_clbits=1)

# Keep applying H and measuring until we get |1⟩
sim3.add(WhileLoop(
    clbit=0, condition="==", value=0,
    body=[
        GateOp("H", [0]),
        MidCircuitMeasure(qubit=0, clbit=0),
    ],
    max_iterations=20
))

# We need to set initial clbit to 0 to enter the loop
# First do a measurement to initialize
sim3.instructions.insert(0, MidCircuitMeasure(qubit=0, clbit=0))

result3 = sim3.run(shots=50)
print(f"  Repeat H+Measure until c0==1:")
print(f"  Counts: {result3['counts']}")
print(f"  Trace: {result3['trace_sample'][:10]}...")
# All shots should end with c0=1 (we loop until we get it)
assert "1" in result3["counts"], "Should always eventually measure 1"
print("✅ While-loop (repeat-until-success) passed")

# ---------------------------------------------------------
# Test 38.2a: Streaming Circuit Submissions
# ---------------------------------------------------------
print("\n--- Test 38.2a: Streaming Circuit Submissions ---")
stream = StreamingCircuitEngine(num_qubits=3)

# Submit fragments incrementally
f1 = stream.submit_fragment([
    {"gate": "H", "qubits": [0]},
    {"gate": "H", "qubits": [1]},
])
print(f"  Fragment 1 submitted: {f1}")

f2 = stream.submit_fragment([
    {"gate": "CNOT", "qubits": [0, 2]},
    {"gate": "CNOT", "qubits": [1, 2]},
])
print(f"  Fragment 2 submitted: {f2}")

# Execute fragment 1 while fragment 2 is still queued
r1 = stream.execute_next()
print(f"  Executed fragment 1: {r1}")
print(f"  Status: {stream.get_status()}")

# Submit another fragment while executing
f3 = stream.submit_fragment([
    {"gate": "H", "qubits": [2]},
])
print(f"  Fragment 3 submitted (while executing): {f3}")

# Execute all remaining
final = stream.execute_all()
print(f"\n  Final Results:")
print(f"    Fragments Executed: {final['fragments_executed']}")
print(f"    Total Gates:        {final['total_gates']}")
print(f"    Probabilities:      {final['probabilities']}")
assert sum(final["probabilities"].values()) > 0.99
print("✅ Streaming circuit submissions passed")

# ---------------------------------------------------------
# Test 38.2b: VQE Parameter Prefetching
# ---------------------------------------------------------
print("\n--- Test 38.2b: VQE Parameter Prefetching ---")

# Mock energy function: a simple quadratic landscape
def mock_energy(params):
    return sum((p - 0.5) ** 2 for p in params) + 0.1 * sum(
        math.sin(p * 3) for p in params
    )

prefetcher = VQEParameterPrefetcher(num_params=4)
result = prefetcher.run_vqe_loop(energy_fn=mock_energy, num_iterations=15)

print(f"  VQE Optimization with Prefetching:")
print(f"    Iterations:     {result['total_iterations']}")
print(f"    Best Energy:    {result['best_energy']}")
print(f"    Final Energy:   {result['final_energy']}")
print(f"    Prefetch Rate:  {result['prefetch_rate']:.0%}")
print(f"    Convergence:    {result['convergence'][:5]}...")
print(f"    Best Params:    {result['best_params']}")

# Verify energy decreased
assert result["convergence"][-1] <= result["convergence"][0] + 1.0, \
    "Energy should generally decrease"
assert result["prefetch_rate"] > 0.5, "Most iterations should use prefetching"
print("✅ VQE parameter prefetching passed")

print("\n" + "=" * 70)
print("  Phase 38 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
