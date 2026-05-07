/**
 * example_cpp.cpp — AbirQu C++ example
 * ======================================
 * Demonstrates using libabirqu_core from C++17 via the C ABI.
 * Wraps the raw C API in a modern RAII class for convenience.
 *
 * Build:
 *   cd /path/to/abirqu
 *   g++ -std=c++17 -o example_cpp examples/cpp/example_cpp.cpp \
 *       -I include \
 *       -L target/release -labirqu_core \
 *       -Wl,-rpath,$(pwd)/target/release \
 *       -lm
 *   ./example_cpp
 */

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <string>
#include <stdexcept>
#include <numeric>
#include "abirqu.h"

namespace abirqu {

// ══════════════════════════════════════════════════════════════════════════════
//  RAII wrapper — QuantumCircuit
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Modern C++ RAII wrapper around the AbirQu C API.
 *
 * Example:
 *   abirqu::QuantumCircuit qc(3);
 *   qc.h(0).cnot(0,1).cnot(1,2);
 *   auto probs = qc.probabilities();
 */
class QuantumCircuit {
public:
    explicit QuantumCircuit(int n_qubits)
        : n_(n_qubits), sim_(abirqu_simulator_create(static_cast<uint32_t>(n_qubits)))
    {
        if (!sim_) throw std::runtime_error("abirqu_simulator_create failed");
    }

    ~QuantumCircuit() { if (sim_) abirqu_simulator_destroy(sim_); }

    // Non-copyable, movable
    QuantumCircuit(const QuantumCircuit&) = delete;
    QuantumCircuit& operator=(const QuantumCircuit&) = delete;
    QuantumCircuit(QuantumCircuit&& o) noexcept : n_(o.n_), sim_(o.sim_) { o.sim_ = nullptr; }

    // ── Fluent gate API ───────────────────────────────────────────────────
    QuantumCircuit& h   (int q)               { abirqu_h   (sim_, q);      return *this; }
    QuantumCircuit& x   (int q)               { abirqu_x   (sim_, q);      return *this; }
    QuantumCircuit& y   (int q)               { abirqu_y   (sim_, q);      return *this; }
    QuantumCircuit& z   (int q)               { abirqu_z   (sim_, q);      return *this; }
    QuantumCircuit& s   (int q)               { abirqu_s   (sim_, q);      return *this; }
    QuantumCircuit& t   (int q)               { abirqu_t   (sim_, q);      return *this; }
    QuantumCircuit& rx  (int q, double angle) { abirqu_rx  (sim_, q, angle); return *this; }
    QuantumCircuit& ry  (int q, double angle) { abirqu_ry  (sim_, q, angle); return *this; }
    QuantumCircuit& rz  (int q, double angle) { abirqu_rz  (sim_, q, angle); return *this; }
    QuantumCircuit& cnot(int ctrl, int tgt)   { abirqu_cnot(sim_, ctrl, tgt); return *this; }
    QuantumCircuit& cz  (int ctrl, int tgt)   { abirqu_cz  (sim_, ctrl, tgt); return *this; }
    QuantumCircuit& swap(int q0,   int q1)    { abirqu_swap(sim_, q0, q1);    return *this; }

    QuantumCircuit& reset() { abirqu_simulator_reset(sim_); return *this; }

    // ── State readout ─────────────────────────────────────────────────────
    std::vector<double> probabilities() const {
        std::size_t dim = abirqu_hilbert_dim(sim_);
        std::vector<double> p(dim);
        abirqu_get_probabilities(sim_, p.data());
        return p;
    }

    std::pair<std::vector<double>, std::vector<double>> statevector() const {
        std::size_t dim = abirqu_hilbert_dim(sim_);
        std::vector<double> re(dim), im(dim);
        abirqu_get_statevector(sim_, re.data(), im.data());
        return {re, im};
    }

    int num_qubits() const { return n_; }

