package com.abirqu;

/**
 * Gate descriptor for batch circuit execution
 * Mirrors the C AbirQuGate struct
 */
import com.sun.jna.Structure;
import java.util.Arrays;
import java.util.List;

/**
 * Gate descriptor for batch circuit execution
 * Mirrors the C AbirQuGate struct
 */
@Structure.FieldOrder({"gateType", "pad0", "pad1", "pad2", "ctrl", "target", "param"})
public class AbirQuGate extends Structure {
    public byte gateType;
    public byte pad0;
    public byte pad1;
    public byte pad2;
    public int ctrl;
    public int target;
    public double param;
    
    public AbirQuGate() {}
    
    public AbirQuGate(int gateType, int ctrl, int target, double param) {
        this.gateType = (byte) gateType;
        this.ctrl = ctrl;
        this.target = target;
        this.param = param;
    }
    
    public AbirQuGate(int gateType, int qubit) {
        this(gateType, qubit, 0, 0.0);
    }
    
    public static class ByReference extends AbirQuGate implements Structure.ByReference {}
    public static class ByValue extends AbirQuGate implements Structure.ByValue {}
    
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

