/**
 * Quantum circuit representation in JavaScript
 * Build and simulate quantum circuits
 */

import { Complex } from 'complex.js';
import QuantumGates from './gates.js';
import ComplexMath from '../complex-math.js';

export class QuantumCircuit {
    constructor(numQubits) {
        this.numQubits = numQubits;
        this.gates = [];
        this.measuredBits = new Map();
        this.stateVector = null;
    }

    /**
     * Add a gate to the circuit
     * @param {string} gateName
     * @param {number[]} qubits
     * @param {Object} [params]
     */
    addGate(gateName, qubits, params = {}) {
        this.gates.push({ gateName, qubits, params });
        return this;
    }

    /**
     * Add X gate
     * @param {number} qubit
     */
    x(qubit) {
        return this.addGate('X', [qubit]);
    }

    /**
     * Add Y gate
     * @param {number} qubit
     */
    y(qubit) {
        return this.addGate('Y', [qubit]);
    }

    /**
     * Add Z gate
     * @param {number} qubit
     */
    z(qubit) {
        return this.addGate('Z', [qubit]);
    }

    /**
     * Add H gate
     * @param {number} qubit
     */
    h(qubit) {
        return this.addGate('H', [qubit]);
    }

    /**
     * Add rotation gates
     * @param {number} qubit
     * @param {number} theta
     */
    rx(qubit, theta) {
        return this.addGate('RX', [qubit], { theta });
    }

    ry(qubit, theta) {
        return this.addGate('RY', [qubit], { theta });
    }

    rz(qubit, theta) {
        return this.addGate('RZ', [qubit], { theta });
    }

    /**
     * Add two-qubit gates
     * @param {number} control
     * @param {number} target
     */
    cnot(control, target) {
        return this.addGate('CNOT', [control, target]);
    }

    cz(control, target) {
        return this.addGate('CZ', [control, target]);
    }

    /**
     * Initialize state vector
     * @returns {Complex[]}
     */
    initializeState() {
        const stateSize = 1 << this.numQubits;
        const state = Array(stateSize).fill(new Complex(0, 0));
        state[0] = new Complex(1, 0);
        this.stateVector = state;
        return state;
    }

    /**
     * Apply single qubit gate to state vector
     * @param {Complex[][]} gate
     * @param {number} qubit
     */
    applySingleQubit(gate, qubit) {
        const state = this.stateVector;
        const newState = Array(state.length).fill(new Complex(0, 0));
        
        for (let i = 0; i < state.length; i++) {
            const bit = (i >> qubit) & 1;
            const otherBits = i & ~(1 << qubit);
            
            if (bit === 0) {
                newState[i] = newState[i].add(gate[0][0].mul(state[i]));
                newState[i | (1 << qubit)] = newState[i | (1 << qubit)].add(gate[0][1].mul(state[i]));
            } else {
                newState[i & ~(1 << qubit)] = newState[i & ~(1 << qubit)].add(gate[1][0].mul(state[i]));
                newState[i] = newState[i].add(gate[1][1].mul(state[i]));
            }
        }
        
        this.stateVector = newState;
    }

    /**
     * Apply CNOT gate
     * @param {number} control
     * @param {number} target
     */
    applyCNOT(control, target) {
        const state = this.stateVector;
        const newState = [...state];
        
        for (let i = 0; i < state.length; i++) {
            const controlBit = (i >> control) & 1;
            if (controlBit === 1) {
                const targetFlipped = i ^ (1 << target);
                newState[targetFlipped] = state[i];
                newState[i] = state[targetFlipped];
            }
        }
        
        this.stateVector = newState;
    }

    /**
     * Simulate the circuit
     * @returns {Complex[]}
     */
    simulate() {
        this.initializeState();
        
        for (const gateOp of this.gates) {
            const { gateName, qubits, params } = gateOp;
            
            if (['X', 'Y', 'Z', 'H', 'S', 'T'].includes(gateName)) {
                const gate = QuantumGates.getGate(gateName);
                this.applySingleQubit(gate, qubits[0]);
            } else if (gateName === 'RX') {
                const gate = QuantumGates.RX(params.theta);
                this.applySingleQubit(gate, qubits[0]);
            } else if (gateName === 'RY') {
                const gate = QuantumGates.RY(params.theta);
                this.applySingleQubit(gate, qubits[0]);
            } else if (gateName === 'RZ') {
                const gate = QuantumGates.RZ(params.theta);
                this.applySingleQubit(gate, qubits[0]);
            } else if (gateName === 'CNOT') {
                this.applyCNOT(qubits[0], qubits[1]);
            } else if (gateName === 'CZ') {
                this.applyCZ(qubits[0], qubits[1]);
            }
        }
        
        return this.stateVector;
    }

    /**
     * Apply CZ gate
     * @param {number} control
     * @param {number} target
     */
    applyCZ(control, target) {
        const state = this.stateVector;
        
        for (let i = 0; i < state.length; i++) {
            const controlBit = (i >> control) & 1;
            const targetBit = (i >> target) & 1;
            if (controlBit === 1 && targetBit === 1) {
                this.stateVector[i] = state[i].mul(new Complex(-1, 0));
            }
        }
    }

    /**
     * Measure qubit in computational basis
     * @param {number} qubit
     * @returns {number}
     */
    measure(qubit) {
        if (!this.stateVector) {
            this.simulate();
        }
        
        const probabilities = this.getProbabilities();
        let prob0 = 0;
        
        for (let i = 0; i < probabilities.length; i++) {
            if (((i >> qubit) & 1) === 0) {
                prob0 += probabilities[i];
            }
        }
        
        const result = Math.random() < prob0 ? 0 : 1;
        this.measuredBits.set(qubit, result);
        this.collapseState(qubit, result);
        return result;
    }

    /**
     * Get measurement probabilities
     * @returns {number[]}
     */
    getProbabilities() {
        if (!this.stateVector) return [];
        return this.stateVector.map(c => c.abs() ** 2);
    }

    /**
     * Collapse state after measurement
     * @param {number} qubit
     * @param {number} value
     */
    collapseState(qubit, value) {
        const newState = Array(this.stateVector.length).fill(new Complex(0, 0));
        let norm = 0;
        
        for (let i = 0; i < this.stateVector.length; i++) {
            if (((i >> qubit) & 1) === value) {
                newState[i] = this.stateVector[i];
                norm += newState[i].abs() ** 2;
            }
        }
        
        const normFactor = Math.sqrt(norm);
        if (normFactor > 0) {
            this.stateVector = newState.map(c => c.div(normFactor));
        }
    }

    /**
     * Get circuit depth
     * @returns {number}
     */
    depth() {
        return this.gates.length;
    }

    /**
     * Get circuit representation
     * @returns {Object}
     */
    toJSON() {
        return {
            numQubits: this.numQubits,
            gates: this.gates,
            depth: this.depth()
        };
    }
}

export default QuantumCircuit;
