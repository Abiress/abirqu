// Auto-generated AbirQu TypeScript definitions — do not edit manually.

type AbirQuSimulator = number;

// Create a new simulator for `num_qubits` qubits.
// Returns a non-null opaque handle.  Must be freed with
// `abirqu_simulator_destroy`.
export function abirqu_simulator_create(u32: any): AbirQuSimulator;
// Free a handle created by `abirqu_simulator_create`.  Passing NULL is safe.
export function abirqu_simulator_destroy(AbirQuSimulator: any): void;
// Reset the simulator to |0…0⟩ without reallocating.
export function abirqu_simulator_reset(AbirQuSimulator: any): void;
// Return the number of qubits this simulator was created with.
export function abirqu_num_qubits(AbirQuSimulator: any): number;
// Return the Hilbert space dimension (2^num_qubits).
export function abirqu_hilbert_dim(AbirQuSimulator: any): number;
export function abirqu_h(AbirQuSimulator: any, u32: any): void;
export function abirqu_x(AbirQuSimulator: any, u32: any): void;
export function abirqu_y(AbirQuSimulator: any, u32: any): void;
export function abirqu_z(AbirQuSimulator: any, u32: any): void;
export function abirqu_s(AbirQuSimulator: any, u32: any): void;
export function abirqu_t(AbirQuSimulator: any, u32: any): void;
export function abirqu_rx(AbirQuSimulator: any, u32: any, f64: any): void;
export function abirqu_ry(AbirQuSimulator: any, u32: any, f64: any): void;
export function abirqu_rz(AbirQuSimulator: any, u32: any, f64: any): void;
export function abirqu_cnot(AbirQuSimulator: any, u32: any, u32: any): void;
export function abirqu_cz(AbirQuSimulator: any, u32: any, u32: any): void;
export function abirqu_swap(AbirQuSimulator: any, u32: any, u32: any): void;
// Execute a batch of gates described by the `gates` array of length `n_gates`.
// 
// # Safety
// `handle` must be a valid non-null pointer from `abirqu_simulator_create`.
// `gates`  must point to at least `n_gates` consecutive `AbirQuGate` values.
export function abirqu_run_circuit(AbirQuSimulator: any, *const AbirQuGate: any, usize: any): void;
// Copy measurement probabilities into caller-supplied buffer `out_probs`.
// 
// `out_probs` must have room for at least `abirqu_hilbert_dim(handle)` doubles.
// Returns the number of values written, or 0 on error.
export function abirqu_get_probabilities(AbirQuSimulator: any, *mut f64: any): number;
// Copy the statevector into caller-supplied buffers `out_re` and `out_im`.
// 
// Both buffers must have room for at least `abirqu_hilbert_dim(handle)` doubles.
// Returns the number of complex amplitudes written, or 0 on error.
export function abirqu_get_statevector(AbirQuSimulator: any, *mut f64: any, *mut f64: any): number;
