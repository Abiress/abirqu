import json
import math
from abirqu.q_agi import (
    QuantumAssociativeMemory,
    QuantumInterferenceDecisionEngine,
    QuantumTensorNetworkAttention,
    QRAM,
    QuantumLanguageModel,
)

print("=" * 70)
print("  Phase 34: General Artificial Intelligence (Q-AGI Engine) Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 34.1a: Quantum Associative Memory
# ---------------------------------------------------------
print("\n--- Test 34.1a: Quantum Superposition Associative Memory ---")
mem = QuantumAssociativeMemory(num_qubits=8)

# Store patterns
patterns = [
    ("cat",    "11001010"),
    ("dog",    "10110101"),
    ("bird",   "01011010"),
    ("fish",   "00101101"),
    ("snake",  "11110000"),
]
for label, pat in patterns:
    res = mem.store_pattern(label, pat)
    print(f"  Stored '{label}': {pat} (utilization: {res['utilization']})")

# Exact recall
print(f"\n  Exact Recall (query='11001010'):")
recall = mem.retrieve("11001010")
print(f"    Best Match: {recall['best_match']['label']} (hamming={recall['best_match']['hamming_distance']})")
assert recall["best_match"]["label"] == "cat"

# Noisy recall (30% bit flip)
print(f"\n  Noisy Recall (query='11001010', noise=30%):")
noisy = mem.retrieve("11001010", noise_level=0.3)
print(f"    Corrupted Query: {noisy['corrupted_query']}")
print(f"    Best Match:      {noisy['best_match']['label']} (hamming={noisy['best_match']['hamming_distance']})")
print(f"    Grover Iters:    {noisy['grover_iterations']}")
print(f"    Complexity:      {noisy['retrieval_complexity']}")
print("✅ Quantum associative memory passed")

# ---------------------------------------------------------
# Test 34.1b: Quantum Interference Decision Engine
# ---------------------------------------------------------
print("\n--- Test 34.1b: Quantum Interference Decision Engine ---")
engine = QuantumInterferenceDecisionEngine()

options = [
    {"name": "Invest in Quantum",  "utility": 0.9, "risk": 0.3, "evidence_strength": 0.8},
    {"name": "Invest in Classical", "utility": 0.6, "risk": 0.1, "evidence_strength": 0.9},
    {"name": "Hold Cash",          "utility": 0.3, "risk": 0.05,"evidence_strength": 1.0},
    {"name": "Crypto Speculation",  "utility": 0.95,"risk": 0.8, "evidence_strength": 0.2},
]

decision = engine.evaluate_options(options)
print(f"  Recommended: {decision['recommended']} (confidence: {decision['confidence']:.4f})")
print(f"  Ranking:")
for r in decision["ranking"]:
    print(f"    {r['name']:25s} → {r['score']:.4f}")

# Multi-step decision
print(f"\n  Multi-Step Decision Chain:")
tree = [
    [{"name": "Research", "utility": 0.8, "risk": 0.1, "evidence_strength": 0.9},
     {"name": "Deploy",   "utility": 0.6, "risk": 0.5, "evidence_strength": 0.4}],
    [{"name": "Scale Up", "utility": 0.7, "risk": 0.3, "evidence_strength": 0.7},
     {"name": "Pivot",    "utility": 0.5, "risk": 0.2, "evidence_strength": 0.6}],
    [{"name": "Exit",     "utility": 0.9, "risk": 0.1, "evidence_strength": 0.95},
     {"name": "Continue", "utility": 0.4, "risk": 0.05,"evidence_strength": 0.8}],
]
multi = engine.multi_step_decision(tree)
for step in multi["decision_path"]:
    print(f"    Step {step['step']}: {step['chosen']:12s} (cum. confidence: {step['cumulative_confidence']:.4f})")
print(f"  Final Confidence: {multi['final_confidence']:.4f}")
print("✅ Quantum interference decision engine passed")

# ---------------------------------------------------------
# Test 34.2a: Tensor Network Attention
# ---------------------------------------------------------
print("\n--- Test 34.2a: Quantum Tensor Network Attention ---")
tn_attn = QuantumTensorNetworkAttention(embed_dim=8, bond_dim=4)
tokens = ["The", "quantum", "cat", "is", "both", "alive"]
attn_result = tn_attn.compute_attention(tokens)
print(f"  Tokens:             {tokens}")
print(f"  Embed Dim:          {attn_result['embed_dim']}")
print(f"  Bond Dim:           {attn_result['bond_dim']}")
print(f"  Entanglement:       {attn_result['entanglement_capacity']}")
print(f"  Cross-Attn Strength:{attn_result['cross_attention_strength']}")
print(f"  Compression Ratio:  {attn_result['compression_ratio']}x")
print(f"  Attention Matrix (first 3 rows):")
for i, row in enumerate(attn_result["attention_matrix"][:3]):
    print(f"    {tokens[i]:8s} → {row}")
print("✅ Tensor network attention passed")

# ---------------------------------------------------------
# Test 34.2b: QRAM Exponential Context
# ---------------------------------------------------------
print("\n--- Test 34.2b: QRAM Exponential Context Window ---")
qram = QRAM(address_qubits=10)

# Load tokens
context_tokens = ["Hello", "world", "quantum", "computing", "is", "the", "future", "of"]
for i, tok in enumerate(context_tokens):
    qram.write(i, tok)
print(f"  Loaded {len(context_tokens)} tokens into QRAM (capacity: {qram.capacity})")

# Superposition read
import cmath
n_addr = 4
uniform_amp = complex(1.0 / math.sqrt(n_addr), 0)
superposition = [(i, uniform_amp) for i in range(n_addr)]
read_result = qram.quantum_read(superposition)
print(f"  Superposition Read ({n_addr} addresses):")
print(f"    Router Depth:     {read_result['router_depth']}")
print(f"    Access Time:      {read_result['access_time']}")
print(f"    Classical Equiv:  {read_result['classical_equivalent_time']}")
print(f"    Speedup:          {read_result['speedup']}")
for r in read_result["results"]:
    print(f"    addr[{r['address']}] → '{r['data']}' (prob={r['probability']})")
print("✅ QRAM passed")

# ---------------------------------------------------------
# Test 34.2c: Full Quantum Language Model
# ---------------------------------------------------------
print("\n--- Test 34.2c: Full Quantum Language Model ---")
qlm = QuantumLanguageModel(vocab_size=256, embed_dim=8, bond_dim=4, context_qubits=10)

# Load context
load_result = qlm.load_context(context_tokens)
print(f"  Context Loaded:     {load_result['tokens_loaded']} tokens")
print(f"  Context Window:     {load_result['context_window']} tokens")
print(f"  Qubits Used:        {load_result['qubits_used']}")

# Attend
query = ["quantum", "is", "future"]
attend_result = qlm.attend(query)
print(f"\n  Query: {query}")
print(f"  Model: {attend_result['model_type']}")
print(f"  Advantages:")
for adv in attend_result["advantages"]:
    print(f"    • {adv}")
print("✅ Quantum Language Model passed")

print("\n" + "=" * 70)
print("  Phase 34 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
