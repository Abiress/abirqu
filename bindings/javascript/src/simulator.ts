/**
 * Local statevector simulator for AbirQu JavaScript binding.
 * Pure JS implementation supporting 1-8 qubits using Float64Array for complex state vectors.
 * Copyright 2026 Abir Maheshwari
 */

/** Complex number as [real, imag] tuple */
type Complex = [number, number];

const SQRT2_INV = 1 / Math.SQRT2;

// Gate matrices as [real, imag] pairs
const GATES = {
  H: [
    [SQRT2_INV, 0], [SQRT2_INV, 0],
    [SQRT2_INV, 0], [-SQRT2_INV, 0],
  ] as Complex[],
  X: [
    [0, 0], [1, 0],
    [1, 0], [0, 0],
  ] as Complex[],
  Y: [
    [0, 0], [0, -1],
    [0, 1], [0, 0],
  ] as Complex[],
  Z: [
    [1, 0], [0, 0],
    [0, 0], [-1, 0],
  ] as Complex[],
  S: [
    [1, 0], [0, 0],
    [0, 0], [0, 1],
  ] as Complex[],
  Sdg: [
    [1, 0], [0, 0],
    [0, 0], [0, -1],
  ] as Complex[],
  T: [
    [1, 0], [0, 0],
    [0, 0], [Math.cos(Math.PI / 4), Math.sin(Math.PI / 4)],
  ] as Complex[],
  Tdg: [
    [1, 0], [0, 0],
    [0, 0], [Math.cos(Math.PI / 4), -Math.sin(Math.PI / 4)],
  ] as Complex[],
};

function rx(theta: number): Complex[] {
  const c = Math.cos(theta / 2);
  const s = Math.sin(theta / 2);
  return [
    [c, 0], [0, -s],
    [0, -s], [c, 0],
  ];
}

function ry(theta: number): Complex[] {
  const c = Math.cos(theta / 2);
  const s = Math.sin(theta / 2);
  return [
    [c, 0], [-s, 0],
    [s, 0], [c, 0],
  ];
}

function rz(theta: number): Complex[] {
  return [
    [Math.cos(theta / 2), -Math.sin(theta / 2)], [0, 0],
    [0, 0], [Math.cos(theta / 2), Math.sin(theta / 2)],
  ];
}

interface GateOp {
  name: string;
  qubits: number[];
  params: number[];
}

export interface SimulationResult {
  probabilities: Record<string, number>;
  counts: Record<string, number>;
  statevector: Complex[];
}

/**
 * Statevector simulator using interleaved complex representation.
 * State vector stored as Float64Array of length 2^(n+1) where
 * state[2*i] = real, state[2*i+1] = imag for amplitude i.
 */
export class StatevectorSimulator {
  private n: number;
  private dim: number;
  private state: Float64Array;

  constructor(numQubits: number) {
    if (numQubits < 1 || numQubits > 8) {
      throw new Error('Simulator supports 1-8 qubits');
    }
    this.n = numQubits;
    this.dim = 1 << numQubits;
    this.state = new Float64Array(this.dim * 2);
    // Initialize to |00...0>
    this.state[0] = 1;
  }

  /** Reset to |00...0> */
  reset(): void {
    this.state.fill(0);
    this.state[0] = 1;
  }

  /** Apply single-qubit gate via explicit loop */
  private apply1Q(gate: Complex[], qubit: number): void {
    const mask = 1 << qubit;
    const newState = new Float64Array(this.dim * 2);

    for (let i = 0; i < this.dim; i++) {
      const bit = (i >> qubit) & 1;
      const other = i ^ mask;

      if (bit === 0) {
        const a0r = this.state[i * 2];
        const a0i = this.state[i * 2 + 1];
        const a1r = this.state[other * 2];
        const a1i = this.state[other * 2 + 1];

        // gate[0] * a0 + gate[1] * a1
        newState[i * 2] = gate[0][0] * a0r - gate[0][1] * a0i + gate[2][0] * a1r - gate[2][1] * a1i;
        newState[i * 2 + 1] = gate[0][0] * a0i + gate[0][1] * a0r + gate[2][0] * a1i + gate[2][1] * a1r;

        // gate[2] * a0 + gate[3] * a1
        newState[other * 2] = gate[1][0] * a0r - gate[1][1] * a0i + gate[3][0] * a1r - gate[3][1] * a1i;
        newState[other * 2 + 1] = gate[1][0] * a0i + gate[1][1] * a0r + gate[3][0] * a1i + gate[3][1] * a1r;
      }
    }

    this.state = newState;
  }

  /** Apply CNOT gate */
  private applyCNOT(control: number, target: number): void {
    const controlMask = 1 << control;
    const targetMask = 1 << target;
    const newState = new Float64Array(this.dim * 2);

    for (let i = 0; i < this.dim; i++) {
      if (i & controlMask) {
        // Control is |1>, flip target
        const j = i ^ targetMask;
        newState[j * 2] = this.state[i * 2];
        newState[j * 2 + 1] = this.state[i * 2 + 1];
      } else {
        newState[i * 2] = this.state[i * 2];
        newState[i * 2 + 1] = this.state[i * 2 + 1];
      }
    }

    this.state = newState;
  }

