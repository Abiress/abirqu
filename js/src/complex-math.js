/**
 * Complex number operations for quantum computing
 * Pure JavaScript implementation with mathjs fallback
 */

import { Complex } from 'complex.js';

export class ComplexMath {
    /**
     * Create complex number
     * @param {number} re - Real part
     * @param {number} im - Imaginary part
     * @returns {Complex}
     */
    static create(re, im = 0) {
        return new Complex(re, im);
    }

    /**
     * Tensor product of two complex vectors
     * @param {Complex[]} v1 - First vector
     * @param {Complex[]} v2 - Second vector
     * @returns {Complex[]}
     */
    static tensorProduct(v1, v2) {
        const result = [];
        for (const a of v1) {
            for (const b of v2) {
                result.push(a.mul(b));
            }
        }
        return result;
    }

    /**
     * Inner product of two complex vectors
     * @param {Complex[]} v1
     * @param {Complex[]} v2
     * @returns {Complex}
     */
    static innerProduct(v1, v2) {
        let result = new Complex(0, 0);
        for (let i = 0; i < v1.length; i++) {
            result = result.add(v1[i].conjugate().mul(v2[i]));
        }
        return result;
    }

    /**
     * Norm of complex vector
     * @param {Complex[]} v
     * @returns {number}
     */
    static norm(v) {
        let sum = 0;
        for (const c of v) {
            sum += c.abs() ** 2;
        }
        return Math.sqrt(sum);
    }

    /**
     * Normalize complex vector
     * @param {Complex[]} v
     * @returns {Complex[]}
     */
    static normalize(v) {
        const norm = this.norm(v);
        if (norm === 0) return v;
        return v.map(c => c.div(norm));
    }

    /**
     * Matrix multiplication for complex matrices
     * @param {Complex[][]} a
     * @param {Complex[][]} b
     * @returns {Complex[][]}
     */
    static matMul(a, b) {
        const rows = a.length;
        const cols = b[0].length;
        const inner = b.length;
        
        const result = Array(rows).fill().map(() => Array(cols).fill(new Complex(0, 0)));
        
        for (let i = 0; i < rows; i++) {
            for (let j = 0; j < cols; j++) {
                for (let k = 0; k < inner; k++) {
                    result[i][j] = result[i][j].add(a[i][k].mul(b[k][j]));
                }
            }
        }
        return result;
    }
}

export default ComplexMath;
