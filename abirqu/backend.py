"""
AbirQu Backend Framework
========================
Provides a unified, hardware-agnostic backend API for running quantum circuits.

- FastBackend   : Local Rust statevector simulator (100% working, AVX-512/SIMD)
- QuantumBackend: Abstract base class for all backends
- IBMQBackend   : IBM Quantum stub (requires qiskit-ibm-runtime)
- BraketBackend : AWS Braket stub (requires amazon-braket-sdk)
- AzureBackend  : Azure Quantum stub (requires azure-quantum)
- IonQBackend   : IonQ REST API stub
- CirqBackend   : Google Quantum / Cirq stub

Usage
-----
    from abirqu.backend import FastBackend
    from abirqu.circuit import Circuit

    circ = Circuit(2)
    circ.h(0)
    circ.cnot(0, 1)

    backend = FastBackend(n_qubits=2)
    result = backend.run_circuit(circ, shots=1024)
    print(result["counts"])   # e.g. {'00': 512, '11': 512}
    print(result["probabilities"])
"""

from __future__ import annotations

import abc
import math
import random
from typing import Any, Dict, List, Optional

import numpy as np

from .circuit import Circuit
from .simulator import SimulatorBackend, RustSimulator, _serialize_circuit, HAS_RUST_CORE


# ──────────────────────────────────────────────────────────────────────────────
# Base class
# ──────────────────────────────────────────────────────────────────────────────

