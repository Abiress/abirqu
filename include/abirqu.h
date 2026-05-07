/**
 * abirqu.h  —  AbirQu Quantum SDK  v0.1.0
 * ==========================================
 * Stable C ABI for libabirqu_core.so / abirqu_core.dll
 *
 * Usage (Linux / macOS):
 *   gcc -o my_program my_program.c -L/path/to/libabirqu_core -labirqu_core -lm
 *   # or with rpath:
 *   gcc -o my_program my_program.c \
 *       -L$(pwd)/target/release -labirqu_core \
 *       -Wl,-rpath,$(pwd)/target/release -lm
 *
 * Usage (Windows / MSVC):
 *   cl my_program.c abirqu_core.lib
 *
 * Memory model
 * ------------
 *   abirqu_simulator_create()  — allocates heap memory, returns opaque handle
 *   abirqu_simulator_destroy() — frees the handle (safe to call with NULL)
 *   All other functions borrow the handle; they do NOT transfer ownership.
 *   Probability / statevector data is written into caller-supplied buffers.
 *
 * Copyright 2026 Abir Maheshwari — MIT License
 */

#ifndef ABIRQU_H
#define ABIRQU_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

/* ────────────────────────────────────────────────────────────────────────────
 * Opaque handle
 * ──────────────────────────────────────────────────────────────────────────── */

/** Opaque pointer to the internal Rust Simulator object. */
typedef void* AbirQuSimulator;

/* ────────────────────────────────────────────────────────────────────────────
 * Gate type constants  (mirror of _GATE_MAP in abirqu/simulator.py)
 * ──────────────────────────────────────────────────────────────────────────── */

#define AQ_GATE_H    ((uint8_t)0)
#define AQ_GATE_X    ((uint8_t)1)
#define AQ_GATE_Y    ((uint8_t)2)
#define AQ_GATE_Z    ((uint8_t)3)
#define AQ_GATE_S    ((uint8_t)4)
#define AQ_GATE_T    ((uint8_t)5)
#define AQ_GATE_CNOT ((uint8_t)6)
#define AQ_GATE_CZ   ((uint8_t)7)
#define AQ_GATE_RX   ((uint8_t)8)
#define AQ_GATE_RY   ((uint8_t)9)
#define AQ_GATE_RZ   ((uint8_t)10)
#define AQ_GATE_SWAP ((uint8_t)11)

/* ────────────────────────────────────────────────────────────────────────────
 * Gate descriptor for batch execution
 * ──────────────────────────────────────────────────────────────────────────── */

/**
 * One gate in a circuit batch.
 *
 * Fields
 * ------
 * gate_type  Gate constant from AQ_GATE_* above.
 * ctrl       Primary qubit index (also the control qubit for 2-qubit gates).
 * target     Target qubit index (used only by CNOT, CZ, SWAP).
 * param      Rotation angle in radians (used only by RX, RY, RZ).
 */
typedef struct {
    uint8_t  gate_type;
    uint8_t  _pad[3];      /* alignment padding — do not use */
    uint32_t ctrl;
    uint32_t target;
    double   param;
} AbirQuGate;

/* ────────────────────────────────────────────────────────────────────────────
 * Lifecycle
 * ──────────────────────────────────────────────────────────────────────────── */

/**
 * Allocate a new simulator for `num_qubits` qubits.
 *
 * The initial state is |0…0⟩.
 * Returns a non-null handle.  Must be freed with abirqu_simulator_destroy().
 */
AbirQuSimulator abirqu_simulator_create(uint32_t num_qubits);

/**
 * Free a handle previously obtained from abirqu_simulator_create.
 * Passing NULL is safe (no-op).
 */
void abirqu_simulator_destroy(AbirQuSimulator handle);

/**
 * Reset the simulator to |0…0⟩ without reallocating.
 * Useful for running many circuits reusing the same object.
 */
void abirqu_simulator_reset(AbirQuSimulator handle);

/** Return the number of qubits this simulator was created with. */
uint32_t abirqu_num_qubits(AbirQuSimulator handle);

/** Return the Hilbert-space dimension: 2^num_qubits. */
size_t abirqu_hilbert_dim(AbirQuSimulator handle);

/* ────────────────────────────────────────────────────────────────────────────
 * Single-gate API
 * ──────────────────────────────────────────────────────────────────────────── */

void abirqu_h   (AbirQuSimulator handle, uint32_t q);
void abirqu_x   (AbirQuSimulator handle, uint32_t q);
void abirqu_y   (AbirQuSimulator handle, uint32_t q);
void abirqu_z   (AbirQuSimulator handle, uint32_t q);
void abirqu_s   (AbirQuSimulator handle, uint32_t q);
void abirqu_t   (AbirQuSimulator handle, uint32_t q);
void abirqu_rx  (AbirQuSimulator handle, uint32_t q, double angle);
void abirqu_ry  (AbirQuSimulator handle, uint32_t q, double angle);
void abirqu_rz  (AbirQuSimulator handle, uint32_t q, double angle);
void abirqu_cnot(AbirQuSimulator handle, uint32_t ctrl, uint32_t target);
void abirqu_cz  (AbirQuSimulator handle, uint32_t ctrl, uint32_t target);
void abirqu_swap(AbirQuSimulator handle, uint32_t q0,   uint32_t q1);

/* ────────────────────────────────────────────────────────────────────────────
 * Batch execution
 * ──────────────────────────────────────────────────────────────────────────── */

/**
 * Execute a batch of gates.
 *
 * @param handle   Valid simulator handle (must not be NULL).
 * @param gates    Array of at least n_gates AbirQuGate descriptors.
 * @param n_gates  Number of gates to execute.
 */
void abirqu_run_circuit(
    AbirQuSimulator   handle,
    const AbirQuGate *gates,
    size_t            n_gates
);

/* ────────────────────────────────────────────────────────────────────────────
 * State readout
 * ──────────────────────────────────────────────────────────────────────────── */

/**
 * Copy measurement probabilities into out_probs.
 *
 * @param handle    Valid simulator handle.
 * @param out_probs Buffer of at least abirqu_hilbert_dim(handle) doubles.
 * @return          Number of values written (abirqu_hilbert_dim(handle)),
 *                  or 0 on error.
 */
size_t abirqu_get_probabilities(
    AbirQuSimulator handle,
    double         *out_probs
);

/**
 * Copy the full statevector into out_re and out_im.
 *
 * @param handle   Valid simulator handle.
 * @param out_re   Buffer of at least abirqu_hilbert_dim(handle) doubles (real parts).
 * @param out_im   Buffer of at least abirqu_hilbert_dim(handle) doubles (imag parts).
 * @return         Number of complex amplitudes written, or 0 on error.
 */
size_t abirqu_get_statevector(
    AbirQuSimulator handle,
    double         *out_re,
    double         *out_im
);

#ifdef __cplusplus
}
#endif

#endif /* ABIRQU_H */
