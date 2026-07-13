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

// ─── OSINT / Graph Optimization ───────────────────────────────────────
export interface OsintGraphParams {
  problem?: string;
  nodes?: number;
  edge_density?: number;
  edges?: [number, number][];
}
export interface OsintGraphResult {
  problem: string;
  num_nodes: number;
  num_edges: number;
  edges: [number, number][];
  cut_value: number;
  partition: string;
  best_state: string;
  hamiltonian_terms: number;
}
export async function runOsintGraph(
  params: OsintGraphParams,
): Promise<OsintGraphResult> {
  return invoke('run_osint_graph', { params });
}

// ─── CV-QKD ───────────────────────────────────────────────────────────
export interface CVQKDParams {
  num_symbols?: number;
  modulation_variance?: number;
  excess_noise?: number;
  transmittance?: number;
}
export interface CVQKDResult {
  excess_noise: number;
  channel_transmittance: number;
  mutual_information: number;
  secret_key_rate: number;
  final_key_length: number;
  secure: boolean;
}
export async function runCVQKD(params: CVQKDParams): Promise<CVQKDResult> {
  return invoke('run_qcomm_cvqkd', { params });
}

// ─── DI-QKD ───────────────────────────────────────────────────────────
export interface DIQKDParams {
  num_rounds?: number;
  noise_level?: number;
  detection_efficiency?: number;
}
export interface DIQKDResult {
  bell_violation: number;
  chsh_parameter: number;
  key_rate: number;
  error_rate: number;
  secure: boolean;
  final_key_length: number;
}
export async function runDIQKD(params: DIQKDParams): Promise<DIQKDResult> {
  return invoke('run_qcomm_diqkd', { params });
}

// ─── Satellite QKD ────────────────────────────────────────────────────
export interface SatelliteQKDParams {
  altitude_km?: number;
  num_pulses?: number;
  detector_efficiency?: number;
}
export interface SatelliteQKDResult {
  distance_km: number;
  channel_loss_db: number;
  detection_rate: number;
  key_rate: number;
  key_length: number;
  secure: boolean;
}
export async function runSatelliteQKD(
  params: SatelliteQKDParams,
): Promise<SatelliteQKDResult> {
  return invoke('run_qcomm_satellite', { params });
}

// ─── Quantum Repeater ─────────────────────────────────────────────────
export interface RepeaterParams {
  total_distance_km?: number;
  num_segments?: number;
}
export interface RepeaterResult {
  total_distance_km: number;
  num_segments: number;
  end_to_end_fidelity: number;
  key_rate: number;
  key_length: number;
  latency_ms: number;
}
export async function runRepeater(params: RepeaterParams): Promise<RepeaterResult> {
  return invoke('run_qcomm_repeater', { params });
}

// ─── Quantum Network ──────────────────────────────────────────────────
export interface NetworkParams {
  topology?: string;
  num_nodes?: number;
  distance_km?: number;
}
export interface NetworkResult {
  topology: string;
  num_nodes: number;
  total_key_rate: number;
  average_fidelity: number;
  num_paths: number;
}
export async function runNetwork(params: NetworkParams): Promise<NetworkResult> {
  return invoke('run_qcomm_network', { params });
}

// ─── Circuit Encryption ───────────────────────────────────────────────
export interface CircuitEncryptParams {
  circuit_data: { num_qubits: number; gates: any[] };
}
export interface CircuitEncryptResult {
  ciphertext: string;
  nonce: string;
  digest: string;
  algorithm: string;
  key_id: string;
}
export async function runCircuitEncrypt(
  params: CircuitEncryptParams,
): Promise<CircuitEncryptResult> {
  return invoke('run_circuit_encrypt', { params });
}

export interface CircuitDecryptParams {
  ciphertext: string;
  nonce: string;
  digest: string;
  key: string;
}
export interface CircuitDecryptResult {
  success: boolean;
  num_qubits?: number;
  num_gates?: number;
  error?: string;
}
export async function runCircuitDecrypt(
  params: CircuitDecryptParams,
): Promise<CircuitDecryptResult> {
  return invoke('run_circuit_decrypt', { params });
}

// ─── Plugins ──────────────────────────────────────────────────────────
export interface PluginInfo {
  name: string;
  version: string;
  description?: string;
  tags?: string[];
  downloads?: number;
  installed?: boolean;
}
export interface PluginListResult {
  installed: PluginInfo[];
  marketplace: PluginInfo[];
}
export async function runPluginList(): Promise<PluginListResult> {
  return invoke('run_plugin_list', { params: {} });
}

// ─── TTN Simulator ─────────────────────────────────────────────────────
export interface TTNCircuit {
  num_qubits: number;
  gates: { name: string; qubits: number[]; params?: number[] }[];
}
export interface TTNResult {
  counts: Record<string, number>;
  n_qubits: number;
  simulator: string;
}
export async function runTTN(circuit: TTNCircuit, shots?: number): Promise<TTNResult> {
  return invoke('run_ttn', { params: { circuit, shots: shots || 1024 } });
}

// ─── Auto-differentiation ──────────────────────────────────────────────
export interface AutoDiffResult {
  method: string;
  gradients: number[];
  circuit_evals: number;
  n_params: number;
}
export async function runAutoDiff(
  method: string,
  n_qubits?: number,
  n_params?: number,
): Promise<AutoDiffResult> {
  return invoke('run_autodiff', { params: { method, n_qubits: n_qubits || 2, n_params: n_params || 4 } });
}

// ─── Dynamical Decoupling ──────────────────────────────────────────────
export interface DDResult {
  sequence_type: string;
  original_depth: number;
  scheduled_depth: number;
  pulses_inserted: number;
  is_identity: boolean;
}
export async function runDD(
  sequence_type: string,
  n_qubits?: number,
  idle_qubit?: number,
): Promise<DDResult> {
  return invoke('run_dd', { params: { sequence_type, n_qubits: n_qubits || 2, idle_qubit: idle_qubit || 0 } });
}

// ─── Distributed Simulation ────────────────────────────────────────────
export interface DistributedResult {
  counts: Record<string, number>;
  n_workers: number;
  n_qubits: number;
}
export async function runDistributed(
  n_workers?: number,
  n_qubits?: number,
  shots?: number,
): Promise<DistributedResult> {
  return invoke('run_distributed', { params: { n_workers: n_workers || 2, n_qubits: n_qubits || 4, shots: shots || 1024 } });
}

// ─── Job Queue Status ──────────────────────────────────────────────────
export interface JobQueueResult {
  costs: Record<string, any>;
  queue_depth: number;
}
export async function jobQueueStatus(): Promise<JobQueueResult> {
  return invoke('job_queue_status', { params: {} });
}
