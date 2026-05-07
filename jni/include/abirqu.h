/**
 * AbirQu C API Header
 * Use this header to link against liabirqu_core.so
 */

#ifndef ABIRQU_H
#define ABIRQU_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Opaque handle type
typedef struct AbirQuSimulator AbirQuSimulator;

// Gate type constants
#define AQ_GATE_H    0
#define AQ_GATE_X    1
#define AQ_GATE_Y    2
#define AQ_GATE_Z    3
#define AQ_GATE_S    4
#define AQ_GATE_T    5
#define AQ_GATE_CNOT 6
#define AQ_GATE_CZ   7
#define AQ_GATE_RX   8
#define AQ_GATE_RY   9
#define AQ_GATE_RZ   10
#define AQ_GATE_SWAP 11

// Gate descriptor for batch execution
typedef struct {
    uint8_t  gate_type;   // AQ_GATE_*
    uint8_t  _pad[3];      // Alignment padding
    uint32_t ctrl;          // Primary qubit or control qubit
    uint32_t target;        // Target qubit (2-qubit gates)
    double   param;         // Rotation angle in radians (Rx/Ry/Rz)
} AbirQuGate;

// Lifecycle
AbirQuSimulator* abirqu_simulator_create(uint32_t num_qubits);
void abirqu_simulator_destroy(AbirQuSimulator* handle);
void abirqu_simulator_reset(AbirQuSimulator* handle);

// Metadata
uint32_t abirqu_num_qubits(AbirQuSimulator* handle);
size_t abirqu_hilbert_dim(AbirQuSimulator* handle);

// Single gates
void abirqu_h(AbirQuSimulator* handle, uint32_t q);
void abirqu_x(AbirQuSimulator* handle, uint32_t q);
void abirqu_y(AbirQuSimulator* handle, uint32_t q);
void abirqu_z(AbirQuSimulator* handle, uint32_t q);
void abirqu_s(AbirQuSimulator* handle, uint32_t q);
void abirqu_t(AbirQuSimulator* handle, uint32_t q);
void abirqu_rx(AbirQuSimulator* handle, uint32_t q, double angle);
void abirqu_ry(AbirQuSimulator* handle, uint32_t q, double angle);
void abirqu_rz(AbirQuSimulator* handle, uint32_t q, double angle);
void abirqu_cnot(AbirQuSimulator* handle, uint32_t ctrl, uint32_t target);
void abirqu_cz(AbirQuSimulator* handle, uint32_t ctrl, uint32_t target);
void abirqu_swap(AbirQuSimulator* handle, uint32_t q0, uint32_t q1);

// Batch execution
void abirqu_run_circuit(AbirQuSimulator* handle, const AbirQuGate* gates, size_t n_gates);

// State readout
size_t abirqu_get_probabilities(AbirQuSimulator* handle, double* out_probs);
size_t abirqu_get_statevector(AbirQuSimulator* handle, double* out_re, double* out_im);

#ifdef __cplusplus
}
#endif

#endif // ABIRQU_H
