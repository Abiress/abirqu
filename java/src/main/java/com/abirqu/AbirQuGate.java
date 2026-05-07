package com.abirqu;

/**
 * Gate descriptor for batch circuit execution
 * Mirrors the C AbirQuGate struct
 */
public class AbirQuGate {
    public byte gateType;
    public int ctrl;
    public int target;
    public double param;
    
    public AbirQuGate(int gateType, int ctrl, int target, double param) {
        this.gateType = (byte) gateType;
        this.ctrl = ctrl;
        this.target = target;
        this.param = param;
    }
    
    public AbirQuGate(int gateType, int qubit) {
        this(gateType, qubit, 0, 0.0);
    }
    
    public static AbirQuGate h(int q) { return new AbirQuGate(AbirQuSimulator.GATE_H, q); }
    public static AbirQuGate x(int q) { return new AbirQuGate(AbirQuSimulator.GATE_X, q); }
    public static AbirQuGate y(int q) { return new AbirQuGate(AbirQuSimulator.GATE_Y, q); }
    public static AbirQuGate z(int q) { return new AbirQuGate(AbirQuSimulator.GATE_Z, q); }
    public static AbirQuGate cnot(int ctrl, int tgt) { 
        return new AbirQuGate(AbirQuSimulator.GATE_CNOT, ctrl, tgt, 0.0); 
    }
    public static AbirQuGate rx(int q, double angle) { 
        return new AbirQuGate(AbirQuSimulator.GATE_RX, q, q, angle); 
    }
    public static AbirQuGate ry(int q, double angle) { 
        return new AbirQuGate(AbirQuSimulator.GATE_RY, q, q, angle); 
    }
    public static AbirQuGate rz(int q, double angle) { 
        return new AbirQuGate(AbirQuSimulator.GATE_RZ, q, q, angle); 
    }
}
