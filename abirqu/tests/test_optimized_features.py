"""
Unit tests for newly optimized and fully implemented AbirQu features.
Copyright 2026 Abir Maheshwari
"""
import os
import tempfile
import numpy as np
import pytest
from abirqu.circuit import Circuit
from abirqu.qec.codes import LDPCCode
from abirqu.qec.ldpc import LDPCDecoder, LDPCEncoder
from abirqu.qec.gpu_decoder import decode_syndrome_gpu
from abirqu.optimize.peephole import optimize_paired_gates
from abirqu.optimize.zx_calculus import simplify_via_zx
from abirqu.optimize.circuit_simplifier import CircuitSimplifier
from abirqu.optimize.pipeline import MultiObjectivePipeline
from abirqu.phases.phase37 import MultiObjectiveRouter
from abirqu.phases.phase33 import NeutralAtomTweezerArray, AdaptiveCompilerPass
from abirqu.tracker import QuantumAdvantageTracker

def test_ldpc_math_and_bp_decoding():
    # 1. Construct LDPCCode
    n, k, d = 40, 20, 5
    code = LDPCCode(n=n, k=k, d=d)
    
    # 2. Check parity-generator mathematical consistency: H * G^T = 0 mod 2
    H = code.H
    G = code.G
    m = n - k
    assert H.shape == (m, n)
    assert G.shape == (k, n)
    
    # Matrix product
    prod = (H @ G.T) % 2
    assert np.all(prod == 0), "Parity check and Generator matrix are mathematically inconsistent!"
    
    # 3. Test systematic structure: G = [I_k | P], H = [P^T | I_m]
    assert np.all(G[:, :k] == np.eye(k, dtype=int))
    assert np.all(H[:, k:] == np.eye(m, dtype=int))
    
    # 4. Encode message
    msg = [np.random.randint(0, 2) for _ in range(k)]
    codeword = code.encode(msg)
    assert len(codeword) == n
    
    # Verify codeword satisfies H * c^T = 0 mod 2
    synd = (H @ np.array(codeword)) % 2
    assert np.all(synd == 0), "Valid codeword did not pass parity checks"
    
    # 5. Corrupt a single bit and decode
    corrupted = list(codeword)
    error_idx = 5
    corrupted[error_idx] ^= 1 # Flip one bit
    
    # Convert to log-domain channel values: 0 maps to low error prob, 1 maps to high
    received = [0.01 if x == 0 else 0.99 for x in corrupted]
    
    # Decode
    decoded_msg = code.decode(received)
    assert decoded_msg == msg, "BP decoder failed to correct the single-bit error!"

def test_gpu_vectorized_syndrome_decoder():
    n, k, d = 30, 15, 4
    code = LDPCCode(n=n, k=k, d=d)
    H = code.H
    
    # Create error vector (single bit error)
    error = np.zeros(n, dtype=int)
    error[8] = 1
    
    # Compute syndrome
    synd = (H @ error) % 2
    
    # Run syndrome-based BP decoder
    decoded_error = decode_syndrome_gpu(synd.tolist(), H=H, use_gpu=False)
    
    # Verify syndrome is satisfied
    decoded_synd = (H @ np.array(decoded_error)) % 2
    assert np.all(decoded_synd == synd), "Syndrome decoder output did not satisfy the syndrome"

def test_peephole_commutation_and_fusion():
    # Construct a circuit with various gates
    c = Circuit(3)
    # Adjacent inverses
    c.x(0).x(0)
    c.h(1).h(1)
    c.s(2).s_dag(2)
    # Merging rotations
    c.rx(0, np.pi/4).rx(0, np.pi/4)
    # Sliding past commuting gates
    c.rz(0, np.pi/4)
    c.x(1) # Acts on qubit 1 (disjoint from qubit 0)
    c.rz(0, np.pi/4)
    
    # Optimize gates
    opt_gates = optimize_paired_gates(c.gates)
    
    # X(0)-X(0), H(1)-H(1), S(2)-S_dag(2) should cancel completely
    # RX(0, pi/4) + RX(0, pi/4) -> RX(0, pi/2) -> which corresponds to RX(pi/2)
    # RZ(0, pi/4) and RZ(0, pi/4) should merge into RZ(0, pi/2) -> S(0)
    # The X(1) should remain
    gate_names = [g.name.upper() for g in opt_gates]
    assert "X" in gate_names # The single X on qubit 1 remains
    # Count of gates should be significantly reduced
    assert len(opt_gates) < len(c.gates)

