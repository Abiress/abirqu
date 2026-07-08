/**
 * AbirQu WebAssembly — JavaScript API
 * =====================================
 *
 * Run AbirQu quantum circuits in the browser or Node.js
 * using Pyodide (Python compiled to WebAssembly).
 *
 * Usage:
 *   import { AbirQu } from '@abirqu/wasm';
 *   const q = await AbirQu.init();
 *   const result = await q.run('from abirqu import Circuit; ...');
 */

const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js';

class AbirQuWASM {
    constructor() {
        this.pyodide = null;
        this.ready = false;
    }

    /**
     * Initialize the AbirQu WASM runtime.
     * @param {Object} options - Configuration options
     * @param {string} options.pyodideCdn - Custom Pyodide CDN URL
     * @param {Function} options.onProgress - Progress callback
     * @returns {Promise<AbirQuWASM>}
     */
    static async init(options = {}) {
        const instance = new AbirQuWASM();
        const { pyodideCdn = PYODIDE_CDN, onProgress = () => {} } = options;

        onProgress('Loading Pyodide runtime...');

        // Load Pyodide script if not already loaded
        if (typeof window !== 'undefined' && !window.loadPyodide) {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = pyodideCdn;
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }

        // Initialize Pyodide
        if (typeof window !== 'undefined') {
            instance.pyodide = await window.loadPyodide();
        } else {
            // Node.js
            const pyodide = await import(pyodideCdn);
            instance.pyodide = await pyodide.loadPyodide();
        }

        onProgress('Installing AbirQu SDK...');

        // Install abirqu
        await instance.pyodide.loadPackage('micropip');
        await instance.pyodide.runPythonAsync(`
            import micropip
            await micropip.install('abirqu')
        `);

        instance.ready = true;
        onProgress('Ready');

        return instance;
    }

    /**
     * Execute Python code with AbirQu available.
     * @param {string} code - Python code to execute
     * @param {Object} options - Execution options
     * @returns {Promise<Object>} - { stdout, stderr, result, error }
     */
    async run(code, options = {}) {
        if (!this.ready) throw new Error('Runtime not initialized. Call AbirQu.init() first.');

        const { captureOutput = true } = options;
        const result = { stdout: '', stderr: '', result: null, error: null };

        if (captureOutput) {
            this.pyodide.runPython(`
import sys
from io import StringIO
_stdout_capture = StringIO()
_stderr_capture = StringIO()
sys.stdout = _stdout_capture
sys.stderr = _stderr_capture
`);
        }

        try {
            await this.pyodide.runPythonAsync(code);
            result.result = true;
        } catch (e) {
            result.error = e.message;
        } finally {
            if (captureOutput) {
                result.stdout = this.pyodide.runPython('_stdout_capture.getvalue()');
                result.stderr = this.pyodide.runPython('_stderr_capture.getvalue()');
                this.pyodide.runPython('sys.stdout = sys.__stdout__; sys.stderr = sys.__stderr__');
            }
        }

        return result;
    }

    /**
     * Run a quantum circuit and return measurement results.
     * @param {string} circuitCode - Python code creating a Circuit named 'circuit'
     * @param {number} shots - Number of measurement shots
     * @returns {Promise<Object>} - { counts, error }
     */
    async runCircuit(circuitCode, shots = 1000) {
        const code = `
${circuitCode}
circuit.measure_all()
from abirqu.primitives import QuantumRun
_result = QuantumRun(circuit, shots=${shots})
`;
        const result = await this.run(code);
        if (result.error) return { counts: {}, error: result.error };

        const counts = this.pyodide.runPython('dict(_result.counts)');
        return { counts, error: null };
    }

    /**
     * Get the loaded AbirQu version.
     * @returns {string}
     */
    getVersion() {
        return this.pyodide.runPython('import abirqu; abirqu.__version__');
    }

    /**
     * List available AbirQu modules.
     * @returns {string[]}
     */
    listModules() {
        return this.pyodide.runPython(`
import abirqu
[name for name in dir(abirqu) if not name.startswith('_')]
`);
    }
}

// Browser global
if (typeof window !== 'undefined') {
    window.AbirQu = AbirQuWASM;
}

// Node.js module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AbirQu: AbirQuWASM, AbirQuWASM };
}

export { AbirQuWASM };
export default AbirQuWASM;
