"""Tests for step-through debugger backend: gate stepping, amplitudes, Bloch spheres, and purity/entanglement."""
import math
import numpy as np
import pytest
from abirqu.gui.server import QuantumServer


def test_step_debugger_bell_analytic():
    """Verify Bell state stepping, amplitudes, and entanglement within 1e-9."""
    server = QuantumServer()
    circuit = {
        "num_qubits": 2,
        "gates": [
            {"name": "H", "qubits": [0]},
            {"name": "CNOT", "qubits": [0, 1]},
        ],
    }

    # Step 0: Initial state |00>
    s0 = server._handle_step_circuit({"circuit": circuit, "step": 0})
    assert s0["step"] == 0
    assert abs(s0["amplitudes"][0]["magnitude"] - 1.0) < 1e-9
    assert abs(s0["bloch_vectors"][0]["z"] - 1.0) < 1e-9
    assert abs(s0["bloch_vectors"][0]["purity"] - 1.0) < 1e-9
    assert abs(s0["bloch_vectors"][0]["entanglement"] - 0.0) < 1e-9

    # Step 1: After H(0) -> (|00> + |10>) / sqrt(2)
    s1 = server._handle_step_circuit({"circuit": circuit, "step": 1})
    assert s1["step"] == 1
    expected_half = 1.0 / math.sqrt(2)
    assert abs(s1["amplitudes"][0]["magnitude"] - expected_half) < 1e-9
    assert abs(s1["bloch_vectors"][0]["x"] - 1.0) < 1e-9
    assert abs(s1["bloch_vectors"][0]["purity"] - 1.0) < 1e-9

    # Step 2: After CNOT(0, 1) -> Bell state (|00> + |11>) / sqrt(2)
    s2 = server._handle_step_circuit({"circuit": circuit, "step": 2})
    assert s2["step"] == 2
    assert abs(s2["amplitudes"][0]["magnitude"] - expected_half) < 1e-9
    assert abs(s2["amplitudes"][3]["magnitude"] - expected_half) < 1e-9
    assert abs(s2["amplitudes"][1]["magnitude"]) < 1e-9
    assert abs(s2["amplitudes"][2]["magnitude"]) < 1e-9

    # Max entanglement on both qubits: r_x=0, r_y=0, r_z=0, purity=0.5, entanglement=1.0
    for bv in s2["bloch_vectors"]:
        assert abs(bv["x"]) < 1e-9
        assert abs(bv["y"]) < 1e-9
        assert abs(bv["z"]) < 1e-9
        assert abs(bv["purity"] - 0.5) < 1e-9
        assert abs(bv["entanglement"] - 1.0) < 1e-9


def test_step_debugger_ghz_analytic():
    """Verify 3-qubit GHZ state (|000> + |111>)/sqrt(2) within 1e-9."""
    server = QuantumServer()
    circuit = {
        "num_qubits": 3,
        "gates": [
            {"name": "H", "qubits": [0]},
            {"name": "CNOT", "qubits": [0, 1]},
            {"name": "CNOT", "qubits": [1, 2]},
        ],
    }

    res = server._handle_step_circuit({"circuit": circuit, "step": 3})
    expected = 1.0 / math.sqrt(2)
    assert abs(res["amplitudes"][0]["magnitude"] - expected) < 1e-9
    assert abs(res["amplitudes"][7]["magnitude"] - expected) < 1e-9

    for i in range(1, 7):
        assert abs(res["amplitudes"][i]["magnitude"]) < 1e-9

    for bv in res["bloch_vectors"]:
        assert abs(bv["purity"] - 0.5) < 1e-9
        assert abs(bv["entanglement"] - 1.0) < 1e-9


def test_step_debugger_qft3_analytic():
    """Verify 3-qubit QFT uniform amplitude 1/sqrt(8) within 1e-9."""
    from abirqu.algorithms import qft_circuit
    server = QuantumServer()
    c = qft_circuit(3)
    gates = [{"name": g.name, "qubits": list(g.qubits), "params": list(g.params)} for g in c.gates]
    circuit = {"num_qubits": 3, "gates": gates}

    res = server._handle_step_circuit({"circuit": circuit, "step": len(gates)})
    expected_mag = 1.0 / math.sqrt(8)
    for entry in res["amplitudes"]:
        assert abs(entry["magnitude"] - expected_mag) < 1e-9


def test_step_debugger_grover2_analytic():
    """Verify 2-qubit Grover search deterministic target state |11> amplitude 1.0 within 1e-9."""
    server = QuantumServer()
    gates = [
        {"name": "H", "qubits": [0]},
        {"name": "H", "qubits": [1]},
        {"name": "CZ", "qubits": [0, 1]},
        {"name": "H", "qubits": [0]},
        {"name": "H", "qubits": [1]},
        {"name": "X", "qubits": [0]},
        {"name": "X", "qubits": [1]},
        {"name": "CZ", "qubits": [0, 1]},
        {"name": "X", "qubits": [0]},
        {"name": "X", "qubits": [1]},
        {"name": "H", "qubits": [0]},
        {"name": "H", "qubits": [1]},
    ]
    circuit = {"num_qubits": 2, "gates": gates}

    res = server._handle_step_circuit({"circuit": circuit, "step": len(gates)})
    assert abs(res["amplitudes"][3]["magnitude"] - 1.0) < 1e-9
    assert abs(res["amplitudes"][0]["magnitude"]) < 1e-9
    assert abs(res["amplitudes"][1]["magnitude"]) < 1e-9
    assert abs(res["amplitudes"][2]["magnitude"]) < 1e-9
