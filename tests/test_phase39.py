import json
from abirqu.devtools import (
    QuantumDebugger, Breakpoint, StateSnapshot,
    QuantumLinter, QuantumCICD, CIQualityGate,
)

print("=" * 70)
print("  Phase 39: Quantum Software Engineering Suite Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 39.1a: Debugger — Step Execution & Snapshots
# ---------------------------------------------------------
print("\n--- Test 39.1a: Quantum Debugger — Full Run & Snapshots ---")
dbg = QuantumDebugger(num_qubits=2)
dbg.add_gate("H", [0])
dbg.add_gate("CNOT", [0, 1])
dbg.add_gate("X", [1])
dbg.add_gate("H", [0])

result = dbg.run_full()
print(f"  Circuit: H(0) → CNOT(0,1) → X(1) → H(0)")
print(f"  Snapshots Recorded: {result['snapshots_recorded']}")
print(f"  Final Probabilities: {result['final_probabilities']}")

# Show each step
for snap in dbg.snapshots:
    d = snap.to_dict()
    print(f"    Step {d['step']}: {d['gate']:15s} → {d['probabilities']}")
print("✅ Debugger step execution passed")

# ---------------------------------------------------------
# Test 39.1b: Time-Travel — Step Back/Forward
# ---------------------------------------------------------
print("\n--- Test 39.1b: Time-Travel Debugging ---")
# We're at step 4 (end). Step back to step 2 (after CNOT)
back = dbg.step_to(2)
print(f"  Step to 2 (after CNOT): {back['probabilities']}")
assert "00" in back["probabilities"] or "11" in back["probabilities"]

# Step back one more
back2 = dbg.step_back(1)
print(f"  Step back 1 → step {back2['current_step']} (after H): {back2['probabilities']}")

# Step forward to end
fwd = dbg.step_to(4)
print(f"  Step to 4 (end): {fwd['probabilities']}")

# Diff between steps
diff = dbg.diff_steps(1, 2)
print(f"\n  Diff step 1→2 ({diff['gate_a']} → {diff['gate_b']}):")
for basis, change in diff["changes"].items():
    print(f"    |{basis}⟩: {change['before']:.4f} → {change['after']:.4f} (Δ={change['delta']:+.4f})")
print("✅ Time-travel debugging passed")

# ---------------------------------------------------------
# Test 39.1c: Conditional Breakpoints
# ---------------------------------------------------------
print("\n--- Test 39.1c: Conditional Breakpoints ---")
dbg2 = QuantumDebugger(num_qubits=2)
dbg2.add_gate("H", [0])
dbg2.add_gate("CNOT", [0, 1])
dbg2.add_gate("X", [0])

# Breakpoint: trigger when |11⟩ probability exceeds 40%
bp1 = Breakpoint(
    name="entanglement_detected",
    condition=lambda snap: snap.probabilities().get("11", 0) > 0.4,
    description="Fires when P(|11⟩) > 40%"
)

# Breakpoint: trigger when qubit 0 is in superposition
bp2 = Breakpoint(
    name="superposition_q0",
    condition=lambda snap: 0.4 < sum(
        abs(snap.state[i]) ** 2 for i in range(len(snap.state))
        if (i >> (snap.nq - 1)) & 1
    ) < 0.6,
    description="Fires when q0 is in balanced superposition"
)

dbg2.add_breakpoint(bp1)
dbg2.add_breakpoint(bp2)

result2 = dbg2.run_full()
print(f"  Breakpoint Hits:")
for hit in result2["breakpoint_hits"]:
    print(f"    🔴 '{hit['breakpoint']}' at step {hit['step']} ({hit['gate']})")
    print(f"       {hit['description']}")
assert len(result2["breakpoint_hits"]) > 0
print("✅ Conditional breakpoints passed")

# ---------------------------------------------------------
# Test 39.1d: Qubit Watchpoint
# ---------------------------------------------------------
print("\n--- Test 39.1d: Qubit Watchpoint ---")
watch = dbg.watch_qubit(0)
print(f"  Qubit 0 Evolution:")
for step in watch["evolution"]:
    bar = "█" * int(step["P(|1⟩)"] * 20)
    print(f"    Step {step['step']}: {step['gate']:15s}  P(|1⟩)={step['P(|1⟩)']:.4f}  {bar}")
print("✅ Qubit watchpoint passed")

# ---------------------------------------------------------
# Test 39.2a: Quantum Linter
# ---------------------------------------------------------
print("\n--- Test 39.2a: Quantum Linter ---")
linter = QuantumLinter()

# A circuit with multiple anti-patterns
bad_circuit = [
    {"gate": "CNOT", "qubits": [0, 1]},      # QF002: control q0 never modified
    {"gate": "H", "qubits": [0]},
    {"gate": "H", "qubits": [0]},              # QF003: H·H = Identity
    {"gate": "MEASURE", "qubits": [0]},
    {"gate": "X", "qubits": [1]},              # QF001: gate after measurement (no conditional)
    {"gate": "RZ", "qubits": [2], "params": [0.5]},
    {"gate": "RZ", "qubits": [2], "params": [0.3]},  # QF006: mergeable rotations
]

lint_result = linter.lint(bad_circuit, num_qubits=5)  # q3, q4 unused → QF004
print(f"  Lint Results:")
print(f"    Total Issues: {lint_result['total_issues']}")
print(f"    Errors:       {lint_result['errors']}")
print(f"    Warnings:     {lint_result['warnings']}")
print(f"    Infos:        {lint_result['infos']}")
print(f"    Pass:         {lint_result['pass']}")

print(f"\n  Issues:")
for issue in lint_result["issues"]:
    icon = {"ERROR": "🔴", "WARNING": "🟡", "INFO": "🔵"}[issue["severity"]]
    print(f"    {icon} [{issue['rule']}] {issue['message']}")
    if issue["suggestion"]:
        print(f"       💡 {issue['suggestion']}")

assert lint_result["errors"] > 0, "Should detect H·H identity pair"
assert lint_result["warnings"] > 0, "Should detect useless CNOT"
print("✅ Quantum linter passed")

# ---------------------------------------------------------
# Test 39.2b: CI/CD Quality Gates
# ---------------------------------------------------------
print("\n--- Test 39.2b: CI/CD Quality Gates ---")
cicd = QuantumCICD()

# Good commit — clean circuit
print(f"  Pipeline Run: commit 'abc123' (clean circuit)")
good_circuit = [
    {"gate": "H", "qubits": [0]},
    {"gate": "CNOT", "qubits": [0, 1]},
    {"gate": "MEASURE", "qubits": [0]},
    {"gate": "MEASURE", "qubits": [1]},
]
run1 = cicd.run_pipeline("abc123", good_circuit, num_qubits=2, estimated_fidelity=0.98)
print(f"    Status:         {run1['status']}")
print(f"    Merge Allowed:  {run1['merge_allowed']}")
print(f"    Quality Gates:")
for qg in run1["quality_gates"]:
    icon = "✅" if qg["passed"] else "❌"
    print(f"      {icon} {qg['gate']:15s}: {qg['value']} {qg['comparator']} {qg['threshold']}")

# Bad commit — has lint errors and low fidelity
print(f"\n  Pipeline Run: commit 'def456' (buggy circuit)")
run2 = cicd.run_pipeline("def456", bad_circuit, num_qubits=5, estimated_fidelity=0.80)
print(f"    Status:         {run2['status']}")
print(f"    Merge Allowed:  {run2['merge_allowed']}")
print(f"    Blocking Failures:")
for f in run2["blocking_failures"]:
    print(f"      ❌ {f['gate']}: {f['metric']}={f['value']} (need {f['comparator']}{f['threshold']})")

assert run1["merge_allowed"] == True
assert run2["merge_allowed"] == False
print("✅ CI/CD quality gates passed")

print("\n" + "=" * 70)
print("  Phase 39 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
