// AbirQuSwiftTests.swift
// Test suite for Swift wrapper

import XCTest

final class AbirQuTests: XCTestCase {
    
    func testCreateSimulator() {
        let sim = AbirQuSimulator(numQubits: 2)
        XCTAssertEqual(sim.numQubits, 2)
        XCTAssertEqual(sim.hilbertDim, 4)
    }
    
    func testBellState() {
        let sim = AbirQuSimulator.createBellState()
        let probs = sim.getProbabilities()
        
        XCTAssertEqual(probs.count, 4)
        XCTAssertLessThan(abs(probs[0] - 0.5), 1e-10)
        XCTAssertLessThan(abs(probs[3] - 0.5), 1e-10)
        XCTAssertLessThan(probs[1], 1e-10)
        XCTAssertLessThan(probs[2], 1e-10)
    }
    
    func testSingleQubitGates() {
        let sim = AbirQuSimulator(numQubits: 1)
        sim.h(0)
        let probs = sim.getProbabilities()
        
        XCTAssertLessThan(abs(probs[0] - 0.5), 1e-10)
        XCTAssertLessThan(abs(probs[1] - 0.5), 1e-10)
    }
    
    func testRotationGates() {
        let sim = AbirQuSimulator(numQubits: 1)
        sim.rx(0, angle: Double.pi)
        let probs = sim.getProbabilities()
        
        XCTAssertLessThan(abs(probs[1] - 1.0), 1e-10)
    }
    
    func testStatevector() {
        let sim = AbirQuSimulator.createBellState()
        let state = sim.getStatevector()
        
        XCTAssertEqual(state.count, 8) // 4 complex numbers * 2
        let expected = 1.0 / sqrt(2.0)
        XCTAssertLessThan(abs(state[0] - expected), 1e-10)
    }
    
    func testRunCircuit() {
        let sim = AbirQuSimulator(numQubits: 2)
        let gates = [
            AbirQuGate.h(0),
            AbirQuGate.cnot(ctrl: 0, tgt: 1)
        ]
        sim.runCircuit(gates)
        let probs = sim.getProbabilities()
        
        XCTAssertEqual(probs.count, 4)
        XCTAssertLessThan(abs(probs[0] - 0.5), 1e-10)
        XCTAssertLessThan(abs(probs[3] - 0.5), 1e-10)
        XCTAssertLessThan(probs[1], 1e-10)
        XCTAssertLessThan(probs[2], 1e-10)
    }
}
