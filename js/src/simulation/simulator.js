/**
 * Quantum state vector simulator in JavaScript
 * Full state vector simulation for quantum circuits
 */

import { Complex } from 'complex.js';
import QuantumCircuit from '../circuits/circuit.js';
import ComplexMath from '../complex-math.js';

export class QuantumSimulator {
    constructor() {
        this.backend = 'cpu';
        this.precision = 'double';
    }

    /**
     * Simulate circuit and return state vector
     * @param {QuantumCircuit} circuit
     * @returns {Object}
     */
    simulate(circuit) {
        const startTime = performance.now();
        const stateVector = circuit.simulate();
        const endTime = performance.now();
        
        return {
            stateVector: stateVector,
            probabilities: circuit.getProbabilities(),
            numQubits: circuit.numQubits,
            time: endTime - startTime,
            backend: this.backend
        };
    }

    /**
     * Run multiple shots and get measurement counts
     * @param {QuantumCircuit} circuit
     * @param {number} shots
     * @returns {Object}
     */
    runShots(circuit, shots = 1024) {
        const counts = {};
        
        for (let i = 0; i < shots; i++) {
            const tempCircuit = this.cloneCircuit(circuit);
            const result = tempCircuit.simulate();
            const measurement = this.measureAll(tempCircuit);
            const key = measurement.join('');
            
            counts[key] = (counts[key] || 0) + 1;
        }
        
        return {
            counts,
            shots,
            probabilities: this.getTheoreticalProbabilities(circuit)
        };
    }

    /**
     * Clone a circuit for repeated simulation
     * @param {QuantumCircuit} circuit
     * @returns {QuantumCircuit}
     */
    cloneCircuit(circuit) {
        const newCircuit = new QuantumCircuit(circuit.numQubits);
        newCircuit.gates = [...circuit.gates];
        return newCircuit;
    }

    /**
     * Measure all qubits
     * @param {QuantumCircuit} circuit
     * @returns {number[]}
     */
    measureAll(circuit) {
        const result = [];
        for (let i = 0; i < circuit.numQubits; i++) {
            result.push(circuit.measure(i));
        }
        return result;
    }

    /**
     * Get theoretical probabilities (no measurement collapse)
     * @param {QuantumCircuit} circuit
     * @returns {number[]}
     */
    getTheoreticalProbabilities(circuit) {
        const tempCircuit = this.cloneCircuit(circuit);
        tempCircuit.simulate();
        return tempCircuit.getProbabilities();
    }

    /**
     * Expectation value of Pauli operator
     * @param {QuantumCircuit} circuit
     * @param {string} pauli - Pauli operator string (e.g., 'XZ')
     * @param {number[]} qubits
     * @returns {number}
     */
    expectationValue(circuit, pauli, qubits) {
        const state = circuit.simulate();
        const stateVector = state.stateVector;
        let expectation = 0;
        
        for (let i = 0; i < stateVector.length; i++) {
            let amplitude = stateVector[i];
            for (let q = 0; q < qubits.length; q++) {
                const bit = (i >> qubits[q]) & 1;
                if (pauli[q] === 'Z' && bit === 1) {
                    expectation -= amplitude.abs() ** 2;
                } else if (pauli[q] === 'X') {
                    const neighbor = i ^ (1 << qubits[q]);
                    if (neighbor < stateVector.length) {
                        expectation += 2 * (amplitude.re * stateVector[neighbor].re + amplitude.im * stateVector[neighbor].im);
                    }
                }
            }
        }
        
        return expectation;
    }

    /**
     * VQE simulation
     * @param {Function} ansatz - Circuit builder function
     * @param {number[]} params - Ansatz parameters
     * @param {Function} hamiltonian - Hamiltonian function
     * @returns {number}
     */
    vqe(ansatz, params, hamiltonian) {
        const circuit = ansatz(params);
        const energy = hamiltonian(circuit, this);
        return energy;
    }

    /**
     * Create Bell state
     * @returns {QuantumCircuit}
     */
    static createBellState() {
        const circuit = new QuantumCircuit(2);
        circuit.h(0);
        circuit.cnot(0, 1);
        return circuit;
    }

    /**
     * Create GHZ state
     * @param {number} numQubits
     * @returns {QuantumCircuit}
     */
    static createGHZState(numQubits) {
        const circuit = new QuantumCircuit(numQubits);
        circuit.h(0);
        for (let i = 0; i < numQubits - 1; i++) {
            circuit.cnot(i, i + 1);
        }
        return circuit;
    }
}

export default QuantumSimulator;
