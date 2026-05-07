// AbirQu Swift Wrapper - Using CInterop
// Swift package that calls libabirqu_core.so via CInterop

import Foundation

/// Quantum Simulator Swift wrapper
public class AbirQuSimulator {
    // Opaque handle
    private var handle: OpaquePointer?
    
    // Gate constants
    public static let GATE_H: UInt8 = 0
    public static let GATE_X: UInt8 = 1
    public static let GATE_Y: UInt8 = 2
    public static let GATE_Z: UInt8 = 3
    public static let GATE_S: UInt8 = 4
    public static let GATE_T: UInt8 = 5
    public static let GATE_CNOT: UInt8 = 6
    public static let GATE_CZ: UInt8 = 7
    public static let GATE_RX: UInt8 = 8
    public static let GATE_RY: UInt8 = 9
    public static let GATE_RZ: UInt8 = 10
    public static let GATE_SWAP: UInt8 = 11
    
    /// Create a new simulator for numQubits qubits
    public init(numQubits: UInt32) {
        let sim = abirqu_simulator_create(numQubits)
        if sim == nil {
            fatalError("Failed to create simulator")
        }
        handle = sim
    }
    
    deinit {
        if let h = handle {
            abirqu_simulator_destroy(h)
        }
    }
    
    /// Get number of qubits
    public var numQubits: UInt32 {
        guard let h = handle else { return 0 }
        return abirqu_num_qubits(h)
    }
    
    /// Get Hilbert space dimension
    public var hilbertDim: UInt {
        guard let h = handle else { return 0 }
        return UInt(abirqu_hilbert_dim(h))
    }
    
    // Gate operations
    public func h(_ q: UInt32) {
        if let h = handle { abirqu_h(h, q) }
    }
    
    public func x(_ q: UInt32) {
        if let h = handle { abirqu_x(h, q) }
    }
    
    public func y(_ q: UInt32) {
        if let h = handle { abirqu_y(h, q) }
    }
    
    public func z(_ q: UInt32) {
        if let h = handle { abirqu_z(h, q) }
    }
    
    public func s(_ q: UInt32) {
        if let h = handle { abirqu_s(h, q) }
    }
    
    public func t(_ q: UInt32) {
        if let h = handle { abirqu_t(h, q) }
    }
    
    public func rx(_ q: UInt32, angle: Double) {
        if let h = handle { abirqu_rx(h, q, angle) }
    }
    
    public func ry(_ q: UInt32, angle: Double) {
        if let h = handle { abirqu_ry(h, q, angle) }
    }
    
    public func rz(_ q: UInt32, angle: Double) {
        if let h = handle { abirqu_rz(h, q, angle) }
    }
    
    public func cnot(ctrl: UInt32, tgt: UInt32) {
        if let h = handle { abirqu_cnot(h, ctrl, tgt) }
    }
    
    public func cz(ctrl: UInt32, tgt: UInt32) {
        if let h = handle { abirqu_cz(h, ctrl, tgt) }
    }
    
    public func swap(_ q0: UInt32, _ q1: UInt32) {
        if let h = handle { abirqu_swap(h, q0, q1) }
    }
    
    /// Get measurement probabilities
    public func getProbabilities() -> [Double] {
        guard let h = handle else { return [] }
        let dim = Int(hilbertDim)
        var probs = [Double](repeating: 0.0, count: dim)
        abirqu_get_probabilities(h, &probs)
        return probs
    }
    
    /// Get state vector as interleaved [re0, im0, re1, im1, ...]
    public func getStatevector() -> [Double] {
        guard let h = handle else { return [] }
        let dim = Int(hilbertDim)
        var re = [Double](repeating: 0.0, count: dim)
        var im = [Double](repeating: 0.0, count: dim)
        abirqu_get_statevector(h, &re, &im)
        
        var state = [Double](repeating: 0.0, count: dim * 2)
        for i in 0..<dim {
            state[i * 2] = re[i]
            state[i * 2 + 1] = im[i]
        }
        return state
    }
    
    /// Create Bell state |00> + |11>
    public static func createBellState() -> AbirQuSimulator {
        let sim = AbirQuSimulator(numQubits: 2)
        sim.h(0)
        sim.cnot(ctrl: 0, tgt: 1)
        return sim
    }
}

// C function declarations
@_silgen_name(abirqu_simulator_create)
func abirqu_simulator_create(_ num_qubits: UInt32) -> OpaquePointer?

@_silgen_name(abirqu_simulator_destroy)
func abirqu_simulator_destroy(_ handle: OpaquePointer)

@_silgen_name(abirqu_num_qubits)
func abirqu_num_qubits(_ handle: OpaquePointer) -> UInt32

@_silgen_name(abirqu_hilbert_dim)
func abirqu_hilbert_dim(_ handle: OpaquePointer) -> UInt

@_silgen_name(abirqu_h)
func abirqu_h(_ handle: OpaquePointer, _ q: UInt32)

@_silgen_name(abirqu_x)
func abirqu_x(_ handle: OpaquePointer, _ q: UInt32)

@_silgen_name(abirqu_y)
func abirqu_y(_ handle: OpaquePointer, _ q: UInt32)

@_silgen_name(abirqu_z)
func abirqu_z(_ handle: OpaquePointer, _ q: UInt32)

@_silgen_name(abirqu_s)
func abirqu_s(_ handle: OpaquePointer, _ q: UInt32)

@_silgen_name(abirqu_t)
func abirqu_t(_ handle: OpaquePointer, _ q: UInt32)

@_silgen_name(abirqu_rx)
func abirqu_rx(_ handle: OpaquePointer, _ q: UInt32, _ angle: Double)

@_silgen_name(abirqu_ry)
func abirqu_ry(_ handle: OpaquePointer, _ q: UInt32, _ angle: Double)

@_silgen_name(abirqu_rz)
func abirqu_rz(_ handle: OpaquePointer, _ q: UInt32, _ angle: Double)

@_silgen_name(abirqu_cnot)
func abirqu_cnot(_ handle: OpaquePointer, _ ctrl: UInt32, _ tgt: UInt32)

@_silgen_name(abirqu_cz)
func abirqu_cz(_ handle: OpaquePointer, _ ctrl: UInt32, _ tgt: UInt32)

@_silgen_name(abirqu_swap)
func abirqu_swap(_ handle: OpaquePointer, _ q0: UInt32, _ q1: UInt32)

@_silgen_name(abirqu_get_probabilities)
func abirqu_get_probabilities(_ handle: OpaquePointer, _ out_probs: UnsafeMutablePointer<Double>)

@_silgen_name(abirqu_get_statevector)
func abirqu_get_statevector(_ handle: OpaquePointer, _ out_re: UnsafeMutablePointer<Double>, _ out_im: UnsafeMutablePointer<Double>)
