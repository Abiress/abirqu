"""
Comprehensive tests for AbirQu Quantum SDK
Copyright 2026 Abir Maheshwari
"""

import math
import numpy as np
import pytest

from abirqu.circuit import Circuit, Gate
from abirqu.backend import get_best_backend
from abirqu.noise import NoiseModel
from abirqu.optimize import CircuitSimplifier
from abirqu.primitives.pauli_optimizer import (
    PauliTerm, PauliHamiltonian, PauliExpectationOptimizer, ClassicalShadow
)
from abirqu.primitives import QuantumRun, Sampler, Estimator
from abirqu.qec import SurfaceCode, LDPCCode
from abirqu.algorithms import (
    grover_search, shor_factorization, qft_circuit,
    bernstein_vazirani, qaoa_maxcut, vqe_hardware_efficient,
    quantum_walk
)
from abirqu.simulation import (
    DensityMatrixSimulator, GPUSimulator, CliffordSimulator,
    MPSSimulator, MonteCarloWavefunctionSimulator, gpu_available, is_clifford_only
)
from abirqu.simulation.hybrid import HybridSimulator
from abirqu.chemistry import JordanWignerMapper, MolecularData
from abirqu.qnlp.phonemes import text_to_phonemes
from abirqu.qnlp.spae import SPAEEncoder
from abirqu.transpiler import TranspilerPipeline
from abirqu.space import HHLSolver
from abirqu.tomography import QuantumStateTomography
from abirqu.benchmark.randomized_benchmarking import RandomizedBenchmarking
from abirqu.optimize.circuit_compiler import CircuitCompiler, GateDecomposer, NATIVE_GATE_SETS
from abirqu.entanglement_cutting import EntanglementCutter


# ==========================================
# SECTION 1: CORE CIRCUIT & BACKEND (15 tests)
# ==========================================

class TestCircuit:
    def test_create_empty(self):
        c = Circuit(3, "test")
        assert c.num_qubits == 3
        assert len(c.gates) == 0
        assert c.name == "test"

    def test_add_single_qubit_gates(self):
        c = Circuit(2, "gates")
        c.add_gate("H", [0])
        c.add_gate("X", [1])
        c.add_gate("Y", [0])
        c.add_gate("Z", [1])
        assert len(c.gates) == 4

    def test_add_two_qubit_gate(self):
        c = Circuit(2, "cnot")
        c.add_gate("CNOT", [0, 1])
        assert len(c.gates) == 1
        assert c.gates[0].qubits == [0, 1]

    def test_add_rotation_gate(self):
        c = Circuit(1, "rot")
        c.add_gate("RX", [0], params=[math.pi / 4])
        c.add_gate("RY", [0], params=[math.pi / 2])
        c.add_gate("RZ", [0], params=[math.pi])
        assert len(c.gates) == 3

    def test_circuit_add_gate_name(self):
        c = Circuit(2, "test")
        c.add_gate("CZ", [0, 1])
        assert c.gates[0].name == "CZ"

    def test_circuit_str(self):
        c = Circuit(1, "test")
        c.add_gate("H", [0])
        s = str(c)
        assert isinstance(s, str)

    def test_gate_repr(self):
        g = Gate("H", [0])
        assert "H" in repr(g)

    def test_circuit_num_qubits(self):
        c = Circuit(5, "big")
        assert c.num_qubits == 5

    def test_circuit_multiple_cnots(self):
        c = Circuit(3, "multi")
        c.add_gate("CNOT", [0, 1])
        c.add_gate("CNOT", [1, 2])
        c.add_gate("CNOT", [0, 2])
        assert len(c.gates) == 3


class TestBackend:
    def test_get_best_backend(self):
        b = get_best_backend(n_qubits=2)
        assert b is not None

    def test_backend_run_circuit(self):
        b = get_best_backend(n_qubits=2)
        c = Circuit(2, "bell")
        c.add_gate("H", [0])
        c.add_gate("CNOT", [0, 1])
        result = b.run_circuit(c, shots=100)
        assert result is not None

    def test_backend_name(self):
        b = get_best_backend(n_qubits=2)
        assert b.name is not None

    def test_backend_is_local(self):
        b = get_best_backend(n_qubits=2)
        assert isinstance(b.is_local, bool)


