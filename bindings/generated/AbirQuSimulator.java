/* Auto-generated AbirQu Java JNI wrapper — do not edit manually. */
package com.abirqu;

public class AbirQuSimulator {
    private long handle;

    static {
        System.loadLibrary("abirqu_core");
    }

    public AbirQuSimulator(int numQubits) {
        this.handle = nativeCreate(numQubits);
    }

    @Override
    protected void finalize() throws Throwable {
        if (handle != 0) {
            nativeDestroy(handle);
        }
        super.finalize();
    }

    // Create a new simulator for `num_qubits` qubits.
    // Returns a non-null opaque handle.  Must be freed with
    // `abirqu_simulator_destroy`.
    public long simulator_create(long U32) {
        return nativesimulator_create(handle, U32);
    }

    private native jlong nativesimulator_create(long handle, jlong);

    // Free a handle created by `abirqu_simulator_create`.  Passing NULL is safe.
    public void simulator_destroy(long AbirQuSimulator) {
        nativesimulator_destroy(handle, AbirQuSimulator);
    }

    private native void nativesimulator_destroy(long handle, jlong);

    // Reset the simulator to |0…0⟩ without reallocating.
    public void simulator_reset(long AbirQuSimulator) {
        nativesimulator_reset(handle, AbirQuSimulator);
    }

    private native void nativesimulator_reset(long handle, jlong);

    // Return the number of qubits this simulator was created with.
    public int num_qubits(long AbirQuSimulator) {
        return nativenum_qubits(handle, AbirQuSimulator);
    }

    private native jint nativenum_qubits(long handle, jlong);

    // Return the Hilbert space dimension (2^num_qubits).
    public long hilbert_dim(long AbirQuSimulator) {
        return nativehilbert_dim(handle, AbirQuSimulator);
    }

    private native jlong nativehilbert_dim(long handle, jlong);

    public void h(long AbirQuSimulator, long U32) {
        nativeh(handle, AbirQuSimulator, U32);
    }

    private native void nativeh(long handle, jlong, jlong);

    public void x(long AbirQuSimulator, long U32) {
        nativex(handle, AbirQuSimulator, U32);
    }

    private native void nativex(long handle, jlong, jlong);

    public void y(long AbirQuSimulator, long U32) {
        nativey(handle, AbirQuSimulator, U32);
    }

    private native void nativey(long handle, jlong, jlong);

    public void z(long AbirQuSimulator, long U32) {
        nativez(handle, AbirQuSimulator, U32);
    }

    private native void nativez(long handle, jlong, jlong);

    public void s(long AbirQuSimulator, long U32) {
        natives(handle, AbirQuSimulator, U32);
    }

    private native void natives(long handle, jlong, jlong);

    public void t(long AbirQuSimulator, long U32) {
        nativet(handle, AbirQuSimulator, U32);
    }

    private native void nativet(long handle, jlong, jlong);

    public void rx(long AbirQuSimulator, long U32, long F64) {
        nativerx(handle, AbirQuSimulator, U32, F64);
    }

    private native void nativerx(long handle, jlong, jlong, jlong);

    public void ry(long AbirQuSimulator, long U32, long F64) {
        nativery(handle, AbirQuSimulator, U32, F64);
    }

    private native void nativery(long handle, jlong, jlong, jlong);

    public void rz(long AbirQuSimulator, long U32, long F64) {
        nativerz(handle, AbirQuSimulator, U32, F64);
    }

    private native void nativerz(long handle, jlong, jlong, jlong);

    public void cnot(long AbirQuSimulator, long U32, long U32) {
        nativecnot(handle, AbirQuSimulator, U32, U32);
    }

    private native void nativecnot(long handle, jlong, jlong, jlong);

    public void cz(long AbirQuSimulator, long U32, long U32) {
        nativecz(handle, AbirQuSimulator, U32, U32);
    }

    private native void nativecz(long handle, jlong, jlong, jlong);

    public void swap(long AbirQuSimulator, long U32, long U32) {
        nativeswap(handle, AbirQuSimulator, U32, U32);
    }

    private native void nativeswap(long handle, jlong, jlong, jlong);

    // Execute a batch of gates described by the `gates` array of length `n_gates`.
    // 
    // # Safety
    // `handle` must be a valid non-null pointer from `abirqu_simulator_create`.
    // `gates`  must point to at least `n_gates` consecutive `AbirQuGate` values.
    public void run_circuit(long AbirQuSimulator, long *const AbirQuGate, long Usize) {
        nativerun_circuit(handle, AbirQuSimulator, *const AbirQuGate, Usize);
    }

    private native void nativerun_circuit(long handle, jlong, jlong, jlong);

    // Copy measurement probabilities into caller-supplied buffer `out_probs`.
    // 
    // `out_probs` must have room for at least `abirqu_hilbert_dim(handle)` doubles.
    // Returns the number of values written, or 0 on error.
    public long get_probabilities(long AbirQuSimulator, long *mut f64) {
        return nativeget_probabilities(handle, AbirQuSimulator, *mut f64);
    }

    private native jlong nativeget_probabilities(long handle, jlong, jlong);

    // Copy the statevector into caller-supplied buffers `out_re` and `out_im`.
    // 
    // Both buffers must have room for at least `abirqu_hilbert_dim(handle)` doubles.
    // Returns the number of complex amplitudes written, or 0 on error.
    public long get_statevector(long AbirQuSimulator, long *mut f64, long *mut f64) {
        return nativeget_statevector(handle, AbirQuSimulator, *mut f64, *mut f64);
    }

    private native jlong nativeget_statevector(long handle, jlong, jlong, jlong);

}
