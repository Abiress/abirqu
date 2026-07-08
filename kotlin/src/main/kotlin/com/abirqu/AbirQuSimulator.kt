package com.abirqu

import com.sun.jna.Native
import com.sun.jna.Pointer

/**
 * AbirQu Kotlin JNA Wrapper
 * Similar to Java wrapper but with Kotlin syntax
 */
class AbirQuSimulator(numQubits: Int) {
    // Load native library using JNA (standard Library interface pattern)
    private interface Lib : com.sun.jna.Library {
        companion object {
            val INSTANCE: Lib = Native.load("abirqu_core", Lib::class.java)
        }

        fun abirqu_simulator_create(numQubits: Int): Pointer?
        fun abirqu_simulator_destroy(handle: Pointer?)
        fun abirqu_simulator_reset(handle: Pointer?)

        fun abirqu_num_qubits(handle: Pointer?): Int
        fun abirqu_hilbert_dim(handle: Pointer?): Long

        fun abirqu_h(handle: Pointer?, q: Int)
        fun abirqu_x(handle: Pointer?, q: Int)
        fun abirqu_y(handle: Pointer?, q: Int)
        fun abirqu_z(handle: Pointer?, q: Int)
        fun abirqu_s(handle: Pointer?, q: Int)
        fun abirqu_t(handle: Pointer?, q: Int)
        fun abirqu_rx(handle: Pointer?, q: Int, angle: Double)
        fun abirqu_ry(handle: Pointer?, q: Int, angle: Double)
        fun abirqu_rz(handle: Pointer?, q: Int, angle: Double)
        fun abirqu_cnot(handle: Pointer?, ctrl: Int, target: Int)
        fun abirqu_cz(handle: Pointer?, ctrl: Int, target: Int)
        fun abirqu_swap(handle: Pointer?, q0: Int, q1: Int)

        fun abirqu_get_probabilities(handle: Pointer?, outProbs: DoubleArray): Long
        fun abirqu_get_statevector(handle: Pointer?, outRe: DoubleArray, outIm: DoubleArray): Long
    }

    
    private var nativeHandle: Pointer? = Lib.INSTANCE.abirqu_simulator_create(numQubits)
    
    init {
        if (nativeHandle == null) {
            throw RuntimeException("Failed to create simulator")
        }
    }
    
    val numQubits: Int get() = Lib.INSTANCE.abirqu_num_qubits(nativeHandle)
    val hilbertDim: Long get() = Lib.INSTANCE.abirqu_hilbert_dim(nativeHandle)
    
    // Gate operations
    fun h(q: Int) = Lib.INSTANCE.abirqu_h(nativeHandle, q)
    fun x(q: Int) = Lib.INSTANCE.abirqu_x(nativeHandle, q)
    fun y(q: Int) = Lib.INSTANCE.abirqu_y(nativeHandle, q)
    fun z(q: Int) = Lib.INSTANCE.abirqu_z(nativeHandle, q)
    fun s(q: Int) = Lib.INSTANCE.abirqu_s(nativeHandle, q)
    fun t(q: Int) = Lib.INSTANCE.abirqu_t(nativeHandle, q)
    fun rx(q: Int, angle: Double) = Lib.INSTANCE.abirqu_rx(nativeHandle, q, angle)
    fun ry(q: Int, angle: Double) = Lib.INSTANCE.abirqu_ry(nativeHandle, q, angle)
    fun rz(q: Int, angle: Double) = Lib.INSTANCE.abirqu_rz(nativeHandle, q, angle)
    fun cnot(ctrl: Int, target: Int) = Lib.INSTANCE.abirqu_cnot(nativeHandle, ctrl, target)
    fun cz(ctrl: Int, target: Int) = Lib.INSTANCE.abirqu_cz(nativeHandle, ctrl, target)
    fun swap(q0: Int, q1: Int) = Lib.INSTANCE.abirqu_swap(nativeHandle, q0, q1)
    
    fun runCircuit(gates: Array<AbirQuGate>) {
        if (gates.isEmpty()) return
        for (g in gates) {
            when (g.gateType.toInt()) {
                GATE_H -> h(g.target)
                GATE_X -> x(g.target)
                GATE_Y -> y(g.target)
                GATE_Z -> z(g.target)
                GATE_S -> s(g.target)
                GATE_T -> t(g.target)
                GATE_RX -> rx(g.target, g.param)
                GATE_RY -> ry(g.target, g.param)
                GATE_RZ -> rz(g.target, g.param)
                GATE_CNOT -> cnot(g.ctrl, g.target)
                GATE_CZ -> cz(g.ctrl, g.target)
                GATE_SWAP -> swap(g.ctrl, g.target)
                else -> { /* unknown gate ignored */ }
            }
        }
    }
    
    fun getProbabilities(): DoubleArray {

        val dim = hilbertDim.toInt()
        val probs = DoubleArray(dim)
        Lib.INSTANCE.abirqu_get_probabilities(nativeHandle, probs)
        return probs
    }
    
    fun getStatevector(): DoubleArray {
        val dim = hilbertDim.toInt()
        val re = DoubleArray(dim)
        val im = DoubleArray(dim)
        Lib.INSTANCE.abirqu_get_statevector(nativeHandle, re, im)
        
        val state = DoubleArray(dim * 2)
        for (i in 0 until dim) {
            state[i * 2] = re[i]
            state[i * 2 + 1] = im[i]
        }
        return state
    }
    
    fun reset() = Lib.INSTANCE.abirqu_simulator_reset(nativeHandle)
    
    fun close() {
        if (nativeHandle != null) {
            Lib.INSTANCE.abirqu_simulator_destroy(nativeHandle)
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