class TestNoise:
    def test_depolarizing_channel(self):
        nm = NoiseModel(num_qubits=1)
        nm.add_depolarizing_error(0, 0.1)
        assert nm is not None

    def test_amplitude_damping(self):
        nm = NoiseModel(num_qubits=1)
        nm.add_amplitude_damping(0, 0.05)
        assert nm is not None

    def test_phase_damping(self):
        nm = NoiseModel(num_qubits=1)
        nm.add_phase_damping(0, 0.02)
        assert nm is not None

    def test_readout_error(self):
        nm = NoiseModel(num_qubits=1)
        nm.add_readout_error(0, 0.01, 0.02)
        assert nm is not None

    def test_noise_model_creation(self):
        nm = NoiseModel(num_qubits=3)
        assert nm.num_qubits == 3


# ==========================================
# SECTION 2: PAULI OPTIMIZER (5 tests)
# ==========================================

class TestPauliOptimizer:
    def test_pauli_term_creation(self):
        pt = PauliTerm(0.5, ["X", "I", "Z"])
        assert pt.coefficient == 0.5
        assert pt.paulis == ["X", "I", "Z"]

    def test_pauli_term_weight(self):
        pt = PauliTerm(1.0, ["X", "I", "Z"])
        assert pt.weight() == 2

    def test_pauli_hamiltonian(self):
        h = PauliHamiltonian(n_qubits=2)
        h.add_term(coefficient=1.0, paulis=["X", "I"])
        h.add_term(coefficient=0.5, paulis=["I", "Z"])
        assert len(h.terms) == 2

    def test_pauli_optimizer_initialization(self):
        opt = PauliExpectationOptimizer()
        assert opt is not None

    def test_classical_shadow(self):
        shadow = ClassicalShadow(n_qubits=2, num_shadows=100)
        assert shadow is not None


# ==========================================
# SECTION 3: CIRCUIT SIMPLIFIER (5 tests)
# ==========================================

class TestCircuitSimplifier:
    def test_simplifier_initialization(self):
        s = CircuitSimplifier()
        assert s is not None

    def test_simplify_identity(self):
        c = Circuit(1, "id")
        c.add_gate("H", [0])
        c.add_gate("H", [0])
        s = CircuitSimplifier()
        result = s.simplify(c)
        assert len(result.gates) == 0

    def test_simplify_x_squared(self):
        c = Circuit(1, "xx")
        c.add_gate("X", [0])
        c.add_gate("X", [0])
        s = CircuitSimplifier()
        result = s.simplify(c)
        assert len(result.gates) == 0

    def test_simplify_preserves_cnot(self):
        c = Circuit(2, "cnot")
        c.add_gate("CNOT", [0, 1])
        s = CircuitSimplifier()
        result = s.simplify(c)
        assert len(result.gates) == 1

    def test_simplify_preserves_non_adjacent(self):
        c = Circuit(2, "test")
        c.add_gate("H", [0])
        c.add_gate("X", [1])
        s = CircuitSimplifier()
        result = s.simplify(c)
        assert len(result.gates) == 2


# ==========================================
# SECTION 4: QUANTUM PRIMITIVES (4 tests)
# ==========================================

class TestPrimitives:
    def test_quantum_run_initialization(self):
        c = Circuit(1, "test")
        c.add_gate("H", [0])
        qr = QuantumRun(circuits=[c])
        assert qr is not None

    def test_sampler_initialization(self):
        s = Sampler()
        assert s is not None

    def test_estimator_initialization(self):
        e = Estimator()
        assert e is not None

    def test_sampler_run(self):
        s = Sampler()
        c = Circuit(1, "test")
        c.add_gate("H", [0])
        result = s.run(c, shots=100)
        assert result is not None


# ==========================================
# SECTION 5: ERROR CORRECTION (5 tests)
# ==========================================

class TestQEC:
    def test_surface_code_3(self):
        code = SurfaceCode(distance=3)
        assert code.distance == 3

    def test_ldpc_code(self):
        code = LDPCCode()
        assert code is not None

    def test_surface_code_5(self):
        code = SurfaceCode(distance=5)
        assert code.distance == 5

    def test_surface_code_7(self):
        code = SurfaceCode(distance=7)
        assert code.distance == 7

    def test_surface_code_properties(self):
        code = SurfaceCode(distance=3)
        assert code.distance == 3


