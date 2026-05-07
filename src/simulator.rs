use num_complex::Complex64;
use pyo3::prelude::*;
use rayon::prelude::*;

const GATE_H: u8 = 0;
const GATE_X: u8 = 1;
const GATE_Y: u8 = 2;
const GATE_Z: u8 = 3;
const GATE_S: u8 = 4;
const GATE_T: u8 = 5;
const GATE_CNOT: u8 = 6;
const GATE_CZ: u8 = 7;
const GATE_RX: u8 = 8;
const GATE_RY: u8 = 9;
const GATE_RZ: u8 = 10;
const GATE_SWAP: u8 = 11;

/// Minimum state size for Rayon parallelization (2^14 = 16384 amplitudes).
const PAR_THRESHOLD: usize = 1 << 14;

/// Minimum super-chunk size for par_chunks_mut (2^16 = 65536 amplitudes ≈ 1MB).
/// Ensures each Rayon task processes enough data to amortize thread dispatch overhead.
const MIN_PAR_CHUNK: usize = 1 << 16;

#[pyclass]
pub struct Simulator {
    num_qubits: usize,
    state: Vec<Complex64>,
}

#[pymethods]
impl Simulator {
    #[new]
    pub fn new(num_qubits: usize) -> Self {
        let size = 1usize << num_qubits;
        let mut state = vec![Complex64::new(0.0, 0.0); size];
        state[0] = Complex64::new(1.0, 0.0);
        Simulator { num_qubits, state }
    }

    /// Batch execute an entire circuit in one FFI call.
    /// Each gate is (gate_type: u8, qubits: Vec<usize>, param: f64).
    pub fn run_circuit(&mut self, gates: Vec<(u8, Vec<usize>, f64)>) {
        for (gt, qs, param) in gates.iter() {
            match *gt {
                GATE_H    => self.apply_gate_butterfly(qs[0], &Self::MAT_H),
                GATE_X    => self.apply_gate_butterfly(qs[0], &Self::MAT_X),
                GATE_Y    => self.apply_gate_butterfly(qs[0], &Self::MAT_Y),
                GATE_Z    => self.apply_gate_butterfly(qs[0], &Self::MAT_Z),
                GATE_S    => self.apply_gate_butterfly(qs[0], &Self::MAT_S),
                GATE_T    => self.apply_gate_butterfly(qs[0], &Self::mat_t()),
                GATE_CNOT => self.apply_cnot(qs[0], qs[1]),
                GATE_CZ   => self.apply_cphase(qs[0], qs[1], Complex64::new(-1.0, 0.0)),
                GATE_RX   => self.apply_gate_butterfly(qs[0], &Self::mat_rx(*param)),
                GATE_RY   => self.apply_gate_butterfly(qs[0], &Self::mat_ry(*param)),
                GATE_RZ   => self.apply_gate_butterfly(qs[0], &Self::mat_rz(*param)),
                GATE_SWAP => {
                    self.apply_cnot(qs[0], qs[1]);
                    self.apply_cnot(qs[1], qs[0]);
                    self.apply_cnot(qs[0], qs[1]);
                },
                _ => {}
            }
        }
    }

    // ── Individual gate methods (backward compatibility) ─────────────
    pub fn apply_h(&mut self, q: usize)           { self.apply_gate_butterfly(q, &Self::MAT_H); }
    pub fn apply_x(&mut self, q: usize)           { self.apply_gate_butterfly(q, &Self::MAT_X); }
    pub fn apply_y(&mut self, q: usize)           { self.apply_gate_butterfly(q, &Self::MAT_Y); }
    pub fn apply_z(&mut self, q: usize)           { self.apply_gate_butterfly(q, &Self::MAT_Z); }
    pub fn apply_rx(&mut self, q: usize, t: f64)  { self.apply_gate_butterfly(q, &Self::mat_rx(t)); }
    pub fn apply_ry(&mut self, q: usize, t: f64)  { self.apply_gate_butterfly(q, &Self::mat_ry(t)); }
    pub fn apply_rz(&mut self, q: usize, t: f64)  { self.apply_gate_butterfly(q, &Self::mat_rz(t)); }
    pub fn apply_cnot(&mut self, c: usize, t: usize) { self._cnot(c, t); }
    pub fn apply_cz(&mut self, c: usize, t: usize)   { self.apply_cphase(c, t, Complex64::new(-1.0, 0.0)); }

    // ── State access ────────────────────────────────────────────────
    pub fn get_state(&self) -> Vec<(f64, f64)> {
        self.state.iter().map(|c| (c.re, c.im)).collect()
    }

    pub fn get_probabilities(&self) -> Vec<f64> {
        if self.state.len() >= PAR_THRESHOLD {
            self.state.par_iter().map(|c| c.norm_sqr()).collect()
        } else {
            self.state.iter().map(|c| c.norm_sqr()).collect()
        }
    }

