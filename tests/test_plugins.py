"""Tests for AbirQu plugins."""
import math
import pytest


class TestErrorMitigationPlugin:
    def test_import(self):
        from plugins.error_mitigation import (
            zero_noise_extrapolation,
            probabilistic_error_cancellation,
            clifford_data_regression,
            mitigate_readout_error,
        )
        assert zero_noise_extrapolation is not None
        assert probabilistic_error_cancellation is not None
        assert clifford_data_regression is not None
        assert mitigate_readout_error is not None

    def test_zne_linear(self):
        from plugins.error_mitigation import zero_noise_extrapolation
        ideal = {"counts": {"00": 500, "11": 500}}
        noisy = [
            {"counts": {"00": 450, "11": 550}},
            {"counts": {"00": 400, "11": 600}},
        ]
        result = zero_noise_extrapolation(ideal, noisy, [1.0, 2.0], method="linear")
        assert "mitigated_expval" in result
        assert result["method"] == "linear"
        assert len(result["noisy_expvals"]) == 2

    def test_zne_richardson(self):
        from plugins.error_mitigation import zero_noise_extrapolation
        ideal = {"counts": {"00": 500, "11": 500}}
        noisy = [
            {"counts": {"00": 450, "11": 550}},
            {"counts": {"00": 400, "11": 600}},
            {"counts": {"00": 350, "11": 650}},
        ]
        result = zero_noise_extrapolation(ideal, noisy, [1.0, 2.0, 3.0], method="richardson")
        assert result["method"] == "richardson"
        assert "mitigated_expval" in result

    def test_pec(self):
        from plugins.error_mitigation import probabilistic_error_cancellation
        noisy_counts = {"00": 450, "11": 550}
        noise_model = {(0, "readout"): 0.05}
        result = probabilistic_error_cancellation(noisy_counts, noise_model, shots=1000)
        assert result["compensation_applied"] is True
        assert "mitigated_counts" in result

    def test_cdr(self):
        from plugins.error_mitigation import clifford_data_regression
        training = [
            {"ideal_expval": 1.0, "noisy_expval": 0.9},
            {"ideal_expval": -1.0, "noisy_expval": -0.85},
        ]
        noisy = [{"counts": {"00": 450, "11": 550}}]
        result = clifford_data_regression(training, noisy)
        assert "mitigated_expvals" in result
        assert result["alpha"] is not None

    def test_readout_mitigation(self):
        from plugins.error_mitigation import mitigate_readout_error
        noisy = {"00": 450, "11": 550}
        cal_matrix = [[0.95, 0.05], [0.05, 0.95]]
        result = mitigate_readout_error(noisy, cal_matrix, shots=1000)
        assert result["applied"] is True
        assert "mitigated_counts" in result


class TestVQEAdvancedPlugin:
    def test_import(self):
        from plugins.vqe_advanced import (
            uccsd_ansatz,
            hardware_efficient_ansatz,
            adam_optimizer,
            adaptive_vqe,
        )
        assert uccsd_ansatz is not None
        assert hardware_efficient_ansatz is not None
        assert adam_optimizer is not None
        assert adaptive_vqe is not None

    def test_uccsd_ansatz(self):
        from plugins.vqe_advanced import uccsd_ansatz
        result = uccsd_ansatz(num_qubits=4, num_electrons=2, depth=1)
        assert result["num_qubits"] == 4
        assert result["num_parameters"] > 0
        assert result["ansatz"] == "uccsd"

    def test_hardware_efficient_ansatz(self):
        from plugins.vqe_advanced import hardware_efficient_ansatz
        result = hardware_efficient_ansatz(num_qubits=3, entangler="circular", repetitions=2)
        assert result["num_qubits"] == 3
        assert result["num_parameters"] > 0
        assert len(result["gates"]) > 0

    def test_adam_optimizer(self):
        from plugins.vqe_advanced import adam_optimizer
        params = [0.1, 0.2, 0.3]
        grads = [0.01, -0.02, 0.03]
        new_params, state = adam_optimizer(params, grads)
        assert len(new_params) == 3
        assert state["t"] == 1
        assert all(new_params[i] != params[i] for i in range(3))

    def test_adam_convergence(self):
        from plugins.vqe_advanced import adam_optimizer
        params = [1.0, 1.0]
        state = None
        for _ in range(100):
            grads = [2 * p for p in params]
            params, state = adam_optimizer(params, grads, state=state, lr=0.01)
        assert abs(params[0]) < 0.5
        assert abs(params[1]) < 0.5

    def test_adaptive_vqe(self):
        from plugins.vqe_advanced import adaptive_vqe
        result = adaptive_vqe(num_qubits=4, num_electrons=2, max_ops=5)
        assert result["num_operators"] <= 5
        assert result["ansatz"] == "adaptive_vqe"


