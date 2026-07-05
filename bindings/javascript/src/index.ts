/**
 * AbirQu JavaScript/TypeScript binding - Main entry point.
 * Provides a Circuit class and built-in quantum circuits.
 * Copyright 2026 Abir Maheshwari
 */

import { StatevectorSimulator, GateOp, SimulationResult, Complex } from './simulator.js';

export { StatevectorSimulator };
export type { GateOp, SimulationResult, Complex };

export interface GateRecord {
  name: string;
  qubits: number[];
  params: number[];
}

export interface MeasurementRecord {
  qubit: number;
  cbit: number;
}

export interface RunResult {
  success: boolean;
  backend: string;
  shots: number;
  counts: Record<string, number>;
  probabilities: Record<string, number>;
  statevector: Complex[] | null;
}

/**
 * Quantum circuit with fluent API for building quantum programs.
 */
export class Circuit {
  readonly numQubits: number;
  readonly name: string;
  readonly gates: GateRecord[] = [];
  readonly measurements: MeasurementRecord[] = [];
  private classicalBits = 0;

  constructor(numQubits: number, name?: string) {
    if (numQubits < 1 || numQubits > 8) {
      throw new Error('Circuit supports 1-8 qubits');
    }
    this.numQubits = numQubits;
    this.name = name || `circuit_${Math.random().toString(36).slice(2, 10)}`;
  }

  private addGate(name: string, qubits: number[], params: number[] = []): this {
    this.gates.push({ name, qubits, params });
    return this;
  }

  /** Hadamard gate */
  h(qubit: number): this {
    return this.addGate('H', [qubit]);
  }

  /** Pauli-X gate */
  x(qubit: number): this {
    return this.addGate('X', [qubit]);
  }

  /** Pauli-Y gate */
  y(qubit: number): this {
    return this.addGate('Y', [qubit]);
  }

  /** Pauli-Z gate */
  z(qubit: number): this {
    return this.addGate('Z', [qubit]);
  }

  /** S gate (phase gate) */
  s(qubit: number): this {
    return this.addGate('S', [qubit]);
  }

  /** S-dagger gate */
  sdg(qubit: number): this {
    return this.addGate('SDG', [qubit]);
  }

  /** T gate (π/8 gate) */
  t(qubit: number): this {
    return this.addGate('T', [qubit]);
  }

  /** T-dagger gate */
  tdg(qubit: number): this {
    return this.addGate('TDG', [qubit]);
  }

  /** Rotation around X-axis */
  rx(qubit: number, theta: number): this {
    return this.addGate('RX', [qubit], [theta]);
  }

  /** Rotation around Y-axis */
  ry(qubit: number, theta: number): this {
    return this.addGate('RY', [qubit], [theta]);
  }

  /** Rotation around Z-axis */
  rz(qubit: number, theta: number): this {
    return this.addGate('RZ', [qubit], [theta]);
  }

  /** CNOT (CX) gate */
  cnot(control: number, target: number): this {
    return this.addGate('CNOT', [control, target]);
  }

  /** CX alias */
  cx(control: number, target: number): this {
    return this.cnot(control, target);
  }

  /** CZ gate */
  cz(control: number, target: number): this {
    return this.addGate('CZ', [control, target]);
  }

  /** SWAP gate */
  swap(q1: number, q2: number): this {
    return this.addGate('SWAP', [q1, q2]);
  }

  /** Toffoli (CCX) gate */
  toffoli(c1: number, c2: number, target: number): this {
    return this.addGate('CCX', [c1, c2, target]);
  }

  /** Measure a qubit into a classical bit */
  measure(qubit: number, cbit?: number): this {
    const c = cbit ?? qubit;
    this.measurements.push({ qubit, cbit: c });
    if (c + 1 > this.classicalBits) {
      this.classicalBits = c + 1;
    }
    return this;
  }

  /** Measure all qubits */
  measureAll(): this {
    for (let q = 0; q < this.numQubits; q++) {
      this.measure(q, q);
    }
    return this;
  }

