// Auto-generated AbirQu Go bindings — do not edit manually.
package abirqu

/*
#cgo LDFLAGS: -labirqu_core
#include <stdlib.h>
#include "abirqu.h"
*/
"C"
import (
    "C"
    "unsafe"
)

// Create a new simulator for `num_qubits` qubits.
// Returns a non-null opaque handle.  Must be freed with
// `abirqu_simulator_destroy`.
func abirqu_simulator_create(u32 unsafe.Pointer) uintptr {
    return uintptr(C.abirqu_simulator_create(u32))
}

// Free a handle created by `abirqu_simulator_create`.  Passing NULL is safe.
func abirqu_simulator_destroy(AbirQuSimulator unsafe.Pointer) {
    C.abirqu_simulator_destroy(AbirQuSimulator)
}

// Reset the simulator to |0…0⟩ without reallocating.
func abirqu_simulator_reset(AbirQuSimulator unsafe.Pointer) {
    C.abirqu_simulator_reset(AbirQuSimulator)
}

// Return the number of qubits this simulator was created with.
func abirqu_num_qubits(AbirQuSimulator unsafe.Pointer) uint32 {
    return uint32(C.abirqu_num_qubits(AbirQuSimulator))
}

// Return the Hilbert space dimension (2^num_qubits).
func abirqu_hilbert_dim(AbirQuSimulator unsafe.Pointer) uintptr {
    return uintptr(C.abirqu_hilbert_dim(AbirQuSimulator))
}

func abirqu_h(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_h(AbirQuSimulator, u32)
}

func abirqu_x(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_x(AbirQuSimulator, u32)
}

func abirqu_y(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_y(AbirQuSimulator, u32)
}

func abirqu_z(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_z(AbirQuSimulator, u32)
}

func abirqu_s(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_s(AbirQuSimulator, u32)
}

func abirqu_t(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_t(AbirQuSimulator, u32)
}

func abirqu_rx(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer, f64 unsafe.Pointer) {
    C.abirqu_rx(AbirQuSimulator, u32, f64)
}

func abirqu_ry(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer, f64 unsafe.Pointer) {
    C.abirqu_ry(AbirQuSimulator, u32, f64)
}

func abirqu_rz(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer, f64 unsafe.Pointer) {
    C.abirqu_rz(AbirQuSimulator, u32, f64)
}

func abirqu_cnot(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_cnot(AbirQuSimulator, u32, u32)
}

func abirqu_cz(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_cz(AbirQuSimulator, u32, u32)
}

func abirqu_swap(AbirQuSimulator unsafe.Pointer, u32 unsafe.Pointer, u32 unsafe.Pointer) {
    C.abirqu_swap(AbirQuSimulator, u32, u32)
}

// Execute a batch of gates described by the `gates` array of length `n_gates`.
// 
// # Safety
// `handle` must be a valid non-null pointer from `abirqu_simulator_create`.
// `gates`  must point to at least `n_gates` consecutive `AbirQuGate` values.
func abirqu_run_circuit(AbirQuSimulator unsafe.Pointer, *const AbirQuGate unsafe.Pointer, usize unsafe.Pointer) {
    C.abirqu_run_circuit(AbirQuSimulator, *const AbirQuGate, usize)
}

// Copy measurement probabilities into caller-supplied buffer `out_probs`.
// 
// `out_probs` must have room for at least `abirqu_hilbert_dim(handle)` doubles.
// Returns the number of values written, or 0 on error.
func abirqu_get_probabilities(AbirQuSimulator unsafe.Pointer, *mut f64 unsafe.Pointer) uintptr {
    return uintptr(C.abirqu_get_probabilities(AbirQuSimulator, *mut f64))
}

// Copy the statevector into caller-supplied buffers `out_re` and `out_im`.
// 
// Both buffers must have room for at least `abirqu_hilbert_dim(handle)` doubles.
// Returns the number of complex amplitudes written, or 0 on error.
func abirqu_get_statevector(AbirQuSimulator unsafe.Pointer, *mut f64 unsafe.Pointer, *mut f64 unsafe.Pointer) uintptr {
    return uintptr(C.abirqu_get_statevector(AbirQuSimulator, *mut f64, *mut f64))
}
