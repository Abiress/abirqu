// WebAssembly tests for AbirQu
use wasm_bindgen_test::*;
use abirqu_core_wasm::WasmSimulator;

#[wasm_bindgen_test]
fn test_create_simulator() {
    let sim = WasmSimulator::new(2);
    assert_eq!(sim.num_qubits(), 2);
    assert_eq!(sim.hilbert_dim(), 4);
}

#[wasm_bindgen_test]
fn test_bell_state() {
    let sim = WasmSimulator::create_bell_state();
    let probs = sim.get_probabilities();
    
    assert!((probs[0] - 0.5).abs() < 1e-10);
    assert!((probs[3] - 0.5).abs() < 1e-10);
}

#[wasm_bindgen_test]
fn test_single_qubit() {
    let mut sim = WasmSimulator::new(1);
    sim.h(0);
    let probs = sim.get_probabilities();
    
    assert!((probs[0] - 0.5).abs() < 1e-10);
    assert!((probs[1] - 0.5).abs() < 1e-10);
}

#[wasm_bindgen_test]
fn test_rotation() {
    let mut sim = WasmSimulator::new(1);
    sim.rx(0, std::f64::consts::PI);
    let probs = sim.get_probabilities();
    
    assert!((probs[1] - 1.0).abs() < 1e-10);
}
