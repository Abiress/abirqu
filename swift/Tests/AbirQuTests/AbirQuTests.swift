import XCTest
@testable import AbirQu

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

    func testBatchCircuit() {
        let sim = AbirQuSimulator(numQubits: 2)
        let gates: [AbirQuGate] = [.h(0), .cnot(ctrl: 0, tgt: 1)]
        sim.runCircuit(gates)
        let probs = sim.getProbabilities()
        XCTAssertLessThan(abs(probs[0] - 0.5), 1e-10)
        XCTAssertLessThan(abs(probs[3] - 0.5), 1e-10)
    }
}
