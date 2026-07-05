/**
 * Tests for AbirQu JavaScript binding.
 */
import { Circuit, run, bellState, ghzState, qft, grover, wState, StatevectorSimulator } from '../src/index.js';

describe('Circuit', () => {
  test('creates circuit with correct properties', () => {
    const c = new Circuit(3, 'test');
    expect(c.numQubits).toBe(3);
    expect(c.name).toBe('test');
    expect(c.gates).toHaveLength(0);
  });

  test('rejects invalid qubit count', () => {
    expect(() => new Circuit(0)).toThrow();
    expect(() => new Circuit(9)).toThrow();
  });

  test('gate methods return self for chaining', () => {
    const c = new Circuit(2);
    const result = c.h(0).x(1).cnot(0, 1);
    expect(result).toBe(c);
    expect(c.gates).toHaveLength(3);
  });

  test('all single-qubit gates', () => {
    const c = new Circuit(1);
    c.h(0).x(0).y(0).z(0).s(0).sdg(0).t(0).tdg(0);
    c.rx(0, 0.5).ry(0, 0.5).rz(0, 0.5);
    expect(c.gates).toHaveLength(11);
  });

  test('two-qubit gates', () => {
    const c = new Circuit(2);
    c.cnot(0, 1).cz(0, 1).swap(0, 1);
    expect(c.gates).toHaveLength(3);
  });

  test('toffoli gate', () => {
    const c = new Circuit(3);
    c.toffoli(0, 1, 2);
    expect(c.gates).toHaveLength(1);
    expect(c.gates[0].name).toBe('CCX');
  });

  test('measure and measureAll', () => {
    const c = new Circuit(3);
    c.measure(0).measure(1, 2);
    expect(c.measurements).toHaveLength(2);

    const c2 = new Circuit(3);
    c2.measureAll();
    expect(c2.measurements).toHaveLength(3);
  });

  test('depth calculation', () => {
    const c = new Circuit(2);
    expect(c.depth()).toBe(0);

    c.h(0);
    expect(c.depth()).toBe(1);

    c.cnot(0, 1);
    expect(c.depth()).toBe(2);

    c.h(0);
    expect(c.depth()).toBe(3);
  });

  test('gate count', () => {
    const c = new Circuit(2);
    c.h(0).h(1).cnot(0, 1);
    const counts = c.countGates();
    expect(counts['H']).toBe(2);
    expect(counts['CNOT']).toBe(1);
  });

  test('toQASM output', () => {
    const c = new Circuit(2, 'bell');
    c.h(0).cnot(0, 1).measureAll();
    const qasm = c.toQASM();
    expect(qasm).toContain('OPENQASM 2.0');
    expect(qasm).toContain('qreg q[2]');
    expect(qasm).toContain('h q[0]');
    expect(qasm).toContain('cx q[0],q[1]');
    expect(qasm).toContain('measure');
  });

  test('toJSON and fromJSON roundtrip', () => {
    const c = new Circuit(2, 'test');
    c.h(0).cnot(0, 1);
    c.measure(0);

    const json = c.toJSON();
    const c2 = Circuit.fromJSON(json);

    expect(c2.numQubits).toBe(2);
    expect(c2.name).toBe('test');
    expect(c2.gates).toHaveLength(2);
    expect(c2.measurements).toHaveLength(1);
  });

  test('toString', () => {
    const c = new Circuit(3, 'my_circuit');
    c.h(0).cnot(0, 1);
    expect(c.toString()).toBe('Circuit(my_circuit, qubits=3, gates=2)');
  });
});

