// ═══════════════════════════════════════════════════════════════════════════
//  AbirQu C ABI  (src/c_api.rs)
//
//  Stable extern "C" symbols exported by libabirqu.so / abirqu.dll.
//  Any language with a C FFI can use these symbols:
//    C / C++   — include abirqu.h, link -labirqu_core
//    Go        — cgo
//    Java      — JNI
//    .NET      — P/Invoke
//    Swift     — CInterop
//    Node.js   — node-ffi-napi / WebAssembly
//
//  Memory model
//  ─────────────
//  abirqu_simulator_create()  →  allocates a Simulator on the heap
//  abirqu_simulator_destroy() →  frees it
//  All other calls borrow the opaque handle; they never transfer ownership.
//  Probability and statevector data is written into caller-supplied buffers.
// ═══════════════════════════════════════════════════════════════════════════

use num_complex::Complex64;
use crate::simulator::Simulator;

/// Opaque handle type returned to C callers.
pub type AbirQuSimulator = *mut Simulator;

// ── Gate type constants (mirror of _GATE_MAP in abirqu/simulator.py) ────────
pub const AQ_GATE_H:    u8 = 0;
pub const AQ_GATE_X:    u8 = 1;
pub const AQ_GATE_Y:    u8 = 2;
pub const AQ_GATE_Z:    u8 = 3;
pub const AQ_GATE_S:    u8 = 4;
pub const AQ_GATE_T:    u8 = 5;
pub const AQ_GATE_CNOT: u8 = 6;
pub const AQ_GATE_CZ:   u8 = 7;
pub const AQ_GATE_RX:   u8 = 8;
pub const AQ_GATE_RY:   u8 = 9;
pub const AQ_GATE_RZ:   u8 = 10;
pub const AQ_GATE_SWAP: u8 = 11;

// ── Gate descriptor for batch execution ─────────────────────────────────────

/// One gate in a circuit batch.  Maps directly to the C struct:
///
/// ```c
/// typedef struct {
///     uint8_t  gate_type;   /* AQ_GATE_H, AQ_GATE_CNOT, … */
///     uint8_t  _pad[3];
///     uint32_t ctrl;        /* primary qubit or control qubit */
///     uint32_t target;      /* target qubit (2-qubit gates only) */
///     double   param;       /* rotation angle in radians (Rx/Ry/Rz) */
/// } AbirQuGate;
/// ```
#[repr(C)]
pub struct AbirQuGate {
    pub gate_type: u8,
    pub _pad: [u8; 3],
    pub ctrl:   u32,
    pub target: u32,
    pub param:  f64,
}

// ═══════════════════════════════════════════════════════════════════════════
// Lifecycle
// ═══════════════════════════════════════════════════════════════════════════

/// Create a new simulator for `num_qubits` qubits.
/// Returns a non-null opaque handle.  Must be freed with
/// `abirqu_simulator_destroy`.
#[no_mangle]
pub extern "C" fn abirqu_simulator_create(num_qubits: u32) -> AbirQuSimulator {
    Box::into_raw(Box::new(Simulator::new(num_qubits as usize)))
}

/// Free a handle created by `abirqu_simulator_create`.  Passing NULL is safe.
#[no_mangle]
pub extern "C" fn abirqu_simulator_destroy(handle: AbirQuSimulator) {
    if !handle.is_null() {
        // SAFETY: handle was created by abirqu_simulator_create.
        unsafe { drop(Box::from_raw(handle)) };
    }
}

/// Reset the simulator to |0…0⟩ without reallocating.
#[no_mangle]
pub extern "C" fn abirqu_simulator_reset(handle: AbirQuSimulator) {
    if handle.is_null() { return; }
    let sim = unsafe { &mut *handle };
    for c in sim.state.iter_mut() { *c = Complex64::new(0.0, 0.0); }
    sim.state[0] = Complex64::new(1.0, 0.0);
}

/// Return the number of qubits this simulator was created with.
#[no_mangle]
pub extern "C" fn abirqu_num_qubits(handle: AbirQuSimulator) -> u32 {
    if handle.is_null() { return 0; }
    unsafe { (*handle).num_qubits as u32 }
}

/// Return the Hilbert space dimension (2^num_qubits).
#[no_mangle]
pub extern "C" fn abirqu_hilbert_dim(handle: AbirQuSimulator) -> usize {
    if handle.is_null() { return 0; }
    unsafe { (*handle).state.len() }
}

// ═══════════════════════════════════════════════════════════════════════════
// Single-gate API
// ═══════════════════════════════════════════════════════════════════════════

