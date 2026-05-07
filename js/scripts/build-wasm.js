/**
 * WebAssembly build script for AbirQu
 * Builds WASM modules from C/C++ core using Emscripten
 * 
 * Prerequisites:
 * - Emscripten SDK installed (https://emscripten.org/docs/getting_started/downloads.html)
 * - Run: source /path/to/emsdk/emsdk_env.sh
 * 
 * Usage: node scripts/build-wasm.js
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { resolve } from 'path';

console.log('=== AbirQu WebAssembly Build ===\n');

const WASM_OUTPUT_DIR = resolve('build/wasm');
const JS_SRC_DIR = resolve('src');

// Check if Emscripten is available
function checkEmscripten() {
    try {
        execSync('emcc --version', { stdio: 'pipe' });
        return true;
    } catch (e) {
        return false;
    }
}

// Build pure JavaScript bundle (WASM-ready)
function buildPureJS() {
    console.log('Building pure JavaScript bundle (WASM-compatible)...');
    
    // Create a bundled JS file that can be loaded in browsers
    const bundleContent = `// AbirQu Quantum SDK - WASM-ready Bundle
// Auto-generated: ${new Date().toISOString()}

export { default as QuantumCircuit } from '../src/circuits/circuit.js';
export { default as QuantumGates } from '../src/circuits/gates.js';
export { default as QuantumSimulator } from '../src/simulation/simulator.js';
export { default as ComplexMath } from '../complex-math.js';
`;
    
    if (!existsSync(WASM_OUTPUT_DIR)) {
        mkdirSync(WASM_OUTPUT_DIR, { recursive: true });
    }
    
    const bundlePath = resolve(WASM_OUTPUT_DIR, 'abirqu-bundle.js');
    writeFileSync(bundlePath, bundleContent);
    console.log(`✓ JavaScript bundle created: ${bundlePath}`);
    
    return true;
}

// Build WASM module from C core (if exists)
function buildWasmModule() {
    if (!checkEmscripten()) {
        console.log('⚠ Emscripten not found. Installing Emscripten:');
        console.log('  See: https://emscripten.org/docs/getting_started/downloads.html');
        console.log('\nFalling back to pure JavaScript build...\n');
        return buildPureJS();
    }

    console.log('✓ Emscripten found');
    
    // If there's a C core, compile it
    const cCore = resolve('..', 'core', 'c_core.c');
    if (existsSync(cCore)) {
        console.log('Building WASM from C core...');
        try {
            execSync(`emcc ${cCore} -o ${WASM_OUTPUT_DIR}/abirqu.js -s WASM=1 -s EXPORTED_FUNCTIONS='["_malloc","_free"]' -s EXPORTED_RUNTIME_METHODS='["ccall","cwrap"]' -O3`, {
                stdio: 'inherit'
            });
            console.log('✓ WASM module built successfully');
        } catch (e) {
            console.log('⚠ C core build failed, using pure JS');
            return buildPureJS();
        }
    } else {
        return buildPureJS();
    }
}

// Create package for browser use
function createBrowserPackage() {
    console.log('\nCreating browser package...');
    
    const htmlExample = `<!DOCTYPE html>
<html>
<head>
    <title>AbirQu Quantum SDK - Browser Demo</title>
</head>
<body>
    <h1>AbirQu Quantum SDK - Browser Demo</h1>
    <div id="output"></div>
    
    <script type="module">
        import { QuantumCircuit, QuantumSimulator } from './abirqu-bundle.js';
        
        const circuit = new QuantumCircuit(2);
        circuit.h(0);
        circuit.cnot(0, 1);
        
        const sim = new QuantumSimulator();
        const result = sim.simulate(circuit);
        
        document.getElementById('output').innerHTML = 
            '<h3>Bell State Probabilities:</h3>' +
            '<pre>' + JSON.stringify(result.probabilities, null, 2) + '</pre>';
    </script>
</body>
</html>`;
    
    const htmlPath = resolve(WASM_OUTPUT_DIR, 'index.html');
    writeFileSync(htmlPath, htmlExample);
    console.log(`✓ Browser demo created: ${htmlPath}`);
}

// Main build process
function main() {
    try {
        buildWasmModule();
        createBrowserPackage();
        
        console.log('\n=== Build Complete ===');
        console.log(`Output directory: ${WASM_OUTPUT_DIR}`);
        console.log('\nTo use in Node.js:');
        console.log('  import { QuantumCircuit } from "abirqu/js/src/index.js";');
        console.log('\nTo use in browser:');
        console.log('  Copy build/wasm/ to your web server');
        console.log('  Open index.html in browser');
        
    } catch (error) {
        console.error('Build failed:', error.message);
        process.exit(1);
    }
}

main();
