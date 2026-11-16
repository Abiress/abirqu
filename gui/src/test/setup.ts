import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Tauri invoke
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(async (cmd: string, args?: any) => {
    switch (cmd) {
      case 'start_server':
      case 'stop_server':
        return 'ok';
      case 'list_hardware':
        return [
          { name: 'abirqu_simulator', type: 'simulator', num_qubits: 30, status: 'online', provider: 'AbirQu', max_shots: 100000, gates: ['H', 'X', 'Y', 'Z', 'CNOT', 'CZ'] },
          { name: 'ibm_fez', type: 'real', num_qubits: 156, status: 'online', provider: 'IBM', max_shots: 10000, gates: ['ECR', 'RZ', 'SX', 'X'] }
        ];
      case 'list_jobs':
        return [];
      case 'list_library_circuits':
        return [
          { id: 'bell_state', name: 'Bell State', num_qubits: 2, description: 'Maximally entangled pair' }
        ];
      case 'get_frameworks':
        return {
          abirqu: { installed: true, version: '1.2.5' },
          qiskit: { installed: false, version: '' },
          cirq: { installed: false, version: '' },
          dwave: { installed: false, version: '' }
        };
      case 'run_plugin_list':
        return [
          { name: 'error_mitigation', version: '0.1.0', description: 'Zero Noise Extrapolation', enabled: true }
        ];
      case 'list_directory':
        return [
          { name: 'README.md', is_dir: false, path: 'README.md' }
        ];
      case 'step_circuit': {
        const step = args?.step ?? 2;
        const s = 1.0 / Math.sqrt(2);
        return {
          step,
          total_steps: 2,
          current_gate: step > 0 ? { name: step === 1 ? 'H' : 'CNOT', qubits: step === 1 ? [0] : [0, 1] } : undefined,
          hit_breakpoint: false,
          amplitudes: [
            { basis: '00', real: s, imag: 0, magnitude: s, phase: 0, probability: 0.5 },
            { basis: '01', real: 0, imag: 0, magnitude: 0, phase: 0, probability: 0 },
            { basis: '10', real: 0, imag: 0, magnitude: 0, phase: 0, probability: 0 },
            { basis: '11', real: s, imag: 0, magnitude: s, phase: 0, probability: 0.5 },
          ],
          bloch_vectors: [
            { qubit: 0, x: 0, y: 0, z: 0, purity: 0.5, entanglement: 1.0 },
            { qubit: 1, x: 0, y: 0, z: 0, purity: 0.5, entanglement: 1.0 },
          ],
          probabilities: { '00': 0.5, '11': 0.5 },
          success: true,
        };
      }
      case 'simulate_noise_lab': {
        const depol = args?.noise?.depolarizing ?? 0.05;
        const readout = args?.noise?.readoutError ?? 0.02;
        const tvd = depol > 0 || readout > 0 ? 0.0950 : 0.0;
        return {
          tvd,
          ideal_distribution: { '00': 0.5, '01': 0.0, '10': 0.0, '11': 0.5 },
          noisy_distribution: { '00': 0.4525, '01': 0.0475, '10': 0.0475, '11': 0.4525 },
          calibration: {
            gate_fidelity: Math.max(0, 1 - 0.75 * depol),
            readout_fidelity: Math.max(0, 1 - readout),
            purity_retention: Math.max(0, 1 - tvd),
            depolarizing: depol,
            amplitude_damping: 0,
            phase_damping: 0,
            readout_error: readout,
          },
          success: true,
        };
      }
      case 'execute_circuit': {
        const shots = args?.shots ?? 1024;
        return {
          job_id: 'job-real-sim',
          backend: args?.backend ?? 'abirqu_simulator',
          status: 'completed',
          shots,
          progress: 1.0,
          result: {
            counts: { '00': Math.floor(shots / 2), '11': Math.ceil(shots / 2) },
            probabilities: { '00': 0.5, '11': 0.5 },
            num_qubits: 2,
            shots,
            backend: 'NumPySimulator',
            simulator: args?.simulator ?? 'statevector',
            success: true,
          },
        };
      }
      case 'get_job_status':
        return {
          job_id: args?.jobId ?? 'job-real-sim',
          status: 'completed',
          backend: 'NumPySimulator',
          shots: 1024,
          progress: 1.0,
          result: {
            counts: { '00': 512, '11': 512 },
            probabilities: { '00': 0.5, '11': 0.5 },
          },
        };
      case 'get_results':
        return {
          counts: { '00': 512, '11': 512 },
          probabilities: { '00': 0.5, '11': 0.5 },
          statevector: [
            { basis: '00', real: 1 / Math.sqrt(2), imag: 0, magnitude: 1 / Math.sqrt(2), phase: 0, probability: 0.5 },
            { basis: '01', real: 0, imag: 0, magnitude: 0, phase: 0, probability: 0 },
            { basis: '10', real: 0, imag: 0, magnitude: 0, phase: 0, probability: 0 },
            { basis: '11', real: 1 / Math.sqrt(2), imag: 0, magnitude: 1 / Math.sqrt(2), phase: 0, probability: 0.5 },
          ],
        };
      default:
        return { status: 'ok', data: {} };
    }
  }),
}));

// Mock ResizeObserver
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock Element.prototype.scrollIntoView
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn();
}

// Mock HTMLCanvasElement.getContext
HTMLCanvasElement.prototype.getContext = function (contextType: string, ..._args: any[]): any {
  if (contextType === '2d') {
    return {
      fillRect: vi.fn(),
      clearRect: vi.fn(),
      getImageData: vi.fn(() => ({ data: [] })),
      putImageData: vi.fn(),
      createImageData: vi.fn(() => []),
      setTransform: vi.fn(),
      drawImage: vi.fn(),
      save: vi.fn(),
      fillText: vi.fn(),
      restore: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      closePath: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
      arc: vi.fn(),
      strokeRect: vi.fn(),
      measureText: vi.fn(() => ({ width: 0 })),
      scale: vi.fn(),
      rotate: vi.fn(),
      translate: vi.fn(),
      quadraticCurveTo: vi.fn(),
      bezierCurveTo: vi.fn(),
      createRadialGradient: vi.fn(() => ({
        addColorStop: vi.fn(),
      })),
      createLinearGradient: vi.fn(() => ({
        addColorStop: vi.fn(),
      })),
      setLineDash: vi.fn(),
      getLineDash: vi.fn(() => []),
    };
  }
  return null;
} as any;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
