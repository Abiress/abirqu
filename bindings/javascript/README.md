# @abirqu/js

JavaScript/TypeScript binding for the AbirQu quantum computing SDK.

Standalone quantum circuit simulator — no Python required.

## Features

- **1-8 qubit simulation** using statevector simulation
- **Full gate set**: H, X, Y, Z, S, T, RX, RY, RZ, CNOT, CZ, SWAP, Toffoli
- **Built-in circuits**: Bell state, GHZ state, QFT, Grover's search, W state
- **Fluent API** for circuit construction
- **OpenQASM 2.0 export**
- **Zero dependencies** (runtime)

## Install

```bash
npm install @abirqu/js
```

## Quick Start

```typescript
import { Circuit, run, bellState } from '@abirqu/js';

// Build a circuit manually
const circuit = new Circuit(2, 'My Bell State');
circuit.h(0).cnot(0, 1).measureAll();

const result = run(circuit, 1024);
console.log(result.counts);
// { "00": ~512, "11": ~512 }

// Or use built-in circuits
const bell = bellState();
const ghz = ghzState(4);

// Run without measurement to get statevector
const stateResult = run(bell, 0);
console.log(stateResult.statevector);
// [[0.707, 0], [0, 0], [0, 0], [0.707, 0]]
```

## API

### `Circuit`

```typescript
const c = new Circuit(numQubits, name?);
```

**Gate methods** (all return `this` for chaining):

| Method | Description |
|--------|-------------|
| `h(qubit)` | Hadamard gate |
| `x(qubit)` | Pauli-X (NOT) gate |
| `y(qubit)` | Pauli-Y gate |
| `z(qubit)` | Pauli-Z gate |
| `s(qubit)` | S (phase) gate |
| `sdg(qubit)` | S-dagger gate |
| `t(qubit)` | T (π/8) gate |
| `tdg(qubit)` | T-dagger gate |
| `rx(qubit, θ)` | X-axis rotation |
| `ry(qubit, θ)` | Y-axis rotation |
| `rz(qubit, θ)` | Z-axis rotation |
| `cnot(ctrl, tgt)` | CNOT gate |
| `cz(ctrl, tgt)` | CZ gate |
| `swap(q1, q2)` | SWAP gate |
| `toffoli(c1, c2, tgt)` | Toffoli (CCX) gate |
| `measure(qubit, cbit?)` | Measure qubit |
| `measureAll()` | Measure all qubits |

**Utility methods**:

- `depth()` — circuit depth
- `countGates()` — gate histogram
- `toQASM()` — OpenQASM 2.0 export
- `toJSON()` / `Circuit.fromJSON()` — serialization

### `run(circuit, shots?)`

Execute a circuit. Returns `{ success, counts, probabilities, statevector }`.

### Built-in Circuits

```typescript
import { bellState, ghzState, qft, grover, wState } from '@abirqu/js';

bellState()          // 2-qubit Bell state
ghzState(n)          // n-qubit GHZ state
qft(n)               // n-qubit Quantum Fourier Transform
grover(n, target)    // Grover's search
wState(n)            // n-qubit W state
```

## Development

```bash
npm install
npm run build
npm test
```

## License

MIT — Copyright 2026 Abir Maheshwari
