"""Tests for Noise Lab backend: depolarizing, amplitude damping, readout error, and TVD calculation."""
import pytest
from abirqu.gui.server import QuantumServer


def test_noiseless_tvd_is_zero():
    server = QuantumServer()
    circuit = {
        "num_qubits": 2,
        "gates": [
            {"name": "H", "qubits": [0]},
            {"name": "CNOT", "qubits": [0, 1]},
        ],
    }
    noise = {
        "depolarizing": 0.0,
        "amplitudeDamping": 0.0,
        "phaseDamping": 0.0,
        "readoutError": 0.0,
    }

    res = server._handle_simulate_noise_lab({"circuit": circuit, "noise": noise})
    assert res["success"] is True
    assert abs(res["tvd"] - 0.0) < 1e-9
    assert res["calibration"]["gate_fidelity"] == 1.0
    assert res["calibration"]["readout_fidelity"] == 1.0
    assert abs(res["calibration"]["purity_retention"] - 1.0) < 1e-9


def test_depolarizing_noise_increases_tvd():
    server = QuantumServer()
    circuit = {
        "num_qubits": 2,
        "gates": [
            {"name": "H", "qubits": [0]},
            {"name": "CNOT", "qubits": [0, 1]},
        ],
    }
    noise = {
        "depolarizing": 0.05,
        "amplitudeDamping": 0.0,
        "phaseDamping": 0.0,
        "readoutError": 0.0,
    }

    res = server._handle_simulate_noise_lab({"circuit": circuit, "noise": noise})
    assert res["success"] is True
    assert res["tvd"] > 0.0
    assert res["tvd"] <= 1.0
    assert res["calibration"]["gate_fidelity"] < 1.0
    assert res["calibration"]["purity_retention"] < 1.0


def test_readout_error_tvd():
    server = QuantumServer()
    circuit = {
        "num_qubits": 2,
        "gates": [
            {"name": "X", "qubits": [0]},
            {"name": "X", "qubits": [1]},
        ],
    }
    noise = {
        "depolarizing": 0.0,
        "amplitudeDamping": 0.0,
        "phaseDamping": 0.0,
        "readoutError": 0.1,
    }

    res = server._handle_simulate_noise_lab({"circuit": circuit, "noise": noise})
    assert res["success"] is True
    assert res["tvd"] > 0.0
    assert res["calibration"]["readout_fidelity"] == 0.9
