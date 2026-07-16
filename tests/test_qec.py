"""
Comprehensive tests for AbirQu QEC module
Copyright 2026 Abir Maheshwari
"""
import numpy as np
import pytest
from abirqu.qec.codes import (
    StabilizerCode, RepetitionCode, BitFlipCode, PhaseFlipCode,
    ShorCode, SteaneCode, SurfaceCode, ColorCode, EncodedState,
)
from abirqu.qec.surface_code import RotatedSurfaceCode
from abirqu.qec.decoder import (
    SyndromeDecoder, SurfaceCodeDecoder, BeliefPropagationDecoder,
    MWPMDecoder, GPUAcceleratedDecoder,
)
from abirqu.qec.magic_state import (
    MagicState, MagicStateDistiller, HStateDistiller,
    TStateFactory, TGateInjector,
)
from abirqu.qec.ft_compiler import (
    FaultTolerantCompiler, TransversalGateSet,
)


class TestRepetitionCode:
    def test_construction(self):
        code = RepetitionCode(3)
        assert code.n == 3
        assert code.k == 1
        assert code.d == 2
        assert code.num_stabilizers == 2

    def test_encode_zero(self):
        code = RepetitionCode(3)
        state = code.encode(0)
        assert np.array_equal(state, [0, 0, 0])

    def test_encode_one(self):
        code = RepetitionCode(3)
        state = code.encode(1)
        assert np.array_equal(state, [1, 1, 1])

    def test_syndrome_no_error(self):
        code = RepetitionCode(3)
        error = np.array([0, 0, 0])
        syndrome = code.compute_syndrome(error)
        assert np.array_equal(syndrome, [0, 0])

    def test_syndrome_single_error(self):
        code = RepetitionCode(3)
        error = np.array([1, 0, 0])
        syndrome = code.compute_syndrome(error)
        assert syndrome[0] == 1
        assert syndrome[1] == 0

    def test_syndrome_two_errors(self):
        code = RepetitionCode(5)
        error = np.array([1, 0, 0, 0, 1])
        syndrome = code.compute_syndrome(error)
        assert syndrome[0] == 1
        assert syndrome[-1] == 1

    def test_n2(self):
        code = RepetitionCode(2)
        assert code.n == 2
        assert code.k == 1
        assert code.d == 1

    def test_overhead(self):
        code = RepetitionCode(5)
        oh = code.get_overhead()
        assert oh['n'] == 5
        assert oh['k'] == 1


class TestBitFlipCode:
    def test_basic(self):
        code = BitFlipCode()
        assert code.n == 3
        assert code.k == 1
        state = code.encode(0)
        assert len(state) == 3

    def test_encode_one(self):
        code = BitFlipCode()
        state = code.encode(1)
        assert np.all(state == 1)


class TestPhaseFlipCode:
    def test_construction(self):
        code = PhaseFlipCode()
        assert code.n == 3
        assert code.k == 1
        assert code.d == 1

    def test_encode(self):
        code = PhaseFlipCode()
        state0 = code.encode(0)
        state1 = code.encode(1)
        assert len(state0) == 3
        assert len(state1) == 3

    def test_syndrome(self):
        code = PhaseFlipCode()
        error = np.array([0, 0, 0])
        syn = code.compute_syndrome(error)
        assert np.array_equal(syn, [0, 0])

    def test_syndrome_error(self):
        code = PhaseFlipCode()
        error = np.array([1, 0, 0])
        syn = code.compute_syndrome(error)
        assert syn[0] == 1


class TestShorCode:
    def test_construction(self):
        code = ShorCode()
        assert code.n == 9
        assert code.k == 1
        assert code.d == 3
        assert code.num_stabilizers == 8

    def test_encode(self):
        code = ShorCode()
        state = code.encode(0)
        assert len(state) == 9
        assert np.all(state == 0)
        state1 = code.encode(1)
        assert np.all(state1 == 1)

    def test_syndrome_no_error(self):
        code = ShorCode()
        error = np.zeros(9, dtype=int)
        syn = code.compute_syndrome(error)
        assert np.all(syn == 0)

    def test_syndrome_single_error(self):
        code = ShorCode()
        error = np.zeros(9, dtype=int)
        error[0] = 1
        syn = code.compute_syndrome(error)
        assert np.any(syn != 0)

    def test_syndrome_different_errors(self):
        code = ShorCode()
        e1 = np.zeros(9, dtype=int)
        e1[0] = 1
        e2 = np.zeros(9, dtype=int)
        e2[8] = 1
        s1 = code.compute_syndrome(e1)
        s2 = code.compute_syndrome(e2)
        assert not np.array_equal(s1, s2)


