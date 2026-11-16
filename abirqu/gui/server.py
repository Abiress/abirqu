"""
AbirQu Backend Server
Copyright 2026 Abir Maheshwari

REST + WebSocket server for the quantum IDE.
Handles circuit compilation, job execution, and real-time streaming.
"""
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

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
    simulator: str = "statevector"
    seed: Optional[int] = None
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
            'simulator': self.simulator,
            'seed': self.seed,
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
        self._handlers['step_circuit'] = self._handle_step_circuit
        self._handlers['simulate_noise_lab'] = self._handle_simulate_noise_lab

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

    SIMULATOR_LIMITS = {
        'statevector': 28,
        'gpu': 32,
        'clifford': 1000,
        'mps': 100,
        'ttn': 200,
        'monte_carlo': 24,
    }

    def _handle_execute(self, request: Dict) -> Dict:
        circuit_data = request.get('circuit', {})
        backend = request.get('backend', 'abirqu_simulator')
        simulator = request.get('simulator', 'statevector')
        shots = request.get('shots', 1024)
        seed = request.get('seed')

        num_qubits = circuit_data.get('num_qubits', 1) if isinstance(circuit_data, dict) else getattr(circuit_data, 'num_qubits', 1)
        sim_key = str(simulator).lower()
        limit = self.SIMULATOR_LIMITS.get(sim_key, 28)
        if num_qubits > limit:
            raise ValueError(f"Circuit has {num_qubits} qubits, exceeding {simulator} limit of {limit} qubits.")

        job_id = str(uuid.uuid4())[:8]
        job = QuantumJob(
            job_id=job_id,
            circuit=circuit_data,
            backend=backend,
            simulator=simulator,
            seed=seed,
            shots=shots,
        )
        with self._lock:
            self.jobs[job_id] = job

        thread = threading.Thread(target=self._execute_job, args=(job,), daemon=True)
        thread.start()

        self._log_event('job_created', {'job_id': job_id, 'backend': backend, 'simulator': simulator, 'shots': shots})
        return job.to_dict()

    def _execute_job(self, job: QuantumJob):
        try:
            if job.status == JobStatus.CANCELLED:
                return
            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            self._emit('job_update', job.to_dict())

            job.progress = 0.25
            self._emit('job_update', job.to_dict())
            time.sleep(0.04)

            if job.status == JobStatus.CANCELLED:
                return

            job.progress = 0.65
            self._emit('job_update', job.to_dict())

            result = self._simulate_circuit(job.circuit, job.shots, job.simulator, job.seed)
            if job.status == JobStatus.CANCELLED:
                return

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

    def _simulate_circuit(self, circuit_data: Any, shots: int, simulator: str = 'statevector', seed: Optional[int] = None) -> Dict:
        """
        Executes a circuit using the real AbirQu SDK simulator
        (abirqu.Circuit.run / NumPySimulator / Clifford / MPS),
        with qubit limits per engine, seed, and full statevector extraction.
        """
        import abirqu
        if seed is not None and np is not None:
            np.random.seed(seed)

        if isinstance(circuit_data, dict):
            num_qubits = circuit_data.get('num_qubits', 1)
            gates = circuit_data.get('gates', [])
        elif isinstance(circuit_data, abirqu.Circuit):
            num_qubits = circuit_data.num_qubits
            gates = [{'name': g.name, 'qubits': list(g.qubits), 'params': list(g.params)} for g in circuit_data.gates]
        else:
            num_qubits = 2
            gates = []

        circuit = abirqu.Circuit(num_qubits)
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            gate_name = gate.get('name', '')
            qubits = gate.get('qubits', [])
            params = gate.get('params') or None
            if not gate_name or not qubits:
                continue
            circuit.add_gate(gate_name, qubits, params)

        sim_name = simulator.lower()
        if sim_name == 'clifford':
            clf = abirqu.CliffordSimulator(num_qubits)
            counts = clf.sample(circuit, shots=shots) if hasattr(clf, 'sample') else {}
            probs = {k: v / shots for k, v in counts.items()} if shots > 0 else {}
            return {
                'counts': counts,
                'num_qubits': num_qubits,
                'shots': shots,
                'probabilities': probs,
                'backend': 'CliffordSimulator',
                'simulator': 'clifford',
                'success': True,
            }
        elif sim_name == 'mps':
            mps = abirqu.MPSSimulator(num_qubits)
            res = mps.run(circuit, shots=shots) if hasattr(mps, 'run') else {}
            counts = res.get('counts', {}) if isinstance(res, dict) else {}
            probs = res.get('probabilities', {}) if isinstance(res, dict) else {}
            return {
                'counts': counts,
                'num_qubits': num_qubits,
                'shots': shots,
                'probabilities': probs,
                'backend': 'MPSSimulator',
                'simulator': 'mps',
                'success': True,
            }
        else:
            # Statevector via NumPySimulator
            sim = abirqu.NumPySimulator(num_qubits)
            exact_probs = sim.run_circuit(circuit)
            sv = sim.get_state_vector()

            formatted_sv = []
            for i, amp in enumerate(sv):
                p = float(abs(amp) ** 2)
                formatted_sv.append({
                    'basis': format(i, f'0{num_qubits}b'),
                    'real': float(amp.real),
                    'imag': float(amp.imag),
                    'magnitude': float(abs(amp)),
                    'phase': float(np.angle(amp)) if np is not None else 0.0,
                    'probability': p,
                })

            states = list(exact_probs.keys())
            probs_list = list(exact_probs.values())
            counts = {}
            if shots > 0 and states:
                import random
                if seed is not None:
                    random.seed(seed)
                choices = random.choices(states, weights=probs_list, k=shots)
                for s in choices:
                    counts[s] = counts.get(s, 0) + 1

            return {
                'counts': counts,
                'num_qubits': num_qubits,
                'shots': shots,
                'probabilities': exact_probs,
                'statevector': formatted_sv,
                'backend': 'NumPySimulator',
                'simulator': simulator,
                'success': True,
            }

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

    def _handle_step_circuit(self, request: Dict) -> Dict:
        """
        Step-through quantum circuit debugger handler.
        Executes circuit up to `step` gates and returns full statevector amplitudes,
        phase-coloured metrics, per-qubit Bloch sphere vectors, and purity/entanglement.
        """
        import abirqu
        from abirqu.visualization.bloch import _bloch_vector

        circuit_data = request.get('circuit', {})
        step = int(request.get('step', 0))
        breakpoints = set(request.get('breakpoints', []))

        if isinstance(circuit_data, dict):
            num_qubits = circuit_data.get('num_qubits', 1)
            all_gates = circuit_data.get('gates', [])
        elif isinstance(circuit_data, abirqu.Circuit):
            num_qubits = circuit_data.num_qubits
            all_gates = [{'name': g.name, 'qubits': list(g.qubits), 'params': list(g.params)} for g in circuit_data.gates]
        else:
            num_qubits = 2
            all_gates = []

        total_steps = len(all_gates)
        target_step = max(0, min(step, total_steps))

        sim = abirqu.NumPySimulator(num_qubits)
        sub_circuit = abirqu.Circuit(num_qubits)
        for i in range(target_step):
            g = all_gates[i]
            if isinstance(g, dict) and g.get('name') and g.get('qubits'):
                sub_circuit.add_gate(g['name'], g['qubits'], g.get('params'))

        exact_probs = sim.run_circuit(sub_circuit)
        sv = sim.get_state_vector()

        amplitudes = []
        for i, amp in enumerate(sv):
            p = float(abs(amp) ** 2)
            amplitudes.append({
                'basis': format(i, f'0{num_qubits}b'),
                'real': float(amp.real),
                'imag': float(amp.imag),
                'magnitude': float(abs(amp)),
                'phase': float(np.angle(amp)) if np is not None else 0.0,
                'probability': p,
            })

        bloch_vectors = []
        for q in range(num_qubits):
            bx, by, bz = _bloch_vector(sv, q, num_qubits)
            r_sq = bx * bx + by * by + bz * bz
            purity = float((1.0 + r_sq) / 2.0)
            entanglement = float(max(0.0, min(1.0, 1.0 - r_sq)))
            bloch_vectors.append({
                'qubit': q,
                'x': float(bx),
                'y': float(by),
                'z': float(bz),
                'purity': purity,
                'entanglement': entanglement,
            })

        current_gate = all_gates[target_step - 1] if target_step > 0 else None
        next_gate = all_gates[target_step] if target_step < total_steps else None
        hit_breakpoint = target_step in breakpoints

        return {
            'step': target_step,
            'total_steps': total_steps,
            'current_gate': current_gate,
            'next_gate': next_gate,
            'hit_breakpoint': hit_breakpoint,
            'amplitudes': amplitudes,
            'bloch_vectors': bloch_vectors,
            'probabilities': exact_probs,
            'success': True,
        }

    def _handle_simulate_noise_lab(self, request: Dict) -> Dict:
        """
        Simulate circuit under ideal and noisy conditions, computing
        Total Variation Distance (TVD) and calibration metrics.
        """
        import abirqu
        from abirqu.noise import NoiseModel

        circuit_data = request.get('circuit', {})
        noise_cfg = request.get('noise', {})

        if isinstance(circuit_data, dict):
            num_qubits = circuit_data.get('num_qubits', 1)
            gates = circuit_data.get('gates', [])
        elif isinstance(circuit_data, abirqu.Circuit):
            num_qubits = circuit_data.num_qubits
            gates = [{'name': g.name, 'qubits': list(g.qubits), 'params': list(g.params)} for g in circuit_data.gates]
        else:
            num_qubits = 2
            gates = []

        circuit = abirqu.Circuit(num_qubits)
        for gate in gates:
            if isinstance(gate, dict) and gate.get('name') and gate.get('qubits'):
                circuit.add_gate(gate['name'], gate['qubits'], gate.get('params'))

        # 1. Ideal simulation
        sim_ideal = abirqu.NumPySimulator(num_qubits)
        ideal_probs = sim_ideal.run_circuit(circuit)

        all_states = [format(i, f'0{num_qubits}b') for i in range(2**num_qubits)]
        full_ideal = {s: float(ideal_probs.get(s, 0.0)) for s in all_states}

        # 2. Noisy simulation
        depol = float(noise_cfg.get('depolarizing', 0.0))
        amp_damp = float(noise_cfg.get('amplitudeDamping', 0.0))
        phase_damp = float(noise_cfg.get('phaseDamping', 0.0))
        readout = float(noise_cfg.get('readoutError', 0.0))

        # Start from ideal probabilities
        noisy = dict(full_ideal)

        # Depolarizing channel: mix with completely mixed state
        if depol > 0:
            eps = min(1.0, depol * num_qubits)
            uniform = 1.0 / len(all_states)
            noisy = {s: (1.0 - eps) * p + eps * uniform for s, p in noisy.items()}

        # Amplitude damping channel: decay |1> to |0>
        if amp_damp > 0:
            for q in range(num_qubits):
                decayed = dict(noisy)
                for s, p in noisy.items():
                    if s[q] == '1':
                        s_decayed = s[:q] + '0' + s[q+1:]
                        decay_amt = p * amp_damp
                        decayed[s] -= decay_amt
                        decayed[s_decayed] = decayed.get(s_decayed, 0.0) + decay_amt
                noisy = decayed

        # Readout error: analytic transition matrix P(measured m | true s)
        if readout > 0:
            readout_dist = {m: 0.0 for m in all_states}
            for s, p_s in noisy.items():
                if p_s <= 0:
                    continue
                for m in all_states:
                    trans = 1.0
                    for q in range(num_qubits):
                        trans *= (1.0 - readout) if s[q] == m[q] else readout
                    readout_dist[m] += p_s * trans
            noisy = readout_dist

        # Normalize
        total_p = sum(noisy.values())
        if total_p > 0:
            full_noisy = {s: float(p / total_p) for s, p in noisy.items()}
        else:
            full_noisy = {s: float(p) for s, p in noisy.items()}

        # 3. Compute Total Variation Distance (TVD)
        # TVD(P, Q) = 0.5 * sum(|P(s) - Q(s)|)
        tvd = 0.5 * sum(abs(full_ideal[s] - full_noisy[s]) for s in all_states)

        # 4. Calibration summary
        gate_fidelity = max(0.0, 1.0 - 0.75 * depol)
        readout_fidelity = max(0.0, 1.0 - readout)
        purity_retention = max(0.0, 1.0 - tvd)

        return {
            'tvd': float(tvd),
            'ideal_distribution': full_ideal,
            'noisy_distribution': full_noisy,
            'calibration': {
                'gate_fidelity': float(gate_fidelity),
                'readout_fidelity': float(readout_fidelity),
                'purity_retention': float(purity_retention),
                'depolarizing': depol,
                'amplitude_damping': amp_damp,
                'phase_damping': phase_damp,
                'readout_error': readout,
            },
            'success': True,
        }

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