  /** Get estimated circuit depth */
  depth(): number {
    if (this.gates.length === 0) return 0;

    const qubitDepth = new Array(this.numQubits).fill(0);
    let maxDepth = 0;

    for (const gate of this.gates) {
      const gateDepth = 1 + Math.max(...gate.qubits.map((q) => qubitDepth[q]));
      for (const q of gate.qubits) {
        qubitDepth[q] = gateDepth;
      }
      maxDepth = Math.max(maxDepth, gateDepth);
    }

    return maxDepth;
  }

  /** Get gate count histogram */
  countGates(): Record<string, number> {
    const counts: Record<string, number> = {};
    for (const gate of this.gates) {
      counts[gate.name] = (counts[gate.name] || 0) + 1;
    }
    return counts;
  }

  /** Execute the circuit */
  run(shots: number = 1024): RunResult {
    const sim = new StatevectorSimulator(this.numQubits);
    sim.execute(this.gates);

    const probabilities = sim.getProbabilities();
    let counts: Record<string, number>;

    if (shots === 0) {
      counts = {};
    } else {
      counts = sim.sample(shots);
    }

    const statevector = shots === 0 ? sim.getStatevector() : null;

    return {
      success: true,
      backend: 'StatevectorSimulator',
      shots,
      counts,
      probabilities,
      statevector,
    };
  }

  /** Convert to OpenQASM 2.0 */
  toQASM(): string {
    const lines = [
      'OPENQASM 2.0;',
      'include "qelib1.inc";',
      '',
      `qreg q[${this.numQubits}];`,
    ];

    if (this.classicalBits > 0) {
      lines.push(`creg c[${this.classicalBits}];`);
    }
    lines.push('');

    for (const gate of this.gates) {
      const qargs = gate.qubits.map((q) => `q[${q}]`).join(',');
      const params = gate.params.length > 0
        ? `(${gate.params.join(',')})`
        : '';

      if (gate.name === 'CNOT') {
        lines.push(`cx ${gate.qubits.map((q) => `q[${q}]`).join(',')};`);
      } else {
        lines.push(`${gate.name.toLowerCase()}${params} ${qargs};`);
      }
    }

    for (const meas of this.measurements) {
      lines.push(`measure q[${meas.qubit}] -> c[${meas.cbit}];`);
    }

    return lines.join('\n');
  }

  /** Convert to JSON */
  toJSON(): string {
    return JSON.stringify({
      name: this.name,
      numQubits: this.numQubits,
      classicalBits: this.classicalBits,
      gates: this.gates,
      measurements: this.measurements,
    }, null, 2);
  }

  /** Create from JSON */
  static fromJSON(json: string): Circuit {
    const data = JSON.parse(json);
    const circuit = new Circuit(data.numQubits, data.name);
    (circuit as any).classicalBits = data.classicalBits || 0;
    circuit.gates.push(...data.gates);
    circuit.measurements.push(...data.measurements);
    return circuit;
  }

  /** Simple text drawing */
  toString(): string {
    return `Circuit(${this.name}, qubits=${this.numQubits}, gates=${this.gates.length})`;
  }
}

// ─── Built-in Circuits ────────────────────────────────────────────────

/** Create a Bell state: H(0) CNOT(0,1) */
export function bellState(): Circuit {
  const c = new Circuit(2, 'Bell State');
  c.h(0).cnot(0, 1).measureAll();
  return c;
}

/** Create an n-qubit GHZ state */
export function ghzState(n: number): Circuit {
  if (n < 2) throw new Error('GHZ state requires at least 2 qubits');
  const c = new Circuit(n, `GHZ State (${n} qubits)`);
  c.h(0);
  for (let i = 0; i < n - 1; i++) {
    c.cnot(i, i + 1);
  }
  c.measureAll();
  return c;
}

/** Quantum Fourier Transform on n qubits */
export function qft(n: number): Circuit {
  const c = new Circuit(n, `QFT (${n} qubits)`);
  for (let i = 0; i < n; i++) {
    c.h(i);
    for (let j = i + 1; j < n; j++) {
      c.cnot(j, i);
      c.rz(i, Math.PI / Math.pow(2, j - i));
      c.cnot(j, i);
    }
  }
  // Reverse qubit order
  for (let i = 0; i < Math.floor(n / 2); i++) {
    c.swap(i, n - 1 - i);
  }
  return c;
}

