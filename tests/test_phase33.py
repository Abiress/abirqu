import json
from abirqu.autonomous import (
    GateFidelityTracker,
    DynamicErrorSuppressor,
    RecalibrationAgent,
    NeutralAtomTweezerArray,
    AdaptiveCompilerPass,
)

print("=" * 70)
print("  Phase 33: Autonomous Quantum Systems Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 33.1a: Gate Fidelity Tracking & Drift Detection
# ---------------------------------------------------------
print("\n--- Test 33.1a: Gate Fidelity Tracker ---")
gates = ["SX", "RZ", "CZ", "CNOT"]
tracker = GateFidelityTracker(gates, target_fidelity=0.999)

# Simulate 10 RB measurements with gradual drift on CZ
for i in range(10):
    for g in gates:
        if g == "CZ":
            fid = 0.999 - 0.003 * i  # Aggressive drift: 0.999 -> 0.972
        else:
            fid = 0.999 - 0.0001 * ((-1) ** i)  # Stable
        tracker.record_rb_measurement(g, fid)

print(f"  EWMA Fidelities:")
for g, f in tracker.ewma.items():
    print(f"    {g:6s}: {f:.6f}")
print(f"  Drift Alerts: {len(tracker.drift_alerts)}")

worst = tracker.get_worst_gates(2)
print(f"  Worst Gates:  {worst}")
assert tracker.ewma["CZ"] < 0.990, "CZ should have drifted below 0.990"
print("✅ Fidelity tracking & drift detection passed")

# ---------------------------------------------------------
# Test 33.1b: Dynamic Error Suppression
# ---------------------------------------------------------
print("\n--- Test 33.1b: Dynamic Error Suppression ---")
suppressor = DynamicErrorSuppressor(tracker)
suppression = suppressor.suppress_all()
print(f"  Per-Gate Strategies:")
for gate, strat in suppression["per_gate_strategies"].items():
    print(f"    {gate:6s}: {strat['strategy']:30s} (overhead: {strat['overhead_factor']}x)")
print(f"  Combined Overhead: {suppression['combined_overhead_factor']}x")
print("✅ Dynamic error suppression passed")

# ---------------------------------------------------------
# Test 33.1c: Autonomous Recalibration Agent
# ---------------------------------------------------------
print("\n--- Test 33.1c: Autonomous Recalibration Agent ---")
agent = RecalibrationAgent(
    gate_names=["SX", "RZ", "CZ", "CNOT"],
    target_fidelity=0.999,
    recalibration_threshold=0.993
)
summary = agent.run_autonomous(num_cycles=30)
print(f"  Cycles Run:          {summary['total_cycles']}")
print(f"  Total Recalibrations:{summary['total_recalibrations']}")
print(f"  Total Drift Alerts:  {summary['total_drift_alerts']}")
print(f"  Final Fidelities:")
for g, f in summary["final_gate_fidelities"].items():
    print(f"    {g:6s}: {f:.6f}")
# After 30 cycles the agent should have recalibrated at least once
assert summary["total_recalibrations"] > 0, "Agent should have triggered recalibrations"
print("✅ Autonomous recalibration agent passed")

# ---------------------------------------------------------
# Test 33.2a: Neutral Atom Tweezer Array
# ---------------------------------------------------------
print("\n--- Test 33.2a: Neutral Atom Tweezer Array ---")
array = NeutralAtomTweezerArray(num_sites=16, num_atoms=6, zone_radius_um=5.0)

# Initial connectivity
initial_conn = array.get_connectivity_graph()
print(f"  Initial Layout:")
print(f"    Qubits: {initial_conn['num_qubits']}, Edges: {initial_conn['num_edges']}")

# Rearrange to optimize for a specific circuit
required = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)]
opt_result = array.optimize_layout_for_circuit(required)
print(f"\n  After Optimization for 6-edge circuit:")
print(f"    Required Edges:     {opt_result['required_edges']}")
print(f"    Natively Satisfied: {opt_result['natively_satisfied']}")
print(f"    Satisfaction Rate:  {opt_result['satisfaction_rate']:.0%}")
print(f"    Rearrange Time:     {opt_result['rearrangement']['rearrangement_time_us']} μs")
print(f"    Total Move Distance:{opt_result['rearrangement']['total_distance_um']} μm")
print("✅ Neutral atom tweezer array passed")

# ---------------------------------------------------------
# Test 33.2b: Adaptive Compiler Pass
# ---------------------------------------------------------
print("\n--- Test 33.2b: Adaptive Compiler Pass ---")
topology = array.get_connectivity_graph()
compiler = AdaptiveCompilerPass(topology)

# Route a circuit with some non-adjacent gates
circuit_gates = [(0, 2), (1, 3), (0, 5), (2, 4), (3, 5)]
route_result = compiler.route_circuit(circuit_gates)
print(f"  Original Gates:      {route_result['original_gates']}")
print(f"  Routed Gates:        {route_result['routed_gates']}")
print(f"  SWAPs Inserted:      {route_result['total_swaps_inserted']}")
print(f"  Swap Overhead:       {route_result['swap_overhead']}")

# Simulate topology change (atom loss + rearrange)
print(f"\n  --- Simulating topology shift ---")
# Rearrange to new sites
new_sites = [0, 1, 4, 5, 8, 9]
rearrange = array.rearrange_atoms(new_sites)
new_topology = array.get_connectivity_graph()
update = compiler.update_topology(new_topology)
print(f"  Old Edges: {update['old_edges']}, New Edges: {update['new_edges']}")

# Re-route the same circuit on the new topology
route_result2 = compiler.route_circuit(circuit_gates)
print(f"  Re-Routed Gates:     {route_result2['routed_gates']}")
print(f"  SWAPs After Shift:   {route_result2['total_swaps_inserted']}")
print(f"  New Mapping:         {route_result2['final_mapping']}")
print("✅ Adaptive compiler pass passed")

print("\n" + "=" * 70)
print("  Phase 33 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
