package com.abirqu

/**
 * AbirQu Kotlin JNA Wrapper
 * Similar to Java wrapper but with Kotlin syntax
 */
class AbirQuSimulator(numQubits: Int) {
    // Load native library
    companion object {
        init {
            System.loadLibrary("abirqu_core")
        }
        
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
    }
    
    // Native methods
    private external fun nativeCreate(numQubits: Int): Long
    private external fun nativeDestroy(handle: Long)
    private external fun nativeReset(handle: Long)
    private external fun nativeNumQubits(handle: Long): Int
    private external fun nativeHilbertDim(handle: Long): Long
    private external fun nativeH(handle: Long, q: Int)
    private external fun nativeX(handle: Long, q: Int)
    private external fun nativeY(handle: Long, q: Int)
    private external fun nativeZ(handle: Long, q: Int)
    private external fun nativeS(handle: Long, q: Int)
    private external fun nativeT(handle: Long, q: Int)
    private external fun nativeRX(handle: Long, q: Int, angle: Double)
    private external fun nativeRY(handle: Long, q: Int, angle: Double)
    private external fun nativeRZ(handle: Long, q: Int, angle: Double)
    private external fun nativeCNOT(handle: Long, ctrl: Int, target: Int)
    private external fun nativeCZ(handle: Long, ctrl: Int, target: Int)
    private external fun nativeSWAP(handle: Long, q0: Int, q1: Int)
    private external fun nativeGetProbabilities(handle: Long, outProbs: DoubleArray): Long
    private external fun nativeGetStatevector(handle: Long, outRe: DoubleArray, outIm: DoubleArray): Long
    
    private val nativeHandle: Long = nativeCreate(numQubits)
    
    init {
        if (nativeHandle == 0L) {
            throw RuntimeException("Failed to create simulator")
        }
    }
    
    val numQubits: Int get() = nativeNumQubits(nativeHandle)
    val hilbertDim: Long get() = nativeHilbertDim(nativeHandle)
    
    // Gate operations
    fun h(q: Int) = nativeH(nativeHandle, q)
    fun x(q: Int) = nativeX(nativeHandle, q)
    fun y(q: Int) = nativeY(nativeHandle, q)
    fun z(q: Int) = nativeZ(nativeHandle, q)
    fun s(q: Int) = nativeS(nativeHandle, q)
    fun t(q: Int) = nativeT(nativeHandle, q)
    fun rx(q: Int, angle: Double) = nativeRX(nativeHandle, q, angle)
    fun ry(q: Int, angle: Double) = nativeRY(nativeHandle, q, angle)
    fun rz(q: Int, angle: Double) = nativeRZ(nativeHandle, q, angle)
    fun cnot(ctrl: Int, target: Int) = nativeCNOT(nativeHandle, ctrl, target)
    fun cz(ctrl: Int, target: Int) = nativeCZ(nativeHandle, ctrl, target)
    fun swap(q0: Int, q1: Int) = nativeSWAP(nativeHandle, q0, q1)
    
    fun getProbabilities(): DoubleArray {
        val dim = hilbertDim.toInt()
        val probs = DoubleArray(dim)
        nativeGetProbabilities(nativeHandle, probs)
        return probs
    }
    
    fun getStatevector(): DoubleArray {
        val dim = hilbertDim.toInt()
        val re = DoubleArray(dim)
        val im = DoubleArray(dim)
        nativeGetStatevector(nativeHandle, re, im)
        
        val state = DoubleArray(dim * 2)
        for (i in 0 until dim) {
            state[i * 2] = re[i]
            state[i * 2 + 1] = im[i]
        }
        return state
    }
    
    fun reset() = nativeReset(nativeHandle)
    
    fun close() {
        if (nativeHandle != 0L) {
            nativeDestroy(nativeHandle)
        }
    }
    
    companion object {
        fun createBellState(): AbirQuSimulator {
            val sim = AbirQuSimulator(2)
            sim.h(0)
            sim.cnot(0, 1)
            return sim
        }
    }
}