    /// Return probabilities as raw f64 bytes for zero-copy numpy ingestion.
    /// Python: np.frombuffer(sim.get_probabilities_bytes(), dtype=np.float64)
    pub fn get_probabilities_bytes<'py>(&self, py: pyo3::Python<'py>) -> pyo3::Py<pyo3::types::PyBytes> {
        let probs = self.get_probabilities();
        let bytes = unsafe {
            std::slice::from_raw_parts(probs.as_ptr() as *const u8, probs.len() * 8)
        };
        pyo3::types::PyBytes::new_bound(py, bytes).unbind()
    }
}

// ── Gate matrices ──────────────────────────────────────────────────────
// Layout: [U00, U01, U10, U11] so new_lo = U00*a + U01*b, new_hi = U10*a + U11*b.

impl Simulator {
    const INV_SQRT2: f64 = std::f64::consts::FRAC_1_SQRT_2;

    const MAT_H: [Complex64; 4] = [
        Complex64::new(Self::INV_SQRT2, 0.0), Complex64::new(Self::INV_SQRT2, 0.0),
        Complex64::new(Self::INV_SQRT2, 0.0), Complex64::new(-Self::INV_SQRT2, 0.0),
    ];
    const MAT_X: [Complex64; 4] = [
        Complex64::new(0.0, 0.0), Complex64::new(1.0, 0.0),
        Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
    ];
    const MAT_Y: [Complex64; 4] = [
        Complex64::new(0.0, 0.0),  Complex64::new(0.0, -1.0),
        Complex64::new(0.0, 1.0),  Complex64::new(0.0, 0.0),
    ];
    const MAT_Z: [Complex64; 4] = [
        Complex64::new(1.0, 0.0),  Complex64::new(0.0, 0.0),
        Complex64::new(0.0, 0.0),  Complex64::new(-1.0, 0.0),
    ];
    const MAT_S: [Complex64; 4] = [
        Complex64::new(1.0, 0.0),  Complex64::new(0.0, 0.0),
        Complex64::new(0.0, 0.0),  Complex64::new(0.0, 1.0),
    ];

    fn mat_t() -> [Complex64; 4] {
        [
            Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
            Complex64::new(0.0, 0.0), Complex64::new(
                std::f64::consts::FRAC_PI_4.cos(),
                std::f64::consts::FRAC_PI_4.sin()),
        ]
    }
    fn mat_rx(theta: f64) -> [Complex64; 4] {
        let c = Complex64::new((theta / 2.0).cos(), 0.0);
        let is = Complex64::new(0.0, -(theta / 2.0).sin());
        [c, is, is, c]
    }
    fn mat_ry(theta: f64) -> [Complex64; 4] {
        let c = Complex64::new((theta / 2.0).cos(), 0.0);
        let s = Complex64::new((theta / 2.0).sin(), 0.0);
        [c, -s, s, c]
    }
    fn mat_rz(theta: f64) -> [Complex64; 4] {
        let p0 = Complex64::new(0.0, -theta / 2.0).exp();
        let p1 = Complex64::new(0.0, theta / 2.0).exp();
        [p0, Complex64::new(0.0, 0.0), Complex64::new(0.0, 0.0), p1]
    }
}

// ── Core simulation engine ────────────────────────────────────────────
//
// Butterfly-block with par_chunks_mut:
//
//   For a single-qubit gate on qubit q:
//     bit = 2^q
//     chunk_size = 2 * bit
//     The state vector is split into chunks of chunk_size.
//     Each chunk contains exactly one butterfly block:
//       chunk[0..bit]    = "lo" half (qubit q = 0)
//       chunk[bit..2*bit] = "hi" half (qubit q = 1)
//     Pairs: (lo[k], hi[k]) for k = 0..bit
//
//   par_chunks_mut gives each thread an exclusive &mut [Complex64] slice.
//   No unsafe, no SendPtr, no data races. Rayon guarantees disjoint slices.
//
//   For high qubits (bit >= state.len()/2), there's only 1 chunk,
//   so we parallelize the inner loop instead using par_iter on lo/hi zips.

