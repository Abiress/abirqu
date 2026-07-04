"""
Tests for Quantum Communication Module
Copyright 2026 Abir Maheshwari
"""

import pytest
import math

from abirqu.quantum_communication.bb84 import BB84Protocol, BB84Simulator, Basis
from abirqu.quantum_communication.e91 import E91Protocol, E91Simulator
from abirqu.quantum_communication.cv_qkd import CVQKDProtocol, GaussianModulation
from abirqu.quantum_communication.di_qkd import DIQKDProtocol, BellTest
from abirqu.quantum_communication.satellite import SatelliteQKD, SatelliteLink
from abirqu.quantum_communication.repeaters import QuantumRepeater, RepeaterChain
from abirqu.quantum_communication.network import QuantumNetwork, QuantumNode, QuantumChannel, Topology


# ==========================================
# BB84 Tests (5 tests)
# ==========================================

class TestBB84:
    def test_bb84_no_eavesdropper(self):
        bb84 = BB84Protocol(num_bits=256, eavesdrop=False, seed=42)
        result = bb84.run()
        assert not result.eavesdropper_detected
        assert result.final_key is not None
        assert len(result.final_key) > 0

    def test_bb84_with_eavesdropper(self):
        bb84 = BB84Protocol(num_bits=1024, eavesdrop=True, seed=42)
        result = bb84.run()
        assert result.eavesdropper_detected
        assert result.error_rate > 0.1

    def test_bb84_sifting(self):
        bb84 = BB84Protocol(num_bits=256, seed=42)
        result = bb84.run()
        # Sifted key should be roughly half the size
        assert len(result.sifted_key_alice) <= 256
        assert len(result.sifted_key_alice) > 0

    def test_bb84_error_rate(self):
        bb84 = BB84Protocol(num_bits=256, eavesdrop=False, seed=42)
        result = bb84.run()
        assert 0.0 <= result.error_rate <= 0.5

    def test_bb84_simulator(self):
        sim = BB84Simulator(distance_km=50, seed=42)
        result = sim.simulate(num_bits=1024)
        assert result['distance_km'] == 50
        assert result['channel_transmission'] > 0


# ==========================================
# E91 Tests (5 tests)
# ==========================================

class TestE91:
    def test_e91_no_eavesdropper(self):
        e91 = E91Protocol(num_pairs=256, eavesdrop=False, seed=42)
        result = e91.run()
        assert not result.eavesdropper_detected
        assert result.bell_violation > 2.0

    def test_e91_with_eavesdropper(self):
        e91 = E91Protocol(num_pairs=1024, eavesdrop=True, seed=42)
        result = e91.run()
        # Eavesdropping reduces Bell violation
        assert result.bell_violation <= 2.828

    def test_e91_key_extraction(self):
        e91 = E91Protocol(num_pairs=256, seed=42)
        result = e91.run()
        assert len(result.sifted_key_alice) <= 256

    def test_e91_simulator(self):
        sim = E91Simulator(distance_km=100, seed=42)
        result = sim.simulate(num_pairs=1024)
        assert result['distance_km'] == 100
        assert result['bell_violation'] > 2.0


# ==========================================
# CV-QKD Tests (4 tests)
# ==========================================

class TestCVQKD:
    def test_cvqkd_basic(self):
        cvqkd = CVQKDProtocol(num_symbols=256, seed=42)
        result = cvqkd.run()
        assert result.mutual_information >= 0

    def test_cvqkd_high_noise(self):
        cvqkd = CVQKDProtocol(num_symbols=256, excess_noise=1.0, seed=42)
        result = cvqkd.run()
        # High noise should reduce key rate
        assert result.secret_key_rate <= 1.0

    def test_gaussian_modulation(self):
        gm = GaussianModulation(variance=4.0, seed=42)
        symbols = gm.generate_symbols(100)
        assert len(symbols) == 100
        assert all(len(s) == 2 for s in symbols)

    def test_gaussian_variance_estimation(self):
        gm = GaussianModulation(variance=4.0, seed=42)
        symbols = gm.generate_symbols(10000)
        estimated = gm.estimate_variance(symbols)
        assert abs(estimated - 4.0) < 0.5


