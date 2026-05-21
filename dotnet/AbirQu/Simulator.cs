// AbirQu C# P/Invoke Wrapper
using System;
using System.Runtime.InteropServices;

namespace AbirQu
{
    /// <summary>
    /// Quantum Simulator using P/Invoke to call libabirqu_core.so
    /// </summary>
    public class Simulator : IDisposable
    {
        // Opaque handle type
        private IntPtr nativeHandle = IntPtr.Zero;

        // Gate constants
        public const byte GATE_H = 0;
        public const byte GATE_X = 1;
        public const byte GATE_Y = 2;
        public const byte GATE_Z = 3;
        public const byte GATE_S = 4;
        public const byte GATE_T = 5;
        public const byte GATE_CNOT = 6;
        public const byte GATE_CZ = 7;
        public const byte GATE_RX = 8;
        public const byte GATE_RY = 9;
        public const byte GATE_RZ = 10;
        public const byte GATE_SWAP = 11;

        // Native method imports
        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern IntPtr abirqu_simulator_create(uint numQubits);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_simulator_destroy(IntPtr handle);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_simulator_reset(IntPtr handle);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern uint abirqu_num_qubits(IntPtr handle);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern UIntPtr abirqu_hilbert_dim(IntPtr handle);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_h(IntPtr handle, uint q);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_x(IntPtr handle, uint q);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_y(IntPtr handle, uint q);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_z(IntPtr handle, uint q);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_s(IntPtr handle, uint q);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_t(IntPtr handle, uint q);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_rx(IntPtr handle, uint q, double angle);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_ry(IntPtr handle, uint q, double angle);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_rz(IntPtr handle, uint q, double angle);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_cnot(IntPtr handle, uint ctrl, uint tgt);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_cz(IntPtr handle, uint ctrl, uint tgt);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_swap(IntPtr handle, uint q0, uint q1);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern UIntPtr abirqu_get_probabilities(IntPtr handle, [MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 2)] double[] outProbs);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern UIntPtr abirqu_get_statevector(IntPtr handle, [MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 2)] double[] outRe, [MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 3)] double[] outIm);

        [DllImport("abirqu_core", CallingConvention = CallingConvention.Cdecl)]
        private static extern void abirqu_run_circuit(IntPtr handle, [In] AbirQuGate[] gates, UIntPtr nGates);

        /// <summary>
        /// Create a new simulator for numQubits qubits
        /// </summary>
        public Simulator(uint numQubits)
        {
            nativeHandle = abirqu_simulator_create(numQubits);
            if (nativeHandle == IntPtr.Zero)
            {
                throw new InvalidOperationException("Failed to create simulator");
            }
        }

        /// <summary>
        /// Get number of qubits
        /// </summary>
        public uint NumQubits => abirqu_num_qubits(nativeHandle);

        /// <summary>
        /// Get Hilbert space dimension (2^numQubits)
        /// </summary>
        public ulong HilbertDim => abirqu_hilbert_dim(nativeHandle).ToUInt64();

        // Gate operations
        public void H(uint q) => abirqu_h(nativeHandle, q);
        public void X(uint q) => abirqu_x(nativeHandle, q);
        public void Y(uint q) => abirqu_y(nativeHandle, q);
        public void Z(uint q) => abirqu_z(nativeHandle, q);
        public void S(uint q) => abirqu_s(nativeHandle, q);
        public void T(uint q) => abirqu_t(nativeHandle, q);
        public void RX(uint q, double angle) => abirqu_rx(nativeHandle, q, angle);
        public void RY(uint q, double angle) => abirqu_ry(nativeHandle, q, angle);
        public void RZ(uint q, double angle) => abirqu_rz(nativeHandle, q, angle);
        public void CNOT(uint ctrl, uint target) => abirqu_cnot(nativeHandle, ctrl, target);
        public void CZ(uint ctrl, uint target) => abirqu_cz(nativeHandle, ctrl, target);
        public void SWAP(uint q0, uint q1) => abirqu_swap(nativeHandle, q0, q1);

        /// <summary>
        /// Execute a sequence of gates in a batch
        /// </summary>
        public void RunCircuit(AbirQuGate[] gates)
        {
            if (gates == null) throw new ArgumentNullException(nameof(gates));
            if (gates.Length == 0) return;
            abirqu_run_circuit(nativeHandle, gates, (UIntPtr)gates.Length);
        }

        /// <summary>
        /// Get measurement probabilities
        /// </summary>
        public double[] GetProbabilities()
        {
            ulong dim = HilbertDim;
            double[] probs = new double[dim];
            abirqu_get_probabilities(nativeHandle, probs);
            return probs;
        }

        /// <summary>
        /// Get state vector as interleaved [re0, im0, re1, im1, ...]
        /// </summary>
        public double[] GetStatevector()
        {
            ulong dim = HilbertDim;
            double[] re = new double[dim];
            double[] im = new double[dim];
            abirqu_get_statevector(nativeHandle, re, im);
            
            double[] state = new double[dim * 2];
            for (int i = 0; i < (int)dim; i++)
            {
                state[i * 2] = re[i];
                state[i * 2 + 1] = im[i];
            }
            return state;
        }

        /// <summary>
        /// Create Bell state |00> + |11>
        /// </summary>
        public static Simulator CreateBellState()
        {
            var sim = new Simulator(2);
            sim.H(0);
            sim.CNOT(0, 1);
            return sim;
        }

        /// <summary>
        /// Reset simulator to |0...0>
        /// </summary>
        public void Reset() => abirqu_simulator_reset(nativeHandle);

        /// <summary>
        /// Dispose and free native resources
        /// </summary>
        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (nativeHandle != IntPtr.Zero)
            {
                abirqu_simulator_destroy(nativeHandle);
                nativeHandle = IntPtr.Zero;
            }
        }

        ~Simulator()
        {
            Dispose(false);
        }
    }
}
