package com.abirqu

import com.sun.jna.Structure

@Structure.FieldOrder("gateType", "pad0", "pad1", "pad2", "ctrl", "target", "param")
open class AbirQuGate : Structure {
    @JvmField var gateType: Byte = 0
    @JvmField var pad0: Byte = 0
    @JvmField var pad1: Byte = 0
    @JvmField var pad2: Byte = 0
    @JvmField var ctrl: Int = 0
    @JvmField var target: Int = 0
    @JvmField var param: Double = 0.0

    constructor() : super()

    constructor(gateType: Int, ctrl: Int, target: Int, param: Double) : super() {
        this.gateType = gateType.toByte()
        this.ctrl = ctrl
        this.target = target
        this.param = param
    }

    constructor(gateType: Int, qubit: Int) : this(gateType, qubit, 0, 0.0)

    class ByReference : AbirQuGate(), Structure.ByReference
    class ByValue : AbirQuGate(), Structure.ByValue

    companion object {
        @JvmStatic fun h(q: Int) = AbirQuGate(AbirQuSimulator.GATE_H, q)
        @JvmStatic fun x(q: Int) = AbirQuGate(AbirQuSimulator.GATE_X, q)
        @JvmStatic fun y(q: Int) = AbirQuGate(AbirQuSimulator.GATE_Y, q)
        @JvmStatic fun z(q: Int) = AbirQuGate(AbirQuSimulator.GATE_Z, q)
        @JvmStatic fun cnot(ctrl: Int, tgt: Int) = AbirQuGate(AbirQuSimulator.GATE_CNOT, ctrl, tgt, 0.0)
        @JvmStatic fun rx(q: Int, angle: Double) = AbirQuGate(AbirQuSimulator.GATE_RX, q, q, angle)
        @JvmStatic fun ry(q: Int, angle: Double) = AbirQuGate(AbirQuSimulator.GATE_RY, q, q, angle)
        @JvmStatic fun rz(q: Int, angle: Double) = AbirQuGate(AbirQuSimulator.GATE_RZ, q, q, angle)
    }
}
