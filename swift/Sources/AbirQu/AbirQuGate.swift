import Foundation

/// Gate descriptor for batch circuit execution.
/// Mirrors the C AbirQuGate struct.
public struct AbirQuGate {
    public var gateType: UInt8
    public var pad0: UInt8 = 0
    public var pad1: UInt8 = 0
    public var pad2: UInt8 = 0
    public var ctrl: UInt32
    public var target: UInt32
    public var param: Double

    public init(gateType: UInt8, ctrl: UInt32, target: UInt32, param: Double) {
        self.gateType = gateType
        self.ctrl = ctrl
        self.target = target
        self.param = param
    }

    public static func h(_ q: UInt32) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_H, ctrl: q, target: 0, param: 0.0)
    }

    public static func x(_ q: UInt32) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_X, ctrl: q, target: 0, param: 0.0)
    }

    public static func y(_ q: UInt32) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_Y, ctrl: q, target: 0, param: 0.0)
    }

    public static func z(_ q: UInt32) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_Z, ctrl: q, target: 0, param: 0.0)
    }

    public static func cnot(ctrl: UInt32, tgt: UInt32) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_CNOT, ctrl: ctrl, target: tgt, param: 0.0)
    }

    public static func rx(_ q: UInt32, angle: Double) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_RX, ctrl: q, target: q, param: angle)
    }

    public static func ry(_ q: UInt32, angle: Double) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_RY, ctrl: q, target: q, param: angle)
    }

    public static func rz(_ q: UInt32, angle: Double) -> AbirQuGate {
        return AbirQuGate(gateType: AbirQuSimulator.GATE_RZ, ctrl: q, target: q, param: angle)
    }
}