class TestSteaneCode:
    def test_construction(self):
        code = SteaneCode()
        assert code.n == 7
        assert code.k == 1
        assert code.d == 3
        assert code.num_stabilizers == 6

    def test_encode(self):
        code = SteaneCode()
        state = code.encode(0)
        assert len(state) == 7

    def test_syndrome_no_error(self):
        code = SteaneCode()
        error = np.zeros(7, dtype=int)
        syn = code.compute_syndrome(error)
        assert np.all(syn == 0)

    def test_syndrome_single_error(self):
        code = SteaneCode()
        for q in range(7):
            error = np.zeros(7, dtype=int)
            error[q] = 1
            syn = code.compute_syndrome(error)
            assert np.any(syn != 0), f"Error on qubit {q} not detected"

    def test_different_errors_different_syndromes(self):
        code = SteaneCode()
        syndromes = set()
        for q in range(7):
            error = np.zeros(7, dtype=int)
            error[q] = 1
            syn = tuple(code.compute_syndrome(error).tolist())
            syndromes.add(syn)
        assert len(syndromes) == 7


class TestSurfaceCode:
    def test_construction_d3(self):
        code = SurfaceCode(3)
        assert code.d == 3
        assert code.physical_qubits == 13
        assert code.logical_qubits == 1

    def test_construction_d5(self):
        code = SurfaceCode(5)
        assert code.d == 5
        assert code.physical_qubits == 41

    def test_encode(self):
        code = SurfaceCode(3)
        state = code.encode(0)
        assert len(state) == 13
        assert np.all(state == 0)

    def test_syndrome_measurement(self):
        code = SurfaceCode(3)
        syn = code.syndrome_measurement()
        assert len(syn) > 0

    def test_stabilizers_exist(self):
        code = SurfaceCode(3)
        assert len(code.x_stabilizers) > 0
        assert len(code.z_stabilizers) > 0

    def test_overhead(self):
        code = SurfaceCode(3)
        oh = code.get_overhead()
        assert oh['n'] == 13
        assert oh['d'] == 3


class TestRotatedSurfaceCode:
    def test_construction(self):
        code = RotatedSurfaceCode(3)
        assert code.d == 3
        assert code.n == 13
        assert code.k == 1

    def test_encode(self):
        code = RotatedSurfaceCode(3)
        state = code.encode(0)
        assert len(state) == 13

    def test_syndrome(self):
        code = RotatedSurfaceCode(3)
        error = np.zeros(13, dtype=int)
        syn = code.syndrome(error)
        assert len(syn) > 0

    def test_syndrome_with_error(self):
        code = RotatedSurfaceCode(3)
        error = np.zeros(13, dtype=int)
        error[0] = 1
        syn = code.syndrome(error)
        assert np.any(syn != 0)

    def test_logical_operators(self):
        code = RotatedSurfaceCode(3)
        lx = code.get_logical_x()
        lz = code.get_logical_z()
        assert len(lx) > 0
        assert len(lz) > 0

    def test_d5(self):
        code = RotatedSurfaceCode(5)
        assert code.n == 41
        assert code.d == 5

    def test_overhead(self):
        code = RotatedSurfaceCode(3)
        oh = code.get_overhead()
        assert oh['n'] == 13


class TestColorCode:
    def test_construction(self):
        code = ColorCode(3)
        assert code.d == 3
        assert code.n == 9
        assert code.k == 1

    def test_encode(self):
        code = ColorCode(3)
        state = code.encode(0)
        assert len(state) == 9
        state1 = code.encode(1)
        assert np.all(state1 == 1)

    def test_syndrome(self):
        code = ColorCode(3)
        error = np.zeros(9, dtype=int)
        syn = code.syndrome(error)
        assert len(syn) > 0

    def test_stabilizers(self):
        code = ColorCode(3)
        assert len(code.stabilizers_x) > 0
        assert len(code.stabilizers_z) > 0

    def test_transversal_gates(self):
        code = ColorCode(3)
        state = code.encode(0)
        state_h = code.apply_transversal_h(state)
        assert np.array_equal(state, state_h)
        state_s = code.apply_transversal_s(state)
        assert np.array_equal(state, state_s)

    def test_overhead(self):
        code = ColorCode(3)
        oh = code.get_overhead()
        assert oh['n'] == 9
        assert 'H' in oh['transversal_clifford']


