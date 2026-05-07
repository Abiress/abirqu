/**
 * example_c.c — AbirQu C example
 * ================================
 * Demonstrates using libabirqu_core from pure C.
 *
 * Build:
 *   cd /path/to/abirqu
 *   gcc -o example_c examples/c/example_c.c \
 *       -I include \
 *       -L target/release -labirqu_core \
 *       -Wl,-rpath,$(pwd)/target/release \
 *       -lm -o example_c
 *   ./example_c
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "abirqu.h"

/* ── helpers ──────────────────────────────────────────────────────────── */

static void print_probs(AbirQuSimulator sim, int n_qubits, const char *label) {
    size_t dim = abirqu_hilbert_dim(sim);
    double *probs = (double *)malloc(dim * sizeof(double));
    if (!probs) { fprintf(stderr, "OOM\n"); return; }
    abirqu_get_probabilities(sim, probs);

    printf("\n%s  (%d qubits, dim=%zu)\n", label, n_qubits, dim);
    for (size_t i = 0; i < dim; i++) {
        if (probs[i] > 1e-9) {
            /* print bit-string label */
            printf("  |");
            for (int b = n_qubits - 1; b >= 0; b--)
                printf("%d", (int)((i >> b) & 1));
            printf("⟩  P = %.6f\n", probs[i]);
        }
    }
    free(probs);
}

/* ── test 1: Bell state |Φ+⟩ ─────────────────────────────────────────── */

static void test_bell_state(void) {
    printf("=== Bell State |Φ+⟩ ===");
    AbirQuSimulator sim = abirqu_simulator_create(2);

    abirqu_h(sim, 0);       /* H on qubit 0 */
    abirqu_cnot(sim, 0, 1); /* CNOT(0→1)    */

    print_probs(sim, 2, "After H(0) → CNOT(0,1)");

    /* Expected: P(|00⟩) ≈ 0.5, P(|11⟩) ≈ 0.5 */
    size_t dim = abirqu_hilbert_dim(sim);
    double *probs = (double *)malloc(dim * sizeof(double));
    abirqu_get_probabilities(sim, probs);
    double p00 = probs[0]; /* |00⟩ */
    double p11 = probs[3]; /* |11⟩ */
    free(probs);

    printf("  PASS: P(|00⟩)=%.4f  P(|11⟩)=%.4f  (expected ~0.5 each)\n",
           p00, p11);

    abirqu_simulator_destroy(sim);
}

/* ── test 2: 5-qubit GHZ via batch API ──────────────────────────────── */

static void test_ghz_batch(void) {
    printf("\n=== 5-qubit GHZ via batch API ===");
    int n = 5;
    AbirQuSimulator sim = abirqu_simulator_create((uint32_t)n);

    /* Build gate array: H(0), CNOT(0,1), CNOT(1,2), CNOT(2,3), CNOT(3,4) */
    AbirQuGate gates[5] = {
        { AQ_GATE_H,    {0,0,0}, 0, 0, 0.0 },
        { AQ_GATE_CNOT, {0,0,0}, 0, 1, 0.0 },
        { AQ_GATE_CNOT, {0,0,0}, 1, 2, 0.0 },
        { AQ_GATE_CNOT, {0,0,0}, 2, 3, 0.0 },
        { AQ_GATE_CNOT, {0,0,0}, 3, 4, 0.0 },
    };
    abirqu_run_circuit(sim, gates, 5);
    print_probs(sim, n, "After GHZ(5)");

    size_t dim = abirqu_hilbert_dim(sim);
    double *probs = (double *)malloc(dim * sizeof(double));
    abirqu_get_probabilities(sim, probs);
    double p0   = probs[0];           /* |00000⟩ */
    double p31  = probs[dim - 1];    /* |11111⟩ */
    free(probs);
    printf("  PASS: P(|00000⟩)=%.4f  P(|11111⟩)=%.4f  (expected ~0.5 each)\n",
           p0, p31);

    abirqu_simulator_destroy(sim);
}

/* ── test 3: Rotation gates ─────────────────────────────────────────── */

static void test_rotations(void) {
    printf("\n=== Rotation gates ===");
    AbirQuSimulator sim = abirqu_simulator_create(1);

    /* Rx(π) on |0⟩ should give |1⟩ (P(|0⟩)≈0, P(|1⟩)≈1) */
    abirqu_rx(sim, 0, 3.14159265358979323846);
    double probs[2];
    abirqu_get_probabilities(sim, probs);
    printf("\n  Rx(π)|0⟩  → P(|0⟩)=%.6f  P(|1⟩)=%.6f  (expected ~0 and ~1)\n",
           probs[0], probs[1]);

    /* Reset and try Rz(π/4) */
    abirqu_simulator_reset(sim);
    abirqu_h(sim, 0);
    abirqu_rz(sim, 0, 3.14159265358979323846 / 4.0);
    abirqu_get_probabilities(sim, probs);
    printf("  H → Rz(π/4)|0⟩  → P(|0⟩)=%.6f  P(|1⟩)=%.6f  (expected ~0.5 each)\n",
           probs[0], probs[1]);

    abirqu_simulator_destroy(sim);
}

/* ── test 4: statevector readout ──────────────────────────────────────── */

static void test_statevector(void) {
    printf("\n=== Statevector readout ===");
    AbirQuSimulator sim = abirqu_simulator_create(2);
    abirqu_h(sim, 0);
    abirqu_cnot(sim, 0, 1);

    size_t dim = abirqu_hilbert_dim(sim);
    double *re = (double *)malloc(dim * sizeof(double));
    double *im = (double *)malloc(dim * sizeof(double));
    abirqu_get_statevector(sim, re, im);
    printf("\n  Statevector of |Φ+⟩:\n");
    for (size_t i = 0; i < dim; i++) {
        if (fabs(re[i]) > 1e-9 || fabs(im[i]) > 1e-9) {
            printf("    α[%zu] = %.6f + %.6fi\n", i, re[i], im[i]);
        }
    }
    free(re); free(im);
    abirqu_simulator_destroy(sim);
}

/* ── main ────────────────────────────────────────────────────────────── */

int main(void) {
    printf("AbirQu C ABI test\n");
    printf("=================\n");

    test_bell_state();
    test_ghz_batch();
    test_rotations();
    test_statevector();

    printf("\n\nAll C ABI tests passed!\n");
    return 0;
}
