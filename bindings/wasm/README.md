# AbirQu WebAssembly

Run AbirQu quantum circuits directly in the browser or Node.js using
[Pyodide](https://pyodide.org) (Python compiled to WebAssembly).

## Browser Usage

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
</head>
<body>
    <script type="module">
        import { AbirQu } from './abirqu_wasm.js';

        const q = await AbirQu.init();
        const result = await q.runCircuit(`
            from abirqu import Circuit
            circuit = Circuit(2)
            circuit.h(0)
            circuit.cnot(0, 1)
        `, shots=1000);

        console.log(result.counts);  // {'00': ~500, '11': ~500}
    </script>
</body>
</html>
```

## Node.js Usage

```javascript
import { AbirQu } from '@abirqu/wasm';

const q = await AbirQu.init();
const result = await q.run(`
    from abirqu.library import ghz_circuit
    from abirqu.primitives import QuantumRun

    circuit = ghz_circuit(num_qubits=4)
    circuit.measure_all()
    result = QuantumRun(circuit, shots=1000)
    print(result.counts)
`);

console.log(result.stdout);
```

## API Reference

### `AbirQu.init(options?)`
Initialize the WASM runtime and install AbirQu.

- `options.pyodideCdn` — Custom Pyodide CDN URL
- `options.onProgress` — Progress callback function

### `abirqu.run(code, options?)`
Execute Python code with AbirQu available.

- `code` — Python source code
- `options.captureOutput` — Capture stdout/stderr (default: true)

Returns: `{ stdout, stderr, result, error }`

### `abirqu.runCircuit(circuitCode, shots?)`
Run a quantum circuit and get measurement results.

- `circuitCode` — Python code creating a `Circuit` named `circuit`
- `shots` — Number of measurement shots (default: 1000)

Returns: `{ counts: { '00': 500, '11': 500 }, error }`

### `abirqu.getVersion()`
Returns the loaded AbirQu version string.

### `abirqu.listModules()`
Returns a list of available AbirQu module names.

## Features

- Full Python SDK in the browser
- No server required — all simulation is local
- Statevector and measurement simulation
- Hardware-efficient ansatz patterns
- 200+ algorithm templates
- Quantum chemistry (VQE)
- Quantum error correction
- Shor's algorithm
- Grover's search

## Limitations

- First load takes ~5-10 seconds (downloading Pyodide + AbirQu)
- Python execution is slower than native (~2-5x)
- No access to hardware backends (D-Wave, IBM, etc.)
- Some numpy operations may be slower in WASM

## License

MIT License — same as AbirQu SDK.