/** Grover's search algorithm for n qubits with marked target state */
export function grover(n: number, target: number): Circuit {
  if (target < 0 || target >= (1 << n)) {
    throw new Error(`Target must be between 0 and ${(1 << n) - 1}`);
  }

  const c = new Circuit(n, `Grover (${n} qubits, target=${target})`);

  // Initialize to uniform superposition
  for (let i = 0; i < n; i++) {
    c.h(i);
  }

  // Number of Grover iterations
  const iterations = Math.floor(Math.PI / 4 * Math.sqrt(1 << n));

  for (let iter = 0; iter < iterations; iter++) {
    // Oracle: flip phase of target state
    for (let q = 0; q < n; q++) {
      if (!((target >> q) & 1)) {
        c.x(q);
      }
    }

    // Multi-controlled Z gate via H and multi-controlled X
    c.h(n - 1);
    if (n === 2) {
      c.cnot(0, 1);
    } else {
      c.toffoli(0, 1, 2);
      // For n > 3, we'd need more complex decomposition
      // For simplicity, use recursive approach for small n
      for (let k = 2; k < n - 1 && k < 3; k++) {
        c.toffoli(k, k + 1, k + 2);
      }
    }
    c.h(n - 1);

    // Undo oracle X gates
    for (let q = 0; q < n; q++) {
      if (!((target >> q) & 1)) {
        c.x(q);
      }
    }

    // Diffusion operator: 2|s><s| - I
    for (let i = 0; i < n; i++) {
      c.h(i);
    }

    for (let i = 0; i < n; i++) {
      c.x(i);
    }

    c.h(n - 1);
    if (n === 2) {
      c.cnot(0, 1);
    } else {
      c.toffoli(0, 1, 2);
      for (let k = 2; k < n - 1 && k < 3; k++) {
        c.toffoli(k, k + 1, k + 2);
      }
    }
    c.h(n - 1);

    for (let i = 0; i < n; i++) {
      c.x(i);
    }

    for (let i = 0; i < n; i++) {
      c.h(i);
    }
  }

  c.measureAll();
  return c;
}

/** Create a W state */
export function wState(n: number): Circuit {
  if (n < 2) throw new Error('W state requires at least 2 qubits');
  const c = new Circuit(n, `W State (${n} qubits)`);

  // Prepare W state using amplitude encoding
  c.ry(0, 2 * Math.acos(Math.sqrt((n - 1) / n)));

  for (let i = 1; i < n; i++) {
    c.ry(i, 2 * Math.acos(Math.sqrt(1 / (n - i))));
    c.cnot(0, i);
  }

  c.measureAll();
  return c;
}

/** Create a random circuit */
export function randomCircuit(n: number, depth: number): Circuit {
  const c = new Circuit(n, `Random (${n} qubits, depth=${depth})`);
  const gateNames = ['H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ'];

  for (let d = 0; d < depth; d++) {
    for (let q = 0; q < n; q++) {
      const gate = gateNames[Math.floor(Math.random() * gateNames.length)];
      if (gate.startsWith('R')) {
        c.gates.push({ name: gate, qubits: [q], params: [Math.random() * 2 * Math.PI] });
      } else {
        c.gates.push({ name: gate, qubits: [q], params: [] });
      }
    }

    // Add entangling gates
    for (let q = 0; q < n - 1; q += 2) {
      c.cnot(q, q + 1);
    }
  }

  return c;
}

// ─── Convenience run function ─────────────────────────────────────────

/** Run a circuit and return results */
export function run(circuit: Circuit, shots: number = 1024): RunResult {
  return circuit.run(shots);
}

export default {
  Circuit,
  run,
  bellState,
  ghzState,
  qft,
  grover,
  wState,
  randomCircuit,
  StatevectorSimulator,
};
