# AbirQu JavaScript/Node.js SDK

Pure Quantum SDK for JavaScript and Node.js with WebAssembly support.

## Features

- **Full Quantum Circuit Simulation** - State vector simulation up to 20+ qubits
- **Standard Gate Set** - All common quantum gates (X, Y, Z, H, S, T, RX, RY, RZ, CNOT, CZ, Toffoli)
- **Measurement & Shot-based Simulation** - Run circuits with multiple shots
- **Algorithm Implementations** - Bell states, GHZ states, teleportation
- **WebAssembly Ready** - Build WASM modules for browser and Node.js
- **TypeScript Compatible** - Full TypeScript definitions included

## Installation

```bash
cd js/
npm install
```

## Usage

### Basic Circuit

```javascript
import { QuantumCircuit, QuantumSimulator } from 'abirqu';

// Create Bell state
const circuit = new QuantumCircuit(2);
circuit.h(0);
circuit.cnot(0, 1);

// Simulate
const sim = new QuantumSimulator();
const result = sim.simulate(circuit);

console.log('Probabilities:', result.probabilities);
// [0.5, 0, 0, 0.5]
```

### Run Shots

```javascript
const shotsResult = sim.runShots(circuit, 1000);
console.log(shotsResult.counts);
// { '00': 502, '11': 498 }
```

### Create Custom Circuits

```javascript
const circuit = new QuantumCircuit(3);
circuit.h(0);
circuit.cnot(0, 1);
circuit.rx(2, Math.PI/4);
circuit.cz(1, 2);

const result = sim.simulate(circuit);
```

## Building WebAssembly

```bash
npm run build
```

This creates WASM modules in `build/` directory.

## Testing

```bash
npm test
```

## Examples

Run example circuits:

```bash
npm run examples
```

## API Reference

### QuantumCircuit

- `new QuantumCircuit(numQubits)` - Create new circuit
- `h(qubit)`, `x(qubit)`, `y(qubit)`, `z(qubit)` - Single qubit gates
- `rx(qubit, theta)`, `ry(qubit, theta)`, `rz(qubit, theta)` - Rotation gates
- `cnot(control, target)`, `cz(control, target)` - Two-qubit gates
- `simulate()` - Run simulation
- `measure(qubit)` - Measure qubit
- `getProbabilities()` - Get measurement probabilities

### QuantumSimulator

- `simulate(circuit)` - Simulate circuit, return state vector
- `runShots(circuit, shots)` - Run multiple shots
- `expectationValue(circuit, pauli, qubits)` - Calculate expectation

## Comparison with Python SDK

| Feature | Python | JavaScript |
|---------|--------|------------|
| Circuit Simulation | ✓ | ✓ |
| State Vector | ✓ | ✓ |
| Gate Set | ✓ | ✓ |
| Algorithms | ✓ | ✓ |
| WASM Build | - | ✓ |
| Browser Ready | - | ✓ |

## Performance

- 10 qubits: ~1ms simulation
- 15 qubits: ~50ms simulation
- 20 qubits: ~2s simulation

## License

MIT

## Author

Abir Datta <abir.datta.pro@gmail.com>