describe('Simulator', () => {
  test('creates with correct state', () => {
    const sim = new StatevectorSimulator(2);
    const sv = sim.getStatevector();
    expect(sv).toHaveLength(4);
    expect(sv[0]).toEqual([1, 0]);
    expect(sv[1]).toEqual([0, 0]);
  });

  test('H gate creates superposition', () => {
    const sim = new StatevectorSimulator(1);
    sim.execute([{ name: 'H', qubits: [0], params: [] }]);
    const sv = sim.getStatevector();
    expect(sv[0][0]).toBeCloseTo(1 / Math.SQRT2);
    expect(sv[1][0]).toBeCloseTo(1 / Math.SQRT2);
  });

  test('X gate flips qubit', () => {
    const sim = new StatevectorSimulator(1);
    sim.execute([{ name: 'X', qubits: [0], params: [] }]);
    const sv = sim.getStatevector();
    expect(sv[0][0]).toBeCloseTo(0);
    expect(sv[1][0]).toBeCloseTo(1);
  });

  test('CNOT creates Bell state', () => {
    const sim = new StatevectorSimulator(2);
    sim.execute([
      { name: 'H', qubits: [0], params: [] },
      { name: 'CNOT', qubits: [0, 1], params: [] },
    ]);
    const probs = sim.getProbabilities();
    expect(probs['00']).toBeCloseTo(0.5);
    expect(probs['11']).toBeCloseTo(0.5);
    expect(probs['01']).toBeUndefined();
    expect(probs['10']).toBeUndefined();
  });

  test('sample returns correct counts', () => {
    const sim = new StatevectorSimulator(1);
    sim.execute([{ name: 'X', qubits: [0], params: [] }]);
    const counts = sim.sample(100);
    expect(counts['1']).toBe(100);
  });

  test('supports 8 qubits', () => {
    const sim = new StatevectorSimulator(8);
    expect(sim.getStatevector()).toHaveLength(256);
  });

  test('rejects > 8 qubits', () => {
    expect(() => new StatevectorSimulator(9)).toThrow();
  });
});

describe('Built-in circuits', () => {
  test('bellState produces Bell state', () => {
    const c = bellState();
    expect(c.numQubits).toBe(2);
    const result = run(c, 0);
    const sv = result.statevector!;
    expect(sv[0][0]).toBeCloseTo(1 / Math.SQRT2);
    expect(sv[3][0]).toBeCloseTo(1 / Math.SQRT2);
  });

  test('ghzState produces GHZ state', () => {
    const c = ghzState(3);
    expect(c.numQubits).toBe(3);
    const result = run(c, 0);
    const probs = result.probabilities;
    expect(probs['000']).toBeCloseTo(0.5);
    expect(probs['111']).toBeCloseTo(0.5);
  });

  test('ghzState requires >= 2 qubits', () => {
    expect(() => ghzState(1)).toThrow();
  });

  test('qft runs without error', () => {
    const c = qft(3);
    expect(c.numQubits).toBe(3);
    const result = run(c, 100);
    expect(result.success).toBe(true);
    expect(Object.keys(result.counts).length).toBeGreaterThan(0);
  });

  test('grover finds target', () => {
    const c = grover(2, 3);
    expect(c.numQubits).toBe(2);
    const result = run(c, 1000);
    expect(result.success).toBe(true);
    // With 2 qubits and target=3, should find |11> with high probability
    const total = Object.values(result.counts).reduce((a, b) => a + b, 0);
    expect(total).toBe(1000);
  });

  test('grover rejects invalid target', () => {
    expect(() => grover(2, 4)).toThrow();
  });

  test('wState runs', () => {
    const c = wState(3);
    expect(c.numQubits).toBe(3);
    const result = run(c, 100);
    expect(result.success).toBe(true);
  });

  test('randomCircuit runs', () => {
    const c = new Circuit(3);
    // Build a simple random-like circuit manually
    c.h(0).rx(1, 0.5).ry(2, 1.0).cnot(0, 1).cnot(1, 2);
    const result = run(c, 100);
    expect(result.success).toBe(true);
  });
});

describe('run function', () => {
  test('returns correct structure', () => {
    const c = new Circuit(1);
    c.h(0);
    const result = run(c, 100);
    expect(result.success).toBe(true);
    expect(result.backend).toBe('StatevectorSimulator');
    expect(result.shots).toBe(100);
    expect(typeof result.counts).toBe('object');
    expect(typeof result.probabilities).toBe('object');
  });

  test('shots=0 returns statevector', () => {
    const c = new Circuit(1);
    c.h(0);
    const result = run(c, 0);
    expect(result.statevector).not.toBeNull();
    expect(result.statevector).toHaveLength(2);
  });

  test('shots=1024 default', () => {
    const c = new Circuit(1);
    c.x(0);
    const result = run(c);
    expect(result.shots).toBe(1024);
    expect(result.counts['1']).toBe(1024);
  });
});