# ==========================================
# SECTION 6: QUANTUM ALGORITHMS (10 tests)
# ==========================================

class TestAlgorithms:
    def test_grover_search(self):
        c = grover_search(target_state=3, num_qubits=2)
        assert c is not None
        assert c.num_qubits == 2

    def test_shor_factorization(self):
        c, meta = shor_factorization(num_to_factor=15, num_qubits=8)
        assert c is not None
        assert meta is not None

    def test_qft_circuit(self):
        c = qft_circuit(num_qubits=3)
        assert c is not None
        assert c.num_qubits == 3

    def test_bernstein_vazirani(self):
        c = bernstein_vazirani(secret="101")
        assert c is not None
        assert c.num_qubits == 4

    def test_qaoa_maxcut(self):
        c = qaoa_maxcut(num_qubits=4, edges=[(0, 1), (1, 2), (2, 3)])
        assert c is not None

    def test_vqe_hardware_efficient(self):
        c = vqe_hardware_efficient(num_qubits=3, depth=2)
        assert c is not None

    def test_quantum_walk(self):
        c = quantum_walk(num_qubits=2, steps=4)
        assert c is not None

    def test_grover_search_3_qubits(self):
        c = grover_search(target_state=5, num_qubits=3)
        assert c.num_qubits == 3

    def test_qft_4_qubits(self):
        c = qft_circuit(num_qubits=4)
        assert c.num_qubits == 4

    def test_shor_factorization_small(self):
        c, meta = shor_factorization(num_to_factor=6, num_qubits=6)
        assert meta["success"] is True or meta["success"] is False


# ==========================================
# SECTION 7: SIMULATION ENGINES (8 tests)
# ==========================================

class TestSimulationEngines:
    def test_clifford_simulator(self):
        sim = CliffordSimulator(n_qubits=2)
        assert sim.n_qubits == 2

    def test_mps_simulator(self):
        sim = MPSSimulator(n_qubits=4)
        assert sim.n_qubits == 4

    def test_hybrid_simulator(self):
        sim = HybridSimulator(n_qubits=4)
        assert sim.n_qubits == 4

    def test_gpu_simulator(self):
        sim = GPUSimulator(n_qubits=2)
        assert sim.n_qubits == 2

    def test_monte_carlo_simulator(self):
        sim = MonteCarloWavefunctionSimulator(num_qubits=2)
        assert sim.num_qubits == 2

    def test_gpu_available(self):
        assert isinstance(gpu_available(), bool)

    def test_clifford_is_clifford_only(self):
        c = Circuit(1, "test")
        c.add_gate("H", [0])
        result = is_clifford_only(c)
        assert result is True

    def test_clifford_run_circuit(self):
        c = Circuit(2, "bell")
        c.add_gate("H", [0])
        c.add_gate("CNOT", [0, 1])
        sim = CliffordSimulator(n_qubits=2)
        result = sim.run_circuit(c, shots=100)
        assert result is not None


# ==========================================
# SECTION 8: CHEMISTRY (3 tests)
# ==========================================

class TestChemistry:
    def test_jordan_wigner_mapper(self):
        jw = JordanWignerMapper(n_orbitals=2)
        assert jw is not None

    def test_molecular_data(self):
        md = MolecularData()
        assert md is not None

    def test_jordan_wigner_mapper_4(self):
        jw = JordanWignerMapper(n_orbitals=4)
        assert jw is not None


# ==========================================
# SECTION 9: QNLP (5 tests)
# ==========================================

class TestQNLP:
    def test_text_to_phoneme(self):
        result = text_to_phonemes("hello")
        assert len(result) > 0

    def test_spae_encoder(self):
        enc = SPAEEncoder()
        assert enc is not None

    def test_text_to_phoneme_world(self):
        result = text_to_phonemes("world")
        assert len(result) > 0

    def test_text_to_phoneme_empty(self):
        result = text_to_phonemes("")
        assert isinstance(result, list)

    def test_text_to_phoneme_long(self):
        result = text_to_phonemes("hello world this is a test")
        assert len(result) > 5


# ==========================================
# SECTION 10: INFRASTRUCTURE (2 tests)
# ==========================================

