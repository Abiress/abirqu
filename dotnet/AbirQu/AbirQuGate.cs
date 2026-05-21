using System;
using System.Runtime.InteropServices;

namespace AbirQu
{
    /// <summary>
    /// Gate descriptor for batch circuit execution.
    /// Mirrors the C AbirQuGate struct.
    /// </summary>
    [StructLayout(LayoutKind.Sequential, Pack = 8)]
    public struct AbirQuGate
    {
        public byte GateType;
        public byte Pad0;
        public byte Pad1;
        public byte Pad2;
        public uint Ctrl;
        public uint Target;
        public double Param;

        public AbirQuGate(byte gateType, uint ctrl, uint target, double param)
        {
            GateType = gateType;
            Pad0 = 0;
            Pad1 = 0;
            Pad2 = 0;
            Ctrl = ctrl;
            Target = target;
            Param = param;
        }

        public AbirQuGate(byte gateType, uint qubit) : this(gateType, qubit, 0, 0.0)
        {
        }

        public static AbirQuGate H(uint q) => new AbirQuGate(Simulator.GATE_H, q);
        public static AbirQuGate X(uint q) => new AbirQuGate(Simulator.GATE_X, q);
        public static AbirQuGate Y(uint q) => new AbirQuGate(Simulator.GATE_Y, q);
        public static AbirQuGate Z(uint q) => new AbirQuGate(Simulator.GATE_Z, q);
        public static AbirQuGate CNOT(uint ctrl, uint tgt) => new AbirQuGate(Simulator.GATE_CNOT, ctrl, tgt, 0.0);
        public static AbirQuGate RX(uint q, double angle) => new AbirQuGate(Simulator.GATE_RX, q, q, angle);
        public static AbirQuGate RY(uint q, double angle) => new AbirQuGate(Simulator.GATE_RY, q, q, angle);
        public static AbirQuGate RZ(uint q, double angle) => new AbirQuGate(Simulator.GATE_RZ, q, q, angle);
    }
}
