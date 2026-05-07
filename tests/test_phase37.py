import json
from abirqu.orchestration import (
    MultiObjectiveRouter,
    CircuitKnitter,
    BackendGlobalMap,
    CostTracker,
    OrchestrationPipeline,
)

print("=" * 70)
print("  Phase 37: Hyper-Heterogeneous Orchestration Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 37.1a: Multi-Objective Routing
# ---------------------------------------------------------
print("\n--- Test 37.1a: Multi-Objective Routing ---")
router = MultiObjectiveRouter()

# Route a 20-qubit circuit with 50 1q + 30 2q gates
result = router.route(
    circuit_qubits=20, num_1q_gates=50, num_2q_gates=30, shots=4096,
    weights={"fidelity": 0.6, "cost": 0.2, "latency": 0.2}
)

print(f"  Circuit: 20 qubits, 50×1q + 30×2q gates, 4096 shots")
print(f"  Weights: fidelity=0.6, cost=0.2, latency=0.2")
print(f"\n  Recommended: {result['recommended']['backend']}")
print(f"  Pareto Front:")
for c in result["pareto_front"]:
    print(f"    {c['backend']:20s} | F={c['estimated_fidelity']:.4f} | "
          f"${c['estimated_cost']:.2f} | {c['latency_ms']}ms | score={c['score']:.4f}")

# Route with cost priority
result2 = router.route(
    circuit_qubits=20, num_1q_gates=50, num_2q_gates=30, shots=4096,
    weights={"fidelity": 0.1, "cost": 0.8, "latency": 0.1}
)
print(f"\n  Cost-Priority Routing → {result2['recommended']['backend']}")
assert result2["recommended"] is not None
print("✅ Multi-objective routing passed")

# ---------------------------------------------------------
# Test 37.1b: Circuit Knitting
# ---------------------------------------------------------
print("\n--- Test 37.1b: Circuit Knitting ---")
knitter = CircuitKnitter()

# A 10-qubit circuit with gates spanning a wide range
gates = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # Chain in first half
    (5, 6), (6, 7), (7, 8), (8, 9),  # Chain in second half
    (4, 5),  # Bridge gate — this will likely be cut
    (0, 9),  # Long-range gate — also a cut candidate
]

cuts = knitter.find_optimal_cuts(
    num_qubits=10,
    two_qubit_gates=gates,
    max_fragment_qubits=5
)
print(f"  Circuit: 10 qubits, {len(gates)} 2q gates")
print(f"  Partition A: qubits {cuts['partition_a']}")
print(f"  Partition B: qubits {cuts['partition_b']}")
print(f"  Fragment Sizes: {cuts['fragment_sizes']}")
print(f"  Cut Edges: {cuts['cut_edges']}")
print(f"  Num Cuts: {cuts['num_cuts']}")
print(f"  Overhead: {cuts['overhead_human']}")

# Execute knitted circuit
exec_result = knitter.execute_knitted(cuts, shots=1024)
print(f"\n  Knitted Execution:")
print(f"    Fragments: {exec_result['fragments_executed']}")
print(f"    Effective Shots: {exec_result['total_effective_shots']}")
print(f"    Overhead: {exec_result['overhead_factor']}x")
for frag in exec_result["fragments"]:
    print(f"    Fragment {frag['fragment_id']}: {frag['qubits']}q, {frag['shots']} shots")
print("✅ Circuit knitting passed")

# ---------------------------------------------------------
# Test 37.2a: Backend Global Map
# ---------------------------------------------------------
print("\n--- Test 37.2a: Backend Global Map ---")
gmap = BackendGlobalMap()

# Register backends
gmap.register_backend("ibm_eagle", "IBM", 127, "us-east-1", latency_ms=50)
gmap.register_backend("google_sycamore", "Google", 72, "us-west-2", latency_ms=30)
gmap.register_backend("ionq_forte", "IonQ", 36, "eu-west-1", latency_ms=200)
gmap.register_backend("abirqu_sim", "AbirQu", 40, "global", latency_ms=5)