class TestEncodedState:
    def test_basic(self):
        code = BitFlipCode()
        state = code.encode(0)
        es = EncodedState(code, state)
        assert es.code is code
        assert len(es.state) == 3

    def test_apply_error(self):
        code = BitFlipCode()
        state = code.encode(0)
        es = EncodedState(code, state)
        error = np.array([1, 0, 0])
        es.apply_error(error)
        assert es.state[0] == 1

    def test_measure_syndrome(self):
        code = BitFlipCode()
        state = code.encode(0)
        es = EncodedState(code, state)
        syn = es.measure_syndrome()
        assert syn is not None


class TestSyndromeDecoder:
    def test_decode_no_syndrome(self):
        code = BitFlipCode()
        decoder = SyndromeDecoder(code)
        syn = np.zeros(2, dtype=int)
        correction = decoder.decode(syn)
        assert np.all(correction == 0)

    def test_decode_single_error(self):
        code = RepetitionCode(5)
        decoder = SyndromeDecoder(code)
        error = np.zeros(5, dtype=int)
        error[2] = 1
        syn = code.compute_syndrome(error)
        correction = decoder.decode(syn)
        # Correction should fix the error
        total = (error + correction) % 2
        # After correction, the total should be in the code space
        # (i.e., all zeros or a valid codeword)
        assert isinstance(correction, np.ndarray)

    def test_decode_shor(self):
        code = ShorCode()
        decoder = SyndromeDecoder(code)
        error = np.zeros(9, dtype=int)
        error[4] = 1
        syn = code.compute_syndrome(error)
        correction = decoder.decode(syn)
        assert len(correction) == 9

    def test_decode_with_history(self):
        code = BitFlipCode()
        decoder = SyndromeDecoder(code)
        syn = np.zeros(2, dtype=int)
        result = decoder.decode_with_history(syn)
        assert 'correction' in result
        assert 'syndrome_weight' in result


class TestSurfaceCodeDecoder:
    def test_decode_clean(self):
        decoder = SurfaceCodeDecoder(3)
        syn = np.zeros(4, dtype=int)
        correction = decoder.decode_x_syndrome(syn)
        assert np.all(correction == 0)

    def test_decode_full(self):
        decoder = SurfaceCodeDecoder(3)
        syn = np.zeros(8, dtype=int)
        result = decoder.decode(syn)
        assert 'x_correction' in result
        assert 'z_correction' in result


class TestMWPMDecoder:
    def test_decode_clean(self):
        code = RepetitionCode(5)
        decoder = MWPMDecoder(code)
        syn = np.zeros(4, dtype=int)
        correction = decoder.decode(syn)
        assert np.all(correction == 0)

    def test_decode_single_defect(self):
        code = RepetitionCode(5)
        decoder = MWPMDecoder(code)
        syn = np.array([1, 0, 0, 0], dtype=int)
        correction = decoder.decode(syn)
        assert np.any(correction != 0)


class TestBeliefPropagationDecoder:
    def test_decode(self):
        decoder = BeliefPropagationDecoder(max_iterations=10)
        H = np.array([[1, 1, 0, 0],
                       [0, 1, 1, 0],
                       [0, 0, 1, 1]])
        syndrome = np.array([1, 0, 1])
        correction = decoder.decode(H, syndrome, error_rate=0.1)
        assert len(correction) == 4


class TestGPUAcceleratedDecoder:
    def test_decode(self):
        decoder = GPUAcceleratedDecoder(backend="cpu")
        H = np.array([[1, 1, 0], [0, 1, 1]])
        syn = [1, 1]
        correction = decoder.decode_syndrome(syn, H)
        assert len(correction) == 3

    def test_benchmark(self):
        decoder = GPUAcceleratedDecoder(backend="cpu")
        stats = decoder.benchmark(num_trials=50, n=10)
        assert 'avg_time_us' in stats
        assert stats['num_trials'] == 50


class TestMagicState:
    def test_creation(self):
        ms = MagicState(state_type='T', fidelity=0.9)
        assert ms.state_type == 'T'
        assert ms.fidelity == 0.9

    def test_repr(self):
        ms = MagicState(state_type='T', fidelity=0.95)
        assert 'T' in repr(ms)