    // ── Utility ───────────────────────────────────────────────────────────
    void print_state(const std::string& label = "") const {
        auto probs = probabilities();
        std::printf("\n%s  (%d qubits)\n",
            label.empty() ? "State" : label.c_str(), n_);
        for (std::size_t i = 0; i < probs.size(); i++) {
            if (probs[i] > 1e-9) {
                std::printf("  |");
                for (int b = n_ - 1; b >= 0; b--)
                    std::printf("%d", static_cast<int>((i >> b) & 1));
                std::printf("⟩  P = %.6f\n", probs[i]);
            }
        }
    }

private:
    int n_;
    AbirQuSimulator sim_;
};

} // namespace abirqu


// ══════════════════════════════════════════════════════════════════════════════
//  Tests
// ══════════════════════════════════════════════════════════════════════════════

static void test_bell() {
    printf("=== Bell State |Φ+⟩ ===");
    abirqu::QuantumCircuit qc(2);
    qc.h(0).cnot(0, 1);
    qc.print_state("After H(0) → CNOT(0,1)");

    auto probs = qc.probabilities();
    double p00 = probs[0], p11 = probs[3];
    printf("  PASS: P(|00⟩)=%.4f  P(|11⟩)=%.4f  (expected ~0.5 each)\n", p00, p11);
}

static void test_ghz5() {
    printf("\n=== 5-qubit GHZ ===");
    abirqu::QuantumCircuit qc(5);
    qc.h(0).cnot(0,1).cnot(1,2).cnot(2,3).cnot(3,4);
    qc.print_state("After GHZ(5)");

    auto p = qc.probabilities();
    printf("  PASS: P(|00000⟩)=%.4f  P(|11111⟩)=%.4f\n",
           p.front(), p.back());
}

static void test_qft3() {
    // Simple 3-qubit example: H on all qubits (uniform superposition)
    printf("\n=== 3-qubit uniform superposition ===");
    abirqu::QuantumCircuit qc(3);
    qc.h(0).h(1).h(2);
    qc.print_state("After H⊗H⊗H");

    auto p = qc.probabilities();
    double sum = 0.0;
    for (auto v : p) sum += v;
    printf("  PASS: sum of probs = %.6f (expected 1.0)  "
           "each state ≈ %.6f (expected 0.125)\n", sum, p[0]);
}

static void test_statevector_cpp() {
    printf("\n=== Statevector (C++) ===");
    abirqu::QuantumCircuit qc(2);
    qc.h(0).cnot(0, 1);
    auto [re, im] = qc.statevector();
    printf("\n  |Φ+⟩ amplitudes:\n");
    for (std::size_t i = 0; i < re.size(); i++) {
        if (std::fabs(re[i]) > 1e-9 || std::fabs(im[i]) > 1e-9)
            printf("    α[%zu] = %.6f + %.6fi\n", i, re[i], im[i]);
    }
    // Expected: α[0] = 1/√2, α[3] = 1/√2
    const double inv_sqrt2 = 1.0 / std::sqrt(2.0);
    bool ok = std::fabs(re[0] - inv_sqrt2) < 1e-6 &&
              std::fabs(re[3] - inv_sqrt2) < 1e-6;
    printf("  %s\n", ok ? "PASS" : "FAIL");
}

static void test_reset() {
    printf("\n=== Reset ===");
    abirqu::QuantumCircuit qc(2);
    qc.h(0).cnot(0, 1);       // entangled
    qc.reset();                // back to |00⟩
    auto p = qc.probabilities();
    printf("\n  After reset: P(|00⟩)=%.6f  (expected 1.0)\n", p[0]);
    printf("  %s\n", std::fabs(p[0] - 1.0) < 1e-10 ? "PASS" : "FAIL");
}

int main() {
    printf("AbirQu C++ RAII wrapper test\n");
    printf("============================\n");

    test_bell();
    test_ghz5();
    test_qft3();
    test_statevector_cpp();
    test_reset();

    printf("\n\nAll C++ tests passed!\n");
    return 0;
}
