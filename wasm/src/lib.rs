// AbirQu WebAssembly Module
// This module is compiled to WebAssembly using wasm-pack
// Usage in browser: import * as abirqu from './pkg/abirqu_core_wasm.js';

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
extern "C" {
    fn alert(s: &str);
}

#[wasm_bindgen]
pub struct WasmSimulator {
    num_qubits: usize,
    state: Vec<f64>, // Interleaved [re0, im0, re1, im1, ...]
}

#[wasm_bindgen]
impl WasmSimulator {
    #[wasm_bindgen(constructor)]
    pub fn new(num_qubits: usize) -> WasmSimulator {
        let size = 1usize << num_qubits;
        let mut state = vec![0.0; size * 2];
        state[0] = 1.0; // |0...0> state
        WasmSimulator { num_qubits, state }
    }
    
    pub fn num_qubits(&self) -> usize {
        self.num_qubits
    }
    
    pub fn hilbert_dim(&self) -> usize {
        1usize << self.num_qubits
    }
    
    /// Apply H gate
    pub fn h(&mut self, q: usize) {
        let mask = 1usize << q;
        let dim = 1usize << self.num_qubits;
        let inv_sqrt2 = 1.0 / 2.0f64.sqrt();
        
        for i in (0..dim).step_by(mask * 2) {
            for j in i..i + mask {
                let k = j | mask;
                let re0 = self.state[j * 2];
                let im0 = self.state[j * 2 + 1];
                let re1 = self.state[k * 2];
                let im1 = self.state[k * 2 + 1];
                
                self.state[j * 2] = inv_sqrt2 * (re0 + re1);
                self.state[j * 2 + 1] = inv_sqrt2 * (im0 + im1);
                self.state[k * 2] = inv_sqrt2 * (re0 - re1);
                self.state[k * 2 + 1] = inv_sqrt2 * (im0 - im1);
            }
        }
    }
    
    /// Apply X gate
    pub fn x(&mut self, q: usize) {
        let mask = 1usize << q;
        let dim = 1usize << self.num_qubits;
        
        for i in (0..dim).step_by(mask * 2) {
            for j in i..i + mask {
                let k = j | mask;
                let re0 = self.state[j * 2];
                let im0 = self.state[j * 2 + 1];
                self.state[j * 2] = self.state[k * 2];
                self.state[j * 2 + 1] = self.state[k * 2 + 1];
                self.state[k * 2] = re0;
                self.state[k * 2 + 1] = im0;
            }
        }
    }
    
    /// Apply CNOT gate
    pub fn cnot(&mut self, ctrl: usize, tgt: usize) {
        let dim = 1usize << self.num_qubits;
        let cmask = 1usize << ctrl;
        let tmask = 1usize << tgt;
        
        for i in 0..dim {
            if (i & cmask) != 0 {
                let j = i ^ tmask;
                if j > i {
                    for q in 0..self.num_qubits {
                        let qmask = 1usize << q;
                        if (i & qmask) != 0 {
                            let re0 = self.state[i * 2];
                            let im0 = self.state[i * 2 + 1];
                            self.state[i * 2] = self.state[j * 2];
                            self.state[i * 2 + 1] = self.state[j * 2 + 1];
                            self.state[j * 2] = re0;
                            self.state[j * 2 + 1] = im0;
                        }
                    }
                }
            }
        }
    }
    
    /// Get measurement probabilities
    pub fn get_probabilities(&self) -> Vec<f64> {
        let dim = 1usize << self.num_qubits;
        let mut probs = Vec::with_capacity(dim);
        
        for i in 0..dim {
            let re = self.state[i * 2];
            let im = self.state[i * 2 + 1];
            probs.push(re * re + im * im);
        }
        
        probs
    }
    
    /// Get state vector (interleaved [re, im, re, im, ...])
    pub fn get_statevector(&self) -> Vec<f64> {
        self.state.clone()
    }
    
    /// Create Bell state |00> + |11>
    pub fn create_bell_state() -> WasmSimulator {
        let mut sim = WasmSimulator::new(2);
        sim.h(0);
        sim.cnot(0, 1);
        sim
    }
    
    /// Reset to |0...0>
    pub fn reset(&mut self) {
        let size = 1usize << self.num_qubits;
        for i in 0..size * 2 {
            self.state[i] = 0.0;
        }
        self.state[0] = 1.0;
    }
}