def test_zx_calculus_spider_fusion():
    c = Circuit(2)
    # Color change: H - RZ - H -> RX
    c.h(0).rz(0, np.pi/4).h(0)
    
    # Commute and fuse through CNOT control
    c.rz(0, np.pi/4)
    c.cnot(0, 1)
    c.rz(0, np.pi/4)
    
    simplified = simplify_via_zx(c)
    
    # The H - RZ - H should become RX/RX-equivalent
    # The RZ(0) before and after CNOT should commute and fuse into a single RZ(0)
    gate_names = [g.name.upper() for g in simplified.gates]
    assert "H" not in gate_names
    assert gate_names.count("RZ") == 1 or gate_names.count("S") == 1 # The two RZ gates fused

def test_integrated_simplifier_and_pipeline():
    c = Circuit(3)
    c.h(0).cnot(0, 1).rz(1, np.pi/4).rz(1, np.pi/4).cnot(0, 1).h(0)
    
    simplifier = CircuitSimplifier()
    opt = simplifier.optimize(c)
    assert len(opt.gates) < len(c.gates)
    
    pipeline = MultiObjectivePipeline()
    pipeline.add_objective("gate_count", lambda circ: len(circ.gates), 1.0)
    pipeline.add_objective("depth", lambda circ: circ.depth(), 1.0)
    
    res = pipeline.optimize(c)
    assert len(res.optimized.gates) <= len(res.original.gates)

def test_quantum_os_router_routing():
    router = MultiObjectiveRouter()
    c = Circuit(4)
    c.h(0).cnot(0, 1).rz(1, np.pi/3).cnot(2, 3)
    
    # Test route_circuit API
    res = router.route_circuit(c, shots=1000, weights={"fidelity": 0.5, "cost": 0.3, "latency": 0.2})
    assert "recommended" in res
    assert "backend" in res["recommended"]
    
    # Test route_workload API
    workload = [{"circuit": c, "shots": 500}, {"circuit": c, "shots": 1000}]
    results = router.route_workload(workload, weights={"fidelity": 0.4, "cost": 0.4, "latency": 0.2})
    assert len(results) == 2
    assert results[0]["recommended"]["backend"] in ["ibm_eagle", "google_sycamore", "abirqu_sim", "ionq_forte"]

def test_automation_sdk_tweezer_layout_and_swap_routing():
    # 1. Tweezer layout optimization
    tweezer = NeutralAtomTweezerArray(num_sites=16, num_atoms=9, zone_radius_um=10.0)
    required_edges = [(0, 1), (1, 2), (0, 3), (3, 4), (6, 7), (2, 8)]
    
    res = tweezer.optimize_layout_for_circuit(required_edges)
    assert "natively_satisfied" in res
    assert "rearrangement" in res
    assert "mapping" in res["rearrangement"]
    assert len(res["rearrangement"]["mapping"]) == 9
    
    # 2. SWAP-routing compiler pass
    topology = tweezer.get_connectivity_graph()
    # Topology edges is linear: [(0, 1), (1, 2), ..., (7, 8)]
    compiler = AdaptiveCompilerPass(topology)
    
    # Interactions: gate between 0 and 2 (needs SWAP because they are not adjacent in linear chain)
    gates = [(0, 2), (1, 3)]
    route_res = compiler.route_circuit(gates)
    
    assert route_res["total_swaps_inserted"] > 0
    assert route_res["routed_gates"] > len(gates)
    assert len(route_res["final_mapping"]) == 9

def test_telemetry_persistence_and_trends():
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry_file = os.path.join(tmpdir, "telemetry.json")
        
        # Initialize tracker (loads empty file or creates it)
        tracker = QuantumAdvantageTracker(filepath=telemetry_file)
        assert len(tracker._points) == 0
        
        # Record points
        tracker.record("qft", quantum_ms=10.0, classical_ms=200.0)
        tracker.record("vqe", quantum_ms=50.0, classical_ms=500.0)
        
        # Verify saved file exists and has content
        assert os.path.exists(telemetry_file)
        
        # Load from file with a new tracker instance
        new_tracker = QuantumAdvantageTracker(filepath=telemetry_file)
        assert len(new_tracker._points) == 2
        assert new_tracker._points[0].workload == "qft"
        assert new_tracker._points[0].speedup == 20.0
        
        # Simulate trending speedup updates
        sim_points = new_tracker.simulate_telemetry_updates(count=3, base_speedup=15.0)
        assert len(sim_points) == 3
        assert len(new_tracker._points) == 5
        
        # Check summary
        summ = new_tracker.summary()
        assert summ["count"] == 5
        assert summ["best_speedup"] >= 20.0
