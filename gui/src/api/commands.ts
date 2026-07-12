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

  // ─── Domain modules (real abirqu SDK calls — see domain_handlers.py) ───

  runChemistryVQE: (params: ChemistryVQEParams) =>
    invoke<ChemistryVQEResult>('run_chemistry_vqe', { params }),

  runQECCycle: (params: QECCycleParams) =>
    invoke<QECCycleResult>('run_qec_cycle', { params }),

  runQECDistill: (params: QECDistillParams) =>
    invoke<QECDistillResult>('run_qec_distill', { params }),

  runQCommBB84: (params: BB84Params) =>
    invoke<BB84Result>('run_qcomm_bb84', { params }),

  runPQCKeygen: (params: Record<string, never> = {}) =>
    invoke<PQCKeygenResult>('run_pqc_keygen', { params }),

  runPQCAssess: (params: Record<string, never> = {}) =>
    invoke<PQCAssessResult>('run_pqc_assess', { params }),

  runQec: (params: any) => invoke<any>('run_qec', { params }),
  runQkd: (params: any) => invoke<any>('run_qkd', { params }),
  runChemistry: (params: any) => invoke<any>('run_chemistry', { params }),
  runShor: (params: any) => invoke<any>('run_shor', { params }),
  runGrover: (params: any) => invoke<any>('run_grover', { params }),
  runHhl: (params: any) => invoke<any>('run_hhl', { params }),
  runQpinn: (params: any) => invoke<any>('run_qpinn', { params }),
  runCrypto: (params: any) => invoke<any>('run_crypto', { params }),
  runAgentic: (params: any) => invoke<any>('run_agentic', { params }),
  askQuantum: (params: any) => invoke<any>('ask_quantum', { params }),
};

// ─── Domain module types ───────────────────────────────────────────────

export interface ChemistryVQEParams {
  molecule?: 'H2' | 'LiH' | 'H2O';
  basis?: string;
  ansatz?: 'uccsd' | 'hardware_efficient';
  mapper?: 'jordan_wigner' | 'bravyi_kitaev' | 'parity';
  optimizer?: string;
  max_iterations?: number;
  shots?: number;
}
export interface ChemistryVQEResult {
  molecule: string;
  basis: string;
  ansatz: string;
  mapper: string;
  n_electrons: number;
  n_orbitals: number;
  energy: number;
  classical_energy: number;
  error: number;
  n_qubits: number;
  n_parameters: number;
  convergence: number[];
}

export interface QECCycleParams {
  code?: 'repetition' | 'bit_flip' | 'phase_flip' | 'shor' | 'steane' | 'surface';
  decoder?: 'lookup' | 'mwpm';
  logical_state?: 0 | 1;
  error_qubits?: number[];
  size?: number;
}
export interface QECCycleResult {
  code: string;
  decoder: string;
  logical_state: number;
  n_physical_qubits: number;
  injected_error_qubits: number[];
  syndrome: number[];
  correction: number[];
  corrected_successfully: boolean;
  overhead: Record<string, number>;
}

export interface QECDistillParams {
  state_type?: 't' | 'h';
  rounds?: number;
  initial_fidelity?: number;
}
export interface QECDistillResult {
  state_type: string;
  rounds: number;
  output_count: number;
  fidelity: number;
  success: boolean;
}

export interface BB84Params {
  distance_km?: number;
  num_bits?: number;
  fiber_loss_db_km?: number;
  detector_efficiency?: number;
  dark_count_rate?: number;
  misalignment?: number;
  seed?: number;
}
export interface BB84Result {
  distance_km: number;
  channel_transmission: number;
  surviving_pulses: number;
  error_rate: number;
  key_rate: number;
  final_key_length: number;
  secure: boolean;
}

export interface PQCKeygenResult {
  scheme: string;
  public_key_shape: number[];
  secret_key_shape: number[];
  public_key_preview: number[][];
}
export interface PQCAssessResult {
  algorithm: string;
  security_level: string;
  parameters: Record<string, number>;
  grover_attack: { complexity: string; feasible: boolean; quantum_speedup: string };
  quantum_bkz: { complexity: string; feasible: boolean };
  recommendation: string;
}
