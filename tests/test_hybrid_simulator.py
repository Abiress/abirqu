#!/usr/bin/env python3
"""Test Hybrid MPS-Clifford Simulator for AbirQu SDK."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from abirqu.circuit import Circuit
from abirqu.simulation.hybrid import HybridSimulator, analyze_circuit_segments, CircuitSegment
from abirqu.simulation.clifford import StabilizerTableau


def test_segment_analysis():
    """Test circuit partitioning into Clifford/non-Clifford segments."""
    print("TEST: Circuit segment analysis")

    # All Clifford circuit
    c1 = Circuit(2)
    c1.h(0)
    c1.cx(0, 1)
    c1.s(0)
    segs = analyze_circuit_segments(c1)
    assert len(segs) == 1, f"Expected 1 segment, got {len(segs)}"
    assert segs[0].is_clifford, "Should be Clifford segment"

    # Mixed Clifford/T gate circuit
    c2 = Circuit(2)
    c2.h(0)          # Clifford
    c2.cx(0, 1)      # Clifford
    c2.t(0)           # Non-Clifford
    c2.h(1)           # Clifford
    c2.cx(0, 1)       # Clifford

    segs = analyze_circuit_segments(c2)
    assert len(segs) == 3, f"Expected 3 segments, got {len(segs)}"

    # Verify segment types
    for seg in segs:
        for gate in seg.gates:
            if seg.is_clifford:
                assert gate.name.upper() in ('H', 'X', 'Y', 'Z', 'S', 'S_DAG', 'CX', 'CNOT', 'CZ', 'SWAP', 'I'), \
                    f"Non-Clifford gate {gate.name} in Clifford segment"

    print("  PASS: Segment analysis works correctly")


def test_all_clifford_circuit():
    """Test hybrid simulator on all-Clifford circuit."""
    print("TEST: All-Clifford circuit")

    c = Circuit(2)
    c.h(0)
    c.cx(0, 1)

    sim = HybridSimulator(n_qubits=2)
    result = sim.run_circuit(c, shots=1000)

    assert result['success'], "Simulation should succeed"

    counts = result['counts']
    total = sum(counts.values())
    assert total == 1000, f"Expected 1000 shots, got {total}"

    # Bell state: should be 00 and 11
    assert '00' in counts or '11' in counts, f"Expected Bell state outputs, got {counts}"
    prob_00 = counts.get('00', 0) / total
    prob_11 = counts.get('11', 0) / total
    assert abs(prob_00 - 0.5) < 0.15, f"P(00) should be ~0.5, got {prob_00}"
    assert abs(prob_11 - 0.5) < 0.15, f"P(11) should be ~0.5, got {prob_11}"

    print(f"  PASS: Bell state: {counts}")


def test_mixed_circuit():
    """Test hybrid simulator on circuit with Clifford + T gates."""
    print("TEST: Mixed Clifford/T circuit")

    c = Circuit(2)
    c.h(0)
    c.cx(0, 1)
    c.t(0)           # Non-Clifford
    c.h(1)

    sim = HybridSimulator(n_qubits=2)
    result = sim.run_circuit(c, shots=1000)

    assert result['success'], "Simulation should succeed"
    assert sum(result['counts'].values()) == 1000, "Should have 1000 shots"

    stats = result['stats']
    print(f"  Stats: {stats}")
    print(f"  Counts: {result['counts']}")
    print("  PASS: Mixed circuit works")


def test_larger_circuit():
    """Test hybrid simulator on larger circuit."""
    print("TEST: Larger circuit (5 qubits)")

    c = Circuit(5)
    for i in range(5):
        c.h(i)
    for i in range(4):
        c.cx(i, i+1)
    for i in range(5):
        c.t(i)
    for i in range(4):
        c.cx(i, i+1)
    for i in range(5):
        c.h(i)

    sim = HybridSimulator(n_qubits=5)
    result = sim.run_circuit(c, shots=500)

    assert result['success'], "Simulation should succeed"
    assert sum(result['counts'].values()) == 500, "Should have 500 shots"

    stats = result['stats']
    print(f"  Stats: {stats}")
    print(f"  Unique outcomes: {len(result['counts'])}")
    print("  PASS: Larger circuit works")


def test_comparison_with_mps():
    """Compare hybrid simulator results with MPS simulator."""
    print("TEST: Hybrid vs MPS comparison")

    c = Circuit(3)
    c.h(0)
    c.cx(0, 1)
    c.t(0)
    c.cx(1, 2)

    from abirqu.simulation.mps import MPSSimulator
    mps_sim = MPSSimulator(n_qubits=3, max_bond=32)
    mps_result = mps_sim.run_circuit(c, shots=2000)

    hybrid_sim = HybridSimulator(n_qubits=3, max_bond=32)
    hybrid_result = hybrid_sim.run_circuit(c, shots=2000)

    mps_probs = {k: v/2000 for k, v in mps_result['counts'].items()}
    hybrid_probs = {k: v/2000 for k, v in hybrid_result['counts'].items()}

    all_keys = set(list(mps_probs.keys()) + list(hybrid_probs.keys()))
    total_diff = sum(abs(mps_probs.get(k, 0) - hybrid_probs.get(k, 0)) for k in all_keys)

    print(f"  MPS counts: {mps_result['counts']}")
    print(f"  Hybrid counts: {hybrid_result['counts']}")
    print(f"  Total probability difference: {total_diff:.4f}")

    # Results should be reasonably similar (both approximate methods)
    assert total_diff < 0.5, f"Results differ too much: {total_diff}"
    print("  PASS: Hybrid and MPS results are comparable")


def test_stats_tracking():
    """Test that stats are properly tracked."""
    print("TEST: Stats tracking")

    c = Circuit(3)
    c.h(0)
    c.cx(0, 1)
    c.t(0)
    c.h(1)
    c.cx(1, 2)

    sim = HybridSimulator(n_qubits=3)
    result = sim.run_circuit(c, shots=100)

    stats = result['stats']
    assert 'clifford_gates' in stats, "Missing clifford_gates stat"
    assert 'non_clifford_gates' in stats, "Missing non_clifford_gates stat"
    assert 'segments' in stats, "Missing segments stat"
    assert stats['clifford_gates'] > 0, "Should have Clifford gates"
    assert stats['non_clifford_gates'] > 0, "Should have non-Clifford gates"
    assert stats['segments'] >= 2, f"Should have >= 2 segments, got {stats['segments']}"

    print(f"  Stats: {stats}")
    print("  PASS: Stats tracking works")


if __name__ == "__main__":
    print("=" * 60)
    print("Hybrid MPS-Clifford Simulator Tests")
    print("=" * 60)

    test_segment_analysis()
    print()
    test_all_clifford_circuit()
    print()
    test_mixed_circuit()
    print()
    test_larger_circuit()
    print()
    test_comparison_with_mps()
    print()
    test_stats_tracking()

    print()
    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
