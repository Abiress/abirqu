/**
 * Basic quantum circuit examples in JavaScript
 */

import { QuantumCircuit, QuantumSimulator } from '../src/index.js';

// Example 1: Bell State
console.log('=== Example 1: Bell State (|00> + |11>)/sqrt(2) ===\n');

const circuit1 = new QuantumCircuit(2);
circuit1.h(0);
circuit1.cnot(0, 1);

const sim1 = new QuantumSimulator();
const result1 = sim1.simulate(circuit1);

console.log('State vector:');
result1.stateVector.forEach((amp, i) => {
    if (amp.abs() > 1e-10) {
        console.log(`|${i.toString(2).padStart(2, '0')}>: ${amp.toString()}`);
    }
});

console.log('\nProbabilities:', result1.probabilities.map(p => p.toFixed(4)));
console.log('Measurement counts (1000 shots):');
const shots1 = sim1.runShots(circuit1, 1000);
console.log(shots1.counts);

// Example 2: Quantum Teleportation Circuit
console.log('\n\n=== Example 2: Quantum Teleportation ===\n');

const circuit2 = new QuantumCircuit(3);
circuit2.h(0);
circuit2.cnot(0, 1);
circuit2.cnot(1, 2);
circuit2.h(0);

const sim2 = new QuantumSimulator();
const result2 = sim2.simulate(circuit2);

console.log('3-qubit state probabilities:');
result2.probabilities.forEach((p, i) => {
    if (p > 0.01) {
        console.log(`|${i.toString(2).padStart(3, '0')}>: ${(p * 100).toFixed(2)}%`);
    }
});

// Example 3: Grover-like search
console.log('\n\n=== Example 3: 2-qubit superposition ===\n');

const circuit3 = new QuantumCircuit(2);
circuit3.h(0);
circuit3.h(1);

const sim3 = new QuantumSimulator();
const result3 = sim3.simulate(circuit3);

console.log('Equal superposition state:');
result3.stateVector.forEach((amp, i) => {
    console.log(`|${i.toString(2).padStart(2, '0')}>: ${amp.toString()}`);
});

console.log('\nAll examples completed successfully!');
