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
