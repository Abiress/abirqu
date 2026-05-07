// AbirQu Rust Core - Public Crate
// Re-export all public modules

pub mod simulator;
pub mod c_api;

// Re-export main types
pub use simulator::Simulator;

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
        sim.h(0);
        sim.cnot(0, 1);
        let probs = sim.get_probabilities();
        assert!((probs[0] - 0.5).abs() < 1e-10);
        assert!((probs[3] - 0.5).abs() < 1e-10);
    }
    
    #[test]
    fn test_single_qubit_gates() {
        let mut sim = Simulator::new(1);
        sim.h(0);
        let probs = sim.get_probabilities();
        assert!((probs[0] - 0.5).abs() < 1e-10);
        assert!((probs[1] - 0.5).abs() < 1e-10);
    }
    
    #[test]
    fn test_rotation_gates() {
        let mut sim = Simulator::new(1);
        sim.rx(0, std::f64::consts::PI);
        let probs = sim.get_probabilities();
        assert!((probs[1] - 1.0).abs() < 1e-10);
    }
}
