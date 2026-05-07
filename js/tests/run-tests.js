/**
 * Test suite for AbirQu JavaScript SDK
 */

import { QuantumCircuit, QuantumGates, QuantumSimulator, ComplexMath } from '../src/index.js';
import { Complex } from 'complex.js';

let passed = 0;
let failed = 0;

function assert(condition, testName) {
    if (condition) {
        console.log(`✓ ${testName}`);
        passed++;
    } else {
        console.log(`✗ ${testName}`);
        failed++;
    }
}

function assertClose(a, b, tolerance, testName) {
    const diff = Math.abs(a - b);
    if (diff < tolerance) {
        console.log(`✓ ${testName}`);
        passed++;
    } else {
        console.log(`✗ ${testName} (expected ${b}, got ${a}, diff ${diff})`);
        failed++;
    }
}

async function runTests() {
    console.log('Running AbirQu JavaScript SDK Tests...\n');

    // Test 1: Complex Math
    console.log('--- Complex Math ---');
    const c1 = ComplexMath.create(1, 2);
    const c2 = ComplexMath.create(3, 4);
    assert(c1.add(c2).re === 4 && c1.add(c2).im === 6, 'Complex addition');
    assert(c1.mul(c2).re === -5 && c1.mul(c2).im === 10, 'Complex multiplication');

    // Test 2: Quantum Gates
    console.log('\n--- Quantum Gates ---');
    const hGate = QuantumGates.H;
    assert(hGate[0][0].re === 1/Math.sqrt(2), 'H gate matrix element');
    assert(QuantumGates.X[0][1].re === 1, 'X gate matrix element');

    // Test 3: Single Qubit Circuit
    console.log('\n--- Single Qubit Circuit ---');
    const circuit1 = new QuantumCircuit(1);
    circuit1.h(0);
    const sim1 = new QuantumSimulator();
    const result1 = sim1.simulate(circuit1);
    assertClose(result1.probabilities[0], 0.5, 1e-10, 'H|0> gives 50% |0>');
    assertClose(result1.probabilities[1], 0.5, 1e-10, 'H|0> gives 50% |1>');

    // Test 4: Bell State
    console.log('\n--- Bell State ---');
    const bellCircuit = QuantumSimulator.createBellState();
    const bellSim = new QuantumSimulator();
    const bellResult = bellSim.simulate(bellCircuit);
    assertClose(bellResult.probabilities[0], 0.5, 1e-10, 'Bell state |00> probability');
    assertClose(bellResult.probabilities[3], 0.5, 1e-10, 'Bell state |11> probability');
    assertClose(bellResult.probabilities[1], 0, 1e-10, 'Bell state |01> probability');
    assertClose(bellResult.probabilities[2], 0, 1e-10, 'Bell state |10> probability');

    // Test 5: GHZ State
    console.log('\n--- GHZ State ---');
    const ghzCircuit = QuantumSimulator.createGHZState(3);
    const ghzSim = new QuantumSimulator();
    const ghzResult = ghzSim.simulate(ghzCircuit);
    assertClose(ghzResult.probabilities[0], 0.5, 1e-10, 'GHZ |000> probability');
    assertClose(ghzResult.probabilities[7], 0.5, 1e-10, 'GHZ |111> probability');

    // Test 6: Shots
    console.log('\n--- Shot-based Simulation ---');
    const shotCircuit = new QuantumCircuit(1);
    shotCircuit.h(0);
    const shotSim = new QuantumSimulator();
    const shotsResult = shotSim.runShots(shotCircuit, 1000);
    assert(shotsResult.shots === 1000, 'Correct number of shots');
    assert(Math.abs(shotsResult.counts['0'] - 500) < 100, 'Shot counts approximately 50/50');

    // Test 7: Circuit Depth
    console.log('\n--- Circuit Properties ---');
    const depthCircuit = new QuantumCircuit(2);
    depthCircuit.h(0).cnot(0, 1).h(1);
    assert(depthCircuit.depth() === 3, 'Circuit depth calculation');
    assert(depthCircuit.numQubits === 2, 'Qubit count');

    // Test 8: Rotation Gates
    console.log('\n--- Rotation Gates ---');
    const rotCircuit = new QuantumCircuit(1);
    rotCircuit.rx(0, Math.PI);
    const rotSim = new QuantumSimulator();
    const rotResult = rotSim.simulate(rotCircuit);
    assertClose(rotResult.probabilities[1], 1.0, 1e-10, 'RX(π) rotates to |1>');

    console.log(`\n--- Results ---`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Total: ${passed + failed}`);

    if (failed > 0) {
        process.exit(1);
    } else {
        console.log('\nAll tests passed! ✓');
    }
}

runTests().catch(console.error);
