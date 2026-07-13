/* Auto-generated AbirQu C API header — do not edit manually. */
#ifndef ABIRQU_H
#define ABIRQU_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Opaque handle */
typedef struct AbirQuSimulator* AbirQuSimulator;

/* Create a new simulator for `num_qubits` qubits. */
/* Returns a non-null opaque handle.  Must be freed with */
/* `abirqu_simulator_destroy`. */
AbirQuSimulator abirqu_simulator_create(num_qubits u32);

/* Free a handle created by `abirqu_simulator_create`.  Passing NULL is safe. */
void abirqu_simulator_destroy(handle AbirQuSimulator);

/* Reset the simulator to |0…0⟩ without reallocating. */
void abirqu_simulator_reset(handle AbirQuSimulator);

/* Return the number of qubits this simulator was created with. */
u32 abirqu_num_qubits(handle AbirQuSimulator);

/* Return the Hilbert space dimension (2^num_qubits). */
usize abirqu_hilbert_dim(handle AbirQuSimulator);

void abirqu_h(h AbirQuSimulator, q u32);

void abirqu_x(h AbirQuSimulator, q u32);

void abirqu_y(h AbirQuSimulator, q u32);

void abirqu_z(h AbirQuSimulator, q u32);

void abirqu_s(h AbirQuSimulator, q u32);

void abirqu_t(h AbirQuSimulator, q u32);

void abirqu_rx(h AbirQuSimulator, q u32, angle f64);

void abirqu_ry(h AbirQuSimulator, q u32, angle f64);

void abirqu_rz(h AbirQuSimulator, q u32, angle f64);

void abirqu_cnot(h AbirQuSimulator, ctrl u32, tgt u32);

void abirqu_cz(h AbirQuSimulator, ctrl u32, tgt u32);

void abirqu_swap(h AbirQuSimulator, q0 u32, q1 u32);

/* Execute a batch of gates described by the `gates` array of length `n_gates`. */
/*  */
/* # Safety */
/* `handle` must be a valid non-null pointer from `abirqu_simulator_create`. */
/* `gates`  must point to at least `n_gates` consecutive `AbirQuGate` values. */
void abirqu_run_circuit(handle AbirQuSimulator, gates *const AbirQuGate, n_gates usize);

/* Copy measurement probabilities into caller-supplied buffer `out_probs`. */
/*  */
/* `out_probs` must have room for at least `abirqu_hilbert_dim(handle)` doubles. */
/* Returns the number of values written, or 0 on error. */
usize abirqu_get_probabilities(handle AbirQuSimulator, out_probs *mut f64);

/* Copy the statevector into caller-supplied buffers `out_re` and `out_im`. */
/*  */
/* Both buffers must have room for at least `abirqu_hilbert_dim(handle)` doubles. */
/* Returns the number of complex amplitudes written, or 0 on error. */
usize abirqu_get_statevector(handle AbirQuSimulator, out_re *mut f64, out_im *mut f64);

#ifdef __cplusplus
}
#endif

#endif /* ABIRQU_H */
