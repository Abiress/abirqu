use num_complex::Complex64;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyBytes;
use rayon::prelude::*;

// Gate constants
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

const PAR_THRESHOLD: usize = 1 << 14;
#[cfg_attr(feature = "python", pyclass)]
pub struct Simulator {
    pub num_qubits: usize,
    pub state: Vec<Complex64>,
}

// Pure Rust / C ABI Methods
impl Simulator {
    pub fn new(num_qubits: usize) -> Self {
        let size = 1usize << num_qubits;
        let mut state = vec![Complex64::new(0.0, 0.0); size];
        state[0] = Complex64::new(1.0, 0.0);
        Simulator { num_qubits, state }
    }

    pub fn run_circuit_internal(&mut self, gates: Vec<(u8, Vec<usize>, f64)>) {
        for (gt, qs, param) in gates.iter() {
            match *gt {
                GATE_H    => self.apply_gate_butterfly(qs[0], &Self::mat_h()),
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

    pub fn apply_h(&mut self, q: usize)    { self.apply_gate_butterfly(q, &Self::mat_h()); }
    pub fn apply_x(&mut self, q: usize)    { self.apply_gate_butterfly(q, &Self::MAT_X); }
    pub fn apply_y(&mut self, q: usize)    { self.apply_gate_butterfly(q, &Self::MAT_Y); }
    pub fn apply_z(&mut self, q: usize)    { self.apply_gate_butterfly(q, &Self::MAT_Z); }
    pub fn apply_rx(&mut self, q: usize, t: f64) { self.apply_gate_butterfly(q, &Self::mat_rx(t)); }
    pub fn apply_ry(&mut self, q: usize, t: f64) { self.apply_gate_butterfly(q, &Self::mat_ry(t)); }
    pub fn apply_rz(&mut self, q: usize, t: f64) { self.apply_gate_butterfly(q, &Self::mat_rz(t)); }
    pub fn apply_cnot(&mut self, c: usize, t: usize) { self._cnot(c, t); }
    pub fn apply_cz(&mut self, c: usize, t: usize)   { self.apply_cphase(c, t, Complex64::new(-1.0, 0.0)); }

    pub fn get_probabilities(&self) -> Vec<f64> {
        if self.state.len() >= PAR_THRESHOLD {
            self.state.par_iter().map(|c| c.norm_sqr()).collect()
        } else {
            self.state.iter().map(|c| c.norm_sqr()).collect()
        }
    }

    pub fn get_state(&self) -> Vec<(f64, f64)> {
        self.state.iter().map(|c| (c.re, c.im)).collect()
    }

    pub(crate) fn apply_gate_butterfly(&mut self, q: usize, gate: &[Complex64; 4]) {
        let n = 1usize << self.num_qubits;
        let mask = 1usize << q;
        for i in (0..n).step_by(mask * 2) {
            for j in i..i + mask {
                let k = j | mask;
                let s0 = self.state[j];
                let s1 = self.state[k];
                self.state[j] = gate[0] * s0 + gate[1] * s1;
                self.state[k] = gate[2] * s0 + gate[3] * s1;
            }
        }
    }

    pub fn _cnot(&mut self, c: usize, t: usize) {
        let n = 1usize << self.num_qubits;
        let cmask = 1usize << c;
        let tmask = 1usize << t;
        for i in 0..n {
            if i & cmask != 0 {
                let j = i ^ tmask;
                if j > i {
                    self.state.swap(i, j);
                }
            }
        }
    }

    pub fn apply_cphase(&mut self, c: usize, t: usize, phase: Complex64) {
        let n = 1usize << self.num_qubits;
        let cmask = 1usize << c;
        let tmask = 1usize << t;
        for i in 0..n {
            if i & cmask != 0 && i & tmask != 0 {
                self.state[i] *= phase;
            }
        }
    }

    pub(crate) fn mat_h() -> [Complex64; 4] {
        let s = 0.5f64.sqrt();
        [Complex64::new(s, 0.0), Complex64::new(s, 0.0),
         Complex64::new(s, 0.0), Complex64::new(-s, 0.0)]
    }

    pub(crate) fn mat_t() -> [Complex64; 4] {
        let c = Complex64::new(0.5f64.sqrt(), 0.5f64.sqrt());
        [Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
         Complex64::new(0.0, 0.0), c]
    }

    pub(crate) fn mat_rx(theta: f64) -> [Complex64; 4] {
        let c = (theta / 2.0).cos();
        let s = (theta / 2.0).sin();
        [Complex64::new(c, 0.0), Complex64::new(0.0, -s),
         Complex64::new(0.0, -s), Complex64::new(c, 0.0)]
    }

    pub(crate) fn mat_ry(theta: f64) -> [Complex64; 4] {
        let c = (theta / 2.0).cos();
        let s = (theta / 2.0).sin();
        [Complex64::new(c, 0.0), Complex64::new(-s, 0.0),
         Complex64::new(s, 0.0), Complex64::new(c, 0.0)]
    }

    pub(crate) fn mat_rz(theta: f64) -> [Complex64; 4] {
        let neg_half = -theta / 2.0;
        [Complex64::new(neg_half.cos(), neg_half.sin()), Complex64::new(0.0, 0.0),
         Complex64::new(0.0, 0.0), Complex64::new(neg_half.cos(), -neg_half.sin())]
    }

    pub(crate) const MAT_X: [Complex64; 4] = [
        Complex64::new(0.0, 0.0), Complex64::new(1.0, 0.0),
        Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
    ];

    pub(crate) const MAT_Y: [Complex64; 4] = [
        Complex64::new(0.0, 0.0), Complex64::new(0.0, -1.0),
        Complex64::new(0.0, 1.0), Complex64::new(0.0, 0.0),
    ];

    pub(crate) const MAT_Z: [Complex64; 4] = [
        Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
        Complex64::new(0.0, 0.0), Complex64::new(-1.0, 0.0),
    ];

    pub(crate) const MAT_S: [Complex64; 4] = [
        Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0),
        Complex64::new(0.0, 0.0), Complex64::new(0.0, 1.0),
    ];
}

// Python Methods
#[cfg(feature = "python")]
#[pymethods]
impl Simulator {
    #[new]
    pub fn py_new(num_qubits: usize) -> Self {
        Self::new(num_qubits)
    }

    pub fn run_circuit(&mut self, gates: Vec<(u8, Vec<usize>, f64)>) {
        self.run_circuit_internal(gates)
    }

    pub fn get_probabilities_bytes<'py>(&self, py: Python<'py>) -> Py<PyBytes> {
        let probs = self.get_probabilities();
        let bytes = unsafe {
            std::slice::from_raw_parts(probs.as_ptr() as *const u8, probs.len() * 8)
        };
        PyBytes::new_bound(py, &bytes).unbind()
    }
}