  /** Apply CZ gate */
  private applyCZ(control: number, target: number): void {
    const controlMask = 1 << control;
    const targetMask = 1 << target;

    for (let i = 0; i < this.dim; i++) {
      if ((i & controlMask) && (i & targetMask)) {
        this.state[i * 2] *= -1;
        this.state[i * 2 + 1] *= -1;
      }
    }
  }

  /** Apply SWAP gate */
  private applySWAP(q0: number, q1: number): void {
    if (q0 === q1) return;

    const m0 = 1 << q0;
    const m1 = 1 << q1;
    const newState = new Float64Array(this.dim * 2);

    for (let i = 0; i < this.dim; i++) {
      const b0 = (i >> q0) & 1;
      const b1 = (i >> q1) & 1;

      let j: number;
      if (b0 === b1) {
        j = i;
      } else {
        j = i ^ m0 ^ m1;
      }

      newState[j * 2] = this.state[i * 2];
      newState[j * 2 + 1] = this.state[i * 2 + 1];
    }

    this.state = newState;
  }

  /** Apply Toffoli gate */
  private applyToffoli(c1: number, c2: number, target: number): void {
    const c1Mask = 1 << c1;
    const c2Mask = 1 << c2;
    const tMask = 1 << target;
    const newState = new Float64Array(this.dim * 2);

    for (let i = 0; i < this.dim; i++) {
      if ((i & c1Mask) && (i & c2Mask)) {
        const j = i ^ tMask;
        newState[j * 2] = this.state[i * 2];
        newState[j * 2 + 1] = this.state[i * 2 + 1];
      } else {
        newState[i * 2] = this.state[i * 2];
        newState[i * 2 + 1] = this.state[i * 2 + 1];
      }
    }

    this.state = newState;
  }

  /** Execute a sequence of gate operations */
  execute(gates: GateOp[]): void {
    for (const gate of gates) {
      const name = gate.name.toUpperCase();
      const qubits = gate.qubits;

      switch (name) {
        case 'H':
          this.apply1Q(GATES.H, qubits[0]);
          break;
        case 'X':
          this.apply1Q(GATES.X, qubits[0]);
          break;
        case 'Y':
          this.apply1Q(GATES.Y, qubits[0]);
          break;
        case 'Z':
          this.apply1Q(GATES.Z, qubits[0]);
          break;
        case 'S':
          this.apply1Q(GATES.S, qubits[0]);
          break;
        case 'SDG':
          this.apply1Q(GATES.Sdg, qubits[0]);
          break;
        case 'T':
          this.apply1Q(GATES.T, qubits[0]);
          break;
        case 'TDG':
          this.apply1Q(GATES.Tdg, qubits[0]);
          break;
        case 'RX':
          this.apply1Q(rx(gate.params[0]), qubits[0]);
          break;
        case 'RY':
          this.apply1Q(ry(gate.params[0]), qubits[0]);
          break;
        case 'RZ':
          this.apply1Q(rz(gate.params[0]), qubits[0]);
          break;
        case 'CNOT':
        case 'CX':
          this.applyCNOT(qubits[0], qubits[1]);
          break;
        case 'CZ':
          this.applyCZ(qubits[0], qubits[1]);
          break;
        case 'SWAP':
          this.applySWAP(qubits[0], qubits[1]);
          break;
        case 'CCX':
        case 'TOFFOLI':
          this.applyToffoli(qubits[0], qubits[1], qubits[2]);
          break;
        default:
          throw new Error(`Unknown gate: ${name}`);
      }
    }
  }

  /** Get probabilities as a record of bitstring -> probability */
  getProbabilities(): Record<string, number> {
    const probs: Record<string, number> = {};
    for (let i = 0; i < this.dim; i++) {
      const re = this.state[i * 2];
      const im = this.state[i * 2 + 1];
      const p = re * re + im * im;
      if (p > 1e-15) {
        probs[i.toString(2).padStart(this.n, '0')] = p;
      }
    }
    return probs;
  }

  /** Get the raw statevector as complex pairs */
  getStatevector(): Complex[] {
    const sv: Complex[] = [];
    for (let i = 0; i < this.dim; i++) {
      sv.push([this.state[i * 2], this.state[i * 2 + 1]]);
    }
    return sv;
  }

  /** Sample measurement outcomes */
  sample(shots: number): Record<string, number> {
    const probs = this.getProbabilities();
    const states = Object.keys(probs);
    const weights = states.map((s) => probs[s]);
    const counts: Record<string, number> = {};

    for (let i = 0; i < shots; i++) {
      const r = Math.random();
      let cum = 0;
      for (let j = 0; j < states.length; j++) {
        cum += weights[j];
        if (r < cum) {
          counts[states[j]] = (counts[states[j]] || 0) + 1;
          break;
        }
      }
    }

    return counts;
  }
}

export { GATES, rx, ry, rz };
export type { GateOp, Complex };
