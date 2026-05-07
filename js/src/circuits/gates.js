/**
 * Quantum gates implementation in JavaScript
 * All standard gates with proper unitary matrices
 */

import { Complex } from 'complex.js';
import ComplexMath from '../complex-math.js';

export class QuantumGates {
    static get I() {
        return [
            [new Complex(1, 0), new Complex(0, 0)],
            [new Complex(0, 0), new Complex(1, 0)]
        ];
    }

    static get X() {
        return [
            [new Complex(0, 0), new Complex(1, 0)],
            [new Complex(1, 0), new Complex(0, 0)]
        ];
    }

    static get Y() {
        return [
            [new Complex(0, 0), new Complex(0, -1)],
            [new Complex(0, 1), new Complex(0, 0)]
        ];
    }

    static get Z() {
        return [
            [new Complex(1, 0), new Complex(0, 0)],
            [new Complex(0, 0), new Complex(-1, 0)]
        ];
    }

    static get H() {
        const invSqrt2 = 1 / Math.sqrt(2);
        return [
            [new Complex(invSqrt2, 0), new Complex(invSqrt2, 0)],
            [new Complex(invSqrt2, 0), new Complex(-invSqrt2, 0)]
        ];
    }

    static get S() {
        return [
            [new Complex(1, 0), new Complex(0, 0)],
            [new Complex(0, 0), new Complex(0, 1)]
        ];
    }

    static get T() {
        return [
            [new Complex(1, 0), new Complex(0, 0)],
            [new Complex(0, 0), new Complex(Math.cos(Math.PI/4), Math.sin(Math.PI/4))]
        ];
    }

    /**
     * Rotation around X axis
     * @param {number} theta
     * @returns {Complex[][]}
     */
    static RX(theta) {
        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);
        return [
            [new Complex(c, 0), new Complex(0, -s)],
            [new Complex(0, -s), new Complex(c, 0)]
        ];
    }

    /**
     * Rotation around Y axis
     * @param {number} theta
     * @returns {Complex[][]}
     */
    static RY(theta) {
        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);
        return [
            [new Complex(c, 0), new Complex(-s, 0)],
            [new Complex(s, 0), new Complex(c, 0)]
        ];
    }

    /**
     * Rotation around Z axis
     * @param {number} theta
     * @returns {Complex[][]}
     */
    static RZ(theta) {
        const negHalf = -theta / 2;
        return [
            [new Complex(Math.cos(negHalf), Math.sin(negHalf)), new Complex(0, 0)],
            [new Complex(0, 0), new Complex(Math.cos(negHalf), Math.sin(-negHalf))]
        ];
    }

    /**
     * CNOT gate
     * @returns {Complex[][]}
     */
    static get CNOT() {
        const d = new Complex(0, 0);
        const o = new Complex(1, 0);
        return [
            [o, d, d, d],
            [d, o, d, d],
            [d, d, d, o],
            [d, d, o, d]
        ];
    }

    /**
     * CZ gate
     * @returns {Complex[][]}
     */
    static get CZ() {
        const d = new Complex(0, 0);
        const o = new Complex(1, 0);
        const neg = new Complex(-1, 0);
        return [
            [o, d, d, d],
            [d, o, d, d],
            [d, d, o, d],
            [d, d, d, neg]
        ];
    }

    /**
     * Toffoli (CCNOT) gate
     * @returns {Complex[][]}
     */
    static get Toffoli() {
        const size = 8;
        const matrix = Array(size).fill().map(() => Array(size).fill(new Complex(0, 0)));
        for (let i = 0; i < size; i++) {
            if (i < 6) {
                matrix[i][i] = new Complex(1, 0);
            }
        }
        matrix[6][6] = new Complex(0, 0);
        matrix[6][7] = new Complex(1, 0);
        matrix[7][6] = new Complex(1, 0);
        matrix[7][7] = new Complex(0, 0);
        return matrix;
    }

    /**
     * Apply gate to qubit state
     * @param {Complex[][]} gate - 2x2 matrix
     * @param {Complex[]} state - 2-element state vector
     * @returns {Complex[]}
     */
    static applySingleQubitGate(gate, state) {
        return [
            gate[0][0].mul(state[0]).add(gate[0][1].mul(state[1])),
            gate[1][0].mul(state[0]).add(gate[1][1].mul(state[1]))
        ];
    }

    /**
     * Get gate by name
     * @param {string} name
     * @returns {Complex[][]}
     */
    static getGate(name) {
        const gateMap = {
            'I': this.I,
            'X': this.X,
            'Y': this.Y,
            'Z': this.Z,
            'H': this.H,
            'S': this.S,
            'T': this.T,
            'CNOT': this.CNOT,
            'CZ': this.CZ,
            'Toffoli': this.Toffoli
        };
        return gateMap[name] || this.I;
    }
}

export default QuantumGates;
