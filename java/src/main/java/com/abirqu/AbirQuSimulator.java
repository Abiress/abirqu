package com.abirqu;

import com.sun.jna.*;
import com.sun.jna.ptr.PointerByReference;

/**
 * AbirQu Quantum Simulator - Java wrapper using JNA
 * 
 * Usage:
 *   AbirQuSimulator sim = new AbirQuSimulator(2);
 *   sim.h(0);
 *   sim.cnot(0, 1);
 *   double[] probs = sim.getProbabilities();
 * 
 * Before use:
 *   System.setProperty("jna.library.path", "/path/to/lib");
 *   or set LD_LIBRARY_PATH to include the directory with libabirqu_core.so
 */
public class AbirQuSimulator {
    
    // Load the native library using JNA (standard Library interface pattern)
    public interface Lib extends Library {
        Lib INSTANCE = Native.load("abirqu_core", Lib.class);

        // Lifecycle
        Pointer abirqu_simulator_create(int num_qubits);
        void abirqu_simulator_destroy(Pointer handle);
        void abirqu_simulator_reset(Pointer handle);

        // Metadata
        int abirqu_num_qubits(Pointer handle);
        long abirqu_hilbert_dim(Pointer handle);

        // Single gates
        void abirqu_h(Pointer handle, int q);
        void abirqu_x(Pointer handle, int q);
        void abirqu_y(Pointer handle, int q);
        void abirqu_z(Pointer handle, int q);
        void abirqu_s(Pointer handle, int q);
        void abirqu_t(Pointer handle, int q);
        void abirqu_rx(Pointer handle, int q, double angle);
        void abirqu_ry(Pointer handle, int q, double angle);
        void abirqu_rz(Pointer handle, int q, double angle);
        void abirqu_cnot(Pointer handle, int ctrl, int target);
        void abirqu_cz(Pointer handle, int ctrl, int target);
        void abirqu_swap(Pointer handle, int q0, int q1);

        // Batch execution
        void abirqu_run_circuit(Pointer handle, AbirQuGate[] gates, long n_gates);

        // State readout
        long abirqu_get_probabilities(Pointer handle, double[] out_probs);
        long abirqu_get_statevector(Pointer handle, double[] out_re, double[] out_im);
    }
    
    // Opaque native handle
    private Pointer nativeHandle;
    
    // Gate constants
    public static final int GATE_H = 0;
    public static final int GATE_X = 1;
    public static final int GATE_Y = 2;
    public static final int GATE_Z = 3;
    public static final int GATE_S = 4;
    public static final int GATE_T = 5;
    public static final int GATE_CNOT = 6;
    public static final int GATE_CZ = 7;
    public static final int GATE_RX = 8;
    public static final int GATE_RY = 9;
    public static final int GATE_RZ = 10;
    public static final int GATE_SWAP = 11;
    
    /**
     * Create a new simulator for numQubits qubits
     */
    public AbirQuSimulator(int numQubits) {
        nativeHandle = Lib.INSTANCE.abirqu_simulator_create(numQubits);
        if (nativeHandle == null) {
            throw new RuntimeException("Failed to create simulator");
        }
    }
    
    /**
     * Reset simulator to |0...0>
     */
    public void reset() {
        Lib.INSTANCE.abirqu_simulator_reset(nativeHandle);
    }
    
    /**
     * Get number of qubits
     */
    public int getNumQubits() {
        return Lib.INSTANCE.abirqu_num_qubits(nativeHandle);
    }
    
    /**
     * Get Hilbert space dimension (2^numQubits)
     */
    public long getHilbertDim() {
        return Lib.INSTANCE.abirqu_hilbert_dim(nativeHandle);
    }
    
    // Gate operations
    public void h(int q) { Lib.INSTANCE.abirqu_h(nativeHandle, q); }
    public void x(int q) { Lib.INSTANCE.abirqu_x(nativeHandle, q); }
    public void y(int q) { Lib.INSTANCE.abirqu_y(nativeHandle, q); }
    public void z(int q) { Lib.INSTANCE.abirqu_z(nativeHandle, q); }
    public void s(int q) { Lib.INSTANCE.abirqu_s(nativeHandle, q); }
    public void t(int q) { Lib.INSTANCE.abirqu_t(nativeHandle, q); }
    public void rx(int q, double angle) { Lib.INSTANCE.abirqu_rx(nativeHandle, q, angle); }
    public void ry(int q, double angle) { Lib.INSTANCE.abirqu_ry(nativeHandle, q, angle); }
    public void rz(int q, double angle) { Lib.INSTANCE.abirqu_rz(nativeHandle, q, angle); }
    public void cnot(int ctrl, int target) { Lib.INSTANCE.abirqu_cnot(nativeHandle, ctrl, target); }
    public void cz(int ctrl, int target) { Lib.INSTANCE.abirqu_cz(nativeHandle, ctrl, target); }
    public void swap(int q0, int q1) { Lib.INSTANCE.abirqu_swap(nativeHandle, q0, q1); }
    
    /**
     * Execute a batch of gates
     */
    public void runCircuit(AbirQuGate[] gates) {
        if (gates == null || gates.length == 0) return;
        AbirQuGate[] contiguousGates = (AbirQuGate[]) new AbirQuGate().toArray(gates.length);
        for (int i = 0; i < gates.length; i++) {
            contiguousGates[i].gateType = gates[i].gateType;
            contiguousGates[i].pad0 = gates[i].pad0;
            contiguousGates[i].pad1 = gates[i].pad1;
            contiguousGates[i].pad2 = gates[i].pad2;
            contiguousGates[i].ctrl = gates[i].ctrl;
            contiguousGates[i].target = gates[i].target;
            contiguousGates[i].param = gates[i].param;
        }
        for (AbirQuGate g : contiguousGates) {
            g.write();
        }
        Lib.INSTANCE.abirqu_run_circuit(nativeHandle, contiguousGates, gates.length);
    }

    
    /**
     * Get measurement probabilities
     * @return array of probabilities for each basis state
     */
    public double[] getProbabilities() {
        long dim = getHilbertDim();
        double[] probs = new double[(int) dim];
        long n = Lib.INSTANCE.abirqu_get_probabilities(nativeHandle, probs);
        if (n != dim) {
            throw new RuntimeException("Failed to get probabilities");
        }
        return probs;
    }
    
    /**
     * Get state vector as interleaved [re0, im0, re1, im1, ...]
     */
    public double[] getStatevector() {
        long dim = getHilbertDim();
        double[] re = new double[(int) dim];
        double[] im = new double[(int) dim];
        long n = Lib.INSTANCE.abirqu_get_statevector(nativeHandle, re, im);
        if (n != dim) {
            throw new RuntimeException("Failed to get state vector");
        }
        double[] state = new double[(int) (dim * 2)];
        for (int i = 0; i < dim; i++) {
            state[i * 2] = re[i];
            state[i * 2 + 1] = im[i];
        }
        return state;
    }
    
    /**
     * Create Bell state |00> + |11>
     */
    public static AbirQuSimulator createBellState() {
        AbirQuSimulator sim = new AbirQuSimulator(2);
        sim.h(0);
        sim.cnot(0, 1);
        return sim;
    }
    
    /**
     * Clean up native resources
     */
    public void close() {
        if (nativeHandle != null) {
            Lib.INSTANCE.abirqu_simulator_destroy(nativeHandle);
            nativeHandle = null;
        }
    }
    
    @Override
    protected void finalize() throws Throwable {
        try {
            close();
        } finally {
            super.finalize();
        }
    }
}
