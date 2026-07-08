package com.abirqu

import org.junit.jupiter.api.*
import org.junit.jupiter.api.Assertions.*

class AbirQuSimulatorTest {

    @Test
    fun testCreateSimulator() {
        val sim = AbirQuSimulator(2)
        assertEquals(2, sim.numQubits)
        assertEquals(4, sim.hilbertDim)
        sim.close()
    }

    @Test
    fun testBellState() {
        val sim = AbirQuSimulator.createBellState()
        val probs = sim.getProbabilities()

        assertTrue(kotlin.math.abs(probs[0] - 0.5) < 1e-10)
        assertTrue(kotlin.math.abs(probs[3] - 0.5) < 1e-10)
        assertTrue(probs[1] < 1e-10)
        assertTrue(probs[2] < 1e-10)
        sim.close()
    }

    @Test
    fun testSingleQubitGates() {
        val sim = AbirQuSimulator(1)
        sim.h(0)
        val probs = sim.getProbabilities()

        assertTrue(kotlin.math.abs(probs[0] - 0.5) < 1e-10)
        assertTrue(kotlin.math.abs(probs[1] - 0.5) < 1e-10)
        sim.close()
    }

    @Test
    fun testRotationGates() {
        val sim = AbirQuSimulator(1)
        sim.rx(0, kotlin.math.PI)
        val probs = sim.getProbabilities()

        assertTrue(kotlin.math.abs(probs[1] - 1.0) < 1e-10)
        sim.close()
    }

    @Test
    fun testRunCircuit() {
        val sim = AbirQuSimulator(2)
        val gates = arrayOf(
            AbirQuGate.h(0),
            AbirQuGate.cnot(0, 1)
        )
        sim.runCircuit(gates)
        val probs = sim.getProbabilities()

        assertTrue(kotlin.math.abs(probs[0] - 0.5) < 1e-10)
        assertTrue(kotlin.math.abs(probs[3] - 0.5) < 1e-10)
        assertTrue(probs[1] < 1e-10)
        assertTrue(probs[2] < 1e-10)
        sim.close()
    }
}