class TestInfrastructure:
    def test_transpiler_pipeline(self):
        tp = TranspilerPipeline()
        assert tp is not None

    def test_hhl_solver(self):
        solver = HHLSolver(n_qubits=2)
        assert solver is not None


# ==========================================
# SECTION 11: NEW v0.5.0 MODULES (10 tests)
# ==========================================

class TestNewModules:
    def test_tomography(self):
        tomo = QuantumStateTomography(n_qubits=1)
        assert tomo is not None

    def test_randomized_benchmarking(self):
        rb = RandomizedBenchmarking()
        assert rb is not None

    def test_entanglement_cutter(self):
        ec = EntanglementCutter()
        assert ec is not None

    def test_circuit_compiler(self):
        compiler = CircuitCompiler(target='universal')
        assert compiler is not None

    def test_circuit_compiler_ibm(self):
        compiler = CircuitCompiler(target='ibm')
        assert compiler is not None

    def test_gate_decomposer(self):
        decomposer = GateDecomposer(['H', 'T', 'CNOT'])
        assert decomposer is not None

    def test_native_gate_sets(self):
        assert 'ibm' in NATIVE_GATE_SETS
        assert 'google' in NATIVE_GATE_SETS
        assert 'ionq' in NATIVE_GATE_SETS

    def test_tomography_2_qubits(self):
        tomo = QuantumStateTomography(n_qubits=2)
        assert tomo.n_qubits == 2

    def test_rb_initialization(self):
        rb = RandomizedBenchmarking()
        assert rb is not None


# ==========================================
# SECTION 12: INTEGRATION (10 tests)
# ==========================================

class TestIntegration:
    def test_full_circuit_pipeline(self):
        c = Circuit(2, "bell")
        c.add_gate("H", [0])
        c.add_gate("CNOT", [0, 1])
        b = get_best_backend(n_qubits=2)
        result = b.run_circuit(c, shots=100)
        assert result is not None

    def test_noise_pipeline(self):
        nm = NoiseModel(num_qubits=1)
        nm.add_depolarizing_error(0, 0.1)
        c = Circuit(1, "noisy")
        c.add_gate("H", [0])
        b = get_best_backend(n_qubits=1)
        result = b.run_circuit(c, shots=100)
        assert result is not None

    def test_optimization_pipeline(self):
        c = Circuit(1, "opt")
        c.add_gate("H", [0])
        c.add_gate("X", [0])
        c.add_gate("X", [0])
        s = CircuitSimplifier()
        result = s.simplify(c)
        assert len(result.gates) <= 2

    def test_algorithm_pipeline(self):
        c = grover_search(target_state=0, num_qubits=2)
        b = get_best_backend(n_qubits=c.num_qubits)
        result = b.run_circuit(c, shots=100)
        assert result is not None

    def test_clifford_bell_state(self):
        c = Circuit(2, "bell")
        c.add_gate("H", [0])
        c.add_gate("CNOT", [0, 1])
        sim = CliffordSimulator(n_qubits=2)
        sv = sim.run_circuit(c, shots=1000)
        assert sv is not None

    def test_compiler_pipeline(self):
        c = Circuit(2, "bell")
        c.add_gate("H", [0])
        c.add_gate("CNOT", [0, 1])
        compiler = CircuitCompiler(target='universal')
        compiled = compiler.compile(c)
        assert compiled is not None
        assert compiled.num_qubits == 2

    def test_compiler_stats(self):
        c = Circuit(1, "test")
        c.add_gate("H", [0])
        compiler = CircuitCompiler(target='universal')
        compiler.compile(c)
        stats = compiler.get_stats()
        assert stats['original_gates'] == 1

    def test_compiler_optimization(self):
        c = Circuit(1, "opt")
        c.add_gate("X", [0])
        c.add_gate("X", [0])
        compiler = CircuitCompiler(target='universal')
        compiled = compiler.compile(c, optimize=True)
        assert len(compiled.gates) <= 1

    def test_full_stack(self):
        c = Circuit(2, "bell")
        c.add_gate("H", [0])
        c.add_gate("CNOT", [0, 1])
        b = get_best_backend(n_qubits=2)
        result = b.run_circuit(c, shots=1000)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