class QuantumBackend(abc.ABC):
    """Abstract base class for all AbirQu backends.

    Every backend must implement :meth:`run_circuit` and expose a
    ``name`` attribute.  The return value of ``run_circuit`` is always a
    ``Result`` dict with at least the keys ``success``, ``counts``, and
    ``probabilities``.
    """

    name: str = "QuantumBackend"

    @abc.abstractmethod
    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute *circuit* and return a result dictionary.

        Parameters
        ----------
        circuit: Circuit
            The quantum circuit to execute.
        shots: int
            Number of measurement shots.  Pass ``0`` to get only the
            statevector (no sampling).

        Returns
        -------
        dict with keys:
            success      – bool
            backend      – str (backend name)
            shots        – int
            counts       – dict[bitstring, count]
            probabilities– dict[bitstring, probability] | None
            statevector  – list[complex] | None  (if shots==0)
        """

    def run_batch(
        self,
        circuits: List[Circuit],
        shots: int = 1024,
    ) -> List[Dict[str, Any]]:
        """Execute multiple circuits sequentially (override for parallelism)."""
        return [self.run_circuit(c, shots=shots) for c in circuits]

    @staticmethod
    def _counts_to_probs(counts: Dict[str, int], shots: int) -> Dict[str, float]:
        if shots == 0:
            return {}
        return {k: v / shots for k, v in counts.items()}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


# ──────────────────────────────────────────────────────────────────────────────
# FastBackend — local Rust statevector (100% working)
# ──────────────────────────────────────────────────────────────────────────────

class FastBackend(QuantumBackend):
    """High-performance local Rust statevector simulator.

    Uses the compiled Rust core (AVX-512/SIMD optimised) when available,
    falling back to the NumPy QVM for portability.  This is the fastest
    and most accurate backend available — all computations are exact.

    Parameters
    ----------
    n_qubits: int
        Number of qubits.  Inferred from the circuit when ``None``.
    use_gpu: bool
        Attempt to use GPU acceleration (requires CUDA build).
    """

    name = "AbirQu-FastBackend"

    def __init__(self, n_qubits: Optional[int] = None, use_gpu: bool = False):
        self._n_qubits = n_qubits
        self._use_gpu = use_gpu
        self._delegate = SimulatorBackend(use_gpu=use_gpu)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        noise_model=None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run circuit on the local Rust simulator and return results."""
        n = self._n_qubits or circuit.num_qubits

        # ── Rust path ─────────────────────────────────────────────────────────
        if HAS_RUST_CORE:
            sim = RustSimulator(n)
            sim.run_circuit(_serialize_circuit(circuit))

            # Get raw probabilities as bytes for speed
            raw = sim.get_probabilities_bytes()
            if isinstance(raw, (bytes, bytearray)):
                probs_arr = np.frombuffer(raw, dtype=np.float64).copy()
            else:
                probs_arr = np.array(sim.get_probabilities(), dtype=np.float64)

            # Apply optional noise
            if noise_model is not None:
                try:
                    probs_arr = noise_model.apply_to_probs_array(probs_arr, n)
                except Exception:
                    pass

            # Normalise
            total = probs_arr.sum()
            if total > 0:
                probs_arr /= total

            probs_dict = {
                format(i, f"0{n}b"): float(p)
                for i, p in enumerate(probs_arr)
                if p > 0
            }

            counts: Dict[str, int] = {}
            if shots > 0:
                indices = np.random.choice(len(probs_arr), size=shots, p=probs_arr)
                unique_idx, raw_counts = np.unique(indices, return_counts=True)
                counts = {
                    format(int(u), f"0{n}b"): int(c)
                    for u, c in zip(unique_idx, raw_counts)
                }

            # Retrieve statevector for shots=0 mode
            statevector = None
            if shots == 0:
                try:
                    statevector = list(sim.get_statevector())
                except Exception:
                    statevector = None

            return {
                "success": True,
                "backend": self.name,
                "shots": shots,
                "counts": counts,
                "probabilities": probs_dict,
                "statevector": statevector,
            }

        # ── NumPy fallback ─────────────────────────────────────────────────────
        result = self._delegate.run(circuit, shots=shots, noise_model=noise_model)
        counts = result.get("counts", {})
        probs = self._counts_to_probs(counts, shots) if shots > 0 else {}
        return {
            "success": result.get("success", True),
            "backend": self.name + "(numpy-fallback)",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# IBM Quantum backend
# ──────────────────────────────────────────────────────────────────────────────

class IBMQBackend(QuantumBackend):
    """IBM Quantum backend using qiskit-ibm-runtime.

    Requires: ``pip install qiskit qiskit-ibm-runtime``

    Parameters
    ----------
    token: str
        IBM Quantum API token from https://quantum.ibm.com/
    backend_name: str
        Name of the IBM device, e.g. ``'ibm_osaka'`` or ``'ibmq_qasm_simulator'``.
    instance: str
        Hub/group/project in the form ``'ibm-q/open/main'``.
    """

    name = "IBMQuantum"

    def __init__(
        self,
        token: str,
        backend_name: str = "ibmq_qasm_simulator",
        instance: str = "ibm-q/open/main",
    ):
        self.token = token
        self.backend_name = backend_name
        self.instance = instance
        self._service = None
        self._backend = None

    def _connect(self):
        if self._service is not None:
            return
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            QiskitRuntimeService.save_account(
                channel="ibm_quantum", token=self.token, overwrite=True
            )
            self._service = QiskitRuntimeService(
                channel="ibm_quantum", instance=self.instance
            )
            self._backend = self._service.backend(self.backend_name)
        except ImportError as exc:
            raise RuntimeError(
                "IBMQBackend requires 'qiskit-ibm-runtime'. "
                "Install with: pip install qiskit qiskit-ibm-runtime"
            ) from exc

    def _circuit_to_qiskit(self, circuit: Circuit):
        """Convert AbirQu Circuit to a Qiskit QuantumCircuit."""
        from qiskit import QuantumCircuit as QkCircuit
        qc = QkCircuit(circuit.num_qubits, circuit.num_qubits)
        for gate in getattr(circuit, "gates", []):
            name = gate.name.upper()
            q = list(gate.qubits)
            p = gate.params
            if name == "H":
                qc.h(q[0])
            elif name in ("CNOT", "CX"):
                qc.cx(q[0], q[1])
            elif name == "X":
                qc.x(q[0])
            elif name == "Y":
                qc.y(q[0])
            elif name == "Z":
                qc.z(q[0])
            elif name == "S":
                qc.s(q[0])
            elif name == "T":
                qc.t(q[0])
            elif name == "RX":
                qc.rx(float(p[0]), q[0])
            elif name == "RY":
                qc.ry(float(p[0]), q[0])
            elif name == "RZ":
                qc.rz(float(p[0]), q[0])
            elif name == "CZ":
                qc.cz(q[0], q[1])
            elif name == "SWAP":
                qc.swap(q[0], q[1])
        qc.measure_all()
        return qc

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        self._connect()
        from qiskit import transpile
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        qc = self._circuit_to_qiskit(circuit)
        tqc = transpile(qc, self._backend)
        sampler = Sampler(mode=self._backend)
        job = sampler.run([tqc], shots=shots)
        pub_result = job.result()[0]
        raw_counts = pub_result.data.meas.get_counts()
        total = sum(raw_counts.values())
        probs = {k: v / total for k, v in raw_counts.items()}
        return {
            "success": True,
            "backend": f"IBMQ:{self.backend_name}",
            "shots": shots,
            "counts": dict(raw_counts),
            "probabilities": probs,
            "statevector": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# AWS Braket backend
# ──────────────────────────────────────────────────────────────────────────────

class BraketBackend(QuantumBackend):
    """AWS Braket backend.

    Requires: ``pip install amazon-braket-sdk``

    Parameters
    ----------
    device_arn: str
        ARN of the Braket device, e.g.
        ``'arn:aws:braket:::device/quantum-simulator/amazon/sv1'``
    s3_bucket: str
        S3 bucket for storing Braket results.
    s3_prefix: str
        S3 key prefix for result files.
    """

    name = "AWS-Braket"

    def __init__(
        self,
        device_arn: str = "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        s3_bucket: str = "",
        s3_prefix: str = "abirqu-results",
    ):
        self.device_arn = device_arn
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix

    def _circuit_to_braket(self, circuit: Circuit):
        try:
            from braket.circuits import Circuit as BCircuit, Gate, Qubit
        except ImportError as exc:
            raise RuntimeError(
                "BraketBackend requires 'amazon-braket-sdk'. "
                "Install with: pip install amazon-braket-sdk"
            ) from exc
        bc = BCircuit()
        for gate in getattr(circuit, "gates", []):
            name = gate.name.upper()
            q = list(gate.qubits)
            p = gate.params
            if name == "H":
                bc.h(q[0])
            elif name in ("CNOT", "CX"):
                bc.cnot(q[0], q[1])
            elif name == "X":
                bc.x(q[0])
            elif name == "Y":
                bc.y(q[0])
            elif name == "Z":
                bc.z(q[0])
            elif name == "S":
                bc.s(q[0])
            elif name == "T":
                bc.t(q[0])
            elif name == "RX":
                bc.rx(q[0], float(p[0]))
            elif name == "RY":
                bc.ry(q[0], float(p[0]))
            elif name == "RZ":
                bc.rz(q[0], float(p[0]))
            elif name == "CZ":
                bc.cz(q[0], q[1])
            elif name == "SWAP":
                bc.swap(q[0], q[1])
        return bc

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from braket.aws import AwsDevice, AwsSession
        except ImportError as exc:
            raise RuntimeError(
                "BraketBackend requires 'amazon-braket-sdk'."
            ) from exc
        bc = self._circuit_to_braket(circuit)
        device = AwsDevice(self.device_arn)
        s3_dest = (self.s3_bucket, self.s3_prefix) if self.s3_bucket else None
        task = device.run(bc, s3_destination_folder=s3_dest, shots=shots)
        result = task.result()
        counts = dict(result.measurement_counts)
        total = sum(counts.values())
        probs = {k: v / total for k, v in counts.items()}
        return {
            "success": True,
            "backend": f"Braket:{self.device_arn.split('/')[-1]}",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Azure Quantum backend
# ──────────────────────────────────────────────────────────────────────────────

class AzureBackend(QuantumBackend):
    """Azure Quantum backend.

    Requires: ``pip install azure-quantum qiskit-ionq``

    Parameters
    ----------
    resource_id: str
        Azure Quantum Workspace resource ID.
    location: str
        Azure region, e.g. ``'eastus'``.
    provider_id: str
        Provider, e.g. ``'ionq'`` or ``'quantinuum'``.
    """

    name = "Azure-Quantum"

    def __init__(
        self,
        resource_id: str,
        location: str = "eastus",
        provider_id: str = "ionq",
        target: str = "ionq.simulator",
    ):
        self.resource_id = resource_id
        self.location = location
        self.provider_id = provider_id
        self.target = target

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from azure.quantum import Workspace
            from azure.quantum.qiskit import AzureQuantumProvider
        except ImportError as exc:
            raise RuntimeError(
                "AzureBackend requires 'azure-quantum'. "
                "Install with: pip install azure-quantum"
            ) from exc
        workspace = Workspace(resource_id=self.resource_id, location=self.location)
        provider = AzureQuantumProvider(workspace=workspace)
        backend = provider.get_backend(self.target)

        from qiskit import QuantumCircuit as QkCircuit, transpile
        # Reuse IBM's helper to build a Qiskit circuit
        ibmq_helper = IBMQBackend.__new__(IBMQBackend)
        qc = ibmq_helper._circuit_to_qiskit(circuit)
        tqc = transpile(qc, backend)
        job = backend.run(tqc, shots=shots)
        result = job.result()
        counts = result.get_counts()
        total = sum(counts.values())
        probs = {k: v / total for k, v in counts.items()}
        return {
            "success": True,
            "backend": f"Azure:{self.target}",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# IonQ backend (REST API)
# ──────────────────────────────────────────────────────────────────────────────

class IonQBackend(QuantumBackend):
    """IonQ REST API backend.

    Requires: ``pip install requests``

    Parameters
    ----------
    api_key: str
        IonQ API key from https://cloud.ionq.com/
    target: str
        ``'simulator'`` (default) or a real device name like ``'qpu.aria-1'``.
    """

    name = "IonQ"
    _BASE_URL = "https://api.ionq.co/v0.3"

    def __init__(self, api_key: str, target: str = "simulator"):
        self.api_key = api_key
        self.target = target

    def _circuit_to_ionq_json(self, circuit: Circuit) -> List[Dict]:
        """Serialize to IonQ native JSON gate format."""
        ops = []
        for gate in getattr(circuit, "gates", []):
            name = gate.name.upper()
            q = list(gate.qubits)
            p = gate.params
            if name == "H":
                ops.append({"gate": "h", "target": q[0]})
            elif name in ("CNOT", "CX"):
                ops.append({"gate": "cnot", "control": q[0], "target": q[1]})
            elif name == "X":
                ops.append({"gate": "x", "target": q[0]})
            elif name == "Y":
                ops.append({"gate": "y", "target": q[0]})
            elif name == "Z":
                ops.append({"gate": "z", "target": q[0]})
            elif name == "S":
                ops.append({"gate": "s", "target": q[0]})
            elif name == "T":
                ops.append({"gate": "t", "target": q[0]})
            elif name == "RX":
                ops.append({"gate": "rx", "target": q[0], "rotation": float(p[0])})
            elif name == "RY":
                ops.append({"gate": "ry", "target": q[0], "rotation": float(p[0])})
            elif name == "RZ":
                ops.append({"gate": "rz", "target": q[0], "rotation": float(p[0])})
            elif name == "CZ":
                ops.append({"gate": "cz", "control": q[0], "target": q[1]})
            elif name == "SWAP":
                ops.append({"gate": "swap", "targets": [q[0], q[1]]})
        return ops

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        import requests  # standard in most environments

        ops = self._circuit_to_ionq_json(circuit)
        payload = {
            "target": self.target,
            "shots": shots,
            "input": {
                "format": "ionq.circuit.v0",
                "gateset": "native",
                "qubits": circuit.num_qubits,
                "circuit": ops,
            },
        }
        headers = {
            "Authorization": f"apiKey {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            f"{self._BASE_URL}/jobs", json=payload, headers=headers, timeout=30
        )
        resp.raise_for_status()
        job_id = resp.json()["id"]

        # Poll until done
        import time
        while True:
            r = requests.get(
                f"{self._BASE_URL}/jobs/{job_id}", headers=headers, timeout=10
            )
            r.raise_for_status()
            data = r.json()
            status = data.get("status")
            if status == "completed":
                break
            if status in ("failed", "canceled"):
                raise RuntimeError(f"IonQ job {job_id} ended with status={status}")
            time.sleep(2)

        # IonQ returns probabilities directly
        raw_probs = data.get("data", {}).get("histogram", {})
        probs = {format(int(k), f"0{circuit.num_qubits}b"): v for k, v in raw_probs.items()}

        # Convert probabilities to counts
        counts: Dict[str, int] = {}
        for state, prob in probs.items():
            count = int(round(prob * shots))
            if count > 0:
                counts[state] = count

        return {
            "success": True,
            "backend": f"IonQ:{self.target}",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Cirq / Google Quantum backend
# ──────────────────────────────────────────────────────────────────────────────

class CirqBackend(QuantumBackend):
    """Google Cirq simulator / Google Quantum backend.

    Requires: ``pip install cirq``

    Parameters
    ----------
    use_gpu: bool
        If True, use ``cirq.CuStateVecSimulator`` (requires cuQuantum).
    processor_id: str | None
        Google QCS processor ID for real hardware (requires cirq-google
        and service credentials).
    """

    name = "Cirq"

    def __init__(self, use_gpu: bool = False, processor_id: Optional[str] = None):
        self.use_gpu = use_gpu
        self.processor_id = processor_id

    def _circuit_to_cirq(self, circuit: Circuit):
        import cirq
        qubits = cirq.LineQubit.range(circuit.num_qubits)
        ops = []
        for gate in getattr(circuit, "gates", []):
            name = gate.name.upper()
            q = list(gate.qubits)
            p = gate.params
            if name == "H":
                ops.append(cirq.H(qubits[q[0]]))
            elif name in ("CNOT", "CX"):
                ops.append(cirq.CNOT(qubits[q[0]], qubits[q[1]]))
            elif name == "X":
                ops.append(cirq.X(qubits[q[0]]))
            elif name == "Y":
                ops.append(cirq.Y(qubits[q[0]]))
            elif name == "Z":
                ops.append(cirq.Z(qubits[q[0]]))
            elif name == "S":
                ops.append(cirq.S(qubits[q[0]]))
            elif name == "T":
                ops.append(cirq.T(qubits[q[0]]))
            elif name == "RX":
                ops.append(cirq.rx(float(p[0]))(qubits[q[0]]))
            elif name == "RY":
                ops.append(cirq.ry(float(p[0]))(qubits[q[0]]))
            elif name == "RZ":
                ops.append(cirq.rz(float(p[0]))(qubits[q[0]]))
            elif name == "CZ":
                ops.append(cirq.CZ(qubits[q[0]], qubits[q[1]]))
            elif name == "SWAP":
                ops.append(cirq.SWAP(qubits[q[0]], qubits[q[1]]))
        # Add measurements
        ops.append(cirq.measure(*qubits, key="result"))
        return cirq.Circuit(ops), qubits

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            import cirq
        except ImportError as exc:
            raise RuntimeError(
                "CirqBackend requires 'cirq'. Install with: pip install cirq"
            ) from exc

        n = circuit.num_qubits
        cq, qubits = self._circuit_to_cirq(circuit)

        if self.processor_id:
            # Real hardware via cirq-google
            try:
                import cirq_google
                engine = cirq_google.Engine(project_id=kwargs.get("project_id", ""))
                sampler = engine.get_sampler(processor_id=self.processor_id)
            except ImportError as exc:
                raise RuntimeError("Real hardware requires 'cirq-google'.") from exc
        else:
            sampler = cirq.Simulator()

        result = sampler.run(cq, repetitions=shots)
        measurements = result.measurements["result"]  # shape (shots, n_qubits)

        counts: Dict[str, int] = {}
        for row in measurements:
            key = "".join(str(b) for b in row)
            counts[key] = counts.get(key, 0) + 1

        probs = self._counts_to_probs(counts, shots)
        return {
            "success": True,
            "backend": f"Cirq:{self.processor_id or 'simulator'}",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Auto-selector: pick the best available backend
# ──────────────────────────────────────────────────────────────────────────────

def get_best_backend(n_qubits: int = 30, **kwargs: Any) -> QuantumBackend:
    """Return the fastest available local backend for the given qubit count.

    Falls back gracefully: Rust → NumPy.
    """
    return FastBackend(n_qubits=n_qubits, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Public exports
# ──────────────────────────────────────────────────────────────────────────────

__all__ = [
    "QuantumBackend",
    "FastBackend",
    "IBMQBackend",
    "BraketBackend",
    "AzureBackend",
    "IonQBackend",
    "CirqBackend",
    "get_best_backend",
]
