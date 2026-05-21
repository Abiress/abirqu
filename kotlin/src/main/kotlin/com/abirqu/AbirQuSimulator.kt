package com.abirqu

import com.sun.jna.Native
import com.sun.jna.Pointer

/**
 * AbirQu Kotlin JNA Wrapper
 * Similar to Java wrapper but with Kotlin syntax
 */
class AbirQuSimulator(numQubits: Int) {
    // Load native library using JNA
    private object Lib {
        init {
            Native.register("abirqu_core")
        }
        
        @JvmStatic external fun abirqu_simulator_create(numQubits: Int): Pointer?
        @JvmStatic external fun abirqu_simulator_destroy(handle: Pointer?)
        @JvmStatic external fun abirqu_simulator_reset(handle: Pointer?)
        
        @JvmStatic external fun abirqu_num_qubits(handle: Pointer?): Int
        @JvmStatic external fun abirqu_hilbert_dim(handle: Pointer?): Long
        
        @JvmStatic external fun abirqu_h(handle: Pointer?, q: Int)
        @JvmStatic external fun abirqu_x(handle: Pointer?, q: Int)
        @JvmStatic external fun abirqu_y(handle: Pointer?, q: Int)
        @JvmStatic external fun abirqu_z(handle: Pointer?, q: Int)
        @JvmStatic external fun abirqu_s(handle: Pointer?, q: Int)
        @JvmStatic external fun abirqu_t(handle: Pointer?, q: Int)
        @JvmStatic external fun abirqu_rx(handle: Pointer?, q: Int, angle: Double)
        @JvmStatic external fun abirqu_ry(handle: Pointer?, q: Int, angle: Double)
        @JvmStatic external fun abirqu_rz(handle: Pointer?, q: Int, angle: Double)
        @JvmStatic external fun abirqu_cnot(handle: Pointer?, ctrl: Int, target: Int)
        @JvmStatic external fun abirqu_cz(handle: Pointer?, ctrl: Int, target: Int)
        @JvmStatic external fun abirqu_swap(handle: Pointer?, q0: Int, q1: Int)
        
        @JvmStatic external fun abirqu_get_probabilities(handle: Pointer?, outProbs: DoubleArray): Long
        @JvmStatic external fun abirqu_get_statevector(handle: Pointer?, outRe: DoubleArray, outIm: DoubleArray): Long
        @JvmStatic external fun abirqu_run_circuit(handle: Pointer?, gates: Array<AbirQuGate>, nGates: Long)
    }

    
    private var nativeHandle: Pointer? = Lib.abirqu_simulator_create(numQubits)
    
    init {
        if (nativeHandle == null) {
            throw RuntimeException("Failed to create simulator")
        }
    }
    
    val numQubits: Int get() = Lib.abirqu_num_qubits(nativeHandle)
    val hilbertDim: Long get() = Lib.abirqu_hilbert_dim(nativeHandle)
    
    // Gate operations
    fun h(q: Int) = Lib.abirqu_h(nativeHandle, q)
    fun x(q: Int) = Lib.abirqu_x(nativeHandle, q)
    fun y(q: Int) = Lib.abirqu_y(nativeHandle, q)
    fun z(q: Int) = Lib.abirqu_z(nativeHandle, q)
    fun s(q: Int) = Lib.abirqu_s(nativeHandle, q)
    fun t(q: Int) = Lib.abirqu_t(nativeHandle, q)
    fun rx(q: Int, angle: Double) = Lib.abirqu_rx(nativeHandle, q, angle)
    fun ry(q: Int, angle: Double) = Lib.abirqu_ry(nativeHandle, q, angle)
    fun rz(q: Int, angle: Double) = Lib.abirqu_rz(nativeHandle, q, angle)
    fun cnot(ctrl: Int, target: Int) = Lib.abirqu_cnot(nativeHandle, ctrl, target)
    fun cz(ctrl: Int, target: Int) = Lib.abirqu_cz(nativeHandle, ctrl, target)
    fun swap(q0: Int, q1: Int) = Lib.abirqu_swap(nativeHandle, q0, q1)
    
    fun runCircuit(gates: Array<AbirQuGate>) {
        if (gates.isEmpty()) return
        @Suppress("UNCHECKED_CAST")
        val contiguousGates = AbirQuGate().toArray(gates.size) as Array<AbirQuGate>
        for (i in gates.indices) {
            contiguousGates[i].gateType = gates[i].gateType
            contiguousGates[i].pad0 = gates[i].pad0
            contiguousGates[i].pad1 = gates[i].pad1
            contiguousGates[i].pad2 = gates[i].pad2
            contiguousGates[i].ctrl = gates[i].ctrl
            contiguousGates[i].target = gates[i].target
            contiguousGates[i].param = gates[i].param
        }
        for (g in contiguousGates) {
            g.write()
        }
        Lib.abirqu_run_circuit(nativeHandle, contiguousGates, gates.size.toLong())
    }
    
    fun getProbabilities(): DoubleArray {

        val dim = hilbertDim.toInt()
        val probs = DoubleArray(dim)
        Lib.abirqu_get_probabilities(nativeHandle, probs)
        return probs
    }
    
    fun getStatevector(): DoubleArray {
        val dim = hilbertDim.toInt()
        val re = DoubleArray(dim)
        val im = DoubleArray(dim)
        Lib.abirqu_get_statevector(nativeHandle, re, im)
        
        val state = DoubleArray(dim * 2)
        for (i in 0 until dim) {
            state[i * 2] = re[i]
            state[i * 2 + 1] = im[i]
        }
        return state
    }
    
    fun reset() = Lib.abirqu_simulator_reset(nativeHandle)
    
    fun close() {
        if (nativeHandle != null) {
            Lib.abirqu_simulator_destroy(nativeHandle)
            nativeHandle = null
        }
    }
    
    @Suppress("deprecation")
    protected fun finalize() {
        close()
    }
    
    companion object {
        // Gate constants
        const val GATE_H = 0
        const val GATE_X = 1
        const val GATE_Y = 2
        const val GATE_Z = 3
        const val GATE_S = 4
        const val GATE_T = 5
        const val GATE_CNOT = 6
        const val GATE_CZ = 7
        const val GATE_RX = 8
        const val GATE_RY = 9
        const val GATE_RZ = 10
        const val GATE_SWAP = 11
        
        fun createBellState(): AbirQuSimulator {
            val sim = AbirQuSimulator(2)
            sim.h(0)
            sim.cnot(0, 1)
            return sim
        }
    }
}