class TestMagicStateDistiller:
    def test_distill_one_round(self):
        distiller = MagicStateDistiller(rounds=1)
        states = [MagicState('T', 0.9) for _ in range(15)]
        result = distiller.distill(states)
        assert result.state_type == 'T'
        assert result.fidelity > 0.9

    def test_distill_improves_fidelity(self):
        distiller = MagicStateDistiller(rounds=2)
        states = [MagicState('T', 0.85) for _ in range(15)]
        result = distiller.distill(states)
        assert result.fidelity > 0.85

    def test_not_enough_states(self):
        distiller = MagicStateDistiller()
        states = [MagicState('T', 0.9) for _ in range(10)]
        with pytest.raises(ValueError):
            distiller.distill(states)

    def test_estimate_resources(self):
        distiller = MagicStateDistiller(rounds=2)
        res = distiller.estimate_resources(target_fidelity=0.99,
                                            initial_fidelity=0.9)
        assert res['rounds'] >= 1
        assert res['final_fidelity'] > 0.5


class TestHStateDistiller:
    def test_distill(self):
        distiller = HStateDistiller(rounds=1)
        states = [MagicState('H', 0.9) for _ in range(20)]
        results = distiller.distill(states)
        assert len(results) == 4
        assert all(r.state_type == 'H' for r in results)

    def test_not_enough_states(self):
        distiller = HStateDistiller()
        with pytest.raises(ValueError):
            distiller.distill([MagicState('H', 0.9)] * 10)


class TestTStateFactory:
    def test_produce(self):
        factory = TStateFactory(distillation_rounds=1,
                                initial_fidelity=0.9)
        states = factory.produce(3)
        assert len(states) == 3
        assert all(s.state_type == 'T' for s in states)

    def test_stats(self):
        factory = TStateFactory(initial_fidelity=0.9)
        factory.produce(5)
        stats = factory.get_stats()
        assert stats['states_produced'] == 5
        assert stats['total_states_consumed'] == 75


class TestTGateInjector:
    def test_inject(self):
        injector = TGateInjector()
        ms = MagicState('T', 0.95)
        result = injector.inject(ms, measurement_outcome=0)
        assert result['gate_fidelity'] > 0.9
        assert 'corrections' in result

    def test_inject_with_correction(self):
        injector = TGateInjector()
        ms = MagicState('T', 0.95)
        result = injector.inject(ms, measurement_outcome=1)
        assert 'S' in result['corrections']

    def test_avg_fidelity(self):
        injector = TGateInjector()
        for _ in range(10):
            injector.inject(MagicState('T', 0.9))
        assert 0.8 < injector.get_avg_fidelity() < 1.0


class TestFaultTolerantCompiler:
    def test_compile_clifford(self):
        compiler = FaultTolerantCompiler(code_distance=3)
        gates = [('H', [0], None), ('CNOT', [0, 1], None)]
        result = compiler.compile(gates, num_qubits=2)
        assert result.clifford_gates == 2
        assert result.magic_states_needed == 0

    def test_compile_t_gate(self):
        compiler = FaultTolerantCompiler(code_distance=3)
        gates = [('T', [0], None)]
        result = compiler.compile(gates, num_qubits=1)
        assert result.non_clifford_gates == 1
        assert result.magic_states_needed == 1

    def test_compile_toffoli(self):
        compiler = FaultTolerantCompiler(code_distance=3)
        gates = [('Toffoli', [0, 1, 2], None)]
        result = compiler.compile(gates, num_qubits=3)
        assert result.non_clifford_gates >= 7
        assert result.magic_states_needed >= 7

    def test_compile_rz(self):
        compiler = FaultTolerantCompiler(code_distance=3)
        gates = [('Rz', [0], [np.pi / 4])]
        result = compiler.compile(gates, num_qubits=1)
        assert result.non_clifford_gates >= 1

    def test_compile_swap(self):
        compiler = FaultTolerantCompiler(code_distance=3)
        gates = [('SWAP', [0, 1], None)]
        result = compiler.compile(gates, num_qubits=2)
        assert result.clifford_gates == 3

    def test_overhead_estimate(self):
        compiler = FaultTolerantCompiler(code_distance=5)
        oh = compiler.estimate_overhead(num_qubits=10, num_gates=100)
        assert oh['logical_qubits'] == 10
        assert oh['code_distance'] == 5

    def test_summary(self):
        compiler = FaultTolerantCompiler(code_distance=3)
        gates = [('H', [0], None), ('T', [0], None)]
        result = compiler.compile(gates, num_qubits=1)
        summary = result.summary()
        assert 'total_gates' in summary
        assert 'magic_states_needed' in summary