class TestQuantumMLPlugin:
    def test_import(self):
        from plugins.quantum_ml import (
            angle_encoding,
            quantum_kernel_matrix,
            variational_classifier,
            qnn_dense_layer,
        )
        assert angle_encoding is not None
        assert quantum_kernel_matrix is not None
        assert variational_classifier is not None
        assert qnn_dense_layer is not None

    def test_angle_encoding(self):
        from plugins.quantum_ml import angle_encoding
        result = angle_encoding([0.5, 1.0, 1.5], num_qubits=3)
        assert result["num_qubits"] == 3
        assert len(result["gates"]) == 3
        assert result["encoding"] == "angle"

    def test_kernel_matrix(self):
        from plugins.quantum_ml import quantum_kernel_matrix
        x1 = [[0.1, 0.2], [0.3, 0.4]]
        x2 = [[0.1, 0.2], [0.5, 0.6]]
        result = quantum_kernel_matrix(x1, x2, num_qubits=2)
        assert result["shape"] == [2, 2]
        assert len(result["kernel_matrix"]) == 2

    def test_variational_classifier(self):
        from plugins.quantum_ml import variational_classifier
        result = variational_classifier(num_qubits=3, num_classes=2)
        assert result["num_qubits"] == 3
        assert result["num_classes"] == 2
        assert result["num_parameters"] > 0

    def test_qnn_dense_layer(self):
        from plugins.quantum_ml import qnn_dense_layer
        result = qnn_dense_layer(num_qubits=3, entangler="linear")
        assert result["num_qubits"] == 3
        assert result["num_parameters"] == 6  # 3 qubits * 2 params (Ry + Rz)
        assert len(result["gates"]) > 3  # At least rotations + entangling


class TestNoiseCharacterizationPlugin:
    def test_import(self):
        from plugins.noise_characterization import (
            generate_rb_circuits,
            fit_rb_decay,
            characterize_noise_spectrum,
        )
        assert generate_rb_circuits is not None
        assert fit_rb_decay is not None
        assert characterize_noise_spectrum is not None

    def test_rb_circuits(self):
        from plugins.noise_characterization import generate_rb_circuits
        result = generate_rb_circuits(num_qubits=1, depths=[1, 2, 4], num_circuits=3, seed=42)
        assert result["total_circuits"] == 9  # 3 depths * 3 circuits
        assert len(result["circuits"]) == 9

    def test_fit_rb_decay(self):
        from plugins.noise_characterization import fit_rb_decay
        depths = [1, 2, 4, 8]
        fidelities = [0.95, 0.90, 0.81, 0.66]
        result = fit_rb_decay(depths, fidelities)
        assert result["converged"] is True
        assert 0 < result["depolarizing_parameter"] < 1

    def test_noise_spectrum(self):
        from plugins.noise_characterization import characterize_noise_spectrum
        times = [0, 10, 20, 30, 40]
        decay = [1.0, 0.9, 0.81, 0.73, 0.65]
        result = characterize_noise_spectrum(times, decay)
        assert result["t1"] > 0
        assert result["t2"] > 0


class TestCircuitOptimizationPlugin:
    def test_import(self):
        from plugins.circuit_optimization import (
            fuse_gates,
            template_optimize,
            reduce_depth,
        )
        assert fuse_gates is not None
        assert template_optimize is not None
        assert reduce_depth is not None

    def test_fuse_identity_gates(self):
        from plugins.circuit_optimization import fuse_gates
        gates = [{"type": "H", "qubit": 0}, {"type": "H", "qubit": 0}]
        result = fuse_gates(gates, num_qubits=1)
        assert result["fused_count"] == 0
        assert result["gates_fused"] == 2

    def test_template_optimize(self):
        from plugins.circuit_optimization import template_optimize
        gates = [
            {"type": "S", "qubit": 0},
            {"type": "H", "qubit": 0},
            {"type": "S", "qubit": 0},
        ]
        result = template_optimize(gates, num_qubits=1)
        assert result["optimized_count"] <= result["original_count"]

    def test_reduce_depth(self):
        from plugins.circuit_optimization import reduce_depth
        gates = [
            {"type": "X", "qubit": 0},
            {"type": "X", "qubit": 1},
            {"type": "CNOT", "qubit": 0, "target": 1},
        ]
        result = reduce_depth(gates, num_qubits=2)
        assert result["depth"] <= 3
        assert result["gate_count"] == 3

    def test_commuting_gates(self):
        from plugins.circuit_optimization import commute_optimize
        gates = [
            {"type": "Z", "qubit": 0},
            {"type": "X", "qubit": 1},
        ]
        result = commute_optimize(gates, num_qubits=2)
        assert len(result["gates"]) == 2


class TestPluginDiscovery:
    def test_entry_points_discover(self):
        from abirqu.plugins import PluginDiscovery
        discovery = PluginDiscovery()
        plugins = discovery.discover()
        assert isinstance(plugins, list)

    def test_plugin_registry(self):
        from abirqu.plugin_market import PluginRegistry, PluginManifest
        registry = PluginRegistry()
        manifest = PluginManifest(
            name="test_plugin",
            version="0.1.0",
            author="test",
            description="test plugin",
            hooks=["run"],
            permissions=[],
        )
        code = "def on_run(data): return data"
        result = registry.register(manifest, code)
        assert result["loaded"] is True
        plugins = registry.list_plugins()
        assert any(p["name"] == "test_plugin" for p in plugins)

    def test_marketplace_search(self):
        from abirqu.plugin_market import AbirHubMarketplace
        marketplace = AbirHubMarketplace("1.2.4")
        result = marketplace.search()
        assert len(result["results"]) > 0

    def test_marketplace_install(self):
        from abirqu.plugin_market import AbirHubMarketplace
        marketplace = AbirHubMarketplace("1.2.4")
        result = marketplace.install("abirqu-noise-pack")
        assert result["installed"] is True

    def test_plugin_base_protocol(self):
        from abirqu.plugin_market import PluginBase
        assert hasattr(PluginBase, 'activate')
        assert hasattr(PluginBase, 'deactivate')
        assert hasattr(PluginBase, 'get_manifest')