impl Simulator {
    /// Apply a 2x2 unitary gate to a single qubit using butterfly blocks.
    /// Optimized with unsafe get_unchecked for SIMD vectorization and 
    /// refined Rayon thresholds to avoid overhead on low qubits.
    fn apply_gate_butterfly(&mut self, qubit: usize, mat: &[Complex64; 4]) {
        let bit = 1usize << qubit;
        let block_size = 2 * bit;
        let n = self.state.len();

        let u00 = mat[0]; let u01 = mat[1];
        let u10 = mat[2]; let u11 = mat[3];

        if n >= 4096 {
            let super_size = block_size.max(65536);
            if super_size < n {
                self.state.par_chunks_mut(super_size).for_each(|super_chunk| {
                    for chunk in super_chunk.chunks_mut(block_size) {
                        let (lo, hi) = chunk.split_at_mut(bit);
                        for k in 0..bit {
                            unsafe {
                                let a = *lo.get_unchecked(k);
                                let b = *hi.get_unchecked(k);
                                *lo.get_unchecked_mut(k) = u00 * a + u01 * b;
                                *hi.get_unchecked_mut(k) = u10 * a + u11 * b;
                            }
                        }
                    }
                });
            } else {
                let (lo, hi) = self.state.split_at_mut(bit);
                lo.par_iter_mut().zip(hi.par_iter_mut()).for_each(|(a_ptr, b_ptr)| {
                    let a = *a_ptr;
                    let b = *b_ptr;
                    *a_ptr = u00 * a + u01 * b;
                    *b_ptr = u10 * a + u11 * b;
                });
            }
        } else {
            for chunk in self.state.chunks_mut(block_size) {
                let (lo, hi) = chunk.split_at_mut(bit);
                for k in 0..bit {
                    unsafe {
                        let a = *lo.get_unchecked(k);
                        let b = *hi.get_unchecked(k);
                        *lo.get_unchecked_mut(k) = u00 * a + u01 * b;
                        *hi.get_unchecked_mut(k) = u10 * a + u11 * b;
                    }
                }
            }
        }
    }

    fn _cnot(&mut self, control: usize, target: usize) {
        let cb = 1usize << control;
        let tb = 1usize << target;
        let block_size = 2 * tb;
        let n = self.state.len();

        if n >= 4096 {
            let super_size = block_size.max(65536);
            if super_size < n {
                self.state.par_chunks_mut(super_size).enumerate().for_each(|(si, super_chunk)| {
                    for (ci, chunk) in super_chunk.chunks_mut(block_size).enumerate() {
                        let base = si * super_size + ci * block_size;
                        let (lo, hi) = chunk.split_at_mut(tb);
                        for k in 0..tb {
                            if ((base + k) & cb) != 0 {
                                unsafe {
                                    let a = *lo.get_unchecked(k);
                                    let b = *hi.get_unchecked(k);
                                    *lo.get_unchecked_mut(k) = b;
                                    *hi.get_unchecked_mut(k) = a;
                                }
                            }
                        }
                    }
                });
            } else {
                let (lo, hi) = self.state.split_at_mut(tb);
                lo.par_iter_mut().zip(hi.par_iter_mut()).enumerate().for_each(|(k, (a, b))| {
                    if (k & cb) != 0 {
                        std::mem::swap(a, b);
                    }
                });
            }
        } else {
            for (si, chunk) in self.state.chunks_mut(block_size).enumerate() {
                let base = si * block_size;
                let (lo, hi) = chunk.split_at_mut(tb);
                for k in 0..tb {
                    if ((base + k) & cb) != 0 {
                        unsafe {
                            let a = *lo.get_unchecked(k);
                            let b = *hi.get_unchecked(k);
                            *lo.get_unchecked_mut(k) = b;
                            *hi.get_unchecked_mut(k) = a;
                        }
                    }
                }
            }
        }
    }

    fn apply_cphase(&mut self, control: usize, target: usize, phase: Complex64) {
        let cb = 1usize << control;
        let tb = 1usize << target;
        let block_size = 2 * tb;
        let n = self.state.len();

        if n >= 4096 {
            let super_size = block_size.max(65536);
            if super_size < n {
                self.state.par_chunks_mut(super_size).enumerate().for_each(|(si, super_chunk)| {
                    for (ci, chunk) in super_chunk.chunks_mut(block_size).enumerate() {
                        let base = si * super_size + ci * block_size;
                        let (_lo, hi) = chunk.split_at_mut(tb);
                        for k in 0..tb {
                            if ((base + k) & cb) != 0 {
                                unsafe {
                                    *hi.get_unchecked_mut(k) = *hi.get_unchecked(k) * phase;
                                }
                            }
                        }
                    }
                });
            } else {
                let (_lo, hi) = self.state.split_at_mut(tb);
                hi.par_iter_mut().enumerate().for_each(|(k, amp)| {
                    if (k & cb) != 0 {
                        *amp = *amp * phase;
                    }
                });
            }
        } else {
            for (si, chunk) in self.state.chunks_mut(block_size).enumerate() {
                let base = si * block_size;
                let (_lo, hi) = chunk.split_at_mut(tb);
                for k in 0..tb {
                    if ((base + k) & cb) != 0 {
                        unsafe {
                            *hi.get_unchecked_mut(k) = *hi.get_unchecked(k) * phase;
                        }
                    }
                }
            }
        }
    }
}