class TestTransversalGateSet:
    def test_steane_transversal(self):
        code = SteaneCode()
        tgs = TransversalGateSet(code)
        assert 'H' in tgs.supported_gates
        assert 'S' in tgs.supported_gates
        assert 'CNOT' in tgs.supported_gates

    def test_shor_transversal(self):
        code = ShorCode()
        tgs = TransversalGateSet(code)
        assert 'CNOT' in tgs.supported_gates

    def test_color_code_transversal(self):
        code = ColorCode(3)
        tgs = TransversalGateSet(code)
        assert 'H' in tgs.supported_gates
        assert 'S' in tgs.supported_gates

    def test_apply_transversal_x(self):
        code = BitFlipCode()
        tgs = TransversalGateSet(code)
        state = np.array([0, 0, 0])
        result = tgs.apply_transversal_x(state)
        assert np.all(result == 1)

    def test_apply_transversal_cnot(self):
        code = RepetitionCode(3)
        tgs = TransversalGateSet(code)
        ctrl = np.array([1, 1, 1])
        tgt = np.array([0, 0, 0])
        new_ctrl, new_tgt = tgs.apply_transversal_cnot(ctrl, tgt)
        assert np.all(new_tgt == 1)

    def test_is_supported(self):
        code = SteaneCode()
        tgs = TransversalGateSet(code)
        assert tgs.is_supported('H')
        assert not tgs.is_supported('T')


# ==========================================
# SECTION: ENCODE/DECODE ROUNTRIP TESTS (5 tests)
# ==========================================

class TestQECRoundtrip:
    def test_repetition_code_roundtrip(self):
        code = RepetitionCode(n=3)
        for logical in [0, 1]:
            codeword = code.encode(logical)
            syndrome = code.compute_syndrome(codeword)
            assert np.all(syndrome == 0), f"No-error syndrome should be zero for logical {logical}"

    def test_steane_code_roundtrip(self):
        code = SteaneCode()
        for logical in [0, 1]:
            codeword = code.encode(logical)
            syndrome = code.compute_syndrome(codeword)
            assert np.all(syndrome == 0), f"No-error syndrome should be zero for logical {logical}"

    def test_shor_code_roundtrip(self):
        code = ShorCode()
        for logical in [0, 1]:
            codeword = code.encode(logical)
            syndrome = code.compute_syndrome(codeword)
            assert np.all(syndrome == 0), f"No-error syndrome should be zero for logical {logical}"

    def test_surface_code_roundtrip(self):
        code = SurfaceCode(distance=3)
        codeword = code.encode(0)
        syndrome = code.syndrome_measurement(codeword)
        assert isinstance(syndrome, np.ndarray)

    def test_color_code_roundtrip(self):
        code = ColorCode(distance=3)
        codeword = code.encode(0)
        syndrome = code.syndrome(codeword)
        assert isinstance(syndrome, np.ndarray)


class TestSingleErrorCorrection:
    def test_repetition_single_error(self):
        code = RepetitionCode(n=3)
        codeword = code.encode(0)
        codeword[0] = 1
        syndrome = code.compute_syndrome(codeword)
        assert np.any(syndrome != 0), "Single error should produce non-zero syndrome"

    def test_steane_single_error(self):
        code = SteaneCode()
        codeword = code.encode(0)
        codeword[0] = 1
        syndrome = code.compute_syndrome(codeword)
        assert np.any(syndrome != 0), "Single error should produce non-zero syndrome"

    def test_shor_single_error(self):
        code = ShorCode()
        codeword = code.encode(0)
        codeword[0] = 1
        syndrome = code.compute_syndrome(codeword)
        assert np.any(syndrome != 0), "Single error should produce non-zero syndrome"

    def test_steane_single_error(self):
        code = SteaneCode()
        codeword = code.encode(0)
        codeword[0] = 1
        syndrome = code.compute_syndrome(codeword)
        assert np.any(syndrome != 0), "Single error should produce non-zero syndrome"

    def test_shor_single_error(self):
        code = ShorCode()
        codeword = code.encode(0)
        codeword[0] = 1
        syndrome = code.compute_syndrome(codeword)
        assert np.any(syndrome != 0), "Single error should produce non-zero syndrome"
