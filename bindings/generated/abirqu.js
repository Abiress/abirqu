// Auto-generated AbirQu JavaScript bindings — do not edit manually.
const ffi = require("ffi-napi");
const ref = require("ref-napi");

const AbirQuSimulator = ref.types.void *;

const lib = ffi.Library(__dirname + "/../target/release/libabirqu_core", {
    abirqu_simulator_create: ["AbirQuSimulator", [pointer]],
    abirqu_simulator_destroy: ["void", [pointer]],
    abirqu_simulator_reset: ["void", [pointer]],
    abirqu_num_qubits: ["uint32", [pointer]],
    abirqu_hilbert_dim: ["size_t", [pointer]],
    abirqu_h: ["void", [pointer, pointer]],
    abirqu_x: ["void", [pointer, pointer]],
    abirqu_y: ["void", [pointer, pointer]],
    abirqu_z: ["void", [pointer, pointer]],
    abirqu_s: ["void", [pointer, pointer]],
    abirqu_t: ["void", [pointer, pointer]],
    abirqu_rx: ["void", [pointer, pointer, pointer]],
    abirqu_ry: ["void", [pointer, pointer, pointer]],
    abirqu_rz: ["void", [pointer, pointer, pointer]],
    abirqu_cnot: ["void", [pointer, pointer, pointer]],
    abirqu_cz: ["void", [pointer, pointer, pointer]],
    abirqu_swap: ["void", [pointer, pointer, pointer]],
    abirqu_run_circuit: ["void", [pointer, pointer, pointer]],
    abirqu_get_probabilities: ["size_t", [pointer, pointer]],
    abirqu_get_statevector: ["size_t", [pointer, pointer, pointer]],
});

module.exports = lib;