#[no_mangle] pub extern "C" fn abirqu_h   (h: AbirQuSimulator, q: u32) { if !h.is_null() { unsafe { (*h).apply_h(q as usize); } } }
#[no_mangle] pub extern "C" fn abirqu_x   (h: AbirQuSimulator, q: u32) { if !h.is_null() { unsafe { (*h).apply_x(q as usize); } } }
#[no_mangle] pub extern "C" fn abirqu_y   (h: AbirQuSimulator, q: u32) { if !h.is_null() { unsafe { (*h).apply_y(q as usize); } } }
#[no_mangle] pub extern "C" fn abirqu_z   (h: AbirQuSimulator, q: u32) { if !h.is_null() { unsafe { (*h).apply_z(q as usize); } } }
#[no_mangle] pub extern "C" fn abirqu_s   (h: AbirQuSimulator, q: u32) { if !h.is_null() { unsafe { (*h).apply_gate_butterfly(q as usize, &Simulator::MAT_S); } } }
#[no_mangle] pub extern "C" fn abirqu_t   (h: AbirQuSimulator, q: u32) { if !h.is_null() { unsafe { (*h).apply_gate_butterfly(q as usize, &Simulator::mat_t()); } } }
#[no_mangle] pub extern "C" fn abirqu_rx  (h: AbirQuSimulator, q: u32, angle: f64) { if !h.is_null() { unsafe { (*h).apply_rx(q as usize, angle); } } }
#[no_mangle] pub extern "C" fn abirqu_ry  (h: AbirQuSimulator, q: u32, angle: f64) { if !h.is_null() { unsafe { (*h).apply_ry(q as usize, angle); } } }
#[no_mangle] pub extern "C" fn abirqu_rz  (h: AbirQuSimulator, q: u32, angle: f64) { if !h.is_null() { unsafe { (*h).apply_rz(q as usize, angle); } } }
#[no_mangle] pub extern "C" fn abirqu_cnot(h: AbirQuSimulator, ctrl: u32, tgt: u32) { if !h.is_null() { unsafe { (*h).apply_cnot(ctrl as usize, tgt as usize); } } }
#[no_mangle] pub extern "C" fn abirqu_cz  (h: AbirQuSimulator, ctrl: u32, tgt: u32) { if !h.is_null() { unsafe { (*h).apply_cz(ctrl as usize, tgt as usize); } } }
#[no_mangle] pub extern "C" fn abirqu_swap(h: AbirQuSimulator, q0: u32, q1: u32) {
    if h.is_null() { return; }
    let sim = unsafe { &mut *h };
    sim._cnot(q0 as usize, q1 as usize);
    sim._cnot(q1 as usize, q0 as usize);
    sim._cnot(q0 as usize, q1 as usize);
}

// ═══════════════════════════════════════════════════════════════════════════
// Batch circuit execution
// ═══════════════════════════════════════════════════════════════════════════

/// Execute a batch of gates described by the `gates` array of length `n_gates`.
///
/// # Safety
/// `handle` must be a valid non-null pointer from `abirqu_simulator_create`.
/// `gates`  must point to at least `n_gates` consecutive `AbirQuGate` values.
#[no_mangle]
pub unsafe extern "C" fn abirqu_run_circuit(
    handle: AbirQuSimulator,
    gates:  *const AbirQuGate,
    n_gates: usize,
) {
    if handle.is_null() || gates.is_null() { return; }
    let sim = &mut *handle;
    let gate_slice = std::slice::from_raw_parts(gates, n_gates);
    for g in gate_slice {
        let c = g.ctrl   as usize;
        let t = g.target as usize;
        match g.gate_type {
            AQ_GATE_H    => sim.apply_h(c),
            AQ_GATE_X    => sim.apply_x(c),
            AQ_GATE_Y    => sim.apply_y(c),
            AQ_GATE_Z    => sim.apply_z(c),
            AQ_GATE_S    => sim.apply_gate_butterfly(c, &Simulator::MAT_S),
            AQ_GATE_T    => sim.apply_gate_butterfly(c, &Simulator::mat_t()),
            AQ_GATE_CNOT => sim.apply_cnot(c, t),
            AQ_GATE_CZ   => sim.apply_cz(c, t),
            AQ_GATE_RX   => sim.apply_rx(c, g.param),
            AQ_GATE_RY   => sim.apply_ry(c, g.param),
            AQ_GATE_RZ   => sim.apply_rz(c, g.param),
            AQ_GATE_SWAP => { sim._cnot(c,t); sim._cnot(t,c); sim._cnot(c,t); }
            _ => {}
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// State readout
// ═══════════════════════════════════════════════════════════════════════════

/// Copy measurement probabilities into caller-supplied buffer `out_probs`.
///
/// `out_probs` must have room for at least `abirqu_hilbert_dim(handle)` doubles.
/// Returns the number of values written, or 0 on error.
#[no_mangle]
pub extern "C" fn abirqu_get_probabilities(
    handle: AbirQuSimulator,
    out_probs: *mut f64,
) -> usize {
    if handle.is_null() || out_probs.is_null() { return 0; }
    let sim = unsafe { &*handle };
    let n = sim.state.len();
    let buf = unsafe { std::slice::from_raw_parts_mut(out_probs, n) };
    for (i, c) in sim.state.iter().enumerate() {
        buf[i] = c.norm_sqr();
    }
    n
}

/// Copy the statevector into caller-supplied buffers `out_re` and `out_im`.
///
/// Both buffers must have room for at least `abirqu_hilbert_dim(handle)` doubles.
/// Returns the number of complex amplitudes written, or 0 on error.
#[no_mangle]
pub extern "C" fn abirqu_get_statevector(
    handle: AbirQuSimulator,
    out_re: *mut f64,
    out_im: *mut f64,
) -> usize {
    if handle.is_null() || out_re.is_null() || out_im.is_null() { return 0; }
    let sim = unsafe { &*handle };
    let n = sim.state.len();
    let re_buf = unsafe { std::slice::from_raw_parts_mut(out_re, n) };
    let im_buf = unsafe { std::slice::from_raw_parts_mut(out_im, n) };
    for (i, c) in sim.state.iter().enumerate() {
        re_buf[i] = c.re;
        im_buf[i] = c.im;
    }
    n
}
