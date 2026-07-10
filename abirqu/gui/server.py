"""
AbirQu Backend Server
Copyright 2026 Abir Maheshwari

REST + WebSocket server for the quantum IDE.
Handles circuit compilation, job execution, and real-time streaming.
"""
import json
import time
import uuid
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    import numpy as np
except ImportError:
    np = None


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QuantumJob:
    job_id: str
    circuit: Any
    backend: str
    shots: int
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    progress: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'job_id': self.job_id,
            'backend': self.backend,
            'shots': self.shots,
            'status': self.status.value,
            'result': self.result,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error': self.error,
            'progress': self.progress,
        }


class QuantumServer:
    """REST + WebSocket backend server for the quantum IDE."""

    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.jobs: Dict[str, QuantumJob] = {}
        self.hardware_registry: Dict[str, Dict] = {}
        self._handlers: Dict[str, Callable] = {}
        self._ws_clients: List[Any] = []
        self._running = False
        self._lock = threading.Lock()
        self._event_log: List[Dict] = []
        self._circuit_cache: Dict[str, Any] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            'job_update': [],
            'hardware_update': [],
            'circuit_update': [],
        }
        self._register_default_handlers()
        self._register_default_hardware()

    def _register_default_handlers(self):
        self._handlers['compile'] = self._handle_compile
        self._handlers['execute'] = self._handle_execute
        self._handlers['cancel'] = self._handle_cancel
        self._handlers['status'] = self._handle_status
        self._handlers['result'] = self._handle_result
        self._handlers['hardware'] = self._handlers.get('hardware', self._handle_hardware)
        self._handlers['list_jobs'] = self._handle_list_jobs

    def _register_default_hardware(self):
        self.hardware_registry = {
            'abirqu_simulator': {
                'name': 'AbirQu Simulator',
                'type': 'simulator',
                'num_qubits': 30,
                'status': 'online',
                'provider': 'AbirQu',
                'max_shots': 100000,
                'gates': ['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'T', 'S', 'Rx', 'Ry', 'Rz', 'SWAP', 'Toffoli'],
            },
            'abirqu_clifford': {
                'name': 'AbirQu Clifford',
                'type': 'simulator',
                'num_qubits': 100,
                'status': 'online',
                'provider': 'AbirQu',
                'max_shots': 1000000,
                'gates': ['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'S'],
            },
            'abirqu_gpu': {
                'name': 'AbirQu GPU',
                'type': 'simulator',
                'num_qubits': 40,
                'status': 'online',
                'provider': 'AbirQu',
                'max_shots': 100000,
                'gpu': True,
                'gates': ['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'T', 'S', 'Rx', 'Ry', 'Rz', 'SWAP', 'Toffoli'],
            },
        }

    def on(self, event: str, callback: Callable):
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any):
        for cb in self._callbacks.get(event, []):
            try:
                cb(data)
            except Exception:
                pass

    def start(self):
        self._running = True
        self._log_event('server_start', {'host': self.host, 'port': self.port})

    def stop(self):
        self._running = False
        self._log_event('server_stop', {})

    @property
    def is_running(self) -> bool:
        return self._running

    def handle_request(self, request: Dict) -> Dict:
        action = request.get('action', '')
        handler = self._handlers.get(action)
        if handler:
            try:
                return {'status': 'ok', 'data': handler(request)}
            except Exception as e:
                return {'status': 'error', 'error': str(e)}
        return {'status': 'error', 'error': f'Unknown action: {action}'}

    def _handle_compile(self, request: Dict) -> Dict:
        circuit_data = request.get('circuit', {})
        backend = request.get('backend', 'abirqu_simulator')
        cache_key = json.dumps(circuit_data, sort_keys=True, default=str)
        if cache_key in self._circuit_cache:
            return self._circuit_cache[cache_key]
        compiled = {
            'gates': circuit_data.get('gates', []),
            'num_qubits': circuit_data.get('num_qubits', 1),
            'depth': len(circuit_data.get('gates', [])),
            'compiled': True,
            'backend': backend,
        }
        self._circuit_cache[cache_key] = compiled
        self._log_event('compile', {'backend': backend, 'depth': compiled['depth']})
        self._emit('circuit_update', compiled)
        return compiled

    def _handle_execute(self, request: Dict) -> Dict:
        circuit_data = request.get('circuit', {})
        backend = request.get('backend', 'abirqu_simulator')
        shots = request.get('shots', 1024)

        job_id = str(uuid.uuid4())[:8]
        job = QuantumJob(
            job_id=job_id,
            circuit=circuit_data,
            backend=backend,
            shots=shots,
        )
        with self._lock:
            self.jobs[job_id] = job

        thread = threading.Thread(target=self._execute_job, args=(job,), daemon=True)
        thread.start()

        self._log_event('job_created', {'job_id': job_id, 'backend': backend, 'shots': shots})
        return job.to_dict()

    def _execute_job(self, job: QuantumJob):
        try:
            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            self._emit('job_update', job.to_dict())

            time.sleep(0.1)
            job.progress = 0.5
            self._emit('job_update', job.to_dict())

            result = self._simulate_circuit(job.circuit, job.shots)
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = time.time()
            job.progress = 1.0

            self._emit('job_update', job.to_dict())
            self._log_event('job_completed', {
                'job_id': job.job_id,
                'duration': job.completed_at - job.started_at,
            })
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = time.time()
            self._emit('job_update', job.to_dict())

    def _simulate_circuit(self, circuit_data: Any, shots: int) -> Dict:
        try:
            from abirqu.circuit import Circuit as AbirCircuit, Gate as AbirGate
            from abirqu.primitives.quantum_run import QuantumRun

            if isinstance(circuit_data, dict):
                num_qubits = circuit_data.get('num_qubits', 2)
                raw_gates = circuit_data.get('gates', [])
            elif isinstance(circuit_data, AbirCircuit):
                num_qubits = circuit_data.num_qubits
                raw_gates = [{'name': g.name, 'qubits': list(g.qubits), 'params': list(g.params)} for g in circuit_data.gates]
            else:
                num_qubits = 2
                raw_gates = []

            circ = AbirCircuit(num_qubits, name='gui_simulation')
            for g in raw_gates:
                name = g.get('name', '') if isinstance(g, dict) else str(g)
                qubits = g.get('qubits', [0]) if isinstance(g, dict) else [0]
                params = g.get('params', []) if isinstance(g, dict) else []
                circ.gates.append(AbirGate(name, qubits, params=params))

            qr = QuantumRun(circuits=circ, shots=shots)
            r = qr[0]

            return {
                'counts': r.counts,
                'num_qubits': num_qubits,
                'shots': shots,
                'probabilities': r.probabilities,
                'statevector': [complex(v).real for v, _ in zip(r.statevector, range(len(r.statevector)))] if r.statevector is not None else None,
                'backend': 'quantumrun',
            }
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"QuantumRun fallback: {e}")
            return self._simulate_circuit_fallback(circuit_data, shots)

    def _simulate_circuit_fallback(self, circuit_data: Any, shots: int) -> Dict:
        if np is None:
            return {'counts': {'0': shots}, 'statevector': None}

        if isinstance(circuit_data, dict):
            num_qubits = circuit_data.get('num_qubits', 1)
            gates = circuit_data.get('gates', [])
        else:
            num_qubits = 2
            gates = []

        state = np.zeros(2**num_qubits, dtype=complex)
        state[0] = 1.0

        for gate in gates:
            gate_name = gate.get('name', '') if isinstance(gate, dict) else str(gate)
            qubits = gate.get('qubits', [0]) if isinstance(gate, dict) else [0]
            self._apply_gate(state, gate_name, qubits, num_qubits)

        probs = np.abs(state) ** 2
        counts = {}
        for i in range(len(state)):
            if probs[i] > 1e-10:
                bitstring = format(i, f'0{num_qubits}b')
                count = int(np.random.binomial(shots, probs[i]))
                if count > 0:
                    counts[bitstring] = count

        total = sum(counts.values())
        if total < shots:
            max_key = max(counts, key=counts.get) if counts else '0' * num_qubits
            counts[max_key] = counts.get(max_key, 0) + (shots - total)

        return {
            'counts': counts,
            'num_qubits': num_qubits,
            'shots': shots,
            'probabilities': {k: v/shots for k, v in counts.items()},
        }

    def _apply_gate(self, state, gate_name: str, qubits: List[int], num_qubits: int):
        if np is None or not qubits:
            return
        q = qubits[0] % num_qubits
        n = len(state)

        if gate_name.upper() in ('H', 'HADAMARD'):
            new_state = np.zeros_like(state)
            for i in range(n):
                bit = (i >> (num_qubits - 1 - q)) & 1
                partner = i ^ (1 << (num_qubits - 1 - q))
                if bit == 0:
                    new_state[i] += state[i] / np.sqrt(2)
                    new_state[partner] += state[i] / np.sqrt(2)
                else:
                    new_state[i] += state[i] / np.sqrt(2)
                    new_state[partner] -= state[i] / np.sqrt(2)
            state[:] = new_state

        elif gate_name.upper() in ('X', 'PAULI_X', 'NOT'):
            for i in range(n):
                bit = (i >> (num_qubits - 1 - q)) & 1
                if bit == 0:
                    partner = i | (1 << (num_qubits - 1 - q))
                    state[i], state[partner] = state[partner].copy(), state[i].copy()

        elif gate_name.upper() in ('Z', 'PAULI_Z'):
            for i in range(n):
                bit = (i >> (num_qubits - 1 - q)) & 1
                if bit == 1:
                    state[i] *= -1

        elif gate_name.upper() in ('Y', 'PAULI_Y'):
            new_state = np.zeros_like(state)
            for i in range(n):
                bit = (i >> (num_qubits - 1 - q)) & 1
                partner = i ^ (1 << (num_qubits - 1 - q))
                if bit == 0:
                    new_state[partner] += -1j * state[i]
                else:
                    new_state[partner] += 1j * state[i]
            state[:] = new_state

        elif gate_name.upper() in ('CNOT', 'CX') and len(qubits) >= 2:
            ctrl = qubits[0] % num_qubits
            tgt = qubits[1] % num_qubits
            new_state = state.copy()
            for i in range(n):
                ctrl_bit = (i >> (num_qubits - 1 - ctrl)) & 1
                if ctrl_bit == 1:
                    partner = i ^ (1 << (num_qubits - 1 - tgt))
                    new_state[i] = state[partner]
                    new_state[partner] = state[i]
            state[:] = new_state

        elif gate_name.upper() in ('CZ',) and len(qubits) >= 2:
            q1 = qubits[0] % num_qubits
            q2 = qubits[1] % num_qubits
            for i in range(n):
                b1 = (i >> (num_qubits - 1 - q1)) & 1
                b2 = (i >> (num_qubits - 1 - q2)) & 1
                if b1 == 1 and b2 == 1:
                    state[i] *= -1

        elif gate_name.upper() in ('S',) and gate_name.upper() != 'SWAP':
            for i in range(n):
                bit = (i >> (num_qubits - 1 - q)) & 1
                if bit == 1:
                    state[i] *= 1j

        elif gate_name.upper() in ('T',) and gate_name.upper() != 'TOFFOLI':
            for i in range(n):
                bit = (i >> (num_qubits - 1 - q)) & 1
                if bit == 1:
                    state[i] *= np.exp(1j * np.pi / 4)

        elif gate_name.upper() in ('RX',) and len(qubits) >= 1:
            theta = 0.0
            new_state = np.zeros_like(state)
            c, s = np.cos(theta/2), -1j * np.sin(theta/2)
            for i in range(n):
                bit = (i >> (num_qubits - 1 - q)) & 1
                partner = i ^ (1 << (num_qubits - 1 - q))
                if bit == 0:
                    new_state[i] += c * state[i]
                    new_state[partner] += s * state[i]
                else:
                    new_state[i] += s * state[i]
                    new_state[partner] += c * state[i]
            state[:] = new_state

        elif gate_name.upper() in ('SWAP',) and len(qubits) >= 2:
            q1, q2 = qubits[0] % num_qubits, qubits[1] % num_qubits
            new_state = state.copy()
            for i in range(n):
                b1 = (i >> (num_qubits - 1 - q1)) & 1
                b2 = (i >> (num_qubits - 1 - q2)) & 1
                if b1 != b2:
                    partner = i ^ (1 << (num_qubits - 1 - q1)) ^ (1 << (num_qubits - 1 - q2))
                    new_state[i] = state[partner]
            state[:] = new_state

    def _handle_cancel(self, request: Dict) -> Dict:
        job_id = request.get('job_id', '')
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.CANCELLED
                return self.jobs[job_id].to_dict()
        return {'error': 'Job not found'}

    def _handle_status(self, request: Dict) -> Dict:
        job_id = request.get('job_id', '')
        with self._lock:
            if job_id in self.jobs:
                return self.jobs[job_id].to_dict()
        return {'error': 'Job not found'}

    def _handle_result(self, request: Dict) -> Dict:
        job_id = request.get('job_id', '')
        with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                if job.status == JobStatus.COMPLETED:
                    return job.result or {}
                return {'status': job.status.value}
        return {'error': 'Job not found'}

    def _handle_hardware(self, request: Dict) -> Dict:
        return {'hardware': list(self.hardware_registry.values())}

    def _handle_list_jobs(self, request: Dict) -> Dict:
        with self._lock:
            return {'jobs': [j.to_dict() for j in self.jobs.values()]}

    def get_hardware(self) -> List[Dict]:
        return list(self.hardware_registry.values())

    def get_job(self, job_id: str) -> Optional[QuantumJob]:
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[QuantumJob]:
        return list(self.jobs.values())

    def _log_event(self, event_type: str, data: Dict):
        self._event_log.append({
            'type': event_type,
            'data': data,
            'timestamp': time.time(),
        })

    def get_event_log(self) -> List[Dict]:
        return list(self._event_log)

    def get_stats(self) -> Dict:
        with self._lock:
            statuses = {}
            for job in self.jobs.values():
                s = job.status.value
                statuses[s] = statuses.get(s, 0) + 1
        return {
            'total_jobs': len(self.jobs),
            'statuses': statuses,
            'hardware_count': len(self.hardware_registry),
            'is_running': self._running,
            'events_logged': len(self._event_log),
        }
