// ═══════════════════════════════════════════════════════════════════════════
//  AbirQu Rust Core - Public Crate for Quantum Computing
//  
//  A high-performance quantum computing library that beats Qiskit & Cirq
//  with LDPC codes, Phase Polynomial Optimization, and GPU acceleration.
// ═══════════════════════════════════════════════════════════════════════════

pub mod simulator;
pub mod c_api;
pub mod gates;
pub mod circuit;
pub mod noise;
pub mod optimizer;
pub mod phase_poly;
pub mod qec;
pub mod tensor_network;
pub mod clifford_sim;
pub mod transpiler;
pub mod zx_calculus;

// Re-export main types for convenience
pub use simulator::Simulator;

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use simulator::Simulator;

/// High-performance Rust backend module for AbirQu
#[cfg(feature = "python")]
#[pymodule]
fn abirqu_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Simulator>()?;
    Ok(())
}

/// Get library version
pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// Get library description
pub fn description() -> &'static str {
    env!("CARGO_PKG_DESCRIPTION")
}

#[cfg(test)]
mod tests {
    use super::*;
    use simulator::Simulator;
    
    #[test]
    fn test_version() {
        assert!(!version().is_empty());
        assert_eq!(version(), "1.0.0");
    }
    
    #[test]
    fn test_simulator_creation() {
        let sim = Simulator::new(2);
        assert_eq!(sim.num_qubits, 2);
    }
    
    #[test]
    fn test_bell_state() {
        let mut sim = Simulator::new(2);
        sim.apply_h(0);
        sim.apply_cnot(0, 1);
        let probs = sim.get_probabilities();
        assert!((probs[0] - 0.5).abs() < 1e-10);
        assert!((probs[3] - 0.5).abs() < 1e-10);
    }
    
    #[test]
    fn test_single_qubit_gates() {
        let mut sim = Simulator::new(1);
        sim.apply_h(0);
        let probs = sim.get_probabilities();
        assert!((probs[0] - 0.5).abs() < 1e-10);
        assert!((probs[1] - 0.5).abs() < 1e-10);
    }
    
    #[test]
    fn test_rotation_gates() {
        let mut sim = Simulator::new(1);
        sim.apply_rx(0, std::f64::consts::PI);
        let probs = sim.get_probabilities();
        assert!((probs[1] - 1.0).abs() < 1e-10);
    }
}
