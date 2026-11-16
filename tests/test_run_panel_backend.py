"""Tests for Run Panel backend: simulator engine choice, qubit limits, seed, and cancellation."""
import pytest
from abirqu import Circuit
from abirqu.gui.server import QuantumServer, JobStatus


def test_simulator_qubit_limit_refusal():
    server = QuantumServer()
    # 30-qubit circuit exceeds statevector limit of 28
    circuit_data = {"num_qubits": 30, "gates": []}
    with pytest.raises(ValueError) as exc:
        server._handle_execute({
            "circuit": circuit_data,
            "simulator": "statevector",
            "shots": 1024,
        })
    assert "exceeding statevector limit" in str(exc.value)


def test_simulator_within_limit_success():
    server = QuantumServer()
    c = Circuit(2)
    c.h(0)
    c.cx(0, 1)
    circuit_data = {"num_qubits": 2, "gates": [{"name": "H", "qubits": [0]}, {"name": "CNOT", "qubits": [0, 1]}]}

    res = server._simulate_circuit(circuit_data, shots=500, simulator="statevector", seed=42)
    assert res["success"] is True
    assert res["num_qubits"] == 2
    assert "00" in res["counts"] or "11" in res["counts"]
    assert "statevector" in res
    assert len(res["statevector"]) == 4


def test_simulator_seed_reproducibility():
    server = QuantumServer()
    circuit_data = {"num_qubits": 2, "gates": [{"name": "H", "qubits": [0]}, {"name": "CNOT", "qubits": [0, 1]}]}

    res1 = server._simulate_circuit(circuit_data, shots=1000, simulator="statevector", seed=12345)
    res2 = server._simulate_circuit(circuit_data, shots=1000, simulator="statevector", seed=12345)
    assert res1["counts"] == res2["counts"]


def test_cancel_job():
    server = QuantumServer()
    circuit_data = {"num_qubits": 2, "gates": [{"name": "H", "qubits": [0]}]}
    job_dict = server._handle_execute({
        "circuit": circuit_data,
        "simulator": "statevector",
        "shots": 1000,
    })
    job_id = job_dict["job_id"]

    cancel_res = server._handle_cancel({"job_id": job_id})
    assert cancel_res["status"] == "cancelled" or cancel_res.get("status") == JobStatus.CANCELLED.value
    status_res = server._handle_status({"job_id": job_id})
    assert status_res["status"] == JobStatus.CANCELLED.value