# ==========================================
# DI-QKD Tests (4 tests)
# ==========================================

class TestDIQKD:
    def test_diqkd_basic(self):
        diqkd = DIQKDProtocol(num_rounds=256, seed=42)
        result = diqkd.run()
        assert result.chsh_parameter >= 0

    def test_diqkd_low_noise(self):
        diqkd = DIQKDProtocol(num_rounds=256, noise_level=0.01, seed=42)
        result = diqkd.run()
        assert result.chsh_parameter > 2.0

    def test_bell_test_chsh(self):
        bt = BellTest()
        assert bt.quantum_bound() == 2 * math.sqrt(2)

    def test_bell_test_violation(self):
        bt = BellTest()
        assert bt.is_violated(2.5)
        assert not bt.is_violated(1.5)


# ==========================================
# Satellite QKD Tests (4 tests)
# ==========================================

class TestSatelliteQKD:
    def test_satellite_basic(self):
        sat = SatelliteQKD(seed=42)
        result = sat.simulate(num_pulses=100000)
        assert result.distance_km > 0
        assert result.key_rate >= 0

    def test_satellite_custom_link(self):
        link = SatelliteLink(altitude_km=300)
        sat = SatelliteQKD(link=link, seed=42)
        result = sat.simulate()
        assert result.link_budget['slant_range_km'] > 0

    def test_satellite_vs_fiber(self):
        sat = SatelliteQKD(seed=42)
        comparison = sat.compare_with_fiber(fiber_distance_km=100)
        assert 'satellite' in comparison
        assert 'fiber' in comparison

    def test_satellite_link_parameters(self):
        link = SatelliteLink(
            altitude_km=500,
            beam_divergence_urad=10,
            telescope_diameter_m=0.5,
        )
        assert link.altitude_km == 500


# ==========================================
# Quantum Repeater Tests (4 tests)
# ==========================================

class TestQuantumRepeater:
    def test_repeater_basic(self):
        rep = QuantumRepeater(total_distance_km=1000, num_segments=10, seed=42)
        result = rep.simulate()
        assert result.total_distance_km == 1000
        assert result.num_segments == 10
        assert 0.5 <= result.end_to_end_fidelity <= 1.0

    def test_repeater_fidelity(self):
        rep = QuantumRepeater(total_distance_km=500, num_segments=5, seed=42)
        result = rep.simulate()
        assert result.end_to_end_fidelity > 0.5

    def test_repeater_chain(self):
        chain = RepeaterChain(
            num_segments=5,
            segment_distance_km=100,
            total_distance_km=500,
            segments=[],
        )
        assert chain.num_segments == 5
        assert chain.total_distance_km == 500

    def test_repeater_optimization(self):
        rep = QuantumRepeater(total_distance_km=1000, seed=42)
        optimal_n = rep.optimize_segments(target_fidelity=0.8)
        assert optimal_n > 0


# ==========================================
# Quantum Network Tests (4 tests)
# ==========================================

class TestQuantumNetwork:
    def test_network_star(self):
        net = QuantumNetwork(num_nodes=5, topology=Topology.STAR, seed=42)
        net.build_topology()
        result = net.simulate()
        assert result.num_nodes == 5
        assert result.num_edges == 4

    def test_network_ring(self):
        net = QuantumNetwork(num_nodes=5, topology=Topology.RING, seed=42)
        net.build_topology()
        result = net.simulate()
        assert result.num_edges == 5

    def test_network_mesh(self):
        net = QuantumNetwork(num_nodes=5, topology=Topology.MESH, seed=42)
        net.build_topology()
        result = net.simulate()
        assert result.num_edges > 0

    def test_network_path_finding(self):
        net = QuantumNetwork(num_nodes=5, topology=Topology.LINE, seed=42)
        net.build_topology()
        path = net.find_path(0, 4)
        assert path is not None
        assert path.source == 0
        assert path.destination == 4

    def test_network_adjacency(self):
        net = QuantumNetwork(num_nodes=3, topology=Topology.LINE, seed=42)
        net.build_topology()
        adj = net.get_adjacency_matrix()
        assert adj.shape == (3, 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
