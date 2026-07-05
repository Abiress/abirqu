"""
Comprehensive tests for AbirQu Hardware module
Copyright 2026 Abir Maheshwari

Tests for calibration, characterization, noise profiler, hardware compiler, cloud manager.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import time
import pytest
from abirqu.hardware.calibration import (
    HardwareCalibration, QubitProperties, GateProperties,
    ReadoutCalibration, T1Calibration, T2Calibration,
)
from abirqu.hardware.characterization import (
    DeviceCharacterizer, RBResult, InterleavedRBResult,
    ProcessTomographyResult, SPAMResult,
)
from abirqu.hardware.noise_profiler import (
    NoiseProfiler, NoiseProfile, DriftTracker,
)
from abirqu.hardware.hw_compiler import (
    HardwareAwareCompiler, CompilationTarget, CompilationReport,
)
from abirqu.hardware.cloud_manager import (
    CloudManager, CloudProvider, CloudCredentials,
    ProviderStatus, ProviderConnection, AuthenticationError,
)


# ==================== QubitProperties Tests ====================

class TestQubitProperties:
    def test_creation(self):
        q = QubitProperties(qubit_id=0, t1_us=50.0, t2_us=70.0)
        assert q.qubit_id == 0
        assert q.t1_us == 50.0

    def test_coherence_time(self):
        q = QubitProperties(qubit_id=0, t1_us=50.0, t2_us=70.0)
        assert q.coherence_time == 35.0

    def test_coherence_t1_limited(self):
        q = QubitProperties(qubit_id=0, t1_us=20.0, t2_us=100.0)
        assert q.coherence_time == 20.0

    def test_is_healthy(self):
        q = QubitProperties(qubit_id=0, t1_us=50.0, t2_us=70.0,
                            readout_fidelity=0.98, x_error_rate=0.001)
        assert q.is_healthy is True

    def test_is_unhealthy(self):
        q = QubitProperties(qubit_id=0, t1_us=5.0, t2_us=70.0,
                            readout_fidelity=0.8, x_error_rate=0.1)
        assert q.is_healthy is False

    def test_to_dict(self):
        q = QubitProperties(qubit_id=0, t1_us=50.0, t2_us=70.0)
        d = q.to_dict()
        assert d['qubit_id'] == 0
        assert d['t1_us'] == 50.0
        assert 'coherence_time' in d
        assert 'is_healthy' in d


# ==================== GateProperties Tests ====================

class TestGateProperties:
    def test_creation(self):
        g = GateProperties(qubit_pair=(0, 1), fidelity=0.99, error_rate=0.01)
        assert g.qubit_pair == (0, 1)
        assert g.fidelity == 0.99

    def test_is_healthy(self):
        g = GateProperties(qubit_pair=(0, 1), fidelity=0.99, error_rate=0.01)
        assert g.is_healthy is True

    def test_is_unhealthy(self):
        g = GateProperties(qubit_pair=(0, 1), fidelity=0.90, error_rate=0.10)
        assert g.is_healthy is False

    def test_to_dict(self):
        g = GateProperties(qubit_pair=(0, 1), fidelity=0.99, error_rate=0.01)
        d = g.to_dict()
        assert d['fidelity'] == 0.99
        assert d['qubit_pair'] == [0, 1]


# ==================== HardwareCalibration Tests ====================

class TestHardwareCalibration:
    def test_init(self):
        cal = HardwareCalibration(num_qubits=5, backend_name='test')
        assert cal.num_qubits == 5
        assert cal.backend_name == 'test'
        assert len(cal.qubits) == 5

    def test_set_t1(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_t1(0, 100.0)
        assert cal.qubits[0].t1_us == 100.0
        assert cal.t1_cal.t1_values[0] == 100.0

    def test_set_t2(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_t2(1, 80.0)
        assert cal.qubits[1].t2_us == 80.0
        assert cal.t2_cal.t2_values[1] == 80.0

    def test_set_gate_error(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_gate_error(0, 1, 0.01)
        gate = cal.get_gate(0, 1)
        assert gate is not None
        assert gate.error_rate == 0.01
        assert gate.fidelity == 0.99

    def test_set_readout_error(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_readout_error(0, 0.02, 0.04)
        assert cal.qubits[0].readout_error_0 == 0.02
        assert cal.qubits[0].readout_error_1 == 0.04

    def test_healthy_qubits(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_t1(0, 50.0)
        cal.set_t1(1, 5.0)
        healthy = cal.get_healthy_qubits()
        assert 0 in healthy
        assert 1 not in healthy

    def test_best_pairs(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_gate_error(0, 1, 0.01)
        cal.set_gate_error(1, 2, 0.05)
        pairs = cal.get_best_qubit_pairs(1)
        assert pairs[0] == (0, 1)

    def test_average_fidelity(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_gate_error(0, 1, 0.01)
        cal.set_gate_error(1, 2, 0.03)
        avg = cal.average_gate_fidelity()
        assert 0.97 < avg < 1.0

    def test_generate_noise_model(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_t1(0, 50.0)
        cal.set_t2(0, 70.0)
        nm = cal.generate_noise_model()
        assert nm is not None

    def test_render_data(self):
        cal = HardwareCalibration(num_qubits=3)
        rd = cal.get_render_data()
        assert rd['num_qubits'] == 3
        assert 'qubits' in rd
        assert 'gates' in rd

    def test_crosstalk_matrix(self):
        cal = HardwareCalibration(num_qubits=3)
        cal.set_gate_error(0, 1, 0.01)
        matrix = cal.compute_crosstalk_matrix()
        assert len(matrix) == 3


# ==================== Characterization Tests ====================

class TestRBResult:
    def test_creation(self):
        rb = RBResult(num_cliffords=[1, 2, 4], survival_probabilities=[0.99, 0.98, 0.96])
        assert len(rb.num_cliffords) == 3

    def test_fit_exponential(self):
        rb = RBResult(num_cliffords=[1, 2, 4, 8, 16], survival_probabilities=[0.99, 0.98, 0.96, 0.92, 0.85])
        result = rb.fit_exponential()
        assert 'alpha' in result
        assert rb.fitted_error_per_gate >= 0

    def test_to_dict(self):
        rb = RBResult(num_cliffords=[1, 2], survival_probabilities=[0.99, 0.98])
        d = rb.to_dict()
        assert 'fitted_error_per_gate' in d
        assert 'fidelity_per_gate' in d


class TestDeviceCharacterizer:
    def test_init(self):
        dc = DeviceCharacterizer(num_qubits=5)
        assert dc.num_qubits == 5

    def test_run_rb(self):
        dc = DeviceCharacterizer(num_qubits=5)
        result = dc.run_rb(qubit=0, max_cliffords=100)
        assert result.qubit == 0
        assert len(result.num_cliffords) > 0
        assert result.fidelity_per_gate > 0

    def test_run_interleaved_rb(self):
        dc = DeviceCharacterizer(num_qubits=5)
        result = dc.run_interleaved_rb(0, 1, 'CNOT')
        assert result.gate_name == 'CNOT'
        assert 0 <= result.gate_fidelity <= 1

    def test_process_tomography(self):
        dc = DeviceCharacterizer(num_qubits=5)
        result = dc.run_process_tomography(0, 1, 'CNOT')
        assert result.qubit_pair == (0, 1)
        assert result.process_fidelity > 0

    def test_spam(self):
        dc = DeviceCharacterizer(num_qubits=5)
        spam = dc.characterize_spam()
        assert spam.overall_spam_fidelity > 0

    def test_rank_qubits(self):
        dc = DeviceCharacterizer(num_qubits=3)
        dc.run_rb(0)
        dc.run_rb(1)
        dc.run_rb(2)
        rankings = dc.rank_qubits()
        assert len(rankings) == 3
        assert rankings[0]['score'] >= rankings[1]['score']

    def test_render_data(self):
        dc = DeviceCharacterizer(num_qubits=3)
        dc.run_rb(0)
        rd = dc.get_render_data()
        assert 'rb_results' in rd
        assert 'rankings' in rd


class TestProcessTomographyResult:
    def test_creation(self):
        ptr = ProcessTomographyResult(qubit_pair=(0, 1), process_fidelity=0.99)
        assert ptr.qubit_pair == (0, 1)

    def test_to_dict(self):
        ptr = ProcessTomographyResult(qubit_pair=(0, 1))
        d = ptr.to_dict()
        assert d['qubit_pair'] == [0, 1]


# ==================== Noise Profiler Tests ====================

class TestNoiseProfile:
    def test_creation(self):
        np_ = NoiseProfile(backend_name='test', num_qubits=3)
        assert np_.backend_name == 'test'

    def test_averages(self):
        np_ = NoiseProfile(backend_name='test', num_qubits=3)
        np_.single_qubit_errors = {0: 0.001, 1: 0.002}
        assert np_.average_1q_error == 0.0015

    def test_worst_best_qubit(self):
        np_ = NoiseProfile(backend_name='test', num_qubits=3)
        np_.single_qubit_errors = {0: 0.001, 1: 0.005, 2: 0.003}
        assert np_.worst_qubit() == 1
        assert np_.best_qubit() == 0

    def test_worst_best_pair(self):
        np_ = NoiseProfile(backend_name='test', num_qubits=3)
        np_.two_qubit_errors = {(0, 1): 0.01, (1, 2): 0.05}
        assert np_.worst_pair() == (1, 2)
        assert np_.best_pair() == (0, 1)

    def test_generate_noise_model(self):
        np_ = NoiseProfile(backend_name='test', num_qubits=3)
        np_.single_qubit_errors = {0: 0.001, 1: 0.002}
        nm = np_.generate_noise_model()
        assert nm is not None

    def test_to_dict(self):
        np_ = NoiseProfile(backend_name='test', num_qubits=3)
        d = np_.to_dict()
        assert d['backend_name'] == 'test'


class TestNoiseProfiler:
    def test_init(self):
        profiler = NoiseProfiler(num_qubits=5, backend_name='test')
        assert profiler.num_qubits == 5

    def test_set_errors(self):
        profiler = NoiseProfiler(num_qubits=3, backend_name='test')
        profiler.set_single_qubit_error(0, 0.001)
        profiler.set_two_qubit_error(0, 1, 0.01)
        profiler.set_readout_error(0, 0.02)
        assert profiler.current_profile.single_qubit_errors[0] == 0.001
        assert profiler.current_profile.two_qubit_errors[(0, 1)] == 0.01

    def test_snapshot(self):
        profiler = NoiseProfiler(num_qubits=3, backend_name='test')
        profiler.set_single_qubit_error(0, 0.001)
        snap = profiler.snapshot()
        assert len(profiler.profile_history) == 1
        assert snap.single_qubit_errors[0] == 0.001

    def test_drift_detection(self):
        profiler = NoiseProfiler(num_qubits=3, backend_name='test')
        for i in range(5):
            profiler.set_single_qubit_error(0, 0.001 + i * 0.0001)
            profiler.snapshot()
        drift = profiler.detect_drift()
        assert 'drift_detected' in drift
        assert 'drift_magnitude' in drift

    def test_calibration_circuits(self):
        profiler = NoiseProfiler(num_qubits=3, backend_name='test')
        circuits = profiler.generate_calibration_circuits()
        assert len(circuits) > 0

    def test_render_data(self):
        profiler = NoiseProfiler(num_qubits=3, backend_name='test')
        rd = profiler.get_render_data()
        assert 'current_profile' in rd
        assert 'drift' in rd


class TestDriftTracker:
    def test_record(self):
        dt = DriftTracker()
        dt.record('t1', 50.0)
        dt.record('t1', 51.0)
        assert len(dt._data['t1']) == 2

    def test_get_drift(self):
        dt = DriftTracker()
        dt.record('t1', 50.0)
        dt.record('t1', 51.0)
        drift = dt.get_drift('t1')
        assert drift['drift'] == 1.0
        assert drift['stable'] is False

    def test_stable(self):
        dt = DriftTracker()
        dt.record('t1', 50.0)
        dt.record('t1', 50.005)
        drift = dt.get_drift('t1')
        assert drift['stable'] is True

    def test_all_drifts(self):
        dt = DriftTracker()
        dt.record('t1', 50.0)
        dt.record('t2', 70.0)
        all_d = dt.get_all_drifts()
        assert 't1' in all_d
        assert 't2' in all_d


# ==================== Hardware Compiler Tests ====================

class TestCompilationTarget:
    def test_creation(self):
        t = CompilationTarget(name='test', num_qubits=5)
        assert t.name == 'test'
        assert t.num_qubits == 5

    def test_native_gate_set(self):
        t = CompilationTarget(name='test', num_qubits=5, native_gates=['H', 'X', 'CNOT'])
        assert 'H' in t.native_gate_set
        assert 'CNOT' in t.native_gate_set

    def test_to_dict(self):
        t = CompilationTarget(name='test', num_qubits=5)
        d = t.to_dict()
        assert d['name'] == 'test'


class TestCompilationReport:
    def test_creation(self):
        r = CompilationReport()
        assert r.original_gates == 0

    def test_to_dict(self):
        r = CompilationReport(original_gates=10, compiled_gates=8)
        d = r.to_dict()
        assert d['original_gates'] == 10
        assert d['compiled_gates'] == 8


class TestHardwareAwareCompiler:
    def test_init(self):
        target = CompilationTarget(name='test', num_qubits=5)
        compiler = HardwareAwareCompiler(target)
        assert compiler.target.name == 'test'

    def test_compile_passthrough(self):
        target = CompilationTarget(name='test', num_qubits=5,
                                   native_gates=['H', 'X', 'CNOT', 'Rz'])
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]
        compiled, report = compiler.compile(gates, 5)
        assert report.original_gates == 2
        assert report.compiled_gates >= 2

    def test_compile_swap(self):
        target = CompilationTarget(name='test', num_qubits=5,
                                   native_gates=['H', 'X', 'CNOT', 'Rz'])
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'SWAP', 'qubits': [0, 1]}]
        compiled, report = compiler.compile(gates, 5)
        assert report.swap_insertions == 1
        assert report.compiled_gates == 3

    def test_compile_toffoli(self):
        target = CompilationTarget(name='test', num_qubits=5,
                                   native_gates=['H', 'X', 'CNOT', 'Rz'])
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'Toffoli', 'qubits': [0, 1, 2]}]
        compiled, report = compiler.compile(gates, 5)
        assert report.compiled_gates > 1

    def test_compile_cz(self):
        target = CompilationTarget(name='test', num_qubits=5,
                                   native_gates=['H', 'X', 'CNOT', 'Rz'])
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'CZ', 'qubits': [0, 1]}]
        compiled, report = compiler.compile(gates, 5)
        assert report.compiled_gates >= 3

    def test_fidelity_estimation(self):
        target = CompilationTarget(name='test', num_qubits=5)
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]
        compiled, report = compiler.compile(gates, 5)
        assert 0 < report.estimated_fidelity <= 1

    def test_time_estimation(self):
        target = CompilationTarget(name='test', num_qubits=5)
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]
        compiled, report = compiler.compile(gates, 5)
        assert report.estimated_time_ns > 0

    def test_render_data(self):
        target = CompilationTarget(name='test', num_qubits=5)
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'H', 'qubits': [0]}]
        compiler.compile(gates, 5)
        rd = compiler.get_render_data()
        assert 'target' in rd
        assert 'report' in rd


# ==================== Cloud Manager Tests ====================

class TestCloudCredentials:
    def test_creation(self):
        creds = CloudCredentials(provider=CloudProvider.IBM_QUANTUM, api_key='test_key')
        assert creds.provider == CloudProvider.IBM_QUANTUM
        assert creds.api_key == 'test_key'

    def test_from_env(self):
        os.environ['IONQ_API_KEY'] = 'test_key'
        creds = CloudCredentials.from_env(CloudProvider.IONQ)
        assert creds.api_key == 'test_key'
        del os.environ['IONQ_API_KEY']

    def test_to_dict(self):
        creds = CloudCredentials(provider=CloudProvider.IBM_QUANTUM, api_key='test')
        d = creds.to_dict()
        assert d['provider'] == 'ibm_quantum'
        assert d['has_api_key'] is True


class TestProviderConnection:
    def test_creation(self):
        conn = ProviderConnection(provider=CloudProvider.IBM_QUANTUM)
        assert conn.status == ProviderStatus.DISCONNECTED

    def test_to_dict(self):
        conn = ProviderConnection(provider=CloudProvider.IBM_QUANTUM)
        d = conn.to_dict()
        assert d['provider'] == 'ibm_quantum'
        assert d['status'] == 'disconnected'


class TestCloudManager:
    def test_init(self):
        cm = CloudManager()
        assert len(cm.connections) >= 0

    def test_add_credentials(self):
        cm = CloudManager()
        cm.add_credentials(CloudProvider.IONQ, api_key='test_key')
        assert CloudProvider.IONQ in cm.credentials

    def test_connect(self):
        cm = CloudManager()
        cm.add_credentials(CloudProvider.IONQ, api_key='test_key')
        result = cm.connect(CloudProvider.IONQ)
        assert result is True
        assert cm.get_status(CloudProvider.IONQ) == ProviderStatus.CONNECTED

    def test_connect_no_credentials(self):
        cm = CloudManager()
        with pytest.raises(AuthenticationError):
            cm.connect(CloudProvider.QUANTINUUM)

    def test_disconnect(self):
        cm = CloudManager()
        cm.add_credentials(CloudProvider.IONQ, api_key='test_key')
        cm.connect(CloudProvider.IONQ)
        cm.disconnect(CloudProvider.IONQ)
        assert cm.get_status(CloudProvider.IONQ) == ProviderStatus.DISCONNECTED

    def test_connected_providers(self):
        cm = CloudManager()
        cm.add_credentials(CloudProvider.IONQ, api_key='test1')
        cm.add_credentials(CloudProvider.IBM_QUANTUM, api_key='test2')
        cm.connect(CloudProvider.IONQ)
        cm.connect(CloudProvider.IBM_QUANTUM)
        connected = cm.get_connected_providers()
        assert len(connected) >= 2

    def test_list_all_providers(self):
        cm = CloudManager()
        providers = cm.list_all_providers()
        assert len(providers) >= 10

    def test_render_data(self):
        cm = CloudManager()
        rd = cm.get_render_data()
        assert 'providers' in rd
        assert 'connected' in rd

    def test_callbacks(self):
        cm = CloudManager()
        received = []
        cm.on('connected', lambda d: received.append(d))
        cm.add_credentials(CloudProvider.IONQ, api_key='test')
        cm.connect(CloudProvider.IONQ)
        assert len(received) >= 1


# ==================== Integration Tests ====================

class TestIntegration:
    def test_calibration_to_noise_model(self):
        cal = HardwareCalibration(num_qubits=3, backend_name='test')
        cal.set_t1(0, 50.0)
        cal.set_t2(0, 70.0)
        cal.set_gate_error(0, 1, 0.01)
        nm = cal.generate_noise_model()
        assert nm.num_qubits == 3

    def test_profiler_to_calibration(self):
        profiler = NoiseProfiler(num_qubits=3, backend_name='test')
        profiler.set_single_qubit_error(0, 0.001)
        profiler.set_t1(0, 50.0)
        profiler.set_t2(0, 70.0)
        cal = HardwareCalibration(num_qubits=3)
        for q, err in profiler.current_profile.single_qubit_errors.items():
            cal.set_t1(q, profiler.current_profile.t1_values.get(q, 50.0))
        assert cal.num_qubits == 3

    def test_characterizer_to_compiler(self):
        dc = DeviceCharacterizer(num_qubits=5)
        dc.run_rb(0)
        target = CompilationTarget(name='test', num_qubits=5)
        compiler = HardwareAwareCompiler(target)
        gates = [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]
        compiled, report = compiler.compile(gates, 5)
        assert report.compiled_gates >= 2

    def test_full_workflow(self):
        cal = HardwareCalibration(num_qubits=5, backend_name='test_backend')
        cal.set_t1(0, 50.0)
        cal.set_t2(0, 70.0)
        cal.set_gate_error(0, 1, 0.01)

        profiler = NoiseProfiler(num_qubits=5, backend_name='test_backend')
        for q in range(5):
            profiler.set_single_qubit_error(q, 0.001)
            profiler.set_t1(q, 50.0)
            profiler.set_t2(q, 70.0)
        profiler.snapshot()

        dc = DeviceCharacterizer(num_qubits=5)
        dc.run_rb(0)
        dc.run_interleaved_rb(0, 1, 'CNOT')
        dc.characterize_spam()

        target = CompilationTarget(
            name='test_backend', num_qubits=5,
            native_gates=['H', 'X', 'CNOT', 'Rz'],
        )
        compiler = HardwareAwareCompiler(target)
        gates = [
            {'name': 'H', 'qubits': [0]},
            {'name': 'CNOT', 'qubits': [0, 1]},
            {'name': 'SWAP', 'qubits': [1, 2]},
        ]
        compiled, report = compiler.compile(gates, 5)

        cm = CloudManager()
        cm.add_credentials(CloudProvider.IONQ, api_key='test')
        cm.connect(CloudProvider.IONQ)

        assert report.compiled_gates >= 3
        assert report.swap_insertions == 1
        assert len(compiled) >= 3
        assert cm.get_status(CloudProvider.IONQ) == ProviderStatus.CONNECTED


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
