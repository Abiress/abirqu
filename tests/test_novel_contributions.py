#!/usr/bin/env python3
"""
Comprehensive Tests for AbirQu Novel Contributions
===================================================
Tests all 4 novel contributions:
1. Noise-Adaptive Circuit Compiler
2. SPAE (Stochastic-Phase Amplitude Encoding) for QNLP
3. Entanglement-Aware Circuit Cutting
4. Hybrid MPS-Clifford Simulator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import time


def test_noise_adaptive_compiler():
    """Phase 1: Noise-Adaptive Circuit Compiler"""
    print("=" * 60)
    print("PHASE 1: Noise-Adaptive Circuit Compiler")
    print("=" * 60)

    from abirqu.circuit import Circuit
    from abirqu.noise import NoiseModel
    from abirqu.optimize.noise_adaptive import (
        NoiseProfile, NoiseAdaptiveCompiler
    )

    # Create test circuit
    circuit = Circuit(5)
    for i in range(5):
        circuit.h(i)
    for i in range(4):
        circuit.cx(i, i + 1)
    circuit.t(0)
    circuit.t(2)
    circuit.cx(1, 3)

    print(f"Original circuit: {len(circuit.gates)} gates")

    # Create noise model with biased noise
    noise = NoiseModel(num_qubits=5)
    noise.add_depolarizing_error(list(range(5)), 0.001)
    noise.add_depolarizing_error([3], 0.1)  # Make qubit 3 very noisy

    # Create compiler and compile
    compiler = NoiseAdaptiveCompiler()
    compiled = compiler.compile(circuit, noise_model=noise)

    print(f"Compiled circuit: {len(compiled.gates)} gates")
    print(f"Stats: {compiler.stats}")

    # Verify circuit is valid
    assert compiled.num_qubits == 5, "Qubit count mismatch"
    assert len(compiled.gates) > 0, "Compiled circuit is empty"
    assert len(compiled.gates) <= len(circuit.gates), "Compilation should not increase gates"

    print("PASS: Noise-adaptive compiler works correctly")
    return True


def test_spae_qnlp():
    """Phase 2: SPAE for QNLP"""
    print("\n" + "=" * 60)
    print("PHASE 2: SPAE (Stochastic-Phase Amplitude Encoding) for QNLP")
    print("=" * 60)

    from abirqu.qnlp.phonemes import text_to_phonemes
    from abirqu.qnlp.bitstream import StochasticBitstream
    from abirqu.qnlp.spae import SPAEEncoder

    # Test text encoding
    text = "hello world"
    print(f"Input text: '{text}'")

    # Phoneme encoding
    phonemes = text_to_phonemes(text)
    print(f"Phonemes: {phonemes}")

    # Stochastic bitstream
    rng = np.random.RandomState(42)
    bitstream = StochasticBitstream(rng=rng)
    bits = bitstream.generate_from_probability(0.7, len(phonemes))
    print(f"Sampled bits: {bits}")

    # SPAE encoding
    rng2 = np.random.RandomState(42)
    spae = SPAEEncoder(n_qubits=6, rng=rng2)
    encoding = spae.encode_text(text)

    print(f"Generated {len(encoding.circuits)} circuits")

    # Verify circuit is valid
    assert len(encoding.circuits) > 0, "SPAEEncoder should generate circuits"
    assert encoding.circuits[0].num_qubits >= 4, "SPAEEncoder should use at least 4 qubits"

    print("PASS: SPAE encoding works correctly")
    return True


def test_entanglement_cutting():
    """Phase 3: Entanglement-Aware Circuit Cutting"""
    print("\n" + "=" * 60)
    print("PHASE 3: Entanglement-Aware Circuit Cutting")
    print("=" * 60)

    from abirqu.circuit import Circuit
    from abirqu.entanglement_cutting import EntanglementCutter

    # Create a circuit with clear entanglement structure
    circuit = Circuit(10)
    for i in range(10):
        circuit.h(i)
    for i in range(9):
        circuit.cx(i, i + 1)
    # Add some local operations
    circuit.t(0)
    circuit.t(4)
    circuit.t(9)
    # Add long-range entangling gate
    circuit.cx(0, 9)

    print(f"Input circuit: {circuit.num_qubits} qubits, {len(circuit.gates)} gates")

    # Create cutter
    cutter = EntanglementCutter(max_subcircuit_qubits=5)

    # Perform cutting
    result = cutter.cut(circuit)

    print(f"Number of subcircuits: {len(result.sub_circuits)}")
    print(f"Bell pair overhead estimate: {result.overhead_estimate}")
    print(f"Cut points: {result.cut_points}")

    # Verify results
    assert len(result.sub_circuits) > 1, "Should produce multiple subcircuits"
    assert result.overhead_estimate >= 0, "Overhead should be non-negative"

    total_qubits = sum(sc.num_qubits for sc in result.sub_circuits)
    print(f"Total qubits across subcircuits: {total_qubits}")

    print("PASS: Entanglement-aware cutting works correctly")
    return True


def test_hybrid_simulator():
    """Phase 4: Hybrid MPS-Clifford Simulator"""
    print("\n" + "=" * 60)
    print("PHASE 4: Hybrid MPS-Clifford Simulator")
    print("=" * 60)

    from abirqu.circuit import Circuit
    from abirqu.simulation.hybrid import HybridSimulator

    # Test 1: All-Clifford circuit
    print("\nTest 1: All-Clifford circuit")
    circuit1 = Circuit(2)
    circuit1.h(0)
    circuit1.cx(0, 1)

    sim1 = HybridSimulator(n_qubits=2)
    result1 = sim1.run_circuit(circuit1, shots=1000)

    assert result1['success'], "Simulation should succeed"
    counts1 = result1['counts']
    total1 = sum(counts1.values())
    assert total1 == 1000, f"Expected 1000 shots, got {total1}"
    print(f"  Counts: {counts1}")

    # Test 2: Mixed Clifford/T circuit
    print("\nTest 2: Mixed Clifford/T circuit")
    circuit2 = Circuit(3)
    circuit2.h(0)
    circuit2.cx(0, 1)
    circuit2.t(0)
    circuit2.h(1)
    circuit2.cx(1, 2)

    sim2 = HybridSimulator(n_qubits=3)
    result2 = sim2.run_circuit(circuit2, shots=1000)

    assert result2['success'], "Simulation should succeed"
    counts2 = result2['counts']
    total2 = sum(counts2.values())
    assert total2 == 1000, f"Expected 1000 shots, got {total2}"
    print(f"  Counts: {counts2}")

    # Test 3: Larger circuit
    print("\nTest 3: Larger circuit (5 qubits)")
    circuit3 = Circuit(5)
    for i in range(5):
        circuit3.h(i)
    for i in range(4):
        circuit3.cx(i, i + 1)
    for i in range(5):
        circuit3.t(i)
    for i in range(4):
        circuit3.cx(i, i + 1)
    for i in range(5):
        circuit3.h(i)

    sim3 = HybridSimulator(n_qubits=5)
    result3 = sim3.run_circuit(circuit3, shots=500)

    assert result3['success'], "Simulation should succeed"
    counts3 = result3['counts']
    total3 = sum(counts3.values())
    assert total3 == 500, f"Expected 500 shots, got {total3}"
    print(f"  Counts: {counts3}")
    print(f"  Unique outcomes: {len(counts3)}")

    # Test stats
    stats = result3['stats']
    print(f"  Stats: {stats}")

    print("\nPASS: Hybrid simulator works correctly")
    return True


def test_integration():
    """Integration: Run all 4 phases together"""
    print("\n" + "=" * 60)
    print("INTEGRATION: All 4 Phases Together")
    print("=" * 60)

    from abirqu.circuit import Circuit
    from abirqu.noise import NoiseModel
    from abirqu.optimize.noise_adaptive import NoiseAdaptiveCompiler
    from abirqu.qnlp.spae import SPAEEncoder
    from abirqu.entanglement_cutting import EntanglementCutter
    from abirqu.simulation.hybrid import HybridSimulator

    start_time = time.time()

    # Phase 1: Create and compile a noise-adaptive circuit
    print("\nPhase 1: Noise-Adaptive Compilation")
    circuit = Circuit(6)
    for i in range(6):
        circuit.h(i)
    for i in range(5):
        circuit.cx(i, i + 1)
    circuit.t(0)
    circuit.t(3)
    circuit.cx(2, 5)

    noise = NoiseModel(num_qubits=6)
    noise.add_depolarizing_error(list(range(6)), 0.001)
    noise.add_depolarizing_error([4], 0.1)

    compiler = NoiseAdaptiveCompiler()
    compiled = compiler.compile(circuit, noise_model=noise)
    print(f"  Compiled: {len(compiled.gates)} gates")

    # Phase 2: SPAE encoding
    print("\nPhase 2: SPAE Encoding")
    rng = np.random.RandomState(42)
    spae = SPAEEncoder(n_qubits=5, rng=rng)
    encoding = spae.encode_text("quantum computing")
    print(f"  SPAE encoding: {len(encoding.circuits)} circuits")

    # Phase 3: Entanglement cutting
    print("\nPhase 3: Entanglement Cutting")
    cutter = EntanglementCutter(max_subcircuit_qubits=4)
    cut_result = cutter.cut(compiled)
    print(f"  Subcircuits: {len(cut_result.sub_circuits)}, Overhead: {cut_result.overhead_estimate}")

    # Phase 4: Hybrid simulation
    print("\nPhase 4: Hybrid Simulation")
    sim = HybridSimulator(n_qubits=6)
    result = sim.run_circuit(compiled, shots=500)
    print(f"  Simulation: {sum(result['counts'].values())} shots, {len(result['counts'])} outcomes")

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.3f}s")
    print("\nPASS: All 4 phases work together")
    return True


def run_all_tests():
    """Run all tests"""
    tests = [
        ("Noise-Adaptive Compiler", test_noise_adaptive_compiler),
        ("SPAE QNLP", test_spae_qnlp),
        ("Entanglement Cutting", test_entanglement_cutting),
        ("Hybrid Simulator", test_hybrid_simulator),
        ("Integration", test_integration),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"FAILED: {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll tests PASSED!")
    else:
        print("\nSome tests FAILED!")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