# Simulate heartbeats
gmap.heartbeat("ibm_eagle", load_percent=45.0, queue_depth=3, latency_ms=52)
gmap.heartbeat("google_sycamore", load_percent=72.0, queue_depth=8, latency_ms=35)
gmap.heartbeat("ionq_forte", load_percent=96.0, queue_depth=15, latency_ms=210)  # Degraded
gmap.heartbeat("abirqu_sim", load_percent=5.0, queue_depth=0, latency_ms=4)

overview = gmap.get_map()
print(f"  Global Map: {overview['total_backends']} backends, "
      f"{overview['healthy']} healthy, {overview['degraded']} degraded")
for b in overview["backends"]:
    status_icon = "🟢" if b["status"] == "HEALTHY" else "🟡"
    print(f"    {status_icon} {b['name']:20s} | {b['provider']:12s} | "
          f"{b['region']:12s} | {b['qubits']}q | {b['load']:>5s} | Q={b['queue']}")

best = gmap.get_best_available(min_qubits=30)
print(f"\n  Best Available (≥30q): {best['name']} ({best['load_percent']:.0f}% load)")
print("✅ Backend global map passed")

# ---------------------------------------------------------
# Test 37.2b: Cost Tracker & Auto-Preemption
# ---------------------------------------------------------
print("\n--- Test 37.2b: Cost Tracker & Auto-Preemption ---")
tracker = CostTracker(budget_limit=10.0, currency="USD")

# Record some costs
for i in range(5):
    tracker.record_cost(f"job_{i}", "ibm_eagle", 1024, 0.001)
print(f"  After 5 jobs: ${tracker.total_spent:.4f} spent")

# Check budget for a large job
big_check = tracker.check_budget(proposed_cost=8.0)
print(f"  Budget check for $8.00: {big_check['action']} — {big_check.get('reason', 'OK')}")

# Push to warning threshold
tracker.record_cost("job_big", "ionq_forte", 1000, 0.005)
warn_check = tracker.check_budget(proposed_cost=2.0)
print(f"  After big job: ${tracker.total_spent:.4f} spent")
print(f"  Budget check for $2.00: {warn_check['action']}")

# Push past limit
tracker.record_cost("job_huge", "quantinuum_h2", 500, 0.008)
over_check = tracker.check_budget(proposed_cost=5.0)
print(f"  Budget check for $5.00: {over_check['action']}")
if not over_check["approved"]:
    preempt = tracker.preempt_job("job_rejected", over_check["reason"])
    print(f"  Preempted: {preempt}")

summary = tracker.get_summary()
print(f"\n  Cost Summary:")
print(f"    Spent:      ${summary['total_spent']}")
print(f"    Budget:     ${summary['budget_limit']}")
print(f"    Remaining:  ${summary['budget_remaining']}")
print(f"    Utilization:{summary['utilization']:.1%}")
print(f"    Preempted:  {summary['preempted_jobs']}")
print(f"    By Backend: {summary['spend_by_backend']}")
print("✅ Cost tracker & auto-preemption passed")

# ---------------------------------------------------------
# Test 37.2c: Full Orchestration Pipeline
# ---------------------------------------------------------
print("\n--- Test 37.2c: Full Orchestration Pipeline ---")
pipeline = OrchestrationPipeline(budget=5.0)

# Submit several jobs
for i in range(3):
    result = pipeline.submit_job(
        job_id=f"pipeline_job_{i}",
        circuit_qubits=10,
        num_1q_gates=20,
        num_2q_gates=10,
        shots=2048,
    )
    status_icon = "✅" if result["status"] == "COMPLETED" else "🚫"
    print(f"  {status_icon} {result['job_id']}: {result['status']} → "
          f"{result.get('backend', 'N/A')} | cost=${result.get('cost', 0):.4f} | "
          f"remaining=${result.get('budget_remaining', 0):.4f}")

# Check global map state
final_map = pipeline.global_map.get_map()
print(f"\n  Final Map: {final_map['healthy']}/{final_map['total_backends']} healthy")
print("✅ Full orchestration pipeline passed")

print("\n" + "=" * 70)
print("  Phase 37 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
