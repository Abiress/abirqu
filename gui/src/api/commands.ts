import { invoke } from '@tauri-apps/api/core';

export interface GateData {
  name: string;
  qubits: number[];
  params?: number[];
}

export interface CircuitData {
  num_qubits: number;
  gates: GateData[];
}

export interface JobInfo {
  job_id: string;
  status: string;
  backend: string;
  shots: number;
  result: any;
  progress: number;
  error?: string;
}

export interface HardwareInfo {
  backend_id: string;
  name: string;
  backend_type: string;
  num_qubits: number;
  provider: string;
  status: string;
  gates: string[];
}

export interface CircuitTemplate {
  template_id: string;
  name: string;
  description: string;
  category: string;
  num_qubits: number;
  depth: number;
  gates: GateData[];
  tags: string[];
  difficulty: string;
}

export const api = {
  startServer: () => invoke<string>('start_server'),
  stopServer: () => invoke<string>('stop_server'),

  compileCircuit: (circuit: CircuitData, backend?: string) =>
    invoke<any>('compile_circuit', { circuit, backend }),

  executeCircuit: (circuit: CircuitData, backend?: string, shots?: number) =>
    invoke<JobInfo>('execute_circuit', { circuit, backend, shots }),

  getJobStatus: (jobId: string) =>
    invoke<JobInfo>('get_job_status', { jobId }),

  getResults: (jobId: string) =>
    invoke<any>('get_results', { jobId }),

  cancelJob: (jobId: string) =>
    invoke<string>('cancel_job', { jobId }),

  listJobs: () => invoke<JobInfo[]>('list_jobs'),

  listHardware: () => invoke<HardwareInfo[]>('list_hardware'),

  listLibraryCircuits: () => invoke<CircuitTemplate[]>('list_library_circuits'),

  loadCircuitFromLibrary: (templateId: string) =>
    invoke<CircuitData>('load_circuit_from_library', { templateId }),

  getServerStats: () => invoke<any>('get_server_stats'),

  convertCircuit: (circuit: CircuitData, target: string) =>
    invoke<any>('convert_circuit', { circuit, target }),

  runQiskit: (circuit: CircuitData, shots?: number) =>
    invoke<any>('run_qiskit', { circuit, shots }),

  runCirq: (circuit: CircuitData, shots?: number) =>
    invoke<any>('run_cirq', { circuit, shots }),

  runOqtopus: (circuit: CircuitData, shots?: number) =>
    invoke<any>('run_oqtopus', { circuit, shots }),

  runDwave: (circuit: CircuitData, shots?: number) =>
    invoke<any>('run_dwave', { circuit, shots }),

  exportCircuit: (circuit: CircuitData, format: string, results?: any) =>
    invoke<any>('export_circuit', { circuit, format, results }),

  getFrameworks: () =>
    invoke<Record<string, { installed: boolean; version: string }>>('get_frameworks'),
};
